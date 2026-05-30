<script lang="ts">
  import FactoryStrip from "./FactoryStrip.svelte";
  import type { PlayerState, WorldState } from "$lib/api/types";
  import { myJoinCode, playerId } from "$lib/stores/session";

  interface Props {
    player: PlayerState | null;
    world: WorldState | null;
    tickId: number;
    matchFinished: boolean;
    onLeave: () => void;
  }

  let { player, world, tickId, matchFinished, onLeave }: Props = $props();
</script>

<header class="match-header">
  <div class="player-block">
    <span class="avatar" aria-hidden="true">🧑‍🌾</span>
    <div>
      <h1>{player?.display_name ?? "Фермер"}</h1>
      <div class="meta-row">
        <span class="pill tick">⏱ тик {tickId}</span>
        {#if $myJoinCode}
          <span class="pill code">🔑 {$myJoinCode}</span>
        {/if}
        {#if matchFinished}
          <span class="pill end">финиш</span>
        {/if}
      </div>
    </div>
  </div>

  <div class="actions">
    <div class="money" title="Bestiki">
      <span class="coin">◎</span>
      <span class="amount">{player?.money_bestiki ?? 0}</span>
      <span class="unit">B</span>
    </div>
    <button type="button" class="btn-leave" onclick={onLeave}>← Лобби</button>
  </div>
</header>

<div class="factory-row">
  <FactoryStrip {world} playerId={$playerId} variant="bar" />
</div>

<style>
  .match-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    flex-wrap: wrap;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid rgba(110, 88, 62, 0.2);
  }

  .player-block {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    min-width: 0;
  }

  .avatar {
    font-size: 2.25rem;
    line-height: 1;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.12));
  }

  h1 {
    margin: 0;
    font-size: 1.35rem;
    font-weight: 800;
    color: var(--panel-header);
    letter-spacing: -0.02em;
  }

  .meta-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    margin-top: 0.35rem;
  }

  .pill {
    font-size: 0.72rem;
    font-weight: 600;
    padding: 0.2rem 0.5rem;
    border-radius: 6px;
    background: rgba(0, 0, 0, 0.05);
    color: var(--text-soft);
  }

  .pill.code {
    font-family: ui-monospace, monospace;
    letter-spacing: 0.08em;
    background: #fff;
    border: 1px solid #e0d6c8;
  }

  .pill.end {
    background: var(--ok);
    color: #fff;
  }

  .actions {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    flex-shrink: 0;
  }

  .money {
    display: flex;
    align-items: baseline;
    gap: 0.25rem;
    padding: 0.45rem 0.85rem;
    background: linear-gradient(180deg, #ffe566, var(--money));
    border: 2px solid #c9a020;
    border-radius: 14px;
    box-shadow:
      0 2px 0 #a08018,
      0 4px 12px rgba(0, 0, 0, 0.12);
  }

  .coin {
    font-size: 0.85rem;
    opacity: 0.7;
  }

  .amount {
    font-size: 1.15rem;
    font-weight: 800;
    color: #5a4010;
  }

  .unit {
    font-size: 0.8rem;
    font-weight: 700;
    color: #7a5820;
  }

  .btn-leave {
    padding: 0.45rem 0.85rem;
    border-radius: 10px;
    border: 1px solid var(--panel-border);
    background: linear-gradient(180deg, #f0e6d6, #e0d4c0);
    font-weight: 600;
    font-size: 0.85rem;
    color: var(--text);
    transition: transform 0.1s, box-shadow 0.15s;
  }

  .btn-leave:hover {
    transform: translateY(-1px);
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
  }

  .factory-row {
    margin-top: 0.65rem;
    min-height: 0;
  }

  .factory-row:empty {
    display: none;
  }
</style>
