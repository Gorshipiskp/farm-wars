"""Background StateSync poller — client zone only."""

import logging
import threading

from client.net import ServerClient, ServerError
from client.session import ClientSession

log = logging.getLogger("farm_wars.client.sync")


class SyncPoller:
    def __init__(
            self,
            client: ServerClient,
            session: ClientSession,
            interval_sec: float = 0.35,
    ):
        self._client = client
        self._session = session
        self._interval = interval_sec
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="sync-poller", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def _run(self) -> None:
        while not self._stop.is_set():
            if not self._session.match_id:
                self._stop.wait(self._interval)
                continue
            try:
                since = self._session.last_sync_tick
                sync = self._client.poll_sync(
                    self._session.match_id,
                    since,
                )
                if sync.get("events"):
                    for ev in sync["events"]:
                        et = ev.get("event_type")
                        if et == "CONTRACT_ERROR":
                            log.warning(
                                "Sync CONTRACT_ERROR: %s",
                                ev.get("payload"),
                            )
                    log.info(
                        "Sync match=%s since_tick=%s tick=%s events=%s",
                        self._session.match_id,
                        since,
                        sync.get("tick_id"),
                        [e.get("event_type") for e in sync["events"]],
                    )
                self._session.apply_sync(sync)
                self._session.clear_error()
            except ServerError as exc:
                self._session.set_error(f"{exc.error_code}: {exc.message}")
            except Exception as exc:
                log.exception("Sync poll failed")
                self._session.set_error(str(exc))
            self._stop.wait(self._interval)
