"""Client session: credentials + latest server state from StateSyncEvent."""

import threading
from dataclasses import dataclass, field


@dataclass
class ClientSession:
    player_name: str = ""
    match_id: str = ""
    player_id: str = ""
    join_code: str = ""
    is_host: bool = False

    world_state: dict | None = None
    last_sync_tick: int = 0
    last_events: list = field(default_factory=list)
    last_error: str = ""
    match_finished: bool = False

    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def apply_sync(self, sync: dict) -> None:
        with self._lock:
            self.world_state = sync.get("world_state")
            self.last_sync_tick = sync.get("tick_id", 0)
            self.last_events = sync.get("events", [])
            for event in self.last_events:
                if event.get("event_type") == "MATCH_FINISHED":
                    self.match_finished = True

    def set_error(self, message: str) -> None:
        with self._lock:
            self.last_error = message

    def clear_error(self) -> None:
        with self._lock:
            self.last_error = ""

    def snapshot(self) -> tuple[dict | None, int, list, str, bool]:
        with self._lock:
            return (
                self.world_state,
                self.last_sync_tick,
                list(self.last_events),
                self.last_error,
                self.match_finished,
            )
