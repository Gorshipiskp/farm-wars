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
| `docs/specs/client/001.NIKITA.CLIENT_PYGAME_CORE_AND_MATCH_UI.md`           | `NIKITA`      | `UX Stability Approved`         | `DONE`      | Нет                                  | 2026-05-28           |
| `docs/specs/gameplay/001.NIKITA_LEAD.VERTICAL_SLICE_PLAYABLE_MATCH_V1.md`   | `NIKITA_LEAD` | `Integration Baseline Approved` | `PLANNED`   | Baseline client/server/db готов; ждёт интеграционный sign-off | 2026-05-28           |
| `docs/specs/gameplay/003.NIKITA.PLAYABLE_FARM_LOOP_V2.md`                   | `NIKITA`      | `Mini Loop Approved`            | `DONE`      | Нет                                  | 2026-05-28           |
| `docs/specs/gameplay/004.NIKITA.HARVEST_AND_RECIPE_INGREDIENTS.md`          | `NIKITA`      | `Harvest + Ingredients Approved` | `DONE`      | Нет                                  | 2026-05-28           |
| `docs/specs/engine_cpp/003.SANYA.PLANT_TICK_GROWTH_AND_ENGINE_MECHANICS.md` | `SANYA`       | `Growth Approved`               | `PLANNED`   | Ждёт обогащение payload (`server/003`) после CP1 | 2026-05-28 |
| `docs/specs/server/003.NIKITA.SERVER_ENRICH_PLANT_GROWTH.md`                | `NIKITA`      | `Enrich Growth Fields`          | `PLANNED`   | После `engine_cpp/003` CP1           | 2026-05-28           |

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
