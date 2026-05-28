"""
Client network adapter tests (no pygame display).

Requires server running OR uses in-process pattern:
This test only hits HTTP — start server manually for full test,
or we test error handling when server is down.

Run:
    py tools/test_client_net.py
    # with server: py -m server (other terminal)
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from client.net import ServerClient, ServerError


def test_offline_error():
    print("\n--- CP4: Network error without crash ---")
    client = ServerClient(base_url="http://127.0.0.1:1", timeout_sec=0.5)
    try:
        client.health()
        print("  [SKIP] port 1 accepted connection unexpectedly")
    except ServerError as exc:
        assert exc.error_code in ("NETWORK_ERROR", "HTTP_ERROR")
        print(f"  [OK] ServerError: {exc.error_code}")


def test_lobby_flow_http():
    print("\n--- CP1: create + join via HTTP ---")
    client = ServerClient()
    try:
        client.health()
    except ServerError:
        print("  [SKIP] server not running — start: py -m server")
        return

    created = client.create_match("HostUI")
    code = created["join_code"]
    mid = created["match_id"]
    joined = client.join_match(code, "GuestUI")
    assert joined["match_id"] == mid
    assert joined["player_id"] == "p2"
    print(f"  [OK] create+join match={mid} code={code}")

    started = client.start_match(mid)
    assert started["status"] == "RUNNING"
    print("  [OK] match started")

    action = client.make_action("p1", "WATER_PLANT", {"tile_id": "p1_t1"})
    client.submit_action(mid, "p1", action)
    print("  [OK] action submitted")

    import time
    time.sleep(1.2)
    sync = client.poll_sync(mid, 0)
    assert sync["contract_version"] == "v1"
    assert "world_state" in sync
    print(f"  [OK] sync tick={sync['tick_id']}")


def main():
    print("=" * 60)
    print("CLIENT NET TEST — client/001 (NIKITA zone)")
    print("=" * 60)
    test_offline_error()
    test_lobby_flow_http()
    print("\n" + "=" * 60)
    print("DONE (UI: manual py -m client)")
    print("=" * 60)


if __name__ == "__main__":
    main()
