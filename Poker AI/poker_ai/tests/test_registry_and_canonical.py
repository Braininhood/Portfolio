"""Coverage for ingest registry and stable non-normalized hand ids."""

from __future__ import annotations

from pathlib import Path

import pytest

from poker_ai.ingest.canonical_id import INGEST_POKERSTARS_RAW_MINIMAL, stable_hand_int
from poker_ai.ingest.registry import parse_hand_text_path


def test_stable_hand_int_zero_digest_uses_one(monkeypatch: pytest.MonkeyPatch) -> None:
    class _ZeroDigest:
        def digest(self) -> bytes:
            return b"\x00" * 8

    monkeypatch.setattr(
        "poker_ai.ingest.canonical_id.hashlib.blake2b",
        lambda *_a, **_k: _ZeroDigest(),
    )
    assert stable_hand_int("any", "ref") == 1


def test_stable_hand_int_deterministic() -> None:
    a = stable_hand_int("src", "ref-a")
    b = stable_hand_int("src", "ref-a")
    c = stable_hand_int("src", "ref-b")
    assert a == b
    assert a != c
    assert a > 0
    assert a <= (1 << 53) - 1  # JSON / JS Number.MAX_SAFE_INTEGER


def test_parse_hand_text_path_minimal(tmp_path: Path) -> None:
    p = tmp_path / "x.txt"
    p.write_text(
        "PokerStars Hand #42424242 - Hold'em No Limit ($0.01/$0.02 USD) - 2020/01/01\n",
        encoding="utf-8",
    )
    h = parse_hand_text_path(p, p.read_bytes(), hand_id=1, uid_secret="k")
    assert h is not None
    assert h.ingest_source == INGEST_POKERSTARS_RAW_MINIMAL
    assert "42424242" in h.external_ref
    assert h.hand_id == stable_hand_int(INGEST_POKERSTARS_RAW_MINIMAL, h.external_ref)
