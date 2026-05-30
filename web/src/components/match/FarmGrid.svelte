<script lang="ts">
  import { FARM_COLS, WATERING_CAN_RADIUS } from "$lib/game/constants";
  import { canDropOnTile, handleTileDrop } from "$lib/dnd/tileDrop";
  import { readDrag } from "$lib/dnd/transfer";
  import type { DragPayload } from "$lib/dnd/types";
  import { activeDrag } from "$lib/stores/drag";
  import { contextMenu } from "$lib/stores/contextMenu";
  import { tilesWithinPlantRadius } from "$lib/game/tileGrid";
  import {
    animalFeedUrgency,
    animalHungerRatio,
    canHarvestPlant,
    growthPercent,
    growthRatio,
    isRipeTile,
    plantMaturity,
    plantMaturityLabel,
    plantWaterUrgency,
    productionRatio,
    tileVisual,
    waterLevelRatio,
  } from "$lib/game/visuals";
  import type { PlayerState, TileState, WorldState } from "$lib/api/types";
  import { get } from "svelte/store";

  interface Props {
    tiles: TileState[];
    selectedTileId: string | null;
    own: boolean;
    myPlayerId: string;
    player: PlayerState | null;
    world: WorldState | null;
    matchFinished: boolean;
    cols?: number;
    splashPlantTiles?: TileState[];
    ariaLabel?: string;
    onSelect: (tileId: string) => void;
  }

  let {
    tiles,
    selectedTileId,
    own,
    myPlayerId,
    player,
    world,
    matchFinished,
    cols = FARM_COLS,
    splashPlantTiles = [],
    ariaLabel = "Поле",
    onSelect,
  }: Props = $props();

  let hoverTileId = $state<string | null>(null);

  const wateringPreview = $derived(
    $activeDrag?.kind === "watering_can" && own && !matchFinished,
  );

  const splashTiles = $derived(
    wateringPreview && hoverTileId && splashPlantTiles.length
      ? tilesWithinPlantRadius(
          hoverTileId,
          splashPlantTiles,
          WATERING_CAN_RADIUS,
          cols,
        )
      : [],
  );

  const splashIds = $derived(new Set(splashTiles.map((t) => t.tile_id)));

  function currentDrag(e: DragEvent): DragPayload | null {
    if (e.dataTransfer) {
      const p = readDrag(e.dataTransfer);
      if (p) return p;
    }
    return get(activeDrag);
  }

  function canWaterTile(tile: TileState): boolean {
    return own && tile.zone_type === "PLANT";
  }

  function dropHighlight(tile: TileState, drag: DragPayload | null): boolean {
    if (!drag || matchFinished) return false;
    if (drag.kind === "watering_can" && splashIds.has(tile.tile_id)) return true;
    return canDropOnTile(drag, tile, myPlayerId, player);
  }

  function resolveTileFromEvent(e: DragEvent): string | null {
    const el = (e.target as HTMLElement).closest("[data-tile-id]");
    return el?.getAttribute("data-tile-id") ?? null;
  }

  function onShellDragOver(e: DragEvent) {
    const p = currentDrag(e);
    if (!p || p.kind !== "watering_can" || matchFinished) return;
    e.preventDefault();
    const tid = resolveTileFromEvent(e);
    if (tid) {
      const tile = tiles.find((t) => t.tile_id === tid);
      if (tile && canWaterTile(tile)) {
        hoverTileId = tid;
        if (e.dataTransfer) e.dataTransfer.dropEffect = "copy";
        return;
      }
    }
    if (e.dataTransfer) e.dataTransfer.dropEffect = "none";
  }

  function onShellDragLeave(e: DragEvent) {
    const shell = e.currentTarget as HTMLElement;
    if (e.relatedTarget instanceof Node && shell.contains(e.relatedTarget)) return;
    hoverTileId = null;
  }

  function onDragOver(e: DragEvent, tile: TileState) {
    if (matchFinished || !e.dataTransfer) return;
    const p = currentDrag(e);
    if (!p) return;

    e.preventDefault();

    const can =
      p.kind === "watering_can"
        ? canWaterTile(tile)
        : canDropOnTile(p, tile, myPlayerId, player);

    if (can) {
      hoverTileId = tile.tile_id;
      e.dataTransfer.dropEffect = "copy";
    } else if (hoverTileId === tile.tile_id) {
      hoverTileId = null;
      e.dataTransfer.dropEffect = "none";
    }
  }

  function onDragLeave(tileId: string) {
    if (hoverTileId === tileId) hoverTileId = null;
  }

  async function onDrop(e: DragEvent, tile: TileState) {
    e.preventDefault();
    hoverTileId = null;
    activeDrag.set(null);
    if (matchFinished || !e.dataTransfer) return;
    const p = readDrag(e.dataTransfer) ?? get(activeDrag);
    if (!p) return;
    const can =
      p.kind === "watering_can"
        ? canWaterTile(tile)
        : canDropOnTile(p, tile, myPlayerId, player);
    if (!can) return;
    onSelect(tile.tile_id);
    await handleTileDrop(tile.tile_id, p, world, myPlayerId, player);
  }

  function onContextMenu(e: MouseEvent, tile: TileState) {
    e.preventDefault();
    onSelect(tile.tile_id);
    contextMenu.set({ x: e.clientX, y: e.clientY, tileId: tile.tile_id });
  }
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
  class="grid-shell"
  ondragover={onShellDragOver}
  ondragleave={onShellDragLeave}
