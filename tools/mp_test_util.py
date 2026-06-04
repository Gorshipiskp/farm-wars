"""Shared helpers for multiplayer integration tests (in-process GameServer)."""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from server.game_server import GameServer


def action_envelope(
    match_id: str,
    player_id: str,
    action_type: str,
    payload: dict,
) -> dict:
    return {
        "contract_version": "v1",
        "match_id": match_id,
        "player_id": player_id,
        "action": {
            "contract_version": "v1",
            "player_id": player_id,
            "action_type": action_type,
            "payload": payload,
            "client_ts": 0,
        },
    }


def tiles_for(world: dict, owner: str) -> list[dict]:
    return [t for t in world["map"]["tiles"] if t.get("owner_player_id") == owner]


def setup_match(player_names: list[str]) -> tuple[GameServer, str, object]:
    """Create match, join guests, start. Returns (game, match_id, Match)."""
    if not player_names:
        raise ValueError("player_names must not be empty")
    game = GameServer()
    created = game.create_match(player_names[0])
    mid = created["match_id"]
    code = created["join_code"]
    for name in player_names[1:]:
        game.join_match(code, name)
    game.start_match(mid)
    return game, mid, game.registry.get_match(mid)


def inventory_amount(world: dict, player_id: str, product_id: str) -> int:
    player = next(p for p in world["players"] if p["player_id"] == player_id)
    for item in player.get("inventory", []):
        if item["product_id"] == product_id:
            return int(item["amount"])
    return 0
