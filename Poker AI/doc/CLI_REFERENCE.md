# Command Line Reference

Complete guide to all Poker AI terminal commands. Run from the `poker_ai` folder.

## Starting the System

### serve — Start the Dashboard

```bash
python -m poker_ai serve
```

**What it does:** Starts the web server so you can use the dashboard in your browser.

**When to use:** Every time you want to use Poker AI.

**After starting:**
- **Dashboard:** http://127.0.0.1:5173 (main interface)
- **API:** http://127.0.0.1:8000 (backend, Swagger docs at `/docs`)

**Options:**
- `--api-port 8000` — Change the API port (default: 8000, falls back to 8765)
- `--no-web` — Run API only without starting the React development server

**Example:**
```bash
python -m poker_ai serve --api-port 8765
```

---

## Importing Hands

### ingest — Import Hand Histories

```bash
python -m poker_ai ingest "path/to/hands"
```

**What it does:** Reads hand history files and stores them in your database.

**When to use:** After downloading hands from your poker client.

**Supported formats:**
- PokerStars text files
- OHH JSON files
- PHH/PHHS archives

**Options:**
- `--max-hands 1000` — Only import first N hands (for testing)
- `--workers 4` — Use multiple CPU cores for faster import
- `--train-hhformer` — Also train the AI model after import

**Examples:**
```bash
# Import all hands from a folder
python -m poker_ai ingest "C:\Users\Me\PokerStars\HandHistory"

# Import only 500 hands (for testing)
python -m poker_ai ingest "C:\hands" --max-hands 500

# Import using 8 CPU cores
python -m poker_ai ingest "C:\hands" --workers 8
```

---

## Database Commands

### db migrate — Update Database Structure

```bash
python -m poker_ai db migrate
```

**What it does:** Updates the database schema to the latest version.

**When to use:** After updating Poker AI to a new version.

### db status — Check Database

```bash
python -m poker_ai db status
```

**What it does:** Shows the current database version.

**When to use:** To verify your database is up to date.

---

## Feature Building

### features build — Prepare Training Data

```bash
python -m poker_ai features build
```

**What it does:** Converts your imported hands into a format the AI can learn from.

**When to use:** After importing hands, before training models.

**Options:**
- `--since 2024-01-01` — Only process hands from this date
- `--output features.jsonl` — Save to specific file
- `--workers 4` — Use multiple CPU cores
- `--blueprint-full` — Include all extended data (recommended)

**Example:**
```bash
python -m poker_ai features build --blueprint-full --workers 4
```

### features hhformer-embed — Export AI Embeddings

```bash
python -m poker_ai features hhformer-embed
```

**What it does:** Creates numerical representations of each hand for advanced analysis.

**When to use:** After training HHFormer, for research purposes.

---

## Training AI Models

### train hhformer — Train the Foundation Model

```bash
python -m poker_ai train hhformer
```

**What it does:** Trains the core AI that understands poker hands.

**When to use:** After building features, first time setup.

**Time required:** 5-30 minutes depending on data size and hardware.

**Options:**
- `--epochs 50` — Training iterations (default: 50)
- `--device cuda` — Use GPU (or `cpu` for CPU only)
- `--batch-size 256` — Hands per training batch

**Example (GPU):**
```bash
python -m poker_ai train hhformer --device cuda --epochs 50
```

### train student — Train the Decision Model

```bash
python -m poker_ai train student
```

**What it does:** Trains the model that makes actual playing decisions.

**When to use:** After running solver cache and training HHFormer.

**Options:**
- `--epochs 30` — Training iterations
- `--device cuda` — Use GPU

### train style — Train Opponent Recognition

```bash
python -m poker_ai train style
```

**What it does:** Trains the model that recognizes different player types.

**When to use:** After importing many hands from different players.

### train multiway-student — Train Multi-Player Decisions

```bash
python -m poker_ai train multiway-student
```

**What it does:** Trains decisions for 3+ player pots.

**When to use:** After training the heads-up student.

### train cql — Train Offline Reinforcement Learning

