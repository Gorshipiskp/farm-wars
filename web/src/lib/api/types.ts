/** Minimal v1 shapes — keep in sync with GAME_CONTRACTS_V1.md */

export interface HealthResponse {
  contract_version: string;
  status: string;
  engine?: string;
  shop_handler?: string;
  catalog?: GameCatalog;
}

export interface GameCatalog {
  products?: CatalogProduct[];
  plants?: CatalogPlant[];
  animals?: CatalogAnimal[];
  recipes?: CatalogRecipe[];
  sabotages?: CatalogSabotage[];
  win_product_id?: string;
}

export interface CatalogProduct {
  product_id: string;
  price: number;
  base_sell_price?: number;
  display_name?: string;
  plant_id?: string;
  category?: string;
}

export interface CatalogPlant {
  plant_id: string;
  product_id: string;
  seed_product_id: string;
  display_name: string;
  seed_display_name?: string;
  crop_display_name?: string;
}

export interface CatalogAnimal {
  animal_id: string;
  product_id?: string;
  price: number;
  display_name: string;
}

export interface CatalogRecipe {
  recipe_id: string;
  building_type: string;
  output_product_id?: string;
  output_display_name?: string;
  production_time_sec?: number;
  ingredients?: { product_id: string; amount: number }[];
}

export interface ActionSubmitResponse {
  contract_version: string;
  accepted: boolean;
  sync?: SyncResponse | null;
}

export interface CatalogSabotage {
  sabotage_id: string;
  price: number;
  display_name: string;
  sabotage_type?: string;
  is_hidden?: boolean;
}

export interface CreateMatchResponse {
  match_id: string;
  join_code: string;
  player_id: string;
}

export interface JoinMatchResponse {
  player_id: string;
  match_id: string;
}

export interface RosterResponse {
  players: { player_id: string; display_name: string }[];
  host_player_id?: string;
}

export interface SyncResponse {
  contract_version: string;
  tick_id: number;
  world_state: WorldState;
  events: GameEvent[];
}

export interface WorldState {
  contract_version: string;
  match_id: string;
  tick_id: number;
  players: PlayerState[];
  map: { width: number; height: number; tiles: TileState[] };
  factories: FactoryState[];
  win_condition: {
    target_product_id?: string;
    winner_player_id?: string | null;
  };
}

export interface PlayerState {
  player_id: string;
  display_name: string;
  money_bestiki: number;
  inventory: InventoryItem[];
}

export interface InventoryItem {
  product_id: string;
  amount: number;
}

export interface TileState {
  tile_id: string;
  zone_type: "PLANT" | "ANIMAL" | string;
  owner_player_id: string;
  occupant_type?: string | null;
  occupant_id?: string | null;
  water_level?: number | null;
  growth_elapsed_sec?: number | null;
  growth_time_sec?: number | null;
  hunger_ticks?: number | null;
  production_elapsed_sec?: number | null;
  production_interval_sec?: number | null;
  flags?: string[];
}

export interface FactoryState {
  factory_id: string;
  factory_type: string;
  owner_player_id: string;
  active_recipe_id?: string | null;
  remaining_time_sec?: number;
}

export interface GameEvent {
  event_type: string;
  server_tick?: number;
  payload?: Record<string, unknown>;
}

export interface PlayerAction {
  contract_version: "v1";
  player_id: string;
  action_type: string;
  payload: Record<string, unknown>;
  client_ts: number;
}

export interface ActionEnvelope {
  contract_version: "v1";
  match_id: string;
  player_id: string;
  action: PlayerAction;
}
