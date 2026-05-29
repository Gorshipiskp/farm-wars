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
pip install pybind11
py tools/init_db.py --seed
```

### C++ движок (опционально)

Без сборки сервер использует Python-заглушку `engine_core_stub`. Для нативного модуля:

```bash
py tools/build_engine.py
```

| Платформа | Рекомендуемый toolchain | Требования |
|-----------|------------------------|------------|
| Windows + python.org | MSVC (по умолчанию) | [VS 2022 Build Tools](https://visualstudio.microsoft.com/downloads/) — «Desktop development with C++»; CMake из PATH или из VS |
| Windows + MinGW | GCC | [MSYS2](https://www.msys2.org/): `pacman -S mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-cmake` и **Python из MSYS2** (тот же ABI, что у g++) |
| Linux | GCC (auto) | `build-essential`, `cmake`, `pybind11` |

```bash
py tools/build_engine.py --toolchain msvc   # Visual Studio
py tools/build_engine.py --toolchain gcc    # g++ / MinGW
py tools/build_engine.py --clean            # пересобрать с нуля
```

PowerShell: `powershell -ExecutionPolicy Bypass -File tools/build_engine.ps1 -Toolchain gcc`

Артефакт ищется в `engine_cpp/build/Release/` (MSVC) или `engine_cpp/build/` (GCC).

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
py tools/test_multiplayer.py   # 2–4 игрока, sync, саботаж, owner-check
py tools/test_vertical_slice.py
py tools/test_client_net.py    # нужен запущенный сервер
```

Перед сборкой C++ остановите `py -m server` и клиенты — иначе Windows не перезапишет `engine_core*.pyd` (`Permission denied`).

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
| GET   | `/api/matches/{match_id}/roster`            | игроки в комнате (лобби)                |

---

## Управление в матче (клиент)

- клик — выбор своей клетки
- **W** — полив (`WATER_PLANT`)
- **A** / **T** — посадка (`PLACE_ON_TILE`; сервер подставляет параметры из БД)
- **H** — сбор (`HARVEST_PLANT`)
- **B** — печь хлеб (`START_RECIPE`)
- кнопки в UI — магазин, полив, посадка, сбор, печь
- **Esc** — выход в lobby (сброс sync, без возврата в старый матч)
- **X** — саботаж по выбранной **чужой** клетке (низ экрана — ферма соперника)

Победа: первый игрок с целевым продуктом в инвентаре (по умолчанию **`bread`**).  
Темп: **4 тика/сек** (`FARM_WARS_TICK_SEC=0.25`); длительности в БД/мире — в **тиках** (~90 с реального времени на рост пшеницы при seed 2026-05-28).  
Случайные события: по умолчанию каждые **120** тиков (~30 с), вероятность **20%** (`FARM_WARS_EVENT_INTERVAL`, `FARM_WARS_EVENT_PROB`).

Стартовый инвентарь: **120** бестиков, пшеница, мука, корм (см. `server/world_factory.py`).  
Продажа из инвентаря: server-only `SELL_PRODUCT` (`shop_handler` **`immediate_v7`**).

После `git pull` пересоздайте БД: `py tools/init_db.py --seed`.

Полный сценарий демо (2 игрока, победа, саботаж): [docs/specs/gameplay/001.SIGNOFF_DEMO_SCRIPT.md](docs/specs/gameplay/001.SIGNOFF_DEMO_SCRIPT.md)

```bash
py tools/test_vertical_slice.py
```

---

## Мультиплеер по сети (LAN, 2–4 игрока)

| Роль  | Действие                                                                    |
|-------|-----------------------------------------------------------------------------|
| Хост  | `py -m server`, Create → **дождаться гостей** → Start; передать **join code** и **LAN IP** из лога |
| Гость | Server IP = IP хоста, Connect → Join → **ждать старт** (клиент сам войдёт в матч) |

Проверено: `py tools/test_multiplayer.py`. Спека: [docs/specs/gameplay/009.NIKITA.MULTIPLAYER_2PLUS_VERIFICATION.md](docs/specs/gameplay/009.NIKITA.MULTIPLAYER_2PLUS_VERIFICATION.md).

Переменные окружения:

| Переменная              | Сторона         | По умолчанию                    |
|-------------------------|-----------------|---------------------------------|
| `FARM_WARS_HOST`        | сервер          | `0.0.0.0`                       |
| `FARM_WARS_PORT`        | сервер / клиент | `8765`                          |
| `FARM_WARS_TICK_SEC`    | сервер          | `0.25` (4 тика/сек)             |
| `FARM_WARS_TICKS_PER_SEC` | сервер        | `4` (если не задан `TICK_SEC`)  |
| `FARM_WARS_SERVER_HOST` | клиент          | `127.0.0.1`                     |
| `FARM_WARS_SERVER_PORT` | клиент          | `8765`                          |
| `FARM_WARS_SERVER`      | клиент          | полный URL (`http://host:port`) |
| `FARM_WARS_DB_PATH`     | сервер          | `db/farm_wars.db`               |
| `FARM_WARS_WIN_PRODUCT` | сервер          | `bread` (цель победы)           |
| `FARM_WARS_DEV`         | сервер          | `1` → цель `cake` (длинный тест) |
| `FARM_WARS_EVENT_INTERVAL` | сервер       | `120` (~30 с при 4 тик/с)       |
| `FARM_WARS_EVENT_PROB`  | сервер          | `0.2` (вероятность события)     |

На хосте: разрешить входящие подключения в брандмауэре Windows для Python на порту `8765`.

---

## Стартовый набор критичных ТЗ уже создан

Расположение: `docs/specs/`

- `architecture/001.NIKITA_LEAD.ARCHITECTURE_CONTRACTS_V1.md`
- `architecture/002.NIKITA_LEAD.CONTRACT_FIXTURE_STUB_WORKFLOW.md`
- `db/001.NIKITA.SQLITE_SCHEMA_AND_SEED_MINIMAL.md`
- `engine_cpp/001.SANYA.CPP_ENGINE_CORE_PYBIND_BASE.md`
- `server/001.NIKITA.SERVER_MATCH_JOIN_AND_TICK_LOOP.md`
- `server/002.NIKITA.SERVER_ENRICH_PLACE_ON_TILE.md`
- `client/001.NIKITA.CLIENT_PYGAME_CORE_AND_MATCH_UI.md`
- `engine_cpp/002.SANYA.PLACE_ON_TILE.md`
- `gameplay/001.NIKITA_LEAD.VERTICAL_SLICE_PLAYABLE_MATCH_V1.md`
- `gameplay/003.NIKITA.PLAYABLE_FARM_LOOP_V2.md` — магазин, рецепты из БД, HUD
- `gameplay/009.NIKITA.MULTIPLAYER_2PLUS_VERIFICATION.md` — MP 2–4, автотесты, LAN sign-off
- `server/009.NIKITA.TILE_OWNER_VALIDATION.md` — owner-check `WATER_PLANT`
- **Handoff и roadmap:** [`docs/specs/gameplay/010.TEAM.WORK_SUMMARY_AND_HANDOFF.md`](docs/specs/gameplay/010.TEAM.WORK_SUMMARY_AND_HANDOFF.md)
- **SANYA дальше:** [`docs/specs/engine_cpp/006.SANYA.NEXT_ENGINE_ROADMAP.md`](docs/specs/engine_cpp/006.SANYA.NEXT_ENGINE_ROADMAP.md)
- **NIKITA дальше:** [`docs/specs/server/010.NIKITA.NEXT_SERVER_CLIENT_ROADMAP.md`](docs/specs/server/010.NIKITA.NEXT_SERVER_CLIENT_ROADMAP.md)

---

## Текущий приоритет команды

**Сделано (`NIKITA` / `SANYA`):**

- SQLite schema + seed + загрузчик (`db/001`)
- Server join/tick/win + HTTP API + LAN (`server/001`)
- Client pygame lobby/match + MP UX + панель урожай/семена (`client/001`)
- C++ engine + stub; owner validation на клетках (`server/009`)
- Семена vs урожай (`*_seed` / RAW), shop/sell, enricher (`server/002`, shop, sell)
- Магазин, животные, события, PvP-саботаж, vertical slice (`gameplay/003`, `server/006`–`008`, `007`)
- MP 2–4 автотесты (`gameplay/009`)

**Дальше (см. ТЗ 006 / 010):**

1. Ручной LAN sign-off 3–4 клиента (`gameplay/009` → `server/010.1`)
2. SANYA: `player_id` в `CONTRACT_ERROR`, owner на `START_RECIPE` (`engine_cpp/006` P0)
3. NIKITA: контрмеры, solo mode, UI polish (`server/010` P1)
4. Расширение контента к ~10 растениям (`GAME_TECH_REQUIREMENTS.md`)

---

## Критерий готовности MVP

| Критерий                                      | Статус                                       |
|-----------------------------------------------|----------------------------------------------|
| Клиент и сервер на Windows                    | есть                                         |
| Multiplayer 2–4 по join code (localhost + LAN) | есть (`gameplay/009`, `test_multiplayer.py`) |
| Матч до победы по целевому продукту           | есть (рецепт → инвентарь → `MATCH_FINISHED`) |
| Контент из SQLite                             | есть (базовый seed)                          |
| Полный контент (10 растений, PvP в матче)     | впереди                                      |
| `PLACE_ON_TILE` (движок + server enrich)      | есть (`002.SANYA` + `server/002`)            |
