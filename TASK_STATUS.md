# TASK STATUS BOARD

Общий трекер прогресса по ТЗ и checkpoint-приемке.

Назначение:

- видеть текущий статус всех критичных задач,
- синхронизировать работу `NIKITA`, `SANYA`, `NIKITA_LEAD`,
- фиксировать блокеры и результаты командных checkpoint.

Правило обновления:

- обновляется после каждого технического checkpoint,
- дополнительно обновляется после каждого общекомандного checkpoint.

---

## Статусы

- `PLANNED` — ТЗ создано, работа еще не начата.
- `IN_PROGRESS` — идет активная реализация.
- `ON_REVIEW` — ожидается приемка checkpoint/ревью.
- `BLOCKED` — есть внешний блокер.
- `DONE` — задача завершена и принята.

---

## Текущая доска

| ТЗ                                                                          | Ответственный | Текущий checkpoint              | Статус      | Блокеры                              | Последнее обновление |
|-----------------------------------------------------------------------------|---------------|---------------------------------|-------------|--------------------------------------|----------------------|
| `docs/specs/architecture/001.NIKITA_LEAD.ARCHITECTURE_CONTRACTS_V1.md`      | `NIKITA_LEAD` | `Team Sign-Off`                 | `IN_PROGRESS` | Ожидается финальное подтверждение от `NIKITA` и `SANYA` | 2026-05-27 |
| `docs/specs/architecture/002.NIKITA_LEAD.CONTRACT_FIXTURE_STUB_WORKFLOW.md` | `NIKITA_LEAD` | `Artifacts Layout Approved`     | `PLANNED`   | Нет                                  | 2026-05-27           |
| `docs/specs/db/001.NIKITA.SQLITE_SCHEMA_AND_SEED_MINIMAL.md`                | `NIKITA`      | `Formula Fallback Approved`     | `DONE`      | Нет                                | 2026-05-28 |
| `docs/specs/engine_cpp/001.SANYA.CPP_ENGINE_CORE_PYBIND_BASE.md`            | `SANYA`       | `Action Handling Approved`      | `DONE`      | Нет                                | 2026-05-27 |
| `docs/specs/engine_cpp/002.SANYA.PLACE_ON_TILE.md`                           | `SANYA`       | `Stub vs C++ Match`             | `DONE`      | Интеграция server/002 выполнена (`NIKITA`) | 2026-05-28 |
| `docs/specs/server/001.NIKITA.SERVER_MATCH_JOIN_AND_TICK_LOOP.md`           | `NIKITA`      | `Win Condition Approved`        | `DONE`      | Нет                                  | 2026-05-28           |
| `docs/specs/server/002.NIKITA.SERVER_ENRICH_PLACE_ON_TILE.md`               | `NIKITA`      | `Contracts Updated`             | `DONE`      | Нет                                  | 2026-05-28           |
| `docs/specs/client/001.NIKITA.CLIENT_PYGAME_CORE_AND_MATCH_UI.md`           | `NIKITA`      | `UX Stability Approved`         | `DONE`      | pygame legacy до web parity          | 2026-05-29           |
| `docs/specs/client/002.NIKITA.WEB_CLIENT_SVELTE_VITE.md`                     | `NIKITA`      | `Phase 0 Scaffold`              | `IN_PROGRESS` | Фаза 1 лобби parity                  | 2026-05-29           |
| `docs/specs/gameplay/001.NIKITA_LEAD.VERTICAL_SLICE_PLAYABLE_MATCH_V1.md`   | `NIKITA_LEAD` | `Demo Ready Approved`           | `DONE`      | Автотесты + `001.SIGNOFF_DEMO_SCRIPT.md` | 2026-05-28           |
| `docs/specs/server/008.NIKITA.PVP_SABOTAGE_MVP.md`                          | `NIKITA`      | `Sabotage MVP Approved`         | `DONE`      | Нет                                   | 2026-05-28           |
| `docs/specs/gameplay/003.NIKITA.PLAYABLE_FARM_LOOP_V2.md`                   | `NIKITA`      | `Mini Loop Approved`            | `DONE`      | Нет                                  | 2026-05-28           |
| `docs/specs/gameplay/004.NIKITA.HARVEST_AND_RECIPE_INGREDIENTS.md`          | `NIKITA`      | `Harvest + Ingredients Approved` | `DONE`      | Нет                                  | 2026-05-28           |
| `docs/specs/engine_cpp/003.SANYA.PLANT_TICK_GROWTH_AND_ENGINE_MECHANICS.md` | `SANYA`       | `Factory Tick Approved`         | `DONE`      | Нет                                  | 2026-05-28 |
| `docs/specs/server/003.NIKITA.SERVER_ENRICH_PLANT_GROWTH.md`                | `NIKITA`      | `Enrich Growth Fields`          | `DONE`      | Нет                                  | 2026-05-28           |
| `docs/specs/server/004.NIKITA.FIX_HARVEST_WATER_LEVEL.md`                    | `NIKITA`      | `Fix Applied`                   | `DONE`      | Нет                                  | 2026-05-28           |
| `docs/specs/server/005.NIKITA.NEXT_FEATURES_ROADMAP.md`                      | `NIKITA`      | `—`                             | `SUPERSEDED` | Заменено на `server/010`               | 2026-05-28           |
| `docs/specs/server/006.NIKITA.RANDOM_EVENTS_AND_RAIN_RENAME.md`              | `NIKITA`      | `Server Trigger Approved`       | `DONE`      | Нет                                   | 2026-05-28           |
| `docs/specs/engine_cpp/004.SANYA.RANDOM_EVENTS.md`                           | `SANYA`       | `APPLY_EVENT Approved`          | `DONE`      | Нет                                   | 2026-05-28           |
| `docs/specs/server/007.NIKITA.ANIMALS_BUY_AND_FEED.md`                        | `NIKITA`      | `Animals E2E Approved`          | `DONE`      | Нет                                   | 2026-05-28           |
| `docs/specs/engine_cpp/005.SANYA.ANIMAL_FEED_AND_MILK.md`                    | `SANYA`       | `Milk Passive Approved`         | `DONE`      | Нет                                   | 2026-05-28           |
| `docs/specs/gameplay/009.NIKITA.MULTIPLAYER_2PLUS_VERIFICATION.md`           | `NIKITA`      | `Manual LAN Approved`           | `ON_REVIEW` | Нужен ручной 3-клиентский LAN         | 2026-05-29           |
| `docs/specs/server/009.NIKITA.TILE_OWNER_VALIDATION.md`                      | `NIKITA`      | `Water Owner Check Approved`    | `DONE`      | `START_RECIPE` owner → `server/010`   | 2026-05-28           |
| `docs/specs/gameplay/010.TEAM.WORK_SUMMARY_AND_HANDOFF.md`                   | `NIKITA_LEAD` | `Handoff Published`             | `DONE`      | Нет                                   | 2026-05-29           |
| `docs/specs/engine_cpp/006.SANYA.NEXT_ENGINE_ROADMAP.md`                     | `SANYA`       | `P0+P1 Done, P2 pending`        | `IN_PROGRESS` | P2 ждёт NIKITA (контрмеры в движке)   | 2026-05-29           |
| `docs/specs/server/010.NIKITA.NEXT_SERVER_CLIENT_ROADMAP.md`               | `NIKITA`      | `P0 LAN Sign-off`               | `PLANNED`   | См. `gameplay/009`, `010.1`           | 2026-05-29           |
| `docs/specs/client/004.NIKITA.MINESWEEPER_UI.md`                             | `NIKITA`      | `—`                             | `PLANNED`   | Логика: `minesweeper/` (SANYA). Тесты: `test_minesweeper.py` | 2026-05-29           |
| `docs/specs/client/003.NIKITA.WATERFLOW_UI.md`                             | `NIKITA`      | `—`                             | `PLANNED`   | Логика: `waterflow/` (SANYA). Тесты: `test_waterflow.py`     | 2026-05-29           |

