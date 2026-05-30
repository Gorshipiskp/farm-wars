import { writable } from "svelte/store";

export type ToastKind = "ok" | "error" | "warn" | "info";

export interface Toast {
  id: number;
  message: string;
  kind: ToastKind;
}

let nextId = 1;

export const toasts = writable<Toast[]>([]);

export function pushToast(message: string, kind: ToastKind = "info"): void {
  const id = nextId++;
  toasts.update((list) => [...list.slice(-7), { id, message, kind }]);
  window.setTimeout(() => {
    toasts.update((list) => list.filter((t) => t.id !== id));
  }, 4500);
}

export function clearToasts(): void {
  toasts.set([]);
}
