"""
Recipe price calculation for declarative content.

When price_override IS NULL:
    sum(ingredient.base_sell_price * amount) + production_time_sec * building.time_coef
"""

from db.loader import Building, GameContentCatalog, Product, Recipe


def calculate_recipe_price(
        recipe: Recipe,
        products: dict[str, Product],
        buildings: dict[str, Building],
) -> int:
    """
    Return sell price for a recipe output.

    Uses price_override when set; otherwise applies default formula with
    the recipe building's time_coef.
    """
    if recipe.price_override is not None:
        return recipe.price_override

    building = buildings.get(recipe.building_type)
    if building is None:
        raise KeyError(f"Unknown building_type: {recipe.building_type}")

    ingredient_cost = 0
    for ing in recipe.ingredients:
        product = products.get(ing.product_id)
        if product is None:
            raise KeyError(f"Unknown product_id in recipe: {ing.product_id}")
        ingredient_cost += product.base_sell_price * ing.amount

    time_cost = int(recipe.production_time_sec * building.time_coef)
    return ingredient_cost + time_cost


def calculate_recipe_price_from_catalog(
        recipe_id: str, catalog: GameContentCatalog
) -> int:
    recipe = catalog.get_recipe(recipe_id)
    if recipe is None:
        raise KeyError(f"Unknown recipe_id: {recipe_id}")
    return calculate_recipe_price(recipe, catalog.products, catalog.buildings)
