"""Format detection and parser dispatch — add new sources by extending ``TEXT_HAND_PARSERS``."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from poker_ai.ingest.records import ParsedHand


class TextHandParser(Protocol):
    """Try to parse ``text`` / ``raw``; return ``None`` if this parser does not apply."""

    def __call__(
        self, path: Path, raw: bytes, text: str, hand_id: int, uid_secret: str
    ) -> ParsedHand | None: ...


def _try_gg(
    path: Path,
    raw: bytes,
    text: str,
    hand_id: int,
    uid_secret: str,
) -> ParsedHand | None:
    from poker_ai.ingest.gg_text import looks_like_gg_text, parse_gg_text

    if not looks_like_gg_text(text):
        return None
    return parse_gg_text(text, _hand_id=hand_id, _uid_secret=uid_secret)


def _try_normalized(
    path: Path,
    raw: bytes,
    text: str,
    hand_id: int,
    uid_secret: str,
) -> ParsedHand | None:
    from poker_ai.ingest.pokerstars_text import looks_like_normalized_converter_text, parse_text

    first = text.splitlines()[0] if text else ""
    if not looks_like_normalized_converter_text(first):
        return None
    return parse_text(text, hand_id=hand_id, uid_secret=uid_secret)


def _try_generic_text(
    path: Path,
    raw: bytes,
    text: str,
    hand_id: int,
    uid_secret: str,
) -> ParsedHand | None:
    from poker_ai.ingest.pokerstars_text import parse_text

    if not text.strip():
        return None
    return parse_text(text, hand_id=hand_id, uid_secret=uid_secret)


# First successful parser wins (order is part of the public contract).
TEXT_HAND_PARSERS: tuple[TextHandParser, ...] = (
    _try_gg,
    _try_normalized,
    _try_generic_text,
)


def parse_hand_text_path(
    path: Path, raw: bytes, *, hand_id: int, uid_secret: str
) -> ParsedHand | None:
    """Parse a non-JSON hand file using registered text parsers."""
    text = raw.decode("utf-8", errors="replace")
    for parser in TEXT_HAND_PARSERS:
        got = parser(path, raw, text, hand_id, uid_secret)
        if got is not None:
            return got
    return None
