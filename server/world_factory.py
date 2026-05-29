"""Build initial WorldState dict for a new match."""

import copy
import json
import os

from db.loader import GameContentCatalog
from server.plant_util import resolve_plant_id

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE_WORLD = os.path.join(ROOT, "fixtures", "world_state", "minimal_world.json")


def _load_fixture_template() -> dict:
    with open(FIXTURE_WORLD, "r", encoding="utf-8") as f:
        return json.load(f)


def create_initial_world(
        match_id: str,
        players: list[tuple[str, str]],
        catalog: GameContentCatalog,
) -> dict:
    """
    players: list of (player_id, display_name)
    Each player gets a farm slice based on minimal_world fixture layout.
    """
    template = _load_fixture_template()
    win_product = catalog.default_win_product_id()
    starter_inventory = [
        {"product_id": "wheat_seed", "amount": 3},
        {"product_id": "corn_seed", "amount": 1},
        {"product_id": "potato_seed", "amount": 1},
        {"product_id": "tomato_seed", "amount": 1},
        {"product_id": "carrot_seed", "amount": 1},
        {"product_id": "flour", "amount": 1},
        {"product_id": "feed", "amount": 3},
    ]

    world_players = []
    all_tiles = []
    all_factories = []

    for index, (player_id, display_name) in enumerate(players):
        prefix = f"p{index + 1}"
        money = 120

        world_players.append({
            "player_id": player_id,
            "display_name": display_name,
            "money_bestiki": money,
            "inventory": copy.deepcopy(starter_inventory),
            "status_effects": [],
        })

        for tile in template["map"]["tiles"]:
            tile_copy = copy.deepcopy(tile)
            tile_copy["tile_id"] = f"{prefix}_{tile['tile_id']}"
            tile_copy["owner_player_id"] = player_id
            if tile_copy.get("occupant_type") == "PLANT" and tile_copy.get("occupant_id"):
                tile_copy["occupant_id"] = resolve_plant_id(tile_copy["occupant_id"])
            elif tile_copy.get("occupant_id"):
                tile_copy["occupant_id"] = f"{prefix}_{tile_copy['occupant_id']}"
            all_tiles.append(tile_copy)

        for factory in template["factories"]:
            factory_copy = copy.deepcopy(factory)
            factory_copy["factory_id"] = f"{prefix}_{factory['factory_id']}"
            factory_copy["owner_player_id"] = player_id
            all_factories.append(factory_copy)

    width = template["map"]["width"]
    height = template["map"]["height"] * max(len(players), 1)

    return {
        "contract_version": "v1",
        "match_id": match_id,
        "tick_id": 0,
        "players": world_players,
        "map": {
            "width": width,
            "height": height,
            "tiles": all_tiles,
        },
        "factories": all_factories,
        "win_condition": {
            "condition_type": "FIRST_PRODUCT",
            "target_product_id": win_product,
            "winner_player_id": None,
        },
    }