---

## Журнал общекомандных checkpoint

Заполняется после каждой синхронизации команды.

### TEAM-CP-001 (2026-05-27)

- **Участники**: `NIKITA`, `SANYA`, `NIKITA_LEAD`
- **Сделано**:
    - Подготовлены `docs/contracts/ARCHITECTURE_V1.md` и `docs/contracts/GAME_CONTRACTS_V1.md`.
    - Зафиксированы модульные границы и owner-ы.
    - Зафиксированы контракты `TickInput`, `TickResult`, `PlayerAction`, `ServerEvent`, `StateSyncEvent`.
- **В работе**:
    - Финальное подтверждение архитектурного `v1` от `NIKITA` и `SANYA`.
    - Параллельный старт задач `db/001` и `engine_cpp/001`.
- **Блокеры**:
    - Ожидается подтверждение контрактов от `NIKITA` и `SANYA`.
- **Взаимная проверка кода**:
    - `NIKITA -> SANYA`: Проверить совместимость server/client flow с `GAME_CONTRACTS_V1.md`.
    - `SANYA -> NIKITA`: Проверить, что `simulate_tick` можно реализовать без неоднозначности полей.
    - `NIKITA_LEAD -> all`: Первичный контроль полноты контрактов выполнен.
- **Решения/действия до следующего checkpoint**:
    - Выполнить первые checkpoints в `db/001` и `engine_cpp/001`.
    - После этого провести TEAM-CP-002 и подготовить запуск `server/001`.