```bash
python -m poker_ai train cql
```

**What it does:** Advanced training using Conservative Q-Learning.

**When to use:** Research/experimentation only.

### train value-net — Train Value Prediction

```bash
python -m poker_ai train value-net
```

**What it does:** Trains a model to predict hand values.

### train decision-quality — Train Decision Auditor

```bash
python -m poker_ai train decision-quality
```

**What it does:** Trains a model to rate the quality of decisions.

---

## Solver Commands

### solve preflop — Generate Preflop Charts

```bash
python -m poker_ai solve preflop --positions 6max
```

**What it does:** Calculates game-theory-optimal preflop strategies.

**When to use:** To generate opening ranges and 3-bet charts.

**Options:**
- `--positions hu` — Heads-up (2 players)
- `--positions 6max` — 6-max tables
- `--positions 9max` — Full ring (9 players)
- `--iters 20000` — Calculation iterations (more = more accurate)
- `--workers 4` — Use multiple CPU cores
- `--production` — High-quality mode (takes longer)
- `--equity-mode real` — Use actual equity calculations

**Examples:**
```bash
# Quick heads-up chart
python -m poker_ai solve preflop --positions hu --iters 10000

# Production 6-max chart
python -m poker_ai solve preflop --positions 6max --production --workers 8

# Full ring chart
python -m poker_ai solve preflop --positions 9max --iters 25000 --workers 4
```

### solve kuhn — Test the Solver

```bash
python -m poker_ai solve kuhn
```

**What it does:** Runs a test on a simple poker game to verify the solver works.

**When to use:** To check if your installation is correct.

### solve grid — Build Teacher Cache

```bash
python -m poker_ai solve grid --n-spots 1000
```

**What it does:** Solves many postflop situations to create training data.

**When to use:** Before training the student model (overnight task).

**Options:**
- `--n-spots 1000` — Number of situations to solve
- `--backend mock` — Use simplified solver (fast, for testing)
- `--backend texas` — Use TexasSolver (accurate, requires install)

### solve validate-student — Check Model Quality

```bash
python -m poker_ai solve validate-student
```

**What it does:** Tests if the trained student meets quality standards.

**When to use:** After training to verify quality.

### solve install-texas — Install TexasSolver

```bash
python -m poker_ai solve install-texas
```

**What it does:** Downloads and installs the TexasSolver engine.

**When to use:** One-time setup for accurate postflop solutions.

### solve texas-status — Check TexasSolver

```bash
python -m poker_ai solve texas-status
```

**What it does:** Shows if TexasSolver is installed and working.

---

## Equity Calculator

### equity spot — Calculate Hand Equity

```bash
python -m poker_ai equity spot AhKd --villain random
```

**What it does:** Calculates your winning chances against a range.

**Options:**
- `--villain "AA,KK,QQ"` — Specific range
- `--villain random` — All possible hands
- `--board "Qh Jc Ts"` — Specific board

**Examples:**
```bash
# AK vs random preflop
python -m poker_ai equity spot AhKd --villain random

# AK vs premium range on a flop
python -m poker_ai equity spot AhKd --villain "AA,KK,QQ,AK" --board "Qh Jc Ts"
```

### equity backfill — Add Equity to Database

```bash
python -m poker_ai equity backfill
```

**What it does:** Calculates and stores equity for all hands in your database.

**When to use:** After importing hands, for detailed analysis.

---

## League Commands

### league run — Run Bot Tournament

```bash
python -m poker_ai league run --until-hours 1
```

**What it does:** Runs AI agents against each other to evaluate performance.

**When to use:** To test if training improved the AI.

**Options:**
- `--until-hours 6` — Run for N hours
- `--hands-per-matchup 200` — Hands per match
- `--table-sizes 2,6,9` — Table formats to test
- `--workers 4` — Parallel matches

### league leaderboard — Show Rankings

```bash
python -m poker_ai league leaderboard
```

**What it does:** Displays how each AI agent is performing.

### league run-replay — Test on Real Hands

```bash
python -m poker_ai league run-replay --limit 500
```

