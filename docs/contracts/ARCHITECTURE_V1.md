# ARCHITECTURE V1

## 1) Назначение

Документ фиксирует модульные границы и зоны ответственности для первой интегрируемой версии проекта (`v1`).

Цели:

- исключить пересечение ответственности между разработчиками,
- обеспечить независимую параллельную разработку,
- дать единый источник правды перед реализацией.

---

## 2) Версия и совместимость

- `architecture_version`: `v1`
- Дата фиксации: `2026-05-27`
- Совместимость: все новые ТЗ должны ссылаться на `v1` до появления `v2`.

Изменения, ломающие границы или контракты, допускаются только через новую версию (`v2+`) и запись в `DECISIONS.md`.

---

## 3) Модули и владельцы

### `web/` (owner: `NIKITA`) — основной клиент (в разработке)

- Svelte SPA (lobby/match/HUD),
- обработка input, DnD, hotkeys,
- HTTP API + poll sync + optimistic UI,
- рендер `world_state` с сервера.

Документация: [`docs/frontend/README.md`](../frontend/README.md).

### `client/` (owner: `NIKITA`) — legacy

- pygame UI (reference до parity с `web/`),
- те же контракты `PlayerAction` / `SyncResponse`, что и веб-клиент.

### `server/` (owner: `NIKITA`)

- создание/управление матчами,
- `join by code`,
- прием `PlayerAction`,
- серверный тик и authoritative state,
- проверка победного условия.

### `db/` (owner: `NIKITA`)

- SQLite schema и seed,
- загрузка декларативного контента,
- доступ к рецептам/сущностям/коэффициентам.

### `engine_cpp/` (owner: `SANYA`)

- C++ simulation core,
- детерминированная обработка тика,
- pybind11 binding,
- экспорт API `simulate_tick`.

### `shared/` (owner: `NIKITA_LEAD`)

- общие DTO/контракты,
- enum action/event type,
- версия контракта и совместимость.

### `docs/contracts/` (owner: `NIKITA_LEAD`)

- архитектурные и data/API-контракты,
- примеры payload,
- правила версионирования.

---

## 4) Правила границ (must-follow)

1. Клиент не вычисляет итоговое состояние мира.
2. Сервер не рендерит UI и не содержит pygame-зависимостей.
3. C++ модуль не работает с сетью и БД напрямую.
4. Клиент отправляет команды, сервер отправляет состояние/события.
5. Любая межмодульная интеграция строится через контракт `v1` из `GAME_CONTRACTS_V1.md`.
6. Временные stubs обязаны повторять интерфейс реального модуля.

---

## 5) Жизненный цикл тика

1. Клиенты отправляют `PlayerAction`.
2. Сервер собирает actions в очередь текущего тика.
3. Сервер формирует `TickInput` и вызывает `engine_core.simulate_tick`.
4. Движок возвращает `TickResult`.
5. Сервер обновляет authoritative `WorldState`.
6. Сервер рассылает `StateSyncEvent` + события игрокам.
7. Сервер проверяет победные условия.

---

## 6) Интеграционные зависимости v1

- `server` зависит от:
    - `db` (чтение контента),
    - `engine_cpp` или `engine_stub` (simulate tick),
    - `shared` (контракты).
- `client` зависит от:
    - `server` API и событий,
    - `shared` (форматы сообщений).
- `engine_cpp` зависит от:
    - `shared` контрактной модели тика (логически, через согласованный формат).

---

## 7) Критерии готовности архитектурного checkpoint

Checkpoint `Module Boundaries Approved` считается пройденным, если:

- для каждого модуля указан owner,
- зафиксированы запреты и границы ответственности,
- серверный тик-поток описан end-to-end,
- команда подтверждает, что может начать реализацию без доп. архитектурных уточнений.

---

## 8) Реализация v1 (снимок 2026-05-28)

Соответствие контрактам в коде:

| Модуль | Entry / API | Контракты |
|--------|-------------|-----------|
| `web/` | `npm run dev` → proxy `/api` → сервер | те же HTTP endpoints, `docs/frontend/` |
| `client/` | `py -m client` → HTTP к серверу | `ClientActionEnvelope`, poll sync (legacy) |
| `server/` | `py -m server` → `server/http_api.py` | create/join/start/action/sync |
| `server/` tick | `match.process_tick` → `engine_core` или stub | `TickInput`, `TickResult` |
| `db/` | `load_catalog()` при старте сервера | декларативный контент |
| `shared/` | `contracts.py` | зеркало `GAME_CONTRACTS_V1` |

Сеть MVP: HTTP JSON, порт `8765`, сервер `0.0.0.0` (см. `DEC-010` в `DECISIONS.md`).

Не в зоне v1-реализации: WebSocket. `PLACE_ON_TILE`: движок (`SANYA`) + обогащение на сервере (`NIKITA`, `server/002`).
