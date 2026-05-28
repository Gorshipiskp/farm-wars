"""In-memory match state: players, world, action queue, sync history."""

import copy
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field

from db.loader import GameContentCatalog

log = logging.getLogger("farm_wars.server.match")

from server.action_enricher import enrich_actions_for_tick
from server.harvest import process_harvest_plant
from server.shop import process_buy_product
from server.world_factory import create_initial_world

SERVER_ONLY_ACTIONS = frozenset({"BUY_PRODUCT", "HARVEST_PLANT"})
# Bump when server-only actions change (visible in /api/health).
SHOP_HANDLER_VERSION = "immediate_v3"


def _action_type(action: dict) -> str:
    raw = action.get("action_type")
    if raw is None:
        return ""
    return str(raw).strip().upper()


@dataclass
class MatchPlayer:
    player_id: str
    display_name: str
    joined_at: float = field(default_factory=time.time)


class Match:
    LOBBY = "LOBBY"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"

    def __init__(self, match_id: str, join_code: str, catalog: GameContentCatalog):
        self.match_id = match_id
        self.join_code = join_code
        self.catalog = catalog
        self.status = self.LOBBY
        self.players: list[MatchPlayer] = []
        self.host_player_id: str | None = None
        self.world_state: dict | None = None
        self.action_queue: deque[dict] = deque()
        self.sync_history: list[dict] = []
        self._unacked_events: list[dict] = []
        self._lock = threading.Lock()

    def add_player(self, display_name: str) -> str:
        with self._lock:
            if self.status != self.LOBBY:
                raise ValueError("MATCH_ALREADY_STARTED")
            player_id = f"p{len(self.players) + 1}"
            self.players.append(MatchPlayer(player_id=player_id, display_name=display_name))
            if self.host_player_id is None:
                self.host_player_id = player_id
            return player_id

    def start(self) -> None:
        with self._lock:
            if self.status != self.LOBBY:
                raise ValueError("MATCH_ALREADY_STARTED")
            if len(self.players) < 1:
                raise ValueError("NOT_ENOUGH_PLAYERS")
            player_tuples = [(p.player_id, p.display_name) for p in self.players]
            self.world_state = create_initial_world(
                self.match_id, player_tuples, self.catalog
            )
            self.status = self.RUNNING
            self._push_sync([], bump_tick=False)

    def enqueue_action(self, envelope: dict) -> None:
        with self._lock:
            if self.status != self.RUNNING:
                raise ValueError("MATCH_NOT_RUNNING")
            if envelope.get("match_id") != self.match_id:
                raise ValueError("MATCH_ID_MISMATCH")
            player_id = envelope.get("player_id")
            if not any(p.player_id == player_id for p in self.players):
                raise ValueError("UNKNOWN_PLAYER")
            action = envelope["action"]
            action_type = _action_type(action)

            if action_type == "BUY_PRODUCT":
                self._handle_server_only_immediate(action, process_buy_product, "Shop")
                return
            if action_type == "HARVEST_PLANT":
                self._handle_server_only_immediate(action, process_harvest_plant, "Harvest")
                return

            log.info(
                "Action queued match=%s player=%s type=%s payload=%s",
                self.match_id,
                player_id,
                action_type,
                action.get("payload"),
            )
            self.action_queue.append(action)

    def _handle_server_only_immediate(self, action: dict, processor, label: str) -> None:
        """Run server-only action now; never queue for the engine."""
        if self.world_state is None:
            raise ValueError("NO_WORLD_STATE")
        tick_id = self.world_state.get("tick_id", 0)
        event = processor(action, self.world_state, self.catalog, tick_id)
        events = [event] if event else []
        log.info(
            "%s immediate tick=%s player=%s -> %s",
            label,
            tick_id,
            action.get("player_id"),
            event.get("event_type") if event else "none",
        )
        if event and event.get("event_type") == "CONTRACT_ERROR":
            log.warning("%s CONTRACT_ERROR: %s", label, event.get("payload"))
        self._unacked_events.extend(events)
        self._push_sync(events, bump_tick=False)

    def process_tick(self, simulate_tick) -> dict | None:
        """Run one simulation tick. Returns latest StateSyncEvent or None if not running."""
        with self._lock:
            if self.status != self.RUNNING or self.world_state is None:
                return None

            actions = list(self.action_queue)
            self.action_queue.clear()

            tick_id = self.world_state.get("tick_id", 0) + 1
            server_events: list[dict] = []
            engine_queue: list[dict] = []

            for action in actions:
                action_type = _action_type(action)
                if action_type in SERVER_ONLY_ACTIONS:
                    if action_type != action.get("action_type"):
                        log.warning(
                            "Normalized action_type %r -> %s",
                            action.get("action_type"),
                            action_type,
                        )
                if action_type in SERVER_ONLY_ACTIONS:
                    processor = (
                        process_buy_product
                        if action_type == "BUY_PRODUCT"
                        else process_harvest_plant
                    )
                    event = processor(action, self.world_state, self.catalog, tick_id)
                    if event:
                        server_events.append(event)
                else:
                    engine_queue.append(action)

            engine_actions, pre_events = enrich_actions_for_tick(
                engine_queue, self.world_state, self.catalog, tick_id
            )
            server_events.extend(pre_events)
            before = len(engine_actions)
            engine_actions = [
                a for a in engine_actions
                if _action_type(a) not in SERVER_ONLY_ACTIONS
            ]
            if before != len(engine_actions):
                log.error(
                    "Tick %s: stripped BUY_PRODUCT from engine queue (server-only action)",
                    tick_id,
                )

            tick_input = {
                "contract_version": "v1",
                "tick_id": tick_id,
                "world_state": self.world_state,
                "actions": engine_actions,
            }

            result = simulate_tick(tick_input)
            self.world_state = result["next_world_state"]
            events = server_events + list(result.get("events", []))
            for ev in events:
                if ev.get("event_type") == "CONTRACT_ERROR":
                    log.warning(
                        "Tick %s CONTRACT_ERROR: %s",
                        tick_id,
                        ev.get("payload"),
                    )

            events.extend(self._advance_factories(tick_id))
            winner = self._check_win()
            if winner:
                events.append({
                    "contract_version": "v1",
                    "event_type": "MATCH_FINISHED",
                    "server_tick": tick_id,
                    "payload": {
                        "winner_player_id": winner,
                        "target_product_id": self.world_state["win_condition"]["target_product_id"],
                    },
                })
                self.world_state["win_condition"]["winner_player_id"] = winner
                self.status = self.FINISHED

            return self._push_sync(events, bump_tick=True, tick_id=tick_id)

    def latest_sync(self, since_tick: int = 0) -> dict | None:
        with self._lock:
            if not self.sync_history:
                return None
            latest = self.sync_history[-1]
            merged_events: list[dict] = list(self._unacked_events)
            self._unacked_events.clear()
            for item in self.sync_history:
                if item["tick_id"] > since_tick:
                    merged_events.extend(item["events"])
            result = copy.deepcopy(latest)
            result["events"] = merged_events
            return result

    def _push_sync(
            self,
            events: list[dict],
            bump_tick: bool,
            tick_id: int | None = None,
    ) -> dict:
        if self.world_state is None:
            raise ValueError("NO_WORLD_STATE")
        if bump_tick and tick_id is not None:
            current_tick = tick_id
        else:
            current_tick = self.world_state.get("tick_id", 0)

        sync = {
            "contract_version": "v1",
            "match_id": self.match_id,
            "tick_id": current_tick,
            "world_state": copy.deepcopy(self.world_state),
            "events": events,
        }
        self.sync_history.append(sync)
        return sync

    def _advance_factories(self, tick_id: int) -> list[dict]:
        events = []
        if self.world_state is None:
            return events

        for factory in self.world_state.get("factories", []):
            recipe_id = factory.get("active_recipe_id")
            remaining = factory.get("remaining_time_sec", 0)
            if not recipe_id or remaining <= 0:
                continue

            factory["remaining_time_sec"] = max(0, remaining - 1)
            if factory["remaining_time_sec"] > 0:
                continue

            recipe = self.catalog.get_recipe(recipe_id)
            if recipe is None:
                continue

            owner_id = factory["owner_player_id"]
            self._add_inventory(owner_id, recipe.output_product_id, 1)
            factory["active_recipe_id"] = None

            events.append({
                "contract_version": "v1",
                "event_type": "RECIPE_FINISHED",
                "server_tick": tick_id,
                "payload": {
                    "factory_id": factory["factory_id"],
                    "recipe_id": recipe_id,
                    "product_id": recipe.output_product_id,
                    "player_id": owner_id,
                },
            })

        return events

    def _add_inventory(self, player_id: str, product_id: str, amount: int) -> None:
        for player in self.world_state.get("players", []):
            if player["player_id"] != player_id:
                continue
            for item in player.get("inventory", []):
                if item["product_id"] == product_id:
                    item["amount"] += amount
                    return
            player.setdefault("inventory", []).append({
                "product_id": product_id,
                "amount": amount,
            })
            return

    def _check_win(self) -> str | None:
        if self.world_state is None:
            return None
        target = self.world_state["win_condition"]["target_product_id"]
        for player in self.world_state.get("players", []):
            for item in player.get("inventory", []):
                if item["product_id"] == target and item["amount"] >= 1:
                    return player["player_id"]
        return None
