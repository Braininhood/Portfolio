# Preflop CFR solve — CLI, web UI, Windows parallel

How **heads-up / 6-max preflop charts** are built, and how the **Tasks UI** relates to the **CLI**.

## Same solver, two entry points

| | **CLI** | **Web (Tasks / Setup)** |
|---|---------|-------------------------|
| Command / job | `python -m poker_ai solve preflop …` | Job type `solve_preflop` |
| Core code | `poker_ai.solver.solve_preflop` | Same |
| Windows + workers > 1 | Runs in main process → **subprocess-per-shard** CFR | API spawns **`preflop_job_isolated`** → same `solve_preflop` → same shards |
| Linux + workers > 1 | **ProcessPool** shards | In-process `solve_preflop` → ProcessPool |
| Progress | stderr `[preflop] …` every ~20s (if logging enabled) | WebSocket + Tasks bar; serve terminal `[job solve_preflop …]` |
| Output | `artifacts/solver/preflop_hu_real.json` (HU + real equity) | Same paths (run `serve` from `poker_ai/`) |

On **Windows**, the web path uses an **isolated child process** so parallel CFR matches the CLI (avoids `ProcessPoolExecutor` deadlocks inside the API worker thread).

## Recommended commands (CLI)

From `poker_ai/` with venv active:

```powershell
# Smoke test (~10 s) — random equity, 4 shards
python -u -m poker_ai solve preflop --positions hu --iters 2000 --equity-mode random --workers 4

# HU recommended — 20k, real equity, 8 workers (~1–3 h typical)
python -u -m poker_ai solve preflop --positions hu --iters 20000 --equity-mode real --workers 8

# HU production — Production bumps HU to ≥50k iters (overnight)
python -u -m poker_ai solve preflop --positions hu --iters 20000 --equity-mode real --workers 8 --production
```

Use **`-u`** (unbuffered). Do **not** pipe stdout through PowerShell `ForEach-Object` during long runs — it buffers output and looks “stuck”.

## Web UI (Tasks page)

1. Set **CPU workers** on the Tasks page (e.g. **8**). `0` = auto (~CPU count − 1).
2. Open **Configure** on **Preflop strategy** → pick preset (**HU quick**, **HU recommended**, **HU production**).
3. Keep **Parallel CFR (Windows)** = **On** (default). **Off** forces a single process (slowest, safest if debugging).
4. Start the job. Watch progress on the card and in the **serve** terminal.

Presets align with CLI flags (`positions`, `iters`, `equity_mode`, `production`, `force_parallel_workers`).

## What happens during a run

### 1. Equity cache (`--equity-mode real`)

- Loads or builds **1,326 combo** equities (2000 MC samples by default).
- Cache file: `poker_ai/artifacts/solver/cache/combo_equity_vs_uniform_n2000.npy`
- **First build** can take **20–60+ minutes**; later runs load in **seconds** (no new file activity).
- Progress: `Building preflop equity table…` → `Equity table ready`

### 2. Parallel CFR (workers > 1)

- Splits iterations across **N subprocess shards** on Windows (N = worker count).
- Example: 20,000 iters, 8 workers → **2,500 iters/shard**.
- Progress stays near **7%** until the **first shard finishes**, then jumps (heartbeat every ~20s: `0/8 shards done (8 running)`).
- **Merging** regret tables → **96%** → writes JSON at **100%**.

### 3. Output

| Format | Equity | Default file |
|--------|--------|----------------|
| HU | real | `artifacts/solver/preflop_hu_real.json` |
| HU | random | `artifacts/solver/preflop_hu.json` |
| 6-max | (config) | `artifacts/solver/preflop_cfr.json` |
| 8-max | production | `artifacts/solver/preflop_8max.json` |
| 9-max | production | `artifacts/solver/preflop_9max.json` |
| 10-max | production | `artifacts/solver/preflop_10max.json` |

CLI picks output automatically when `-o` is left at the 6-max default:

```powershell
python -u -m poker_ai solve preflop --positions 9max --production --workers 8
```

## CPU and Task Manager

- **Overall CPU ~15–25%** on a 12-core CPU with 8 shards is normal (average across all logical processors).
- Use **Details** → sort by **CPU** → several **`python.exe`** children should be busy during CFR.
- A **flat** graph means **steady** load, not idle.
- Stop old **`python.exe`** orphans from cancelled runs (Task Manager) before a long solve.

## Production mode

With **`production: true`** (web) or **`--production`** (CLI), HU runs use **at least 50,000** iterations even if you typed 20,000. The UI and logs will say so explicitly.

## Troubleshooting

| Symptom | Likely cause | Action |
|---------|----------------|--------|
| No output for minutes | Equity cache building, or PowerShell pipe buffering | Use plain terminal + `python -u`; check cache folder |
| Stuck at 7%, 0/N shards | Shards still running (real equity is slow) | Wait; check 8× `python.exe` CPU in Details |
| 50k iters when you chose 20k | Production on | Turn Production off or use HU recommended preset |
| Web 0% forever | Old API build or stuck job | Restart `serve`, **Stop** job, re-run; check terminal for `[job …]` lines |
| Alembic spam in terminal | API `serve` reloading / health (fixed in recent builds) | Restart API once; migrations run only at startup |

## Implementation map

| Piece | Path |
|-------|------|
| CLI command | `poker_ai/src/poker_ai/apps/cli/main.py` → `solve preflop` |
| Solve + equity warmup | `poker_ai/src/poker_ai/solver/solve_preflop.py` |
| Windows parallel shards | `poker_ai/src/poker_ai/solver/parallel_cfr.py` |
| Shard worker | `poker_ai/src/poker_ai/solver/preflop_shard_main.py` |
| Web isolated job (Windows) | `poker_ai/src/poker_ai/solver/preflop_job_isolated.py` |
| API job runner | `apps/api/services/job_runner.py` → `_job_solve_preflop` |
| UI presets | `apps/web/src/lib/pipelineTasks.ts` |

## Related docs

- `apps/README.md` — quick start, serve, terminal job logs
- `apps/web/src/lib/paramGuides.ts` — per-field help in Configure dialogs
