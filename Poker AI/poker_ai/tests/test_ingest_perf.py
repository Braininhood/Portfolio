"""Phase 1 exit gate — full text-corpus ingest under 90 s (``hand_*.txt`` only)."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from poker_ai.config.settings import get_settings
from poker_ai.ingest.service import _collect_hand_files, ingest_path
from poker_ai.store.db import create_engine_and_session_factory


def _corpus_root() -> Path:
    env = os.environ.get("POKER_AI_CORPUS_ROOT", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    # Prefer txt-only subtree when present (repo layout: Poker AI/hand/6).
    base = Path(__file__).resolve().parents[2] / "hand"
    sub = base / "6"
    if sub.is_dir() and len(list(sub.glob("**/hand_*.txt"))) >= 17000:
        return sub
    return base


def test_full_corpus_ingest_under_budget(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """~19k-hand Phase 1 gate: ``POKER_AI_PERF_INGEST=1``, budget default 90 s."""
    if os.environ.get("POKER_AI_PERF_INGEST", "").strip() != "1":
        pytest.skip("Set POKER_AI_PERF_INGEST=1 to run the Phase 1 ingest timing gate.")

    root = _corpus_root()
    if not root.is_dir():
        pytest.skip(f"Corpus missing: {root}")

    hands = sorted(root.glob("**/hand_*.txt"))
    min_hands = int(os.environ.get("POKER_AI_PERF_MIN_HANDS", "17000"))
    if len(hands) < min_hands:
        pytest.skip(
            f"Only {len(hands)} hand_*.txt files (need >= {min_hands}); "
            "adjust POKER_AI_PERF_MIN_HANDS."
        )

    all_ingestable = _collect_hand_files(root)
    if len(all_ingestable) != len(hands):
        pytest.skip(
            f"{root} has {len(all_ingestable)} ingestable files but {len(hands)} hand_*.txt — "
            "use POKER_AI_CORPUS_ROOT pointing at a subtree with only normalized "
            "`hand_*.txt` (exclude bulk PHH trees like `poker-hand-histories/`)."
        )

    db = tmp_path / "perf.sqlite"
    monkeypatch.setenv("POKER_AI_DATABASE_URL", f"sqlite+aiosqlite:///{db.as_posix()}")
    monkeypatch.setenv("POKER_AI_PLAYER_UID_HMAC_SECRET", "perf-test-secret-not-for-production")
    monkeypatch.setenv("POKER_AI_SQLITE_SYNC_OFF", "1")
    monkeypatch.setenv("POKER_AI_INGEST_APPEND_ONLY", "1")
    get_settings.cache_clear()

    import asyncio

    from alembic import command

    from poker_ai.store.migrate import alembic_config

    cfg = alembic_config()
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db.as_posix()}")
    command.upgrade(cfg, "head")

    engine, factory = create_engine_and_session_factory()
    try:
        t0 = time.perf_counter()
        stats = asyncio.run(
            ingest_path(
                root,
                session_factory=factory,
                uid_secret="perf-test-secret-not-for-production",
            )
        )
        elapsed = time.perf_counter() - t0
    finally:
        asyncio.run(engine.dispose())
        get_settings.cache_clear()

    assert stats.files_processed == len(all_ingestable) == len(hands)
    min_yield = float(os.environ.get("POKER_AI_PERF_MIN_YIELD", "0.5"))
    yield_ratio = stats.hands_new / len(hands) if hands else 0.0
    assert yield_ratio >= min_yield, (
        f"Too many parse/store skips: {stats.hands_new} new / {len(hands)} files "
        f"(yield {yield_ratio:.2f} < {min_yield})."
    )
    budget = float(os.environ.get("POKER_AI_PERF_BUDGET_SEC", "90"))
    assert elapsed < budget, (
        f"Ingest too slow: {elapsed:.1f}s for {stats.hands_new} hands (budget {budget}s). "
        f"Use SSD, POKER_AI_INGEST_BATCH_SIZE=500, parallel parse workers."
    )
