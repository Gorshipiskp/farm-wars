"""
Server-side shop: BUY_PRODUCT without engine.

See docs/specs/gameplay/003.NIKITA.PLAYABLE_FARM_LOOP_V2.md
"""

import logging

from db.loader import GameContentCatalog
from server.catalog_api import SHOP_EXTRA_PRODUCT_IDS
from server.world_util import add_inventory, find_player, make_event

log = logging.getLogger("farm_wars.server.shop")


def shop_buyable_product_ids(catalog: GameContentCatalog) -> frozenset[str]:
    """Seeds for planting plus flour/feed; crops are not sold in the shop."""
    ids = set(SHOP_EXTRA_PRODUCT_IDS)
    for plant in catalog.plants.values():
        ids.add(plant.seed_product_id)
    return frozenset(ids)


def process_buy_product(
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

    product = catalog.products.get(product_id)
    if product is None:
        return make_event(tick_id, "PURCHASE_FAILED", {
            "player_id": player_id,
            "product_id": product_id,
            "reason": "UNKNOWN_PRODUCT",
            "required": 0,
            "available": 0,
        })

    if product_id not in shop_buyable_product_ids(catalog):
        return make_event(tick_id, "PURCHASE_FAILED", {
            "player_id": player_id,
            "product_id": product_id,
            "reason": "NOT_IN_SHOP",
            "required": 0,
            "available": 0,
        })

    player = find_player(world_state, player_id)
    if player is None:
        return make_event(tick_id, "CONTRACT_ERROR", {
            "error_code": "MISSING_FIELD",
            "message": f"Player not found: {player_id}",
            "field_path": "player_id",
        })

    total = product.base_sell_price * amount
    available = player.get("money_bestiki", 0)
    if available < total:
        return make_event(tick_id, "PURCHASE_FAILED", {
            "player_id": player_id,
            "product_id": product_id,
            "reason": "NOT_ENOUGH_MONEY",
            "required": total,
            "available": available,
        })

    player["money_bestiki"] = available - total
    add_inventory(player, product_id, amount)
    log.info(
        "BUY_PRODUCT ok player=%s product=%s x%d paid=%s",
        player_id, product_id, amount, total,
    )
    return make_event(tick_id, "PRODUCT_PURCHASED", {
        "player_id": player_id,
        "product_id": product_id,
        "amount": amount,
        "total_paid": total,
    })
