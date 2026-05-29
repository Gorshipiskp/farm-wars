"""Resolve plant_id from tile occupant_id (fixture instances vs catalog ids)."""

PLANT_IDS = (
    "wheat", "corn", "potato",
    "tomato", "carrot", "sunflower",
)


def resolve_plant_id(occupant_id: str | None) -> str | None:
    if not occupant_id:
        return None
    if occupant_id in PLANT_IDS:
        return occupant_id
    for plant_id in PLANT_IDS:
        if f"_{plant_id}" in occupant_id or occupant_id.endswith(plant_id):
            return plant_id
    return occupant_id
