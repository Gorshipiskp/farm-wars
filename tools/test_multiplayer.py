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
from shared.game_pacing import ticks_for_real_seconds
from tools.mp_test_util import (
    action_envelope as _action,
    inventory_amount,
    setup_match,
    tiles_for as _tiles_for,
)


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

    cross = game.submit_action(_action(mid, "p2", "WATER_PLANT", {"tile_id": p1_tile}))
    tick_events = cross["sync"]["events"]
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
    r1 = game.submit_action(_action(mid, "p2", "APPLY_SABOTAGE", {
        "sabotage_id": "poison_water",
        "target_tile_id": p1_plant,
    }))
    ok = [e for e in r1["sync"]["events"] if e["event_type"] == "SABOTAGE_APPLIED"]
    assert ok and ok[0]["payload"]["target_player_id"] == "p1"

    p2_plant = _tiles_for(match.world_state, "p2")[0]["tile_id"]
    r3 = game.submit_action(_action(mid, "p3", "APPLY_SABOTAGE", {
        "sabotage_id": "poison_water",
        "target_tile_id": p2_plant,
    }))
    ok3 = [e for e in r3["sync"]["events"] if e["event_type"] == "SABOTAGE_APPLIED"]
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
    bread_ticks = ticks_for_real_seconds(game.catalog.recipes["bread"].production_time_sec)

    game.submit_action(_action(mid, "p1", "START_RECIPE", {
        "factory_id": "p1_bakery_1",
        "recipe_id": "bread",
    }))
    for _ in range(bread_ticks + 25):
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


def test_four_players_world_layout():
    print("\n--- MP: 4 players, map height scales ---")
    game, mid, match = setup_match(["H", "A", "B", "C"])
    assert len(match.players) == 4
    world = match.world_state
    assert len(world["players"]) == 4
    owners = {t["owner_player_id"] for t in world["map"]["tiles"]}
    assert owners == {"p1", "p2", "p3", "p4"}
    for pid in owners:
        assert len(_tiles_for(world, pid)) >= 8
    print("  [OK] 4 farms on expanded map")


def test_join_code_case_insensitive():
    print("\n--- MP: join code trim + case ---")
    game = GameServer()
    created = game.create_match("Host")
    code = created["join_code"]
    j = game.join_match(f"  {code.lower()}  ", "Guest")
    assert j["player_id"] == "p2"
    print("  [OK] lowercase/spaces accepted")


def test_roster_lobby_and_running():
    print("\n--- MP: roster in lobby and after start ---")
    game = GameServer()
    created = game.create_match("Host")
    mid = created["match_id"]
    game.join_match(created["join_code"], "Guest")
    lobby = game.get_roster(mid)
    assert lobby["status"] == "LOBBY"
    assert lobby["host_player_id"] == "p1"
    assert len(lobby["players"]) == 2

    game.start_match(mid)
    running = game.get_roster(mid)
    assert running["status"] == "RUNNING"
    assert running["join_code"] == created["join_code"]
    print("  [OK] roster status LOBBY -> RUNNING")


def test_sync_since_tick_filters_events():
    print("\n--- MP: sync since_tick returns only newer events ---")
    game, mid, match = setup_match(["Host", "Guest"])
    sim = game.simulate_tick
    base = game.get_sync(mid, 0)
    assert base is not None
    tick0 = base["tick_id"]

    tile = _tiles_for(match.world_state, "p1")[0]["tile_id"]
    game.submit_action(_action(mid, "p1", "WATER_PLANT", {"tile_id": tile}))
    match.process_tick(sim)
    after = game.get_sync(mid, tick0)
    assert after is not None
    assert after["tick_id"] > tick0
    assert any(e.get("event_type") == "PLANT_WATERED" for e in after["events"])

    stale = game.get_sync(mid, after["tick_id"])
    assert stale is not None
    assert stale["events"] == []
    print("  [OK] since_tick filters historical events")


def test_unknown_player_action_rejected():
    print("\n--- MP: unknown player_id on action ---")
    game, mid, _match = setup_match(["Host", "Guest"])
    try:
        game.submit_action(_action(mid, "p99", "WATER_PLANT", {"tile_id": "p1_t1"}))
        raise AssertionError("expected ValueError UNKNOWN_PLAYER")
    except ValueError as exc:
        assert "UNKNOWN_PLAYER" in str(exc)
    print("  [OK] UNKNOWN_PLAYER")


def test_action_while_lobby_rejected():
    print("\n--- MP: action before match start ---")
    game = GameServer()
    created = game.create_match("Host")
    mid = created["match_id"]
    try:
        game.submit_action(_action(mid, "p1", "WATER_PLANT", {"tile_id": "p1_t1"}))
        raise AssertionError("expected ValueError MATCH_NOT_RUNNING")
    except ValueError as exc:
        assert "MATCH_NOT_RUNNING" in str(exc)
    print("  [OK] MATCH_NOT_RUNNING in lobby")


def test_sabotage_own_tile_rejected():
    print("\n--- MP: cannot sabotage own tile ---")
    game, mid, match = setup_match(["Host", "Guest"])
    p1 = next(p for p in match.world_state["players"] if p["player_id"] == "p1")
    p1["money_bestiki"] = 200
    own_tile = _tiles_for(match.world_state, "p1")[0]["tile_id"]
    result = game.submit_action(_action(mid, "p1", "APPLY_SABOTAGE", {
        "sabotage_id": "poison_water",
        "target_tile_id": own_tile,
    }))
    failed = [
        e for e in result["sync"]["events"]
        if e.get("event_type") == "SABOTAGE_FAILED"
    ]
    assert failed
    assert failed[0]["payload"]["reason"] == "OWN_TILE"
    print("  [OK] OWN_TILE blocks self-sabotage")


def test_per_player_shop_isolation():
    print("\n--- MP: BUY affects only acting player ---")
    game, mid, match = setup_match(["Host", "Guest"])
    p1_before = inventory_amount(match.world_state, "p1", "wheat_seed")
    p2_before = inventory_amount(match.world_state, "p2", "wheat_seed")

    game.submit_action(_action(mid, "p2", "BUY_PRODUCT", {
        "product_id": "wheat_seed",
        "amount": 1,
    }))
    world = match.world_state
    assert inventory_amount(world, "p2", "wheat_seed") == p2_before + 1
    assert inventory_amount(world, "p1", "wheat_seed") == p1_before
    print("  [OK] guest buy does not change host inventory")


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
    test_four_players_world_layout()
    test_join_code_case_insensitive()
    test_roster_lobby_and_running()
    test_sync_since_tick_filters_events()
    test_unknown_player_action_rejected()
    test_action_while_lobby_rejected()
    test_sabotage_own_tile_rejected()
    test_per_player_shop_isolation()
    print("\n" + "=" * 60)
    print("ALL MULTIPLAYER CHECKS PASSED")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
