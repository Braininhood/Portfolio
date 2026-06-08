# GTO theory and solver landscape — bridging the repo to formal CFR

This document grounds the heuristic `MCCFRPlus` class in `db/GTO_Solver_Data.py` against **real CFR theory** and against the **commercial / open-source solver ecosystem** that pros and researchers use today (2025–2026). Read it alongside [SELF_LEARNING_AND_RESEARCH.md](SELF_LEARNING_AND_RESEARCH.md), which covers neural extensions and benchmarks.

---

## 1. Mental model — what a “solver” actually does

A No-Limit Hold’em solver outputs, for a given **input tree**:

1. A **mixed strategy** at every information set (probability of fold/call/check/bet-X/raise-Y).
2. The **expected value** of each action under that strategy.
3. Optionally an **exploitability** number — how many milli-big-blinds per hand (mbb/g) the worst-case opponent gains by deviating.

It does *not* tell you how to play in a *different* tree (different stack depth, different bet sizes, different villain range). “GTO” solutions are **conditional on inputs**; mis-specifying them is the most common professional mistake.

The two essential algorithmic ingredients are:

- **Information set (info-set).** The set of all game histories indistinguishable to the acting player. Two hands where you hold AhKh on a Qh7c2d board after the same betting line share an info-set.
- **Counterfactual regret (CFR).** For every info-set and every action, the *regret* is the difference between the expected value of always playing that action vs. the strategy actually played, weighted by the probability the player would reach this info-set if they were trying to.

CFR iterates the strategy in the direction of positive regrets; the **time-average** strategy converges to a Nash equilibrium in two-player zero-sum games (Zinkevich et al., 2007).

---

## 2. CFR family — what every poker AI builds on

