# Poker AI

Part of the [Professional Portfolio](../README.md).

**A professional poker analysis and training platform.**

Train your own AI models, analyze your hand histories, and improve your game — all running locally on your computer. No cloud services, no subscriptions, your data stays private.

## What This Software Does

Poker AI helps you become a better poker player by:

1. **Importing Your Hands** — Load hand histories from PokerStars, OHH files, or PHH archives
2. **Analyzing Your Play** — See your statistics, find leaks, compare to optimal play
3. **Training Against AI** — Play practice hands against intelligent bots
4. **Building Solvers** — Generate GTO (Game Theory Optimal) preflop charts
5. **Learning Patterns** — The AI learns from your imported hands to give better analysis

## Quick Start (5 Minutes)

### Step 1: Install

**Windows (recommended):**
```powershell
cd poker_ai
powershell -ExecutionPolicy Bypass -File scripts\install.ps1
```

**Linux/Mac:**
```bash
cd poker_ai
./scripts/install.sh
```

### Step 2: Open the Dashboard

After installation completes, open your browser:

**http://127.0.0.1:5173**

You'll see the Setup page guiding you through the next steps.

### Step 3: Import Your Hands

1. Click **Import** in the menu
2. Select a folder containing your hand history files
3. Click **Start Import**

The system will process your hands and store them in a local database.

## What You Need

- **Windows 10/11**, Linux, or macOS
- **Python 3.11** (the installer handles this)
- **4GB RAM minimum** (8GB recommended for training)
- **GPU optional** (speeds up AI training but not required)

## Dashboard Pages

| Page | What It Does |
|------|--------------|
| **Setup** | Step-by-step guide to configure everything |
| **Import** | Load hand histories from your computer |
| **Status** | Check system health and AI models |
| **Tasks** | Run AI training jobs and analysis |
| **Play** | Practice against AI opponents |
| **Drill** | Test your decision-making on real hands |
| **Equity** | Calculate odds for any situation |
| **League** | See how the AI agents perform |
| **Models** | Manage AI model versions |
| **Health** | System diagnostics |

## Documentation

| Document | Who It's For |
|----------|--------------|
| [doc/AI_ARCHITECTURE.md](doc/AI_ARCHITECTURE.md) | Everyone — How the AI learns |
| [doc/WEB_GUIDE.md](doc/WEB_GUIDE.md) | Everyone — Dashboard walkthrough |
| [doc/CLI_REFERENCE.md](doc/CLI_REFERENCE.md) | Power users — Command line options |
| [doc/ROADMAP.md](doc/ROADMAP.md) | Developers — Technical architecture |

## Privacy & Security

- **100% Local** — Nothing leaves your computer
- **No Accounts** — No signup, no login, no tracking
- **Your Data** — Hand histories stay on your machine
- **Open Source** — You can inspect all the code

## Getting Help

1. Check the **Health** page in the dashboard for diagnostics
2. Read the documentation in the `doc/` folder
3. Look at error messages in the terminal where you started the server

## License

MIT License — free to use, modify, and share.

Third-party components (TexasSolver) are AGPL-licensed — see `doc/SECURITY_AND_COMPLIANCE.md`.
