"""Background fixed-interval tick loop for all running matches."""

import logging
import threading

log = logging.getLogger("farm_wars.server.tick")


class TickLoop:
    def __init__(self, registry, simulate_tick, interval_sec: float = 1.0):
        self.registry = registry
        self.simulate_tick = simulate_tick
        self.interval_sec = interval_sec
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="farm-wars-tick", daemon=True)
        self._thread.start()
        log.info("Tick loop started (interval=%.2fs)", self.interval_sec)

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def _run(self) -> None:
        while not self._stop.is_set():
            for match_id in self.registry.list_match_ids():
                try:
                    match = self.registry.get_match(match_id)
                    if match.status != match.RUNNING:
                        continue
                    sync = match.process_tick(self.simulate_tick)
                    if sync and sync.get("events"):
                        log.debug(
                            "match %s tick %s events: %s",
                            match_id,
                            sync["tick_id"],
                            [e["event_type"] for e in sync["events"]],
                        )
                except Exception:
                    log.exception("Tick failed for match %s", match_id)
            self._stop.wait(self.interval_sec)
