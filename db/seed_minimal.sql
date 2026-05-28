-- Farm Wars — minimal seed for vertical slice
-- Checkpoint 2: Seed Approved (001.NIKITA.SQLITE_SCHEMA_AND_SEED_MINIMAL)
-- IDs aligned with fixtures: bread, wheat, corn, BAKERY, cake.

PRAGMA
foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- Products
-- ---------------------------------------------------------------------------

INSERT INTO products (product_id, display_name, category, base_sell_price)
VALUES ('wheat', 'Пшеница', 'RAW', 5),
       ('corn', 'Кукуруза', 'RAW', 6),
       ('potato', 'Картофель', 'RAW', 4),
       ('flour', 'Мука', 'PROCESSED', 8),
       ('bread', 'Хлеб', 'PROCESSED', 20),
       ('cake', 'Торт', 'PROCESSED', 35),
       ('milk', 'Молоко', 'RAW', 10),
       ('feed', 'Корм', 'FEED', 3);

-- ---------------------------------------------------------------------------
-- Plants (3) — plant_id matches catalog; occupant_id in world is instance id
-- ---------------------------------------------------------------------------

INSERT INTO plants (plant_id, product_id, display_name,
                    growth_time_sec, water_decay_per_tick, initial_water_level)
VALUES ('wheat', 'wheat', 'Пшеница', 120, 2, 50),
       ('corn', 'corn', 'Кукуруза', 150, 2, 40),
       ('potato', 'potato', 'Картофель', 90, 1, 60);

-- ---------------------------------------------------------------------------
-- Animals (1)
-- ---------------------------------------------------------------------------

INSERT INTO animals (animal_id, product_id, display_name,
                     feed_product_id, production_interval_sec)
VALUES ('cow', 'milk', 'Корова', 'feed', 180);

-- ---------------------------------------------------------------------------
-- Buildings — each factory has its own time_coef for price formula
-- ---------------------------------------------------------------------------

INSERT INTO buildings (building_type, display_name, time_coef)
VALUES ('BAKERY', 'Хлебопекарня', 2.0),
       ('DAIRY', 'Молочный', 1.5),
       ('MEAT', 'Мясокомбинат', 2.5);

-- ---------------------------------------------------------------------------
-- Recipes (2) — win target: bread (FIRST_PRODUCT in fixtures)
-- bread: price_override NULL -> formula uses BAKERY.time_coef
-- cake:  price_override set   -> fixed price for formula-fallback tests (CP4)
-- ---------------------------------------------------------------------------

INSERT INTO recipes (recipe_id, building_type, output_product_id,
                     production_time_sec, price_override)
VALUES ('bread', 'BAKERY', 'bread', 30, NULL),
       ('cake', 'BAKERY', 'cake', 60, 100);

INSERT INTO recipe_ingredients (recipe_id, product_id, amount)
VALUES ('bread', 'flour', 2),
       ('bread', 'wheat', 1),
       ('cake', 'flour', 3),
       ('cake', 'milk', 2);

-- ---------------------------------------------------------------------------
-- Random events (1 per effect_type for MVP catalog)
-- ---------------------------------------------------------------------------

INSERT INTO random_events (event_id, display_name, effect_type, duration_ticks, severity)
VALUES ('drought', 'Засуха', 'DROUGHT', 15, 1.0),
       ('flood', 'Наводнение', 'FLOOD', 12, 1.2),
       ('earthquake', 'Землетрясение', 'EARTHQUAKE', 8, 1.5),
       ('epidemic', 'Эпидемия', 'EPIDEMIC', 20, 0.8);

-- ---------------------------------------------------------------------------
-- Sabotages
-- ---------------------------------------------------------------------------

INSERT INTO sabotages (sabotage_id, display_name, sabotage_type, cost_bestiki, is_hidden)
VALUES ('mine_tile', 'Мина на клетке', 'MINE', 25, 1),
       ('spread_disease', 'Заражение', 'DISEASE', 30, 1),
       ('poison_water', 'Саботаж воды', 'WATER_SABOTAGE', 20, 1);

-- ---------------------------------------------------------------------------
-- Countermeasures
-- ---------------------------------------------------------------------------

INSERT INTO countermeasures (countermeasure_id, display_name, countermeasure_type,
                             cost_bestiki, targets_sabotage_id)
VALUES ('vaccine', 'Вакцинация', 'PREVENTIVE', 15, 'spread_disease'),
       ('mine_scanner', 'Сканер мин', 'ACTIVE', 20, 'mine_tile');
