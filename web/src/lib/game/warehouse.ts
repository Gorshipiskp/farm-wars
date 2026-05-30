import type { GameCatalog, PlayerState } from "$lib/api/types";
import { bagProducts, isSellableProduct } from "./inventory";
import { sellUnitPrice } from "./prices";

export type WarehouseCategory = "RAW" | "PROCESSED" | "OTHER";

const CATEGORY_LABELS: Record<WarehouseCategory, string> = {
  RAW: "Сырьё",
  PROCESSED: "Готовое",
  OTHER: "Прочее",
};

const CATEGORY_ORDER: WarehouseCategory[] = ["RAW", "PROCESSED", "OTHER"];

export interface WarehouseItemView {
  product_id: string;
  amount: number;
  category: WarehouseCategory;
  sellPrice: number;
  sellable: boolean;
}

export function warehouseItemsGrouped(
  player: PlayerState | null,
  catalog: GameCatalog | null,
): { category: WarehouseCategory; label: string; items: WarehouseItemView[] }[] {
  const items: WarehouseItemView[] = bagProducts(player)
    .map((item) => {
      const meta = catalog?.products?.find((p) => p.product_id === item.product_id);
      const raw = meta?.category;
      const category: WarehouseCategory =
        raw === "RAW" || raw === "PROCESSED"
          ? raw
          : "OTHER";
      const sellPrice = sellUnitPrice(item.product_id, catalog);
      const sellable = isSellableProduct(item.product_id, catalog);
      return {
        ...item,
        category,
        sellPrice,
        sellable,
      };
    })
    .filter((item) => item.sellable);

  return CATEGORY_ORDER.map((category) => ({
    category,
    label: CATEGORY_LABELS[category],
    items: items.filter((i) => i.category === category),
  })).filter((g) => g.items.length > 0);
}

export function warehouseTotals(items: WarehouseItemView[]): {
  kinds: number;
  units: number;
  sellValue: number;
} {
  let units = 0;
  let sellValue = 0;
  for (const i of items) {
    units += i.amount;
    if (i.sellable) sellValue += i.sellPrice * i.amount;
  }
  return { kinds: items.length, units, sellValue };
}
