"""v2 Stream A — blueprint features schema + optional parquet export."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from poker_ai.features.blueprint_schema import validate_row
from poker_ai.features.export_parquet import validate_blueprint_file
from poker_ai.features.info_set import encode_hand_tensor
from poker_ai.features.parallel import _encode_record
from poker_ai.ingest.records import ParsedAction, ParsedHand, ParsedPlayer


def _fixture_hand() -> ParsedHand:
    return ParsedHand(
        hand_id=1,
        stakes="0.05/0.10",
        game_type="NLH",
        num_players=2,
        small_blind=5.0,
        big_blind=10.0,
        hero_position="BTN",
        hero_cards="As Kh",
        board_cards="Qs Jh 2h",
        pot_preflop=50.0,
        pot_flop=50.0,
        pot_turn=0.0,
        pot_river=0.0,
        players=(
            ParsedPlayer(1, "BTN", 100.0, 100.0, True, "hero", None),
            ParsedPlayer(2, "BB", 100.0, 100.0, False, "villain", None),
        ),
        actions=(
            ParsedAction(1, "BTN", "Preflop", "Raise", 20.0, False, 100.0, 10.0, 30.0, 2.0),
            ParsedAction(2, "BB", "Preflop", "Call", 20.0, False, 100.0, 30.0, 50.0, None),
        ),
    )


def main() -> int:
    hand = _fixture_hand()
    import time

    t0 = time.perf_counter()
    for _ in range(19_000):
        encode_hand_tensor(hand)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    per_hand_us = elapsed_ms / 19_000 * 1000
    if per_hand_us > 5000:
        print(f"FAIL: encode {per_hand_us:.1f} us/hand (want <5ms)")
        return 1

    row = _encode_record(hand, blueprint_full=True)
    errs = validate_row(row, blueprint_full=True)
    if errs:
        print("FAIL: extended row validation:", errs)
        return 1

    features_path = Path("features.jsonl")
    if features_path.is_file():
        report = validate_blueprint_file(features_path, blueprint_full=False)
        if not report["schema_ok"]:
            print("FAIL: features.jsonl schema:", report["errors"][:3])
            return 1
        print(f"features.jsonl OK: {report['hands_checked']} hands")

    print(f"OK: schema valid, encode {per_hand_us:.0f} us/hand")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
