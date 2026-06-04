"""Serve built web client (Vite dist) from the game server."""

from __future__ import annotations

import mimetypes
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote, urlparse

# Vite may emit paths without registered types on Windows.
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/wasm", ".wasm")


def serve_static(handler: BaseHTTPRequestHandler, static_root: Path) -> bool:
    """
    Try to serve a file under static_root. Returns True if a response was sent.
  SPA: unknown paths fall back to index.html.
    """
    parsed = urlparse(handler.path)
    rel = unquote(parsed.path.split("?", 1)[0])
    if rel in ("", "/"):
        rel = "/index.html"

    safe = os.path.normpath(rel.lstrip("/"))
    if safe.startswith("..") or safe.startswith(os.sep):
        handler.send_error(HTTPStatus.FORBIDDEN)
        return True

    target = static_root / safe
    if target.is_file():
        return _send_file(handler, target)

    # SPA client-side routes
    index = static_root / "index.html"
    if index.is_file():
        return _send_file(handler, index)

    handler.send_error(HTTPStatus.NOT_FOUND)
    return True


def _send_file(handler: BaseHTTPRequestHandler, path: Path) -> bool:
    data = path.read_bytes()
    mime, _ = mimetypes.guess_type(str(path))
    if not mime:
        mime = "application/octet-stream"
    handler.send_response(HTTPStatus.OK)
    handler._send_cors()
    handler.send_header("Content-Type", mime)
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)
    return True
