"""CLI, store helpers, and parser edge cases (coverage for Phase 1)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest import mock

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typer.testing import CliRunner

from poker_ai.apps.cli.main import app
from poker_ai.config.settings import get_settings
from poker_ai.ingest.ohh_json import parse_ohh_dict, parse_ohh_json_bytes
from poker_ai.ingest.pokerstars_text import hand_id_from_path, parse_text
from poker_ai.ingest.service import ingest_path, run_ingest_sync
from poker_ai.store import db as db_mod
from poker_ai.store.db import (
    create_engine_and_session_factory,
    dispose_async_store,
    get_async_session_factory,
    session_scope,
)
from poker_ai.store.duckdb_analytics import attach_sqlite_readonly, explain_analytics_layer
from poker_ai.store.migrate import _sync_sqlalchemy_url, current_revision, upgrade_head

runner = CliRunner()


def test_sync_sqlalchemy_url_variants() -> None:
    assert "+asyncpg" not in _sync_sqlalchemy_url("sqlite+aiosqlite:///./a.db")
    assert _sync_sqlalchemy_url("postgresql+asyncpg://u:p@h/db").startswith("postgresql://")


def test_explain_analytics_layer() -> None:
    assert "DuckDB" in explain_analytics_layer()


def test_duckdb_attach_sqlite(
    tmp_path: Path,
    migrated_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    db = tmp_path / "db.sqlite"
    assert db.is_file()
    try:
        con = attach_sqlite_readonly(db)
    except Exception as exc:  # pragma: no cover — platform / extension variance
        pytest.skip(f"duckdb sqlite attach: {exc}")
    row = con.execute("SELECT COUNT(*) FROM poker.games").fetchone()
    assert row is not None
    con.close()


def test_session_scope_uses_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    asyncio.run(dispose_async_store())
    get_settings.cache_clear()
    eng, fac = create_engine_and_session_factory("sqlite+aiosqlite:///:memory:")
    monkeypatch.setattr(db_mod, "_engine", eng, raising=False)
    monkeypatch.setattr(db_mod, "_session_factory", fac, raising=False)

    async def _inner() -> None:
        async with session_scope() as session:
            assert session.bind is eng

    asyncio.run(_inner())
    asyncio.run(eng.dispose())
    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_session_factory", None, raising=False)
    get_settings.cache_clear()


def test_current_revision_operational_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POKER_AI_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    get_settings.cache_clear()

    with mock.patch(
        "poker_ai.store.migrate.create_engine",
        side_effect=OperationalError("stmt", {}, orig=Exception("x")),
    ):
        assert current_revision() is None

    get_settings.cache_clear()


def test_cli_db_migrate_status_ingest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "cli.db"
    monkeypatch.setenv("POKER_AI_DATABASE_URL", f"sqlite+aiosqlite:///{db.as_posix()}")
    monkeypatch.setenv("POKER_AI_PLAYER_UID_HMAC_SECRET", "cli-test-secret")
    get_settings.cache_clear()

    r = runner.invoke(app, ["db", "migrate"])
    assert r.exit_code == 0

    r2 = runner.invoke(app, ["db", "status"])
    assert r2.exit_code == 0
    assert "0006_jobs_table" in r2.stdout or "0005_games_ingested_at" in r2.stdout

    fx = Path(__file__).resolve().parent / "fixtures" / "hands" / "hand_900006.txt"
    r3 = runner.invoke(app, ["ingest", str(fx)])
    assert r3.exit_code == 0
    assert "new=1" in r3.stdout

    asyncio.run(dispose_async_store())
    get_settings.cache_clear()


def test_cli_ingest_applies_migrations_without_prior_db_migrate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ingest must create schema on a fresh DB (no separate ``db migrate``)."""
    db = tmp_path / "ingest_only.db"
    monkeypatch.setenv("POKER_AI_DATABASE_URL", f"sqlite+aiosqlite:///{db.as_posix()}")
    monkeypatch.setenv("POKER_AI_PLAYER_UID_HMAC_SECRET", "cli-test-secret")
    get_settings.cache_clear()

    fx = Path(__file__).resolve().parent / "fixtures" / "hands" / "hand_900006.txt"
    r = runner.invoke(app, ["ingest", str(fx)])
    assert r.exit_code == 0, r.stdout + r.stderr
    assert "new=1" in r.stdout
    assert current_revision() is not None

    asyncio.run(dispose_async_store())
    get_settings.cache_clear()


