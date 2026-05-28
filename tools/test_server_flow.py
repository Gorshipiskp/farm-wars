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


def test_place_on_tile_enriched():
    print("\n--- server/002: PLACE_ON_TILE (client payload, server enrich) ---")
    game = GameServer()
    created = game.create_match("Farmer")
    match_id = created["match_id"]
    game.start_match(match_id)
    match = game.registry.get_match(match_id)

    player = match.world_state["players"][0]
    wheat_before = _inventory_amount(player, "wheat")
    assert wheat_before >= 1, "starter inventory should include wheat seeds"

    tile_id = "p1_t3"
    game.submit_action({
        "contract_version": "v1",
        "match_id": match_id,
        "player_id": "p1",
        "action": {
            "contract_version": "v1",
            "player_id": "p1",
            "action_type": "PLACE_ON_TILE",
            "payload": {"tile_id": tile_id, "plant_id": "wheat"},
            "client_ts": 1000,
        },
    })

    match.process_tick(game.simulate_tick)
    sync = match.sync_history[-1]
    placed = [e for e in sync["events"] if e["event_type"] == "PLANT_PLACED"]
    assert placed, f"expected PLANT_PLACED, got {[e['event_type'] for e in sync['events']]}"

    tile = _find_tile(sync["world_state"], tile_id)
    assert tile["occupant_type"] == "PLANT"
    assert tile["occupant_id"] == "wheat"
    assert tile["water_level"] == 50  # wheat initial_water_level from seed

    wheat_after = _inventory_amount(sync["world_state"]["players"][0], "wheat")
    assert wheat_after == wheat_before - 1
    print(f"  [OK] PLANT_PLACED on {tile_id}, wheat {wheat_before} -> {wheat_after}")


def test_place_on_tile_unknown_plant():
    print("\n--- server/002: unknown plant_id -> CONTRACT_ERROR ---")
    game = GameServer()
    created = game.create_match("Farmer")
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
            "action_type": "PLACE_ON_TILE",
            "payload": {"tile_id": "p1_t3", "plant_id": "nonexistent_plant"},
            "client_ts": 1000,
        },
    })

    match.process_tick(game.simulate_tick)
    sync = match.sync_history[-1]
    errors = [e for e in sync["events"] if e["event_type"] == "CONTRACT_ERROR"]
    assert errors, "expected CONTRACT_ERROR for unknown plant"
    assert "Unknown plant_id" in errors[0]["payload"]["message"]
    print("  [OK] unknown plant rejected on server")


def test_buy_immediate_sync():
    print("\n--- gameplay/003: BUY immediate sync (not via tick queue) ---")
    game = GameServer()
    created = game.create_match("Shopper")
    match_id = created["match_id"]
    game.start_match(match_id)
    match = game.registry.get_match(match_id)

    assert len(match.action_queue) == 0
    game.submit_action(_action(match_id, "p1", "BUY_PRODUCT", {"product_id": "wheat", "amount": 1}))
    assert len(match.action_queue) == 0, "BUY must not sit in engine queue"
    sync = match.latest_sync(0)
    purchased = [e for e in sync["events"] if e["event_type"] == "PRODUCT_PURCHASED"]
    assert purchased, f"expected immediate PRODUCT_PURCHASED, got {[e['event_type'] for e in sync['events']]}"
    print("  [OK] immediate shop sync, queue empty")


def test_buy_product_ok():
    print("\n--- gameplay/003: BUY_PRODUCT potato ---")
    game = GameServer()
    created = game.create_match("Shopper")
    match_id = created["match_id"]
    game.start_match(match_id)
    match = game.registry.get_match(match_id)

    money_before = match.world_state["players"][0]["money_bestiki"]
    potato_before = _inventory_amount(match.world_state["players"][0], "potato")

    game.submit_action(_action(match_id, "p1", "BUY_PRODUCT", {"product_id": "potato", "amount": 1}))
    sync = match.latest_sync(0)

    purchased = [e for e in sync["events"] if e["event_type"] == "PRODUCT_PURCHASED"]
    assert purchased, f"expected PRODUCT_PURCHASED, got {[e['event_type'] for e in sync['events']]}"
    player = sync["world_state"]["players"][0]
    assert player["money_bestiki"] == money_before - 4
    assert _inventory_amount(player, "potato") == potato_before + 1
    print(f"  [OK] bought potato, money {money_before} -> {player['money_bestiki']}")


