import type { CatalogRecipe, FactoryState, WorldState } from "$lib/api/types";

const FACTORY_LABELS: Record<string, string> = {
  BAKERY: "Пекарня",
  DAIRY: "Сыроварня",
  MEAT: "Мясной цех",
};

export function factoryLabel(factoryType: string): string {
  return FACTORY_LABELS[factoryType] ?? factoryType;
}

export function myFactories(world: WorldState | null, playerId: string): FactoryState[] {
  if (!world?.factories) return [];
  return world.factories.filter((f) => f.owner_player_id === playerId);
}

export function myFactoryTypes(world: WorldState | null, playerId: string): Set<string> {
  return new Set(myFactories(world, playerId).map((f) => f.factory_type));
}

export function factoryForRecipe(
  world: WorldState | null,
  playerId: string,
  recipe: CatalogRecipe | null,
): FactoryState | null {
  if (!world || !recipe) return null;
  const btype = recipe.building_type;
  return (
    world.factories.find(
      (f) => f.owner_player_id === playerId && f.factory_type === btype,
    ) ?? null
  );
}

export function busyFactory(world: WorldState | null, playerId: string): FactoryState | null {
  return (
    myFactories(world, playerId).find((f) => f.active_recipe_id) ?? null
  );
}