def test_get_async_session_factory_singleton() -> None:
    asyncio.run(dispose_async_store())
    get_settings.cache_clear()
    a = get_async_session_factory()
    b = get_async_session_factory()
    assert a is b
    asyncio.run(dispose_async_store())
    get_settings.cache_clear()


def test_upgrade_head_smoke(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "u.db"
    monkeypatch.setenv("POKER_AI_DATABASE_URL", f"sqlite+aiosqlite:///{db.as_posix()}")
    get_settings.cache_clear()
    upgrade_head()
    assert db.is_file()
    asyncio.run(dispose_async_store())
    get_settings.cache_clear()


def test_parse_ohh_edge_cases() -> None:
    assert parse_ohh_json_bytes(b"\xff\xff", uid_secret="k") is None
    assert parse_ohh_dict({"x": 1}, uid_secret="k") is None
    assert parse_ohh_dict({"ohh": {"players": []}}, uid_secret="k") is None


def test_parse_text_raw_pokerstars_stub() -> None:
    text = """PokerStars Hand #1:  Hold'em No Limit ($0.01/$0.02 USD) - 2021/01/01
Table 'Test' 6-max Seat #1 is the button
"""
    h = parse_text(text, hand_id=42, uid_secret="s")
    assert h is not None
    assert h.stakes == "0.01/0.02"


def test_hand_id_from_path_none() -> None:
    assert hand_id_from_path(Path("foo.txt")) is None


def test_run_ingest_sync_empty_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "e.db"
    monkeypatch.setenv("POKER_AI_DATABASE_URL", f"sqlite+aiosqlite:///{db.as_posix()}")
    get_settings.cache_clear()
    from alembic import command as alembic_command

    from poker_ai.store.migrate import alembic_config

    cfg = alembic_config()
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db.as_posix()}")
    alembic_command.upgrade(cfg, "head")

    empty = tmp_path / "empty"
    empty.mkdir()
    eng, fac = create_engine_and_session_factory()
    stats = run_ingest_sync(empty, session_factory=fac, uid_secret="k")
    assert stats.files_processed == 0
    assert stats.hands_new == 0
    asyncio.run(eng.dispose())
    asyncio.run(dispose_async_store())
    get_settings.cache_clear()


def test_sync_sqlalchemy_url_unknown_passthrough() -> None:
    assert _sync_sqlalchemy_url("mysql+pymysql://h/db") == "mysql+pymysql://h/db"


def test_default_sqlite_database_url_targets_package_data() -> None:
    from sqlalchemy.engine.url import make_url

    from poker_ai.config.settings import default_sqlite_database_url

    url = default_sqlite_database_url()
    parsed = make_url(url)
    assert parsed.database is not None
    p = Path(parsed.database)
    assert p.name == "poker_ai.db"
    assert p.parent.name == "data"
    assert (p.parent.parent / "pyproject.toml").is_file()


def test_ensure_sqlite_dir_branches(tmp_path: Path) -> None:
    from poker_ai.apps.cli.main import _ensure_sqlite_dir

    _ensure_sqlite_dir("postgresql+asyncpg://localhost/db")
    _ensure_sqlite_dir("sqlite+aiosqlite:///:memory:")
    target = tmp_path / "nested" / "f.db"
    _ensure_sqlite_dir(f"sqlite+aiosqlite:///{target.as_posix()}")
    assert target.parent.is_dir()


def test_sqlite_db_path_and_echo_sqlite_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from poker_ai.apps.cli.main import _echo_sqlite_file, _sqlite_db_path

    assert _sqlite_db_path("postgresql+asyncpg://localhost/db") is None
    assert _sqlite_db_path("sqlite+aiosqlite:///:memory:") is None

    _echo_sqlite_file("postgresql+asyncpg://localhost/db")
    _echo_sqlite_file("sqlite+aiosqlite:///:memory:")
    assert capsys.readouterr().out == ""

    db = tmp_path / "echo.db"
    url = f"sqlite+aiosqlite:///{db.as_posix()}"
    assert _sqlite_db_path(url) == db.resolve()
    _echo_sqlite_file(url)
    out = capsys.readouterr().out
    assert "SQLite file:" in out
    assert str(db.resolve()) in out


