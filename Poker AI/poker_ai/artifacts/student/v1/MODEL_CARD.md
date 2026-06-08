# Student policy v1 (Phase 7)

## Summary
Behavioral clone of offline GTO teacher strategies (TexasSolver AGPL or mock equity teacher).

## Training data
- Cache directory: `artifacts\solver_cache`
- Rows: 1129 (val_frac=0.1)
- Teacher backends: {"play_study": 104, "texas": 536, "mock": 488, "monker": 1}

## Metrics (held-out)
- MSE on action frequencies: **0.0178**
- KL (teacher || student): **0.2251**

## License / compliance
**TexasSolver** ([bupticybee/TexasSolver](https://github.com/bupticybee/TexasSolver))
is **AGPL-3.0**.
Rows labeled `backend=texas` are derived from that solver. Redistribution of those
teacher artifacts requires AGPL compliance. The student weights are MIT-licensed code
trained on those labels — document provenance and do not ship TexasSolver binaries
without meeting AGPL obligations.

## Inference
- Target: p99 < 10 ms on CPU (see `tests/test_solver_phase7.py`)
- Runtime: `DistilledPolicy` + frozen HHFormer [CLS]
