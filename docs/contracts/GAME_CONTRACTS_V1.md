# GAME CONTRACTS V1

## 1) Назначение

Документ фиксирует data/API-контракты `v1` между клиентом, сервером и C++ движком.

---

## 2) Общие правила

- Все сообщения содержат `contract_version`.
- Для `v1`: `contract_version = "v1"`.
- Неизвестные поля игнорируются (forward-tolerant), отсутствующие обязательные поля -> ошибка валидации.
- Все ID и типы событий/action передаются строками.

---

## 3) Базовые типы

### `PlayerAction`

- `contract_version: string` (required)
- `player_id: string` (required)
- `action_type: string` (required)
- `payload: object` (required)
- `client_ts: number` (required, unix ms)

Примеры `action_type` для `v1`:

- `WATER_PLANT`
- `START_RECIPE`
- `PLACE_ON_TILE`
- `HARVEST_PLANT`
- `APPLY_EVENT` (сервер или тесты; `player_id` может быть `__world__`)
- `BUY_PRODUCT` (server-only; не передаётся в C++ движок)
- `BUY_ANIMAL` (server-only)
- `APPLY_SABOTAGE` (server-only PvP)
- `FEED_ANIMAL` (клиент → сервер обогащает → движок)

### `ServerEvent`

- `contract_version: string` (required)
- `event_type: string` (required)
- `payload: object` (required)
- `server_tick: number` (required)

Примеры `event_type` для `v1`:

- `PLANT_WATERED`
- `PLANT_PLACED`
- `RECIPE_STARTED`
- `RECIPE_FINISHED`
- `MATCH_FINISHED`
- `CONTRACT_ERROR`
- `PRODUCT_PURCHASED`
- `PURCHASE_FAILED`
- `RECIPE_REJECTED`
- `PLANT_HARVESTED`
- `HARVEST_FAILED`
- `PLANT_DIED`
- `EVENT_TRIGGERED`
- `ANIMAL_PURCHASED` / `ANIMAL_PURCHASE_FAILED`
- `ANIMAL_FED` / `FEED_FAILED`
- `ANIMAL_PRODUCED`
- `SABOTAGE_APPLIED` / `SABOTAGE_FAILED`

### `APPLY_EVENT` — payload (сервер → движок)

- `event_type: string` (required) — `DROUGHT`, `RAIN`, `FLOOD` (alias `RAIN`), `EARTHQUAKE`, `EPIDEMIC`

Эффекты меняют параметры симуляции (decay, время завода), не мгновенный урон по всей карте. См. `docs/specs/engine_cpp/004.SANYA.RANDOM_EVENTS.md`.

### `EVENT_TRIGGERED` — payload

- `event_type: string` (required)
- `severity: number` (optional)
- `affected_tiles: number` (optional)
- `display_name: string` (optional, для UI)

### `BUY_PRODUCT` — payload (клиент → сервер)

- `product_id: string` (required)
- `amount: number` (required, >= 1)

Обрабатывается на сервере до `simulate_tick`. Цена = `products.base_sell_price * amount`.

### `START_RECIPE` — payload (клиент → сервер)

Клиент отправляет: `{factory_id, recipe_id}`.

Сервер добавляет перед `simulate_tick`:

- `duration_sec: number` (из `recipes.production_time_sec` в SQLite)
- при несовпадении `factory.factory_type` и `recipe.building_type` → `RECIPE_REJECTED`, действие не уходит в движок

См. `docs/specs/gameplay/003.NIKITA.PLAYABLE_FARM_LOOP_V2.md`.

### `PLACE_ON_TILE` — payload для движка (после обогащения сервером)

Клиент отправляет: `{tile_id, plant_id}`.

Сервер добавляет перед `simulate_tick`:

- `initial_health: number` (default `100`)
- `initial_water_level: number` (из `plants.initial_water_level` в SQLite)
- `growth_time_sec: number` (из `plants.growth_time_sec` в SQLite)
- `water_decay_per_tick: number` (из `plants.water_decay_per_tick` в SQLite)
- `seed_product_id: string` — пакет семян в инвентаре (категория `SEED`, например `wheat_seed`)
- `crop_product_id: string` — урожай при сборе (категория `RAW`, например `wheat`)

Движок списывает `seed_product_id` из инвентаря; на клетке `occupant_id` = `crop_product_id`.

**Магазин:** покупка только семян (`*_seed`) и доп. товаров (`flour`, `feed`). **Продажа:** только `RAW` и `PROCESSED` (урожай и готовые изделия), не семена.

См. `docs/specs/engine_cpp/002.SANYA.PLACE_ON_TILE.md`, `docs/specs/server/002.NIKITA.SERVER_ENRICH_PLACE_ON_TILE.md`.

### `WATER_PLANT` — payload (клиент → движок)

- `tile_id: string` (required)

Правила в движке:
- Клетка существует, `owner_player_id == player_id` → иначе `CONTRACT_ERROR` (`INVALID_TYPE`)
- Успех: `water_level = 100`, событие `PLANT_WATERED`

См. `docs/specs/server/009.NIKITA.TILE_OWNER_VALIDATION.md`.

### `HARVEST_PLANT` — payload (клиент → движок)

- `tile_id: string` (required)

