# Testing and QA — making the pipeline trustworthy

Today the repo is **executable scripts on a single workstation**: there are no automated tests, ingest is destructive, and bugs in the parser silently propagate to every downstream NN. This document is a **concrete pytest blueprint** the next contributor can implement in a day, plus longer-horizon ideas.

It assumes Phase 0–1 of [ROADMAP.md](ROADMAP.md) (config + non-destructive ingest) is at least in flight. Even before that, the unit tests below are useful for the parsing logic.

---

## 1. Test pyramid for this codebase

```
                  /\
                 /  \   1. End-to-end (slow, few)
                /----\
               /      \  2. Integration: ingest -> SQLite -> downstream
              /--------\
             /          \ 3. Unit: parsing, equity, regret, metrics
            /------------\
```

| Layer | Owner module(s) | Speed budget | What it proves |
|-------|-----------------|--------------|----------------|
| Unit | `convert/*`, `db/poker_hand_analysis.parse_hand_file`, `MCCFRPlus`, NN forward pass | ≤ 50 ms each | Pure logic — no SQLite, no torch training. |
| Integration | `db/*` ingest + queries | ≤ 5 s each | Migrations + ingest + a single GTO row. |
| End-to-end | Full ETL on 2–3 golden hands + FastAPI smoke | ≤ 30 s | Pipeline doesn’t bit-rot. |

Aim for **CI < 60 s** so contributors run it locally before pushing.

---

## 2. Recommended layout

```
tests/
  conftest.py                # shared fixtures (tmp DB, fake config, sample lines)
  fixtures/
    hands/
      6max_hu_allin.txt
      8handed_multiway.txt
      9handed_full_ring.txt
      malformed_no_stakes.txt
    golden/
      6max_hu_allin.expected.json
      ...
  unit/
    test_parser_header.py
    test_parser_actions.py
    test_equity_treys.py
    test_mccfr_regret_math.py
    test_metrics_formulas.py
  integration/
    test_ingest_and_query.py
    test_gto_solutions_idempotent.py
    test_exploitability_endtoend.py
  e2e/
    test_full_pipeline_smoke.py
    test_api_health.py            # once apps/api exists
```

---

## 3. Shared fixtures — `conftest.py`

```python
# tests/conftest.py
import os
import sqlite3
from pathlib import Path
import pytest

FIX = Path(__file__).parent / "fixtures"

@pytest.fixture
def tmp_db_path(tmp_path):
    """An empty, isolated SQLite file. Never points at production poker.db."""
    return tmp_path / "test_poker.db"

@pytest.fixture
def empty_db(tmp_db_path):
    """Schema applied, no data."""
    from db.poker_hand_analysis import create_tables, DB_PATH  # noqa: F401
    # Patch DB_PATH for this test (until config refactor lands).
    import db.poker_hand_analysis as pha
    pha.DB_PATH = str(tmp_db_path)
    create_tables()
    return tmp_db_path

@pytest.fixture
def golden_hand_text():
    return (FIX / "hands" / "6max_hu_allin.txt").read_text(encoding="utf-8")

@pytest.fixture
def populated_db(empty_db, golden_hand_text, tmp_path):
    from db.poker_hand_analysis import parse_hand_file, insert_into_db, evaluator
    hand_file = tmp_path / "hand_99999999.txt"
    hand_file.write_text(golden_hand_text, encoding="utf-8")
    parsed = parse_hand_file(str(hand_file))
    with sqlite3.connect(empty_db, timeout=30) as conn:
        insert_into_db(conn, parsed)
    return empty_db
```

> Once the config refactor lands, replace the `pha.DB_PATH = ...` monkey-patch with `monkeypatch.setenv("POKER_AI_DATABASE_URL", f"sqlite:///{tmp_db_path}")`.

---

## 4. Unit tests — surgical and fast

### 4.1 Parser invariants

`tests/unit/test_parser_header.py`

