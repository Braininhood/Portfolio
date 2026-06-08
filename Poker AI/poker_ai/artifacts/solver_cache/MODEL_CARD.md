# Solver cache (postflop teacher spots)

Offline **GTO teacher labels** for distilling the student policy (Phase 7). Each entry is one solved (or mock-labeled) spot.

## Layout

- Index: `artifacts/solver_cache/index.jsonl` (one JSON object per spot)
- Spot files: `artifacts/solver_cache/spots/<cache_key>.json`
- Action frequencies + metadata per board / stack / pot line

## Provenance

| Backend | Meaning |
|---------|---------|
| `texas` | Labels from **TexasSolver** (AGPL-3.0) |
| `mock` | Heuristic / equity teacher when solver binary unavailable |
| `monker` | Optional Monker export (when configured) |

Check `backend` field per row in `index.jsonl`.

## Training use

- Student HU / multi-way models read this cache during `train_student`.
- Typical scale: hundreds of spots for a first run; grow via **Tasks → solve grid**.

## License / compliance

**TexasSolver** ([bupticybee/TexasSolver](https://github.com/bupticybee/TexasSolver)) is **AGPL-3.0**.

- Rows with `backend=texas` are derived from that solver.
- Do not redistribute TexasSolver binaries without meeting AGPL obligations.
- Student weights are separate artifacts — document teacher provenance in the student `MODEL_CARD.md`.

## Limitations

- Cache coverage is spotty by design (discrete boards/lines), not full-game equilibrium.
- Mock rows are for pipeline testing, not production GTO claims.
- Stale cache after rule/ante changes — rebuild grid after format changes.
