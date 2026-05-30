import { writable } from "svelte/store";
import type { DragPayload } from "$lib/dnd/types";

/** Текущий перетаскиваемый объект (подсветка зон сброса). */
export const activeDrag = writable<DragPayload | null>(null);

/** Cursor position while dragging (watering-can follower). */
export const dragPointer = writable<{ x: number; y: number } | null>(null);
