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

| ТЗ                                                                          | Ответственный | Текущий checkpoint              | Статус    | Блокеры                              | Последнее обновление |
|-----------------------------------------------------------------------------|---------------|---------------------------------|-----------|--------------------------------------|----------------------|
| `docs/specs/architecture/001.NIKITA_LEAD.ARCHITECTURE_CONTRACTS_V1.md`      | `NIKITA_LEAD` | `Module Boundaries Approved`    | `PLANNED` | Нет                                  | 2026-05-27           |
| `docs/specs/architecture/002.NIKITA_LEAD.CONTRACT_FIXTURE_STUB_WORKFLOW.md` | `NIKITA_LEAD` | `Artifacts Layout Approved`     | `PLANNED` | Нет                                  | 2026-05-27           |
| `docs/specs/db/001.NIKITA.SQLITE_SCHEMA_AND_SEED_MINIMAL.md`                | `NIKITA`      | `Schema Approved`               | `PLANNED` | Нет                                  | 2026-05-27           |
| `docs/specs/engine_cpp/001.SANYA.CPP_ENGINE_CORE_PYBIND_BASE.md`            | `SANYA`       | `Build Chain Approved`          | `PLANNED` | Нет                                  | 2026-05-27           |
| `docs/specs/server/001.NIKITA.SERVER_MATCH_JOIN_AND_TICK_LOOP.md`           | `NIKITA`      | `Join Flow Approved`            | `PLANNED` | Зависит от контракта `v1`            | 2026-05-27           |
| `docs/specs/client/001.NIKITA.CLIENT_PYGAME_CORE_AND_MATCH_UI.md`           | `NIKITA`      | `Lobby Flow Approved`           | `PLANNED` | Зависит от server create/join API    | 2026-05-27           |
| `docs/specs/gameplay/001.NIKITA_LEAD.VERTICAL_SLICE_PLAYABLE_MATCH_V1.md`   | `NIKITA_LEAD` | `Integration Baseline Approved` | `PLANNED` | Зависит от client/server/db baseline | 2026-05-27           |

---

## Журнал общекомандных checkpoint

Заполняется после каждой синхронизации команды.

### TEAM-CP-001 (YYYY-MM-DD)

- **Участники**: `NIKITA`, `SANYA`, `NIKITA_LEAD`
- **Сделано**:
    - TBD
- **В работе**:
    - TBD
- **Блокеры**:
    - TBD
- **Взаимная проверка кода**:
    - `NIKITA -> SANYA`: TBD
    - `SANYA -> NIKITA`: TBD
    - `NIKITA_LEAD -> all`: TBD
- **Решения/действия до следующего checkpoint**:
    - TBD
