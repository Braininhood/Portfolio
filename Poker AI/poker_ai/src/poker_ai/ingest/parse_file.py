"""Parse a single hand-history file (shared by ingest service and parallel workers)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from poker_ai.ingest.canonical_id import INGEST_NORMALIZED_TXT, INGEST_PHH, resolve_hand_id
from poker_ai.ingest.identity import player_uid_hmac
from poker_ai.ingest.ohh_json import parse_ohh_json_bytes
from poker_ai.ingest.phh_text import parse_phh_bytes
from poker_ai.ingest.pokerstars_text import hand_id_from_path
from poker_ai.ingest.records import ParsedHand, ParsedPlayer
from poker_ai.ingest.registry import parse_hand_text_path


def _apply_tree_path_identity(
    parsed: ParsedHand,
    *,
    file_path: Path,
    corpus_root: Path,
    uid_secret: str,
) -> ParsedHand:
    """One DB row per file when the same ``hand_<id>.txt`` appears in different folders."""
    rel_s = file_path.resolve().relative_to(corpus_root.resolve()).as_posix()
    new_hid = resolve_hand_id(INGEST_NORMALIZED_TXT, rel_s)
    new_players = tuple(
        ParsedPlayer(
            player_id=p.player_id,
            position=p.position,
            stack_size=p.stack_size,
            bb_size=p.bb_size,
            is_hero=p.is_hero,
            player_uid=player_uid_hmac(
                uid_secret,
                nickname=p.screen_name,
                hand_id=new_hid,
                seat_player_id=p.player_id,
            ),
            screen_name=p.screen_name,
        )
        for p in parsed.players
    )
    return replace(parsed, hand_id=new_hid, external_ref=rel_s, players=new_players)


def _apply_phh_tree_identity(
    parsed: ParsedHand,
    *,
    file_path: Path,
    corpus_root: Path,
    uid_secret: str,
) -> ParsedHand:
    """Stable ``hand_id`` / ``external_ref`` per relative path for PHH trees."""
    rel_s = file_path.resolve().relative_to(corpus_root.resolve()).as_posix()
    ext = parsed.external_ref
    tail = ext.rsplit("#", 1)[-1] if "#" in ext else ext
    new_ref = f"{rel_s}#{tail}"
    new_hid = resolve_hand_id(INGEST_PHH, new_ref)
    new_players = tuple(
        ParsedPlayer(
            player_id=p.player_id,
            position=p.position,
            stack_size=p.stack_size,
            bb_size=p.bb_size,
            is_hero=p.is_hero,
            player_uid=player_uid_hmac(
                uid_secret,
                nickname=p.screen_name,
                hand_id=new_hid,
                seat_player_id=p.player_id,
            ),
            screen_name=p.screen_name,
        )
        for p in parsed.players
    )
    return replace(parsed, hand_id=new_hid, external_ref=new_ref, players=new_players)


def parse_file_hands(
    path: Path,
    *,
    uid_secret: str,
    tree_root: Path | None = None,
) -> list[ParsedHand]:
    """Parse one file into zero or more :class:`ParsedHand` records."""
    hid = hand_id_from_path(path)
    if hid is None:
        hid = abs(hash(path.resolve().as_posix())) % (10**9)

    suffix = path.suffix.lower()
    raw = path.read_bytes()

    if suffix == ".json":
        parsed = parse_ohh_json_bytes(raw, uid_secret=uid_secret)
        if parsed is None:
            return []
        return [parsed]

    if suffix in (".phh", ".phhs"):
        hands = parse_phh_bytes(raw, path=path, uid_secret=uid_secret)
        if not hands:
            return []
        if tree_root is None:
            return hands
        return [
            _apply_phh_tree_identity(
                h, file_path=path, corpus_root=tree_root, uid_secret=uid_secret
            )
            for h in hands
        ]

    parsed = parse_hand_text_path(path, raw, hand_id=hid, uid_secret=uid_secret)
    if parsed is None:
        return []
    if (
        tree_root is not None
        and parsed.ingest_source == INGEST_NORMALIZED_TXT
        and suffix != ".json"
    ):
        parsed = _apply_tree_path_identity(
            parsed, file_path=path, corpus_root=tree_root, uid_secret=uid_secret
        )
    return [parsed]


def parse_file(
    path: Path,
    *,
    uid_secret: str,
    tree_root: Path | None = None,
) -> ParsedHand | None:
    """Return the first parsed hand; prefer :func:`parse_file_hands` for PHH bundles."""
    hands = parse_file_hands(path, uid_secret=uid_secret, tree_root=tree_root)
    return hands[0] if hands else None
