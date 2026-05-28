-- Farm Wars — SQLite schema v1
-- Checkpoint 1: Schema Approved (001.NIKITA.SQLITE_SCHEMA_AND_SEED_MINIMAL)
--
-- Price rule (when recipes.price_override IS NULL):
--   sum(products.base_sell_price * recipe_ingredients.amount)
--   + recipes.production_time_sec * buildings.time_coef
-- building.time_coef applies per factory type to that building's recipes.

PRAGMA
foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- Core catalog
-- ---------------------------------------------------------------------------

CREATE TABLE products
(
    product_id      TEXT PRIMARY KEY,
    display_name    TEXT    NOT NULL,
    category        TEXT    NOT NULL CHECK (category IN ('RAW', 'PROCESSED', 'SEED', 'FEED')),
    base_sell_price INTEGER NOT NULL DEFAULT 0 CHECK (base_sell_price >= 0)
);

CREATE TABLE plants
(
    plant_id             TEXT PRIMARY KEY,
    product_id           TEXT    NOT NULL REFERENCES products (product_id),
    display_name         TEXT    NOT NULL,
    growth_time_sec      INTEGER NOT NULL CHECK (growth_time_sec > 0),
    water_decay_per_tick INTEGER NOT NULL DEFAULT 1 CHECK (water_decay_per_tick >= 0),
    initial_water_level  INTEGER NOT NULL DEFAULT 50
        CHECK (initial_water_level BETWEEN 0 AND 100)
);

CREATE TABLE animals
(
    animal_id               TEXT PRIMARY KEY,
    product_id              TEXT    NOT NULL REFERENCES products (product_id),
    display_name            TEXT    NOT NULL,
    feed_product_id         TEXT REFERENCES products (product_id),
    production_interval_sec INTEGER NOT NULL CHECK (production_interval_sec > 0)
);

-- Factory types; time_coef is used in default price formula for their recipes.
CREATE TABLE buildings
(
    building_type TEXT PRIMARY KEY,
    display_name  TEXT NOT NULL,
    time_coef     REAL NOT NULL CHECK (time_coef > 0)
);

CREATE TABLE recipes
(
    recipe_id           TEXT PRIMARY KEY,
    building_type       TEXT    NOT NULL REFERENCES buildings (building_type),
    output_product_id   TEXT    NOT NULL REFERENCES products (product_id),
    production_time_sec INTEGER NOT NULL CHECK (production_time_sec > 0),
    price_override      INTEGER CHECK (price_override IS NULL OR price_override >= 0)
);

CREATE TABLE recipe_ingredients
(
    recipe_id  TEXT    NOT NULL REFERENCES recipes (recipe_id) ON DELETE CASCADE,
    product_id TEXT    NOT NULL REFERENCES products (product_id),
    amount     INTEGER NOT NULL CHECK (amount >= 1),
    PRIMARY KEY (recipe_id, product_id)
);

-- ---------------------------------------------------------------------------
-- Events and PvP (declarative content for MVP)
-- ---------------------------------------------------------------------------

CREATE TABLE random_events
(
    event_id       TEXT PRIMARY KEY,
    display_name   TEXT    NOT NULL,
    effect_type    TEXT    NOT NULL CHECK (
        effect_type IN ('DROUGHT', 'FLOOD', 'EARTHQUAKE', 'EPIDEMIC')
        ),
    duration_ticks INTEGER NOT NULL DEFAULT 10 CHECK (duration_ticks > 0),
    severity       REAL    NOT NULL DEFAULT 1.0 CHECK (severity > 0)
);

CREATE TABLE sabotages
(
    sabotage_id   TEXT PRIMARY KEY,
    display_name  TEXT    NOT NULL,
    sabotage_type TEXT    NOT NULL CHECK (
        sabotage_type IN ('MINE', 'DISEASE', 'WATER_SABOTAGE')
        ),
    cost_bestiki  INTEGER NOT NULL CHECK (cost_bestiki >= 0),
    is_hidden     INTEGER NOT NULL DEFAULT 1 CHECK (is_hidden IN (0, 1))
);

CREATE TABLE countermeasures
(
    countermeasure_id   TEXT PRIMARY KEY,
    display_name        TEXT    NOT NULL,
    countermeasure_type TEXT    NOT NULL CHECK (
        countermeasure_type IN ('PREVENTIVE', 'ACTIVE')
        ),
    cost_bestiki        INTEGER NOT NULL CHECK (cost_bestiki >= 0),
    targets_sabotage_id TEXT REFERENCES sabotages (sabotage_id)
);

-- ---------------------------------------------------------------------------
-- Indexes for server load paths
-- ---------------------------------------------------------------------------

CREATE INDEX idx_plants_product ON plants (product_id);
CREATE INDEX idx_animals_product ON animals (product_id);
CREATE INDEX idx_recipes_building ON recipes (building_type);
CREATE INDEX idx_recipes_output ON recipes (output_product_id);
CREATE INDEX idx_recipe_ingredients_product ON recipe_ingredients (product_id);
