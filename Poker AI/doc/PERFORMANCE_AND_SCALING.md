# Performance and scaling — making the pipeline cheap and fast

This document is a **performance playbook** for the codebase as it stands. The bottlenecks today are: (a) a single SQLite file with default settings, (b) per-hand Treys Monte Carlo simulations at `NUM_SIMULATIONS=10000`, (c) 1000 MCCFR+ iterations × 4 streets × every hand, and (d) hard-coded paths that prevent moving compute off `D:\`.

Numbers below assume a mid-range laptop (8-core CPU, 16 GB RAM, NVMe SSD). They are conservative — tune for your hardware.

---

## 1. SQLite — the cheapest 100× win in the repo

The default SQLite journal mode is `DELETE` with `synchronous=FULL`. Switching to **WAL + NORMAL** has been measured at **~33 000 inserts/s vs ~280 inserts/s** in independent benchmarks ([reference](https://travishorn.com/a-hands-on-exploration-of-sqlite-for-production/)) — that is genuinely two orders of magnitude on bulk ingest.

### 1.1 Drop-in `init_connection` helper

Add this to every script (or, better, a shared `db/_connection.py`):

```python
import sqlite3

PRAGMAS = (
    "PRAGMA journal_mode = WAL;",            # concurrent readers, single writer
    "PRAGMA synchronous = NORMAL;",          # safe with WAL, fewer fsyncs
    "PRAGMA temp_store = MEMORY;",           # faster temp ops; switch to 1 (disk) for >50 GB DBs
    "PRAGMA cache_size = -65536;",           # 64 MB page cache
    "PRAGMA mmap_size = 268435456;",         # 256 MB mmap; raise to 512 MB on 32 GB+ machines
    "PRAGMA wal_autocheckpoint = 10000;",    # checkpoint less often during heavy writes
    "PRAGMA foreign_keys = ON;",             # enforce the FKs documented in DATABASE_SCHEMA.md
    "PRAGMA busy_timeout = 30000;",          # 30 s — replaces the ad hoc time.sleep retries
)

def open_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, timeout=30, isolation_level=None)  # autocommit; we BEGIN explicitly
    for stmt in PRAGMAS:
        conn.execute(stmt)
    return conn
```

### 1.2 Batch transactions, not statement-level commits

`poker_hand_analysis.process_all_files_in_batches` already batches at the *file* level but still calls `conn.commit()` inside `insert_into_db` and inside `update_equities_in_db`. Each commit triggers a WAL fsync — about **500 µs–2 ms** apiece on NVMe. With ~6 commits per hand × 19 000 hands ≈ 100 000 fsyncs ≈ **2–4 minutes wasted**.

Use **explicit transactions per batch** instead:

```python
with conn:                       # begins transaction; commits on exit
    for file in batch_files:
        parsed = parse_hand_file(file)
        if parsed:
            _insert_no_commit(conn, parsed)