### TEAM-CP-002 (2026-05-28)

- **Участники**: `NIKITA` (+ синхронизация для `SANYA`, `NIKITA_LEAD`)
- **Сделано (`NIKITA`)**:
    - `db/001` DONE: `schema.sql`, `seed_minimal.sql`, `loader.py`, `pricing.py`, `tools/init_db.py`.
    - `server/001` DONE: HTTP API, join/tick/engine stub, win condition, `tools/test_server_flow.py`.
    - `client/001` DONE: pygame lobby/match, 3 action types, sync poller, `tools/test_client_net.py`.
    - LAN: сервер `0.0.0.0`, клиент — поля Server IP / Port, `--host`, env-переменные.
    - Документация: `README.md`, `GAME_TECH_REQUIREMENTS.md`, ТЗ db/server/client, `DECISIONS.md`.
- **В работе**:
    - `architecture/001` — team sign-off контрактов v1.
    - `gameplay/001` — формальный вертикальный срез (`NIKITA_LEAD`).
- **Блокеры**:
    - Нет.
- **Взаимная проверка**:
    - `SANYA`: сверить, что server tick payload совместим с `simulate_tick`.
    - `NIKITA_LEAD`: принять baseline для `gameplay/001`.
- **Следующие шаги**:
    - Ручной LAN-тест: host + guest, матч до `bread`.
    - `SANYA`: `PLACE_ON_TILE` или расширение тика.

### TEAM-CP-003 (2026-05-28)

- **Участники**: `NIKITA`, `SANYA`
- **Сделано (`SANYA`)**:
    - `engine_cpp/003` DONE: harvest с проверкой зрелости, пассивная фаза (испарение/рост/смерть), фабричный тик с очередью.
    - Stub: зеркальные изменения, stub vs C++ идентичны.
    - `GAME_CONTRACTS_V1.md`: обновлён (HARVEST_PLANT, PLANT_DIED, пассивная фаза, новые поля TileState).
    - `smoke_test.py`: +20 тестов (рост, harvest, фабрики, stub actions).