```python
import re
from db.poker_hand_analysis import parse_hand_file

def test_first_line_extracts_stakes_blinds_and_num_players(tmp_path):
    txt = "$0.05/$0.10, NLH, 6 Players\n\nHero (BTN): $10 (100 bb)\n"
    f = tmp_path / "hand_42.txt"; f.write_text(txt)
    parsed = parse_hand_file(str(f))
    assert parsed["hand_id"] == 42
    assert parsed["stakes"] == "0.05/0.1"
    assert parsed["game_type"] == "NLH"
    assert parsed["num_players"] == 6

def test_invalid_stakes_returns_none(tmp_path):
    f = tmp_path / "hand_43.txt"; f.write_text("nonsense\nHero (BTN): $1 (10 bb)\n")
    assert parse_hand_file(str(f)) is None
```

`tests/unit/test_parser_actions.py` — covers each branch of the action regex (Fold, Call, Raise, Bet, Check, all-in), the “N folds” shorthand, and the `Hero` → position substitution. Run with at least:

- 6-max heads-up to all-in (your `hand/5/hand_37900207.txt` is a perfect golden file).
- 9-handed full ring with two raises and a multi-way fold-out.
- A line containing `2 folds` between actions (use to confirm fold expansion logic).

### 4.2 Equity and Treys/Deuces conversions

```python
from db.poker_hand_analysis import calculate_equity_monte_carlo, evaluator

def test_aces_vs_kings_preflop_equity_within_bounds(monkeypatch):
    players = [{"hero_cards": "Ah Ac"}, {"hero_cards": "Kh Kc"}]
    eq = calculate_equity_monte_carlo(players, [], evaluator, num_simulations=2000)
    # Iconic AA vs KK heads-up = 81–82% / 18–19%. Generous bounds for MC noise.
    assert 0.78 < list(eq.values())[0] < 0.86
```

> Use **deterministic seeds** (`numpy.random.seed`, `random.seed`) inside the test by monkeypatching at module load — the function in this repo doesn’t expose a seed; consider adding `seed: int | None = None`.

### 4.3 Regret math (`MCCFRPlus`)

```python
import numpy as np
from db.GTO_Solver_Data import MCCFRPlus

def test_regret_matching_returns_uniform_when_all_regrets_negative():
    m = MCCFRPlus()
    info = "test_set"
    m.regret[info] = np.array([-1, -2, -3, -4, -5], dtype=float)
    s = m.get_strategy(info)
    assert np.allclose(s.sum(), 1.0)
    assert np.all(s > 0)  # uniform-ish, exploration ensures non-zero
```

### 4.4 Metric formulas — pin them down

The formulas in `populate_exploitability.py` diverge from canonical poker tracker definitions ([POKER_METRICS_GLOSSARY.md](POKER_METRICS_GLOSSARY.md)). Lock in the *current* values with characterization tests so any future fix is visible:

```python
def test_current_vpip_formula_is_action_frequency_not_canonical(populated_db):
    import sqlite3
    conn = sqlite3.connect(populated_db)
    # Run the exact SQL from populate_exploitability.py and assert the value.
    # If we later fix the formula, this test will fail loudly.
```

---

## 5. Golden-hand testing

For each of 6-max, 8-handed and 9-handed hands, commit:

- A **redacted** `*.txt` (replace nicknames with `Player1`, … to dodge GDPR — see [SECURITY_AND_COMPLIANCE.md](SECURITY_AND_COMPLIANCE.md)).
- A `*.expected.json` describing the parser output: `players[]`, `actions[]`, `pot_sizes`, `hero_cards`, `board_cards`, etc.

Test:

```python
import json
from db.poker_hand_analysis import parse_hand_file

@pytest.mark.parametrize("name", [
    "6max_hu_allin",
    "8handed_multiway",
    "9handed_full_ring",
])
def test_parser_matches_golden(tmp_path, name):
    src = (FIX / "hands" / f"{name}.txt").read_text()
    hand_file = tmp_path / f"hand_99999999.txt"
    hand_file.write_text(src)
    parsed = parse_hand_file(str(hand_file))
    expected = json.loads((FIX / "golden" / f"{name}.expected.json").read_text())
    # Compare structurally, not field-order-sensitively
    assert parsed["num_players"] == expected["num_players"]
    assert len(parsed["actions"]) == expected["action_count"]
    assert parsed["hero_cards"] == expected["hero_cards"]
```

