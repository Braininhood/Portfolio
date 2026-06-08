"""Automated promotion gates — drift, league AIVAT, candidate metrics, canary (Phase 11)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from poker_ai.learn.model_registry import REGISTRY, SOLVER_PINNED, get_model_info


@dataclass(frozen=True, slots=True)
class GateCheck:
    gate_id: str
    label: str
    passed: bool
    detail: str
    required: bool = True


@dataclass(frozen=True, slots=True)
class PromotionGateReport:
    model_name: str
    checks: tuple[GateCheck, ...]
    can_promote: bool
    blocking: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "can_promote": self.can_promote,
            "blocking": list(self.blocking),
            "checks": [
                {
                    "gate_id": c.gate_id,
                    "label": c.label,
                    "passed": c.passed,
                    "detail": c.detail,
                    "required": c.required,
                }
                for c in self.checks
            ],
        }


def _league_report_path() -> Path:
    raw = os.environ.get("POKER_AI_LEAGUE_REPORT", "reports/league_leaderboard.json")
    return Path(raw)


def _drift_ok() -> GateCheck:
    from poker_ai.observability.drift import list_drift_reports

    reports = list_drift_reports()
    if not reports:
        return GateCheck(
            "drift",
            "Drift report",
            False,
            "No drift report — run POST /drift/run or `poker_ai drift run` first.",
        )
    latest = reports[0]
    status = (latest.status or "").lower()
    ok = status in ("green", "ok", "pass", "warning", "warn")
    return GateCheck(
        "drift",
        "Drift report",
        ok,
        f"latest={latest.date} status={latest.status} flagged={latest.features_flagged}",
    )


def _league_aivat_ok(model_name: str) -> GateCheck:
    path = _league_report_path()
    if not path.is_file():
        return GateCheck(
            "league_aivat",
            "League AIVAT",
            False,
            f"No league report at {path} — run `poker_ai league run` first.",
            required=model_name.startswith("student"),
        )
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return GateCheck("league_aivat", "League AIVAT", False, str(exc))

    pval = float(raw.get("promotion_pvalue") or 1.0)
    promoted = bool(raw.get("promoted"))
    hands = int(raw.get("hands_played") or 0)
    main_row = next(
        (r for r in raw.get("leaderboard") or [] if r.get("agent_id") == "main_agent"),
        None,
    )
    aivat_bb = float(main_row.get("aivat_bb_per_100") or 0.0) if main_row else 0.0
    alpha = float(os.environ.get("POKER_AI_PROMOTION_ALPHA", "0.05"))
    min_hands = int(os.environ.get("POKER_AI_PROMOTION_MIN_HANDS", "1000"))
    ok = (
        hands >= min_hands
        and pval < alpha
        and aivat_bb > 0
    ) or promoted
    return GateCheck(
        "league_aivat",
        "League AIVAT",
        ok,
        f"hands={hands} aivat_bb100={aivat_bb:.2f} p={pval:.4f} promoted_flag={promoted}",
        required=model_name.startswith("student"),
    )


def _candidate_metrics_ok(model_name: str, info: Any) -> GateCheck:
    cand = info.candidate_metrics or {}
    if not info.candidate_version:
        return GateCheck("candidate", "Candidate version", False, "No candidate artifact.")
    if model_name.startswith("student"):
        mse = cand.get("mse_val")
        if mse is None:
            return GateCheck(
                "candidate",
                "Student MSE",
                True,
                "No mse_val in metrics.json — optional; run solve validate-student.",
                required=False,
            )
        ok = float(mse) <= 0.05
        return GateCheck("candidate", "Student MSE", ok, f"mse_val={float(mse):.4f} (limit 0.05)")
    if model_name == "hhformer":
        acc = cand.get("map_accuracy")
        if acc is None:
            return GateCheck("candidate", "HHFormer MAP", True, "No map_accuracy in metrics.", required=False)
        ok = float(acc) >= 0.5
        return GateCheck("candidate", "HHFormer MAP", ok, f"map_accuracy={float(acc):.3f}")
    return GateCheck("candidate", "Candidate version", True, f"candidate={info.candidate_version}")


def _canary_artifacts_ok(model_name: str) -> GateCheck:
    if model_name in SOLVER_PINNED:
        root = REGISTRY[model_name]
        pinned = root / SOLVER_PINNED[model_name]
        ok = pinned.is_file()
        return GateCheck("canary", "Artifact on disk", ok, str(pinned.resolve()))
    root = REGISTRY.get(model_name, Path(f"artifacts/{model_name}"))
    if model_name == "student_hu":
        root = Path("artifacts/student")
    cand = get_model_info(model_name).candidate_version
    if not cand:
        return GateCheck("canary", "Artifact on disk", False, "No candidate dir.")
    cand_dir = root / cand
    weights = list(cand_dir.glob("*.safetensors")) + list(cand_dir.glob("*.pt"))
    ok = cand_dir.is_dir() and bool(weights or (cand_dir / "metrics.json").is_file())
    return GateCheck("canary", "Artifact on disk", ok, str(cand_dir.resolve()))


def evaluate_promotion_gates(model_name: str, *, skip_drift: bool = False) -> PromotionGateReport:
    """Full gate report for registry promote (API + CLI)."""
    info = get_model_info(model_name)
    checks: list[GateCheck] = []

    if not info.candidate_version and model_name not in SOLVER_PINNED:
        checks.append(
            GateCheck("registry", "Registry candidate", False, "No promotable candidate.")
        )
    else:
        checks.append(
            GateCheck(
                "registry",
                "Registry candidate",
                True,
                f"candidate={info.candidate_version or 'n/a'}",
            )
        )

    if not skip_drift:
        checks.append(_drift_ok())
    checks.append(_league_aivat_ok(model_name))
    checks.append(_candidate_metrics_ok(model_name, info))
    checks.append(_canary_artifacts_ok(model_name))

    blocking = tuple(c.gate_id for c in checks if c.required and not c.passed)
    can = not blocking and (info.candidate_version is not None or model_name in SOLVER_PINNED)
    return PromotionGateReport(
        model_name=model_name,
        checks=tuple(checks),
        can_promote=can,
        blocking=blocking,
    )