- **Сделано (`NIKITA`)**:
    - `server/003` DONE: `action_enricher.py` обогащает `PLACE_ON_TILE` (`growth_time_sec`, `water_decay_per_tick`) и `START_RECIPE` (`output_product_id`).
    - `server/004` DONE: убрано обнуление `water_level` при harvest.
    - Снят блокер `engine_cpp/003`: `HARVEST_PLANT` убран из `SERVER_ONLY_ACTIONS`, harvest идёт через engine.
    - Убран `_advance_factories` из `match.py` — фабричный тик только в engine (было двойное срабатывание).
    - Очередь завода: при занятом заводе рецепт кладётся в очередь с `duration_sec` из БД, событие `RECIPE_QUEUED`.
    - Клиент:
        - Индикатор роста (зелёная полоска на тайлах), `tile_hint` с % роста.
        - События `PLANT_DIED`, `NOT_RIPE`, `RECIPE_QUEUED` с тостами.
        - Статус пекарни под кнопками + очередь в сайдбаре.
        - Окно 1280×800, логи не перекрывают магазин.
        - Кнопка «Печь» всегда крафтит хлеб (не зависит от цели победы).
        - `SHOP_HANDLER_VERSION` → `immediate_v4`.
    - `growth_time_sec` всех культур → 5 сек (для отладки).
    - `default_win_product_id()` → `"cake"` (невозможно скрафтить → игра не заканчивается).
    - Тесты обновлены под пассивную фазу engine + новый win target.
- **Блокеры**: Нет.
- **Замечание для `SANYA`**:
    - Engine в `RECIPE_FINISHED` использует `recipe_id` как `product_id`. В MVP совпадает, но правильно — брать `output_product_id` из payload START_RECIPE (enricher его уже отправляет).

### TEAM-CP-004 (2026-05-28) — задача для `SANYA`

**`engine_cpp/004` — случайные события (`APPLY_EVENT`)**

Движок должен обрабатывать новый action `APPLY_EVENT` с payload:
- `event_type: string` — `"DROUGHT"`, `"FLOOD"`, `"EARTHQUAKE"`, `"EPIDEMIC"`

Эффекты на все клетки всех игроков:
| Тип | Действие |
|---|---|
| `DROUGHT` | `water_level -= 20` (min 0) |
| `FLOOD` | `water_level += 30` (max 100) |
| `EARTHQUAKE` | `health -= 30` у всех PLANT-клеток; при `health <= 0` → `PLANT_DIED` |
| `EPIDEMIC` | `health -= 40` у всех ANIMAL-клеток |

На каждое событие — emit `EVENT_TRIGGERED` с полями: `event_type`, `severity`, `affected_tiles` (количество).

**Stub:** зеркально в `engine_core_stub/stub.py`.

**Контракты:** обновить `GAME_CONTRACTS_V1.md` — добавить `APPLY_EVENT` в список action_type и описать пассивную обработку событий.

Серверная часть (случайный выбор события раз в N тиков) — сделает `NIKITA` после приёмки.
    - Пора провести ручной LAN-тест (host + guest, матч до `bread`).

### TEAM-CP-005 (2026-05-28)

- **Сделано**:
    - `server/006` DONE: `server/random_events.py`, FLOOD→RAIN в seed/schema, триггер каждые 30 тиков (20%).
    - `engine_cpp/004` формализован, статус DONE.
    - Победа по умолчанию `bread`; `FARM_WARS_DEV=1` → `cake`.
    - Рост культур в seed: 25–35 сек (не 5 сек debug).
    - Клиент: тосты `EVENT_TRIGGERED`.
    - Контракты: `APPLY_EVENT`, `EVENT_TRIGGERED`.
    - Удалён мёртвый `server/harvest.py`.
- **В работе**: `gameplay/001` LAN sign-off, `architecture/001` team sign-off.
- **Следующее**: countermeasures, engine formalization.

### TEAM-CP-006 (2026-05-28) — животные

- **Сделано**:
    - Животные E2E: `BUY_ANIMAL`, `FEED_ANIMAL`, пассивное молоко (stub + C++).
    - `server/007`, `engine_cpp/005` DONE; `SHOP_HANDLER_VERSION` → `immediate_v5`.
    - Клиент: загон, кнопки корова/корм, корм в магазине, тосты.
    - `cow.production_interval_sec` = 12 в seed.

### TEAM-CP-007 (2026-05-28) — PvP саботаж

