import type { GameCatalog } from "$lib/api/types";
import { productLabel } from "./labels";

export function recipeHintForTarget(
  cat: GameCatalog | null,
  targetProductId: string,
): string | null {
  if (!cat?.recipes?.length) return null;
  const recipe =
    cat.recipes.find(
      (r) => r.output_product_id === targetProductId || r.recipe_id === targetProductId,
    ) ?? null;
  if (!recipe?.ingredients?.length) return null;

  return recipe.ingredients
    .map((ing) => {
      const prod = cat.products?.find((p) => p.product_id === ing.product_id);
      const name = prod?.display_name ?? productLabel(ing.product_id);
      return `${name} x${ing.amount}`;
    })
    .join(", ");
}

export function targetDisplayName(
  cat: GameCatalog | null,
  targetProductId: string,
  serverDisplayName?: string | null,
): string {
  if (serverDisplayName) return serverDisplayName;
  return productLabel(targetProductId);
}
