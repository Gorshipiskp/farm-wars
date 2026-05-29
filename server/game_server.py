"""Farm Wars game server: registry + tick loop + catalog."""

import logging
import os

from db.loader import load_catalog
from server.engine_adapter import get_simulate_tick
from server.registry import MatchRegistry
from server.tick_loop import TickLoop

log = logging.getLogger("farm_wars.server")


class GameServer:
    def __init__(
            self,
            db_path: str | None = None,
            tick_interval_sec: float | None = None,
    ):
        self.catalog = load_catalog(db_path)
        self.registry = MatchRegistry(self.catalog)
        self.simulate_tick, self.engine_name = get_simulate_tick()
        if tick_interval_sec is None:
            from shared.game_pacing import tick_interval_sec as default_interval

            interval = default_interval()
        else:
            interval = tick_interval_sec
        self.tick_loop = TickLoop(self.registry, self.simulate_tick, interval)
        log.info("Tick loop: %.2f s interval (%.1f ticks/sec)", interval, 1.0 / interval)
        log.info("Simulation backend: %s", self.engine_name)
        from server.match import SHOP_HANDLER_VERSION

        log.info(
            "Server handler=%s (BUY_PRODUCT immediate; HARVEST_PLANT -> engine)",
            SHOP_HANDLER_VERSION,
        )

    def start_ticks(self) -> None:
        self.tick_loop.start()

    def stop_ticks(self) -> None:
        self.tick_loop.stop()

    def create_match(self, host_name: str | None = None) -> dict:
        return self.registry.create_match(host_name)

    def join_match(self, join_code: str, player_name: str) -> dict:
        return self.registry.join_match(join_code, player_name)

    def start_match(self, match_id: str) -> dict:
        self.registry.start_match(match_id)
        match = self.registry.get_match(match_id)
        return {
            "contract_version": "v1",
            "match_id": match_id,
            "status": match.status,
            "player_count": len(match.players),
        }

    def submit_action(self, envelope: dict) -> dict:
        match_id = envelope["match_id"]
        match = self.registry.get_match(match_id)
        action = envelope.get("action", {})
        log.debug(
            "submit_action match=%s player=%s type=%s",
            match_id,
            envelope.get("player_id"),
            action.get("action_type"),
        )
        match.enqueue_action(envelope)
        return {"contract_version": "v1", "accepted": True}

    def get_sync(self, match_id: str, since_tick: int = 0) -> dict | None:
        match = self.registry.get_match(match_id)
        return match.latest_sync(since_tick)

    def get_roster(self, match_id: str) -> dict:
        match = self.registry.get_match(match_id)
        return match.roster_payload()