>
  <div
    class="grid"
    style="--cols: {cols}"
    role="grid"
    aria-label={ariaLabel}
  >
    {#each tiles as tile (tile.tile_id)}
      {@const empty = !tile.occupant_type || tile.occupant_type === "EMPTY"}
      {@const animal = tile.zone_type === "ANIMAL"}
      {@const mined = (tile.flags ?? []).includes("MINED")}
      {@const selected = selectedTileId === tile.tile_id}
      {@const vis = tileVisual(tile, own)}
      {@const droppable = dropHighlight(tile, $activeDrag)}
      {@const inSplash = splashIds.has(tile.tile_id)}
      {@const splashCenter = inSplash && hoverTileId === tile.tile_id}
      {@const ripe = !empty && !animal && isRipeTile(tile)}
      {@const harvestReady = ripe && canHarvestPlant(tile)}
      {@const maturity = !empty && !animal ? plantMaturity(tile) : "none"}
      {@const growPct = !empty && !animal ? growthPercent(tile) : 0}
      {@const grow = growthRatio(tile)}
      {@const prod = productionRatio(tile)}
      {@const waterUrgency = plantWaterUrgency(tile)}
      {@const feedUrgency = animalFeedUrgency(tile)}
      {@const waterPct = waterLevelRatio(tile)}
      {@const hungerPct = animalHungerRatio(tile)}
      <button
        type="button"
        class="tile"
        class:own
        class:enemy={!own}
        class:empty
        class:animal
        class:mined
        class:selected
        class:droppable
        class:splash={inSplash}
        class:splash-center={splashCenter}
        class:ripe
        class:harvest-ready={harvestReady}
        class:ripe-dry={ripe && !harvestReady}
        class:almost-ripe={maturity === "almost"}
        class:growing={maturity === "growing"}
        class:needs-water={waterUrgency === "low" || waterUrgency === "critical"}
        class:water-critical={waterUrgency === "critical"}
        class:needs-feed={feedUrgency === "low" || feedUrgency === "critical"}
        class:feed-critical={feedUrgency === "critical"}
        data-tile-id={tile.tile_id}
        style="--accent: {vis.accent}"
        onclick={() => onSelect(tile.tile_id)}
        oncontextmenu={(e) => onContextMenu(e, tile)}
        ondragover={(e) => onDragOver(e, tile)}
        ondragleave={() => onDragLeave(tile.tile_id)}
        ondrop={(e) => onDrop(e, tile)}
        aria-pressed={selected}
        title={inSplash && wateringPreview
          ? "В зоне полива"
          : !empty && !animal
            ? plantMaturityLabel(tile)
            : vis.subtitle}
      >
        {#if inSplash && wateringPreview}
          <span class="water-overlay" aria-hidden="true"></span>
        {/if}
        {#if waterUrgency && waterUrgency !== "ok"}
          <span class="care-alert water-alert" aria-hidden="true">
            <span class="care-icon">💧</span>
            <span class="care-label">Жажда</span>
          </span>
          <span
            class="care-meter water-meter"
            class:urgent-low={waterUrgency === "low"}
            class:urgent-critical={waterUrgency === "critical"}
            title="Влажность {Math.round(waterPct * 100)}%"
          >
            <span class="care-fill" style="width: {waterPct * 100}%"></span>
          </span>
        {/if}
        {#if feedUrgency && feedUrgency !== "ok"}
          <span class="care-alert feed-alert" aria-hidden="true">
            <span class="care-icon">🍽️</span>
            <span class="care-label">{feedUrgency === "critical" ? "Голод" : "Корм"}</span>
          </span>
          <span
            class="care-meter hunger-meter"
            class:urgent-low={feedUrgency === "low"}
            class:urgent-critical={feedUrgency === "critical"}
            title="Сытость {Math.max(0, 100 - Math.round(hungerPct * 100))}%"
          >
            <span class="care-fill hunger-fill" style="width: {hungerPct * 100}%"></span>
          </span>
        {/if}
        {#if (waterUrgency === "low" || waterUrgency === "critical") && own}
          <span class="care-glow water-glow" aria-hidden="true"></span>
        {/if}
        {#if (feedUrgency === "low" || feedUrgency === "critical") && own}
          <span class="care-glow feed-glow" aria-hidden="true"></span>
        {/if}
        {#if maturity === "ripe"}
          <span
            class="maturity-badge ripe-badge"
            class:dry={!harvestReady}
            aria-hidden="true"
          >
            <span class="maturity-icon">{harvestReady ? "🧺" : "💧"}</span>
            <span class="maturity-text">{harvestReady ? "Созрело!" : "Полей!"}</span>
          </span>
        {:else if maturity === "almost"}
          <span class="maturity-badge almost-badge" aria-hidden="true">
            <span class="maturity-text">{growPct}%</span>
          </span>
        {/if}
        {#if harvestReady}
          <span class="ripe-glow" aria-hidden="true"></span>
          <span class="ripe-sparkle" aria-hidden="true">✦</span>
        {/if}
        <span class="emoji" class:ripe-pop={harvestReady} aria-hidden="true">{vis.emoji}</span>
        {#if !empty && animal}
          <div class="prod-track" aria-hidden="true" title="Прогресс продукции">
            <span class="bar prod" style="width: {Math.max(prod * 100, prod > 0 ? 4 : 0)}%"></span>
          </div>
        {:else if !empty && !animal}
          <div
            class="grow-track"
            class:full={ripe}
            title="Рост {growPct}%"
            aria-hidden="true"
          >
            <span class="bar grow" class:ready={ripe} style="width: {Math.max(grow * 100, 4)}%"></span>
            <span class="grow-pct">{growPct}%</span>
          </div>
        {/if}
        {#if droppable && !inSplash}
          <span class="drop-ring" aria-hidden="true"></span>
        {/if}
        {#if splashCenter}
          <span class="splash-center-mark" aria-hidden="true">🪣</span>
        {:else if inSplash && wateringPreview}
          <span class="splash-mark" aria-hidden="true">💧</span>
        {/if}
      </button>
    {/each}
  </div>
</div>

<style>
  .grid-shell {
    position: relative;
    width: 100%;
    max-width: 360px;
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(var(--cols), 1fr);
    gap: 0.5rem;
    width: 100%;
  }

  .tile {
    aspect-ratio: 1;
    border-radius: 12px;
    border: 2px solid rgba(50, 35, 20, 0.45);
    background: var(--accent, #c4a574);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    position: relative;
    padding: 0;
    cursor: pointer;
    box-shadow:
      0 3px 0 rgba(50, 35, 20, 0.25),
      0 4px 10px rgba(0, 0, 0, 0.12);
    transition:
      box-shadow 0.08s,
      transform 0.08s,
      background 0.1s;
    overflow: hidden;
  }

  .tile:hover {
    transform: translateY(-2px);
  }

  .tile:active:not(:disabled) {
    transform: scale(0.96);
    transition-duration: 0.04s;
  }

  .tile.enemy {
    filter: saturate(0.85);
  }

  .tile.mined {
    outline: 3px solid #c34137;
  }

  .tile.selected {
    box-shadow:
      0 0 0 3px #ffd237,
      0 4px 0 rgba(50, 35, 20, 0.25);
    transform: translateY(-2px);
  }

  .tile.ripe {
    border-color: #2a8a42;
    box-shadow:
      0 0 0 2px rgba(52, 135, 72, 0.55),
      0 3px 0 rgba(50, 35, 20, 0.25);
  }

  .tile.harvest-ready {
    border-color: #ffd237;
    border-width: 3px;
    animation: ripe-harvest-pulse 1s ease-in-out infinite;
  }

  .tile.ripe-dry {
    border-color: #d87820;
    animation: ripe-dry-pulse 1.1s ease-in-out infinite;
  }

  .tile.almost-ripe {
    border-color: #c8a030;
    box-shadow:
      0 0 0 2px rgba(200, 160, 48, 0.4),
      0 3px 0 rgba(50, 35, 20, 0.25);
  }

  @keyframes ripe-harvest-pulse {
    0%,
    100% {
      box-shadow:
        0 0 0 3px rgba(255, 210, 55, 0.65),
        0 0 12px rgba(52, 135, 72, 0.45),
        0 3px 0 rgba(50, 35, 20, 0.25);
    }
    50% {
      box-shadow:
        0 0 0 6px rgba(255, 210, 55, 0.35),
        0 0 18px rgba(52, 135, 72, 0.55),
        0 3px 0 rgba(50, 35, 20, 0.25);
    }
  }

  @keyframes ripe-dry-pulse {
    0%,
    100% {
      box-shadow: 0 0 0 2px rgba(216, 120, 32, 0.55), 0 3px 0 rgba(50, 35, 20, 0.25);
    }
    50% {
      box-shadow: 0 0 0 5px rgba(216, 120, 32, 0.35), 0 3px 0 rgba(50, 35, 20, 0.25);
    }
  }

  .tile.needs-water {
    border-color: #d87820;
    box-shadow:
      0 0 0 2px rgba(216, 120, 32, 0.55),
      0 3px 0 rgba(50, 35, 20, 0.25);
    animation: care-pulse-water 1.4s ease-in-out infinite;
  }

  .tile.needs-water.water-critical {
    border-color: #c43828;
    animation: care-pulse-water-critical 0.9s ease-in-out infinite;
  }

  .tile.needs-feed {
    border-color: #c87828;
    box-shadow:
      0 0 0 2px rgba(200, 120, 40, 0.5),
      0 3px 0 rgba(50, 35, 20, 0.25);
    animation: care-pulse-feed 1.4s ease-in-out infinite;
  }

  .tile.needs-feed.feed-critical {
    border-color: #b83030;
    animation: care-pulse-feed-critical 0.9s ease-in-out infinite;
  }

  .tile.needs-water.selected,
  .tile.needs-feed.selected,
  .tile.harvest-ready.selected,
  .tile.ripe-dry.selected {
    animation: none;
  }

  @keyframes care-pulse-water {
    0%,
    100% {
      box-shadow: 0 0 0 2px rgba(216, 120, 32, 0.45), 0 3px 0 rgba(50, 35, 20, 0.25);
    }
    50% {
      box-shadow: 0 0 0 5px rgba(216, 120, 32, 0.35), 0 3px 0 rgba(50, 35, 20, 0.25);
    }
  }

  @keyframes care-pulse-water-critical {
    0%,
    100% {
      box-shadow: 0 0 0 3px rgba(196, 56, 40, 0.65), 0 3px 0 rgba(50, 35, 20, 0.25);
    }
    50% {
      box-shadow: 0 0 0 7px rgba(196, 56, 40, 0.4), 0 3px 0 rgba(50, 35, 20, 0.25);
    }
  }

  @keyframes care-pulse-feed {
    0%,
    100% {
      box-shadow: 0 0 0 2px rgba(200, 120, 40, 0.45), 0 3px 0 rgba(50, 35, 20, 0.25);
    }
    50% {
      box-shadow: 0 0 0 5px rgba(200, 120, 40, 0.32), 0 3px 0 rgba(50, 35, 20, 0.25);
    }
  }

  @keyframes care-pulse-feed-critical {
    0%,
    100% {
      box-shadow: 0 0 0 3px rgba(184, 48, 48, 0.65), 0 3px 0 rgba(50, 35, 20, 0.25);
    }
    50% {
      box-shadow: 0 0 0 7px rgba(184, 48, 48, 0.42), 0 3px 0 rgba(50, 35, 20, 0.25);
    }
  }

  .tile.droppable:not(.splash) {
    box-shadow: 0 0 0 2px rgba(205, 115, 47, 0.65);
  }

  .tile.splash {
    border-color: #3d8cc4;
    z-index: 1;
  }

  .tile.splash-center {
    z-index: 2;
    transform: scale(1.05);
    border-color: #1a6aa8;
    box-shadow:
      0 0 0 3px rgba(32, 128, 192, 0.55),
      0 4px 14px rgba(50, 120, 200, 0.35);
  }

  .water-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(
      160deg,
      rgba(140, 210, 255, 0.55) 0%,
      rgba(70, 160, 230, 0.7) 100%
    );
    pointer-events: none;
    animation: water-pulse 1.1s ease-in-out infinite;
  }

  .tile.splash-center .water-overlay {
    background: linear-gradient(
      160deg,
      rgba(160, 225, 255, 0.65) 0%,
      rgba(50, 140, 220, 0.85) 100%
    );
  }

  @keyframes water-pulse {
    0%,
    100% {
      opacity: 0.85;
    }
    50% {
      opacity: 1;
    }
  }

  .emoji {
    font-size: 1.85rem;
    line-height: 1;
    filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.25));
    z-index: 1;
    transition: transform 0.15s ease;
  }

  .emoji.ripe-pop {
    transform: scale(1.12);
    filter: drop-shadow(0 0 6px rgba(255, 220, 80, 0.7));
  }

  .maturity-badge {
    position: absolute;
    top: 2px;
    left: 2px;
    right: 2px;
    z-index: 4;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.12rem;
    padding: 0.14rem 0.22rem;
    border-radius: 6px;
    font-size: 0.58rem;
    font-weight: 900;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    pointer-events: none;
    line-height: 1.05;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
  }

  .ripe-badge {
    color: #1a3a18;
    background: linear-gradient(180deg, #b8f0a0, #6ac85a);
    border: 1px solid #3d8a32;
    animation: maturity-badge-pop 1.2s ease-in-out infinite;
  }

  .ripe-badge.dry {
    color: #5a3010;
    background: linear-gradient(180deg, #ffe0a8, #f0b050);
    border-color: #c87828;
    animation: none;
  }

  .almost-badge {
    color: #4a3810;
    background: linear-gradient(180deg, #fff0b0, #e8c860);
    border: 1px solid #c8a030;
  }

  .maturity-icon {
    font-size: 0.72rem;
    line-height: 1;
  }

  @keyframes maturity-badge-pop {
    0%,
    100% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.04);
    }
  }

  .ripe-glow {
    position: absolute;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    border-radius: 10px;
    background: radial-gradient(
      ellipse at 50% 40%,
      rgba(255, 230, 100, 0.55) 0%,
      rgba(80, 180, 90, 0.25) 45%,
      transparent 70%
    );
    animation: care-glow-fade 1s ease-in-out infinite;
  }

  .ripe-sparkle {
    position: absolute;
    top: 4px;
    right: 5px;
    z-index: 4;
    font-size: 0.65rem;
    color: #fff8c0;
    text-shadow: 0 0 4px rgba(255, 200, 50, 0.9);
    pointer-events: none;
    animation: sparkle-twinkle 1.4s ease-in-out infinite;
  }

  @keyframes sparkle-twinkle {
    0%,
    100% {
      opacity: 0.5;
      transform: scale(0.9);
    }
    50% {
      opacity: 1;
      transform: scale(1.15);
    }
  }

  .grow-track {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 14px;
    z-index: 2;
    background: rgba(0, 0, 0, 0.22);
    border-radius: 0 0 10px 10px;
    overflow: hidden;
    display: flex;
    align-items: stretch;
  }

  .grow-track.full {
    background: rgba(30, 80, 40, 0.35);
  }

  .grow-track .bar,
  .prod-track .bar {
    position: relative;
    display: block;
    height: 100%;
    min-width: 0;
    border-radius: 0;
    flex-shrink: 0;
  }

  .grow-track .bar.grow {
    background: linear-gradient(90deg, #5a8a32, #8bc96a);
  }

  .grow-track .bar.grow.ready {
    background: linear-gradient(90deg, #2d8a3a, #6ee878);
  }

  .grow-pct {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.58rem;
    font-weight: 800;
    color: #fff;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.55);
    pointer-events: none;
    z-index: 1;
  }

  .prod-track {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 5px;
    z-index: 2;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 0 0 10px 10px;
    overflow: hidden;
  }

  .prod-track .bar.prod {
    background: linear-gradient(90deg, #d8e8f8, #f0f8ff);
    opacity: 0.95;
  }

  .drop-ring {
    position: absolute;
    inset: 4px;
    border: 2px dashed rgba(52, 135, 72, 0.7);
    border-radius: 8px;
    pointer-events: none;
    z-index: 2;
  }

  .splash-mark,
  .splash-center-mark {
    position: absolute;
    font-size: 0.75rem;
    pointer-events: none;
    z-index: 2;
    filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
  }

  .splash-mark {
    top: 3px;
    left: 4px;
  }

  .splash-center-mark {
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 1.1rem;
  }

  .care-glow {
    position: absolute;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    border-radius: 10px;
  }

  .care-glow.water-glow {
    background: radial-gradient(
      ellipse at 50% 0%,
      rgba(100, 180, 255, 0.35) 0%,
      transparent 65%
    );
    animation: care-glow-fade 1.4s ease-in-out infinite;
  }

  .care-glow.feed-glow {
    background: radial-gradient(
      ellipse at 50% 100%,
      rgba(255, 160, 80, 0.4) 0%,
      transparent 65%
    );
    animation: care-glow-fade 1.4s ease-in-out infinite;
  }

  .feed-critical .care-glow.feed-glow {
    background: radial-gradient(
      ellipse at 50% 50%,
      rgba(255, 90, 70, 0.45) 0%,
      transparent 70%
    );
    animation: care-glow-fade 0.9s ease-in-out infinite;
  }

  @keyframes care-glow-fade {
    0%,
    100% {
      opacity: 0.55;
    }
    50% {
      opacity: 1;
    }
  }

  .care-alert {
    position: absolute;
    top: 3px;
    left: 3px;
    right: 3px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.15rem;
    padding: 0.12rem 0.2rem;
    border-radius: 6px;
    font-size: 0.58rem;
    font-weight: 800;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    z-index: 3;
    pointer-events: none;
    line-height: 1.1;
  }

  .care-alert.water-alert {
    color: #1a4a78;
    background: linear-gradient(180deg, rgba(200, 230, 255, 0.95), rgba(140, 200, 255, 0.9));
    border: 1px solid rgba(60, 130, 200, 0.65);
    box-shadow: 0 1px 4px rgba(40, 100, 180, 0.25);
  }

  .water-critical .care-alert.water-alert {
    color: #fff;
    background: linear-gradient(180deg, #e85a40, #c43828);
    border-color: #8a2018;
    animation: care-badge-shake 0.85s ease-in-out infinite;
  }

  .care-alert.feed-alert {
    color: #5a3010;
    background: linear-gradient(180deg, rgba(255, 230, 180, 0.95), rgba(240, 190, 120, 0.92));
    border: 1px solid rgba(180, 110, 40, 0.6);
    box-shadow: 0 1px 4px rgba(120, 70, 20, 0.2);
  }

  .feed-critical .care-alert.feed-alert {
    color: #fff;
    background: linear-gradient(180deg, #e06050, #b83030);
    border-color: #7a1818;
    animation: care-badge-shake 0.85s ease-in-out infinite;
  }

  .care-icon {
    font-size: 0.72rem;
    line-height: 1;
  }

  @keyframes care-badge-shake {
    0%,
    100% {
      transform: translateX(0);
    }
    25% {
      transform: translateX(-1px);
    }
    75% {
      transform: translateX(1px);
    }
  }

  .care-meter {
    position: absolute;
    left: 4px;
    right: 4px;
    height: 6px;
    border-radius: 4px;
    background: rgba(0, 0, 0, 0.2);
    overflow: hidden;
    z-index: 3;
    pointer-events: none;
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.15);
  }

  .care-meter.water-meter {
    top: 22px;
  }

  .care-meter.hunger-meter {
    bottom: 16px;
  }

  .tile.harvest-ready .care-meter.water-meter,
  .tile.ripe .care-meter.water-meter,
  .tile.almost-ripe .care-meter.water-meter {
    top: 24px;
  }

  .care-meter .care-fill {
    display: block;
    height: 100%;
    border-radius: 4px;
    transition: width 0.25s ease;
  }

  .water-meter .care-fill {
    background: linear-gradient(90deg, #4a9ee8, #7ec8ff);
  }

  .water-meter.urgent-low .care-fill {
    background: linear-gradient(90deg, #e8a030, #f0c050);
  }

  .water-meter.urgent-critical .care-fill {
    background: linear-gradient(90deg, #d04030, #f07050);
  }

  .hunger-meter .care-fill.hunger-fill {
    background: linear-gradient(90deg, #e8a848, #f0c878);
  }

  .hunger-meter.urgent-critical .care-fill.hunger-fill {
    background: linear-gradient(90deg, #c43030, #e85848);
  }

  .tile.needs-water .emoji,
  .tile.needs-feed .emoji,
  .tile.harvest-ready .emoji,
  .tile.ripe .emoji,
  .tile.almost-ripe .emoji {
    margin-top: 0.5rem;
  }
</style>
