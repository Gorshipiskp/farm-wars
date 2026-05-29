"""Shared helpers for server-side world mutation and events."""

from __future__ import annotations


def find_player(world_state: dict, player_id: str) -> dict | None:
    for player in world_state.get("players", []):
        if player.get("player_id") == player_id:
            return player
    return None


def find_tile(world_state: dict, tile_id: str) -> dict | None:
    if not tile_id:
        return None
    for tile in world_state.get("map", {}).get("tiles", []):
        if tile.get("tile_id") == tile_id:
            return tile
    return None


def add_inventory(player: dict, product_id: str, amount: int) -> None:
    for item in player.get("inventory", []):
        if item["product_id"] == product_id:
            item["amount"] += amount
            return
    player.setdefault("inventory", []).append({
        "product_id": product_id,
        "amount": amount,
    })


def consume_product(player: dict, product_id: str, amount: int) -> bool:
    inventory = player.get("inventory", [])
    amounts = {i["product_id"]: i["amount"] for i in inventory}
    if amounts.get(product_id, 0) < amount:
        return False
    amounts[product_id] -= amount
    player["inventory"] = [
        {"product_id": pid, "amount": amt}
        for pid, amt in amounts.items()
        if amt > 0
    ]
    return True


def make_event(tick_id: int, event_type: str, payload: dict) -> dict:
    return {
        "contract_version": "v1",
        "event_type": event_type,
        "server_tick": tick_id,
        "payload": payload,
    }


def contract_error(
    tick_id: int,
    code: str,
    message: str,
    field_path: str | None,
) -> dict:
    return make_event(tick_id, "CONTRACT_ERROR", {
        "error_code": code,
        "message": message,
        "field_path": field_path,
    })
