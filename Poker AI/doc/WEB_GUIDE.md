# Web Dashboard Guide

Complete guide to using the Poker AI dashboard. Everything you need to know to analyze your game and train against the AI.

## Getting Started

### Opening the Dashboard

1. Start the server (in terminal):
   ```
   python -m poker_ai serve
   ```

2. Wait for "API ready" message

3. Open your browser to: **http://127.0.0.1:5173**

---

## Setup Page

**URL:** `/setup`

**What it does:** Guides you through initial configuration step-by-step.

### The Steps

| Step | What Happens | Time Required |
|------|--------------|---------------|
| 1. Import Hands | Load your hand histories | 1-5 minutes |
| 2. Build Features | Prepare data for AI | 2-10 minutes |
| 3. Train HHFormer | Train core AI model | 5-30 minutes |
| 4. Solve Preflop | Generate opening ranges | 10-60 minutes |
| 5. Train Student | Train decision AI | 5-15 minutes |

### Status Indicators

- **Green checkmark** — Step completed
- **Orange badge** — Step needs attention
- **Gray** — Waiting for previous step

### Tips

- Complete steps in order
- Don't close the browser during long tasks
- Check the terminal for detailed progress

---

## Import Page

**URL:** `/import`

**What it does:** Loads hand history files from your computer into the database.

### How to Import

1. Click **Browse** or drag files into the upload area
2. Or enter a **folder path** and click **Start Import**
3. Watch the progress bar
4. See the summary when complete

### Supported Formats

| Format | File Type | From |
|--------|-----------|------|
| PokerStars | `.txt` files | PokerStars client |
| Open Hand History | `.json` files | Various tools |
| PHH Archives | `.phh`, `.phhs` | Research databases |

### Import Settings

- **Max hands** — Limit how many hands to import (for testing)
- **Workers** — Use more CPU cores for faster import

### After Importing

Your hands are now in the database. Go to:
- **Setup** → Build Features (to prepare for AI training)
- **Replayer** → View your hands
- **Equity** → Analyze specific situations

---

## Status Page

**URL:** `/status`

**What it does:** Shows the health of your system and all AI components.

### What You See

**System Info:**
- Database status and hand count
- Memory usage
- CPU information

**AI Models:**

| Model | What It Does | Status Meaning |
|-------|--------------|----------------|
| HHFormer | Understands hand patterns | Ready/Not Trained |
| Student HU | Makes heads-up decisions | Ready/Not Trained |
| Student Multiway | Makes 3+ player decisions | Ready/Not Trained |
| Preflop HU | Heads-up opening ranges | Ready/Not Solved |
| Preflop 6-max | 6-max opening ranges | Ready/Not Solved |
| Style Encoder | Recognizes player types | Ready/Not Trained |
| Solver Cache | Postflop solutions | Empty/Has Spots |

### Actions

- **Quick Test** — Verify the model works
- **Configure** — Go to training task

### Tips

- All models should show "Ready" for full functionality
- The status page is your diagnostic center

---

## Tasks Page (Jobs)

**URL:** `/jobs`

**What it does:** Run AI training tasks and long-running operations.

### Available Tasks

**Preparation:**
| Task | What It Does | When to Use |
|------|--------------|-------------|
| Prepare hands | Convert hands for AI | After importing |
| Export Parquet | Save features for backup | For data export |
| Validate schema | Check feature format | Troubleshooting |

**Training:**
| Task | What It Does | When to Use |
|------|--------------|-------------|
| Train HHFormer | Train core AI | First setup |
| Train Student | Train decision AI | After solver cache |
| Train Multiway | Train 3+ player AI | After student |
| Train Style | Train opponent recognition | After many hands |
| Train CQL | Advanced learning | Research |

**Solvers:**
| Task | What It Does | When to Use |
|------|--------------|-------------|
| Solve Preflop HU | Calculate HU ranges | First setup |
| Solve Preflop 6-max | Calculate 6-max ranges | First setup |
| Build Solver Cache | Solve postflop spots | Before training student |
| Kuhn Test | Verify solver works | Troubleshooting |

**Analysis:**
| Task | What It Does | When to Use |
|------|--------------|-------------|
| Equity Backfill | Calculate all equities | After import |
| Run League | Test AI performance | After training |
| AIVAT Audit | Statistical validation | Quality check |
| Policy Benchmark | Test decision speed | Performance check |

### Running a Task

1. Select task from dropdown
2. Configure options (if any)
3. Click **Start**
4. Watch progress bar
5. See results when complete

### Task Controls

- **Stop** — Cancel a running task
- **Release All** — Clear stuck tasks

### Tips

- Only one task runs at a time
- Long tasks show progress in the terminal
- Don't close the browser during tasks

---

## Play Page

**URL:** `/play`

**What it does:** Play poker hands against AI opponents.

### Starting a Session

1. Choose table size: **2**, **6**, or **9** players
2. Set starting stack
3. Click **Start Session**

### During Play

**Your Options:**
- **Fold** — Give up your hand
- **Call** — Match the current bet
- **Raise** — Increase the bet (enter amount)
- **All-In** — Bet everything

**Timer:**
- You have 10 seconds to act
- Auto-folds if you don't act

**AI Hints (optional):**
- Click **Get Hint** for AI recommendation
- Shows what the AI would do

### After Each Hand

- See the showdown (who won and why)
- Your session statistics update
- Continue to next hand or end session

### Session Statistics

- Hands played
- Your win rate (BB/100)
- VPIP and PFR
- Per-opponent results

### Study Mode

After playing:
1. Go to **Study** panel
2. Click **Export Decisions**
3. Use **Train from Play** to improve your personal AI

---

## Drill Page

**URL:** `/drill`