Правила в движке:
- Клетка существует, `owner_player_id == player_id`, `occupant_type == "PLANT"` → иначе `HARVEST_FAILED`
- Если есть `growth_time_sec`: `growth_elapsed_sec >= growth_time_sec` → иначе `HARVEST_FAILED` (`NOT_RIPE`)
- Если `water_level < 50` → `HARVEST_FAILED` (`NOT_READY`)
- При посадке: `water_level` грядки = `initial_water_level` из payload (cap 0–100)
- Успех: `+2` продукта в инвентарь, клетка → `EMPTY`, событие `PLANT_HARVESTED`
- `water_level` грядки не изменяется при сборе

### Пассивная фаза тика

Каждый тик движок выполняет после обработки действий:
- **Испарение**: все клетки с `water_level > 0` → `water_level -= water_decay_per_tick` (или 1 если поле отсутствует)
- **Рост**: клетки с `occupant_type == "PLANT"` и `water_level > 0` → `growth_elapsed_sec += 1`
- **Засыхание**: клетки с `occupant_type == "PLANT"` и `water_level == 0` → `health -= 10`
- **Смерть**: `health <= 0` → клетка очищается, событие `PLANT_DIED` (`reason: "DEHYDRATED"`), `water_level` сохраняется
- **Заводы**: `active_recipe_id != null` и `remaining_time_sec > 0` → `remaining_time_sec -= 1`; при достижении 0 → `RECIPE_FINISHED`, `+1` продукта, завод простаивает

---

## 4) Контракт симуляции тика

### `TickInput`

- `contract_version: string` (required)
- `tick_id: number` (required)
- `world_state: WorldState` (required)
- `actions: PlayerAction[]` (required, can be empty)

### `TickResult`

- `contract_version: string` (required)
- `tick_id: number` (required)
- `next_world_state: WorldState` (required)
- `events: ServerEvent[]` (required, can be empty)

Правила:

- `tick_id` в `TickResult` должен совпадать с входным `tick_id`.
- При одинаковом `TickInput` движок обязан вернуть одинаковый `TickResult`.

---

## 5) WorldState (минимум для v1)

### `WorldState`

- `contract_version: string` (required)
- `match_id: string` (required)
- `tick_id: number` (required)
- `players: PlayerState[]` (required)
- `map: MapState` (required)
- `factories: FactoryState[]` (required)
- `win_condition: WinConditionState` (required)

### `PlayerState`

- `player_id: string` (required)
- `display_name: string` (required)
- `money_bestiki: number` (required)
- `inventory: InventoryItem[]` (required)
- `status_effects: string[]` (optional)

### `InventoryItem`

- `product_id: string` (required)
- `amount: number` (required, >= 0)

### `MapState`

- `width: number` (required)
- `height: number` (required)
- `tiles: TileState[]` (required)

### `TileState`

- `tile_id: string` (required)
- `zone_type: string` (required, `PLANT` | `ANIMAL`)
- `owner_player_id: string` (required)
- `occupant_type: string` (optional, `PLANT` | `ANIMAL` | `EMPTY`)
- `occupant_id: string` (optional)
- `health: number` (optional)
- `water_level: number` (optional)
- `flags: string[]` (optional, например `MINED`, `INFECTED`)
- `growth_elapsed_sec: number` (optional, сколько тиков растение уже растет)
- `growth_time_sec: number` (optional, порог созревания из каталога)
- `water_decay_per_tick: number` (optional, расход воды за тик)

### `FactoryState`

- `factory_id: string` (required)
- `factory_type: string` (required)
- `owner_player_id: string` (required)
- `level: number` (required, >= 1)
- `active_recipe_id: string | null` (required)
- `remaining_time_sec: number` (required, >= 0)
- `queue: QueueItem[]` (required)

### `QueueItem`

- `recipe_id: string` (required)
- `requested_amount: number` (required, >= 1)

### `WinConditionState`

- `condition_type: string` (required, `FIRST_PRODUCT`)
- `target_product_id: string` (required)
- `winner_player_id: string | null` (required)

---

## 6) Клиент-сервер обертки

### `CreateMatchResponse`

- `contract_version: string`
- `match_id: string`
- `join_code: string`

### `JoinMatchRequest`

- `contract_version: string`
- `join_code: string`
- `player_name: string`

### `JoinMatchResponse`

- `contract_version: string`
- `match_id: string`
- `player_id: string`

### `ClientActionEnvelope`

- `contract_version: string`
- `match_id: string`
- `player_id: string`
- `action: PlayerAction`

### `StateSyncEvent`

- `contract_version: string`
- `match_id: string`
- `tick_id: number`
- `world_state: WorldState`
- `events: ServerEvent[]`

---

## 7) Ошибки контракта

Минимальный формат ошибки (`CONTRACT_ERROR`):

- `error_code: string` (`MISSING_FIELD`, `INVALID_TYPE`, `UNSUPPORTED_VERSION`)
- `message: string`
- `field_path: string | null`

Сервер обязан:

- не падать при контрактной ошибке,
- возвращать диагностируемую ошибку отправителю.

---

## 8) Правила эволюции контракта

- В рамках `v1` можно добавлять только необязательные поля.
- Удаление/переименование обязательных полей требует `v2`.
- Любое изменение контракта должно сопровождаться:
    - записью в `DECISIONS.md`,
    - обновлением связанных ТЗ,
    - обновлением fixture/stub, если они затронуты.
