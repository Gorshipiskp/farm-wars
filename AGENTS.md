# AGENTS.md — правила для ИИ-агентов в Farm Wars

Этот файл — **канонический** гайд для Cursor/Codex и других агентов.

---

## 1) Назначение

- предсказуемая работа ИИ по задачам команды;
- сохранение архитектурной целостности;
- обучение постановке задач через ТЗ и checkpoints.

**Приоритет документов:** [`GAME_TECH_REQUIREMENTS.md`](GAME_TECH_REQUIREMENTS.md) > этот файл > остальные спеки.

**Операционные журналы:**

- [`DECISIONS.md`](DECISIONS.md) — почему приняли решение;
- [`TASK_STATUS.md`](TASK_STATUS.md) — статусы ТЗ и checkpoints.

---

## 2) Контекст проекта

- Игра: 2D farm simulator, мультиплеер 2–4, LAN.
- Платформа: Windows (сервер + desktop; браузерный клиент в активной разработке).
- **Сервер (авторитет):** Python, SQLite, HTTP API, tick loop.
- **Симуляция тика:** C++ (`pybind11`) + зеркальный `engine_core_stub`.
- **Клиенты:**
  - **Основной (целевой):** `web/` — Svelte 5 + TypeScript + Vite SPA;
  - **Legacy:** `client/` — pygame (reference до parity).
- Контракты: [`docs/contracts/GAME_CONTRACTS_V1.md`](docs/contracts/GAME_CONTRACTS_V1.md).

### Документация веб-клиента

При задачах в `web/` читайте и обновляйте при необходимости:

| Документ | Содержание |
|----------|------------|
| [`docs/frontend/README.md`](docs/frontend/README.md) | индекс |
| [`docs/frontend/architecture.md`](docs/frontend/architecture.md) | слои, поток данных |
| [`docs/frontend/structure.md`](docs/frontend/structure.md) | дерево модулей |
| [`docs/frontend/state-and-sync.md`](docs/frontend/state-and-sync.md) | stores, sync, optimistic |
| [`docs/frontend/ui-and-input.md`](docs/frontend/ui-and-input.md) | UI, DnD, hotkeys |
| [`docs/frontend/development.md`](docs/frontend/development.md) | dev/build/LAN |

ТЗ миграции UI: [`docs/specs/client/002.NIKITA.WEB_CLIENT_SVELTE_VITE.md`](docs/specs/client/002.NIKITA.WEB_CLIENT_SVELTE_VITE.md).

---

## 3) Роли команды

| Роль | Зона |
|------|------|
| `NIKITA_LEAD` | архитектура, контракты, интеграция, приёмка |
| `NIKITA` | Python server/client/db, **web/** |
| `SANYA` | C++ engine, stub, smoke |

Если исполнитель не указан — **спросить**: `NIKITA`, `SANYA` или `NIKITA_LEAD`.

---

## 4) Рабочий цикл агента

1. Получить задачу, изучить релевантные файлы (в т.ч. frontend docs для `web/`).
2. Задать уточняющие вопросы по критичным пробелам.
3. Дождаться ответов → ТЗ в `docs/specs/<section>/` (формат ниже).
4. Реализация **по checkpoints**; после каждого — отчёт и запрос приёмки.
5. Архитектурные решения → `DECISIONS.md`; прогресс → `TASK_STATUS.md`.

**Запрещено:**

- генерировать ТЗ без фазы вопросов (если задача нетривиальна);
- молча менять контракты между слоями;
- делать всю задачу одним коммитом без checkpoint-приёмки (если в ТЗ есть checkpoints).

---

## 5) Генерация ТЗ

### Именование

`{NNN}.{DEVELOPER}.{TITLE}.md`  
Пример: `003.NIKITA.WEB_WAREHOUSE_SELL_FILTER.md`

### Размещение

`docs/specs/<section>/` — `client`, `server`, `engine_cpp`, `gameplay`, `architecture`, `db`, …

Для **веб-клиента** секция: `client/` (файлы могут ссылаться на `docs/frontend/*`).

### Обязательные секции

`Context`, `Goal`, `Scope`, `Functional Requirements`, `Non-Functional Requirements`, `Data Contracts / API Contracts`, `Implementation Plan`, `Checkpoints`, `Acceptance Criteria`, `Test Plan`.

---

## 6) Уточняющие вопросы (минимум)

- границы in/out of scope;
- исполнитель и затронутые модули;
- контракты API/событий;
- критерии приёмки;
- риски для соседних подсистем (server ↔ web ↔ engine).

---

## 7) Checkpoint-приемка

После checkpoint — короткий отчёт:

1. Что сделано.
2. Какие файлы/контракты затронуты.
3. Как проверить локально.
4. Запрос: *«Подтверди приемку checkpoint N»*.

Без явной приемки — не переходить к следующему checkpoint (если ТЗ так устроено).

Обновить `TASK_STATUS.md` после приёмки.

---

## 8) Архитектурные правила

- Python владеет orchestration и game loop на сервере.
- **Server-authoritative:** клиент шлёт actions, не финальный state.
- C++ не трогает UI и сеть.
- Контент из SQLite, не хардкод в логике (где возможно).
- Изменения Python ↔ C++ → контракт + smoke/stub parity.
- Межмодульно: `contract → fixture → stub → real integration`.
- **Web:** без дублирования серверной логики; optimistic только для UX, reconcile через `sync`.

---

## 9) Изолированная разработка

1. Зафиксировать контракт (типы, events, version).
2. Fixtures: ≥1 positive, ≥1 edge.
3. Stub соседа с тем же интерфейсом.
4. Checkpoints: Contract / Fixtures / Stub / Integration approved.
5. Не блокироваться на «ждём чужой модуль», если есть stub.

---

## 10) Качество изменений

- минимальный diff под задачу;
- читаемые имена;
- команды запуска в отчёте;
- **не коммитить** без явной просьбы пользователя;
- **не пушить** без явной просьбы.

### Интеграционные тесты (server/engine/MP)

```bash
py tools/init_db.py --seed
py tools/test_server_flow.py
py tools/test_multiplayer.py
py tools/test_pvp.py
py tools/test_vertical_slice.py
```

Мультиплеер: [`docs/specs/gameplay/009.NIKITA.MULTIPLAYER_2PLUS_VERIFICATION.md`](docs/specs/gameplay/009.NIKITA.MULTIPLAYER_2PLUS_VERIFICATION.md).

Перед `py tools/build_engine.py` на Windows — остановить сервер и клиенты (блокировка `.pyd`).

### Фронтенд

```bash
cd web && npm run check
```

Ручная проверка: сервер + `npm run dev`, два игрока в двух вкладках.

---

## 11) Итоговый отчёт задачи

1. **Result** — цель достигнута или нет.
2. **Changes** — ключевые файлы.
3. **Verification** — что запускали.
4. **Limitations** — что не сделано.
5. **Next Step** — логичное продолжение.

---

## 12) Стартовый промпт

```
Работай по AGENTS.md и GAME_TECH_REQUIREMENTS.md.
Для web/ — docs/frontend/README.md и связанные файлы.
Сначала изучи релевантный код и задай уточняющие вопросы.
После ответов создай ТЗ в docs/specs/<section>/ как NNN.DEVELOPER.TITLE.md.
Выполняй по checkpoints; после каждого запроси приемку.
```

---

## 13) Критерий успеха

- понятные ТЗ и checkpoints;
- архитектура не расползается;
- команда может продолжить после агента;
- web остаётся тонким клиентом с документированным sync/UI.
