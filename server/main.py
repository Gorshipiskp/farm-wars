"""
Farm Wars authoritative server.

Run from repo root:
    py tools/init_db.py --seed
    py -m server

Environment:
    FARM_WARS_HOST      — bind address (default 0.0.0.0 = LAN + localhost)
    FARM_WARS_PORT      — HTTP port (default 8765)
    FARM_WARS_TICK_SEC  — tick interval seconds (default 1.0)
    FARM_WARS_DB_PATH   — SQLite path
"""

import logging
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from shared.log_config import setup_logging
from server.game_server import GameServer
from server.http_api import serve
from server.network_util import guess_lan_ipv4

setup_logging()
log = logging.getLogger("farm_wars.server")


def run() -> int:
    log.info("Starting Farm Wars server...")

    try:
        game = GameServer()
    except FileNotFoundError as exc:
        log.error("%s", exc)
        return 1

    log.info(
        "Content loaded: %d products, %d recipes, win=%s",
        len(game.catalog.products),
        len(game.catalog.recipes),
        game.catalog.default_win_product_id(),
    )

    game.start_ticks()

    host = os.environ.get("FARM_WARS_HOST", "0.0.0.0")
    port = int(os.environ.get("FARM_WARS_PORT", "8765"))
    httpd = serve(game, host=host, port=port)

    if host in ("0.0.0.0", ""):
        lan_ip = guess_lan_ipv4()
        if lan_ip:
            log.info("Clients on your network: http://%s:%s", lan_ip, port)
        log.info("Clients on this PC: http://127.0.0.1:%s", port)

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
