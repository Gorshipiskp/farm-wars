<script lang="ts">
  import { get } from "svelte/store";
  import { readDrag } from "$lib/dnd/transfer";
  import type { DragPayload } from "$lib/dnd/types";
  import { activeDrag } from "$lib/stores/drag";

  interface Props {
    label: string;
    hint?: string;
    accept: (payload: DragPayload) => boolean;
    onDrop: (payload: DragPayload) => void;
    disabled?: boolean;
  }

  let { label, hint = "", accept, onDrop, disabled = false }: Props = $props();

  let over = $state(false);

  function payloadNow(e: DragEvent): DragPayload | null {
    if (e.dataTransfer) {
      const p = readDrag(e.dataTransfer);
      if (p) return p;
    }
    return get(activeDrag);
  }

  const canAccept = $derived(
    !disabled && $activeDrag != null && accept($activeDrag),
  );

  function onDragOver(e: DragEvent) {
    if (disabled) return;
    const p = payloadNow(e);
    if (p && accept(p)) {
      e.preventDefault();
      e.stopPropagation();
      over = true;
      if (e.dataTransfer) e.dataTransfer.dropEffect = "copy";
    }
  }

  function onDragLeave() {
    over = false;
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    over = false;
    if (disabled || !e.dataTransfer) return;
    const p = readDrag(e.dataTransfer) ?? get(activeDrag);
    if (p && accept(p)) onDrop(p);
    activeDrag.set(null);
  }
</script>

<div
  class="bin"
  class:over
  class:ready={canAccept}
  class:disabled
  role="region"
  aria-label={label}
  ondragover={onDragOver}
  ondragleave={onDragLeave}
  ondrop={handleDrop}
>
  <span class="icon">🏪</span>
  <span class="label">{label}</span>
  {#if hint}
    <span class="hint">{hint}</span>
  {/if}
</div>

<style>
  .bin {
    border: 2px dashed var(--panel-border);
    border-radius: 12px;
    padding: 0.75rem 1rem;
    text-align: center;
    background: #f0e8dc;
    transition:
      border-color 0.15s,
      background 0.15s;
  }

  .bin.ready {
    border-color: var(--accent);
    background: #fff5e8;
  }

  .bin.over {
    border-color: var(--ok);
    background: #e8f4ea;
    transform: scale(1.01);
  }

  .bin.disabled {
    opacity: 0.5;
  }

  .icon {
    display: block;
    font-size: 1.5rem;
    margin-bottom: 0.25rem;
  }

  .label {
    display: block;
    font-weight: 600;
    font-size: 0.85rem;
    color: var(--panel-header);
  }

  .hint {
    display: block;
    margin-top: 0.25rem;
    font-size: 0.72rem;
    color: var(--text-soft);
  }
</style>
