import { DND_MIME, type DragPayload } from "./types";

export function writeDrag(dt: DataTransfer, payload: DragPayload): void {
  const json = JSON.stringify(payload);
  dt.setData(DND_MIME, json);
  dt.setData("text/plain", json);
  dt.effectAllowed = "copy";
}

export function readDrag(dt: DataTransfer): DragPayload | null {
  const raw = dt.getData(DND_MIME) || dt.getData("text/plain");
  if (!raw) return null;
  try {
    const p = JSON.parse(raw) as DragPayload;
    if (p && typeof p === "object" && "kind" in p) return p;
  } catch {
    /* ignore */
  }
  return null;
}
