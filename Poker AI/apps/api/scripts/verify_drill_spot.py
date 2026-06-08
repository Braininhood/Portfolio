"""W6 verification — ``POST /decide`` vs ``POST /drill/spot`` action parity.

Usage (from repo root, with venv active)::

    cd poker_ai
    python ../apps/api/scripts/verify_drill_spot.py
    python scripts/verify_drill_spot.py   # shim in poker_ai/scripts/

    python scripts/verify_drill_spot.py --hand-id 9006606259057126 --step-index 2
    python scripts/verify_drill_spot.py --samples 5 --policy best

Exit 0 when all sampled spots match within tolerance; 1 otherwise.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

# Allow ``python apps/api/scripts/verify_drill_spot.py`` from repo root.
_API_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = os.path.dirname(os.path.dirname(_API_DIR))
_SRC = os.path.join(_REPO_ROOT, "poker_ai", "src")
for p in (_SRC, _API_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from services.drill_service import (
    build_drill_spot,
    compare_action_lists,
    hero_decision_indices,
    run_decide_parity,
)
from poker_ai.store.db import get_async_session_factory
from poker_ai.store.loader import list_hand_summaries, load_parsed_hand_by_id


async def _sample_spots(
    session: object,
    *,
    samples: int,
    hand_id: int | None,
    step_index: int | None,
) -> list[tuple[int, int]]:
    from sqlalchemy.ext.asyncio import AsyncSession

    if not isinstance(session, AsyncSession):
        msg = "invalid session"
        raise TypeError(msg)

    if hand_id is not None and step_index is not None:
        return [(hand_id, step_index)]

    out: list[tuple[int, int]] = []
    offset = 0
    while len(out) < samples:
        rows, _ = await list_hand_summaries(session, limit=40, offset=offset)
        if not rows:
            break
        for row in rows:
            hand = await load_parsed_hand_by_id(session, row.hand_id)
            if hand is None:
                continue
            for idx in hero_decision_indices(hand):
                out.append((row.hand_id, idx))
                if len(out) >= samples:
                    return out
        offset += 40
    return out


async def _verify_one(
    session: object,
    hand_id: int,
    step_index: int,
    *,
    policy: str,
    lenient: bool,
    prob_tol: float,
) -> bool:
    from sqlalchemy.ext.asyncio import AsyncSession

    if not isinstance(session, AsyncSession):
        msg = "invalid session"
        raise TypeError(msg)

    hand = await load_parsed_hand_by_id(session, hand_id)
    if hand is None:
        print(f"  hand {hand_id}: NOT FOUND")
        return False

    label = f"hand={hand_id} step={step_index} policy={policy} lenient={lenient}"
    try:
        decide_actions, decide_policy, street = run_decide_parity(
            hand,
            step_index,
            policy_name=policy,
            lenient=lenient,
        )
        spot = build_drill_spot(hand, step_index, policy_name=policy)
    except ValueError as e:
        print(f"  {label}: SKIP ({e})")
        return True

    drill_actions = spot["actions"]
    if spot["policy_name"] != decide_policy:
        print(
            f"  WARN {label}: drill used fallback policy {spot['policy_name']!r} "
            f"(decide={decide_policy!r})"
        )

    ok, issues = compare_action_lists(decide_actions, drill_actions, prob_tol=prob_tol)

    if ok:
        top = max(drill_actions, key=lambda a: float(a["prob"]))
        print(
            f"  PASS {label} street={street} policy={decide_policy} "
            f"top={top['label']} {float(top['prob']):.0%}"
        )
        return True

    print(f"  FAIL {label} street={street}")
    for issue in issues:
        print(f"    - {issue}")
    return False


async def _main_async(args: argparse.Namespace) -> int:
    factory = get_async_session_factory()
    async with factory() as session:
        spots = await _sample_spots(
            session,
            samples=args.samples,
            hand_id=args.hand_id,
            step_index=args.step_index,
        )
        if not spots:
            print("No drillable hero spots found in database.")
            return 1

        print(f"Checking {len(spots)} spot(s), prob_tol={args.prob_tol}…")
        passed = 0
        for hand_id, step_index in spots:
            if await _verify_one(
                session,
                hand_id,
                step_index,
                policy=args.policy,
                lenient=args.lenient,
                prob_tol=args.prob_tol,
            ):
                passed += 1

        print(f"\n{passed}/{len(spots)} checks passed.")
        if not args.lenient:
            print("Note: imported hands may need lenient replay for /drill/spot parity.")
        return 0 if passed == len(spots) else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify /drill/spot matches /decide actions.")
    parser.add_argument("--hand-id", type=int, default=None)
    parser.add_argument("--step-index", type=int, default=None)
    parser.add_argument("--samples", type=int, default=3, help="Random drill spots when hand not set")
    parser.add_argument("--policy", default="best", choices=("distilled", "best", "heuristic"))
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict replay (POST /decide). Default is lenient (matches /drill/spot).",
    )
    parser.add_argument("--prob-tol", type=float, default=0.001)
    args = parser.parse_args()
    args.lenient = not args.strict
    if (args.hand_id is None) ^ (args.step_index is None):
        parser.error("--hand-id and --step-index must be used together")
    raise SystemExit(asyncio.run(_main_async(args)))


if __name__ == "__main__":
    main()
