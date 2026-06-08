# HHFormer v1

Self-supervised hand-history encoder (Phase 5).

## Metrics (held-out)

| Metric | Value |
|--------|-------|
| MAP top-1 | 0.822 |
| MCP top-1 | 0.029 |
| SOP AUC | 0.976 |
| Strength probe AUC | 0.777 |

## Training

- Seed: `42`
- Epochs: `50`
- Batch size: `256`
- Parameters: `5,312,574`

No external LLM weights. Trained only on local hand histories.
