"""
Vertical slice tests for gameplay/001 (2 players, win, sabotage).

Run: py tools/test_vertical_slice.py
"""

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from server.game_server import GameServer


def _action(match_id, player_id, action_type, payload):
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


def _enemy_plant_tile(match, victim_id: str) -> str:
    for tile in match.world_state["map"]["tiles"]:
        if tile.get("owner_player_id") == victim_id and tile.get("zone_type") == "PLANT":
            return tile["tile_id"]
    raise AssertionError(f"no PLANT tile for {victim_id}")


def test_two_player_join_and_sync():
    print("\n--- gameplay/001: two players join ---")
    game = GameServer(tick_interval_sec=0.15)
    created = game.create_match("Host")
    code = created["join_code"]
    mid = created["match_id"]
    j = game.join_match(code, "Guest")
    assert j["player_id"] == "p2"
    game.start_match(mid)
    game.start_ticks()

    sync = None
    for _ in range(40):
        time.sleep(0.15)
        sync = game.get_sync(mid, 0)
        if sync and sync.get("world_state"):
            break
    game.stop_ticks()

    assert sync is not None
    players = sync["world_state"]["players"]
    assert len(players) == 2
    print(f"  [OK] 2 players, tick={sync['tick_id']}")


def test_win_bread_two_player_match():
    print("\n--- gameplay/001: p1 wins with bread (2 players in match) ---")
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

    game.submit_action(_action(mid, "p1", "START_RECIPE", {
        "factory_id": "p1_bakery_1",
        "recipe_id": "bread",
    }))
    bread_ticks = game.catalog.recipes["bread"].production_time_sec
    for _ in range(bread_ticks + 10):
        match.process_tick(sim)
        if match.status == match.FINISHED:
            break

    assert match.status == match.FINISHED
    assert match.world_state["win_condition"]["winner_player_id"] == "p1"
    print("  [OK] MATCH_FINISHED winner=p1 (bread)")


def test_sabotage_poison_water():
    print("\n--- gameplay/008: sabotage poison_water on enemy tile ---")
    game = GameServer()
    created = game.create_match("Host")
    mid = created["match_id"]
    game.join_match(created["join_code"], "Guest")
    game.start_match(mid)
    match = game.registry.get_match(mid)

    victim_tile = _enemy_plant_tile(match, "p1")
    water_before = next(
        t["water_level"] for t in match.world_state["map"]["tiles"]
        if t["tile_id"] == victim_tile
    )
    match.world_state["players"][1]["money_bestiki"] = 100

    game.submit_action(_action(mid, "p2", "APPLY_SABOTAGE", {
        "sabotage_id": "poison_water",
        "target_tile_id": victim_tile,
    }))
    sync = match.latest_sync(0)
    applied = [e for e in sync["events"] if e["event_type"] == "SABOTAGE_APPLIED"]
    assert applied, f"events={[e['event_type'] for e in sync['events']]}"

    tile = next(t for t in match.world_state["map"]["tiles"] if t["tile_id"] == victim_tile)
    assert tile["water_level"] == max(0, water_before - 30)
    print(f"  [OK] water {water_before} -> {tile['water_level']}")


def main():
    print("=" * 60)
    print("VERTICAL SLICE / gameplay/001")
    print("=" * 60)
    if not os.path.isfile(os.path.join(ROOT, "db", "farm_wars.db")):
        print("Run: py tools/init_db.py --seed", file=sys.stderr)
        sys.exit(1)

    test_two_player_join_and_sync()
    test_win_bread_two_player_match()
    test_sabotage_poison_water()
    print("\n" + "=" * 60)
    print("ALL VERTICAL SLICE CHECKS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
