"""
Server-side animals: BUY_ANIMAL (immediate).

See docs/specs/server/007.NIKITA.ANIMALS_BUY_AND_FEED.md
"""

import logging

from db.loader import Animal, GameContentCatalog
from server.world_util import contract_error, find_player, find_tile, make_event

log = logging.getLogger("farm_wars.server.animals")

DEFAULT_ANIMAL_ID = "cow"


def animal_buy_price(catalog: GameContentCatalog, animal: Animal) -> int:
    product = catalog.products.get(animal.product_id)
    base = product.base_sell_price if product else 10
    return base * 5


def process_buy_animal(
    action: dict,
    world_state: dict,
    catalog: GameContentCatalog,
    tick_id: int,
) -> dict | None:
    player_id = action.get("player_id")
    payload = action.get("payload") or {}
    tile_id = payload.get("tile_id")
    animal_id = payload.get("animal_id") or DEFAULT_ANIMAL_ID

    animal = catalog.animals.get(animal_id)
    if animal is None:
        return make_event(tick_id, "ANIMAL_PURCHASE_FAILED", {
            "player_id": player_id,
            "animal_id": animal_id,
            "reason": "UNKNOWN_ANIMAL",
        })

    player = find_player(world_state, player_id)
    if player is None:
        return contract_error(tick_id, "MISSING_FIELD", f"Player not found: {player_id}", "player_id")

    tile = find_tile(world_state, tile_id)
    if tile is None:
        return make_event(tick_id, "ANIMAL_PURCHASE_FAILED", {
            "player_id": player_id,
            "tile_id": tile_id,
            "reason": "UNKNOWN_TILE",
        })

    if tile.get("owner_player_id") != player_id:
        return make_event(tick_id, "ANIMAL_PURCHASE_FAILED", {
            "player_id": player_id,
            "tile_id": tile_id,
            "reason": "NOT_OWNER",
        })

    if tile.get("zone_type") != "ANIMAL":
        return make_event(tick_id, "ANIMAL_PURCHASE_FAILED", {
            "player_id": player_id,
            "tile_id": tile_id,
            "reason": "WRONG_ZONE",
        })

    if tile.get("occupant_type") not in (None, "EMPTY"):
        return make_event(tick_id, "ANIMAL_PURCHASE_FAILED", {
            "player_id": player_id,
            "tile_id": tile_id,
            "reason": "TILE_OCCUPIED",
        })

    price = animal_buy_price(catalog, animal)
    available = player.get("money_bestiki", 0)
    if available < price:
        return make_event(tick_id, "ANIMAL_PURCHASE_FAILED", {
            "player_id": player_id,
            "animal_id": animal_id,
            "reason": "NOT_ENOUGH_MONEY",
            "required": price,
            "available": available,
        })

    player["money_bestiki"] = available - price
    tile["occupant_type"] = "ANIMAL"
    tile["occupant_id"] = animal_id
    tile["health"] = 100
    tile["production_elapsed_sec"] = 0
    tile["production_interval_sec"] = animal.production_interval_sec
    tile["product_id"] = animal.product_id
    tile["hunger_ticks"] = 0

    log.info("BUY_ANIMAL ok player=%s animal=%s tile=%s paid=%s", player_id, animal_id, tile_id, price)
    return make_event(tick_id, "ANIMAL_PURCHASED", {
        "player_id": player_id,
        "tile_id": tile_id,
        "animal_id": animal_id,
        "total_paid": price,
    })
