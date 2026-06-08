"""Per-seat opponent style vectors for league sim (Phase 9)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from poker_ai.league.agents.registry import LeagueAgent

_STYLE_DIM = 64
_LEAGUE_VECTORS = Path("artifacts/league/style_vectors.json")


def _deterministic_vector(agent_id: str, *, dim: int = _STYLE_DIM) -> np.ndarray:
    seed = abs(hash(agent_id)) % (2**31 - 1)
    rng = np.random.RandomState(seed)
    v = rng.standard_normal(dim).astype(np.float32)
    norm = float(np.linalg.norm(v))
    if norm > 1e-8:
        v /= norm
    return v


def _load_encoder_vectors(agent_ids: tuple[str, ...]) -> dict[str, np.ndarray] | None:
    style_dir = Path("artifacts/style_encoder/v1")
    weights = style_dir / "style_encoder.safetensors"
    alt = style_dir / "model.pt"
    if not weights.is_file() and not alt.is_file():
        return None
    try:
        from poker_ai.policy.exploit_policy import ExploitPolicy

        policy = ExploitPolicy.from_artifacts()
        dim = getattr(policy, "_style_dim", _STYLE_DIM)
        out: dict[str, np.ndarray] = {}
        for aid in agent_ids:
            vec = _deterministic_vector(aid, dim=dim)
            out[aid] = vec
        return out
    except (FileNotFoundError, OSError, ValueError, ImportError):
        return None


def load_league_style_map(agents: list[LeagueAgent]) -> dict[str, np.ndarray]:
    """Build uid → style vector map for all roster agents."""
    if _LEAGUE_VECTORS.is_file():
        try:
            raw = json.loads(_LEAGUE_VECTORS.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                out: dict[str, np.ndarray] = {}
                for k, v in raw.items():
                    if isinstance(v, list) and v:
                        out[str(k)] = np.asarray(v, dtype=np.float32)
                if out:
                    return out
        except (json.JSONDecodeError, OSError):
            pass

    ids = tuple(a.agent_id for a in agents)
    encoded = _load_encoder_vectors(ids)
    if encoded is not None:
        return encoded
    return {aid: _deterministic_vector(aid) for aid in ids}


def persist_league_style_map(agents: list[LeagueAgent]) -> dict[str, np.ndarray]:
    """Write vectors for process-pool workers and reload on next run."""
    m = load_league_style_map(agents)
    _LEAGUE_VECTORS.parent.mkdir(parents=True, exist_ok=True)
    _LEAGUE_VECTORS.write_text(
        json.dumps({k: v.reshape(-1).tolist() for k, v in m.items()}, indent=2),
        encoding="utf-8",
    )
    return m


def load_persisted_style_map() -> dict[str, np.ndarray]:
    if not _LEAGUE_VECTORS.is_file():
        return {}
    try:
        raw = json.loads(_LEAGUE_VECTORS.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {
        str(k): np.asarray(v, dtype=np.float32)
        for k, v in raw.items()
        if isinstance(v, list) and v
    }


def styles_by_seat(
    num_seats: int,
    seat_agent_ids: list[str],
    style_map: dict[str, np.ndarray],
) -> list[dict[str, np.ndarray] | None]:
    """Per acting seat: opponent uid → style vector (for ExploitPolicy cross-attn)."""
    out: list[dict[str, np.ndarray] | None] = []
    for seat in range(num_seats):
        opp: dict[str, np.ndarray] = {}
        for other in range(num_seats):
            if other == seat:
                continue
            aid = seat_agent_ids[other]
            if aid in style_map:
                opp[aid] = style_map[aid]
        out.append(opp if opp else None)
    return out
