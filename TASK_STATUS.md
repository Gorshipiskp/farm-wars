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
| `docs/specs/server/001.NIKITA.SERVER_MATCH_JOIN_AND_TICK_LOOP.md`           | `NIKITA`      | `Win Condition Approved`        | `DONE`      | Нет                                  | 2026-05-28           |
| `docs/specs/client/001.NIKITA.CLIENT_PYGAME_CORE_AND_MATCH_UI.md`           | `NIKITA`      | `UX Stability Approved`         | `DONE`      | Нет                                  | 2026-05-28           |
| `docs/specs/gameplay/001.NIKITA_LEAD.VERTICAL_SLICE_PLAYABLE_MATCH_V1.md`   | `NIKITA_LEAD` | `Integration Baseline Approved` | `PLANNED`   | Зависит от client/server/db baseline | 2026-05-27           |

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
