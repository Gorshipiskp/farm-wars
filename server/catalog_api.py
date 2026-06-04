"""Catalog snapshot for client UI (prices from SQLite, not hardcoded)."""

from __future__ import annotations

from db.loader import GameContentCatalog
from server.animals import animal_buy_price

# Extra shop items (not grown on farm).
SHOP_EXTRA_PRODUCT_IDS = ("flour",)


def catalog_for_client(catalog: GameContentCatalog) -> dict:
    products = []
    seen: set[str] = set()
    for plant_id in sorted(catalog.plants.keys()):
        plant = catalog.plants[plant_id]
        seed = catalog.products.get(plant.seed_product_id)
        if seed is None:
            continue
        seen.add(plant.seed_product_id)
        products.append({
            "product_id": plant.seed_product_id,
            "price": seed.base_sell_price,
            "base_sell_price": seed.base_sell_price,
            "display_name": seed.display_name,
            "category": seed.category,
            "plant_id": plant_id,
        })
    for product_id in SHOP_EXTRA_PRODUCT_IDS:
        if product_id in seen:
            continue
        product = catalog.products.get(product_id)
        if product is None:
            continue
        products.append({
            "product_id": product_id,
            "price": product.base_sell_price,
            "base_sell_price": product.base_sell_price,
            "display_name": product.display_name,
            "category": product.category,
        })

    seen_products = {p["product_id"] for p in products}
    for product_id, product in sorted(catalog.products.items()):
        if product_id in seen_products:
            continue
        if product.category not in ("RAW", "PROCESSED"):
            continue
        products.append({
            "product_id": product_id,
            "price": product.base_sell_price,
            "base_sell_price": product.base_sell_price,
            "display_name": product.display_name,
            "category": product.category,
        })

    plants = []
    for plant_id, plant in sorted(catalog.plants.items()):
        seed = catalog.products.get(plant.seed_product_id)
        crop = catalog.products.get(plant.product_id)
        plants.append({
            "plant_id": plant_id,
            "product_id": plant.product_id,
            "seed_product_id": plant.seed_product_id,
            "display_name": plant.display_name,
            "seed_display_name": seed.display_name if seed else plant.seed_product_id,
            "crop_display_name": crop.display_name if crop else plant.product_id,
        })

    animals = []
    for animal_id, animal in sorted(catalog.animals.items()):
        animals.append({
            "animal_id": animal_id,
            "product_id": animal.product_id,
            "price": animal_buy_price(catalog, animal),
            "display_name": animal.display_name,
        })

    sabotages = []
    for sabotage_id, sab in sorted(catalog.sabotages.items()):
        sabotages.append({
            "sabotage_id": sabotage_id,
            "price": sab.cost_bestiki,
            "display_name": sab.display_name,
            "sabotage_type": sab.sabotage_type,
            "is_hidden": bool(sab.is_hidden),
        })

    recipes = []
    for recipe_id, recipe in sorted(catalog.recipes.items()):
        out = catalog.products.get(recipe.output_product_id)
        recipes.append({
            "recipe_id": recipe_id,
            "building_type": recipe.building_type,
            "output_product_id": recipe.output_product_id,
            "output_display_name": out.display_name if out else recipe.output_product_id,
            "production_time_sec": recipe.production_time_sec,
            "ingredients": [
                {"product_id": ing.product_id, "amount": ing.amount}
                for ing in recipe.ingredients
            ],
        })

    return {
        "products": products,
        "plants": plants,
        "animals": animals,
        "sabotages": sabotages,
        "recipes": recipes,
        "win_product_id": None,
        "win_product_note": "Цель матча выбирается случайно при создании комнаты (см. roster).",
    }
