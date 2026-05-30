import { WATERING_CAN_RADIUS } from "$lib/game/constants";

/** Approx. rendered garden tile size — scales follower to match grid splash. */
export const WATERING_TILE_PX = 76;
export const WATERING_CAN_PX = 30;
export const WATERING_GAP_PX = 5;

const TRANSPARENT_DRAG_IMG =
  "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7";

let emptyDragImg: HTMLImageElement | null = null;

/** Circle diameter ≈ span of watered cells on the garden grid. */
export function wateringSplashDiameterPx(): number {
  const spanCells = WATERING_CAN_RADIUS * 2 + 1;
  return spanCells * WATERING_TILE_PX * 0.92;
}

/** Hide native chip ghost; follower overlay draws can + ring at cursor. */
export function useTransparentDragImage(e: DragEvent): void {
  if (!e.dataTransfer) return;
  if (!emptyDragImg) {
    emptyDragImg = new Image();
    emptyDragImg.src = TRANSPARENT_DRAG_IMG;
  }
  e.dataTransfer.setDragImage(emptyDragImg, 0, 0);
}
