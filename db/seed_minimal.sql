-- Farm Wars — game content seed (plants, animals, recipes, events, PvP)
-- plants.growth_time_sec, animals.production_interval_sec = simulation ticks
-- recipes.production_time_sec = wall-clock seconds (→ ticks in action_enricher)

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- Products
-- ---------------------------------------------------------------------------

INSERT INTO products (product_id, display_name, category, base_sell_price)
VALUES
    -- Seeds (plant only; bought in shop)
    ('wheat_seed', 'Семена пшеницы', 'SEED', 3),
    ('corn_seed', 'Семена кукурузы', 'SEED', 4),
    ('potato_seed', 'Семена картофеля', 'SEED', 3),
    ('tomato_seed', 'Семена томата', 'SEED', 5),
    ('carrot_seed', 'Семена моркови', 'SEED', 3),
    ('sunflower_seed', 'Семена подсолнечника', 'SEED', 4),
    -- RAW crops (harvest & sell)
    ('wheat', 'Пшеница', 'RAW', 5),
    ('corn', 'Кукуруза', 'RAW', 6),
    ('potato', 'Картофель', 'RAW', 4),
    ('tomato', 'Помидор', 'RAW', 7),
    ('carrot', 'Морковь', 'RAW', 5),
    ('sunflower', 'Подсолнечник', 'RAW', 6),
    ('milk', 'Молоко', 'RAW', 10),
    ('egg', 'Яйцо', 'RAW', 8),
    ('wool', 'Шерсть', 'RAW', 12),
    ('pork', 'Свинина', 'RAW', 14),
    -- Processed
    ('flour', 'Мука', 'PROCESSED', 8),
    ('bread', 'Хлеб', 'PROCESSED', 20),
    ('cake', 'Торт', 'PROCESSED', 35),
    ('cheese', 'Сыр', 'PROCESSED', 22),
    ('butter', 'Масло', 'PROCESSED', 18),
    ('sausage', 'Колбаса', 'PROCESSED', 28),
    ('pie', 'Пирог', 'PROCESSED', 32),
    ('soup', 'Суп', 'PROCESSED', 24),
    ('omelette', 'Омлет', 'PROCESSED', 26),
    -- Feed
    ('feed', 'Корм', 'FEED', 3);

-- ---------------------------------------------------------------------------
-- Plants (6)
-- ---------------------------------------------------------------------------

INSERT INTO plants (plant_id, product_id, seed_product_id, display_name,
                    growth_time_sec, water_decay_per_tick, initial_water_level)
VALUES ('wheat', 'wheat', 'wheat_seed', 'Пшеница', 400, 1, 55),
       ('corn', 'corn', 'corn_seed', 'Кукуруза', 480, 1, 45),
       ('potato', 'potato', 'potato_seed', 'Картофель', 320, 1, 60),
       ('tomato', 'tomato', 'tomato_seed', 'Помидор', 360, 1, 50),
       ('carrot', 'carrot', 'carrot_seed', 'Морковь', 340, 1, 55),
       ('sunflower', 'sunflower', 'sunflower_seed', 'Подсолнечник', 420, 1, 48);

-- ---------------------------------------------------------------------------
-- Animals (4)
-- ---------------------------------------------------------------------------

INSERT INTO animals (animal_id, product_id, display_name,
                     feed_product_id, production_interval_sec)
VALUES ('cow', 'milk', 'Корова', 'feed', 100),
       ('chicken', 'egg', 'Курица', 'feed', 80),
       ('sheep', 'wool', 'Овца', 'feed', 120),
       ('pig', 'pork', 'Свинья', 'feed', 140);

-- ---------------------------------------------------------------------------
-- Buildings
-- ---------------------------------------------------------------------------

INSERT INTO buildings (building_type, display_name, time_coef)
VALUES ('BAKERY', 'Пекарня', 2.0),
       ('DAIRY', 'Сыроварня', 1.5),
       ('MEAT', 'Мясной цех', 2.5);

-- ---------------------------------------------------------------------------
-- Recipes (8) — win target: bread by default
-- ---------------------------------------------------------------------------

INSERT INTO recipes (recipe_id, building_type, output_product_id,
                     production_time_sec, price_override)
VALUES ('bread', 'BAKERY', 'bread', 30, NULL),
       ('cake', 'BAKERY', 'cake', 65, 100),
       ('pie', 'BAKERY', 'pie', 45, NULL),
       ('soup', 'BAKERY', 'soup', 35, NULL),
       ('omelette', 'BAKERY', 'omelette', 25, NULL),
       ('cheese', 'DAIRY', 'cheese', 40, NULL),
       ('butter', 'DAIRY', 'butter', 30, NULL),
       ('sausage', 'MEAT', 'sausage', 50, NULL);

INSERT INTO recipe_ingredients (recipe_id, product_id, amount)
VALUES ('bread', 'flour', 2),
       ('bread', 'wheat', 1),
       ('cake', 'flour', 3),
       ('cake', 'milk', 2),
       ('pie', 'flour', 2),
       ('pie', 'egg', 2),
       ('pie', 'wheat', 1),
       ('soup', 'tomato', 2),
       ('soup', 'potato', 1),
       ('soup', 'carrot', 1),
       ('omelette', 'egg', 3),
       ('omelette', 'milk', 1),
       ('cheese', 'milk', 2),
       ('butter', 'milk', 1),
       ('butter', 'flour', 1),
       ('sausage', 'pork', 2),
       ('sausage', 'flour', 1);

-- ---------------------------------------------------------------------------
-- Random events
-- ---------------------------------------------------------------------------

INSERT INTO random_events (event_id, display_name, effect_type, duration_ticks, severity)
VALUES ('drought', 'Засуха', 'DROUGHT', 60, 1.0),
       ('rain', 'Дождь', 'RAIN', 48, 1.2),
       ('earthquake', 'Землетрясение', 'EARTHQUAKE', 32, 1.5),
       ('epidemic', 'Эпидемия', 'EPIDEMIC', 80, 0.8);

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