def test_buy_amount_as_float():
    print("\n--- gameplay/003: BUY_PRODUCT amount=1.0 (JSON float) ---")
    game = GameServer()
    created = game.create_match("Shopper")
    match_id = created["match_id"]
    game.start_match(match_id)
    match = game.registry.get_match(match_id)

    game.submit_action(_action(match_id, "p1", "BUY_PRODUCT", {"product_id": "wheat", "amount": 1.0}))
    sync = match.latest_sync(0)

    purchased = [e for e in sync["events"] if e["event_type"] == "PRODUCT_PURCHASED"]
    assert purchased, f"expected PRODUCT_PURCHASED, got {[e['event_type'] for e in sync['events']]}"
    print("  [OK] float amount coerced to int")


def test_sync_merges_events_since_tick():
    print("\n--- sync: events since_tick merge ---")
    game = GameServer(tick_interval_sec=0.2)
    created = game.create_match("Sync")
    match_id = created["match_id"]
    game.start_match(match_id)
    game.submit_action(_action(match_id, "p1", "BUY_PRODUCT", {"product_id": "wheat", "amount": 1}))
    game.start_ticks()
    import time
    time.sleep(0.6)
    game.stop_ticks()
    match = game.registry.get_match(match_id)
    sync0 = match.latest_sync(0)
    sync1 = match.latest_sync(1)
    assert sync0 is not None and sync1 is not None
    types0 = [e["event_type"] for e in sync0["events"]]
    assert "PRODUCT_PURCHASED" in types0, f"since 0 should include buy, got {types0}"
    assert "PRODUCT_PURCHASED" not in [e["event_type"] for e in sync1["events"]], (
        "since 1 should not repeat old buy"
    )
    print(f"  [OK] since_tick=0 events={types0}")


def test_buy_not_enough_money():
    print("\n--- gameplay/003: BUY_PRODUCT NOT_ENOUGH_MONEY ---")
    game = GameServer()
    created = game.create_match("Broke")
    match_id = created["match_id"]
    game.start_match(match_id)
    match = game.registry.get_match(match_id)
    match.world_state["players"][0]["money_bestiki"] = 3

    game.submit_action(_action(match_id, "p1", "BUY_PRODUCT", {"product_id": "wheat", "amount": 1}))
    sync = match.latest_sync(0)

    failed = [e for e in sync["events"] if e["event_type"] == "PURCHASE_FAILED"]
    assert failed, "expected PURCHASE_FAILED"
    assert failed[0]["payload"]["reason"] == "NOT_ENOUGH_MONEY"
    print("  [OK] purchase rejected when money < price")


def test_start_recipe_enriched():
    print("\n--- gameplay/003: START_RECIPE without duration_sec ---")
    game = GameServer()
    created = game.create_match("Baker")
    match_id = created["match_id"]
    game.start_match(match_id)
    match = game.registry.get_match(match_id)
    match.world_state["players"][0]["inventory"] = [
        {"product_id": "flour", "amount": 2},
        {"product_id": "wheat", "amount": 1},
    ]

    game.submit_action(_action(match_id, "p1", "START_RECIPE", {
        "factory_id": "p1_bakery_1",
        "recipe_id": "bread",
    }))
    match.process_tick(game.simulate_tick)
    sync = match.sync_history[-1]

    factory = next(f for f in sync["world_state"]["factories"] if f["factory_id"] == "p1_bakery_1")
    assert factory["active_recipe_id"] == "bread"
    # Enriched to 30s from catalog; same tick _advance_factories decrements by 1
    assert 28 <= factory["remaining_time_sec"] <= 30
    started = [e for e in sync["events"] if e["event_type"] == "RECIPE_STARTED"]
    assert started, "expected RECIPE_STARTED"
    print(f"  [OK] recipe enriched, remaining={factory['remaining_time_sec']}s")


