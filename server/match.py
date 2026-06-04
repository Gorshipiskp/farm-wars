"""In-memory match state: players, world, action queue, sync history."""

import copy
import logging
import os
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

from db.loader import GameContentCatalog
from server.action_enricher import enrich_actions_for_tick
from server.animals import process_buy_animal
from server.random_events import maybe_random_event_action
from server.stipend import apply_stipends
from server.mine_defuse import process_clear_mine
from server.sabotage import process_apply_sabotage
from server.sell import process_sell_product
from server.shop import process_buy_product
from server.world_factory import create_initial_world

log = logging.getLogger("farm_wars.server.match")

SERVER_ONLY_ACTIONS = frozenset({
    "BUY_PRODUCT", "SELL_PRODUCT", "BUY_ANIMAL", "APPLY_SABOTAGE", "CLEAR_MINE",
})
SERVER_ONLY_PROCESSORS: dict[str, Callable] = {
    "BUY_PRODUCT": process_buy_product,
    "SELL_PRODUCT": process_sell_product,
    "BUY_ANIMAL": process_buy_animal,
    "APPLY_SABOTAGE": process_apply_sabotage,
    "CLEAR_MINE": process_clear_mine,
}
# Bump when server-only actions change (visible in /api/health).
SHOP_HANDLER_VERSION = "immediate_v7"
SYNC_HISTORY_MAX = int(os.environ.get("FARM_WARS_SYNC_HISTORY_MAX", "200"))


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

    def roster_payload(self) -> dict:
        with self._lock:
            return {
                "contract_version": "v1",
                "match_id": self.match_id,
                "join_code": self.join_code,
                "status": self.status,
                "host_player_id": self.host_player_id,
                "players": [
                    {
                        "player_id": p.player_id,
                        "display_name": p.display_name,
                    }
                    for p in self.players
                ],
            }

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

    def enqueue_action(self, envelope: dict) -> str:
        """Return ``immediate`` if applied on server now, else ``queued`` for engine tick."""
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

            processor = SERVER_ONLY_PROCESSORS.get(action_type)
            if processor is not None:
                labels = {
                    "BUY_PRODUCT": "Shop",
                    "SELL_PRODUCT": "Sell",
                    "BUY_ANIMAL": "Animals",
                    "APPLY_SABOTAGE": "Sabotage",
                    "CLEAR_MINE": "MineDefuse",
                }
                label = labels.get(action_type, action_type)
                self._handle_server_only_immediate(action, processor, label)
                return "immediate"

            log.info(
                "Action queued match=%s player=%s type=%s payload=%s",
                self.match_id,
                player_id,
                action_type,
                action.get("payload"),
            )
            self.action_queue.append(action)
            return "queued"

    def _handle_server_only_immediate(self, action: dict, processor, label: str) -> None:
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
                    log.error(
                        "Tick %s: server-only action %s in queue (should be immediate only)",
                        tick_id,
                        action_type,
                    )
                    continue
                engine_queue.append(action)

            world_event = maybe_random_event_action(self.catalog, tick_id)
            if world_event is not None:
                engine_queue.append(world_event)

            server_events.extend(apply_stipends(self.world_state, self.catalog, tick_id))

            engine_actions, pre_events = enrich_actions_for_tick(
                engine_queue, self.world_state, self.catalog, tick_id
            )
            server_events.extend(pre_events)

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
        if len(self.sync_history) > SYNC_HISTORY_MAX:
            self.sync_history = self.sync_history[-SYNC_HISTORY_MAX:]
        return sync

    def _check_win(self) -> str | None:
        if self.world_state is None:
            return None
        win = self.world_state.get("win_condition") or {}
        target = win.get("target_product_id")
        if not target:
            return None
        for player in self.world_state.get("players", []):
            for item in player.get("inventory", []):
                if item["product_id"] == target and item["amount"] >= 1:
                    return player["player_id"]
        return None
