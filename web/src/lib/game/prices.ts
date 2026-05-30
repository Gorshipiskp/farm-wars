import type { GameCatalog } from "$lib/api/types";

/**
 * Fallback unit sell prices (db/seed_minimal.sql) when /api/health catalog is stale.
 */
const FALLBACK_SELL_UNIT: Record<string, number> = {
  wheat: 5,
  corn: 6,
  potato: 4,
  tomato: 7,
  carrot: 5,
  sunflower: 6,
  milk: 10,
  egg: 8,
  wool: 12,
  pork: 14,
  flour: 8,
  bread: 20,
  cake: 35,
  cheese: 22,
  butter: 18,
  sausage: 28,
  pie: 32,
  soup: 24,
  omelette: 26,
};

/** Bestiki per unit when selling on the market (matches server sell.py). */
export function sellUnitPrice(productId: string, catalog: GameCatalog | null): number {
  const row = catalog?.products?.find((p) => p.product_id === productId);
  if (row) {
    const fromCatalog = row.base_sell_price ?? row.price;
    if (typeof fromCatalog === "number" && fromCatalog > 0) {
      return fromCatalog;
    }
  }
  return FALLBACK_SELL_UNIT[productId] ?? 0;
}
