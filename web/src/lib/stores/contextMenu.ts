import { writable } from "svelte/store";

export interface ContextMenuState {
  x: number;
  y: number;
  tileId: string;
}

export const contextMenu = writable<ContextMenuState | null>(null);

export function closeContextMenu(): void {
  contextMenu.set(null);
}
