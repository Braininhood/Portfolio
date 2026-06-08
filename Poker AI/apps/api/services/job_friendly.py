"""Plain-language job results and advice for non-technical users (Phase W1+)."""

from __future__ import annotations

from typing import Any


def _num(v: Any) -> int | float | None:
    if isinstance(v, (int, float)):
        return v
    return None


def _metrics_dict(result: dict[str, Any]) -> dict[str, Any]:
    raw = result.get("metrics")
    if isinstance(raw, dict):
        return raw
    return {}


def friendly_error_message(raw: str | None) -> str:
    if not raw:
        return "Something went wrong. Try again or check System health."
    low = raw.lower()
    if "charmap" in low or "unicodeencodeerror" in low:
        return (
            "A Windows text-encoding issue stopped this task. "
            "This has been fixed for training logs — please run the job again."
        )
    if "no hands in store" in low or "ingest before" in low:
        return "Your hand library is empty. Go to Import and add hand histories first."
    if "no training rows" in low or "solve grid" in low:
        return (
            "The AI teacher cache is empty. Run a small solver grid first, "
            "or use Setup when it is available."
        )
    if "need >=" in low and "multi-way" in low:
        return "Not enough multi-way hands yet. Import more ring-game histories (6–9 players)."
    if "filenotfound" in low or "no such file" in low:
        return "A folder or file could not be found. Check the path and try again."
    if len(raw) > 280:
        return raw[:280] + "…"
    return raw


def friendly_job_summary(
    job_type: str,
    *,
    status: str,
    result: dict[str, Any] | None = None,
    error: str | None = None,
    db_hands: int | None = None,
) -> dict[str, Any]:
    """Build headline, explanation, advice list, and next-step hints."""
    if status == "error":
        return {
            "headline": "Task did not finish",
            "explanation": friendly_error_message(error),
            "advice": _error_advice(job_type, error),
            "next_steps": _next_steps(job_type, ok=False),
            "severity": "error",
        }
    if status == "cancelled":
        return {
            "headline": "Task cancelled",
            "explanation": "You stopped this task before it finished.",
            "advice": ["You can start it again anytime from Jobs or Import."],
            "next_steps": _next_steps(job_type, ok=False),
            "severity": "neutral",
        }
    if status in ("queued", "running"):
        return {
            "headline": _type_title(job_type),
            "explanation": "Working on your computer — you can leave this page open or come back later.",
            "advice": [],
            "next_steps": [],
            "severity": "info",
        }

    return _success_summary(job_type, result or {}, db_hands)


def _type_title(job_type: str) -> str:
    titles = {
        "ingest": "Import hand histories",
        "features_build": "Prepare hands for AI training",
        "train_hhformer": "Train HHFormer model",
        "solve_preflop": "Solve preflop strategy",
        "solve_grid": "Build solver teacher cache",
        "train_student": "Train decision AI (student)",
        "train_style": "Train player-style model",
    "train_multiway_student": "Train multi-way AI",
    "train_cql": "Train CQL policy",
    "train_hhformer_finetune": "Fine-tune HHFormer on solver outputs",
    "play_study_materialize": "Register play-vs-AI hands for training",
    "play_auto_learn": "Learn from your Play vs AI sessions",
    "equity_backfill": "Backfill results.*_equity in database",
        "league_run": "Run bot league",
        "validate_student": "Validate student quality gates",
        "league_train_exploiters": "Train league exploiters",
        "features_export_parquet": "Export feature snapshot",
        "features_validate_blueprint": "Validate feature schema",
        "aivat_audit": "Run AIVAT audit",
        "league_replay_run": "League on your library",
        "policy_bench": "Policy speed test",
        "solve_kuhn": "Solver sanity (Kuhn)",
        "features_hhformer_embed": "Export embeddings",
        "opponents_eval_exploit": "Test exploit vs baseline",
        "train_value_net": "Train value net",
        "train_decision_quality": "Train decision quality",
    }
    return titles.get(job_type, job_type.replace("_", " ").title())


