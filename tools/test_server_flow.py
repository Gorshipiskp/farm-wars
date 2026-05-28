"""
Integration tests for server/001 checkpoints.

Run from repo root (after init_db --seed):
    py tools/test_server_flow.py
"""

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from server.game_server import GameServer


def test_join_flow():
    print("\n--- CP1: Join flow (2 players, same code) ---")
    game = GameServer()
    created = game.create_match("Host")
    join_code = created["join_code"]
    match_id = created["match_id"]

    j1 = game.join_match(join_code, "Guest")
    assert j1["match_id"] == match_id
    assert j1["player_id"] == "p2"

    match = game.registry.get_match(match_id)
    assert len(match.players) == 2
    print(f"  [OK] match={match_id} code={join_code} players=p1,p2")

    try:
        game.join_match("BADCODE", "Hacker")
        raise AssertionError("expected KeyError")
    except KeyError as e:
        assert e.args[0] == "INVALID_JOIN_CODE"
    print("  [OK] invalid join code rejected")


def test_tick_loop_and_sync():
    print("\n--- CP2: Tick loop publishes StateSync ---")
    game = GameServer(tick_interval_sec=0.2)
    created = game.create_match("Alice")
    match_id = created["match_id"]
    game.join_match(created["join_code"], "Bob")
    game.start_match(match_id)
    game.start_ticks()

    sync = None
    for _ in range(30):
        time.sleep(0.2)
        sync = game.get_sync(match_id, 0)
        if sync and sync["tick_id"] >= 1:
            break

    game.stop_ticks()
    assert sync is not None, "no sync received"
    assert sync["contract_version"] == "v1"
    assert sync["world_state"]["match_id"] == match_id
    assert sync["tick_id"] >= 1
    print(f"  [OK] sync tick_id={sync['tick_id']}")


def test_engine_integration():
    print("\n--- CP3: Player action affects world ---")
    game = GameServer(tick_interval_sec=0.2)
    created = game.create_match("Farmer")
    match_id = created["match_id"]
    game.start_match(match_id)

    match = game.registry.get_match(match_id)
    tile_id = "p1_t1"
    assert match.world_state is not None
    before = _tile_water(match.world_state, tile_id)

    game.submit_action({
        "contract_version": "v1",
        "match_id": match_id,
        "player_id": "p1",
        "action": {
            "contract_version": "v1",
            "player_id": "p1",
            "action_type": "WATER_PLANT",
            "payload": {"tile_id": tile_id},
            "client_ts": 1000,
        },
    })

    game.start_ticks()
    sync = None
    for _ in range(30):
        time.sleep(0.2)
        sync = game.get_sync(match_id, 0)
        if sync and any(e["event_type"] == "PLANT_WATERED" for e in sync.get("events", [])):
            break
    game.stop_ticks()

    assert sync is not None
    after = _tile_water(sync["world_state"], tile_id)
    assert after == 100, f"expected water 100, got {after} (before={before})"
    print(f"  [OK] WATER_PLANT: {before} -> {after}")


def test_win_condition():
    print("\n--- CP4: Win when target product in inventory ---")
    game = GameServer()
    created = game.create_match("Winner")
    match_id = created["match_id"]
    game.start_match(match_id)
    match = game.registry.get_match(match_id)

    game.submit_action({
        "contract_version": "v1",
        "match_id": match_id,
        "player_id": "p1",
        "action": {
            "contract_version": "v1",
            "player_id": "p1",
            "action_type": "START_RECIPE",
            "payload": {
                "factory_id": "p1_bakery_1",
                "recipe_id": "bread",
                "duration_sec": 1,
            },
            "client_ts": 1000,
        },
    })

    simulate = game.simulate_tick
    for _ in range(3):
        match.process_tick(simulate)

    assert match.status == match.FINISHED
    assert match.world_state["win_condition"]["winner_player_id"] == "p1"
    finished = [e for e in match.sync_history[-1]["events"] if e["event_type"] == "MATCH_FINISHED"]
    assert finished, "MATCH_FINISHED event expected"
    print(f"  [OK] winner=p1 events={[e['event_type'] for e in match.sync_history[-1]['events']]}")


def _tile_water(world_state: dict, tile_id: str) -> int | None:
    for tile in world_state["map"]["tiles"]:
        if tile["tile_id"] == tile_id:
            return tile.get("water_level")
    return None


def main():
    print("=" * 60)
    print("SERVER FLOW TEST — server/001")
    print("=" * 60)
    if not os.path.isfile(os.path.join(ROOT, "db", "farm_wars.db")):
        print("Run: py tools/init_db.py --seed", file=sys.stderr)
        sys.exit(1)

    test_join_flow()
    test_tick_loop_and_sync()
    test_engine_integration()
    test_win_condition()
    print("\n" + "=" * 60)
    print("ALL SERVER CHECKS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