```

Drop the `conn.commit()` calls inside helpers; let the `with conn:` block be the single commit boundary.

### 1.3 Indexes that pay back immediately

After ingest, run:

```sql
CREATE INDEX IF NOT EXISTS ix_actions_hand_street     ON Actions(hand_id, street);
CREATE INDEX IF NOT EXISTS ix_actions_player_street   ON Actions(player_id, street);
CREATE INDEX IF NOT EXISTS ix_results_hand            ON Results(hand_id);
CREATE INDEX IF NOT EXISTS ix_players_is_hero         ON Players(is_hero);
CREATE INDEX IF NOT EXISTS ix_gto_hand_street         ON GTO_Solutions(hand_id, street);
CREATE INDEX IF NOT EXISTS ix_exploitability_player   ON Exploitability(player_id);
ANALYZE;
```

Without these, `populate_exploitability.py`'s aggregate query on `Players LEFT JOIN Actions LEFT JOIN Results` is `O(N²)` per player; with them it’s `O(N log N)` and ~10× faster on > 5 k hands.

### 1.4 Use `executemany`, not per-row `INSERT`

`insert_into_db` runs one `cursor.execute(...)` per `Actions` row. Switch to:

```python
cursor.executemany(
    "INSERT OR REPLACE INTO Actions (...) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    actions,    # already a list of tuples
)
```

`executemany` is roughly 3× faster than the equivalent loop on Windows + Python 3.11.

### 1.5 SQLite limits and when to upgrade

| Concern | SQLite | When to migrate to PostgreSQL |
|---------|--------|-------------------------------|
| Concurrent writers | 1 | > 1 (e.g. parallel ingest workers writing simultaneously). |
| DB size | Comfortable up to ~200 GB; theoretical 281 TB. | When you’re over ~50 GB and queries get slow even with indexes. |
| Network access | None (single file). | When the dashboard backend is on a different machine than the data. |
| Replication / backup | File copy (use `.backup` for online safety). | When you need point-in-time recovery. |

For this project, SQLite stays viable for **all** development and even small-team production. Reach for Postgres when adding **HM2 Postgres ingest** (future integration; HM2 already runs Postgres) — not required for Phase 6 CFR.

---

## 2. Monte Carlo equity — convergence vs. cost

`calculate_equity_monte_carlo` runs `NUM_SIMULATIONS = 10 000` random rollouts per (street × hand). On a single CPU core that’s ~150 ms per call × 4 streets × 19 000 hands ≈ **3.2 hours** before any parallelism.

### 2.1 How many simulations do you really need?

Standard error of an estimated probability `p` from `n` rollouts is `sqrt(p(1-p)/n)`. Equity values cluster around 0.3–0.7 for live decisions, so worst-case `p(1-p) = 0.25`.

| `num_simulations` | 1-σ on equity | 2-σ (95 % CI) |
|-------------------|---------------|---------------|
| 1 000 | ±0.0158 | ±0.032 |
| 5 000 | ±0.0071 | ±0.014 |
| 10 000 | ±0.005 | ±0.010 |
| 50 000 | ±0.0022 | ±0.004 |

**Ingest needs `n=2000` at most** for downstream metrics. Keep `n=10 000+` only when the equity number is the *headline* of a UI element. Make this configurable:

```python
NUM_SIMULATIONS_INGEST = int(os.environ.get("POKER_AI_MC_INGEST", "2000"))
NUM_SIMULATIONS_DASHBOARD = int(os.environ.get("POKER_AI_MC_DASHBOARD", "20000"))
```

### 2.2 Cache cards instead of re-creating decks

Inside the inner loop, `Deck()` is reconstructed each iteration and `deck.cards.remove(card)` is a Python list `.remove` (`O(n)`). Build the deck **once** outside the loop and copy:

```python
import random
TEMPLATE = [Card.new(r+s) for r in "23456789TJQKA" for s in "shdc"]

def mc_equity(known_cards, ...):
    pool = [c for c in TEMPLATE if c not in known_cards]
    for _ in range(N):
        random.shuffle(pool)
        # take the first k cards as runout/villain hole cards
```

Empirical speed-up: ~2–3× on the same `n`.

### 2.3 Vectorize with numpy / move to a fast evaluator

For 100 k+ hand databases, Treys / Deuces become the bottleneck. Options:

- [`pokerkit`](https://github.com/uoftcprg/pokerkit) — modern Python card library; not strictly faster than Treys for evaluation, but better-maintained.
- [`phevaluator`](https://github.com/HenryRLee/PokerHandEvaluator) — C++ 7-card evaluator with Python bindings. Roughly **5–10×** faster than Treys for raw 7-card evals.
- A custom **CUDA evaluator** (Pluribus’ team and `TexasSolverGPU` use this) — only worth it if you are doing hundreds of millions of rollouts.

For this repo: **picking ONE library** (Treys *or* Deuces, see [PRODUCT_SPEC.md](PRODUCT_SPEC.md) Phase 2) is more important than absolute speed.

### 2.4 Parallelize at the hand level

`process_all_files_in_batches` is embarrassingly parallel. Use a process pool:

```python
from concurrent.futures import ProcessPoolExecutor
import os

def parse_one(path):
    return parse_hand_file(path)

