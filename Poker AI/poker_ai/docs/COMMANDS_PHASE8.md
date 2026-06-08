# Phase 8 — CLI commands (style embeddings + exploit)

Living cheat sheet. Detail: [PHASE8_STYLE.md](PHASE8_STYLE.md).

---

## Prerequisites

```powershell
cd D:\Poker AI\poker_ai
.venv\Scripts\Activate.ps1
pip install -e ".[ml]"
python -m poker_ai db migrate
# Ingested hands in data\poker_ai.db (HU nicknames best for style train)
```

---

## Train style encoder (SimCLR)

```powershell
python -m poker_ai train style --epochs 40 --batch-size 256 --device auto -o artifacts/style_encoder/v1
```

Dev cap:

```powershell
python -m poker_ai train style --limit-hands 5000 --epochs 25 --device cpu
```

Check exit metric:

```powershell
type artifacts\style_encoder\v1\metrics.json
# knn_top5_acc should be > 0.6
```

---

## List player_uid from DB

**HU (2-max, stable nicknames):**

```powershell
python -c "import sqlite3; c=sqlite3.connect('data/poker_ai.db');
for r in c.execute('''SELECT MAX(screen_name), COUNT(DISTINCT hand_id), player_uid FROM players p JOIN games g ON g.hand_id=p.hand_id WHERE g.num_players=2 GROUP BY player_uid ORDER BY 2 DESC LIMIT 5'''): print(r)"
```

**6-max** — usually one hand per uid unless OHH/PokerStars nicknames were ingested.

---

## Player profile

```powershell
python -m poker_ai opponents profile <player_uid> --weights artifacts/style_encoder/v1
python -m poker_ai opponents profile <player_uid> --max-hands 500
```

Examples (this repo):

```powershell
python -m poker_ai opponents profile 2b67e56fc91333d73a83c7f24b56fd38dd7ab62a59926356a7c091d16b72d8ef
python -m poker_ai opponents profile fd0ed3c2dcf21be6771b460ccfa7d2eacc0e7bc583f8b0ec9d657ebe11acd8af
```

---

## Exploit vs GTO eval (AIVAT HU)

**Default — Phase 7 `load_best_policy()` router/student:**

```powershell
python -m poker_ai opponents eval-exploit --hands 2000 --seed 42
```

Tune exploit blend (0 = pure GTO, 1 = full nudge):

```powershell
python -m poker_ai opponents eval-exploit --hands 2000 --strength 0.28
python -m poker_ai opponents eval-exploit --hands 2000 --strength 0.15
```

Heuristic baseline only (debug):

```powershell
python -m poker_ai opponents eval-exploit --baseline heuristic --hands 2000
```

Target: **mean delta ≥ +5 BB/100** vs TAG + call_station + maniac.

---

## Tests

```powershell
python -m pytest tests/test_style_phase8.py -q
```

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-21 | Phase 8 commands; `eval-exploit --baseline best`, `--strength`, seat alternation |
