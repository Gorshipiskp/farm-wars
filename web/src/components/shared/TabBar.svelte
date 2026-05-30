<script lang="ts">
  export interface TabItem {
    id: string;
    label: string;
    badge?: string | number;
  }

  interface Props {
    tabs: TabItem[];
    activeId: string;
    onSelect: (id: string) => void;
    compact?: boolean;
  }

  let { tabs, activeId, onSelect, compact = false }: Props = $props();
</script>

<div class="tabbar" class:compact role="tablist">
  {#each tabs as tab (tab.id)}
    <button
      type="button"
      role="tab"
      class="tab"
      class:active={activeId === tab.id}
      aria-selected={activeId === tab.id}
      onclick={() => onSelect(tab.id)}
    >
      {tab.label}
      {#if tab.badge != null && tab.badge !== ""}
        <span class="badge">{tab.badge}</span>
      {/if}
    </button>
  {/each}
</div>

<style>
  .tabbar {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    padding: 0.25rem;
    background: #ebe3d6;
    border-radius: 10px;
    border: 1px solid var(--panel-border);
  }

  .tabbar.compact .tab {
    padding: 0.3rem 0.55rem;
    font-size: 0.78rem;
  }

  .tab {
    flex: 1 1 auto;
    min-width: 0;
    padding: 0.45rem 0.75rem;
    border: none;
    border-radius: 8px;
    background: transparent;
    color: var(--text-soft);
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition:
      background 0.15s,
      color 0.15s;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.35rem;
  }

  .tab:hover {
    background: rgba(255, 255, 255, 0.45);
    color: var(--text);
  }

  .tab.active {
    background: var(--panel-bg);
    color: var(--panel-header);
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  }

  .badge {
    font-size: 0.7rem;
    padding: 0.1rem 0.35rem;
    border-radius: 6px;
    background: var(--accent);
    color: var(--text-on-dark);
    font-weight: 600;
  }
</style>
