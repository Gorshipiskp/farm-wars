# Разработка веб-клиента

## Требования

- Node.js 18+ (рекомендуется 20 LTS)
- npm
- Запущенный Python-сервер игры (`py -m server`)
- Инициализированная БД: `py tools/init_db.py --seed`

## Первый запуск

Из корня репозитория:

```bash
py -m server
```

В другом терминале:

```bash
cd web
npm install
npm run dev
```

Откройте http://localhost:5173

Запросы к `/api/*` проксируются на `http://127.0.0.1:8765` (`vite.config.ts`). CORS для dev не обязателен.

## Переменные окружения

Файл `web/.env.local` (не коммитить секреты; шаблон можно в `.env.example`):

| Переменная | Пример | Назначение |
|------------|--------|------------|
| `VITE_API_BASE` | `http://192.168.1.10:8765` | Прямой URL сервера без Vite proxy (LAN) |

Без `VITE_API_BASE` клиент ходит на same-origin `/api` (dev proxy или статика с того же хоста, что API).

На сервере CORS уже разрешён для браузерного клиента (`server/http_api.py`).

## LAN-игра

1. Хост: `py -m server` (в логе LAN IP).
2. Гости: `web/.env.local` → `VITE_API_BASE=http://<host-ip>:8765`
3. `npm run dev` или `npm run build` + раздача `dist/`
4. Брандмауэр Windows: порт **8765** для Python.

В лобби ввести IP хоста и порт, **Connect**, затем join code.

## Сборка production

```bash
cd web
npm run build
```

Артефакт: `web/dist/`. Preview локально:

```bash
npm run preview
```

Опционально (roadmap ТЗ 002): отдавать `dist/` с Python-сервера (`GET /`).

## Проверка типов

```bash
cd web
npm run check
```

`svelte-check` + `tsconfig.json`. Запускайте перед PR с изменениями в `web/`.

## Соглашения кода

| Тема | Правило |
|------|---------|
| Язык UI | пользовательские строки на **русском** (`labels.ts`, toasts) |
| Игровая логика | не в компонентах — `gameActions`, `game/*`, `optimistic` |
| API | только `GameApi` / `api` singleton |
| Контракт | сначала `GAME_CONTRACTS_V1.md`, потом `types.ts` |
| Стили | общие токены в `app.css`, не хардкодить hex в каждом файле |
| Svelte 5 | новые компоненты: `$props()`, `$derived`, `$state` где уместно; stores для кросс-экранного state |

## Типичный workflow фичи

1. Прочитать серверное поведение и event types.
2. Обновить `lib/api/types.ts` при изменении JSON.
3. Реализовать `gameActions.send*` + UI.
4. Добавить optimistic (если критична задержка UX).
5. Обработать события в `events.ts`.
6. Ручная проверка: 2 вкладки браузера = 2 игрока, или `py tools/test_multiplayer.py` для сервера.
7. Обновить [structure.md](structure.md) / [ui-and-input.md](ui-and-input.md) при новых модулях.

## Отладка

| Проблема | Что проверить |
|----------|----------------|
| Network Error | сервер запущен, порт, `VITE_API_BASE` |
| Пустой каталог | `init_db --seed`, `/api/health` |
| Старый мир после action | приходит ли `sync` в ответе action |
| Двойные тосты | `feedToasts` dedupe keys |
| HMR сломал state | F5 или `leaveMatch` → снова в матч |

## Тесты репозитория (без браузера)

Фронтенд пока без автотестов в CI. Регресс сервера:

```bash
py tools/test_server_flow.py
py tools/test_multiplayer.py
py tools/test_pvp.py
```

После изменений API обязательно зелёные server tests.

## Связанные файлы конфигурации

| Файл | Назначение |
|------|------------|
| `vite.config.ts` | proxy, aliases |
| `svelte.config.js` | препроцессор Svelte |
| `tsconfig.json` | strict TS, paths |
| `package.json` | scripts, версии Svelte/Vite |

## Документация

Полный индекс: [README.md](README.md) в этой папке.

ИИ-агентам: правила репозитория в [`AGENTS.md`](../../AGENTS.md).
