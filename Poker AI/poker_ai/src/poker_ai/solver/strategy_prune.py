"""Drop low-mass info sets from exported CFR tables."""

from __future__ import annotations

import numpy as np


def prune_strategy(
    raw: dict[str, np.ndarray],
    *,
    min_mass: float = 5.0,
) -> dict[str, np.ndarray]:
    """Keep nodes whose average-strategy denominator mass exceeds ``min_mass``."""
    if min_mass <= 0:
        return raw
    out: dict[str, np.ndarray] = {}
    for key, sigma in raw.items():
        if float(np.asarray(sigma).sum()) >= min_mass * 0.01:
            out[key] = sigma
    return out
