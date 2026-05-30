<script lang="ts">
  import { toasts, type ToastKind } from "$lib/stores/toasts";

  function kindClass(k: ToastKind): string {
    return k;
  }
</script>

<div class="stack" aria-live="polite">
  {#each $toasts as t (t.id)}
    <div class="toast {kindClass(t.kind)}">{t.message}</div>
  {/each}
</div>

<style>
  .stack {
    position: fixed;
    right: 1rem;
    bottom: 1rem;
    z-index: 100;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    max-width: min(360px, 90vw);
    pointer-events: none;
  }

  .toast {
    padding: 0.55rem 0.85rem;
    border-radius: 10px;
    font-size: 0.9rem;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    background: var(--panel-bg);
    border: 1px solid var(--panel-border);
  }

  .toast.ok {
    border-color: var(--ok);
    background: #e8f4ea;
  }

  .toast.error {
    border-color: var(--error);
    background: #fdecea;
  }

  .toast.warn {
    border-color: #c9a030;
    background: #fff8e6;
  }

  .toast.info {
    background: #f0e8dc;
  }
</style>
