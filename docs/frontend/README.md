# Документация веб-клиента Farm Wars

Браузерный клиент — **основной UI** в разработке (`web/`). Pygame-клиент (`client/`) остаётся как legacy reference до полной parity.

## С чего начать

| Документ | Содержание |
|----------|------------|
| [architecture.md](architecture.md) | Роль клиента, слои, поток данных, принципы |
| [structure.md](structure.md) | Дерево `web/src`, модули `$lib`, компоненты |
| [state-and-sync.md](state-and-sync.md) | Svelte stores, poll sync, optimistic updates |
| [ui-and-input.md](ui-and-input.md) | Экраны, DnD, горячие клавиши, тосты и события |
| [development.md](development.md) | Установка, dev/prod, LAN, чеклист новой фичи |

## Связанные документы репозитория

| Документ | Зачем |
|----------|--------|
| [`web/README.md`](../../web/README.md) | Краткие команды `npm run dev` / build |
| [`docs/specs/client/002.NIKITA.WEB_CLIENT_SVELTE_VITE.md`](../specs/client/002.NIKITA.WEB_CLIENT_SVELTE_VITE.md) | ТЗ миграции и фазы parity |
| [`docs/contracts/GAME_CONTRACTS_V1.md`](../contracts/GAME_CONTRACTS_V1.md) | Форматы `action`, `sync`, событий |
| [`README.md`](../../README.md) | Запуск сервера, API, тесты |
| [`AGENTS.md`](../../AGENTS.md) | Правила работы ИИ-агента в репозитории |

## Стек

- **Svelte 5** (runes `$state` / `$derived` в новых компонентах, stores в общем состоянии)
- **TypeScript**
- **Vite 6** (SPA, **без SvelteKit**)
- HTTP: `fetch` → тот же REST API, что и pygame (`client/net.py`)