**What it does:** Tests AI decisions against your actual imported hands.

### league train-exploiters — Train Counter-Strategies

```bash
python -m poker_ai league train-exploiters
```

**What it does:** Trains agents to exploit weaknesses in other agents.

---

## Opponent Analysis

### opponents profile — Analyze a Player

```bash
python -m poker_ai opponents profile "player_uid_here"
```

**What it does:** Shows statistics and tendencies for a specific player.

**What you get:**
- VPIP (how often they play hands)
- PFR (how often they raise)
- Aggression factor
- Style classification

### opponents eval-exploit — Test Exploitation

```bash
python -m poker_ai opponents eval-exploit
```

**What it does:** Tests if the AI can profitably exploit different player types.

---

## Model Management

### models list — Show All Models

```bash
python -m poker_ai models list
```

**What it does:** Lists all trained AI models and their versions.

### models gates — Check Upgrade Requirements

```bash
python -m poker_ai models gates student_hu
```

**What it does:** Shows if a model can be safely upgraded.

### models promote — Upgrade Model Version

```bash
python -m poker_ai models promote hhformer --confirm
```

**What it does:** Sets a new model version as the active one.

**Options:**
- `--confirm` — Required to actually make the change
- `--skip-gates` — Override safety checks (not recommended)

### models rollback — Revert to Previous Version

```bash
python -m poker_ai models rollback student_hu
```

**What it does:** Reverts to the previous model version.

---

## Pipeline Commands

### pipeline run — Run Everything

```bash
python -m poker_ai pipeline run --corpus "path/to/hands"
```

**What it does:** Runs the complete pipeline: import → features → train → solve.

**Options:**
- `--skip-ingest` — Don't re-import hands
- `--skip-features` — Don't rebuild features
- `--skip-train` — Don't retrain models
- `--solver-grid` — Also build teacher cache
- `--train-student` — Also train student

---

## Policy Benchmarks

### policy bench — Test Decision Speed

```bash
python -m poker_ai policy bench
```

**What it does:** Measures how fast the AI can make decisions.

**What you see:**
- p50 = median response time
- p99 = worst-case response time
- Target: p99 under 30ms

---

## Evaluation Commands

### eval aivat-audit — Statistical Validation

```bash
python -m poker_ai eval aivat-audit --hands 1000
```

**What it does:** Runs statistical tests to validate the AI's performance.

---

## Common Workflows

### First Time Setup

```bash
# 1. Start the server (leave running)
python -m poker_ai serve

# 2. In browser, use Setup page to:
#    - Import hands
#    - Build features
#    - Train HHFormer
#    - Solve preflop
```

### Daily Use

```bash
# Start the server
python -m poker_ai serve
# Open http://127.0.0.1:5173
```

### After Importing New Hands

```bash
python -m poker_ai features build --blueprint-full
python -m poker_ai equity backfill
```

### Training a Better AI (Overnight)

```bash
python -m poker_ai solve grid --n-spots 2000 --backend texas
python -m poker_ai train student --epochs 30
python -m poker_ai league run --until-hours 6
```

---

## Environment Variables

Set these in a `.env` file in the `poker_ai` folder:

| Variable | What It Does |
|----------|--------------|
| `POKER_AI_DATABASE_URL` | Change database location |
| `POKER_AI_NUM_WORKERS` | Default parallel workers |
| `POKER_AI_TEXAS_SOLVER_EXE` | Custom TexasSolver path |

---

## Troubleshooting

### "No module named poker_ai"

You're running the wrong Python. Use:
```bash
python -m uv run python -m poker_ai serve
```

### "Port already in use"

Another program is using port 8000. Either:
- Close the other program
- Use a different port: `python -m poker_ai serve --api-port 8765`

### Solver stuck at low percentage

This is normal for large solves. Check Task Manager — you should see multiple Python processes working. Be patient (can take 1-3 hours for production solves).

### GPU not detected

Install CUDA-enabled PyTorch:
```bash
# Windows
.\scripts\install_torch_cuda.ps1
```
