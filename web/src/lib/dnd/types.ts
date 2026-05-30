export type DragPayload =
  | { kind: "seed"; plantId: string }
  | { kind: "harvest"; productId: string }
  | { kind: "sabotage"; sabotageId: string }
  | { kind: "watering_can" }
  | { kind: "animal"; animalId: string };

export const DND_MIME = "application/x-farm-wars";

export function dragKey(payload: DragPayload): string {
  switch (payload.kind) {
    case "seed":
      return `seed:${payload.plantId}`;
    case "harvest":
      return `harvest:${payload.productId}`;
    case "sabotage":
      return `sab:${payload.sabotageId}`;
    case "watering_can":
      return "watering_can";
    case "animal":
      return `animal:${payload.animalId}`;
  }
}
