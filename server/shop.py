"""
Server-side shop: BUY_PRODUCT without engine.

See docs/specs/gameplay/003.NIKITA.PLAYABLE_FARM_LOOP_V2.md
"""

import logging

from db.loader import GameContentCatalog

log = logging.getLogger("farm_wars.server.shop")


def process_buy_product(
    action: dict,
    world_state: dict,
    catalog: GameContentCatalog,
    tick_id: int,
) -> dict | None:
    """
    Apply purchase to world_state in place.
    Returns ServerEvent dict or None if action is invalid (caller may emit error).
    """
    player_id = action.get("player_id")
    payload = action.get("payload") or {}
    product_id = payload.get("product_id")
    raw_amount = payload.get("amount", 1)
    try:
        amount = int(raw_amount)
    except (TypeError, ValueError):
        amount = -1

    log.debug(
        "BUY_PRODUCT player=%s product=%s amount=%s (raw=%r)",
        player_id, product_id, amount, raw_amount,
    )

    if not product_id or amount < 1:
        log.warning(
            "BUY_PRODUCT rejected: invalid payload player=%s product=%r amount=%r",
            player_id, product_id, raw_amount,
        )
        return _event(tick_id, "CONTRACT_ERROR", {
            "error_code": "MISSING_FIELD",
            "message": "product_id and amount>=1 required",
            "field_path": "payload",
        })

    product = catalog.products.get(product_id)
    if product is None:
        log.warning("BUY_PRODUCT unknown product=%s player=%s", product_id, player_id)
        return _event(tick_id, "PURCHASE_FAILED", {
            "player_id": player_id,
            "product_id": product_id,
            "reason": "UNKNOWN_PRODUCT",
            "required": 0,
            "available": 0,
        })

    player = _find_player(world_state, player_id)
    if player is None:
        log.error(
            "BUY_PRODUCT player not found: %s (world players: %s)",
            player_id,
            [p.get("player_id") for p in world_state.get("players", [])],
        )
        return _event(tick_id, "CONTRACT_ERROR", {
            "error_code": "MISSING_FIELD",
            "message": f"Player not found: {player_id}",
            "field_path": "player_id",
        })

    total = product.base_sell_price * amount
    available = player.get("money_bestiki", 0)

    if available < total:
        log.info(
            "BUY_PRODUCT failed NOT_ENOUGH_MONEY player=%s need=%s have=%s",
            player_id, total, available,
        )
        return _event(tick_id, "PURCHASE_FAILED", {
            "player_id": player_id,
            "product_id": product_id,
            "reason": "NOT_ENOUGH_MONEY",
            "required": total,
            "available": available,
        })

    player["money_bestiki"] = available - total
    _add_inventory(player, product_id, amount)

    log.info(
        "BUY_PRODUCT ok player=%s product=%s x%d paid=%s money=%s",
        player_id, product_id, amount, total, player["money_bestiki"],
    )
    return _event(tick_id, "PRODUCT_PURCHASED", {
        "player_id": player_id,
        "product_id": product_id,
        "amount": amount,
        "total_paid": total,
    })


def _find_player(world_state: dict, player_id: str) -> dict | None:
    for player in world_state.get("players", []):
        if player["player_id"] == player_id:
            return player
    return None


def _add_inventory(player: dict, product_id: str, amount: int) -> None:
    for item in player.get("inventory", []):
        if item["product_id"] == product_id:
            item["amount"] += amount
            return
    player.setdefault("inventory", []).append({
        "product_id": product_id,
        "amount": amount,
    })


def _event(tick_id: int, event_type: str, payload: dict) -> dict:
    return {
        "contract_version": "v1",
        "event_type": event_type,
        "server_tick": tick_id,
        "payload": payload,
    }
