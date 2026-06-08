# Phase 5 — HHFormer

Canonical roadmap: [../../doc/ROADMAP.md](../../doc/ROADMAP.md).

## Status (May 2026)

| Area | State |
|------|--------|
| Code + CLI + tests | **Done** |
| Roadmap exit criteria | **Met** (see production `metrics.json` below) |
| `artifacts/hhformer/v1/` | **Trained** on ~31k hands in canonical DB |

### Production metrics (`artifacts/hhformer/v1/metrics.json`)

| Field | Value | Exit target |
|--------|-------|-------------|
| MAP top-1 (val) | **80.5 %** | ≥ 65 % |
| SOP AUC (val) | **0.966** | ≥ 0.80 |
| Strength probe AUC | **0.792** | ≥ 0.55 |
| MCP top-1 | 3.1 % | (informational only) |
| train / val hands | 28,106 / 3,122 | — |
| epochs · batch | 50 · 256 | — |
| device · wall time | cuda · **411 s** | — |
| parameters | 5,312,574 | ~5–10 M |
| seed | 42 | reproducibility |

## What was built

| Module | Role |
|--------|------|
| `features/hhformer_tokens.py` | `ParsedHand` → 128-token sequence |
| `models/hhformer.py` | Pre-LN transformer; MAP / MCP / SOP heads |
| `learn/pretrain_hhformer.py` | Training loop, metrics, safetensors export |
| `learn/dataset.py` | Masking, DataLoader, train/val split |
| `learn/hhformer_inference.py` | Load weights; JSONL embeddings; optional equity |
| `learn/_ml_deps.py` | Lazy `torch` / `safetensors`; `cuda_available()` |

## Commands

```powershell
cd poker_ai
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# GPU (RTX 5070 / 50-series — not default pip torch):
.\scripts\install_torch_cuda.ps1

# Train (after ingest)
python -m poker_ai train hhformer --epochs 50 --batch-size 256 --device cuda --log-every 50

# Export embeddings (+ optional Phase 4 hero equity)
python -m poker_ai features hhformer-embed -o data/processed/hhformer_embeddings.jsonl
python -m poker_ai features hhformer-embed --with-equity -w artifacts/hhformer/v1

# Optional: pretrain immediately after ingest
python -m poker_ai ingest "..\hand" --train-hhformer

python -m pytest tests/test_hhformer_phase5.py -q
```

### Training time (rough)

| Corpus · epochs · batch | CPU | NVIDIA GPU |
|-------------------------|-----|------------|
| ~30k · 50 · 256 | 2–6+ h | **~7–60 min** (observed **~7 min** on RTX 5070 + cu128) |
| ~1M · 50 · 256 | 2–3+ days | ~3–8 h |

Use `--num-workers 0` on Windows if DataLoader pickling fails.

## Artifacts

| File | Purpose |
|------|---------|
| `weights.safetensors` | Model weights |
| `metrics.json` | Full run metadata + validation metrics |
| `MODEL_CARD.md` | Short human summary |

## JSONL embed format

```json
{"hand_id": 123, "embedding": […256 floats…], "hero_strength_class": 84, "hero_equity": 0.62}
```

`hero_equity` only with `--with-equity` (Phase 4: exact on river, MC otherwise).

## Out of scope (later phases)

- FastAPI / dashboard serving
- Deep policy fusion on embeddings (Phase 7–8 student / exploit heads)

## Next

**Phase 6 (done):** CFR/MCCFR preflop + `StackedPolicy` — see [PHASE6_SOLVER.md](PHASE6_SOLVER.md). **Phase 7:** TexasSolver-distilled student on `[CLS]` embeddings.
