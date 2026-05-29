"""
Multiplayer integration tests (2+ players): join, start, sync, actions, sabotage.

Run from repo root:
    py tools/init_db.py --seed
    py tools/test_multiplayer.py
"""

from __future__ import annotations

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


def _guest_sees_match(game: GameServer, match_id: str) -> dict:
    """Simulate client lobby poll after host started."""
    sync = game.get_sync(match_id, 0)
    assert sync is not None, "guest poll: expected sync after start"
    assert sync.get("world_state"), "guest poll: expected world_state"
    return sync


def test_three_players_join_and_world():
    print("\n--- MP: 3 players join, start, world layout ---")
    game = GameServer()
    created = game.create_match("Host")
    mid = created["match_id"]
    code = created["join_code"]

    j2 = game.join_match(code, "Alice")
    j3 = game.join_match(code, "Bob")
    assert j2["player_id"] == "p2"
    assert j3["player_id"] == "p3"

    match = game.registry.get_match(mid)
    assert len(match.players) == 3

    game.start_match(mid)
    world = match.world_state
    assert world is not None

    owners = {t["owner_player_id"] for t in world["map"]["tiles"]}
    assert owners == {"p1", "p2", "p3"}

    for pid in ("p1", "p2", "p3"):
        tiles = _tiles_for(world, pid)
        assert len(tiles) >= 8, f"{pid} should have 8 farm tiles, got {len(tiles)}"
        factories = [f for f in world["factories"] if f["owner_player_id"] == pid]
        assert len(factories) == 3, f"{pid} should have bakery + dairy + meat"

    sync2 = _guest_sees_match(game, mid)
    sync3 = _guest_sees_match(game, mid)
    assert len(sync2["world_state"]["players"]) == 3
    assert len(sync3["world_state"]["players"]) == 3
    print("  [OK] 3 players, separate farms, guests receive sync")


def test_join_after_start_rejected():
    print("\n--- MP: join after match started ---")
    game = GameServer()
    created = game.create_match("Host")
    mid = created["match_id"]
    game.start_match(mid)
    try:
        game.join_match(created["join_code"], "Late")
        raise AssertionError("expected ValueError MATCH_ALREADY_STARTED")
    except ValueError as e:
        assert "MATCH_ALREADY_STARTED" in str(e)
    print("  [OK] late join rejected")


def test_two_players_independent_actions():
    print("\n--- MP: p1 and p2 actions on own tiles only ---")
    game = GameServer()
    created = game.create_match("Host")
    mid = created["match_id"]
    game.join_match(created["join_code"], "Guest")
    game.start_match(mid)
    match = game.registry.get_match(mid)
    sim = game.simulate_tick

    p1_tile = _tiles_for(match.world_state, "p1")[2]["tile_id"]
    p2_tile = _tiles_for(match.world_state, "p2")[2]["tile_id"]

    game.submit_action(_action(mid, "p1", "WATER_PLANT", {"tile_id": p1_tile}))
    match.process_tick(sim)
    w1 = next(t for t in match.world_state["map"]["tiles"] if t["tile_id"] == p1_tile)
    assert (w1.get("water_level") or 0) >= 50

    game.submit_action(_action(mid, "p2", "WATER_PLANT", {"tile_id": p2_tile}))
    match.process_tick(sim)
    w2 = next(t for t in match.world_state["map"]["tiles"] if t["tile_id"] == p2_tile)
    assert (w2.get("water_level") or 0) >= 50

    game.submit_action(_action(mid, "p2", "WATER_PLANT", {"tile_id": p1_tile}))
    cross_tick = match.process_tick(sim)
    assert cross_tick is not None
    tick_events = cross_tick["events"]
    errors = [e for e in tick_events if e.get("event_type") == "CONTRACT_ERROR"]
    watered = [e for e in tick_events if e.get("event_type") == "PLANT_WATERED"]
    assert errors and not watered, "p2 watering p1 tile should fail"
    print("  [OK] each player waters own farm; cross-owner blocked")


