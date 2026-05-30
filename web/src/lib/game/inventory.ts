import type { GameCatalog, PlayerState } from "$lib/api/types";

export function inventoryAmount(player: PlayerState | null, productId: string): number {
  if (!player?.inventory) return 0;
  for (const item of player.inventory) {
    if (item.product_id === productId) return item.amount;
  }
  return 0;
}

export function isSeedProduct(productId: string): boolean {
  return productId.endsWith("_seed");
}

/** Урожай и товары для продажи (не семена). */
export function isBagProduct(productId: string): boolean {
  return !isSeedProduct(productId);
}

export function isSellableProduct(productId: string, catalog: GameCatalog | null): boolean {
  if (!isBagProduct(productId) || productId === "feed") {
    return false;
  }
  const p = catalog?.products?.find((x) => x.product_id === productId);
  if (!p?.category) {
    return true;
  }
  return p.category === "RAW" || p.category === "PROCESSED";
}

export function bagProducts(player: PlayerState | null): { product_id: string; amount: number }[] {
  if (!player?.inventory) return [];
  return player.inventory.filter(
    (i) => isBagProduct(i.product_id) && i.amount > 0,
  );
}
