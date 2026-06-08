# Poker AI — Product datasheet (Phase 12 / W9)

## Intended use

Local-first **offline** analysis of **your own** hand histories: import, replay, equity, drills, league evaluation, and optional play-vs-AI study. Not for real-time assistance on third-party real-money poker clients.

## Data

| Item | Detail |
|------|--------|
| Training data | User-imported hand histories only (SQLite store — any supported format/path you choose) |
| External APIs | None required at runtime |
| Cloud LLMs | Not used |
| Bundled corpora | None shipped with the product; optional `../hand/` trees are operator-supplied only |

## Models (when trained)

| Artifact | Role | Model card |
|----------|------|------------|
| HHFormer v1 | Self-supervised hand-history encoder | `artifacts/hhformer/v1/MODEL_CARD.md` |
| Student HU | Distilled postflop policy (HU) | `artifacts/student/v1/MODEL_CARD.md` |
| Student multi-way | Distilled postflop policy (3+) | `artifacts/student/multiway_v1/MODEL_CARD.md` |
| Preflop CFR (HU) | Tabular HU preflop chart | `artifacts/solver/preflop_hu/MODEL_CARD.md` |
| Preflop CFR (6-max) | Tabular 6-max preflop chart | `artifacts/solver/preflop_6max/MODEL_CARD.md` |
| Style encoder v1 | Opponent tendency embeddings | `artifacts/style_encoder/v1/MODEL_CARD.md` |
| Solver cache | Postflop teacher spots | `artifacts/solver_cache/MODEL_CARD.md` |

View in the dashboard: **Models → Model card**, or `GET /models/{name}/card`.

## Limitations

- Multi-table tournaments (ICM, payouts, table balancing) are planned for **v2** — see [ROADMAP.md](ROADMAP.md#v2-backlog--next-version-todo).
- Solver quality depends on installed TexasSolver or mock teacher.
- Equity and decide latency depend on CPU/GPU; smoke tests encode baseline budgets on your machine.

## Compliance

- See [SECURITY_AND_COMPLIANCE.md](SECURITY_AND_COMPLIANCE.md) for GDPR, EU AI Act documentation hooks.
- Third-party licenses: [LICENSES/inventory.json](../LICENSES/inventory.json) and **Licenses** (`/licenses`) in the dashboard.
- Footer badges: **Offline · No external AI · Owned data only** (from `GET /compliance`).

## Verification

1. **System status → Run smoke test** (or `GET /health/smoke`) on an air-gapped machine before production install.
2. Production serve: `npm run build` in `apps/web` with `VITE_API_BASE_URL=""`, then `python -m poker_ai serve --no-web`.
3. Installers: `poker_ai/scripts/install.ps1` (Windows) or `poker_ai/scripts/install.sh` (Linux/macOS).
