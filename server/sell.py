"""Server-side sell: SELL_PRODUCT — convert inventory to Bestiki."""

from __future__ import annotations

import logging

from db.loader import GameContentCatalog
from server.world_util import consume_product, find_player, make_event

log = logging.getLogger("farm_wars.server.sell")

def sellable_product_ids(catalog: GameContentCatalog) -> frozenset[str]:
    """Harvested/processed goods only; seeds and feed cannot be sold."""
    return frozenset(
        pid
        for pid, product in catalog.products.items()
        if product.category in ("RAW", "PROCESSED")
    )


def process_sell_product(
    action: dict,
    world_state: dict,
    catalog: GameContentCatalog,
    tick_id: int,
) -> dict | None:
    player_id = action.get("player_id")
    payload = action.get("payload") or {}
    product_id = payload.get("product_id")
    raw_amount = payload.get("amount", 1)
    try:
        amount = int(raw_amount)
    except (TypeError, ValueError):
        amount = -1

    if not product_id or amount < 1:
        return make_event(tick_id, "CONTRACT_ERROR", {
            "error_code": "MISSING_FIELD",
            "message": "product_id and amount>=1 required",
            "field_path": "payload",
        })

    if product_id not in sellable_product_ids(catalog):
        return make_event(tick_id, "SELL_FAILED", {
            "player_id": player_id,
            "product_id": product_id,
            "reason": "NOT_SELLABLE",
        })

    product = catalog.products.get(product_id)
    if product is None:
        return make_event(tick_id, "SELL_FAILED", {
            "player_id": player_id,
            "product_id": product_id,
            "reason": "UNKNOWN_PRODUCT",
        })

    player = find_player(world_state, player_id)
    if player is None:
        return make_event(tick_id, "CONTRACT_ERROR", {
            "error_code": "MISSING_FIELD",
            "message": f"Player not found: {player_id}",
            "field_path": "player_id",
        })

    if not consume_product(player, product_id, amount):
        return make_event(tick_id, "SELL_FAILED", {
            "player_id": player_id,
            "product_id": product_id,
            "reason": "NOT_ENOUGH_PRODUCT",
        })

    total = product.base_sell_price * amount
    player["money_bestiki"] = player.get("money_bestiki", 0) + total
    log.info(
        "SELL_PRODUCT ok player=%s product=%s x%d earned=%s",
        player_id, product_id, amount, total,
    )
    return make_event(tick_id, "PRODUCT_SOLD", {
        "player_id": player_id,
        "product_id": product_id,
        "amount": amount,
        "total_earned": total,
    })