def _success_summary(
    job_type: str,
    result: dict[str, Any],
    db_hands: int | None,
) -> dict[str, Any]:
    advice: list[str] = []
    next_steps = _next_steps(job_type, ok=True)

    if job_type == "ingest":
        new_h = int(_num(result.get("hands_new")) or 0)
        updated = int(_num(result.get("hands_updated")) or 0)
        skipped = int(_num(result.get("hands_skipped")) or 0)
        files = int(_num(result.get("files_seen")) or 0)
        before = _num(result.get("hands_before"))
        after = _num(result.get("hands_after"))
        if db_hands is not None and after is None:
            after = float(db_hands)
        headline = f"{new_h:,} new hands added to your library"
        explanation = (
            f"We scanned {files:,} file(s) including all subfolders. "
            f"{new_h:,} hands were new; {updated:,} were already in your library and were refreshed "
            "(not counted twice). "
        )
        if skipped > 0:
            explanation += f"{skipped:,} incomplete hands were skipped. "
        if before is not None and after is not None:
            explanation += (
                f"Your library went from {int(before):,} to {int(after):,} hands "
                f"(+{int(after - before):,})."
            )
        if new_h == 0 and updated > 0:
            headline = "No new hands - library already had these files"
            advice.append(
                "All parsed hands matched hands you imported before. "
                "Choose a different folder or add new hand history files."
            )
        elif new_h == 0:
            advice.append("No hands were saved. Check that files are valid hand histories (.txt, .phh, .json).")
        elif new_h < 500:
            advice.append("Fewer than 500 new hands - fine for testing; import more for stronger AI training.")
        elif new_h >= 5_000:
            advice.append("Good batch of new hands for training and player profiles.")
        if updated > new_h * 2 and new_h > 0:
            advice.append(
                "Many duplicates were refreshed - normal if you re-import the same folder. "
                "Only new hands increase your library size."
            )
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "features_build":
        written = int(_num(result.get("hands_written")) or 0)
        headline = f"{written:,} hands prepared for AI training"
        explanation = (
            "We built a training file from hands already in your library. "
            "This step does not add new hands — it prepares data for models like HHFormer."
        )
        if written == 0:
            advice.append("No hands were processed. Import hand histories first, then run this again.")
        elif written < 1_000:
            advice.append(
                "Under 1,000 hands — OK to experiment, but import more (5,000+) for reliable model quality."
            )
        elif written >= 10_000:
            advice.append("Solid amount for starting HHFormer training from the Jobs page.")
        else:
            advice.append("Reasonable size. You can import more hands anytime to improve models later.")
        if db_hands is not None and written > 0 and written < db_hands * 0.5:
            advice.append(
                "Only part of your library was included (incremental build). "
                "That is normal if you ran this before."
            )
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "train_hhformer":
        metrics = _metrics_dict(result)
        map_acc = _num(metrics.get("map_top1_acc"))
        headline = "HHFormer training finished"
        explanation = (
            "HHFormer learns patterns from your hand histories (positions, actions, outcomes). "
            "Other AI steps use this model."
        )
        if map_acc is not None:
            explanation += f" Validation accuracy: {map_acc:.0%}."
            if map_acc < 0.25:
                advice.append("Low accuracy — try more hands, more epochs, or check import quality.")
            elif map_acc >= 0.35:
                advice.append("Accuracy looks healthy for a first training run.")
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "solve_preflop":
        info_sets = int(_num(result.get("info_sets")) or 0)
        headline = "Preflop strategy chart saved"
        explanation = (
            f"Computed a preflop strategy with {info_sets:,} decision points. "
            "The bot uses this for opening and 3-bet spots in heads-up pots — a required step in the full AI path."
        )
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "solve_grid":
        solved = int(_num(result.get("solved")) or 0)
        failed = int(_num(result.get("failed")) or 0)
        headline = f"Solver cache updated ({solved} new spots)"
        explanation = (
            "Postflop spots were solved (or loaded from cache) to teach the student AI. "
            "TexasSolver spots need the solver installed under System."
        )
        if failed > 0:
            advice.append(f"{failed} spot(s) failed — often OK if using mock mode or missing TexasSolver.")
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "train_student":
        metrics = _metrics_dict(result)
        mse = _num(metrics.get("mse_val"))
        headline = "Decision AI (student) trained"
        explanation = "The student model learns to mimic the solver teacher on postflop spots."
        if mse is not None and mse > 0.15:
            advice.append("Validation error is high — run a larger solver grid or import more hands.")
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "train_style":
        metrics = _metrics_dict(result)
        knn = _num(metrics.get("knn_top5_acc"))
        val_players = int(_num(metrics.get("val_players")) or 0)
        train_w = int(_num(metrics.get("train_windows")) or 0)
        headline = "Player-style model trained"
        explanation = (
            f"Learned style fingerprints from {train_w:,} hand windows "
            f"across {val_players:,} players in validation."
        )
        if knn is not None:
            explanation += f" Player-match accuracy (top-5): {knn * 100:.1f}%."
        if knn is not None and knn < 0.5:
            advice.append("Style matching is weak — import more hands from diverse opponents.")
        elif knn is not None and knn >= 0.6:
            advice.append("Strong player matching — useful for Profiles and opponent adaptation.")
        if val_players < 20:
            advice.append("Very few unique players — add histories from more sites or stakes.")
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "train_cql":
        metrics = _metrics_dict(result)
        loss = _num(metrics.get("final_loss"))
        rows = int(_num(metrics.get("train_rows")) or 0)
        alpha = _num(metrics.get("alpha"))
        headline = "CQL policy trained"
        explanation = (
            f"Conservative offline policy saved from {rows:,} logged rows. "
            "League can now include cql_agent when the artifact exists."
        )
        if loss is not None:
            explanation += f" Final loss: {loss:.4f}."
        if alpha is not None:
            explanation += f" Alpha (conservatism): {alpha:.2f}."
        if rows < 5000:
            advice.append(
                "Few training rows — build a larger solver cache or raise max_rows, then re-run."
            )
        if loss is not None and loss > 2.0:
            advice.append("High loss — try lower alpha (0.7) or more epochs with same seed.")
        elif loss is not None and loss <= 0.5:
            advice.append("Loss looks healthy — run league to compare cql_agent vs student.")
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "train_hhformer_finetune":
        metrics = _metrics_dict(result)
        map_acc = _num(metrics.get("map_top1_acc"))
        sop = _num(metrics.get("sop_auc"))
        headline = "HHFormer v2 fine-tune finished"
        explanation = (
            "Solver-supervised continual pretrain wrote a v2 candidate. "
            "Compare MAP/SOP on Models before promote."
        )
        if map_acc is not None:
            explanation += f" MAP: {map_acc:.0%}."
        if sop is not None:
            explanation += f" SOP AUC: {sop:.2f}."
        if map_acc is not None and map_acc < 0.2:
            advice.append("MAP below v1 — reduce epochs or max_hands, or enlarge solver cache.")
        elif map_acc is not None and map_acc >= 0.3:
            advice.append("Metrics look competitive — check drift green, then promote on Models.")
        advice.append("Artifact: artifacts/hhformer/v2 — promote only after league gates pass.")
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "league_run":
        hands = int(_num(result.get("hands_played")) or 0)
        promoted = bool(result.get("promoted"))
        until = bool(result.get("run_until_wall"))
        mode = "wall-clock" if until else "round-robin"
        headline = f"League finished ({hands:,} hands, {mode})"
        explanation = (
            "Bots played against each other to rank strengths. "
            + ("Main agent promotion criteria met." if promoted else "Promotion not reached this run.")
        )
        if until:
            advice.append("Checkpoints saved when promotion fires — run Train league exploiters next.")
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "validate_student":
        mse = _num(result.get("mse_val"))
        p99_ms = (_num(result.get("p99_sec")) or 0) * 1000
        passed = bool(result.get("passed"))
        headline = "Student gates passed" if passed else "Student gates failed"
        explanation = (
            f"MSE {mse:.4f} ({'OK' if result.get('mse_ok') else 'fail'}), "
            f"p99 {p99_ms:.1f} ms ({'OK' if result.get('latency_ok') else 'fail'})."
        )
        if passed:
            advice.append("Student meets Phase 7 thresholds — safe to use in league and Play vs AI.")
        return _pack(headline, explanation, advice, next_steps, "success" if passed else "warning")

    if job_type == "league_train_exploiters":
        best = _num(result.get("best_strength"))
        n_cp = int(_num(result.get("checkpoints_targeted")) or 0)
        beats = bool(result.get("beats_all_checkpoints"))
        headline = f"Exploiters calibrated (strength {best:.2f})" if best is not None else "Exploiter training finished"
        explanation = (
            f"Tested {n_cp} checkpoint(s). "
            + ("Beats all targets at min delta." if beats else "Review metrics.json for per-checkpoint deltas.")
        )
        advice.append(f"Artifacts: {result.get('artifact_dir', 'artifacts/league/exploiters/v1')}")
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "train_multiway_student":
        metrics = _metrics_dict(result)
        mse = _num(metrics.get("mse_val"))
        db_rows = int(_num(metrics.get("db_rows")) or 0)
        monker_rows = int(_num(metrics.get("monker_rows")) or 0)
        train_rows = int(_num(metrics.get("train_rows")) or 0)
        headline = "Multi-way AI training finished"
        explanation = (
            f"Trained on {train_rows:,} rows from your database "
            f"({db_rows:,} multi-way hero spots"
            + (f", plus {monker_rows:,} Monker labels" if monker_rows else "")
            + ")."
        )
        if db_rows < 1000:
            advice.append(
                "Few multi-way spots in your DB — import more 6–9 player ring-game histories."
            )
        if monker_rows == 0:
            advice.append(
                "No Monker export labels used — optional, but they improve quality when available."
            )
        if mse is not None and mse > 0.2:
            advice.append("Validation error is high — train longer or increase row_limit.")
        elif mse is not None and mse <= 0.15:
            advice.append("Validation error looks healthy — check Status for the green checkmark.")
        if db_hands is not None and db_hands < 5000:
            advice.append(f"Library has {db_hands:,} hands total — more data helps all models.")
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "play_study_materialize":
        hands = int(_num(result.get("hands")) or 0)
        decisions = int(_num(result.get("hero_decisions")) or 0)
        manifest = result.get("manifest_path") or "artifacts/play_study/manifest.json"
        headline = f"Play study pool ready ({hands:,} hands, {decisions:,} hero decisions)"
        explanation = (
            "Hands stay in play_hands in your database. A training manifest was written so "
            "future student / NN jobs can load hero decisions via poker_ai.learn.play_study_loader."
        )
        advice.append(f"Manifest: {manifest}")
        if decisions < 50:
            advice.append("Play more hands vs bots — more hero decisions improve training quality.")
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "play_auto_learn":
        raw_trained = result.get("trained")
        trained: list[Any] = raw_trained if isinstance(raw_trained, list) else []
        routes = ", ".join(str(t.get("route", "?")) for t in trained) or "none"
        promoted = result.get("router") is not None
        headline = "Play vs AI learning complete"
        explanation = (
            f"Retrained from your sessions ({routes}) and "
            + ("activated new weights in the live router." if promoted else "saved updated weights.")
        )
        advice.append("Your next hand at /play uses the updated policy automatically.")
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "equity_backfill":
        raw_stats = result.get("stats")
        stats: dict[str, Any] = raw_stats if isinstance(raw_stats, dict) else result
        updated = int(_num(stats.get("hands_updated")) or 0)
        seats = int(_num(stats.get("seats_enriched")) or 0)
        headline = f"Equities backfilled ({updated:,} hands, {seats:,} seats)"
        explanation = (
            "Replayer, Drill, and Play hints can now read hero equity from the database "
            "instead of recomputing on every page load."
        )
        if updated == 0:
            advice.append("No rows updated — run Import first or pass refresh=true to recompute.")
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "features_export_parquet":
        rows = int(_num(result.get("num_rows")) or 0)
        headline = f"Feature snapshot exported ({rows:,} rows)"
        explanation = "Parquet + manifest written under data/processed/ for analytics."
        advice.append(f"Manifest: {result.get('manifest_path', 'data/processed/')}")
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "features_validate_blueprint":
        checked = int(_num(result.get("hands_checked")) or 0)
        full = bool(result.get("blueprint_full"))
        headline = f"Feature schema OK ({checked:,} hands)"
        explanation = (
            "Blueprint full columns validated."
            if full
            else "Standard v1 columns validated — run Extended preset before full-mode export."
        )
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "aivat_audit":
        reduction = _num(result.get("stderr_reduction_pct"))
        headline = "AIVAT audit complete"
        explanation = (
            f"Full AIVAT stderr reduction: {reduction:.1f}% "
            f"(target >= 15%). View details on League → AIVAT tab."
        )
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "league_replay_run":
        hands = int(_num(result.get("hands_scored")) or 0)
        dec = int(_num(result.get("hero_decisions")) or 0)
        headline = f"Replay league scored {hands:,} hands"
        explanation = f"{dec:,} hero decisions evaluated on your imported library."
        advice.append("Open League → Real hands tab for BB/100 and action-match breakdown.")
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "policy_bench":
        p99 = _num(result.get("best_p99_ms"))
        passed = bool(result.get("passed"))
        headline = f"Policy speed: p99 {p99:.1f} ms" if p99 is not None else "Policy benchmark done"
        explanation = "Latency test for decision policies (Phase 10 gate: p99 < 30 ms)."
        if not passed:
            advice.append("p99 above 30 ms — use GPU student or reduce model size for Play vs AI.")
        return _pack(headline, explanation, advice, next_steps, "success" if passed else "warning")

    if job_type == "solve_kuhn":
        exp = _num(result.get("exploitability_mbb"))
        headline = "Kuhn CFR sanity check passed" if result.get("passed") else "Kuhn CFR finished"
        explanation = f"Exploitability {exp:.4f} mbb/g — confirms solver stack works."
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "features_hhformer_embed":
        n = int(_num(result.get("hands_written")) or 0)
        headline = f"Exported {n:,} HHFormer embeddings"
        explanation = "Frozen [CLS] vectors written for research / external tools."
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "opponents_eval_exploit":
        delta = _num(result.get("mean_delta_bb100"))
        headline = f"Exploit test: {delta:+.2f} bb/100 vs baseline" if delta is not None else "Exploit eval done"
        explanation = "Compared exploit policy vs GTO baseline vs scripted opponents."
        if delta is not None and delta < 5:
            advice.append("Mean delta below +5 bb/100 target — try higher strength or more hands.")
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "train_value_net":
        metrics = _metrics_dict(result)
        mse = _num(metrics.get("mse_val"))
        headline = "Value net trained"
        explanation = "Scalar EV head learned from solver cache teacher targets."
        if mse is not None:
            explanation += f" Validation MSE: {mse:.4f}."
        return _pack(headline, explanation, advice, next_steps, "success")

    if job_type == "train_decision_quality":
        metrics = _metrics_dict(result)
        mse = _num(metrics.get("mse_val"))
        mean_q = _num(metrics.get("mean_quality"))
        headline = "Decision quality model trained"
        explanation = "Audit head learned how GTO-aligned hero spots are in your library."
        if mean_q is not None:
            explanation += f" Mean teacher quality: {mean_q:.2f}."
        if mse is not None and mse > 0.05:
            advice.append("Higher error — run equity backfill and import more hands.")
        return _pack(headline, explanation, advice, next_steps, "success")

    return {
        "headline": "Task completed",
        "explanation": "See technical details if you need them.",
        "advice": advice,
        "next_steps": next_steps,
        "severity": "success",
    }


