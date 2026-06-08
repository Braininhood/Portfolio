# Poker AI — Product Overview

**Your personal poker coach that learns from your game.**

---

## What Is Poker AI?

Poker AI is software that helps you become a better poker player. It runs entirely on your computer — your hand histories and analysis stay private, and there are no monthly fees.

Think of it as having a poker coach available 24/7 who:
- Studies every hand you've ever played
- Shows you where you made mistakes
- Lets you practice against smart opponents
- Calculates the mathematically correct plays

---

## Who Is It For?

### Recreational Players
- Want to improve but don't have time for poker courses
- Curious how their play compares to "optimal"
- Like playing against computer opponents for practice

### Serious Amateurs
- Play regularly online or live
- Want to find and fix leaks in their game
- Interested in GTO (Game Theory Optimal) strategy

### Aspiring Professionals
- Need detailed hand analysis tools
- Want solver-quality recommendations
- Building a systematic study routine

---

## What Can You Do With It?

### 1. Import Your Hands

Upload your hand history files from PokerStars or other sites. The software reads them and builds a database of every hand you've played.

**Supported sites:**
- PokerStars
- Any site with Open Hand History export
- PHH archive files

### 2. Analyze Your Play

See your statistics at a glance:
- **VPIP** — How often you play hands (are you too loose or tight?)
- **PFR** — How often you raise preflop
- **Aggression** — Do you bet enough or just call?
- **Win rate** — Are you winning or losing?

Compare your decisions to what the AI recommends. Find out which spots are costing you money.

### 3. Practice Against AI Opponents

Play poker hands against intelligent computer opponents:
- Choose 2-player, 6-player, or 9-player tables
- AI opponents use different playing styles
- Get hints when you're unsure what to do
- Review your session statistics afterward

### 4. Train Your Decisions

The **Drill** feature shows you real situations from your hand history:
1. You see your cards, the board, and the action
2. You decide what to do
3. The AI shows what it would recommend
4. You learn from the comparison

### 5. Calculate Equity

Wondering how your hand does against a range? The equity calculator tells you your exact winning percentage in any situation.

**Example:** "How does AK do against someone who only 3-bets QQ+, AK?"  
Answer: 40% equity.

### 6. Generate Preflop Charts

The software can calculate mathematically optimal preflop strategies:
- Which hands to raise from each position
- How to respond to 3-bets
- Heads-up and 6-max solutions

---

## Key Features

### Completely Private

Your hand histories never leave your computer. There's no account to create, no data uploaded to servers, no tracking. Everything runs locally.

### No Subscription

Pay nothing. The software is free and open source. Train the AI once and use it forever.

### Learns From Your Data

The more hands you import, the smarter it gets:
- Recognizes patterns in your play
- Identifies your specific weaknesses
- Adapts recommendations to your style

### Works Offline

No internet required after installation. Use it on a plane, at a cabin, anywhere.

### Multiple Opponent Styles

Practice against different player types:
- **TAG** (Tight-Aggressive) — Solid, winning players
- **LAG** (Loose-Aggressive) — Tricky, unpredictable
- **Calling Station** — Calls everything
- **Nit** — Only plays premium hands
- And more...

---

## How It Works (Simple Version)

1. **You import hands** → Software reads your history files
2. **AI learns patterns** → Studies thousands of your hands
3. **Math calculates optimal play** → Solver finds the best strategies
4. **AI gives recommendations** → Fast answers when you need them

The AI combines:
- **Your personal data** — What you actually did
- **Mathematical solutions** — What's theoretically best
- **Opponent modeling** — Adjustments for different player types

---

## What You Need

### Computer Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Operating System | Windows 10, Mac, Linux | Windows 11 |
| Memory (RAM) | 4 GB | 8 GB |
| Storage | 2 GB free | 10 GB free |
| Processor | Any modern CPU | Multi-core CPU |
| Graphics | Not required | NVIDIA GPU (faster training) |

### Your Time

| Task | Time |
|------|------|
| Installation | 5 minutes |
| Import 10,000 hands | 2 minutes |
| Initial AI training | 30 minutes |
| Daily use | As much as you want |

---

## The Dashboard

When you open Poker AI in your browser, you see a clean dashboard with these sections:

### Setup
Step-by-step guide to get everything working. Follow the numbered steps and you're ready to go.

### Import
Add your hand history files. Just select a folder and click import.

### Status
See if everything is working correctly. Green checkmarks mean you're good.

### Play
Sit at a virtual table and play hands against AI opponents.

### Drill
Practice decision-making on real hands from your history.

### Equity
Calculator for any poker situation.

### League
Watch AI opponents compete against each other and see rankings.

### Profiles
Analyze specific players from your database.

---

## Common Questions

### Is this legal?

**Yes**, for personal study. The software analyzes your past hands and lets you practice offline. It does not connect to poker sites or assist during live play.

### Will this get me banned?

**No**, if you use it correctly. This is a study tool, like reading a poker book. Don't use it while playing — that would violate site rules.

### How is this different from GTO Wizard or PioSolver?

| Feature | Poker AI | Commercial Tools |
|---------|----------|------------------|
| Price | Free | $50-500/month |
| Privacy | 100% local | Cloud-based |
| Learning | Adapts to your hands | Generic solutions |
| Practice play | Built-in | Separate tools |

### Do I need programming skills?

**No.** Everything works through a visual dashboard in your web browser. Point, click, done.

### How accurate is the AI?

The AI approximates professional-level strategy. It's based on the same mathematical foundations (CFR algorithms) used by commercial solvers. For most players, it's more than accurate enough to significantly improve your game.

### Can I use my phone?

Currently desktop only (Windows, Mac, Linux). Mobile may come in the future.

---

## Getting Started

### Step 1: Install

Run the installer (takes about 5 minutes):

**Windows:**
```
Double-click install.ps1
```

**Mac/Linux:**
```
Run install.sh
```

### Step 2: Open Dashboard

Open your web browser and go to:
```
http://127.0.0.1:5173
```

### Step 3: Follow Setup

The Setup page guides you through:
1. Importing your hands
2. Building the database
3. Training the AI
4. You're ready!

---

## What's Included

### Analysis Tools
- Hand replayer with equity display
- Player statistics and tendencies
- Decision comparison vs optimal
- Equity calculator

### Training Features
- Play vs AI at any table size
- Decision drills on your hands
- Session review and statistics
- Opponent style practice

### AI Models
- HHFormer (pattern recognition)
- Student (fast decisions)
- Style Encoder (opponent profiling)
- Solver integration (GTO calculations)

### Documentation
- Getting started guide
- Feature explanations
- Command reference (for power users)
- AI architecture (for the curious)

---

## Summary

**Poker AI** is your personal, private poker improvement system:

✓ **Free** — No subscription, no fees  
✓ **Private** — Everything stays on your computer  
✓ **Smart** — AI learns from your actual hands  
✓ **Complete** — Analysis, practice, and training in one tool  
✓ **Offline** — Works without internet  

Import your hands, train the AI, and start improving today.

---

*Questions? Check the documentation in the `doc/` folder or the Help section in the dashboard.*
