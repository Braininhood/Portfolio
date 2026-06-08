# HHFormer v2 (solver fine-tuned)

Self-supervised hand-history encoder (Phase 5).

## Metrics (held-out)

| Metric | Value |
|--------|-------|
| MAP top-1 | 0.704 |
| MCP top-1 | 0.012 |
| SOP AUC | 0.961 |
| Strength probe AUC | 0.854 |

## Training

- Seed: `42`
- Epochs: `8`
- Batch size: `128`
- Parameters: `5,312,574`

No external LLM weights. Trained only on local hand histories.