| Variant | Idea | When it shines | Reference |
|---------|------|----------------|-----------|
| **Vanilla CFR** | Full-tree traversal each iteration. | Tiny games (Kuhn poker, Leduc). | [Zinkevich et al., NeurIPS 2007](https://papers.nips.cc/paper/3306-regret-minimization-in-games-with-incomplete-information). |
| **CFR+** | Replaces negative regrets with 0; uses linear averaging. Empirically much faster. | HUNL & HU LHE (Bowling et al. essentially solved HU LHE with CFR+). | [Tammelin, 2014](https://arxiv.org/abs/1407.5042). |
| **External-Sampling MCCFR** | Sample the **opponent and chance** branches, traverse the player. | Memory-bound large games. | [Lanctot et al., NIPS 2009](https://papers.nips.cc/paper/3713-monte-carlo-sampling-for-regret-minimization-in-extensive-games). |
| **Outcome-Sampling MCCFR** | Sample a single trajectory per iteration. | Fastest per iteration; noisier. | Same paper. |
| **MCCFR+ (this repo)** | MCCFR-style sampling combined with CFR+ regret matching. | Practical compromise; **what `db/GTO_Solver_Data.py` claims to be**. | Hybrid; many implementations. |
| **Deep CFR** | Replace tabular regrets with neural networks. | Avoids hand-crafted abstractions. | [Brown et al., ICML 2019](https://proceedings.mlr.press/v97/brown19b/brown19b.pdf). |
| **Single Deep CFR** | Drops the average-policy net via reservoir sampling. | Simpler training pipeline. | [Steinberger, 2019](https://arxiv.org/abs/1901.07621). |
| **DREAM / RNN-CFR** | Variance reduction + recurrent encoders for partial obs. | Larger info-sets, longer game horizons. | [Steinberger et al., 2020](https://arxiv.org/abs/2006.10410). |

> Anything described as “self-play CFR” in conferences over the last decade is one of these flavors plus engineering tricks (sub-game solving, action abstraction, distillation).

---

## 3. From `MCCFRPlus` (the class) to `MCCFR+` (the algorithm)

The repo’s class lives in `db/GTO_Solver_Data.py`. Read it as a **CFR-flavored heuristic**, not a faithful MCCFR+ implementation. Comparing line-by-line:

| Faithful MCCFR+ | What `MCCFRPlus` does today |
|---|---|
| **Info-set key** = (private cards bucket, public history). | `info_set = f"{hand_id}_{street}_{num_players}"` — the hero's private cards are not part of the key, and `hand_id` is per-row in the DB so different hands cannot share strategies. **Effect:** no cross-hand learning. |
| **Action set** = legal actions in the current state (fold, call, raise-to-X for several sizes). | Fixed 5-action vector `[fold, call, raise, bet, check]`, agnostic of legality. |
| **Regret update** uses CFV computed by traversing the sub-tree under each action. | `_calculate_counterfactual_value` reads aggregated DB stats (`pot_before/after`, `fold_count/total_actions`) and applies a hand-strength heuristic. There is no game-tree traversal. |
| **Strategy averaging** uses linear weighting (CFR+). | `update_strategy` averages with `iteration+1` weights — the linear part is correct, but it’s applied to the *current* regret-matched strategy and never to a true sub-tree solve, so convergence guarantees do **not** carry over. |
| **Exploration** is **off-policy** — the algorithm itself is deterministic given the sample path. | An ε-greedy exploration with `exploration_decay=0.9999` is layered on top; this can keep the strategy stuck if iterations are short. |
| **Termination** is by exploitability bound or iteration count. | 1000 iterations per street, no exploitability check. |

### What this means in practice

- `GTO_Solutions.frequency` and `nash_equilibrium` are **research artifacts** about the *current observed line*, not exploitability-bounded strategies.
- The **good news**: the regret structure is genuinely useful as a *feature engineering target* for downstream nets (Bot_Performance, Live_Adjustments). Treat the table as “solver-flavored priors”, not as ground truth.
- The **fix path** (Phase 3 of [ROADMAP.md](ROADMAP.md)) is to:
  1. Re-key info-sets by `(hand_strength_bucket, board_texture_bucket, action_history)`.
  2. Define a real legal-action set per state (with bet sizings as fractions of pot).
  3. Either (a) bridge to an external solver via `subprocess` + JSON, or (b) integrate a small Deep CFR loop on a fixed bet abstraction.

---

## 4. Action and card abstraction — the unspoken core

NLH has a **continuous bet space** and a 1326 × C(48,3) flop tree. No solver works without abstraction:

- **Card abstraction.** Bucket private hands and boards into equity histograms (e.g. `imperfect-recall, EHS-distribution(50)`); used by Libratus and many academic systems.
- **Action abstraction.** Restrict bet sizes to e.g. `{0, 0.33pot, 0.5pot, 0.75pot, pot, 1.5pot, allin}`. Pros call this the **bet tree**.
- **Translation.** When facing an off-tree bet, map it to the nearest abstracted size — a frequent source of leaks.

> **Read once:** [Brown & Sandholm’s “Action Translation in Extensive-Form Games with Large Action Spaces” (IJCAI 2017)](https://www.cs.cmu.edu/~noamb/papers/17-IJCAI-Action.pdf) — explains why pseudo-harmonic translation beats naive nearest-size matching.

For this repo:

- A practical first iteration is `[0, 33%, 75%, 150%, allin]` per street. Five bet sizes × four streets gives a tractable tree at fixed stack depths.
- For mixed strategies, store **frequencies per legal size**, not per the existing 5-action enum.

---

## 5. Commercial and open-source solver landscape

A professional NLH AI product almost always **integrates** with one of these solvers rather than rewrites a solver from scratch. As of 2025–2026:

| Solver | Type | Strengths | Limits |
|--------|------|-----------|--------|
| [**PioSOLVER**](https://www.piosolver.com/) | Commercial, post-flop, single-tree per run, tree-config GUI. | Industry standard for HU NLH; fast convergence; large pro library; scripted tree-building via [PioCloud](https://piocloud.com/). | Heads-up only; Windows-only; expensive (Pro tier $499+); abstraction baked into the tree builder. |
| [**GTO+**](https://www.gtoplusapp.com/) | Commercial, post-flop. | Lower price (~$249 lifetime), Mac support, 99 % strategy agreement with Pio in mid-stakes spots. | Slower on large trees; more memory-hungry; less precise convergence at deep SPRs. |
| [**MonkerSolver**](https://www.monkersolver.com/) | Commercial; multiway and PLO. | The only mainstream tool for **3+ player** spots and PLO. | Memory & time intensive; less polished UX. |
| [**Simple Postflop / Simple Preflop Holdem**](https://www.simplepoker.com/) | Commercial. | Strong preflop solver; integrates with HUD-style trainers. | Smaller community library. |
| [**TexasSolver**](https://github.com/bupticybee/TexasSolver) | **Open source (AGPL-3.0)**, post-flop, C++ core, GUI optional. | Free for personal use; results align with PioSOLVER on benchmark spots; JSON strategy export; cross-platform. | Last stable release v0.2.0 (Nov 2021); commercial use needs the author’s permission; preflop is left to the user. |
| [**TexasSolverGPU**](https://github.com/bupticybee/TexasSolver) | Successor with GPU acceleration. | Faster convergence on consumer GPUs. | Less battle-tested; same licensing constraints. |
| [**OpenSolver / WASM-based community solvers**](https://github.com/) | Open source experiments. | Useful for learning; rapidly improving. | Not yet at PioSOLVER strength. |
| [**GTO Wizard Benchmark API**](https://github.com/gtowizard-ai/researcher-api-client) | Public **evaluation** API (not a solver you run). | Standardized HU NL benchmark with **AIVAT** variance reduction; 2026 leaderboard for bots and LLMs. | Evaluation only; rate-limited. |

### When to integrate vs. when to roll your own

- **Always integrate** for strategy ground truth, training labels, exploitability checks. PioSOLVER + TexasSolver cover ~99 % of the analysis needs for HU NL; MonkerSolver covers multiway.
- **Roll your own only for:** learning, research replication, novel abstractions, or non-NLH variants. Even Pluribus’ team distilled blueprint strategies from a *modified* MCCFR — they did not invent a fundamentally new tabular solver.

### Suggested integration architecture for this repo

```
solver_bridge/
  pio/        # subprocess driver, .cfr file builder, .csv frequency parser
  texas/      # TexasSolver --console driver, JSON loader
  wizard/     # HTTP client for GTO Wizard Benchmark
  schemas/    # Pydantic models — Tree, NodeStrategy, FrequencyByAction
```

Use the same `schemas.NodeStrategy` shape as the eventual `policy/` module; that way `GTO_Solutions` rows can be regenerated from any solver without touching downstream consumers.

---

## 6. Exploitability — the only measurement that matters

For HU NL, **exploitability** is reported in **mbb/g** (milli–big-blinds per game): how many `0.001 * BB` per hand the best response can extract from the strategy.

- Pluribus’ blueprint had estimated exploitability **far above** unbeatable-by-humans level — but its **post-blueprint nested re-solving** dropped it dramatically in practice.
- TexasSolver / Pio report convergence as `exploitability ≤ ε` thresholds — typical analysis runs target `ε = 0.5 BB / pot` (≈ 5 mbb/g) on small post-flop trees.

The repo today **stores an NN-predicted “exploitability score”** in `Exploitability.exploitability_score`, which is **not** mbb/g. Treat it as an internal proxy for player loose/tightness. To compute real exploitability you must:

1. Fix a tree (size, depth, bet abstraction).
2. Compute the **best response** to your strategy in that tree.
3. Measure `EV(BR) - EV(strategy)`, normalized to mbb/g.

[OpenSpiel’s `exploitability.py`](https://github.com/google-deepmind/open_spiel/blob/master/open_spiel/python/algorithms/exploitability.py) does exactly this for small games — re-using OpenSpiel for Kuhn / Leduc smoke tests is the cheapest way to validate any solver code in this repo before scaling.

---

## 7. Variance reduction during evaluation — AIVAT

When comparing two strategies on the same hand sample, **AIVAT** (Burch et al., 2018) cuts the standard deviation by ~85 % on average — meaning a tournament that needed 10 000 hands for a 1 BB/100 confidence interval needs only **~1 500** with AIVAT, and the [GTO Wizard Benchmark](https://arxiv.org/abs/2603.23660) leverages it to reach significance in under 50 000 HU hands.

How it works (sketch):

1. Compute a **value baseline** at every decision and chance node (any reasonable estimate works — a small CNN, the Treys evaluator, even average opponent equity).
2. The AIVAT estimator subtracts the *expected* baseline from the actual outcome — both for chance events (cards) and for the player’s own choices.
3. Because both terms have the same expectation, the unbiased estimator preserves the mean while shrinking the variance.

Use AIVAT in this repo as soon as a `Policy` interface exists (Phase 3 of [ROADMAP.md](ROADMAP.md)). For now, you can pre-compute baselines from `Results.preflop_equity` / `Results.flop_equity` and store an `aivat_adjusted_net` in `Bot_Performance`.

---

## 8. Putting it together — concrete next steps for this repo

1. **Stop calling the heuristic “MCCFR+”.** Rename to `RegretMatchedHeuristic` until at least info-sets, legal actions, and regret CFV are real.
2. **Wire one solver bridge.** Start with TexasSolver (`solver_bridge/texas`): JSON in, JSON out, AGPL acceptable for an internal tool.
3. **Add an `info_sets/` feature builder** that produces (hand bucket, board texture bucket, action history) keys — the foundation for any later Deep CFR work.
4. **Add `compute_exploitability_kuhn.py`** as a smoke test: import OpenSpiel, run CFR for 500 iters on Kuhn, assert exploitability < 1 mbb/g. Keeps you honest if you write your own solver later.
5. **Adopt AIVAT** for any A/B between profiles in `Bot_Performance`.

Cross-references:

- Algorithm details and benchmarks: [SELF_LEARNING_AND_RESEARCH.md](SELF_LEARNING_AND_RESEARCH.md).
- Where solver outputs land in SQLite: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) §2.1 (`GTO_Solutions`).
- Production policy interface: [ARCHITECTURE.md](ARCHITECTURE.md) §“Universal instrument”.
- Variance-aware monitoring: [OBSERVABILITY.md](OBSERVABILITY.md).
