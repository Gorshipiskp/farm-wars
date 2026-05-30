<script lang="ts">
  interface KeyItem {
    key: string;
    label: string;
  }

  interface Props {
    disabled?: boolean;
  }

  let { disabled = false }: Props = $props();

  const keys: KeyItem[] = [
    { key: "W", label: "уход" },
    { key: "T", label: "посадка" },
    { key: "H", label: "сбор" },
    { key: "B", label: "печь" },
    { key: "C", label: "животное" },
    { key: "V", label: "продажа" },
    { key: "1–6", label: "семена" },
  ];
</script>

<div class="hotkeys" class:disabled aria-label="Горячие клавиши">
  {#each keys as item}
    <span class="item" title={item.label}>
      <kbd>{item.key}</kbd>
      <span class="lbl">{item.label}</span>
    </span>
  {/each}
  <span class="item hint-item" title="ПКМ по клетке">
    <kbd>🖱</kbd>
    <span class="lbl">меню</span>
  </span>
</div>

<style>
  .hotkeys {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem 0.5rem;
    padding: 0.55rem 0.65rem;
    background: rgba(0, 0, 0, 0.04);
    border-radius: 10px;
    border: 1px solid rgba(110, 88, 62, 0.2);
  }

  .hotkeys.disabled {
    opacity: 0.45;
    pointer-events: none;
  }

  .item {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 0.72rem;
    color: var(--text-soft);
  }

  kbd {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 1.35rem;
    padding: 0.15rem 0.35rem;
    font-family: inherit;
    font-size: 0.68rem;
    font-weight: 700;
    background: #fff;
    border: 1px solid #c4b5a0;
    border-radius: 5px;
    box-shadow: 0 1px 0 #c4b5a0;
    color: var(--panel-header);
  }

  .lbl {
    white-space: nowrap;
  }

  .hint-item kbd {
    min-width: auto;
    padding: 0.15rem 0.4rem;
  }
</style>
