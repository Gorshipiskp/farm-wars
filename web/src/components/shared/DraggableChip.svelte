<script lang="ts">
  import { writeDrag } from "$lib/dnd/transfer";
  import type { DragPayload } from "$lib/dnd/types";
  import { dragKey } from "$lib/dnd/types";
  import { useTransparentDragImage } from "$lib/dnd/wateringDragImage";
  import { activeDrag, dragPointer } from "$lib/stores/drag";

  const key = $derived(dragKey(payload));
  const isDragging = $derived($activeDrag != null && dragKey($activeDrag) === key);

  interface Props {
    payload: DragPayload;
    label: string;
    emoji?: string;
    sublabel?: string;
    disabled?: boolean;
    active?: boolean;
    draggable?: boolean;
    onclick?: () => void;
    class?: string;
  }

  let {
    payload,
    label,
    emoji = "",
    sublabel = "",
    disabled = false,
    active = false,
    draggable = true,
    onclick,
    class: className = "",
  }: Props = $props();

  function onDragStart(e: DragEvent) {
    if (disabled || !draggable || !e.dataTransfer) return;
    writeDrag(e.dataTransfer, payload);
    activeDrag.set(payload);
    if (payload.kind === "watering_can") {
      useTransparentDragImage(e);
      dragPointer.set({ x: e.clientX, y: e.clientY });
    } else {
      e.dataTransfer.setDragImage(e.currentTarget as HTMLElement, 24, 16);
    }
  }

  function onDragEnd() {
    dragPointer.set(null);
    activeDrag.set(null);
  }
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
  class="chip {className}"
  class:active
  class:disabled
  class:dragging={isDragging}
  class:dragging-water={isDragging && payload.kind === "watering_can"}
  draggable={draggable && !disabled}
  role="button"
  tabindex={disabled ? -1 : 0}
  ondragstart={onDragStart}
  ondragend={onDragEnd}
  onclick={onclick}
  onkeydown={(e) => e.key === "Enter" && onclick?.()}
>
  <span class="grip" aria-hidden="true">⠿</span>
  {#if emoji}
    <span class="emoji" aria-hidden="true">{emoji}</span>
  {/if}
  <span class="text">
    <span class="label">{label}</span>
    {#if sublabel}
      <span class="sub">{sublabel}</span>
    {/if}
  </span>
</div>

<style>
  .chip {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.4rem 0.55rem;
    border-radius: 8px;
    border: 1px solid var(--panel-border);
    background: #e8dfd0;
    font-size: 0.78rem;
    cursor: grab;
    user-select: none;
    text-align: left;
    transition:
      box-shadow 0.15s,
      transform 0.1s;
  }

  .chip:hover:not(.disabled) {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .chip:active:not(.disabled) {
    cursor: grabbing;
    transform: scale(0.98);
  }

  .chip.active {
    background: var(--accent);
    color: var(--text-on-dark);
    border-color: #a06030;
  }

  .chip.active .sub {
    color: rgba(255, 252, 245, 0.85);
  }

  .chip.disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }

  .chip.dragging {
    opacity: 0.55;
  }

  .chip.dragging-water {
    opacity: 0;
  }

  .grip {
    color: var(--text-soft);
    font-size: 0.85rem;
    line-height: 1;
  }

  .emoji {
    font-size: 1.15rem;
    line-height: 1;
  }

  .text {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
    flex: 1;
    min-width: 0;
  }

  .sub {
    font-size: 0.68rem;
    color: var(--text-soft);
  }
</style>
