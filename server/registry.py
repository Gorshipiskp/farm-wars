"""In-memory match registry: create, join by code."""

import random
import string
import uuid

from db.loader import GameContentCatalog
from server.match import Match


class MatchRegistry:
    def __init__(self, catalog: GameContentCatalog):
        self.catalog = catalog
        self._matches: dict[str, Match] = {}
        self._join_codes: dict[str, str] = {}

    def create_match(self, host_name: str | None = None) -> dict:
        match_id = f"match-{uuid.uuid4().hex[:8]}"
        join_code = self._generate_join_code()
        match = Match(match_id, join_code, self.catalog)
        self._matches[match_id] = match
        self._join_codes[join_code] = match_id

        if host_name:
            match.add_player(host_name)

        return {
            "contract_version": "v1",
            "match_id": match_id,
            "join_code": join_code,
        }

    def join_match(self, join_code: str, player_name: str) -> dict:
        code = join_code.strip().upper()
        match_id = self._join_codes.get(code)
        if match_id is None:
            raise KeyError("INVALID_JOIN_CODE")

        match = self._matches[match_id]
        player_id = match.add_player(player_name)
        return {
            "contract_version": "v1",
            "match_id": match_id,
            "player_id": player_id,
        }

    def get_match(self, match_id: str) -> Match:
        match = self._matches.get(match_id)
        if match is None:
            raise KeyError("UNKNOWN_MATCH")
        return match

    def start_match(self, match_id: str) -> None:
        self.get_match(match_id).start()

    def list_match_ids(self) -> list[str]:
        return list(self._matches.keys())

    def _generate_join_code(self) -> str:
        alphabet = string.ascii_uppercase + string.digits
        for _ in range(100):
            code = "".join(random.choices(alphabet, k=6))
            if code not in self._join_codes:
                return code
        raise RuntimeError("Could not allocate join code")
