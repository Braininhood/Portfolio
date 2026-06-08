"""Typer CLI — entrypoint for ``python -m poker_ai`` and the ``poker-ai`` script."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

import typer
from sqlalchemy.engine.url import make_url

from poker_ai import __version__
from poker_ai.config.settings import get_settings
from poker_ai.features.build import write_feature_jsonl
from poker_ai.ingest.service import run_ingest_sync
from poker_ai.runtime.workers import resolve_worker_count
from poker_ai.store.db import get_async_session_factory
from poker_ai.store.migrate import current_revision, upgrade_head

_CLI_HELP = """\
================================================================
  Poker AI - local-first No-Limit Hold'em platform
================================================================

Fully local analysis and training - no external AI APIs.
Canonical documentation lives under doc/ at the repository root
(start with doc/ROADMAP.md).
"""

app = typer.Typer(
    name="poker_ai",
    help=_CLI_HELP,
    no_args_is_help=True,
)

db_app = typer.Typer(no_args_is_help=True, help="Database migrations and status.")
features_app = typer.Typer(no_args_is_help=True, help="Feature extraction (Phase 3).")
train_app = typer.Typer(no_args_is_help=True, help="Model training (Phase 5+).")
solve_app = typer.Typer(no_args_is_help=True, help="CFR solvers (Phase 6).")
policy_app = typer.Typer(no_args_is_help=True, help="Runtime policies (Phase 6–7).")
pipeline_app = typer.Typer(no_args_is_help=True, help="End-to-end local pipeline (Phases 1–7).")
equity_app = typer.Typer(no_args_is_help=True, help="Range equity tools (Phase 4).")
league_app = typer.Typer(no_args_is_help=True, help="Self-play league (Phase 9).")
opponents_app = typer.Typer(no_args_is_help=True, help="Opponent style embeddings (Phase 8).")
eval_app = typer.Typer(no_args_is_help=True, help="AIVAT evaluation and audits (v2).")

from poker_ai.apps.serve import serve_cmd  # noqa: E402


def _workers_opt(workers: int) -> int:
    return resolve_worker_count(workers if workers != 0 else None)


@app.callback()
def _main() -> None:
    """Load settings so invalid env fails fast on any subcommand."""
    _ = get_settings()


@app.command()
def version() -> None:
    """Print package version."""
    typer.echo(__version__)


def _sqlite_db_path(url: str) -> Path | None:
    """Resolved path for file-backed SQLite, or ``None`` for non-SQLite / in-memory."""
    parsed = make_url(url)
    if parsed.get_dialect().name != "sqlite" or not parsed.database:
        return None
    if parsed.database == ":memory:":
        return None
    return Path(parsed.database).expanduser().resolve()


def _ensure_sqlite_dir(url: str) -> None:
    p = _sqlite_db_path(url)
    if p is None:
        return
    p.parent.mkdir(parents=True, exist_ok=True)


def _echo_sqlite_file(url: str) -> None:
    """Print resolved on-disk path for file-backed SQLite (skips in-memory)."""
    p = _sqlite_db_path(url)
    if p is None:
        return
    typer.echo(f"SQLite file: {p}")


@app.command("ingest")
def ingest_cmd(
    path: Annotated[
        Path,
        typer.Argument(help="File or directory.", exists=True, readable=True),
    ],
    max_hands: Annotated[
        int | None,
        typer.Option(
            "--max-hands",
            min=1,
            help="Stop after N hands (dev). Default: POKER_AI_INGEST_MAX_HANDS if set.",
        ),
    ] = None,
    train_hhformer: Annotated[
        bool,
        typer.Option(
            "--train-hhformer",
            help="After ingest, run HHFormer pretrain (or set POKER_AI_INGEST_TRAIN_HHFORMER=1).",
        ),
    ] = False,
    workers: Annotated[
        int,
        typer.Option(
            "--workers",
            min=0,
            help="Parse files in parallel (0 = auto from POKER_AI_NUM_WORKERS / CPU).",
        ),
    ] = 0,
) -> None:
    """Parse hand histories and upsert into the canonical store (idempotent)."""
    settings = get_settings()
    cap = max_hands if max_hands is not None else settings.ingest_max_hands
    if cap is not None and cap <= 0:
        cap = None
    _ensure_sqlite_dir(settings.database_url)
    _echo_sqlite_file(settings.database_url)
    upgrade_head()
    factory = get_async_session_factory()
    nw = _workers_opt(workers)
    stats = run_ingest_sync(
        path,
        session_factory=factory,
        uid_secret=settings.player_uid_hmac_secret,
        max_hands=cap,
        workers=nw,
    )
    typer.echo(
        f"Ingest complete: files={stats.files_processed} new={stats.hands_new} "
        f"updated={stats.hands_updated} skipped={stats.hands_skipped} workers={nw}"
    )
    if train_hhformer or settings.ingest_train_hhformer:
        from poker_ai.learn.pretrain_hhformer import PretrainConfig, run_pretrain

        typer.echo("Starting HHFormer pretrain after ingest...")
        metrics = run_pretrain(session_factory=factory, cfg=PretrainConfig())
        typer.echo(
            f"HHFormer train done: map={metrics.map_top1_acc:.3f} "
            f"sop_auc={metrics.sop_auc:.3f} wall_s={metrics.wall_time_sec:.0f}"
        )


@db_app.command("migrate")
def db_migrate() -> None:
    """Apply Alembic migrations to head."""
    settings = get_settings()
    _ensure_sqlite_dir(settings.database_url)
    _echo_sqlite_file(settings.database_url)
    upgrade_head()
    typer.echo("Migrations applied (head).")


@db_app.command("status")
def db_status() -> None:
    """Show current Alembic revision (if any)."""
    rev = current_revision()
    typer.echo(rev or "(no alembic_version row — run db migrate)")


app.add_typer(db_app, name="db")


@features_app.command("build")
def features_build(
    since: Annotated[
        str | None,
        typer.Option(
            "--since",
            help="UTC calendar date YYYY-MM-DD — only hands with ingested_at on/after 00:00 UTC.",
        ),
    ] = None,
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="JSONL output path (one JSON object per hand)."),
    ] = Path("features.jsonl"),
    workers: Annotated[
        int,
        typer.Option("--workers", min=0, help="Parallel encode workers (0 = auto)."),
    ] = 0,
    blueprint_full: Annotated[
        bool,
        typer.Option(
            "--blueprint-full",
            help="Write extended v2 columns (board texture, student extras, manifest).",
        ),
    ] = False,
) -> None:
    """Materialise Phase 3 tensors + range vectors for hands in the canonical store."""
    settings = get_settings()
    _ensure_sqlite_dir(settings.database_url)
    _echo_sqlite_file(settings.database_url)
    upgrade_head()
    factory = get_async_session_factory()
    since_dt: datetime | None = None
    if since is not None:
        since_dt = datetime.fromisoformat(since).replace(tzinfo=UTC)

    nw = _workers_opt(workers)

    async def _run() -> int:
        async with factory() as session:
            return await write_feature_jsonl(
                session,
                output,
                since=since_dt,
                workers=nw,
                blueprint_full=blueprint_full,
            )

    n = asyncio.run(_run())
    mode = "blueprint-full" if blueprint_full else "standard"
    typer.echo(f"Features written: hands={n} path={output.resolve()} workers={nw} mode={mode}")


@features_app.command("export-parquet")
def features_export_parquet_cmd(
    since: Annotated[
        str | None,
        typer.Option("--since", help="UTC date YYYY-MM-DD for snapshot folder name."),
    ] = None,
    source: Annotated[
        Path,
        typer.Option("--source", "-s", help="Input features.jsonl."),
    ] = Path("features.jsonl"),
) -> None:
    """Export features.jsonl to versioned Parquet + FEATURE_MANIFEST.json."""
    from poker_ai.features.export_parquet import export_features_parquet

    result = export_features_parquet(source, since=since)
    typer.echo(
        f"Parquet export: rows={result['num_rows']} version={result['version']} "
        f"path={result['parquet_path']}"
    )


@features_app.command("validate-blueprint")
def features_validate_blueprint_cmd(
    path: Annotated[
        Path,
        typer.Argument(help="features.jsonl to validate."),
    ] = Path("features.jsonl"),
    blueprint_full: Annotated[
        bool,
        typer.Option("--blueprint-full", help="Require extended v2 columns."),
    ] = False,
) -> None:
    """Round-trip schema gate for feature JSONL."""
    from poker_ai.features.export_parquet import validate_blueprint_file

    result = validate_blueprint_file(path, blueprint_full=blueprint_full)
    if not result["schema_ok"]:
        for err in result["errors"]:
            typer.echo(f"FAIL: {err}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"Schema OK: hands={result['hands_checked']} blueprint_full={blueprint_full}")


app.add_typer(features_app, name="features")


@features_app.command("hhformer-embed")
def features_hhformer_embed(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="JSONL: hand_id, embedding, optional hero_equity."),
    ] = Path("data/processed/hhformer_embeddings.jsonl"),
    weights: Annotated[
        Path,
        typer.Option("--weights", "-w", help="HHFormer artifact dir with weights.safetensors."),
    ] = Path("artifacts/hhformer/v1"),
    device: Annotated[str, typer.Option("--device", help="cpu | cuda | mps | auto")] = "auto",
    batch_size: Annotated[int, typer.Option("--batch-size", min=1)] = 256,
    max_hands: Annotated[int | None, typer.Option("--max-hands", min=1)] = None,
    with_equity: Annotated[
        bool,
        typer.Option(
            "--with-equity",
            help="Attach Phase 4 hero vs-random equity (exact river, MC otherwise).",
        ),
    ] = False,
) -> None:
    """Export frozen HHFormer [CLS] embeddings (+ optional equity) from the store."""
    from poker_ai.learn.hhformer_inference import EmbedConfig, export_embeddings_jsonl

    settings = get_settings()
    _ensure_sqlite_dir(settings.database_url)
    upgrade_head()
    factory = get_async_session_factory()
    cfg = EmbedConfig(
        weights_dir=weights,
        device=device,
        batch_size=batch_size,
        max_hands=max_hands,
        with_equity=with_equity,
    )
    n = export_embeddings_jsonl(factory, output, cfg=cfg)
    typer.echo(f"Embeddings written: hands={n} path={output.resolve()}")


@train_app.command("hhformer")
def train_hhformer(
    epochs: Annotated[int, typer.Option("--epochs", min=1)] = 50,
    batch_size: Annotated[int, typer.Option("--batch-size", min=1)] = 256,
    seed: Annotated[int, typer.Option("--seed")] = 42,
    device: Annotated[str, typer.Option("--device", help="cpu | cuda | mps | auto")] = "auto",
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Artifact directory (weights + metrics)."),
    ] = Path("artifacts/hhformer/v1"),
    max_hands: Annotated[
        int | None,
        typer.Option("--max-hands", min=1, help="Cap hands loaded from DB (dev)."),
    ] = None,
    num_workers: Annotated[
        int,
        typer.Option(
            "--num-workers",
            min=0,
            help=(
                "DataLoader workers for batch collation "
                "(0 = safest on Windows; 2-4 optional on Linux)."
            ),
        ),
    ] = 0,
    log_every: Annotated[
        int,
        typer.Option("--log-every", min=0, help="Log every N batches (0 = off)."),
    ] = 50,
    eval_every: Annotated[
        int,
        typer.Option(
            "--eval-every",
            min=0,
            help="Run validation every N epochs (0 = only at end).",
        ),
    ] = 0,
    no_amp: Annotated[
        bool,
        typer.Option("--no-amp", help="Disable CUDA automatic mixed precision."),
    ] = False,
) -> None:
    """Pretrain HHFormer (MAP + MCP + SOP) on hands in the canonical store."""
    from poker_ai.learn.pretrain_hhformer import PretrainConfig, run_pretrain

    settings = get_settings()
    _ensure_sqlite_dir(settings.database_url)
    _echo_sqlite_file(settings.database_url)
    upgrade_head()
    factory = get_async_session_factory()
    cfg = PretrainConfig(
        epochs=epochs,
        batch_size=batch_size,
        seed=seed,
        device=device,
        max_hands=max_hands,
        num_workers=num_workers,
        log_every=log_every,
        eval_every=eval_every,
        amp=not no_amp,
    )
    metrics = run_pretrain(artifact_dir=output, session_factory=factory, cfg=cfg)
    typer.echo(
        "HHFormer training complete: "
        f"map_acc={metrics.map_top1_acc:.3f} "
        f"sop_auc={metrics.sop_auc:.3f} "
        f"probe_auc={metrics.probe_auc:.3f} "
        f"artifacts={output.resolve()}"
    )


@train_app.command("style")
def train_style_cmd(
    epochs: Annotated[int, typer.Option("--epochs", min=1)] = 25,
    batch_size: Annotated[int, typer.Option("--batch-size", min=8)] = 256,
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Style encoder artifact directory."),
    ] = Path("artifacts/style_encoder/v1"),
    device: Annotated[str, typer.Option("--device", help="cpu | cuda | auto")] = "auto",
    seed: Annotated[int, typer.Option("--seed")] = 42,
    limit_hands: Annotated[
        int | None,
        typer.Option("--limit-hands", min=100, help="Cap hands from DB (dev)."),
    ] = None,
    val_frac: Annotated[float, typer.Option("--val-frac", min=0.05, max=0.4)] = 0.15,
) -> None:
    """Contrastive pretrain style encoder (SimCLR) on ingested hand histories."""
    from poker_ai.learn.style_contrastive import StyleTrainConfig, run_style_contrastive

    settings = get_settings()
    _ensure_sqlite_dir(settings.database_url)
    upgrade_head()
    factory = get_async_session_factory()
    metrics = run_style_contrastive(
        session_factory=factory,
        artifact_dir=output,
        cfg=StyleTrainConfig(
            epochs=epochs,
            batch_size=batch_size,
            seed=seed,
            device=device,
            limit_hands=limit_hands,
            val_frac=val_frac,
        ),
    )
    typer.echo(
        "Style training complete: "
        f"knn_top5={metrics.knn_top5_acc:.3f} knn_top1={metrics.knn_top1_acc:.3f} "
        f"train_windows={metrics.train_windows} val_windows={metrics.val_windows} "
        f"artifacts={output.resolve()}"
    )
    if metrics.knn_top5_acc < 0.6:
        typer.echo(
            "Warning: kNN top-5 < 0.6 (Phase 8 exit criterion). Ingest more hands or train longer.",
            err=True,
        )


app.add_typer(train_app, name="train")


def _preflop_cli_progress(event: dict[str, Any]) -> None:
    """Print solve progress to stderr (visible even when stdout is piped)."""
    pct = event.get("pct")
    msg = str(event.get("msg") or "").strip()
    if not msg:
        return
    head = f"{int(pct):>3}%" if pct is not None else "   "
    print(f"[preflop] {head} {msg}", file=sys.stderr, flush=True)


def _configure_preflop_cli_logging() -> None:
    if logging.getLogger().handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )
    for name in ("alembic", "alembic.runtime.migration"):
        logging.getLogger(name).setLevel(logging.WARNING)


@solve_app.command("preflop")
def solve_preflop_cmd(
    positions: Annotated[
        str,
        typer.Option("--positions", help="Table format: hu | 6max | 8max | 9max | 10max."),
    ] = "6max",
    iters: Annotated[
        int,
        typer.Option("--iters", min=1, help="Total CFR iterations (split across --workers)."),
    ] = 20_000,
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="JSON strategy artifact."),
    ] = Path("artifacts/solver/preflop_cfr.json"),
    chance_samples: Annotated[
        int,
        typer.Option("--chance-samples", min=8, help="Root deal samples for abstraction."),
    ] = 64,
    seed: Annotated[int, typer.Option("--seed")] = 42,
    log_every: Annotated[int, typer.Option("--log-every", min=0)] = 0,
    max_raises: Annotated[
        int,
        typer.Option("--max-raises", min=0, help="Cap raises per hand (keeps tree tractable)."),
    ] = 1,
    workers: Annotated[
        int,
        typer.Option(
            "--workers",
            min=0,
            help=(
                "Process pool shards (0 = auto). Skips slow state-tree exploitability "
                "unless --measure-exploitability."
            ),
        ),
    ] = 0,
    measure_exploitability: Annotated[
        bool,
        typer.Option(
            "--measure-exploitability",
            help="Run full-tree best response after solve (slow on 6-max).",
        ),
    ] = False,
    equity_mode: Annotated[
        str,
        typer.Option(
            "--equity-mode",
            help="Deal strength: random (abstract) | real (Phase-4 MC vs random range).",
        ),
    ] = "random",
    equity_mc_samples: Annotated[
        int,
        typer.Option(
            "--equity-mc-samples",
            min=100,
            help="MC samples per combo when --equity-mode real (table built once).",
        ),
    ] = 2000,
    production: Annotated[
        bool,
        typer.Option(
            "--production",
            help="Higher iters, real equity, prune low-mass info sets (HU/6-max charts).",
        ),
    ] = False,
    prune_min_mass: Annotated[
        float,
        typer.Option(
            "--prune-min-mass",
            min=0.0,
            help="Drop CFR info sets with cumulative strategy mass below this.",
        ),
    ] = 5.0,
) -> None:
    """Run CFR on the abstracted preflop tree (6-max or heads-up)."""
    from poker_ai.policy.cfr_policy import CFRPolicy
    from poker_ai.solver.preflop_equity import EquityMode
    from poker_ai.solver.preflop_artifacts import preflop_cfr_path
    from poker_ai.solver.solve_preflop import parse_table_seats, resolve_solve_config, solve_preflop

    mode_raw = equity_mode.strip().lower()
    if mode_raw not in ("random", "real"):
        typer.echo("--equity-mode must be 'random' or 'real'.", err=True)
        raise typer.Exit(code=1)
    eq_mode: EquityMode = "real" if mode_raw == "real" else "random"

    num_players = parse_table_seats(positions)

    cfg = resolve_solve_config(
        num_players=num_players,
        iterations=iters,
        chance_samples=chance_samples,
        equity_mode=eq_mode,
        prune_min_mass=prune_min_mass,
        production=production,
    )
    out_path = output
    _default_6 = Path("artifacts/solver/preflop_cfr.json")
    if out_path == _default_6 and num_players != 6:
        out_path = preflop_cfr_path(num_players)
    if num_players == 2 and output == _default_6:
        out_path = Path(
            "artifacts/solver/preflop_hu_real.json"
            if cfg.equity_mode == "real"
            else "artifacts/solver/preflop_hu.json"
        )
        typer.echo(
            f"Note: HU solve — default output is {out_path} (pass -o to override).",
        )
    algo = "MCCFR" if num_players > 2 else "CFR+"
    nw = _workers_opt(workers)
    cpu = os.cpu_count() or 4
    if nw > cpu:
        typer.echo(
            f"Warning: --workers {nw} > cpu_count {cpu}; consider --workers {max(1, cpu - 1)}.",
            err=True,
        )
    eff_log = log_every if log_every > 0 else (5000 if cfg.iterations >= 10_000 else 0)
    prod_note = " production" if production else ""
    typer.echo(
        f"Solving preflop {algo} ({num_players}-max{prod_note}, iters={cfg.iterations}, "
        f"workers={nw}, chance_samples={cfg.chance_samples}, equity_mode={cfg.equity_mode})..."
    )
    typer.echo(
        "Solver uses CPU (tabular CFR + Numba MC). HHFormer training uses GPU; this step does not."
    )
    typer.echo(f"Output file (written at end only): {out_path.resolve()}")
    if cfg.equity_mode == "real":
        typer.echo(
            "Real equity: first run builds a 1326-combo cache (often 20–60 min on CPU); "
            "later runs load it in seconds."
        )
    if nw > 1:
        typer.echo(
            "Parallel CFR: progress prints to stderr every ~20s. "
            "Do not pipe stdout (PowerShell buffers); use plain terminal or `python -u`."
        )
    elif eff_log > 0:
        typer.echo(f"Single-process: iteration logs every {eff_log} iters.")
    typer.echo("Leave this terminal alone until done (Cursor/IDE Stop can cancel too).")
    if measure_exploitability:
        typer.echo(
            "Exploitability measurement is slow on large trees — omit for a faster chart-only run."
        )
    _configure_preflop_cli_logging()
    result = solve_preflop(
        num_players=num_players,
        iterations=iters,
        chance_samples=chance_samples,
        seed=seed,
        log_every=eff_log,
        max_raises=max_raises,
        workers=nw,
        measure_exploitability=measure_exploitability,
        equity_mode=eq_mode,
        equity_mc_samples=equity_mc_samples,
        production=production,
        prune_min_mass=prune_min_mass,
        progress=_preflop_cli_progress,
    )
    policy = CFRPolicy(
        strategy=result.strategy,
        equity_mode=result.equity_mode,
        equity_mc_samples=result.equity_mc_samples,
    )
    exp_save = result.exploitability_mbb if result.exploitability_mbb is not None else -1.0
    policy.save_json(
        out_path,
        iterations=result.iterations,
        exploitability_mbb=exp_save,
        equity_mode=result.equity_mode,
        equity_mc_samples=result.equity_mc_samples,
    )
    exp_msg = (
        f"{result.exploitability_mbb:.3f}"
        if result.exploitability_mbb is not None
        else "skipped (use --measure-exploitability)"
    )
    typer.echo(
        f"Preflop solve complete: info_sets={result.num_info_sets} "
        f"exploitability_mbb={exp_msg} workers={result.workers} "
        f"path={out_path.resolve()}"
    )


@solve_app.command("kuhn")
def solve_kuhn_cmd(
    iters: Annotated[int, typer.Option("--iters", min=1)] = 10_000,
    mode: Annotated[str, typer.Option("--mode", help="cfr_plus | vanilla | external")] = "cfr_plus",
) -> None:
    """Smoke-test CFR on Kuhn poker (reports exploitability in mbb/g)."""
    from poker_ai.solver.cfr import CFRSolver, ExternalSamplingMCCFRSolver
    from poker_ai.solver.validate import OpenSpielKuhnBridge, openspiel_exploitability_mbb

    game = OpenSpielKuhnBridge()
    if mode == "external":
        solver = ExternalSamplingMCCFRSolver(game)
    else:
        solver = CFRSolver(game, mode="cfr_plus" if mode == "cfr_plus" else "vanilla")
    solver.run(iters)
    strat = solver.average_strategy()
    exp = openspiel_exploitability_mbb(strat, big_blind=1.0)
    typer.echo(f"Kuhn {mode}: iters={iters} info_sets={len(strat)} exploitability_mbb={exp:.4f}")


@solve_app.command("install-texas")
def solve_install_texas_cmd(
    force: Annotated[
        bool,
        typer.Option("--force", help="Re-download and replace an existing install."),
    ] = False,
    version: Annotated[
        str,
        typer.Option("--version", help="GitHub release tag (default v0.2.0)."),
    ] = "v0.2.0",
    install_dir: Annotated[
        Path,
        typer.Option(
            "--install-dir", help="Install root (default artifacts/third_party/texassolver)."
        ),
    ] = Path("artifacts/third_party/texassolver"),
) -> None:
    """Download TexasSolver console binary for this OS (AGPL; not bundled in git)."""
    from poker_ai.solver.bridge.install_texas import env_setup_hint, install_texas_solver

    try:
        manifest = install_texas_solver(install_dir=install_dir, tag=version, force=force)
    except OSError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(env_setup_hint(manifest))


@solve_app.command("register-texas")
def solve_register_texas_cmd(
    zip_path: Annotated[
        Path | None,
        typer.Option("--zip", help="Local TexasSolver release zip (manual download)."),
    ] = None,
    exe_path: Annotated[
        Path | None,
        typer.Option("--exe", help="Built console_solver executable."),
    ] = None,
    version: Annotated[
        str,
        typer.Option("--version", help="Release tag for manifest (default v0.2.0)."),
    ] = "v0.2.0",
    install_dir: Annotated[
        Path,
        typer.Option("--install-dir", help="Install root."),
    ] = Path("artifacts/third_party/texassolver"),
    force: Annotated[
        bool,
        typer.Option("--force", help="Replace existing unpacked install."),
    ] = False,
) -> None:
    """Register TexasSolver from a local zip or built console_solver (no download)."""
    from poker_ai.solver.bridge.install_texas import (
        env_setup_hint,
        register_texas_executable,
        register_texas_from_zip,
    )

    if zip_path is None and exe_path is None:
        typer.echo("Provide --zip PATH or --exe PATH", err=True)
        raise typer.Exit(code=1)
    try:
        if zip_path is not None:
            manifest = register_texas_from_zip(
                zip_path,
                install_dir=install_dir,
                tag=version,
                force=force,
            )
        else:
            manifest = register_texas_executable(
                exe_path,  # type: ignore[arg-type]
                install_dir=install_dir,
                tag=version,
            )
    except (OSError, FileNotFoundError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(env_setup_hint(manifest))


@solve_app.command("texas-status")
def solve_texas_status_cmd(
    install_dir: Annotated[
        Path,
        typer.Option("--install-dir", help="Install root to inspect."),
    ] = Path("artifacts/third_party/texassolver"),
) -> None:
    """Show TexasSolver install / discovery status for this machine."""
    from poker_ai.solver.bridge.install_texas import texas_solver_status
    from poker_ai.solver.bridge.texas import TexasSolverDriver

    status = texas_solver_status(install_dir)
    typer.echo(f"platform={status['platform']} zip={status['release_zip']}")
    typer.echo(f"install_dir={status['install_dir']}")
    typer.echo(f"vendored_source={status['vendored_source']}")
    if status["installed"]:
        typer.echo(f"installed=yes version={status['version']}")
        typer.echo(f"executable={status['executable']}")
        typer.echo(f"resource_dir={status['resource_dir']}")
    else:
        typer.echo(
            "installed=no — run: python -m poker_ai solve install-texas "
            "(or register-texas --zip / --exe)"
        )
    drv = TexasSolverDriver(install_dir=install_dir)
    typer.echo(f"driver_available={drv.available()}")


@solve_app.command("grid")
def solve_grid_cmd(
    n_spots: Annotated[int, typer.Option("--n-spots", min=1, help="Spots in curated grid.")] = 128,
    cache_dir: Annotated[
        Path,
        typer.Option("--cache-dir", help="Solver cache root."),
    ] = Path("artifacts/solver_cache"),
    backend: Annotated[
        str,
        typer.Option("--backend", help="auto | mock | texas (TexasSolver AGPL)."),
    ] = "auto",
    seed: Annotated[int, typer.Option("--seed")] = 42,
    refresh: Annotated[
        bool,
        typer.Option("--refresh", help="Re-solve spots already in cache."),
    ] = False,
    continue_on_error: Annotated[
        bool,
        typer.Option(
            "--continue-on-error",
            help="Skip spots where TexasSolver crashes (logs failed_spots.jsonl).",
        ),
    ] = False,
    texas_threads: Annotated[
        int,
        typer.Option(
            "--texas-threads",
            min=1,
            max=16,
            help="Thread count passed to TexasSolver (lower = more stable on Windows).",
        ),
    ] = 2,
) -> None:
    """Overnight teacher run: solve a grid of postflop spots into the disk cache."""
    from poker_ai.solver.bridge.batch import solve_grid
    from poker_ai.solver.bridge.texas import Backend

    b_raw = backend.strip().lower()
    if b_raw not in ("auto", "mock", "texas"):
        typer.echo("--backend must be auto, mock, or texas.", err=True)
        raise typer.Exit(code=1)
    b: Backend = b_raw  # type: ignore[assignment]
    result = solve_grid(
        n_spots=n_spots,
        cache_dir=cache_dir,
        backend=b,
        seed=seed,
        skip_cached=not refresh,
        continue_on_error=continue_on_error,
        texas_threads=texas_threads,
    )
    typer.echo(
        f"Grid solve: requested={result.requested} new_solved={result.solved} "
        f"cache_hits={result.cache_hits} failed={result.failed} "
        f"backends={result.backends} path={cache_dir.resolve()}"
    )
    if result.failed_spots_path is not None:
        typer.echo(f"Failed spots logged: {result.failed_spots_path.resolve()}")


@train_app.command("student")
def train_student_cmd(
    epochs: Annotated[int, typer.Option("--epochs", min=1)] = 30,
    batch_size: Annotated[int, typer.Option("--batch-size", min=1)] = 128,
    cache_dir: Annotated[Path, typer.Option("--cache-dir")] = Path("artifacts/solver_cache"),
    hhformer_dir: Annotated[Path, typer.Option("--hhformer-dir", "-w")] = Path(
        "artifacts/hhformer/v1"
    ),
    output: Annotated[Path, typer.Option("--output", "-o")] = Path("artifacts/student/v1"),
    device: Annotated[str, typer.Option("--device", help="cpu | cuda | auto")] = "auto",
    seed: Annotated[int, typer.Option("--seed")] = 42,
) -> None:
    """Distil cached teacher strategies into the student head (HHFormer [CLS] + MLP)."""
    from poker_ai.learn.train_student import TrainStudentConfig, run_train_student

    metrics = run_train_student(
        cache_dir=cache_dir,
        hhformer_dir=hhformer_dir,
        artifact_dir=output,
        cfg=TrainStudentConfig(epochs=epochs, batch_size=batch_size, seed=seed, device=device),
    )
    typer.echo(
        f"Student training complete: mse_val={metrics.mse_val:.4f} kl_val={metrics.kl_val:.4f} "
        f"rows={metrics.train_rows}+{metrics.val_rows} artifacts={output.resolve()}"
    )


@train_app.command("value-net")
def train_value_net_cmd(
    epochs: Annotated[int, typer.Option("--epochs", min=1)] = 20,
    batch_size: Annotated[int, typer.Option("--batch-size", min=1)] = 128,
    cache_dir: Annotated[Path, typer.Option("--cache-dir")] = Path("artifacts/solver_cache"),
    hhformer_dir: Annotated[Path, typer.Option("--hhformer-dir", "-w")] = Path(
        "artifacts/hhformer/v1"
    ),
    output: Annotated[Path, typer.Option("--output", "-o")] = Path("artifacts/value_net/v1"),
    device: Annotated[str, typer.Option("--device", help="cpu | cuda | auto")] = "auto",
    seed: Annotated[int, typer.Option("--seed")] = 42,
) -> None:
    """Train scalar value head on solver cache rows (blueprint v2)."""
    from poker_ai.learn.train_value_net import TrainValueNetConfig, run_train_value_net

    metrics = run_train_value_net(
        cache_dir=cache_dir,
        hhformer_dir=hhformer_dir,
        artifact_dir=output,
        cfg=TrainValueNetConfig(epochs=epochs, batch_size=batch_size, seed=seed, device=device),
    )
    typer.echo(
        f"Value net complete: mse_val={metrics.mse_val:.4f} "
        f"rows={metrics.train_rows}+{metrics.val_rows} artifacts={output.resolve()}"
    )


@train_app.command("decision-quality")
def train_decision_quality_cmd(
    epochs: Annotated[int, typer.Option("--epochs", min=1)] = 15,
    batch_size: Annotated[int, typer.Option("--batch-size", min=1)] = 64,
    hhformer_dir: Annotated[Path, typer.Option("--hhformer-dir", "-w")] = Path(
        "artifacts/hhformer/v1"
    ),
    output: Annotated[
        Path,
        typer.Option("--output", "-o"),
    ] = Path("artifacts/decision_quality/v1"),
    row_limit: Annotated[int, typer.Option("--row-limit", min=100)] = 5000,
    device: Annotated[str, typer.Option("--device", help="cpu | cuda | auto")] = "auto",
    seed: Annotated[int, typer.Option("--seed")] = 42,
) -> None:
    """Train hero decision audit head vs GTO teacher on imported hands."""
    from poker_ai.learn.train_decision_quality import (
        TrainDecisionQualityConfig,
        run_train_decision_quality,
    )

    metrics = run_train_decision_quality(
        hhformer_dir=hhformer_dir,
        artifact_dir=output,
        cfg=TrainDecisionQualityConfig(
            epochs=epochs,
            batch_size=batch_size,
            seed=seed,
            device=device,
            row_limit=row_limit,
        ),
    )
    typer.echo(
        f"Decision quality complete: mse_val={metrics.mse_val:.4f} "
        f"mean_teacher_quality={metrics.mean_quality:.3f} "
        f"rows={metrics.train_rows}+{metrics.val_rows} artifacts={output.resolve()}"
    )


@train_app.command("multiway-student")
def train_multiway_student_cmd(
    epochs: Annotated[int, typer.Option("--epochs", min=1)] = 20,
    batch_size: Annotated[int, typer.Option("--batch-size", min=1)] = 32,
    hhformer_dir: Annotated[Path, typer.Option("--hhformer-dir", "-w")] = Path(
        "artifacts/hhformer/v1"
    ),
    output: Annotated[Path, typer.Option("--output", "-o")] = Path("artifacts/student/multiway_v1"),
    monker_dir: Annotated[
        Path | None,
        typer.Option(
            "--monker-dir",
            help="Monker JSON exports (default: POKER_AI_MONKER_EXPORT_DIR).",
        ),
    ] = None,
    device: Annotated[str, typer.Option("--device", help="cpu | cuda | auto")] = "auto",
    seed: Annotated[int, typer.Option("--seed")] = 42,
    row_limit: Annotated[
        int | None,
        typer.Option("--row-limit", min=100, help="Max DB training rows."),
    ] = 50_000,
) -> None:
    """Train multi-way postflop student (DB imitation + optional Monker JSON labels)."""
    from poker_ai.config.settings import get_settings
    from poker_ai.learn.train_multiway_student import (
        TrainMultiwayConfig,
        run_train_multiway_student,
    )

    settings = get_settings()
    mdir = monker_dir or settings.monker_export_dir
    metrics = run_train_multiway_student(
        session_factory=get_async_session_factory(),
        hhformer_dir=hhformer_dir,
        artifact_dir=output,
        cfg=TrainMultiwayConfig(
            epochs=epochs,
            batch_size=batch_size,
            seed=seed,
            device=device,
            row_limit=row_limit,
            monker_export_dir=mdir if mdir.is_dir() else None,
            write_monker_to_cache=settings.solver_cache_dir,
        ),
    )
    typer.echo(
        f"Multi-way student complete: mse_val={metrics.mse_val:.4f} "
        f"db={metrics.db_rows} monker={metrics.monker_rows} "
        f"train={metrics.train_rows} val={metrics.val_rows} artifacts={output.resolve()}"
    )


@train_app.command("cql")
def train_cql_cmd(
    epochs: Annotated[int, typer.Option("--epochs", min=1)] = 15,
    batch_size: Annotated[int, typer.Option("--batch-size", min=1)] = 128,
    alpha: Annotated[float, typer.Option("--alpha", min=0.0)] = 1.0,
    output: Annotated[Path, typer.Option("--output", "-o")] = Path("artifacts/cql/v1"),
    student_dir: Annotated[Path, typer.Option("--student-dir")] = Path("artifacts/student/v1"),
    device: Annotated[str, typer.Option("--device", help="cpu | cuda | auto")] = "auto",
    seed: Annotated[int, typer.Option("--seed")] = 42,
    max_rows: Annotated[
        int | None,
        typer.Option("--max-rows", min=100, help="Cap solver-cache training rows."),
    ] = 50_000,
) -> None:
    """Conservative Q-Learning offline policy from logged solver/student rows."""
    from poker_ai.learn.train_cql import CQLTrainConfig, run_train_cql

    cfg = CQLTrainConfig(
        epochs=epochs,
        batch_size=batch_size,
        alpha=alpha,
        seed=seed,
        device=device,
        max_rows=max_rows,
    )
    metrics = run_train_cql(artifact_dir=output, student_dir=student_dir, cfg=cfg)
    typer.echo(
        f"CQL training complete: rows={metrics.train_rows} loss={metrics.final_loss:.4f} "
        f"artifacts={output.resolve()}"
    )


@train_app.command("hhformer-finetune")
def train_hhformer_finetune_cmd(
    epochs: Annotated[int, typer.Option("--epochs", min=1)] = 8,
    batch_size: Annotated[int, typer.Option("--batch-size", min=1)] = 128,
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Fine-tuned HHFormer v2 artifact directory."),
    ] = Path("artifacts/hhformer/v2"),
    max_hands: Annotated[int, typer.Option("--max-hands", min=100)] = 5000,
    device: Annotated[str, typer.Option("--device", help="cpu | cuda | auto")] = "auto",
    seed: Annotated[int, typer.Option("--seed")] = 42,
) -> None:
    """Solver-supervised HHFormer continual pretrain → v2 candidate."""
    from poker_ai.learn.pretrain_hhformer import PretrainConfig, run_pretrain

    settings = get_settings()
    _ensure_sqlite_dir(settings.database_url)
    upgrade_head()
    factory = get_async_session_factory()
    cfg = PretrainConfig(
        epochs=epochs,
        batch_size=batch_size,
        seed=seed,
        device=device,
        max_hands=max_hands,
    )
    metrics = run_pretrain(artifact_dir=output, session_factory=factory, cfg=cfg)
    typer.echo(
        "HHFormer fine-tune complete: "
        f"map_acc={metrics.map_top1_acc:.3f} sop_auc={metrics.sop_auc:.3f} "
        f"artifacts={output.resolve()} — promote with: poker-ai models promote hhformer --confirm"
    )


@train_app.command("play-study")
def train_play_study_cmd(
    manifest: Annotated[
        Path,
        typer.Option("--manifest", "-m", help="Play-study manifest JSON."),
    ] = Path("artifacts/play_study/manifest.json"),
    hu_output: Annotated[Path, typer.Option("--hu-output")] = Path(
        "artifacts/student/play_study_hu_v1"
    ),
    multiway_output: Annotated[
        Path, typer.Option("--multiway-output")
    ] = Path("artifacts/student/play_study_multiway_v1"),
    hhformer_dir: Annotated[Path, typer.Option("--hhformer-dir", "-w")] = Path(
        "artifacts/hhformer/v1"
    ),
    device: Annotated[str, typer.Option("--device", help="cpu | cuda | auto")] = "auto",
    promote_router: Annotated[
        bool,
        typer.Option("--promote-router/--no-promote-router", help="Wire play-study weights into RouterPolicy."),
    ] = False,
) -> None:
    """Behavioral clone from play-vs-AI hero decisions (HU + multi-way split)."""
    from poker_ai.learn.train_multiway_student import TrainMultiwayConfig, run_train_multiway_student
    from poker_ai.learn.train_student import TrainStudentConfig, run_train_student

    if not manifest.is_file():
        typer.echo(f"Manifest missing: {manifest.resolve()}", err=True)
        raise typer.Exit(code=1)

    hu_metrics = run_train_student(
        hhformer_dir=hhformer_dir,
        artifact_dir=hu_output,
        play_study_manifest=manifest,
        play_study_only=True,
        cfg=TrainStudentConfig(device=device),
    )
    typer.echo(
        f"Play-study HU student: rows={hu_metrics.train_rows}+{hu_metrics.val_rows} "
        f"→ {hu_output.resolve()}"
    )

    mw_metrics = run_train_multiway_student(
        session_factory=get_async_session_factory(),
        hhformer_dir=hhformer_dir,
        artifact_dir=multiway_output,
        play_study_manifest=manifest,
        play_study_only=True,
        cfg=TrainMultiwayConfig(device=device),
    )
    typer.echo(
        f"Play-study multi-way student: train={mw_metrics.train_rows} "
        f"→ {multiway_output.resolve()}"
    )

    if promote_router:
        from poker_ai.policy.router_sources import promote_play_study_to_router

        status = promote_play_study_to_router(hu=True, multiway=True, confirm=True)
        typer.echo(f"Router promoted: HU={status.hu.student_dir} multiway={status.multiway.student_dir}")


@solve_app.command("monker-import")
def solve_monker_import(
    export_dir: Annotated[
        Path,
        typer.Option("--export-dir", "-d", help="Directory of Monker *.json exports."),
    ] = Path("artifacts/solver/monker_exports"),
    cache_dir: Annotated[
        Path,
        typer.Option("--cache-dir", help="Also write spots into solver cache."),
    ] = Path("artifacts/solver_cache"),
) -> None:
    """Import Monker JSON strategy files for multi-way training and runtime blend."""
    from poker_ai.learn.monker_rows import load_monker_training_rows
    from poker_ai.solver.bridge.monker import load_monker_export_dir

    spots = load_monker_export_dir(export_dir)
    rows = load_monker_training_rows(export_dir, also_write_cache=cache_dir)
    typer.echo(
        f"Monker import: {len(spots)} spots, {len(rows)} training rows "
        f"from {export_dir.resolve()} (cache={cache_dir.resolve()})"
    )


app.add_typer(solve_app, name="solve")


@equity_app.command("spot")
def equity_spot_cmd(
    hero: Annotated[str, typer.Argument(help="Hero hand e.g. AhKd or AA.")],
    villain: Annotated[
        str,
        typer.Option("--villain", "-v", help="Villain range notation or random."),
    ] = "random",
    board: Annotated[str, typer.Option("--board", "-b", help="Board cards e.g. Qh Jc Ts.")] = "",
    mode: Annotated[str, typer.Option("--mode", help="auto | exact | mc.")] = "auto",
    samples: Annotated[int, typer.Option("--samples", min=1000)] = 80_000,
) -> None:
    """Heads-up equity spot (same engine as web ``POST /equity``)."""
    from poker_ai.core.cards import cards_from_space_separated
    from poker_ai.equity.breakdown import equity_breakdown
    from poker_ai.equity.range_notation import range_from_notation
    from poker_ai.features.range import one_hot_range_from_hole_string

    hero_norm = hero.strip()
    if len(hero_norm) == 4 and " " not in hero_norm:
        hero_norm = f"{hero_norm[:2]} {hero_norm[2:]}"
    hero_range = one_hot_range_from_hole_string(hero_norm)
    hero_cards = cards_from_space_separated(hero_norm)
    board_cards = cards_from_space_separated(board) if board.strip() else ()
    villain_range = range_from_notation(
        villain,
        dead_cards=(*hero_cards, *board_cards),
    )
    bd, mode_used = equity_breakdown(
        hero_range,
        villain_range,
        board_cards,
        mode=mode,
        n_samples=samples,
    )
    typer.echo(
        f"mode={mode_used} hero={bd.hero_equity:.4f} villain={bd.villain_win:.4f} tie={bd.tie:.4f}"
    )


@equity_app.command("backfill")
def equity_backfill_cmd(
    since: Annotated[
        str | None,
        typer.Option("--since", help="UTC date YYYY-MM-DD — only hands ingested on/after."),
    ] = None,
    limit: Annotated[
        int | None,
        typer.Option("--limit", min=1, help="Max hands to scan."),
    ] = None,
    refresh: Annotated[
        bool,
        typer.Option("--refresh", help="Recompute even when equities exist."),
    ] = False,
    mc_samples: Annotated[int, typer.Option("--mc-samples", min=500)] = 6000,
) -> None:
    """Write ``results.*_equity`` for stored hands with known hole cards."""
    from datetime import datetime

    from poker_ai.equity.backfill import backfill_equities_sync

    settings = get_settings()
    _ensure_sqlite_dir(settings.database_url)
    upgrade_head()
    factory = get_async_session_factory()
    since_dt: datetime | None = None
    if since:
        since_dt = datetime.strptime(since, "%Y-%m-%d").replace(tzinfo=UTC)
    stats = backfill_equities_sync(
        factory,
        since=since_dt,
        limit=limit,
        skip_existing=not refresh,
        mc_samples=mc_samples,
        progress=lambda e: typer.echo(f"{e.get('pct', 0)}% {e.get('msg', '')}"),
    )
    typer.echo(
        f"Equity backfill: scanned={stats.hands_scanned} updated={stats.hands_updated} "
        f"seats={stats.seats_enriched} skipped_no_cards={stats.skipped_no_cards}"
    )


app.add_typer(equity_app, name="equity")


@solve_app.command("validate-student")
def validate_student_cmd(
    n_spots: Annotated[int, typer.Option("--n-spots", min=40)] = 1000,
    cache_dir: Annotated[Path, typer.Option("--cache-dir")] = Path("artifacts/solver_cache"),
    hhformer_dir: Annotated[Path, typer.Option("--hhformer-dir", "-w")] = Path(
        "artifacts/hhformer/v1"
    ),
    output: Annotated[Path, typer.Option("--output", "-o")] = Path("artifacts/student/v1"),
    backend: Annotated[str, typer.Option("--backend", help="mock | auto | texas")] = "mock",
    seed: Annotated[int, typer.Option("--seed")] = 42,
    epochs: Annotated[int, typer.Option("--epochs", min=1)] = 30,
) -> None:
    """Run Phase 7 exit gates: teacher grid → train → MSE ≤ 0.05 and p99 latency."""
    from poker_ai.learn.validate_student import run_student_gates

    gate = run_student_gates(
        n_spots=n_spots,
        cache_dir=cache_dir,
        hhformer_dir=hhformer_dir,
        student_dir=output,
        backend=backend,
        seed=seed,
        train_epochs=epochs,
    )
    typer.echo(
        f"Student gates: mse_val={gate.mse_val:.4f} ({'OK' if gate.mse_ok else 'FAIL'}) "
        f"p99={gate.p99_sec * 1000:.1f}ms ({'OK' if gate.latency_ok else 'FAIL'}) "
        f"spots={gate.n_spots}"
    )
    if not gate.mse_ok or not gate.latency_ok:
        raise typer.Exit(code=1)


@pipeline_app.command("run")
def pipeline_run(
    corpus: Annotated[
        Path | None,
        typer.Option("--corpus", help="Hand history tree to ingest (skip with --skip-ingest)."),
    ] = None,
    workers: Annotated[int, typer.Option("--workers", min=0)] = 0,
    skip_ingest: Annotated[bool, typer.Option("--skip-ingest")] = False,
    skip_features: Annotated[bool, typer.Option("--skip-features")] = False,
    skip_train: Annotated[bool, typer.Option("--skip-train")] = True,
    skip_embed: Annotated[bool, typer.Option("--skip-embed")] = True,
    skip_solve: Annotated[bool, typer.Option("--skip-solve")] = False,
    solver_grid: Annotated[
        bool,
        typer.Option(
            "--solver-grid",
            help="Run Phase 7 teacher grid into artifacts/solver_cache.",
        ),
    ] = False,
    train_student: Annotated[
        bool,
        typer.Option(
            "--train-student",
            help="Distil student from solver cache (requires cache or --solver-grid).",
        ),
    ] = False,
    student_spots: Annotated[
        int,
        typer.Option("--student-spots", min=1, help="Spots when --solver-grid is set."),
    ] = 256,
    student_epochs: Annotated[int, typer.Option("--student-epochs", min=1)] = 15,
    solver_backend: Annotated[
        str,
        typer.Option("--solver-backend", help="auto | mock | texas for --solver-grid."),
    ] = "auto",
    preflop_iters_6: Annotated[int, typer.Option("--preflop-iters-6", min=1)] = 20_000,
    preflop_iters_hu: Annotated[int, typer.Option("--preflop-iters-hu", min=1)] = 15_000,
) -> None:
    """Run connected phases: ingest → features → train/embed → CFR → grid → student."""
    from poker_ai.pipeline.run import PipelineConfig, run_pipeline

    nw = _workers_opt(workers)
    if not skip_ingest and corpus is None:
        typer.echo("Provide --corpus or use --skip-ingest.", err=True)
        raise typer.Exit(code=1)
    if train_student and not solver_grid:
        from poker_ai.solver.bridge.cache import SolverCache

        if SolverCache(Path("artifacts/solver_cache")).stats()["count"] == 0:
            typer.echo(
                "No solver cache found — add --solver-grid or run `poker_ai solve grid` first.",
                err=True,
            )
            raise typer.Exit(code=1)
    typer.echo(f"Pipeline starting (workers={nw})...")
    cfg = PipelineConfig(
        corpus=corpus,
        workers=nw,
        skip_ingest=skip_ingest,
        skip_features=skip_features,
        skip_train=skip_train,
        skip_embed=skip_embed,
        skip_solve=skip_solve,
        solver_grid=solver_grid,
        train_student=train_student,
        solver_grid_spots=student_spots,
        student_epochs=student_epochs,
        solver_backend=solver_backend,
        preflop_iters_6=preflop_iters_6,
        preflop_iters_hu=preflop_iters_hu,
    )
    result = run_pipeline(cfg)
    typer.echo(
        "Pipeline complete: "
        f"ingested={result.hands_ingested} features={result.features_written} "
        f"embeddings={result.embeddings_written} "
        f"preflop_6_info_sets={result.preflop_6_info_sets} "
        f"preflop_hu_info_sets={result.preflop_hu_info_sets} "
        f"solver_spots={result.solver_spots_cached} "
        f"student_mse={result.student_mse_val}"
    )


@policy_app.command("bench")
def policy_bench_cmd(
    n_samples: Annotated[int, typer.Option("--samples", min=10)] = 500,
    n_warmup: Annotated[int, typer.Option("--warmup", min=0)] = 10,
    report: Annotated[
        Path,
        typer.Option("--report", "-o", help="JSON report path."),
    ] = Path("reports/policy_bench.json"),
) -> None:
    """Benchmark propose() latency (p50/p99 ms) for available policies on a HU flop spot."""
    from poker_ai.policy.bench import bench_policy, write_bench_report
    from poker_ai.policy.distilled_policy import DistilledPolicy, load_best_policy
    from poker_ai.policy.heuristic import HeuristicPolicy
    from poker_ai.policy.postflop_equity import PostflopEquityPolicy
    from poker_ai.policy.stacked import StackedPolicy

    results = []
    for label, factory in (
        ("heuristic", HeuristicPolicy),
        ("postflop_equity", PostflopEquityPolicy),
        ("stacked", lambda: StackedPolicy.from_artifacts()),
        ("best", load_best_policy),
    ):
        try:
            pol = factory()
            results.append(bench_policy(pol, n_samples=n_samples, n_warmup=n_warmup))
            typer.echo(
                f"{label} ({pol.name}): p50={results[-1].p50_ms:.2f}ms "
                f"p99={results[-1].p99_ms:.2f}ms mean={results[-1].mean_ms:.2f}ms"
            )
        except Exception as exc:
            typer.echo(f"{label}: skipped ({exc})")

    if Path("artifacts/student/v1/student.safetensors").is_file():
        try:
            dist = DistilledPolicy.from_artifacts()
            r = bench_policy(dist, n_samples=n_samples, n_warmup=n_warmup)
            results.append(r)
            typer.echo(
                f"distilled: p50={r.p50_ms:.2f}ms p99={r.p99_ms:.2f}ms (target p99 < 10ms on CPU)"
            )
        except Exception as exc:
            typer.echo(f"distilled: skipped ({exc})")

    if results:
        write_bench_report(results, report)
        typer.echo(f"Report written: {report.resolve()}")


app.add_typer(policy_app, name="policy")
app.add_typer(pipeline_app, name="pipeline")


@league_app.command("run")
def league_run_cmd(
    hours: Annotated[
        float,
        typer.Option("--hours", min=0.01, help="Wall-clock cap for round-robin (seconds = hours×3600)."),
    ] = 0.1,
    until_hours: Annotated[
        float | None,
        typer.Option(
            "--until-hours",
            min=0.01,
            help="Run until wall clock elapses (random pairings). Default formats: 6max+9max.",
        ),
    ] = None,
    hands_per_matchup: Annotated[
        int,
        typer.Option(
            "--hands-per-matchup",
            min=10,
            help="Hands per round-robin matchup, or batch size per random job in --until-hours mode.",
        ),
    ] = 200,
    table_sizes: Annotated[
        str,
        typer.Option(
            "--table-sizes",
            help="Comma-separated seats: 2,6,9 or hu,6max,9max (default 2,6,9).",
        ),
    ] = "2,6,9",
    until_hu: Annotated[
        bool,
        typer.Option(
            "--until-hu/--no-until-hu",
            help="With --until-hours, include HU tables (default: multi-way only).",
        ),
    ] = False,
    workers: Annotated[
        int,
        typer.Option(
            "--workers",
            min=0,
            help="Parallel matchup processes (0 = auto ~75%% CPUs, 1 = serial).",
        ),
    ] = 0,
    seed: Annotated[int, typer.Option("--seed")] = 42,
    report: Annotated[
        Path,
        typer.Option("--report", "-o"),
    ] = Path("reports/league_leaderboard.json"),
) -> None:
    """Run mixed-format league (HU + multi-way); router switches brains per street."""
    from poker_ai.league.formats import parse_table_sizes
    from poker_ai.league.orchestrator import LeagueConfig, run_league

    run_until = until_hours is not None
    max_sec = (until_hours if run_until else hours) * 3600.0
    if run_until and table_sizes == "2,6,9":
        sizes = parse_table_sizes("6max,9max")
    else:
        sizes = parse_table_sizes(table_sizes)
    nw = _workers_opt(workers)
    result = run_league(
        cfg=LeagueConfig(
            hands_per_matchup=hands_per_matchup,
            max_wall_sec=max_sec,
            run_until_wall=run_until,
            until_include_hu=until_hu,
            until_multiway_only=not until_hu,
            seed=seed,
            report_path=report,
            table_sizes=sizes,
            workers=nw,
            min_hands_for_promotion=min(1000, hands_per_matchup * len(sizes) * 2),
        ),
    )
    schedule = "until_wall" if run_until else "round_robin"
    typer.echo(
        f"League done ({schedule}): hands={result.hands_played} matchups={result.matchups} "
        f"wall_h={result.wall_sec / 3600:.2f} workers={result.workers} "
        f"formats={','.join(result.formats_played)} "
        f"brain_switches={result.brain_switches_total} "
        f"main_elo={result.main_elo:.1f} main_aivat_bb100={result.main_aivat_bb100:.2f} "
        f"aivat_p={result.main_aivat_pvalue:.4f} promoted={result.promoted} "
        f"report={result.report_path.resolve()}"
    )


@league_app.command("run-replay")
def league_run_replay_cmd(
    limit: Annotated[int, typer.Option("--limit", min=50)] = 500,
    strata: Annotated[
        str,
        typer.Option("--strata", help="Comma-separated: hu,mw"),
    ] = "hu,mw",
    agents: Annotated[
        str,
        typer.Option("--agents", help="Comma-separated agent ids to score."),
    ] = "main_agent,distilled_gto",
    since: Annotated[
        str | None,
        typer.Option("--since", help="UTC date YYYY-MM-DD — hands ingested on/after."),
    ] = None,
) -> None:
    """Score policies on ingested hands (hero replay league — v2)."""
    from poker_ai.league.replay_league import run_replay_league

    since_dt = None
    if since:
        since_dt = datetime.fromisoformat(since).replace(tzinfo=UTC)
    report = run_replay_league(
        limit=limit,
        strata=strata,
        agents=agents,
        since=since_dt,
    )
    typer.echo(
        f"Replay league: hands={report.hands_scored} decisions={report.hero_decisions} "
        f"aivat_mode={report.aivat_mode} report={report.report_path}"
    )
    for agent in report.agents:
        typer.echo(
            f"  {agent.agent_id}: bb100={agent.bb_per_100:+.2f} "
            f"match={agent.action_match_pct:.1f}% hands={agent.hands}"
        )


@league_app.command("checkpoints")
def league_checkpoints_cmd() -> None:
    """List promoted main-agent checkpoints (Phase 9)."""
    from poker_ai.league.checkpoint_registry import current_checkpoint_id, list_checkpoints

    rows = list_checkpoints()
    cur = current_checkpoint_id()
    if not rows:
        typer.echo("No league checkpoints yet — run league until promotion fires.")
        return
    for cp in rows:
        mark = "*" if cp.checkpoint_id == cur else " "
        typer.echo(
            f"{mark} {cp.checkpoint_id} elo={cp.main_elo:.0f} hands={cp.hands} "
            f"promoted={cp.promoted} {cp.note}"
        )


@league_app.command("train-exploiters")
def league_train_exploiters_cmd(
    hands: Annotated[
        int,
        typer.Option("--hands", help="HU hands per checkpoint × strength trial."),
    ] = 400,
    max_checkpoints: Annotated[
        int,
        typer.Option("--max-checkpoints", help="Newest promoted snapshots to target."),
    ] = 5,
    out_dir: Annotated[
        Path,
        typer.Option("--out", "-o"),
    ] = Path("artifacts/league/exploiters/v1"),
) -> None:
    """Calibrate ExploitPolicy vs promoted main checkpoints (Phase 9 research loop)."""
    from poker_ai.league.exploiter_loop import ExploiterLoopConfig, run_exploiter_loop

    report = run_exploiter_loop(
        ExploiterLoopConfig(hands_per_matchup=hands, max_checkpoints=max_checkpoints),
        out_dir=out_dir,
    )
    typer.echo(
        f"Exploiter loop done: best_strength={report.best_strength:.2f} "
        f"beats_all={report.beats_all_checkpoints} "
        f"checkpoints={len({r.checkpoint_id for r in report.checkpoint_results})} "
        f"artifact={report.artifact_dir}"
    )


@league_app.command("leaderboard")
def league_leaderboard_cmd(
    report: Annotated[
        Path,
        typer.Option("--report", "-r"),
    ] = Path("reports/league_leaderboard.json"),
) -> None:
    """Print the latest league leaderboard JSON."""
    from poker_ai.league.orchestrator import load_leaderboard

    if not report.is_file():
        typer.echo(f"No report at {report} — run `poker_ai league run` first.", err=True)
        raise typer.Exit(code=1)
    data = load_leaderboard(report)
    rows = data.get("leaderboard") or []
    chip_bal = data.get("chip_balance")
    if chip_bal is not None:
        typer.echo(f"chip_balance={chip_bal} (expect 0 in zero-sum league)")
    for row in rows:
        fmt = row.get("formats") or {}
        typer.echo(
            f"{row.get('agent_id')}: elo={row.get('elo')} hands={row.get('hands')} "
            f"bb100={row.get('bb_per_100')} aivat_bb100={row.get('aivat_bb_per_100')} "
            f"aivat_p={row.get('aivat_pvalue')} "
            f"hu_dec={row.get('hu_decisions')} mw_dec={row.get('multiway_decisions')} "
            f"brain_sw={row.get('brain_switches')} formats={fmt}"
        )


app.add_typer(league_app, name="league")


@opponents_app.command("profile")
def opponents_profile_cmd(
    player_uid: Annotated[str, typer.Argument(help="HMAC player uid from ingest.")],
    weights: Annotated[
        Path,
        typer.Option(
            "--weights",
            "-w",
            "--artifact-dir",
            help="Style encoder artifact dir (default: artifacts/style_encoder/v1).",
        ),
    ] = Path("artifacts/style_encoder/v1"),
    max_hands: Annotated[
        int | None,
        typer.Option("--max-hands", min=1, help="Cap hands scanned from DB."),
    ] = None,
    device: Annotated[str, typer.Option("--device", help="cpu | cuda | auto")] = "cpu",
) -> None:
    """Print style vector, kNN neighbours, and canonical VPIP/PFR/AF for a player."""
    import asyncio

    from poker_ai.opponents.profile import format_profile_report, profile_for_player
    from poker_ai.store.loader import iter_parsed_hands_since

    settings = get_settings()
    art = weights
    _ensure_sqlite_dir(settings.database_url)
    upgrade_head()
    factory = get_async_session_factory()

    async def _load() -> list:
        hands = []
        async with factory() as session:
            async for hand in iter_parsed_hands_since(session, since=None):
                if any(p.player_uid == player_uid for p in hand.players):
                    hands.append(hand)
                if max_hands is not None and len(hands) >= max_hands:
                    break
        return hands

    hands = asyncio.run(_load())
    if not hands:
        typer.echo(f"No hands found for player_uid={player_uid}", err=True)
        raise typer.Exit(code=1)

    profile = profile_for_player(
        player_uid,
        hands,
        artifact_dir=art,
        device=device,
    )
    if profile is None:
        typer.echo("Profile build failed.", err=True)
        raise typer.Exit(code=1)
    typer.echo(format_profile_report(profile))


@opponents_app.command("eval-exploit")
def opponents_eval_exploit_cmd(
    hands: Annotated[int, typer.Option("--hands", min=50)] = 400,
    seed: Annotated[int, typer.Option("--seed")] = 42,
    baseline: Annotated[
        str,
        typer.Option(
            "--baseline",
            help="GTO baseline: best (Phase 7 router/student) | heuristic.",
        ),
    ] = "best",
    strength: Annotated[
        float,
        typer.Option(
            "--strength",
            min=0.0,
            max=1.0,
            help="Exploit deviation blend (0 = pure GTO, 1 = full nudge).",
        ),
    ] = 0.28,
    no_seat_alt: Annotated[
        bool,
        typer.Option("--no-seat-alt", help="Disable BTN/BB alternation per hand."),
    ] = False,
) -> None:
    """AIVAT BB/100: exploit policy vs GTO baseline vs TAG / station / maniac."""
    from poker_ai.opponents.eval import evaluate_exploit_vs_gto

    use_best = baseline.strip().lower() != "heuristic"
    results = evaluate_exploit_vs_gto(
        hands_per_opponent=hands,
        seed=seed,
        use_best_baseline=use_best,
        deviation_strength=strength,
        alternate_seats=not no_seat_alt,
    )
    bname = results[0].baseline_name if results else "?"
    typer.echo(f"baseline={bname} strength={strength} seat_alt={not no_seat_alt}")
    for r in results:
        typer.echo(
            f"{r.opponent}: gto={r.gto_aivat_bb100:+.2f} exploit={r.exploit_aivat_bb100:+.2f} "
            f"delta={r.delta_bb100:+.2f} bb/100 (hands={r.hands})"
        )
    mean_delta = sum(r.delta_bb100 for r in results) / max(1, len(results))
    typer.echo(f"mean_delta_vs_gto={mean_delta:+.2f} bb/100 (target >= +5 vs exploitable pool)")


app.add_typer(opponents_app, name="opponents")


@eval_app.command("aivat-audit")
def eval_aivat_audit_cmd(
    hands: Annotated[int, typer.Option("--hands", min=100)] = 1000,
    seed: Annotated[int, typer.Option("--seed")] = 42,
    report: Annotated[
        Path,
        typer.Option("--report", "-o"),
    ] = Path("reports/aivat_audit.json"),
) -> None:
    """Run full AIVAT audit on synthetic HU sample (v2)."""
    os.environ["POKER_AI_AIVAT_FULL"] = "1"
    from poker_ai.eval.aivat import run_aivat_audit

    result = run_aivat_audit(hands=hands, seed=seed, report_path=report)
    typer.echo(
        f"AIVAT audit: hands={result.hands} naive_stderr={result.naive_stderr:.4f} "
        f"full_stderr={result.full_stderr:.4f} reduction={result.stderr_reduction_pct:.1f}% "
        f"report={result.report_path}"
    )


app.add_typer(eval_app, name="eval")

models_app = typer.Typer(no_args_is_help=True, help="Model registry promote/rollback (Phase W8).")
router_app = typer.Typer(no_args_is_help=True, help="RouterPolicy student bindings.")


@models_app.command("list")
def models_list_cmd() -> None:
    """Show versioned models and router bindings."""
    from poker_ai.learn.model_registry import list_models
    from poker_ai.policy.router_sources import get_router_status

    for m in list_models():
        cur = m.current_version or "—"
        cand = f" candidate={m.candidate_version}" if m.candidate_version else ""
        typer.echo(f"{m.name}: current={cur}{cand}")
    status = get_router_status()
    typer.echo(f"router HU → {status.hu.student_dir} ({status.hu.source})")
    typer.echo(f"router multiway → {status.multiway.student_dir} ({status.multiway.source})")


@models_app.command("gates")
def models_gates_cmd(
    name: Annotated[str, typer.Argument(help="Registry name (e.g. student_hu).")],
) -> None:
    """Show promotion gates (drift, league AIVAT, candidate metrics, canary)."""
    from poker_ai.learn.promotion_gates import evaluate_promotion_gates

    report = evaluate_promotion_gates(name)
    for c in report.checks:
        mark = "OK" if c.passed else "FAIL"
        req = "" if c.required else " (optional)"
        typer.echo(f"  [{mark}] {c.label}{req}: {c.detail}")
    if report.can_promote:
        typer.echo(f"{name}: gates passed — promote with --confirm")
    else:
        typer.echo(f"{name}: blocked ({', '.join(report.blocking) or 'see above'})", err=True)
        raise typer.Exit(code=1)


@models_app.command("promote")
def models_promote_cmd(
    name: Annotated[str, typer.Argument(help="Registry name (e.g. hhformer, student_hu).")],
    confirm: Annotated[
        bool,
        typer.Option("--confirm", help="Required after reviewing drift/league gates."),
    ] = False,
    skip_gates: Annotated[
        bool,
        typer.Option("--skip-gates", help="Override gate failures (emergency only)."),
    ] = False,
) -> None:
    """Promote candidate model version to CURRENT."""
    from poker_ai.learn.model_registry import promote

    info = promote(name, confirm=confirm, skip_gates=skip_gates)
    typer.echo(f"Promoted {info.name} → {info.current_version} ({info.current_path})")


@models_app.command("rollback")
def models_rollback_cmd(
    name: Annotated[str, typer.Argument(help="Registry name.")],
) -> None:
    """Rollback to PREVIOUS version pointer."""
    from poker_ai.learn.model_registry import rollback

    info = rollback(name)
    typer.echo(f"Rolled back {info.name} → {info.current_version}")


@router_app.command("status")
def router_status_cmd() -> None:
    """Show which student dirs RouterPolicy uses."""
    from poker_ai.policy.router_sources import get_router_status

    status = get_router_status()
    for binding in (status.hu, status.multiway):
        tag = " [play-study]" if binding.play_study else ""
        typer.echo(f"{binding.route}: {binding.student_dir} ({binding.source}){tag}")


@router_app.command("promote-play-study")
def router_promote_play_study_cmd(
    confirm: Annotated[
        bool,
        typer.Option("--confirm", help="Required after play-study training completes."),
    ] = False,
    hu: Annotated[bool, typer.Option("--hu/--no-hu", help="Promote HU play-study student.")] = True,
    multiway: Annotated[
        bool,
        typer.Option("--multiway/--no-multiway", help="Promote multi-way play-study student."),
    ] = True,
) -> None:
    """Wire play-study artifacts into RouterPolicy (runtime decide/play bots)."""
    from poker_ai.policy.router_sources import promote_play_study_to_router

    status = promote_play_study_to_router(hu=hu, multiway=multiway, confirm=confirm)
    typer.echo(f"Router HU → {status.hu.student_dir}")
    typer.echo(f"Router multiway → {status.multiway.student_dir}")


@router_app.command("rollback")
def router_rollback_cmd(
    route: Annotated[str, typer.Argument(help="hu or multiway")],
) -> None:
    """Restore router pointer from ROUTER_*_PREVIOUS."""
    from poker_ai.policy.router_sources import rollback_router_play_study

    if route not in ("hu", "multiway"):
        typer.echo("route must be hu or multiway", err=True)
        raise typer.Exit(code=1)
    status = rollback_router_play_study(route)  # type: ignore[arg-type]
    typer.echo(f"Router {route} → {getattr(status, route).student_dir}")


models_app.add_typer(router_app, name="router")
app.add_typer(models_app, name="models")

app.command(
    "serve",
    help="Run FastAPI + Vite dashboard (Phase 10).",
)(serve_cmd)


def main() -> None:
    """Console script entry (see ``project.scripts``)."""
    app()


if __name__ == "__main__":
    main()