This single suite catches **80 %** of regressions when the parser is touched.

---

## 6. Integration — DB and downstream NNs

### 6.1 Idempotent ingest

```python
def test_double_ingest_does_not_duplicate_hands(empty_db, populated_db, golden_hand_text, tmp_path):
    """Re-running the ingest must not multiply rows."""
    from db.poker_hand_analysis import parse_hand_file, insert_into_db
    f = tmp_path / "hand_99999999.txt"; f.write_text(golden_hand_text)
    parsed = parse_hand_file(str(f))
    import sqlite3
    with sqlite3.connect(empty_db) as conn:
        insert_into_db(conn, parsed)  # first time
        insert_into_db(conn, parsed)  # second time
        n_actions = conn.execute("SELECT COUNT(*) FROM Actions WHERE hand_id=99999999").fetchone()[0]
    assert n_actions == parsed_action_count  # not 2x parsed_action_count
```

> This **fails today** because `Actions` uses `INSERT OR REPLACE` keyed on `action_id` (autoincrement), not on `(hand_id, player_id, street, action_type, amount)`. Make the test xfail with a clear marker until Phase 1 is done — it documents the known bug.

### 6.2 GTO row presence

```python
def test_gto_solutions_populated_after_process_hand(populated_db):
    from db.GTO_Solver_Data import GTOSolverData
    gsd = GTOSolverData(); gsd.create_tables(); gsd.process_hand(99999999)
    import sqlite3
    rows = sqlite3.connect(populated_db).execute(
        "SELECT COUNT(*) FROM GTO_Solutions WHERE hand_id=99999999"
    ).fetchone()[0]
    assert rows > 0
```

### 6.3 NN forward pass shape

For each model class (`AdvancedPokerNN`, `DecisionQualityNN`, `StrategyAdjustmentNN`, `ImprovedExploitabilityNN`, `MonteCarloCFR`):

```python
import torch
from db.populate_exploitability import AdvancedPokerNN

def test_advanced_poker_nn_forward_shapes():
    m = AdvancedPokerNN(input_size=10)
    x = torch.zeros(7, 10)
    y = m(x)
    assert y.shape == (7, 1)
```

These prevent silent breakage when input feature counts are bumped.

---

## 7. End-to-end smoke

```python
def test_full_pipeline_smoke(tmp_path, monkeypatch):
    # 1. Stage 3 hands in tmp dir
    # 2. Run filter -> convert -> converter (via subprocess if hard-coded paths persist)
    # 3. Run db.poker_hand_analysis.main()
    # 4. Run db.GTO_Solver_Data.process_hand for each hand_id
    # 5. Run db.populate_exploitability (skip NN training: monkeypatch epochs=2)
    # 6. Assert minimum row counts in each table
    ...
```

For models, **monkeypatch training epochs to 2** in tests — the goal is shape correctness, not convergence:

```python
def test_exploitability_pipeline_runs_quickly(monkeypatch, populated_db):
    import db.populate_exploitability as pe
    monkeypatch.setattr(pe, "train_model", lambda *a, **k: None)
    # invoke main / module in a controlled way
```

---

## 8. Property-based testing

Install `hypothesis` and add property tests where formulas matter:

```python
from hypothesis import given, strategies as st

@given(st.floats(0, 1), st.floats(0, 1))
def test_vpip_minus_pfr_is_nonnegative_when_pfr_subset_of_vpip(vpip, pfr):
    """If we eventually fix VPIP/PFR semantics: pfr <= vpip."""
    pfr = min(pfr, vpip)
    assert vpip - pfr >= 0
```

Equity properties are a goldmine:

- Hero equity + sum(opponent equities) ≈ 1.0 ± Monte-Carlo tolerance.
- Equity is monotone non-decreasing along a fixed line where hero never folds.

---

## 9. API contract tests (once `apps/api/` exists)

**Shipped (June 2026):** `poker_ai/tests/test_phase10_api.py` (health, decide, jobs), `poker_ai/tests/test_phase12_w9_api.py` (smoke, licenses, compliance, model cards). Tests load the app via `load_api_app.py` (no static `import main`).

Use `pytest + httpx.AsyncClient` against the FastAPI app instance:

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_endpoint_reports_schema_version(api_app):
    async with AsyncClient(app=api_app, base_url="http://test") as ac:
        r = await ac.get("/api/health")
    assert r.status_code == 200
    assert r.json()["schema_version"] >= 1
```

For OpenAPI fuzzing, add [Schemathesis](https://schemathesis.readthedocs.io/) — it generates test cases automatically from the FastAPI-generated `openapi.json`.

---

## 10. Regression for ML models

Whenever you change features or hyperparameters in `populate_exploitability.py`, `Bot_Performance.py`, `Live_Adjustments.py`, or `Opponent_Profiles.py`, write to `tests/regression/<model>_v<N>.json`:

```json
{
  "input_size": 10,
  "training_loss_after_2_epochs": 1.247,
  "predicted_score_for_canary_player": 0.512
}
```

Then assert the new code reproduces the canary within tolerance:

```python
def test_exploitability_canary_score(canary_features, baseline_json):
    pred = predict_batch(model, canary_features)
    assert abs(pred[0] - baseline_json["predicted_score_for_canary_player"]) < 1e-3
```

This is what the AI/ML community calls a **canary test** — cheap, catches accidental input-shape and weight-init regressions.

---

## 11. CI configuration sketch (GitHub Actions)

```yaml
name: tests
on: [push, pull_request]
jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest -q --maxfail=1 --durations=20
```

`requirements-dev.txt` should pin: `pytest`, `pytest-asyncio`, `pytest-cov`, `hypothesis`, `httpx`, `schemathesis`.

---

## 12. Linting and static analysis

| Tool | Why | One-time setup |
|------|-----|----------------|
| **ruff** | Fast linting + isort + many bugbear rules. | `ruff check . --fix` |
| **mypy** (or **pyright**) | Catch the silent dict/float drift in `GTO_Solutions.expected_value`. | Start with `--strict` only in `db/` and progressively expand. |
| **pre-commit** | Run ruff + mypy on `git commit`. | `pre-commit install`. |
| **bandit** | Security lint — flags `subprocess shell=True`, hard-coded passwords. | Before deploying any API. |

---

## 13. Mutating the data lake safely

When testing destructive scripts (`populate_exploitability.py`, `Bankroll_Tracking.py`, …):

1. **Never** import them in tests as side-effectful modules. Refactor each into `def main(): …` first; tests then call `main()` against the temp DB.
2. Keep a `tests/fixtures/poker_canary.db` (≤ 1 MB) as a snapshot of the schema with 5–10 hands; use `sqlite3 src.db ".backup canary.db"` to regenerate.
3. Use `pytest --maxfail=1 -p no:cacheprovider` in CI to avoid stale `.pytest_cache` SQLite inside the workspace.

---

## 14. Checklist before any release

- [ ] All unit + integration tests pass (`pytest -q`).
- [ ] Smoke test imports 3 golden hands and computes ≥ 1 row per downstream table.
- [ ] No script writes to a *prod* DB without a `--reset` or `--db` flag.
- [ ] OpenAPI changes reviewed (Schemathesis).
- [ ] Model canaries within tolerance.
- [ ] `CHANGELOG.md` updated with schema version bump if any migration is shipped.

See also: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) §7 (migrations), [PERFORMANCE_AND_SCALING.md](PERFORMANCE_AND_SCALING.md) (timing budgets), [OBSERVABILITY.md](OBSERVABILITY.md) (production health beyond tests).
