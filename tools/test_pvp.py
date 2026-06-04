"""
PvP sabotage and cross-player rules.

Run: py tools/test_pvp.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from server.game_server import GameServer


def _action(match_id: str, player_id: str, action_type: str, payload: dict) -> dict:
    return {
        "contract_version": "v1",
        "match_id": match_id,
        "player_id": player_id,
        "action": {
            "contract_version": "v1",
            "player_id": player_id,
            "action_type": action_type,
            "payload": payload,
            "client_ts": 0,
        },
    }


def _tiles_for(world: dict, owner: str) -> list[dict]:
    return [t for t in world["map"]["tiles"] if t.get("owner_player_id") == owner]


def _plant_tile(world: dict, owner: str, index: int = 0) -> str:
    plants = [t for t in _tiles_for(world, owner) if t.get("zone_type") == "PLANT"]
    return plants[index]["tile_id"]


def _setup_two_player_match():
    game = GameServer()
    created = game.create_match("Host")
    mid = created["match_id"]
    game.join_match(created["join_code"], "Guest")
    game.start_match(mid)
    match = game.registry.get_match(mid)
    for pid in ("p1", "p2"):
        p = next(x for x in match.world_state["players"] if x["player_id"] == pid)
        p["money_bestiki"] = 200
    return game, mid, match


def test_sabotage_own_tile_rejected():
    print("\n--- PvP: sabotage on own tile -> SABOTAGE_FAILED ---")
    game, mid, match = _setup_two_player_match()
    own = _plant_tile(match.world_state, "p1")
    r = game.submit_action(_action(mid, "p1", "APPLY_SABOTAGE", {
        "sabotage_id": "poison_water",
        "target_tile_id": own,
    }))
    failed = [e for e in r["sync"]["events"] if e["event_type"] == "SABOTAGE_FAILED"]
    assert failed and failed[0]["payload"]["reason"] == "OWN_TILE"
    print("  [OK] OWN_TILE")


def test_sabotage_poison_water():
    print("\n--- PvP: poison_water reduces enemy water ---")
    game, mid, match = _setup_two_player_match()
    victim = _plant_tile(match.world_state, "p1")
    tile = next(t for t in match.world_state["map"]["tiles"] if t["tile_id"] == victim)
    tile["water_level"] = 80
    tile["occupant_type"] = "PLANT"
    tile["occupant_id"] = "wheat"

    r = game.submit_action(_action(mid, "p2", "APPLY_SABOTAGE", {
        "sabotage_id": "poison_water",
        "target_tile_id": victim,
    }))
    applied = [e for e in r["sync"]["events"] if e["event_type"] == "SABOTAGE_APPLIED"]
    assert applied and applied[0]["payload"]["effect"] == "WATER_REDUCED"
    assert tile["water_level"] == 50
    p2 = next(x for x in match.world_state["players"] if x["player_id"] == "p2")
    assert p2["money_bestiki"] == 180
    print(f"  [OK] water 80 -> {tile['water_level']}, paid 20 B")


def test_clear_mine_after_mined():
    print("\n--- PvP: CLEAR_MINE removes MINED flag ---")
    game, mid, match = _setup_two_player_match()
    victim_tile = _plant_tile(match.world_state, "p1")
    tile = next(t for t in match.world_state["map"]["tiles"] if t["tile_id"] == victim_tile)
    tile.setdefault("flags", []).append("MINED")

    r = game.submit_action(_action(mid, "p1", "CLEAR_MINE", {"tile_id": victim_tile}))
    cleared = [e for e in r["sync"]["events"] if e["event_type"] == "MINE_CLEARED"]
    assert cleared, "expected MINE_CLEARED"
    assert "MINED" not in (tile.get("flags") or [])
    print("  [OK] MINED cleared on own tile")


def test_minesweeper_lost_blasts_neighbors():
    print("\n--- PvP: MINESWEEPER_LOST destroys adjacent plants ---")
    game, mid, match = _setup_two_player_match()
    tiles = [t for t in match.world_state["map"]["tiles"] if t["owner_player_id"] == "p1" and t["zone_type"] == "PLANT"]
    tiles.sort(key=lambda t: t["tile_id"])
    center = tiles[4]
    neighbor = tiles[5]
    center["flags"] = ["MINED"]
    center["occupant_type"] = "PLANT"
    center["occupant_id"] = "wheat"
    neighbor["occupant_type"] = "PLANT"
    neighbor["occupant_id"] = "corn"

    r = game.submit_action(_action(mid, "p1", "MINESWEEPER_LOST", {"tile_id": center["tile_id"]}))
    blast = [e for e in r["sync"]["events"] if e["event_type"] == "MINESWEEPER_BLAST"]
    assert blast
    assert neighbor["occupant_type"] == "EMPTY"
    assert "MINED" in (center.get("flags") or [])
    print("  [OK] neighbor plant cleared, mine remains")


def test_place_on_mined_tile_fails():
    print("\n--- PvP: PLACE_ON_TILE on MINED tile rejected ---")
    game, mid, match = _setup_two_player_match()
    tile = _plant_tile(match.world_state, "p1")
    t = next(x for x in match.world_state["map"]["tiles"] if x["tile_id"] == tile)
    t.setdefault("flags", []).append("MINED")
    sim = game.simulate_tick
    game.submit_action(_action(mid, "p1", "PLACE_ON_TILE", {"tile_id": tile, "plant_id": "wheat"}))
    match.process_tick(sim)
    sync = game.get_sync(mid, 0)
    failed = [e for e in sync["events"] if e.get("event_type") == "PLACE_FAILED"]
    assert failed and failed[-1]["payload"]["reason"] == "MINED_TILE"
    print("  [OK] PLACE_FAILED MINED_TILE")


def test_clear_mine_not_mined_fails():
    print("\n--- PvP: CLEAR_MINE on clean tile fails ---")
    game, mid, match = _setup_two_player_match()
    own = _plant_tile(match.world_state, "p1")
    r = game.submit_action(_action(mid, "p1", "CLEAR_MINE", {"tile_id": own}))
    failed = [e for e in r["sync"]["events"] if e["event_type"] == "CLEAR_MINE_FAILED"]
    assert failed and failed[0]["payload"]["reason"] == "NOT_MINED"
    print("  [OK] NOT_MINED")


def test_sabotage_mine_flag():
    print("\n--- PvP: mine_tile sets MINED flag ---")
    game, mid, match = _setup_two_player_match()
    victim = _plant_tile(match.world_state, "p1")
    tile = next(t for t in match.world_state["map"]["tiles"] if t["tile_id"] == victim)

    r = game.submit_action(_action(mid, "p2", "APPLY_SABOTAGE", {
        "sabotage_id": "mine_tile",
        "target_tile_id": victim,
    }))
    applied = [e for e in r["sync"]["events"] if e["event_type"] == "SABOTAGE_APPLIED"]
    assert applied and applied[0]["payload"]["effect"] == "MINE_PLACED"
    assert "MINED" in (tile.get("flags") or [])
    print("  [OK] MINED flag on enemy tile")


def test_sabotage_disease_on_plant():
    print("\n--- PvP: spread_disease damages plant ---")
    game, mid, match = _setup_two_player_match()
    victim = _plant_tile(match.world_state, "p1")
    tile = next(t for t in match.world_state["map"]["tiles"] if t["tile_id"] == victim)
    tile["occupant_type"] = "PLANT"
    tile["occupant_id"] = "wheat"
    tile["health"] = 100

    r = game.submit_action(_action(mid, "p2", "APPLY_SABOTAGE", {
        "sabotage_id": "spread_disease",
        "target_tile_id": victim,
    }))
    applied = [e for e in r["sync"]["events"] if e["event_type"] == "SABOTAGE_APPLIED"]
    assert applied and applied[0]["payload"]["effect"] == "PLANT_DAMAGED"
    assert tile["health"] == 60
    assert "INFECTED" in (tile.get("flags") or [])
    print(f"  [OK] health 100 -> {tile['health']}, INFECTED")


def test_sabotage_not_enough_money():
    print("\n--- PvP: NOT_ENOUGH_MONEY ---")
    game, mid, match = _setup_two_player_match()
    p2 = next(x for x in match.world_state["players"] if x["player_id"] == "p2")
    p2["money_bestiki"] = 5
    victim = _plant_tile(match.world_state, "p1")

    r = game.submit_action(_action(mid, "p2", "APPLY_SABOTAGE", {
        "sabotage_id": "poison_water",
        "target_tile_id": victim,
    }))
    failed = [e for e in r["sync"]["events"] if e["event_type"] == "SABOTAGE_FAILED"]
    assert failed and failed[0]["payload"]["reason"] == "NOT_ENOUGH_MONEY"
    print("  [OK] broke attacker cannot sabotage")


def test_catalog_exposes_sabotages():
    print("\n--- PvP: catalog API lists sabotages ---")
    game = GameServer()
    from server.catalog_api import catalog_for_client

    payload = catalog_for_client(game.catalog)
    ids = {s["sabotage_id"] for s in payload["sabotages"]}
    assert ids >= {"poison_water", "mine_tile", "spread_disease"}
    print(f"  [OK] sabotages in catalog: {sorted(ids)}")


def test_stipend_when_broke():
    print("\n--- Economy: stipend when balance is low ---")
    import os

    os.environ["FARM_WARS_STIPEND_PROB"] = "1.0"
    from server.stipend import apply_stipends, poverty_threshold

    game, mid, match = _setup_two_player_match()
    p1 = next(x for x in match.world_state["players"] if x["player_id"] == "p1")
    p1["money_bestiki"] = 2
    threshold = poverty_threshold(game.catalog)
    assert p1["money_bestiki"] < threshold

    from shared.game_pacing import ticks_for_real_seconds

    tick_id = ticks_for_real_seconds(45)
    events = apply_stipends(match.world_state, game.catalog, tick_id)

    assert events, "expected stipend at interval tick with prob=1"
    assert p1["money_bestiki"] >= 2 + 5
    assert events[0]["event_type"] == "STIPEND_GRANTED"
    print(f"  [OK] p1 {2} -> {p1['money_bestiki']} B, threshold={threshold}")


def main() -> int:
    print("=" * 60)
    print("PVP / SABOTAGE TESTS")
    print("=" * 60)
    if not os.path.isfile(os.path.join(ROOT, "db", "farm_wars.db")):
        print("Run: py tools/init_db.py --seed", file=sys.stderr)
        return 1

    test_catalog_exposes_sabotages()
    test_sabotage_own_tile_rejected()
    test_sabotage_poison_water()
    test_clear_mine_after_mined()
    test_minesweeper_lost_blasts_neighbors()
    test_place_on_mined_tile_fails()
    test_clear_mine_not_mined_fails()
    test_sabotage_mine_flag()
    test_sabotage_disease_on_plant()
    test_sabotage_not_enough_money()
    test_stipend_when_broke()
    print("\n" + "=" * 60)
    print("ALL PVP CHECKS PASSED")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