- **Сделано**:
    - `gameplay/001` DONE: `tools/test_vertical_slice.py`, demo script.
    - `server/008` PvP: `APPLY_SABOTAGE`, 3 типа из БД, скрытые тосты.
    - Клиент: ферма соперника, саботаж в сайдбаре, клавиша X.
    - `SHOP_HANDLER_VERSION` → `immediate_v6`.

### TEAM-CP-008 (2026-05-28) — мультиплеер 2–4, pacing, MP UX

- **Сделано**:
    - `gameplay/009`: автотест `tools/test_multiplayer.py` (join 3–4, sync, саботаж, win, owner water).
    - `server/009` DONE: `WATER_PLANT` проверяет `owner_player_id` (C++ + stub).
    - Клиент: гостевой `_poll_match_started()`, Esc → lobby без возврата в матч, `is_left_click`, вёрстка HUD.
    - Pacing: `FARM_WARS_TICK_SEC=0.25` (4 т/с), `shared/game_pacing.py`, seed длительнее (рост/хлеб/корова).
    - Геймплей: стартовый инвентарь, `SELL_PRODUCT`, `SHOP_HANDLER_VERSION` → `immediate_v7`.
    - Контракты: секция `WATER_PLANT` в `GAME_CONTRACTS_V1.md`.
    - README, SIGNOFF, DECISIONS обновлены.
- **В работе**: ручной LAN 3 окна (`gameplay/009` Manual LAN).
- **Операционно**: пересборка `.pyd` только при остановленных server/client (Windows lock).

### TEAM-CP-009 (2026-05-29) — семена/урожай, UI, стабилизация

- **Сделано**:
    - Разделение продуктов: `SEED` (`*_seed`) vs `RAW` (урожай); `plants.seed_product_id` в schema/seed.
    - Server: enricher, shop whitelist, sell RAW/PROCESSED; стартовый инвентарь — семена.
    - Engine stub + C++: списание `seed_product_id`; пересборка `engine_core`.
    - Client: панель «Ферма и склад», `ProductPicker` / `SeedPicker`, фиксы `_send_buy_animal`, MP tabs.
    - Тесты обновлены; `smoke_test`, `test_server_flow`, `test_multiplayer` — зелёные.
    - Handoff: `docs/specs/gameplay/010.TEAM.WORK_SUMMARY_AND_HANDOFF.md`.
    - Roadmap: `engine_cpp/006` (SANYA), `server/010` (NIKITA).
- **В работе**:
    - `gameplay/009` — ручной LAN 3–4 клиента.
- **Следующее**: контрмеры, solo mode.

### TEAM-CP-010 (2026-05-29) — engine_cpp/006 P0+P1 + мини-игры (SANYA)

- **Сделано (SANYA)**:
    - `engine_cpp/006` P0: `player_id` добавлен во все `CONTRACT_ERROR` (C++ + stub).
    - `engine_cpp/006` P0: проверка владельца завода в `START_RECIPE` → `RECIPE_REJECTED NOT_OWNER`.
    - `engine_cpp/006` P1: рефакторинг `find_tile`/`find_factory` → индексы (in-place мутации).
    - `minesweeper/` — чистая логика сапера: 12 тестов PASS, пресеты easy/medium/hard.
    - `waterflow/` — логика «три в ряд с вёдрами»: 10 тестов PASS.
    - ТЗ для NIKITA: `client/002` (сапер UI), `client/003` (waterflow UI).
    - `smoke_test.py`: 53+ теста PASS, stub == C++.
    - `GAME_CONTRACTS_V1.md` обновлён (пассивная фаза, новые события, APPLY_EVENT).
- **Нужно NIKITA**:
    - Прикрутить pygame-окошки к `minesweeper/` и `waterflow/`.
    - Анимации для waterflow (свайпы, падения, исчезновения).
    - При победе — снимать эффект саботажа.
    - `FARM_WARS_TICK_SEC=0.25` — engine пересобирать после остановки сервера.
- **Блокеры**: нет (со стороны SANYA всё готово).
