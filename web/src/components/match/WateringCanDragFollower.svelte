<script lang="ts">
  import {
    wateringSplashDiameterPx,
    WATERING_CAN_PX,
    WATERING_GAP_PX,
  } from "$lib/dnd/wateringDragImage";
  import { activeDrag, dragPointer } from "$lib/stores/drag";

  const visible = $derived($activeDrag?.kind === "watering_can" && $dragPointer != null);
  const d = $derived(wateringSplashDiameterPx());
  const anchorY = $derived(WATERING_CAN_PX + WATERING_GAP_PX + d / 2);
</script>

{#if visible && $dragPointer}
  <div
    class="follower"
    style="left: {$dragPointer.x}px; top: {$dragPointer.y}px; --d: {d}px; --anchor-y: {anchorY}px"
    aria-hidden="true"
  >
    <span class="can">🪣</span>
    <span class="ring"></span>
  </div>
{/if}

<style>
  .follower {
    position: fixed;
    z-index: 100000;
    pointer-events: none;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 5px;
    transform: translate(-50%, calc(-1 * var(--anchor-y)));
    will-change: left, top;
  }

  .can {
    font-size: 30px;
    line-height: 1;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.35));
  }

  .ring {
    width: var(--d);
    height: var(--d);
    border-radius: 50%;
    border: 2px dashed rgba(45, 120, 180, 0.9);
    background: radial-gradient(
      circle at 50% 45%,
      rgba(160, 215, 255, 0.65) 0%,
      rgba(90, 170, 230, 0.2) 70%,
      transparent 100%
    );
    box-shadow: inset 0 0 10px rgba(255, 255, 255, 0.45);
    box-sizing: border-box;
  }
</style>
