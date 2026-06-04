"""
Per-match win targets: random choice among harder crafted products.
"""

from __future__ import annotations

import hashlib
import os
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from db.loader import GameContentCatalog, Recipe

# Easiest goal — excluded from random pool (still allowed via FARM_WARS_WIN_PRODUCT).
_EASY_PRODUCTS = frozenset({"bread"})

# Extra weight for especially long chains (animals + multiple crops + factory).
_EXTRA_WEIGHT = {
    "cake": 4,
    "sausage": 4,
    "pie": 3,
    "soup": 3,
    "cheese": 2,
    "omelette": 2,
    "butter": 1,
}


def _rng_for_match(match_id: str, join_code: str) -> random.Random:
    seed = hashlib.sha256(f"{match_id}:{join_code}".encode("utf-8")).hexdigest()
    return random.Random(int(seed[:16], 16))


def _needs_animal_product(catalog: GameContentCatalog, recipe: Recipe) -> bool:
    animal_products = {a.product_id for a in catalog.animals.values()}
    for ing in recipe.ingredients:
        if ing.product_id in animal_products:
            return True
    return False


def _recipe_weight(catalog: GameContentCatalog, recipe: Recipe) -> int:
    if recipe.output_product_id in _EASY_PRODUCTS:
        return 0
    base = 1 + len(recipe.ingredients)
    if _needs_animal_product(catalog, recipe):
        base += 2
    if recipe.building_type == "MEAT":
        base += 1
    base += _EXTRA_WEIGHT.get(recipe.output_product_id, 0)
    return base


def eligible_win_targets(catalog: GameContentCatalog) -> list[tuple[str, int]]:
    """(product_id, weight) for random selection."""
    by_output: dict[str, int] = {}
    for recipe in catalog.recipes.values():
        w = _recipe_weight(catalog, recipe)
        if w <= 0:
            continue
        pid = recipe.output_product_id
        by_output[pid] = max(by_output.get(pid, 0), w)
    return sorted(by_output.items(), key=lambda x: x[0])


def pick_match_win_target(
    catalog: GameContentCatalog,
    match_id: str,
    join_code: str,
) -> str:
    """
    Pick a win target for one match.

    FARM_WARS_WIN_PRODUCT forces a specific product.
    FARM_WARS_RANDOM_WIN=0 disables random (always bread) for tests.
    """
    override = os.environ.get("FARM_WARS_WIN_PRODUCT", "").strip()
    if override:
        return override

    if os.environ.get("FARM_WARS_RANDOM_WIN", "1").strip().lower() in ("0", "false", "no"):
        return "bread"

    pool = eligible_win_targets(catalog)
    if not pool:
        return catalog.default_win_product_id()

    ids, weights = zip(*pool)
    rng = _rng_for_match(match_id, join_code)
    return rng.choices(list(ids), weights=list(weights), k=1)[0]


def recipe_hint_for_product(catalog: GameContentCatalog, product_id: str) -> str | None:
    recipe = catalog.get_recipe(product_id)
    if recipe is None:
        for r in catalog.recipes.values():
            if r.output_product_id == product_id:
                recipe = r
                break
    if recipe is None or not recipe.ingredients:
        return None

    parts: list[str] = []
    for ing in recipe.ingredients:
        prod = catalog.products.get(ing.product_id)
        name = prod.display_name if prod else ing.product_id
        parts.append(f"{name} x{ing.amount}")
    return ", ".join(parts)


def display_name_for_product(catalog: GameContentCatalog, product_id: str) -> str:
    prod = catalog.products.get(product_id)
    return prod.display_name if prod else product_id