def _pack(
    headline: str,
    explanation: str,
    advice: list[str],
    next_steps: list[dict[str, Any]],
    severity: str,
) -> dict[str, Any]:
    return {
        "headline": headline,
        "explanation": explanation,
        "advice": advice,
        "next_steps": next_steps,
        "severity": severity,
    }


def _error_advice(job_type: str, error: str | None) -> list[str]:
    out: list[str] = []
    if job_type in ("train_hhformer", "train_student", "features_build") and error:
        if "no hands" in (error or "").lower():
            out.append("Open Import and add hand history files or a folder on this PC.")
    if job_type == "train_student":
        out.append("Run solver grid (mock is fine for testing) before training the student.")
    return out


def _next_steps(job_type: str, *, ok: bool) -> list[dict[str, Any]]:
    if not ok:
        if job_type == "ingest":
            return [{"label": "Try Import again", "path": "/import"}]
        return [{"label": "System check", "path": "/health"}]

    common_import: dict[str, Any] = {"label": "Import more hands", "path": "/import"}
    browse: dict[str, Any] = {"label": "Browse hands", "path": "/"}

    steps: dict[str, list[dict[str, Any]]] = {
        "features_build": [
            {
                "label": "Train HHFormer",
                "path": "/jobs",
                "hint": "Starts HHFormer training and shows progress on Tasks",
                "action": "start_job",
                "job_type": "train_hhformer",
                "job_params": {"epochs": 2, "max_hands": 500, "device": "cpu"},
            },
            browse,
            common_import,
        ],
        "ingest": [
            browse,
            {
                "label": "Prepare for AI training",
                "path": "/jobs",
                "hint": "Build features.jsonl from your library",
                "action": "start_job",
                "job_type": "features_build",
                "job_params": {},
            },
            {"label": "System overview", "path": "/health"},
        ],
        "train_hhformer": [
            {
                "label": "Train decision AI",
                "path": "/jobs",
                "action": "start_job",
                "job_type": "train_student",
                "job_params": {},
            },
            {"label": "Solver spots", "path": "/solver"},
        ],
        "solve_grid": [
            {
                "label": "Train student AI",
                "path": "/jobs",
                "action": "start_job",
                "job_type": "train_student",
                "job_params": {},
            }
        ],
        "train_student": [
            {
                "label": "Train CQL policy",
                "path": "/jobs",
                "action": "start_job",
                "job_type": "train_cql",
                "job_params": {"epochs": 15, "alpha": 1.0, "device": "auto"},
            },
            {"label": "System status", "path": "/status"},
        ],
        "train_cql": [
            {
                "label": "Fine-tune HHFormer v2",
                "path": "/jobs",
                "action": "start_job",
                "job_type": "train_hhformer_finetune",
                "job_params": {"epochs": 8, "max_hands": 5000, "device": "auto"},
            },
            {"label": "Models page", "path": "/models"},
        ],
        "train_hhformer_finetune": [
            {"label": "Promote HHFormer v2", "path": "/models"},
            {"label": "Train player styles", "path": "/setup"},
        ],
        "train_style": [
            {
                "label": "Run bot league",
                "path": "/jobs",
                "action": "start_job",
                "job_type": "league_run",
                "job_params": {"hours": 0.1, "hands_per_matchup": 200},
            }
        ],
        "league_run": [{"label": "League leaderboard", "path": "/league"}],
        "validate_student": [
            {
                "label": "Run bot league",
                "path": "/jobs",
                "action": "start_job",
                "job_type": "league_run",
                "job_params": {"hours": 0.1, "hands_per_matchup": 200},
            },
            {"label": "System status", "path": "/status"},
        ],
        "league_train_exploiters": [
            {"label": "League leaderboard", "path": "/league"},
            {"label": "Run longer league", "path": "/jobs"},
        ],
        "features_validate_blueprint": [
            {
                "label": "Export feature snapshot",
                "path": "/jobs?task=features_export_parquet&preset=quick",
            },
            {"label": "Train HHFormer", "path": "/jobs?task=train_hhformer&preset=recommended"},
        ],
        "train_value_net": [
            {"label": "Train decision quality", "path": "/jobs?task=train_decision_quality&preset=recommended"},
            {"label": "System status", "path": "/status"},
        ],
        "train_decision_quality": [
            {"label": "League on your library", "path": "/jobs?task=league_replay_run&preset=quick"},
            {"label": "Player profiles", "path": "/profiles"},
        ],
        "league_replay_run": [{"label": "League → Real hands", "path": "/league"}],
        "opponents_eval_exploit": [{"label": "Player profiles", "path": "/profiles"}],
        "solve_grid": [
            {"label": "Train value net", "path": "/jobs?task=train_value_net&preset=recommended"},
            {"label": "Train decision AI", "path": "/jobs?task=train_student&preset=recommended"},
        ],
    }
    return steps.get(job_type, [browse, common_import])
