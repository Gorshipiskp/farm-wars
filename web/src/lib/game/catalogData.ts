import type { GameCatalog } from "$lib/api/types";

export function plantIds(cat: GameCatalog | null): string[] {
  if (cat?.plants?.length) {
    return cat.plants.map((p) => p.plant_id);
  }
  return ["wheat", "corn", "potato", "tomato", "carrot", "sunflower"];
}

export function seedProductIdForPlant(cat: GameCatalog | null, plantId: string): string {
  const pl = cat?.plants?.find((p) => p.plant_id === plantId);
  return pl?.seed_product_id ?? `${plantId}_seed`;
}

export function winProductId(cat: GameCatalog | null): string {
  return cat?.win_product_id ?? "bread";
}

/** Shop-only rows (seeds + extras), not full warehouse catalog. */
export function shopItems(cat: GameCatalog | null): { product_id: string; price: number }[] {
  if (!cat?.products?.length) {
    const fallback: { product_id: string; price: number }[] = [
      { product_id: "wheat_seed", price: 5 },
      { product_id: "corn_seed", price: 8 },
      { product_id: "flour", price: 12 },
    ];
    return fallback;
  }
  return cat.products
    .filter(
      (p) =>
        p.category === "SEED" ||
        p.plant_id != null ||
        p.product_id === "flour",
    )
    .map((p) => ({
      product_id: p.product_id,
      price: p.price,
    }));
}