def test_start_recipe_wrong_building():
    print("\n--- gameplay/003: START_RECIPE WRONG_BUILDING_TYPE ---")
    game = GameServer()
    created = game.create_match("WrongFactory")
    match_id = created["match_id"]
    game.start_match(match_id)
    match = game.registry.get_match(match_id)
    match.world_state["factories"][0]["factory_type"] = "DAIRY"

    game.submit_action(_action(match_id, "p1", "START_RECIPE", {
        "factory_id": "p1_bakery_1",
        "recipe_id": "bread",
    }))
    match.process_tick(game.simulate_tick)
    sync = match.sync_history[-1]

    rejected = [e for e in sync["events"] if e["event_type"] == "RECIPE_REJECTED"]
    assert rejected, f"expected RECIPE_REJECTED, got {[e['event_type'] for e in sync['events']]}"
    assert rejected[0]["payload"]["reason"] == "WRONG_BUILDING_TYPE"
    print("  [OK] bread on DAIRY factory rejected")


def test_mini_loop_buy_plant_water_bake():
    print("\n--- gameplay/003: buy -> plant -> water -> bake -> win ---")
    game = GameServer()
    created = game.create_match("Farmer")
    match_id = created["match_id"]
    game.start_match(match_id)
    match = game.registry.get_match(match_id)
    simulate = game.simulate_tick

    game.submit_action(_action(match_id, "p1", "BUY_PRODUCT", {"product_id": "potato", "amount": 1}))
    game.submit_action(_action(match_id, "p1", "PLACE_ON_TILE", {"tile_id": "p1_t3", "plant_id": "potato"}))
    match.process_tick(simulate)
    game.submit_action(_action(match_id, "p1", "WATER_PLANT", {"tile_id": "p1_t3"}))
    match.process_tick(simulate)
    game.submit_action(_action(match_id, "p1", "HARVEST_PLANT", {"tile_id": "p1_t3"}))
    game.submit_action(_action(match_id, "p1", "BUY_PRODUCT", {"product_id": "flour", "amount": 2}))
    game.submit_action(_action(match_id, "p1", "START_RECIPE", {
        "factory_id": "p1_bakery_1",
        "recipe_id": "bread",
    }))

    for _ in range(40):
        match.process_tick(simulate)
        if match.status == match.FINISHED:
            break

    assert match.status == match.FINISHED
    assert match.world_state["win_condition"]["winner_player_id"] == "p1"
    events = [e["event_type"] for e in match.sync_history[-1]["events"]]
    assert "PRODUCT_PURCHASED" in events or any(
        e["event_type"] == "PRODUCT_PURCHASED"
        for sync in match.sync_history
        for e in sync["events"]
    )
    print(f"  [OK] mini-loop finished, last events={events[-5:]}")


def test_harvest_plant():
    print("\n--- gameplay/004: HARVEST_PLANT ---")
    game = GameServer()
    created = game.create_match("Farmer")
    match_id = created["match_id"]
    game.start_match(match_id)
    match = game.registry.get_match(match_id)

    game.submit_action(_action(match_id, "p1", "PLACE_ON_TILE", {"tile_id": "p1_t3", "plant_id": "wheat"}))
    match.process_tick(game.simulate_tick)
    game.submit_action(_action(match_id, "p1", "WATER_PLANT", {"tile_id": "p1_t3"}))
    match.process_tick(game.simulate_tick)
    wheat_before = _inventory_amount(match.world_state["players"][0], "wheat")

    game.submit_action(_action(match_id, "p1", "HARVEST_PLANT", {"tile_id": "p1_t3"}))
    sync = match.latest_sync(0)
    harvested = [e for e in sync["events"] if e["event_type"] == "PLANT_HARVESTED"]
    assert harvested, f"expected PLANT_HARVESTED, got {[e['event_type'] for e in sync['events']]}"

    tile = _find_tile(sync["world_state"], "p1_t3")
    assert tile["occupant_type"] == "EMPTY"
    wheat_after = _inventory_amount(sync["world_state"]["players"][0], "wheat")
    assert wheat_after >= wheat_before + 1
    print(f"  [OK] harvested wheat, tile cleared, inv {wheat_before} -> {wheat_after}")


