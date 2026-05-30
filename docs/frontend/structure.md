# Структура проекта `web/`

## Корень `web/`

```
web/
├── index.html              # точка входа Vite
├── package.json
├── vite.config.ts          # alias $lib, $components; proxy /api → :8765
├── svelte.config.js
├── tsconfig.json
├── src/
│   ├── main.ts             # mount App
│   ├── App.svelte          # lobby | match
│   ├── app.css             # глобальные CSS-переменные (палитра фермы)
│   ├── vite-env.d.ts
│   ├── components/
│   └── lib/
└── dist/                   # npm run build (не в git)
```

## Алиасы путей

В `vite.config.ts`:

| Алиас | Путь |
|-------|------|
| `$lib` | `src/lib` |
| `$components` | `src/components` |

Импорты: `import { api } from "$lib/api/client"`.

## `src/lib/api/`

| Файл | Назначение |
|------|------------|
| `client.ts` | `GameApi`: health, create/join/start, action, sync, roster; singleton `api` |
| `types.ts` | TypeScript-типы контракта v1 |
| `errors.ts` | `ApiError` (код + message с сервера) |

`VITE_API_BASE` — полный URL сервера; пусто = same-origin (dev proxy).

## `src/lib/stores/`

| Store | Файл | Содержимое |
|-------|------|------------|
| Сессия / лобби | `session.ts` | `screen`, `matchId`, `playerId`, `catalog`, IP/порт, join code |
| Мир матча | `game.ts` | `worldState`, `lastTick`, `matchFinished`, `selectedTileId`, `syncEnabled` |
| UI матча | `matchUi.ts` | выбранные plant/recipe/animal/sell, `viewOpponentId` |
| Лобби | `lobby.ts` | `awaitingMatchStart` (гость ждёт start) |
| DnD | `drag.ts` | активный drag (семена, лейка, животное) |
| Тосты | `toasts.ts` | очередь уведомлений |
| Контекстное меню | `contextMenu.ts` | позиция и target tile |

Writable stores + `$store` в шаблонах; в Svelte 5 lobby использует `$state` локально для roster.

## `src/lib/sync/`

| Файл | Назначение |
|------|------------|
| `poller.ts` | `startSyncPoller` / `stopSyncPoller` — interval `SYNC_POLL_MS` |
| `requestSync.ts` | один запрос `pollSync(matchId, sinceTick)` |
| `applySync.ts` | обновить stores, `MATCH_FINISHED`, toasts из events |
| `optimistic.ts` | `applyOptimisticAction` — предсказание для части action types |

## `src/lib/actions/`

`gameActions.ts` — **единая точка** отправки игровых действий:

- `sendCare`, `sendPlant`, `sendHarvest`, `sendRecipe`, `sendSell`, `sendBuyAnimal`, `sendSabotage`, …
- внутри `sendAction` → optimistic → `api.submitAction` → `applySync`

Компоненты вызывают функции отсюда, а не `api` напрямую (кроме лобби).

## `src/lib/game/`

Чистые функции без side effects (удобно для unit-тестов в будущем):

| Модуль | Назначение |
|--------|------------|
| `constants.ts` | размеры сетки (12 грядок + 8 загонов), интервалы poll |
| `tiles.ts`, `tileGrid.ts` | поиск тайлов, сортировка, радиус лейки |
| `inventory.ts` | количество в инвентаре, sellable |
| `catalogData.ts` | plant ids, seed product id, win product |
| `labels.ts`, `events.ts` | RU-подписи, humanize событий, фильтр тостов |
| `visuals.ts` | срочность полива / голода (CSS классы) |
| `shop.ts`, `warehouse.ts`, `craft.ts`, `factories.ts` | панели магазина/склада/рецептов |
| `pacing.ts` | `TICKS_PER_SECOND` (зеркало `shared/game_pacing`) |
| `contextMenu.ts` | пункты меню по тайлу |

## `src/lib/` — прочее

| Путь | Назначение |
|------|------------|
| `match/lifecycle.ts` | enter/leave match, host start |
| `input/hotkeys.ts` | W/T/H/B/C/F/V/X/Esc → actions |
| `dnd/*.ts` | drag payload, drop на тайл, лейка |

## `src/components/`

```
components/
├── lobby/
│   └── LobbyPanel.svelte      # connect, create, join, roster poll, start
├── match/
│   ├── MatchView.svelte       # layout + hotkeys
│   ├── MatchHeader.svelte
│   ├── FarmPanel.svelte       # своя ферма + вкладка врага
│   ├── FarmGrid.svelte        # сетка клеток, DnD targets
│   ├── MatchSidebar.svelte    # вкладки: цель, склад, магазин, крафт, PvP
│   ├── ShopPanel.svelte
│   ├── WarehousePanel.svelte
│   ├── CraftPanel.svelte
│   ├── FactoryStrip.svelte
│   ├── SeedBar.svelte / WateringCanBar.svelte / AnimalBar.svelte
│   ├── HotkeyBar.svelte
│   ├── GoalProgress.svelte
│   ├── WinOverlay.svelte
│   ├── ToastStack.svelte
│   ├── TileContextMenu.svelte
│   └── WateringCanDragFollower.svelte
└── shared/
    ├── DraggableChip.svelte
    ├── DropBin.svelte
    └── TabBar.svelte
```

### Карта «кто за что» на экране матча

| Зона экрана | Компоненты |
|-------------|------------|
| Верх | `MatchHeader` — тик, баланс, выход |
| Центр-слева | `FarmPanel` → `FarmGrid` (грядки + загоны) |
| Центр-справа | `MatchSidebar` (табы) |
| Оверлеи | `WinOverlay`, `TileContextMenu`, `WateringCanDragFollower` |
| Уведомления | `ToastStack` (lobby + match) |

## Сетка фермы

Константы в `game/constants.ts`:

- **12** слотов грядок (`FARM_PLANT_SLOTS`), сетка 4×3 (`FARM_COLS = 4`)
- **8** слотов загонов (`FARM_ANIMAL_SLOTS`), 4×2
- Лейка: Chebyshev-радиус `WATERING_CAN_RADIUS = 1` на грядках

Порядок `tile_id` и привязка к `owner_player_id` приходят с сервера в `world_state.map.tiles`.

## Добавление нового модуля

1. Типы/поля — `lib/api/types.ts` (если меняется контракт — сначала `GAME_CONTRACTS_V1.md`).
2. Отображение — `lib/game/*` + компонент.
3. Действие — `gameActions.ts` + при необходимости ветка в `optimistic.ts`.
4. Событие с сервера — `lib/game/events.ts` (`humanizeEvent`, `shouldSkipEvent`, `feedToasts`).
5. Документировать в [ui-and-input.md](ui-and-input.md) или [state-and-sync.md](state-and-sync.md).
