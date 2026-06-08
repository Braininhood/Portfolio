# Phase 4 — equity module (complete)

Canonical roadmap: [doc/ROADMAP.md](../../doc/ROADMAP.md) (Phase 4 + implementation snapshot).  
Web calculator: [doc/WEB_IMPLEMENTATION_GUIDE.md](../../doc/WEB_IMPLEMENTATION_GUIDE.md) Phase W5.

## What shipped

| Piece | Role |
|-------|------|
| `equity/mc.py` | Seedable Monte Carlo (preflop, fallback) |
| `equity/exact.py` | Postflop exact RvR via runout rank cache |
| `equity/range_vs_range.py` | Public API, histograms, FFT convolution |
| `equity/cache.py` | Optional parquet + xxhash |
| `equity/engine.py` | `EquityEngine` for live warm + query |
| `equity/backfill.py` | MC → `results.*_equity` in SQLite |
| `equity/live.py` | Runtime hero equity for HUD/play |
| `equity/breakdown.py` | Win/tie/loss breakdown (exact + MC) — **W5** |
| `equity/range_notation.py` | Parse `TT+`, `AKs`, `AhKd`, `random` — **W5** |
| `equity/spot_insight.py` | Plain-English draw/pair hints — **W5** |
| `equity/multiway.py` | Hero vs *n* uniform opponents (Phase 7b play) |
| `tests/test_equity_phase4.py` | Library exit criteria |
| `tests/test_equity_backfill.py` | DB backfill |
| `scripts/bench_equity.py` | Latency benchmark |

## Web (Phase W5) — shipped ✅

| Piece | Role |
|-------|------|
| `apps/api/routers/equity.py` | `POST /equity` |
| `apps/api/services/equity_service.py` | Card/range parse, breakdown, insight |
| `apps/web/src/pages/EquityPage.tsx` | User-facing calculator |
| `apps/web/src/components/CardPicker.tsx` | 4×13 card grid |

## CLI (June 2026) — shipped ✅

```powershell
python -m poker_ai equity spot --hero "Ah Kd" --board "Qs Jh 2h" --villain random
python -m poker_ai equity backfill
python -m poker_ai equity backfill --limit 500 --refresh
```

Setup wizard step **Backfill hand equities** and Jobs task `equity_backfill` call the same job runner path.

## Integration map — who uses equity today

| Consumer | Uses Phase 4? | Entry point |
|----------|---------------|-------------|
| **Preflop CFR solve** | Yes | `solver/preflop_equity.py` — `--equity-mode real` |
| **Mock GTO teacher** | Yes | `solver/bridge/mock_teacher.py` |
| **HHFormer embed (optional)** | Yes | `learn/hhformer_inference.py` — `--with-equity` |
| **HU postflop play (fallback)** | Yes | `policy/postflop_equity.py` → `EquityEngine` |
| **Multi-way postflop play** | Yes | `policy/multiway_postflop.py` → `hero_equity_vs_n_uniform` |
| **Distilled student fallback** | Yes | `DistilledPolicy` → `PostflopEquityPolicy` when student missing |
| **W5 `/equity` UI** | Yes | `equity_service` → `equity_breakdown` |
| **SQLite `results.*_equity`** | Yes (after backfill) | `equity/backfill.py` |
| **Replayer / Drill** | Yes | API replay + drill services read DB or live MC |
| **Play / decide HUD** | Yes | `include_equity` on `POST /decide` |

## Ops

After import, run a full backfill once (or from Setup):

```powershell
cd poker_ai
python -m poker_ai equity backfill
```

Use `--limit N` for a slice; `--refresh` to recompute existing rows.

## Quick commands

```powershell
cd poker_ai
$env:POKER_AI_SKIP_PERF = "1"
$env:POKER_AI_EQUITY_WORKERS = "1"
.\.venv\Scripts\python.exe -m pytest tests/test_equity_phase4.py tests/test_equity_backfill.py -q
.\.venv\Scripts\python.exe scripts/bench_equity.py
```
