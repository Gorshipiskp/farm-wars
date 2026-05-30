"""Bestiki costs for watering and feeding (server enricher, before engine)."""

from __future__ import annotations

from db.loader import GameContentCatalog

FEED_PRODUCT_ID = "feed"
DEFAULT_FEED_COST = 3
DEFAULT_WATER_COST = 2


def feed_care_cost(catalog: GameContentCatalog) -> int:
    product = catalog.products.get(FEED_PRODUCT_ID)
    if product is None:
        return DEFAULT_FEED_COST
    return max(1, int(product.base_sell_price))


def water_care_cost(catalog: GameContentCatalog) -> int:
    feed = feed_care_cost(catalog)
    if feed > 1:
        return feed - 1
    return DEFAULT_WATER_COST


def try_spend_bestiki(player: dict, amount: int) -> bool:
    available = int(player.get("money_bestiki", 0))
    if available < amount:
        return False
    player["money_bestiki"] = available - amount
    return True
