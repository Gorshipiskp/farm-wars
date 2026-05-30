import type { CatalogSabotage, TileState, WorldState } from "$lib/api/types";
import { isEnemyTile } from "./tiles";
import { isRipeTile } from "./visuals";

export interface ContextMenuItem {
  id: string;
  label: string;
  hotkey?: string;
  disabled?: boolean;
  danger?: boolean;
  children?: ContextMenuItem[];
}

export function buildTileContextMenu(
  tile: TileState,
  myPlayerId: string,
  matchFinished: boolean,
  sabotages: CatalogSabotage[],
): ContextMenuItem[] {
  if (matchFinished) {
    return [{ id: "noop", label: "Матч окончен", disabled: true }];
  }

  const own = tile.owner_player_id === myPlayerId;
  const enemy = isEnemyTile(tile, myPlayerId);
  const empty = !tile.occupant_type || tile.occupant_type === "EMPTY";
  const animal = tile.zone_type === "ANIMAL";
  const items: ContextMenuItem[] = [];

  if (enemy) {
    const sabItems: ContextMenuItem[] = sabotages.map((s) => ({
      id: `sabotage:${s.sabotage_id}`,
      label: `${s.display_name ?? s.sabotage_id} (${s.price} B)`,
      danger: true,
    }));
    if (sabItems.length) {
      items.push({ id: "sabotage-menu", label: "Саботаж", children: sabItems });
    } else {
      items.push({ id: "sabotage:poison_water", label: "Саботаж", danger: true });
    }
    items.push({ id: "select", label: "Выбрать клетку" });
    return items;
  }

  if (!own) return items;

  if (animal) {
    if (empty) {
      items.push({ id: "buy_animal", label: "Купить животное", hotkey: "C" });
    } else if (tile.occupant_type === "ANIMAL") {
      items.push({ id: "care", label: "Покормить", hotkey: "W" });
    }
    items.push({ id: "select", label: "Выбрать загон" });
    return items;
  }

  // plant zone
  if (empty) {
    items.push({ id: "plant", label: "Посадить", hotkey: "T" });
  } else {
    const ripe = isRipeTile(tile);
    const water = tile.water_level ?? 100;
    if (water < 50) {
      items.push({ id: "care", label: "Полить", hotkey: "W" });
    }
    if (ripe) {
      items.push({ id: "harvest", label: "Собрать урожай", hotkey: "H" });
    } else if (!empty) {
      items.push({ id: "harvest", label: "Собрать (если созрело)", hotkey: "H" });
    }
  }
  items.push({ id: "select", label: "Выбрать грядку" });
  return items;
}
