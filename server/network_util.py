"""Small helpers for LAN multiplayer (server zone)."""

import socket


def guess_lan_ipv4() -> str | None:
    """Best-effort local IPv4 for other machines on the same network."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return None
