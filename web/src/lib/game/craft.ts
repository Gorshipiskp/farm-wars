import type { CatalogRecipe, GameCatalog, PlayerState } from "$lib/api/types";
import { inventoryAmount } from "./inventory";
import { productLabel } from "./labels";
import { formatDurationRu } from "./pacing";
import { sellUnitPrice } from "./prices";

export interface IngredientStatus {
  productId: string;
  label: string;
  need: number;
  have: number;
  ok: boolean;
}

export function recipeIngredientStatus(
  player: PlayerState | null,
  recipe: CatalogRecipe | null,
): IngredientStatus[] {
  if (!recipe?.ingredients?.length) return [];
  return recipe.ingredients.map((ing) => {
    const need = ing.amount;
    const have = inventoryAmount(player, ing.product_id);
    return {
      productId: ing.product_id,
      label: productLabel(ing.product_id),
      need,
      have,
      ok: have >= need,
    };
  });
}

/** Catalog `production_time_sec` = wall-clock seconds until the recipe finishes. */
export function recipeCookSeconds(recipe: CatalogRecipe | null | undefined): number {
  if (!recipe) return 0;
  return Math.max(1, recipe.production_time_sec ?? 30);
}

export function recipeCookLabel(recipe: CatalogRecipe | null | undefined): string {
  return formatDurationRu(recipeCookSeconds(recipe));
}

export function recipeOutputProductId(recipe: CatalogRecipe | null | undefined): string {
  if (!recipe) return "";
  return recipe.output_product_id ?? recipe.recipe_id;
}

/** Unit sell price on the market (matches server sell.py / products.base_sell_price). */
export function recipeSellUnitPrice(
  recipe: CatalogRecipe | null | undefined,
  catalog: GameCatalog | null = null,
): number {
  const outId = recipeOutputProductId(recipe);
  if (!outId) return 0;
  return sellUnitPrice(outId, catalog);
}

export function canCraftRecipe(
  player: PlayerState | null,
  recipe: CatalogRecipe | null,
): { ok: boolean; missing: string[] } {
  if (!player || !recipe) return { ok: false, missing: [] };
  const missing: string[] = [];
  for (const ing of recipe.ingredients ?? []) {
    const need = ing.amount;
    const have = inventoryAmount(player, ing.product_id);
    if (have < need) {
      missing.push(`${productLabel(ing.product_id)} ×${need - have}`);
    }
  }
  return { ok: missing.length === 0, missing };
}
