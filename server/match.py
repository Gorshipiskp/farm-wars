"""In-memory match state: players, world, action queue, sync history."""

import copy
import threading
import time
from collections import deque
from dataclasses import dataclass, field

from db.loader import GameContentCatalog
from server.world_factory import create_initial_world


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
            self.action_queue.append(envelope["action"])

    def process_tick(self, simulate_tick) -> dict | None:
        """Run one simulation tick. Returns latest StateSyncEvent or None if not running."""
        with self._lock:
            if self.status != self.RUNNING or self.world_state is None:
                return None

            actions = list(self.action_queue)
            self.action_queue.clear()

            tick_id = self.world_state.get("tick_id", 0) + 1
            tick_input = {
                "contract_version": "v1",
                "tick_id": tick_id,
                "world_state": self.world_state,
                "actions": actions,
            }

            result = simulate_tick(tick_input)
            self.world_state = result["next_world_state"]
            events = list(result.get("events", []))

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
            for item in reversed(self.sync_history):
                if item["tick_id"] >= since_tick:
                    return copy.deepcopy(item)
            return copy.deepcopy(self.sync_history[-1])

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
