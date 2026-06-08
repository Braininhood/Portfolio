"""Application settings — env vars use the ``POKER_AI_`` prefix."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_sqlite_database_url() -> str:
    """SQLite file always under the ``poker_ai`` package root: ``data/poker_ai.db``."""
    # settings.py → config → poker_ai (src package) → src → project root (pyproject.toml)
    project_root = Path(__file__).resolve().parents[3]
    db_path = (project_root / "data" / "poker_ai.db").resolve()
    return f"sqlite+aiosqlite:///{db_path.as_posix()}"


class Settings(BaseSettings):
    """Runtime configuration loaded from environment and optional ``.env``."""

    model_config = SettingsConfigDict(
        env_prefix="POKER_AI_",
        env_file=(".env",),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    debug: bool = Field(default=False, description="Enable verbose diagnostics.")
    log_level: str = Field(default="INFO", description="Logging level name.")
    database_url: str = Field(
        default_factory=default_sqlite_database_url,
        description=(
            "Async SQLAlchemy URL. Default is the repo ``poker_ai/data/poker_ai.db`` "
            "(not cwd-relative). Override with ``POKER_AI_DATABASE_URL``."
        ),
    )
    player_uid_hmac_secret: str = Field(
        default="dev-only-CHANGE-ME-use-POKER_AI_PLAYER_UID_HMAC_SECRET",
        description="Secret for HMAC-SHA256 player_uid (see doc/SECURITY_AND_COMPLIANCE.md).",
    )
    strict_nlh_card_integrity: bool = Field(
        default=True,
        description=(
            "When true, normalized NLH hands must pass 52-card dedup + hero two hole cards. "
            "Set false for mixed/legacy imports (see README)."
        ),
    )
    ingest_max_hands: int | None = Field(
        default=None,
        description=(
            "Directory ingest stops after this many hands are written (upserted). "
            "Unset = process every matching file. CLI ``--max-hands`` overrides for one run."
        ),
    )
    ingest_require_complete_hands: bool = Field(
        default=True,
        description=(
            "When true, skip hands missing BB, full seat grid, actions, or PHH per-seat "
            "results / OHH settlement rows. Set ``POKER_AI_INGEST_REQUIRE_COMPLETE_HANDS=false`` "
            "to load legacy or partial parser output."
        ),
    )
    ingest_train_hhformer: bool = Field(
        default=False,
        description=(
            "After ingest, run HHFormer pretrain. Prefer CLI ``ingest --train-hhformer`` "
            "or ``POKER_AI_INGEST_TRAIN_HHFORMER=1``."
        ),
    )
    num_workers: int = Field(
        default=0,
        description=(
            "CPU worker processes for ingest, features, and CFR (0 = auto from CPU count). "
            "Override with ``POKER_AI_NUM_WORKERS``."
        ),
    )
    texas_solver_exe: str | None = Field(
        default=None,
        description=(
            "Path to TexasSolver ``console_solver`` binary (AGPL teacher). "
            "Env: ``POKER_AI_TEXAS_SOLVER_EXE``. "
            "Auto-discovered after ``solve install-texas``."
        ),
    )
    texas_solver_install_dir: Path = Field(
        default=Path("artifacts/third_party/texassolver"),
        description=(
            "Directory for downloaded TexasSolver release (see ``solve install-texas``). "
            "Env: ``POKER_AI_TEXAS_SOLVER_INSTALL_DIR``."
        ),
    )
    solver_cache_dir: Path = Field(
        default=Path("artifacts/solver_cache"),
        description="Disk cache for Phase 7 solved spots.",
    )
    student_artifact_dir: Path = Field(
        default=Path("artifacts/student/v1"),
        description="Distilled student weights + MODEL_CARD.",
    )
    multiway_student_dir: Path = Field(
        default=Path("artifacts/student/multiway_v1"),
        description="Multi-way postflop student (DB + Monker labels).",
    )
    monker_export_dir: Path = Field(
        default=Path("artifacts/solver/monker_exports"),
        description="Directory of Monker JSON strategy exports (Phase 7c).",
    )
    monker_teacher_blend: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Runtime blend weight for Monker frequencies into multi-way student.",
    )
    style_encoder_artifact_dir: Path = Field(
        default=Path("artifacts/style_encoder/v1"),
        description="Contrastive style encoder weights (Phase 8).",
    )
    play_auto_learn: bool = Field(
        default=True,
        description="After Play vs AI hands, debounce-train from play_hands and promote router weights.",
    )
    play_auto_learn_debounce_sec: float = Field(
        default=45.0,
        ge=5.0,
        description="Wait after last hand before queuing play auto-learn (seconds).",
    )
    play_auto_learn_min_decisions: int = Field(
        default=3,
        ge=1,
        description="Minimum new hero decisions since last auto-learn before retraining.",
    )
    play_auto_learn_hu_epochs: int = Field(default=20, ge=1, le=200)
    play_auto_learn_mw_epochs: int = Field(default=15, ge=1, le=200)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return process-wide settings (cached)."""
    return Settings()