def test_recipe_requires_ingredients():
    print("\n--- gameplay/004: START_RECIPE without ingredients ---")
    game = GameServer()
    created = game.create_match("Baker")
    match_id = created["match_id"]
    game.start_match(match_id)
    match = game.registry.get_match(match_id)
    match.world_state["players"][0]["inventory"] = [{"product_id": "wheat", "amount": 1}]

    game.submit_action(_action(match_id, "p1", "START_RECIPE", {
        "factory_id": "p1_bakery_1",
        "recipe_id": "bread",
    }))
    match.process_tick(game.simulate_tick)
    sync = match.sync_history[-1]
    rejected = [e for e in sync["events"] if e["event_type"] == "RECIPE_REJECTED"]
    assert rejected and rejected[0]["payload"]["reason"] == "NOT_ENOUGH_INGREDIENTS"
    print("  [OK] bread rejected without flour")


def test_win_condition():
    print("\n--- CP4: Win when target product in inventory ---")
    game = GameServer()
    created = game.create_match("Winner")
    match_id = created["match_id"]
    game.start_match(match_id)
    match = game.registry.get_match(match_id)
    match.world_state["players"][0]["inventory"] = [
        {"product_id": "flour", "amount": 2},
        {"product_id": "wheat", "amount": 1},
    ]

    game.submit_action(_action(match_id, "p1", "START_RECIPE", {
        "factory_id": "p1_bakery_1",
        "recipe_id": "bread",
    }))

    simulate = game.simulate_tick
    for _ in range(40):
        match.process_tick(simulate)
        if match.status == match.FINISHED:
            break

    assert match.status == match.FINISHED
    assert match.world_state["win_condition"]["winner_player_id"] == "p1"
    finished = [e for e in match.sync_history[-1]["events"] if e["event_type"] == "MATCH_FINISHED"]
    assert finished, "MATCH_FINISHED event expected"
    print(f"  [OK] winner=p1 events={[e['event_type'] for e in match.sync_history[-1]['events']]}")


def _tile_water(world_state: dict, tile_id: str) -> int | None:
    tile = _find_tile(world_state, tile_id)
    return tile.get("water_level") if tile else None


def _find_tile(world_state: dict, tile_id: str) -> dict | None:
    for tile in world_state["map"]["tiles"]:
        if tile["tile_id"] == tile_id:
            return tile
    return None


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
            "client_ts": 1000,
        },
    }


def _inventory_amount(player: dict, product_id: str) -> int:
    for item in player.get("inventory", []):
        if item["product_id"] == product_id:
            return item["amount"]
    return 0


def main():
    print("=" * 60)
    print("SERVER FLOW TEST — server/001–002 + gameplay/003–004")
    print("=" * 60)
    if not os.path.isfile(os.path.join(ROOT, "db", "farm_wars.db")):
        print("Run: py tools/init_db.py --seed", file=sys.stderr)
        sys.exit(1)

    test_join_flow()
    test_tick_loop_and_sync()
    test_engine_integration()
    test_place_on_tile_enriched()
    test_place_on_tile_unknown_plant()
    test_buy_immediate_sync()
    test_buy_product_ok()
    test_buy_amount_as_float()
    test_sync_merges_events_since_tick()
    test_buy_not_enough_money()
    test_start_recipe_enriched()
    test_start_recipe_wrong_building()
    test_harvest_plant()
    test_recipe_requires_ingredients()
    test_mini_loop_buy_plant_water_bake()
    test_win_condition()
    print("\n" + "=" * 60)
    print("ALL SERVER CHECKS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