def ingest_parallel(files, db_path, workers=os.cpu_count() // 2):
    with ProcessPoolExecutor(max_workers=workers) as pool:
        parsed_iter = pool.map(parse_one, files, chunksize=64)
        with open_db(db_path) as conn:
            with conn:
                for parsed in parsed_iter:
                    if parsed:
                        _insert_no_commit(conn, parsed)
```

> SQLite supports **one writer at a time**. Parse in workers, write in the main process — that is enough to saturate one NVMe.

---

## 3. MCCFR+ iterations — heuristic loop sized vs cost

`process_hand` runs `1000` MCCFR iterations × ~4 streets per hand. Per iteration the heuristic does ~4 SQL queries on `Hands`, `Actions`, `Players`. On 19 000 hands that is **~300 million SQL hits** and dominates total runtime.

### 3.1 Cache once, iterate in memory

Refactor `_calculate_counterfactual_value` to receive a **pre-fetched dict** for the hand:

```python
def fetch_hand_context(conn, hand_id):
    cur = conn.cursor()
    cur.execute("SELECT hero_cards, board_cards FROM Hands WHERE hand_id=?", (hand_id,))
    cards = cur.fetchone()
    cur.execute("""SELECT street, action_type, amount, pot_before, pot_after, player_id
                   FROM Actions WHERE hand_id=? ORDER BY action_id""", (hand_id,))
    actions = cur.fetchall()
    return {"cards": cards, "actions": actions}

# in process_hand:
ctx = fetch_hand_context(self.conn, hand_id)
for _ in range(N):
    self.mccfr.run_iteration_from_ctx(ctx, street, num_players)
```

This trades 4 000 SQL queries per hand for ~3, and is enough to cut wall-clock by **5×** on its own.

### 3.2 Profile before tuning

```bash
python -m cProfile -o gto.prof db/GTO_Solver_Data.py
python -m snakeviz gto.prof
```

The expected hot spots are `_calculate_counterfactual_value` (DB I/O), `Card.new` (Deuces parsing), and `evaluator.evaluate`. Move `Card.new` calls outside the inner loop and cache the parsed `hero_hand`/`board` per hand.

### 3.3 Iteration count vs. convergence

The current 1000 iterations are arbitrary. For a *real* CFR you would track **exploitability** vs iteration; for the heuristic, you can:

- Track **strategy stability**: stop when `||strategy_t - strategy_{t-1}||_∞ < 1e-3`.
- Decay `exploration_rate` faster (`0.999` → 0.37 after 1000 iters; `0.99` → 0.0001 after 1000).
- Add a CLI flag: `--mccfr-iterations 500` so testing runs quickly.

---

## 4. Neural networks — costs and sizing

### 4.1 Today’s nets

| Module | Architecture | Approx params | Training cost |
|--------|--------------|---------------|---------------|
| `AdvancedPokerNN` (`populate_exploitability.py`) | 10 → 128 → 128 → 1, dropout 0.3 | ~17 k | Trivial; CPU < 30 s @ 1 000 epochs. |
| `DecisionQualityNN` (`Bot_Performance.py`) | 3 → 64 → 32 → 3 | ~2.5 k | Trivial. |
| `StrategyAdjustmentNN` (`Live_Adjustments.py`) | 8 → 32 → 16 → 2 | ~1 k | Trivial. |
| `ImprovedExploitabilityNN` (`Opponent_Profiles.py`) | 6 → 64 → 32 → 16 → 1 | ~3 k | Trivial. |
| `MonteCarloCFR.regret_network` (`Bot_Performance.py`) | 50 → 256 → 256 → 4 | ~80 k | Per-episode update; 10 000 episodes ≈ several minutes. |

**Conclusion:** these are all CPU-comfortable. GPU is unnecessary until you scale to Deep CFR–style nets (2–10 M params) — see [GTO_THEORY_AND_SOLVERS.md](GTO_THEORY_AND_SOLVERS.md).

### 4.2 What to do with the “training inside ingest” pattern

Today every `populate_*` script trains a model at the bottom of the same module that ingests SQL. Best practice splits this into:

```
ingest -> SQLite        # idempotent
features -> tensors      # cached parquet/npz
train -> artifacts/v.pt  # versioned weights
predict -> SQLite        # cheap forward pass
```

This is also Phase 7 of [ROADMAP.md](ROADMAP.md). The win:

- Re-ingest doesn’t retrain.
- Re-train doesn’t re-ingest.
- Predictions can be **batched** (PyTorch is much faster on > 1024 rows than on N=1).

### 4.3 Inference batching

`predict_decision_quality(features)` is called **per row**. Replace with a batched call once at the end:

```python
features = torch.tensor(np.stack(all_feature_rows), dtype=torch.float32)
preds = model(features).argmax(dim=1).cpu().numpy()
```

On 19 000 rows this drops from minutes to milliseconds.

---

## 5. Selenium scraper — politeness and reliability

`convert/hand_parser.py` requests `freepokertools.holdemmanager.com` every 0.5 s. For ~37 000 IDs × 0.5 s = **5 hours minimum**. Notes:

- **Rate limiting.** 0.5 s is reasonable but consider exponential back-off on errors and randomized jitter (`random.uniform(0.4, 0.8)`) so the request pattern is less bot-like — keeps the upstream service from blocking your IP.
- **Headless Chrome.** Add `--headless=new --disable-gpu --no-sandbox` to halve memory.
- **Cache 404s.** Persist a `seen_404.txt` so re-runs don’t hit dead IDs again.
- **Compliance.** Only scrape *your own* hand viewer URLs; see [SECURITY_AND_COMPLIANCE.md](SECURITY_AND_COMPLIANCE.md) §5.

---

## 6. Memory profile cheatsheet

`tracemalloc` is the easiest way to find leaks:

```python
import tracemalloc; tracemalloc.start()
main()
snap = tracemalloc.take_snapshot()
for stat in snap.statistics("lineno")[:10]:
    print(stat)
```

Common offenders today:

- `MCCFRPlus.regret` is a `defaultdict(lambda: np.zeros(5))`. Every unique info-set keeps a 40-byte numpy array forever. With per-hand-keyed info-sets (`f"{hand_id}_..."`), the dict grows linearly with hands — **purge or persist between hands** or just **not key by `hand_id`** (see [GTO_THEORY_AND_SOLVERS.md](GTO_THEORY_AND_SOLVERS.md) §3).
- `Bot_Performance.PokerEnv.state_size = 50` — fine.
- Treys `Deck()` is recreated per Monte Carlo iteration — addressed in §2.2.

---

## 7. End-to-end performance budget

For the existing dataset (≈19 000 staged hands, ≈500 KB each):

| Stage | Today (default settings) | Target with the changes above |
|-------|--------------------------|-------------------------------|
| `convert/filter.py` | I/O bound; ~30 s | ~30 s (already efficient). |
| `convert/converter.py` | ~60 s | ~60 s. |
| `db/poker_hand_analysis.py` (ingest + MC equity) | ~3.5 hours | **~20 minutes** (WAL + executemany + parallel parse + `n=2000` MC). |
| `db/GTO_Solver_Data.py` | ~6 hours | **~40 minutes** (ctx caching + iter cap + 5-action info-sets without `hand_id`). |
| `db/populate_exploitability.py` | ~3 minutes | ~30 s (indexes + batched inference). |
| Other downstream scripts | < 1 minute each | < 10 s each. |

If you cannot drive total wall-clock under an hour after these tweaks, profile before guessing — the answer is almost always either an `INSERT` per row or an `O(N²)` SQL aggregate.

---

## 8. References

- [SQLite WAL documentation](https://sqlite.org/wal.html)
- [SQLite PRAGMA statements](https://sqlite.org/pragma.html)
- [Hands-on SQLite for production (33k inserts/s benchmark)](https://travishorn.com/a-hands-on-exploration-of-sqlite-for-production/)
- [PHEvaluator — fast 7-card evaluator](https://github.com/HenryRLee/PokerHandEvaluator)
- [PokerKit — modern Python card library](https://github.com/uoftcprg/pokerkit)
- Treys: <https://github.com/ihendley/treys> · Deuces: <https://github.com/worldveil/deuces>

See also: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) (indexes), [TESTING_AND_QA.md](TESTING_AND_QA.md) (timing budgets), [OBSERVABILITY.md](OBSERVABILITY.md) (production monitoring).
