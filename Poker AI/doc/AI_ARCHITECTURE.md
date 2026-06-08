# How the AI Works

A guide to understanding the Poker AI's learning system. No external AI services are used — everything runs locally on your computer.

## Overview

The Poker AI uses **neural networks** (the same technology behind ChatGPT, but much smaller and specialized for poker) to learn how to play. Instead of following fixed rules, it learns patterns from:

1. Your imported hand histories
2. Mathematical solver calculations
3. Playing against itself

## The AI Models

### 1. HHFormer — The Foundation Model

**What it is:** A "Transformer" neural network (similar architecture to GPT models, but poker-specific)

**What it learns:**
- Patterns in betting sequences
- Board texture recognition
- Showdown outcomes

**How it learns:**
- You import hand histories
- It reads through thousands of hands
- It learns to predict what happens next in each hand
- This gives it a deep understanding of poker

**Size:** ~10 million parameters (tiny compared to ChatGPT's billions, but specialized)

**Training time:** 5-30 minutes on a modern computer

### 2. Student — The Decision Maker

**What it is:** A simpler neural network that makes actual playing decisions

**What it learns:**
- What action to take in any situation
- Mimics the mathematical solver's recommendations

**How it learns:**
1. The CFR solver calculates "perfect" play for thousands of situations
2. The Student network learns to copy these decisions
3. Result: Fast decisions (~10ms) that approximate slow solver calculations (~seconds)

**Why two models?** 
- The solver is mathematically accurate but slow
- The Student is fast enough for real-time play
- Best of both worlds

### 3. Style Encoder — The Opponent Reader

**What it is:** A neural network that recognizes different player types

**What it learns:**
- Each player's unique patterns
- How to classify players (tight, loose, aggressive, passive)
- How to adjust against different styles

**How it learns:**
- Contrastive learning: "These hands are from the same player" vs "These are different players"
- Groups similar players together in mathematical space
- Enables personalized counter-strategies

### 4. Value Net — The Hand Evaluator

**What it is:** A neural network that predicts how much a hand is worth

**What it learns:**
- Expected value of different situations
- How to rank hands beyond simple card strength

### 5. CQL Policy — The Safe Learner

**What it is:** Conservative Q-Learning (a type of reinforcement learning)

**What it learns:**
- How to improve from historical play data
- Avoids risky moves that weren't in training data

**Why "conservative"?**
- Regular AI might try untested moves
- CQL stays close to what it's seen work before
- More reliable in real games

## The Learning Process

### Step 1: Data Collection (Import)

```
Your hand history files
        ↓
    Parser reads them
        ↓
    Database stores them
```

### Step 2: Feature Extraction (Build Features)

```
Raw hand data
        ↓
    Convert to numbers the AI understands
        ↓
    Position, stack size, board texture, actions → Numerical vectors
```

### Step 3: Foundation Training (Train HHFormer)

```
Thousands of hands
        ↓
    HHFormer reads them
        ↓
    Learns to predict masked (hidden) information
        ↓
    Result: Deep poker understanding
```

### Step 4: Solver Calculation (Solve Preflop / Build Cache)

```
Many poker situations
        ↓
    CFR algorithm calculates optimal play
        ↓
    Stores results in cache
```

### Step 5: Student Training (Train Student)

```
Solver's optimal decisions
        ↓
    Student learns to copy them
        ↓
    Result: Fast decisions that approximate perfect play
```

### Step 6: Self-Play League (League Run)

```
AI plays against itself
        ↓
    Measures win rates
        ↓
    Identifies weaknesses
        ↓
    Continuous improvement
```

## Key Concepts

### Neural Network

A mathematical function that learns patterns from data. Like a very sophisticated pattern-matching system that improves with more examples.

### Transformer

A specific type of neural network architecture that's good at understanding sequences (like poker action sequences). The same architecture used in ChatGPT, but much smaller.

### Self-Supervised Learning

The AI learns without being told what's "correct" — it just predicts missing information (like a word in a sentence) and learns from its mistakes.

### Behavioral Cloning

Teaching by example: show the AI many examples of good play, and it learns to copy that behavior.

### Reinforcement Learning

Learning by trial and error: the AI tries things, sees what works, and does more of what succeeds.

### CFR (Counterfactual Regret Minimization)

A mathematical algorithm that calculates game-theory-optimal (GTO) play. Guaranteed to find the best strategy, but slow.

## What Makes This Different

### vs. Simple Bots

Old poker bots used fixed rules like "raise with AA, fold with 72". This AI learns flexible strategies from data.

### vs. Cloud AI (ChatGPT, etc.)

- **Privacy:** Your hands never leave your computer
- **No subscription:** Train once, use forever
- **Specialized:** Purpose-built for poker, not general conversation
- **Fast:** Optimized for real-time decisions

### vs. Commercial Solvers

- **Integrated:** Learning, solving, and playing in one system
- **Adaptive:** Can learn opponent-specific adjustments
- **Free:** No per-month fees

## Training Requirements

| Task | Time | Hardware |
|------|------|----------|
| Import 10k hands | 1-2 min | Any CPU |
| Build features | 2-5 min | Any CPU |
| Train HHFormer | 5-30 min | GPU recommended |
| Solve preflop | 10-60 min | Multi-core CPU |
| Train Student | 5-15 min | GPU recommended |

**GPU Note:** Training works on CPU but is 5-10x faster with a modern NVIDIA GPU (RTX 3060 or better).

## Model Files

After training, your models are saved in `poker_ai/artifacts/`:

```
artifacts/
├── hhformer/v1/
│   ├── weights.safetensors  ← Neural network weights
│   ├── metrics.json         ← Training stats
│   └── MODEL_CARD.md        ← Documentation
├── student/v1/
│   └── ...
├── style_encoder/v1/
│   └── ...
└── solver/
    ├── preflop_cfr.json     ← Preflop charts
    └── preflop_hu_real.json
```

## Frequently Asked Questions

### How good is the AI?

The AI approximates GTO (game-theory-optimal) play. Against recreational players, it should be solidly profitable. Against professionals using commercial solvers, it's competitive but may not be cutting-edge.

### Can it beat online poker?

The AI is for **study only**. Using it during live play would violate poker site terms of service. Use it to analyze your past hands and practice offline.

### Why not use ChatGPT?

1. ChatGPT wasn't trained on poker-specific data
2. It's slow (seconds per response)
3. Your hands would be sent to OpenAI's servers
4. It can't do mathematical solver calculations

### How much data does it need?

- **Minimum:** 5,000 hands to start seeing patterns
- **Good:** 20,000+ hands for solid training
- **Better:** 50,000+ hands for nuanced understanding

### Can it learn my style?

Yes! The Style Encoder learns to recognize different players. You can analyze your own patterns and see how the AI would exploit you.

### Does it improve over time?

Yes, through:
1. Importing more hands
2. Running more solver calculations
3. Self-play league tournaments
4. Retraining with new data

## Technical Specifications

### HHFormer Architecture

```
Type: Pre-LayerNorm Transformer Encoder
Layers: 6
Attention Heads: 8
Hidden Dimension: 256
Feed-Forward Dimension: 1024
Parameters: ~10 million
Input: Token sequence (max 128 tokens)
Output: 256-dim embedding per hand
```

### Student Architecture

```
Type: Multi-Layer Perceptron (MLP)
Input: HHFormer embedding (256) + State features (28)
Hidden Layers: 512 → 256
Output: Action distribution (softmax)
Parameters: ~5 million
```

### Style Encoder Architecture

```
Type: Pre-LayerNorm Transformer
Layers: 2
Attention Heads: 4
Hidden Dimension: 128
Output: 64-dim style vector (L2 normalized)
Parameters: ~2 million
```

## Bot Profiles (Opponents)

The AI includes **11 different bot personalities** that simulate real player types:

### Main Agents

| Bot | Type | Description |
|-----|------|-------------|
| **main_agent** | Trained AI | Your trained neural network — the main player |
| **main_exploiter** | Adaptive | Tries to exploit weaknesses in main_agent |
| **distilled_gto** | GTO | Pure game-theory-optimal play |
| **cql_agent** | Research | Conservative Q-Learning agent (when trained) |
| **cfr_stacked** | Solver | CFR preflop + solver postflop |

### Player Archetypes (Frozen Baselines)

| Bot | Style | VPIP | Description |
|-----|-------|------|-------------|
| **TAG** | Tight-Aggressive | 15-22% | Plays few hands, bets strong — solid winning player |
| **LAG** | Loose-Aggressive | 25-35% | Plays many hands aggressively — tricky opponent |
| **Nit / Rock** | Tight-Passive | <14% | Only plays premium hands, rarely bluffs |
| **Call Station** | Loose-Passive | 40%+ | Calls everything, rarely raises — easy to value bet |
| **Fish** | Very Loose-Passive | 50%+ | Never folds, always calls — classic recreational player |
| **Maniac** | Hyper-Aggressive | 40%+ | Raises constantly — good for testing exploit strategies |
| **Passive Reg** | Weak-Tight | 18-22% | Plays okay cards but doesn't apply pressure |
| **Random** | Chaotic | 50% | Random legal actions — baseline for comparison |

### How Profiles Work

Each profile adjusts three "knobs":

```
Fold tendency:  How often they fold
Call tendency:  How often they call/check  
Aggro tendency: How often they bet/raise
```

**Example — TAG vs Fish:**

```
TAG:   fold_mul=1.35, call_mul=0.85, aggro_mul=1.20
       → Folds more weak hands, calls less, raises good hands

Fish:  fold_mul=0.005, call_mul=0.92, aggro_mul=0.075
       → Almost never folds, calls 92%, rarely raises
```

### Using Bot Profiles

**In Play Mode:**
- Choose table size (2, 6, or 9 players)
- AI opponents use various profiles
- Practice against different styles

**In League Mode:**
- All bots compete against each other
- Elo ratings track who's winning
- Your main_agent should beat fish/random, compete with TAG/LAG

**For Training:**
- `opponents eval-exploit` tests if your AI can beat each type
- Goal: Beat exploitable players (fish, station) by >5 BB/100

### Profile Statistics Reference

| Profile | VPIP | PFR | Aggression | Exploitability |
|---------|------|-----|------------|----------------|
| GTO | ~25% | ~20% | Balanced | Unexploitable |
| TAG | 15-22% | 12-18% | High | Low |
| LAG | 25-35% | 20-28% | Very High | Medium |
| Nit | <14% | <10% | Low | High (too tight) |
| Station | 40%+ | <10% | Very Low | Very High |
| Fish | 50%+ | <5% | None | Extreme |
| Maniac | 40%+ | 35%+ | Extreme | High |

**VPIP** = Voluntarily Put $ In Pot (% of hands played)  
**PFR** = Pre-Flop Raise (% of hands raised)

---

## Summary

The Poker AI is a **local, self-learning system** that:

1. **Learns** from your hand histories using neural networks
2. **Calculates** optimal play using CFR solvers
3. **Adapts** to different opponents using style embeddings
4. **Improves** through self-play tournaments

All of this runs on your computer with no external services, subscriptions, or data sharing.
