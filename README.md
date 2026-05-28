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

## Структура репозитория (реализовано)

| Путь                | Зона                 | Содержимое                                                  |
|---------------------|----------------------|-------------------------------------------------------------|
| `client/`           | `NIKITA`             | pygame lobby/match, HTTP-клиент, poll `StateSync`           |
| `server/`           | `NIKITA`             | HTTP API, матчи, tick loop, победа                          |
| `db/`               | `NIKITA`             | `schema.sql`, `seed_minimal.sql`, `loader.py`, `pricing.py` |
| `shared/`           | `NIKITA_LEAD`        | Python DTO контрактов v1                                    |
| `engine_cpp/`       | `SANYA`              | C++ `simulate_tick` + pybind11                              |
| `engine_core_stub/` | `SANYA` / интеграция | Python-заглушка движка                                      |
| `fixtures/`         | общая                | `world_state/`, `actions/`                                  |
| `tools/`            | общая                | `init_db.py`, smoke/integration-тесты                       |

---

## Быстрый старт

### 1. Один раз: БД и зависимости

```bash
pip install -r client/requirements.txt
py tools/init_db.py --seed
```

### 2. Сервер

```bash
py -m server
```

По умолчанию: `http://0.0.0.0:8765` (localhost + LAN). В логе — IP для гостей в сети.

### 3. Клиент

```bash
py -m client
```

В lobby: **Server IP**, **Port**, **Connect**, затем Create/Join и (хост) Start.

CLI для гостя в LAN: `py -m client --host 192.168.x.x --port 8765`

### Автотесты (без pygame-окна)

```bash
py tools/verify_seed.py
py tools/test_db_pricing.py
py tools/test_server_flow.py
py tools/test_client_net.py    # нужен запущенный сервер
```

---

## HTTP API (контракт v1)

Базовый URL: `http://<host>:8765`

| Метод | Путь                                        | Назначение                               |
|-------|---------------------------------------------|------------------------------------------|
| GET   | `/api/health`                               | проверка сервера                         |
| POST  | `/api/matches/create`                       | создать матч (`player_name` опционально) |
| POST  | `/api/matches/join`                         | `{join_code, player_name}`               |
| POST  | `/api/matches/start`                        | `{match_id}`                             |
| POST  | `/api/matches/action`                       | `ClientActionEnvelope`                   |
| GET   | `/api/matches/{match_id}/sync?since_tick=0` | `StateSyncEvent`                         |

---

## Управление в матче (клиент)

- клик — выбор своей клетки
- **W** — полив (`WATER_PLANT`)
- **T** — посадка (`PLACE_ON_TILE`; в движке пока может быть ошибка — зона `SANYA`)
- **B** — запуск рецепта победы на заводе (`START_RECIPE`)
- **Esc** — вернуться в lobby

Победа: первый игрок с целевым продуктом в инвентаре (в seed — `bread`).

---

## Мультиплеер по сети (LAN)

| Роль  | Действие                                                                    |
|-------|-----------------------------------------------------------------------------|
| Хост  | `py -m server`, Create → Start, передать **join code** и **LAN IP** из лога |
| Гость | `py -m client`, Server IP = IP хоста, Connect → Join                        |

Переменные окружения:

| Переменная              | Сторона         | По умолчанию                    |
|-------------------------|-----------------|---------------------------------|
| `FARM_WARS_HOST`        | сервер          | `0.0.0.0`                       |
| `FARM_WARS_PORT`        | сервер / клиент | `8765`                          |
| `FARM_WARS_TICK_SEC`    | сервер          | `1.0`                           |
| `FARM_WARS_SERVER_HOST` | клиент          | `127.0.0.1`                     |
| `FARM_WARS_SERVER_PORT` | клиент          | `8765`                          |
| `FARM_WARS_SERVER`      | клиент          | полный URL (`http://host:port`) |
| `FARM_WARS_DB_PATH`     | сервер          | `db/farm_wars.db`               |

На хосте: разрешить входящие подключения в брандмауэре Windows для Python на порту `8765`.

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

**Сделано (`NIKITA` / `SANYA`):**

- SQLite schema + seed + загрузчик на сервере (`db/001` — DONE)
- Server join/tick/win + HTTP API + LAN (`server/001` — DONE)
- Client pygame lobby/match + IP в lobby (`client/001` — DONE)
- C++ engine base + stub (`engine_cpp/001` — DONE)

**Дальше:**

1. Закрыть sign-off архитектуры `v1` (`NIKITA_LEAD`)
2. Вертикальный срез end-to-end (`gameplay/001` — `NIKITA_LEAD`)
3. `PLACE_ON_TILE` и расширение симуляции (`SANYA`)
4. События / PvP из декларативной БД в геймплей

---

## Критерий готовности MVP

| Критерий                                      | Статус                                       |
|-----------------------------------------------|----------------------------------------------|
| Клиент и сервер на Windows                    | есть                                         |
| Multiplayer 2+ по join code (localhost + LAN) | есть                                         |
| Матч до победы по целевому продукту           | есть (рецепт → инвентарь → `MATCH_FINISHED`) |
| Контент из SQLite                             | есть (базовый seed)                          |
| Полный контент (10 растений, PvP в матче)     | впереди                                      |
| `PLACE_ON_TILE` в движке                      | впереди (`SANYA`)                            |
