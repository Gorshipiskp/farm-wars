# Farm Wars

Мультиплеерный 2D farm-sim проект для учебной практики, где команда разрабатывает игру через формализованный процесс
постановки задач с ИИ-агентом.

---

## Что это за проект

`Farm Wars` — соревновательная ферма, где игроки:

- выращивают растения и животных,
- перерабатывают ресурсы через заводы,
- реагируют на случайные катастрофы,
- мешают соперникам через скрытые саботажи,
- защищаются контрмерами,
- соревнуются за выполнение цели матча.

Ключевой критерий MVP: можно доиграть хотя бы одну полноценную партию (singleplayer и multiplayer).

---

## Техническое направление

- Платформа: Windows desktop.
- Клиент/UI: Python + `pygame`.
- Сервер и мультиплеерная логика: Python.
- Игровая симуляция: C++ модуль через `pybind11`.
- База данных: SQLite (нормализованная схема + FK).
- Мультиплеер: псевдо-реалтайм, server-authoritative, вход в матч по `join code`.

---

## Команда и зоны ответственности

- `NIKITA_LEAD` — архитектура, контракты, интеграция, приемка.
- `NIKITA` — Python client/server/network/db.
- `SANYA` — C++ simulation core + Python bindings.

---

## Основные документы проекта

- `GAME.md`  
  Концепция и идея игры, core gameplay, режимы, ценность проекта.

- `GAME_TECH_REQUIREMENTS.md`  
  Полные технические требования: архитектура, БД, сетевая модель, roadmap, DoD, изолированная разработка.

- `GUIDE_FOR_AI.md`  
  Регламент работы ИИ-агента: цикл вопросов, генерация ТЗ, checkpoint-приемка, архитектурные ограничения.

- `TZ_REQUIREMENTS.md`  
  Стандарт подготовки ТЗ: формат имени, обязательные разделы, quality-критерии, правила командных checkpoints.

- `DECISIONS.md`  
  Журнал архитектурных и процессных решений с причинами выбора и последствиями.

- `TASK_STATUS.md`  
  Единая доска статусов ТЗ и checkpoint-ов + журнал общекомандных синхронизаций.

---

## Как работает процесс с ИИ-агентом

1. Разработчик формулирует идею задачи.
2. ИИ изучает репозиторий и задает все нужные вопросы.
3. Разработчик отвечает на вопросы.
4. ИИ создает ТЗ по стандарту.
5. Работа идет по checkpoints.
6. После каждого checkpoint ИИ показывает результат и запрашивает приемку.
7. Регулярно выполняется общий командный checkpoint:
    - краткий отчет каждого в общую группу (`сделано / в работе / блокеры`),
    - взаимная проверка кода друг друга.
8. Ключевые архитектурные/процессные выборы фиксируются в `DECISIONS.md`.
9. Текущий прогресс и блокеры по ТЗ обновляются в `TASK_STATUS.md`.

---

## Стандарт именования ТЗ

Формат файла:

`NNN.DEVELOPER.TITLE.md`

Где:

- `NNN` — трехзначный индекс,
- `DEVELOPER` — `NIKITA` | `SANYA` | `NIKITA_LEAD`,
- `TITLE` — краткое имя задачи в `UPPER_SNAKE_CASE`.

Пример:

- `001.SANYA.CPP_ENGINE_CORE_PYBIND_BASE.md`

---

## Обязательные разделы любого ТЗ

1. `Context`
2. `Goal`
3. `Scope`
4. `Functional Requirements`
5. `Non-Functional Requirements`
6. `Data Contracts / API Contracts`
7. `Implementation Plan`
8. `Checkpoints`
9. `Acceptance Criteria`
10. `Test Plan`

---

## Изолированная параллельная разработка (обязательно)

Чтобы разработчики не блокировали друг друга при отсутствии "боевых" данных:

- Используется `contract-first` подход.
- Для межмодульных задач обязательны:
    - контракты,
    - fixtures,
    - stubs,
    - отдельный checkpoint интеграции с реальным модулем.
- Любая задача должна быть выполнима локально независимо от готовности соседнего компонента.

---

## Быстрый старт БД и сервера

```bash
py tools/init_db.py --seed
py tools/verify_seed.py
py tools/test_db_pricing.py
py tools/test_server_flow.py
py -m server
```

HTTP API (после `py -m server`, порт `8765`):

- `POST /api/matches/create` — создать матч (`player_name` опционально)
- `POST /api/matches/join` — `{join_code, player_name}`
- `POST /api/matches/start` — `{match_id}`
- `POST /api/matches/action` — `ClientActionEnvelope`
- `GET /api/matches/{match_id}/sync?since_tick=0` — `StateSyncEvent`

Клиент (pygame, зона `NIKITA`):

```bash
pip install -r client/requirements.txt
py -m server
py -m client
```

Управление в матче: клик по клетке, `W` полив, `T` посадка (`PLACE_ON_TILE`), `B` запуск рецепта, `Esc` в lobby.

---

## Стартовый набор критичных ТЗ уже создан

Расположение: `docs/specs/`

- `architecture/001.NIKITA_LEAD.ARCHITECTURE_CONTRACTS_V1.md`
- `architecture/002.NIKITA_LEAD.CONTRACT_FIXTURE_STUB_WORKFLOW.md`
- `db/001.NIKITA.SQLITE_SCHEMA_AND_SEED_MINIMAL.md`
- `engine_cpp/001.SANYA.CPP_ENGINE_CORE_PYBIND_BASE.md`
- `server/001.NIKITA.SERVER_MATCH_JOIN_AND_TICK_LOOP.md`
- `client/001.NIKITA.CLIENT_PYGAME_CORE_AND_MATCH_UI.md`
- `gameplay/001.NIKITA_LEAD.VERTICAL_SLICE_PLAYABLE_MATCH_V1.md`

---

## Текущий приоритет команды

1. Закрыть архитектурные контракты `v1`.
2. Поднять SQLite schema + seed minimal.
3. Собрать C++ `engine_core` с `pybind11`.
4. Реализовать server join/tick loop.
5. Реализовать клиентский lobby + match UI.
6. Собрать первый играбельный вертикальный срез до победы в матче.

---

## Критерий готовности MVP

MVP готов, если:

- на Windows запускаются клиент и сервер,
- доступны singleplayer и multiplayer (2+),
- можно сыграть полный матч до победного условия,
- работают базовые растения/животные/рецепты/заводы/события/саботажи/защиты,
- контент загружается из SQLite,
- задачи ведутся через ТЗ и checkpoints по стандартам проекта.
