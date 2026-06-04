"""
Load declarative game content from SQLite.

Used by server on startup; interface is stable for match/tick logic later.
"""

import os
import sqlite3
from dataclasses import dataclass, field

from shared.paths import default_db_path

DEFAULT_DB_PATH = default_db_path()


@dataclass(frozen=True)
class Product:
    product_id: str
    display_name: str
    category: str
    base_sell_price: int


@dataclass(frozen=True)
class Plant:
    plant_id: str
    product_id: str
    seed_product_id: str
    display_name: str
    growth_time_sec: int
    water_decay_per_tick: int
    initial_water_level: int


@dataclass(frozen=True)
class Animal:
    animal_id: str
    product_id: str
    display_name: str
    feed_product_id: str | None
    production_interval_sec: int


@dataclass(frozen=True)
class Building:
    building_type: str
    display_name: str
    time_coef: float


@dataclass(frozen=True)
class RecipeIngredient:
    product_id: str
    amount: int


@dataclass(frozen=True)
class Recipe:
    recipe_id: str
    building_type: str
    output_product_id: str
    production_time_sec: int
    price_override: int | None
    ingredients: tuple[RecipeIngredient, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RandomEvent:
    event_id: str
    display_name: str
    effect_type: str
    duration_ticks: int
    severity: float


@dataclass(frozen=True)
class Sabotage:
    sabotage_id: str
    display_name: str
    sabotage_type: str
    cost_bestiki: int
    is_hidden: bool


@dataclass(frozen=True)
class Countermeasure:
    countermeasure_id: str
    display_name: str
    countermeasure_type: str
    cost_bestiki: int
    targets_sabotage_id: str | None


@dataclass
class GameContentCatalog:
    """In-memory snapshot of DB content for one server process."""

    products: dict[str, Product]
    plants: dict[str, Plant]
    animals: dict[str, Animal]
    buildings: dict[str, Building]
    recipes: dict[str, Recipe]
    random_events: dict[str, RandomEvent]
    sabotages: dict[str, Sabotage]
    countermeasures: dict[str, Countermeasure]

    def get_recipe(self, recipe_id: str) -> Recipe | None:
        return self.recipes.get(recipe_id)

    def get_building(self, building_type: str) -> Building | None:
        return self.buildings.get(building_type)

    def default_win_product_id(self) -> str:
        """
        Match win target from env.

        FARM_WARS_WIN_PRODUCT — override (e.g. bread, cake).
        FARM_WARS_DEV=1 — default cake (harder to finish while testing animals).
        """
        override = os.environ.get("FARM_WARS_WIN_PRODUCT", "").strip()
        if override:
            return override
        dev = os.environ.get("FARM_WARS_DEV", "").lower() in ("1", "true", "yes")
        if dev:
            return "cake"
        return "bread"


def _row_product(row) -> Product:
    return Product(
        product_id=row["product_id"],
        display_name=row["display_name"],
        category=row["category"],
        base_sell_price=row["base_sell_price"],
    )


def load_catalog(db_path: str | None = None) -> GameContentCatalog:
    path = db_path or os.environ.get("FARM_WARS_DB_PATH", DEFAULT_DB_PATH)
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Database not found: {path}. Run: py tools/init_db.py --seed"
        )

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        products = {
            r["product_id"]: _row_product(r)
            for r in conn.execute("SELECT * FROM products ORDER BY product_id")
        }

        plants = {
            r["plant_id"]: Plant(
                plant_id=r["plant_id"],
                product_id=r["product_id"],
                seed_product_id=r["seed_product_id"],
                display_name=r["display_name"],
                growth_time_sec=r["growth_time_sec"],
                water_decay_per_tick=r["water_decay_per_tick"],
                initial_water_level=r["initial_water_level"],
            )
            for r in conn.execute("SELECT * FROM plants ORDER BY plant_id")
        }

        animals = {
            r["animal_id"]: Animal(
                animal_id=r["animal_id"],
                product_id=r["product_id"],
                display_name=r["display_name"],
                feed_product_id=r["feed_product_id"],
                production_interval_sec=r["production_interval_sec"],
            )
            for r in conn.execute("SELECT * FROM animals ORDER BY animal_id")
        }

        buildings = {
            r["building_type"]: Building(
                building_type=r["building_type"],
                display_name=r["display_name"],
                time_coef=r["time_coef"],
            )
            for r in conn.execute("SELECT * FROM buildings ORDER BY building_type")
        }

        recipe_rows = {
            r["recipe_id"]: r
            for r in conn.execute("SELECT * FROM recipes ORDER BY recipe_id")
        }
        ingredients_by_recipe: dict[str, list[RecipeIngredient]] = {
            rid: [] for rid in recipe_rows
        }
        for row in conn.execute(
                "SELECT recipe_id, product_id, amount FROM recipe_ingredients "
                "ORDER BY recipe_id, product_id"
        ):
            ingredients_by_recipe[row["recipe_id"]].append(
                RecipeIngredient(product_id=row["product_id"], amount=row["amount"])
            )

        recipes = {}
        for recipe_id, row in recipe_rows.items():
            recipes[recipe_id] = Recipe(
                recipe_id=recipe_id,
                building_type=row["building_type"],
                output_product_id=row["output_product_id"],
                production_time_sec=row["production_time_sec"],
                price_override=row["price_override"],
                ingredients=tuple(ingredients_by_recipe.get(recipe_id, [])),
            )

        random_events = {
            r["event_id"]: RandomEvent(
                event_id=r["event_id"],
                display_name=r["display_name"],
                effect_type=r["effect_type"],
                duration_ticks=r["duration_ticks"],
                severity=r["severity"],
            )
            for r in conn.execute("SELECT * FROM random_events ORDER BY event_id")
        }

        sabotages = {
            r["sabotage_id"]: Sabotage(
                sabotage_id=r["sabotage_id"],
                display_name=r["display_name"],
                sabotage_type=r["sabotage_type"],
                cost_bestiki=r["cost_bestiki"],
                is_hidden=bool(r["is_hidden"]),
            )
            for r in conn.execute("SELECT * FROM sabotages ORDER BY sabotage_id")
        }

        countermeasures = {
            r["countermeasure_id"]: Countermeasure(
                countermeasure_id=r["countermeasure_id"],
                display_name=r["display_name"],
                countermeasure_type=r["countermeasure_type"],
                cost_bestiki=r["cost_bestiki"],
                targets_sabotage_id=r["targets_sabotage_id"],
            )
            for r in conn.execute(
                "SELECT * FROM countermeasures ORDER BY countermeasure_id"
            )
        }

        return GameContentCatalog(
            products=products,
            plants=plants,
            animals=animals,
            buildings=buildings,
            recipes=recipes,
            random_events=random_events,
            sabotages=sabotages,
            countermeasures=countermeasures,
        )
    finally:
        conn.close()