def test_three_player_sabotage_chain():
    print("\n--- MP: 3 players — sabotage targets correct owner ---")
    game = GameServer()
    created = game.create_match("Host")
    mid = created["match_id"]
    game.join_match(created["join_code"], "Alice")
    game.join_match(created["join_code"], "Bob")
    game.start_match(mid)
    match = game.registry.get_match(mid)

    for pid, money in (("p2", 100), ("p3", 100)):
        p = next(x for x in match.world_state["players"] if x["player_id"] == pid)
        p["money_bestiki"] = money

    p1_plant = _tiles_for(match.world_state, "p1")[0]["tile_id"]
    game.submit_action(_action(mid, "p2", "APPLY_SABOTAGE", {
        "sabotage_id": "poison_water",
        "target_tile_id": p1_plant,
    }))
    sync = match.latest_sync(0)
    ok = [e for e in sync["events"] if e["event_type"] == "SABOTAGE_APPLIED"]
    assert ok and ok[0]["payload"]["target_player_id"] == "p1"

    p2_plant = _tiles_for(match.world_state, "p2")[0]["tile_id"]
    game.submit_action(_action(mid, "p3", "APPLY_SABOTAGE", {
        "sabotage_id": "poison_water",
        "target_tile_id": p2_plant,
    }))
    sync = match.latest_sync(0)
    ok3 = [e for e in sync["events"] if e["event_type"] == "SABOTAGE_APPLIED"]
    assert ok3 and ok3[-1]["payload"]["target_player_id"] == "p2"
    print("  [OK] p2 sabotages p1, p3 sabotages p2")


def test_win_only_one_winner_two_players():
    print("\n--- MP: first to bread wins, other player stays in match until sync ---")
    game = GameServer()
    created = game.create_match("Host")
    mid = created["match_id"]
    game.join_match(created["join_code"], "Guest")
    game.start_match(mid)
    match = game.registry.get_match(mid)
    match.world_state["win_condition"]["target_product_id"] = "bread"
    match.world_state["players"][0]["inventory"] = [
        {"product_id": "flour", "amount": 2},
        {"product_id": "wheat", "amount": 1},
    ]
    sim = game.simulate_tick
    bread_ticks = game.catalog.recipes["bread"].production_time_sec

    game.submit_action(_action(mid, "p1", "START_RECIPE", {
        "factory_id": "p1_bakery_1",
        "recipe_id": "bread",
    }))
    for _ in range(bread_ticks + 10):
        match.process_tick(sim)
        if match.status == match.FINISHED:
            break

    assert match.status == match.FINISHED
    assert match.world_state["win_condition"]["winner_player_id"] == "p1"
    p2 = match.world_state["players"][1]
    assert not any(i["product_id"] == "bread" and i["amount"] >= 1 for i in p2.get("inventory", []))
    sync_guest = game.get_sync(mid, 0)
    assert sync_guest["world_state"]["win_condition"]["winner_player_id"] == "p1"
    print("  [OK] winner=p1, p2 sees finished state via sync")


def test_duplicate_player_ids_per_join():
    print("\n--- MP: sequential joins get unique player_id ---")
    game = GameServer()
    created = game.create_match("A")
    code = created["join_code"]
    ids = ["p1"]
    for name in ("B", "C", "D"):
        r = game.join_match(code, name)
        ids.append(r["player_id"])
    assert ids == ["p1", "p2", "p3", "p4"]
    print("  [OK] p1..p4 for host + 3 guests")


def main() -> int:
    print("=" * 60)
    print("MULTIPLAYER TESTS (2+ players)")
    print("=" * 60)
    if not os.path.isfile(os.path.join(ROOT, "db", "farm_wars.db")):
        print("Run: py tools/init_db.py --seed", file=sys.stderr)
        return 1

    test_three_players_join_and_world()
    test_join_after_start_rejected()
    test_two_players_independent_actions()
    test_three_player_sabotage_chain()
    test_win_only_one_winner_two_players()
    test_duplicate_player_ids_per_join()
    print("\n" + "=" * 60)
    print("ALL MULTIPLAYER CHECKS PASSED")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