def test_current_revision_connect_operational_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POKER_AI_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    get_settings.cache_clear()
    mock_eng = mock.MagicMock()
    mock_eng.connect.side_effect = OperationalError("stmt", {}, orig=Exception("x"))
    with mock.patch("poker_ai.store.migrate.create_engine", return_value=mock_eng):
        assert current_revision() is None
    get_settings.cache_clear()


def test_parse_text_empty_and_non_normalized() -> None:
    assert parse_text("", hand_id=1, uid_secret="k") is None
    assert parse_text("not a hand\n", hand_id=1, uid_secret="k") is None


def test_service_parse_file_variants(tmp_path: Path) -> None:
    from poker_ai.ingest.records import ParsedHand
    from poker_ai.ingest.parse_file import parse_file

    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{", encoding="utf-8")
    assert parse_file(bad_json, uid_secret="k") is None

    empty_txt = tmp_path / "blank.txt"
    empty_txt.write_text("   \n", encoding="utf-8")
    assert parse_file(empty_txt, uid_secret="k") is None

    gg_txt = tmp_path / "gg.txt"
    gg_txt.write_text("GGPoker Hand #1\n$0.01/$0.02, NLH, 6 Players\n", encoding="utf-8")
    assert parse_file(gg_txt, uid_secret="k") is None

    ph = ParsedHand(
        hand_id=1,
        stakes="0/0",
        game_type="NLH",
        num_players=0,
        small_blind=0.0,
        big_blind=0.0,
        hero_position=None,
        hero_cards=None,
        board_cards=None,
        pot_preflop=0.0,
        pot_flop=0.0,
        pot_turn=0.0,
        pot_river=0.0,
        ingest_source="gg_network",
        external_ref="mock-1",
    )
    with mock.patch("poker_ai.ingest.gg_text.parse_gg_text", return_value=ph):
        assert parse_file(gg_txt, uid_secret="k") is ph


def test_ingest_path_max_hands(
    tmp_path: Path,
    migrated_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    fx = Path(__file__).resolve().parent / "fixtures" / "hands" / "sample_two_hands.phhs"
    (tmp_path / "sample_two_hands.phhs").write_bytes(fx.read_bytes())

    async def _run() -> None:
        stats = await ingest_path(
            tmp_path,
            session_factory=migrated_session_factory,
            uid_secret="k",
            max_hands=1,
        )
        assert stats.hands_new == 1
        assert stats.files_processed == 1

    asyncio.run(_run())


def test_ingest_path_max_hands_zero_unlimited(
    tmp_path: Path,
    migrated_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    fx = Path(__file__).resolve().parent / "fixtures" / "hands" / "sample_two_hands.phhs"
    (tmp_path / "sample_two_hands.phhs").write_bytes(fx.read_bytes())

    async def _run() -> None:
        stats = await ingest_path(
            tmp_path,
            session_factory=migrated_session_factory,
            uid_secret="k",
            max_hands=0,
        )
        assert stats.hands_new == 2
        assert stats.files_processed == 1

    asyncio.run(_run())


def test_cli_ingest_max_hands_flag(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = tmp_path / "cap.db"
    monkeypatch.setenv("POKER_AI_DATABASE_URL", f"sqlite+aiosqlite:///{db.as_posix()}")
    monkeypatch.setenv("POKER_AI_PLAYER_UID_HMAC_SECRET", "cli-cap-secret")
    get_settings.cache_clear()
    fx = Path(__file__).resolve().parent / "fixtures" / "hands" / "sample_two_hands.phhs"
    d = tmp_path / "corpus"
    d.mkdir()
    (d / "sample_two_hands.phhs").write_bytes(fx.read_bytes())
    r = runner.invoke(app, ["ingest", str(d), "--max-hands", "1"])
    assert r.exit_code == 0, r.stdout + r.stderr
    assert "new=1" in r.stdout
    assert "files_seen=1" in r.stdout
    asyncio.run(dispose_async_store())
    get_settings.cache_clear()


def test_cli_ingest_max_hands_from_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = tmp_path / "cap_env.db"
    monkeypatch.setenv("POKER_AI_DATABASE_URL", f"sqlite+aiosqlite:///{db.as_posix()}")
    monkeypatch.setenv("POKER_AI_PLAYER_UID_HMAC_SECRET", "cli-cap-env-secret")
    monkeypatch.setenv("POKER_AI_INGEST_MAX_HANDS", "1")
    get_settings.cache_clear()
    fx = Path(__file__).resolve().parent / "fixtures" / "hands" / "sample_two_hands.phhs"
    d = tmp_path / "corpus_env"
    d.mkdir()
    (d / "sample_two_hands.phhs").write_bytes(fx.read_bytes())
    r = runner.invoke(app, ["ingest", str(d)])
    assert r.exit_code == 0, r.stdout + r.stderr
    assert "new=1" in r.stdout
    asyncio.run(dispose_async_store())
    get_settings.cache_clear()


def test_cli_ingest_max_hands_non_positive_env_ignored(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = tmp_path / "cap0.db"
    monkeypatch.setenv("POKER_AI_DATABASE_URL", f"sqlite+aiosqlite:///{db.as_posix()}")
    monkeypatch.setenv("POKER_AI_PLAYER_UID_HMAC_SECRET", "cli-cap0-secret")
    monkeypatch.setenv("POKER_AI_INGEST_MAX_HANDS", "0")
    get_settings.cache_clear()
    fx = Path(__file__).resolve().parent / "fixtures" / "hands" / "sample_two_hands.phhs"
    d = tmp_path / "corpus_zero_cap"
    d.mkdir()
    (d / "sample_two_hands.phhs").write_bytes(fx.read_bytes())
    r = runner.invoke(app, ["ingest", str(d)])
    assert r.exit_code == 0, r.stdout + r.stderr
    assert "new=2" in r.stdout
    asyncio.run(dispose_async_store())
    get_settings.cache_clear()


def test_run_ingest_sync_respects_max_hands(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = tmp_path / "sync_cap.db"
    monkeypatch.setenv("POKER_AI_DATABASE_URL", f"sqlite+aiosqlite:///{db.as_posix()}")
    get_settings.cache_clear()
    from alembic import command as alembic_command

    from poker_ai.store.migrate import alembic_config

    cfg = alembic_config()
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db.as_posix()}")
    alembic_command.upgrade(cfg, "head")
    fx = Path(__file__).resolve().parent / "fixtures" / "hands" / "sample_two_hands.phhs"
    (tmp_path / "sample_two_hands.phhs").write_bytes(fx.read_bytes())
    eng, fac = create_engine_and_session_factory()
    stats = run_ingest_sync(tmp_path, session_factory=fac, uid_secret="k", max_hands=1)
    assert stats.files_processed == 1
    assert stats.hands_new == 1
    asyncio.run(eng.dispose())
    asyncio.run(dispose_async_store())
    get_settings.cache_clear()


def test_ingest_path_skips_unparsed_files(
    tmp_path: Path,
    migrated_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    d = tmp_path / "mix"
    d.mkdir()
    (d / "bad.json").write_text("{", encoding="utf-8")
    (d / "empty.txt").write_text(" \n", encoding="utf-8")

    async def _run() -> None:
        stats = await ingest_path(
            d,
            session_factory=migrated_session_factory,
            uid_secret="k",
        )
        assert stats.files_processed == 2
        assert stats.hands_new == 0

    asyncio.run(_run())


def test_ingest_path_nonexistent_returns_zero(
    migrated_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def _run() -> None:
        stats = await ingest_path(
            Path("nonexistent_path_xyz_99999"),
            session_factory=migrated_session_factory,
            uid_secret="k",
        )
        assert stats.files_processed == 0
        assert stats.hands_new == 0

    asyncio.run(_run())