**What it does:** Practice decision-making on real hand spots.

### How It Works

1. You see a hand situation (your cards, board, action)
2. Make your decision
3. See what the AI recommends
4. Compare and learn

### Drill Settings

- **Hand source** — Use your imported hands
- **Street filter** — Focus on preflop, flop, turn, or river
- **Thinking time** — How long AI considers (more time = better analysis)

### Results Show

- **Your action** — What you actually did
- **AI recommendation** — What GTO suggests
- **Explanation** — Why the AI recommends this
- **EV difference** — How much the difference costs

### Deep Search Mode

Enable for more accurate analysis:
- Uses the full solver
- Takes longer but more accurate
- Best for important spots

---

## Equity Page

**URL:** `/equity`

**What it does:** Calculate your winning chances in any situation.

### How to Use

1. **Enter your hand:** Type like `AhKd` or `AA`
2. **Enter villain's range:** 
   - `random` = all hands
   - `AA,KK,QQ` = specific hands
   - `TT+,AQs+` = range notation
3. **Enter board (optional):** Like `Qh Jc Ts`
4. Click **Calculate**

### Results Show

- **Your equity** — Your winning percentage
- **Villain equity** — Their winning percentage
- **Tie** — Percentage you split the pot

### Range Notation Examples

| Notation | Meaning |
|----------|---------|
| `AA` | Pocket Aces |
| `AKs` | Ace-King suited |
| `AKo` | Ace-King offsuit |
| `TT+` | Tens or better pairs |
| `AQs+` | AQ suited or better |
| `22-66` | Pairs 22 through 66 |

### Tips

- Use for pre-session preparation
- Compare different scenarios
- Understand your edge in common spots

---

## League Page

**URL:** `/league`

**What it does:** Shows how AI agents perform against each other.

### Leaderboard

| Column | Meaning |
|--------|---------|
| Agent | AI bot name |
| Elo | Skill rating (higher = better) |
| Hands | Total hands played |
| BB/100 | Big blinds won per 100 hands |
| AIVAT | Statistical performance score |

### Agent Types

| Agent | Description |
|-------|-------------|
| main_agent | Your trained AI |
| distilled_gto | Pure GTO baseline |
| TAG | Tight-Aggressive bot |
| LAG | Loose-Aggressive bot |
| calling_station | Calls too much |
| random | Random decisions |

### Running League

1. Go to **Tasks**
2. Select **Bot League**
3. Choose duration (e.g., "Until 6 hours")
4. Start and wait

### Understanding Results

- **main_agent** should beat random/calling_station
- **Elo above 1550** means training is working
- **Positive AIVAT** means statistically winning

---

## Models Page

**URL:** `/models`

**What it does:** Manage different versions of your AI models.

### Version Management

Each model tracks:
- **Current** — Active version being used
- **Candidate** — New version to test
- **Previous** — Backup version

### Actions

| Action | What It Does |
|--------|--------------|
| Check Gates | Verify safe to upgrade |
| Promote | Make candidate the current version |
| Rollback | Revert to previous version |

### Model Cards

Click any model to see:
- Training date and parameters
- Performance metrics
- Data sources used

### Tips

- Always check gates before promoting
- Keep backups by not deleting previous versions
- Train new versions, don't overwrite

---

## Drift Page

**URL:** `/drift`

**What it does:** Monitors if player behavior is changing over time.

### What It Shows

- **Feature distributions** — How your plays are distributed
- **Changepoints** — When patterns shift
- **Drift reports** — Statistical comparisons

### Why It Matters

- Detects when opponents change strategy
- Shows if you're playing differently
- Identifies when retraining might help

---

## Profiles Page

**URL:** `/profiles`

**What it does:** Analyze individual player tendencies.

### Player Statistics

| Stat | Meaning | Good Players |
|------|---------|--------------|
| VPIP | % hands played | 20-30% |
| PFR | % hands raised | 15-25% |
| AF | Aggression factor | 2-4 |
| 3-Bet | % 3-bet when possible | 6-10% |
| C-Bet | % continuation bet | 50-70% |

### Range Inference

Shows estimated preflop range for any player:
- Based on their observed actions
- Updates as you import more hands

### Causal Analysis

Shows potential leaks:
- **What they do wrong**
- **How much it costs them**
- **How to exploit it**

---

## Health Page

**URL:** `/health`

**What it does:** Diagnoses system problems.

### Health Checks

| Check | What It Tests |
|-------|---------------|
| Database | Can connect and query |
| Models | Are files present |
| Solver | Is TexasSolver available |
| Memory | Enough RAM available |
| API | All endpoints working |

### Smoke Test

Click **Run Smoke Test** to verify:
- All components work
- No network traffic (air-gapped)
- Ready for use

### Troubleshooting

Red indicators mean:
1. Read the error message
2. Check the terminal for details
3. Follow suggested fix

---

## Common Questions

### How do I start over?

Delete `poker_ai/data/poker_ai.db` and restart. All imported hands will be lost.

### How do I backup my data?

Copy the entire `poker_ai/data/` folder and `poker_ai/artifacts/` folder.

### Why is training slow?

- Enable GPU: Install CUDA PyTorch
- Reduce batch size if running out of memory
- Import more hands for better results

### Can I use this during live play?

**No.** This is for study only. Using during live play may violate poker site terms of service.

### How accurate is the AI?

The AI is trained on your data and CFR solvers. It's not perfect but provides good GTO approximations. Results improve with:
- More imported hands
- Longer solver runs
- Better hardware

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `F5` | Refresh page |
| `Escape` | Close dialogs |

---

## Browser Tips

- Use Chrome or Firefox for best compatibility
- Keep only one tab open to the dashboard
- Clear cache if you see stale data: `Ctrl+Shift+R`
