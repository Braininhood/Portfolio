# Observability — logging, metrics, drift, and variance reduction

Once the pipeline is running on real data and a service is exposed, you stop debugging by `print` and start looking at **dashboards** and **alerts**. This document is the practical observability plan for this codebase, covering:

1. Structured logs in scripts and FastAPI.
2. Operational metrics (Prometheus / Grafana).
3. Data and model drift detection.
4. **AIVAT** for low-variance evaluation of policies.
5. Model registry and audit logs.

It complements [TESTING_AND_QA.md](TESTING_AND_QA.md) (pre-prod) and [SECURITY_AND_COMPLIANCE.md](SECURITY_AND_COMPLIANCE.md) (audit).

---

## 1. Logging — switch to structured early

### 1.1 Adopt JSON logs

The current scripts use `logging.basicConfig(... format='%(asctime)s - %(levelname)s - %(message)s')`. That’s fine for one-shot runs; for anything you want to query later, log structured JSON.

[`structlog`](https://www.structlog.org/) is the lightest tool that does this well:

```python
import logging, structlog

logging.basicConfig(level=logging.INFO, format="%(message)s")
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)
log = structlog.get_logger()

log.info("hand_ingested", hand_id=hand_id, num_actions=len(actions), elapsed_ms=int(dt*1000))
```

A line then looks like:

```json
{"event":"hand_ingested","hand_id":37900207,"num_actions":14,"elapsed_ms":273,"timestamp":"2026-05-10T18:32:14Z","level":"info"}
```

…which `jq`, `grep`, Loki, or Splunk can all index.

### 1.2 Required fields per event

Every log line should carry **at least**:

| Field | Why |
|-------|-----|
| `event` | Stable name (`hand_ingested`, `gto_solved`, `nn_predicted`, `db_locked_retry`). |
| `hand_id` (if applicable) | Trace a single hand through every stage. |
| `module` | `convert.filter`, `db.populate_exploitability`, … |
| `version` | Schema or model version for forensic replay. |
| `elapsed_ms` | Cheap performance budget tracker. |
| `outcome` | `ok` / `error` / `skipped`. |

### 1.3 Correlation IDs in FastAPI

Add a middleware that stamps every request with a UUID:

```python
import uuid, structlog
from starlette.middleware.base import BaseHTTPMiddleware

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        cid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        structlog.contextvars.bind_contextvars(request_id=cid)
        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.clear_contextvars()
        response.headers["X-Request-ID"] = cid
        return response
```

Now a single user click can be followed across `apps/api` → DB → simulator without grep gymnastics.

### 1.4 Log levels

| Level | When |
|-------|------|
| `debug` | Per-iteration MCCFR+ values (off by default in prod). |
| `info` | One per hand, per HTTP request, per training epoch milestone. |
| `warning` | Recoverable parser issues, DB lock retries, NaN replaced with 0, schema drift. |
| `error` | Insertion rollback, NN training divergence, FK violation. |
| `critical` | DB unreachable, secret missing, model file corrupt. |

---

## 2. Operational metrics — Prometheus + Grafana

For long-running services (the FastAPI dashboard, an ingest daemon, a sim worker) ship metrics on `/metrics`:

```python
from fastapi import FastAPI
from prometheus_client import Counter, Histogram, make_asgi_app

app = FastAPI()
app.mount("/metrics", make_asgi_app())

HAND_INGEST_TOTAL = Counter("hand_ingest_total", "Hands ingested", ["status"])
HAND_INGEST_DURATION = Histogram("hand_ingest_seconds", "Hand ingest latency")

@app.post("/api/ingest")
async def ingest(...):
    with HAND_INGEST_DURATION.time():
        ...
        HAND_INGEST_TOTAL.labels(status="ok").inc()
```

Useful built-in metrics for this stack:

| Metric | Type | Purpose |
|--------|------|---------|
| `hand_ingest_total{status}` | Counter | `ok`, `parse_error`, `db_error`. |
| `hand_ingest_seconds` | Histogram | Latency budget alarms. |
| `mc_equity_simulations_total` | Counter | Monitor MC cost. |
| `gto_iterations_total{street}` | Counter | Per-street MCCFR progress. |
| `nn_predict_seconds{model}` | Histogram | Watch for accidental N=1 inference loops. |
| `db_lock_retries_total` | Counter | Detect WAL contention regressions. |
| `policy_decisions_total{profile,action}` | Counter | Verify profile diversity in sims. |

Grafana dashboard → 1 row per stage, RED method (Rate, Errors, Duration).

---

## 3. Data drift — when your pool changes under you

Population statistics on poker rooms shift over time (game-pool gets tougher, rake changes, new layouts). Models trained on last year’s VPIP distribution drift silently if you don’t monitor.

### 3.1 What to monitor

| Signal | Source | Alert when… |
|--------|--------|-------------|
| Pool VPIP / PFR distribution | `Exploitability` rollups by week | KS-statistic vs baseline > 0.1 |
| Stake mix | `Games.stakes` | New stakes appear / disappear |
| Average stack-to-pot ratio at flop | computed from `Actions` | Mean shift > 0.5 SPR |
| Model prediction distribution | `Bot_Performance.decision_quality` per session | Class imbalance shifts > 10 % |
| Multi-way vs HU decision mix | League sim / `play_hands` by `n_active` | Share of 3+ player pots shifts > 15 % vs baseline |
| Equity-bucket histogram on river | `Results.river_equity` | Mass shifts > 0.1 KL |

A simple drift check:

```python
from scipy.stats import ks_2samp
ref = baseline_vpip_array
cur = recent_vpip_array
stat, p = ks_2samp(ref, cur)
if stat > 0.1:
    log.warning("vpip_drift", ks_stat=stat, p_value=p)
```

### 3.2 Tooling (shipped May 2026 — W8)

**Implemented today:**

| Component | Path | Web |
|---|---|---|
| Feature drift reports | `poker_ai/observability/drift.py` | `/drift` — list + iframe HTML |
| BOCPD changepoints | `poker_ai/learn/changepoint.py` | `/drift` — opponent alerts panel |
| Model registry | `poker_ai/learn/model_registry.py` | `/models` — promote / rollback; `GET /models/{name}/promotion-gates` (drift + league AIVAT + canary) |

Reports are written to `data/drift/drift_<YYYY-MM-DD>.html`. Run via CLI
(`python -m poker_ai observability drift`) or **`POST /drift/run`** from the Drift page.
Implementation uses stdlib JSONL feature profiles (no pandas/Evidently dependency).

**Optional upgrades (not required):**

- [Evidently AI](https://docs.evidentlyai.com/) — richer HTML reports from a DataFrame.
- [Great Expectations](https://greatexpectations.io/) — declarative “expectations” per ingest.
- [whylogs](https://whylogs.readthedocs.io/) — lightweight statistical profiles.

### 3.3 Where drift detection sits in the pipeline

```
ingest  →  features  →  observability/drift.py  →  data/drift/*.html  →  /drift page
                              ↓
                    learn/changepoint.py  →  data/drift/changepoints.json  →  /drift + (Profiles Day 36)
```

---

## 4. Variance-reduced evaluation — AIVAT

### 4.1 Why AIVAT matters for this project

Comparing two policies on a fixed sample of hands is dominated by **luck variance** (cards) and **decision variance** (sampling within a strategy). AIVAT (Burch et al., 2018) reduces both:

- Adjusts every chance event by its baseline value, conditional on info-set.
- Adjusts every player decision by the strategy’s expectation.
- The result is **provably unbiased** but with up to **85 % lower standard deviation** than the naive estimator.

> The 2026 [GTO Wizard Benchmark](https://arxiv.org/abs/2603.23660) uses AIVAT to require ~10× fewer hands than naive Monte Carlo for the same statistical significance.

### 4.2 Pseudocode adapted to this repo

For each hand and each player action that could be sampled differently:

```
naive_value          = actual_net_result_in_BB
chance_correction    = sum_over_chance_nodes(baseline(node) - E[baseline(node) | known cards])
strategy_correction  = sum_over_decisions(  baseline(action_taken) - E[baseline | strategy ])
aivat_value          = naive_value - chance_correction - strategy_correction
```

Where `baseline(...)` is **any** value estimator — the simplest is the all-in equity at the river, which you already store in `Results.river_equity`.

A Python sketch:

```python
def aivat_estimate(hand_records, policy, baseline_fn):
    """Return mean and stderr of policy value with AIVAT corrections."""
    samples = []
    for h in hand_records:
        naive = h.net_result_bb
        cc = sum(baseline_fn(c.node) - c.expected_baseline for c in h.chance_events)
        sc = sum(baseline_fn(a.node) - sum(p*baseline_fn(a.node, alt) for alt, p in policy.dist(a.info_set).items()) for a in h.decisions)
        samples.append(naive - cc - sc)
    return np.mean(samples), np.std(samples) / sqrt(len(samples))
```

Add a column `Bot_Performance.aivat_adjusted_net` once a policy interface lands.

### 4.3 Alternatives when AIVAT is overkill

- **All-in EV (PT4-style)** — replace the river runout with equity probability. Simpler than AIVAT, only handles chance variance, not decision variance. Good as a first iteration.
- **Bootstrap CIs** on `bb/100` — non-parametric, easy, informative.

---

## 5. Model registry and lineage

Once you have more than two trained models in flight:

```
artifacts/
  exploitability_nn/
    v2026-05-10/
      weights.pt
      MODEL_CARD.md
      metrics.json     # train loss, val loss, canary scores
      input_features.json
      training_data.json  # source DB hash + row counts + filter
  decision_quality_nn/
    v2026-05-12/
      ...
```

`metrics.json` is the source of truth for promotions:

```json
{
  "model": "exploitability_nn",
  "version": "2026-05-10",
  "git_commit": "a1b2c3d",
  "train_loss": 0.342,
  "val_loss": 0.371,
  "canary_player_score": 0.512,
  "training_data": {"db_hash": "sha256:...", "rows": 18920}
}
```

Tools that automate this if you outgrow flat files:

- [MLflow Tracking](https://mlflow.org/docs/latest/tracking.html) — local SQLite-backed registry; runs anywhere.
- [DVC](https://dvc.org/) — git for large model files + dataset versioning.
- [Weights & Biases](https://wandb.ai/) — hosted; richer experiment UI.

---

## 6. Audit logs (compliance crossover)

For anything user-facing (FastAPI, future API key access, sim sessions touching personal data):

```sql
CREATE TABLE IF NOT EXISTS Audit_Log (
  audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts DATETIME DEFAULT CURRENT_TIMESTAMP,
  user_id TEXT,
  action TEXT,             -- 'login', 'export', 'erasure_request', 'profile_update'
  target_type TEXT,        -- 'hand', 'player_uid', 'profile'
  target_id TEXT,
  request_id TEXT,         -- ties back to log correlation IDs
  ip TEXT,
  user_agent TEXT,
  notes TEXT
);
```

Append-only, never `UPDATE`. Index on `user_id, ts` for SAR (subject-access requests, see [SECURITY_AND_COMPLIANCE.md](SECURITY_AND_COMPLIANCE.md) §2.3).

---

## 7. Health check that actually means something

Many services ship a `/health` that just returns `{"status": "ok"}`. Make yours useful:

```python
@app.get("/api/health")
async def health(db = Depends(get_db)):
    # 1. DB ping
    db.execute("SELECT 1").fetchone()
    # 2. Schema version
    sv = db.execute("SELECT MAX(version) FROM _schema_meta").fetchone()[0]
    # 3. Stale data check
    last_hand = db.execute("SELECT MAX(hand_id) FROM Games").fetchone()[0]
    # 4. Latest model
    return {
        "status": "ok",
        "schema_version": sv,
        "last_hand_id": last_hand,
        "exploitability_model": Path("artifacts/exploitability_nn/CURRENT").read_text(),
    }
```

A failing dependency immediately bubbles up to the dashboard and to your alerting rules.

---

## 8. Alerting rules — the bare minimum

Configure (Prometheus Alertmanager, Grafana, or even a simple cron + email):

| Rule | Trigger |
|------|---------|
| **Ingest stalled** | `increase(hand_ingest_total[15m]) == 0` while a worker is supposedly running. |
| **Latency budget breach** | `histogram_quantile(0.95, hand_ingest_seconds) > 0.5` for 5 min. |
| **Model loss diverged** | Last training run’s `val_loss` more than 2× baseline. |
| **Drift detected** | KS-statistic on weekly VPIP distribution > 0.1. |
| **DB lock storm** | `rate(db_lock_retries_total[5m]) > 1`. |
| **Secrets in repo** | gitleaks finding in CI. |

---

## 9. Reading order

1. Wire JSON logging (1 hour change).
2. Add `/health` and `/metrics` (when FastAPI lands).
3. Stand up Grafana + Prometheus locally.
4. Drift reports — **done (W8):** `observability/drift.py` + `/drift` page; optional Evidently upgrade later.
5. Plug AIVAT into `Bot_Performance` as soon as a `Policy` interface exists.
6. Wire MLflow once you have ≥ 3 models in flight.

---

## 10. References

- AIVAT — [Burch et al., AAAI 2018 (PDF)](https://poker.cs.ualberta.ca/publications/aaai18-burch-aivat.pdf)
- GTO Wizard Benchmark using AIVAT — [arXiv:2603.23660](https://arxiv.org/abs/2603.23660)
- Evidently AI — <https://docs.evidentlyai.com/>
- Great Expectations — <https://greatexpectations.io/>
- whylogs — <https://whylogs.readthedocs.io/>
- structlog — <https://www.structlog.org/>
- prometheus_client (Python) — <https://github.com/prometheus/client_python>
- MLflow Tracking — <https://mlflow.org/docs/latest/tracking.html>

See also: [PERFORMANCE_AND_SCALING.md](PERFORMANCE_AND_SCALING.md), [TESTING_AND_QA.md](TESTING_AND_QA.md), [SECURITY_AND_COMPLIANCE.md](SECURITY_AND_COMPLIANCE.md).
