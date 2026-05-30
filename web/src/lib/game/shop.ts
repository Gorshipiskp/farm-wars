import type { GameCatalog } from "$lib/api/types";
import { shopItems } from "./catalogData";

export type ShopCategory = "SEED" | "FEED" | "OTHER";

const CATEGORY_LABELS: Record<ShopCategory, string> = {
  SEED: "Семена",
  FEED: "Корм",
  OTHER: "Прочее",
};

const CATEGORY_ORDER: ShopCategory[] = ["SEED", "FEED", "OTHER"];

export interface ShopItemView {
  product_id: string;
  price: number;
  category: ShopCategory;
}

export function shopItemsGrouped(
  cat: GameCatalog | null,
): { category: ShopCategory; label: string; items: ShopItemView[] }[] {
  const items: ShopItemView[] = shopItems(cat).map((item) => {
    const meta = cat?.products?.find((p) => p.product_id === item.product_id);
    const raw = meta?.category ?? "OTHER";
    const category: ShopCategory =
      raw === "SEED" || raw === "FEED" ? raw : "OTHER";
    return { ...item, category };
  });

  return CATEGORY_ORDER.map((category) => ({
    category,
    label: CATEGORY_LABELS[category],
    items: items.filter((i) => i.category === category),
  })).filter((g) => g.items.length > 0);
}
