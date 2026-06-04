"""
Farm Wars authoritative server.

Run from repo root:
    py tools/init_db.py --seed
    py -m server
    # or: bash scripts/play.sh

Environment:
    FARM_WARS_HOST      — bind address (default 0.0.0.0 = LAN + localhost)
    FARM_WARS_PORT      — HTTP port (default 8765)
    FARM_WARS_TICK_SEC  — tick interval seconds (default 1/3 ≈ 3 ticks/sec)
    FARM_WARS_DB_PATH   — SQLite path
    FARM_WARS_OPEN_BROWSER — 1 to open default browser (default 1 if web dist exists)
    FARM_WARS_PORTABLE  — 1 to store DB in ./data next to exe
    FARM_WARS_DEV       — if 1, win target cake
    FARM_WARS_EVENT_INTERVAL / FARM_WARS_EVENT_PROB — random events
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
import webbrowser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from shared.log_config import setup_logging
from shared.paths import ensure_user_db, web_dist_dir
from server.game_server import GameServer
from server.http_api import serve
from server.network_util import guess_lan_ipv4

setup_logging()
log = logging.getLogger("farm_wars.server")


def _should_open_browser() -> bool:
    flag = os.environ.get("FARM_WARS_OPEN_BROWSER", "").strip().lower()
    if flag in ("0", "false", "no"):
        return False
    if flag in ("1", "true", "yes"):
        return True
    return web_dist_dir() is not None


def _open_browser_later(port: int) -> None:
    time.sleep(1.2)
    url = f"http://127.0.0.1:{port}/"
    log.info("Opening browser: %s", url)
    try:
        webbrowser.open(url)
    except OSError as exc:
        log.warning("Could not open browser: %s", exc)


def run() -> int:
    log.info("Starting Farm Wars server...")

    try:
        os.environ.setdefault("FARM_WARS_DB_PATH", ensure_user_db())
    except FileNotFoundError as exc:
        log.error("%s", exc)
        return 1

    try:
        game = GameServer()
    except FileNotFoundError as exc:
        log.error("%s", exc)
        return 1

    from server.random_events import EVENT_TICK_INTERVAL, EVENT_TRIGGER_PROBABILITY

    log.info(
        "Content loaded: %d products, %d recipes, win=%s, events every %s ticks p=%s",
        len(game.catalog.products),
        len(game.catalog.recipes),
        game.catalog.default_win_product_id(),
        EVENT_TICK_INTERVAL,
        EVENT_TRIGGER_PROBABILITY,
    )

    game.start_ticks()

    host = os.environ.get("FARM_WARS_HOST", "0.0.0.0")
    port = int(os.environ.get("FARM_WARS_PORT", "8765"))
    static = web_dist_dir()
    httpd = serve(game, host=host, port=port, static_root=static)

    if host in ("0.0.0.0", ""):
        lan_ip = guess_lan_ipv4()
        if lan_ip:
            log.info("Clients on your network: http://%s:%s", lan_ip, port)
        log.info("Clients on this PC: http://127.0.0.1:%s", port)
    else:
        log.info("Open in browser: http://%s:%s", host, port)

    if static is not None and _should_open_browser():
        threading.Thread(target=_open_browser_later, args=(port,), daemon=True).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down...")
    finally:
        game.stop_ticks()
        httpd.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(run())
