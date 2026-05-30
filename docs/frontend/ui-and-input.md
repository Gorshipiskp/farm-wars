# UI, ввод и обратная связь

## Экран лобби (`LobbyPanel.svelte`)

| Блок | Поведение |
|------|-----------|
| Server IP + Port | `parseServerBase` → `api.setBaseUrl` |
| Connect | `GET /api/health`, загрузка `catalog` |
| Create match | `POST create` → host, join code, roster poll |
| Join | `POST join` → guest, `awaitingMatchStart` |
| Start | только host → `hostStartMatch` → `enterMatch` |
| Roster poll | пока в комнате; гость при `running` сам входит в матч |

Статусная строка: store `statusMessage`. Тосты через `pushToast`.

## Экран матча (`MatchView.svelte`)

Layout:

- **Header** — тик, цель, деньги, кнопка выхода (`leaveMatch`).
- **FarmPanel** — своя ферма; вкладка соперника если `opponents.length > 0`.
- **MatchSidebar** — TabBar: прогресс, склад, магазин, крафт, PvP.

Глобальный `keydown` на document (если не `shouldIgnoreGameHotkey`):

| Клавиша | Action | Функция |
|---------|--------|---------|
| W | care | `sendCare` — полив грядки или корм в загоне |
| T | plant | `sendPlant` |
| H | harvest | `sendHarvest` |
| B | recipe | `sendRecipe` |
| C | buy_animal | `sendBuyAnimal` |
| F | sell | `sendSell` (нужен выбранный товар склада) |
| V | — | выбор sell из склада (клик) |
| X | sabotage | первый sabotage из каталога по **чужой** клетке |
| Esc | — | выход в лобби |

Логика хоткеев: `lib/input/hotkeys.ts`. При изменении — обновить `HotkeyBar.svelte` и этот документ.

## Уход за фермой (care)

Одна кнопка / клавиша **W** — `sendCare()`:

- клетка `PLANT` → `WATER_AREA` (списание B, полив в радиусе лейки на сервере);
- клетка `ANIMAL` с животным → `FEED_ANIMAL`.

Стоимость на сервере: `server/care_costs.py`. В магазине **корм не продаётся** (только уход за B).

## Сетка и выбор клетки

`FarmGrid.svelte`:

- клик → `selectedTileId`;
- визуальные классы из `visuals.ts` (`plantWaterUrgency`, `animalFeedUrgency`);
- drop targets для DnD (`lib/dnd/tileDrop.ts`).

`TileContextMenu.svelte` — ПКМ: посадка, сбор, уход (дублирует часть actions).

## Drag and drop

| Источник | Drop | Действие |
|----------|------|----------|
| `SeedBar` | грядка | посадка выбранной культуры |
| `WateringCanBar` | грядка | полив области (радиус) |
| `AnimalBar` | пустой загон | покупка животного |
| `WarehousePanel` | `DropBin` | продажа (если sellable) |

Состояние drag: `stores/drag.ts` + `WateringCanDragFollower` для курсора лейки.

Типы payload: `lib/dnd/types.ts`, разбор: `lib/dnd/transfer.ts`.

## Склад и магазин

- **Склад** (`warehouse.ts`): только `RAW` / `PROCESSED` с `sellable` — семена и несбыточное скрыты.
- **Магазин** (`shop.ts`): семена, мука и пр. из `catalog`; без `feed`.
- Продажа: чип в складе → `selectedSellProductId` → F или drop в bin.

## Крафт и заводы

- `CraftPanel` + `FactoryStrip` — выбор рецепта, кнопка печи, привязка к типу здания (`factories.ts`).
- `sendRecipe` шлёт `START_RECIPE` с `building_tile_id` и `recipe_id`.

## PvP

- Вкладка в `MatchSidebar` — список соперников, выбор `viewOpponentId`.
- `FarmPanel` показывает чужую сетку read-only.
- Саботаж: выбор чужой клетки + hotkey X или UI; optimistic + события `SABOTAGE_*`.
- Скрытые саботажи: `shouldSkipEvent` для чужого `is_hidden`.

## Цель матча и победа

- `GoalProgress` — прогресс к `win_condition.target_product_id` из мира или каталога.
- `MATCH_FINISHED` → `matchFinished`, `WinOverlay`.

## Тосты

`ToastStack.svelte` + `stores/toasts.ts`:

- kind: `ok` | `error` | `warn` | `info`;
- `STIPEND_GRANTED` — info, только своему `player_id`;
- ошибки действий — error с текстом из `humanizeEvent`.

Не спамить: `feedToasts` помнит последние ключи событий.

## Стили

`app.css` — CSS variables (`--color-soil`, `--color-water`, …). Компоненты используют scoped `<style>` + общие токены.

Срочность ухода — классы на тайлах из `visuals.ts`, не отдельные ассеты.

## Доступность и ввод

- Hotkeys не срабатывают в `input` / `textarea` (`shouldIgnoreGameHotkey`).
- Кнопки дублируют клавиши для мыши/touch.

## Чеклист нового UI-действия

1. Кнопка/жест в компоненте → функция в `gameActions.ts`.
2. Подсказка в `HotkeyBar` / tooltip при наличии клавиши.
3. События сервера в `events.ts`.
4. При необходимости optimistic в `optimistic.ts`.
5. Строка в этом файле (таблица хоткеев или DnD).
