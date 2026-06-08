# Glossary — poker AI vocabulary used in this repository

Quick lookup for every term used in code, comments, or other docs. Where a term has a deeper treatment, follow the link.

> Conventions: card ranks `2 3 4 5 6 7 8 9 T J Q K A`. Suits `s h d c`. Sizes in **big blinds** unless noted. Cash-game NLH unless noted.

---

## A

| Term | Meaning |
|------|---------|
| **AAMAS / AAAI** | Conferences where most foundational poker AI work was published. |
| **Action abstraction** | Restricting the continuous bet space to a finite set (e.g. `{0.33, 0.66, 1.0, 2.0}× pot`). See [GTO_THEORY_AND_SOLVERS.md](GTO_THEORY_AND_SOLVERS.md) §4. |
| **AF (Aggression Factor)** | `(Bets+Raises)/Calls` post-flop. See [POKER_METRICS_GLOSSARY.md](POKER_METRICS_GLOSSARY.md) §2.1. |
| **AFq (Aggression Frequency)** | `(Bets+Raises)/(Bets+Raises+Calls+Checks)`. Bounded `[0,1]`, ML-friendly. |
| **AIVAT** | All-In Value Adjustment Tool — variance-reduced unbiased policy evaluator (Burch et al., 2018). See [OBSERVABILITY.md](OBSERVABILITY.md) §4. |
| **All-in equity** | Probability of winning at showdown given current cards, computed as if all chips go in now. |
| **Annex III** | EU AI Act schedule of high-risk AI use cases. See [SECURITY_AND_COMPLIANCE.md](SECURITY_AND_COMPLIANCE.md) §3. |

## B

| Term | Meaning |
|------|---------|
| **Bankroll** | Money set aside specifically for poker; tracked in `Bankroll_Tracking`. |
| **BB** | Big blind (forced bet). Also a position label. |
| **BB/100** | Big blinds won per 100 hands — the standard win-rate unit. |
| **Bet abstraction** | Same as action abstraction. |
| **Best response** | Strategy that maximally exploits an opponent strategy; used to compute exploitability. |
| **Blueprint strategy** | Coarse precomputed strategy used as a starting point at runtime; refined by sub-game solving (Libratus). |
| **BTN** | Button — the seat with the dealer marker; last to act post-flop, very profitable. |

## C

| Term | Meaning |
|------|---------|
| **Cbet (continuation bet)** | Bet on the next street by the previous-street aggressor. |
| **CFR (Counterfactual Regret Minimization)** | Iterative algorithm whose time-average converges to a Nash equilibrium in two-player zero-sum imperfect-information games (Zinkevich et al., 2007). |
| **CFR+** | Variant that zeroes negative regrets and uses linear averaging — much faster than vanilla CFR (Tammelin, 2014). |
| **CFV** | Counterfactual value — expected value at an info-set assuming the player would play to reach it. |
| **Chico** | Poker network. Hand-history format is similar to PokerStars text. |
| **Chip EV vs $EV** | Tournament concept; `$EV` adjusts chip values for ICM, see ICM. |
| **CO (Cutoff)** | Seat to the right of the BTN. |
| **Code Connect** | Figma plugin (referenced only via skills, unrelated to poker logic). |
| **Convergence** | The strategy reaching a target exploitability bound (e.g. ε ≤ 0.5 BB/pot). |

## D

| Term | Meaning |
|------|---------|
| **Datasheet** | Document describing a dataset’s provenance, biases, and consent basis (Gebru et al., 2018). |
| **Deep CFR** | CFR variant where regrets/strategy are approximated by neural networks (Brown et al., 2019). |
| **DeepStack** | First ≥ pro-level HU NL bot using continual re-solving + neural value nets (Moravčík et al., 2017). |
| **Deuces** | Python card library used by `db/GTO_Solver_Data.py` and `validate_card_data.py`. |
| **DPIA** | Data Protection Impact Assessment (GDPR). |
| **Drift** | Distribution shift between training data and live data. See [OBSERVABILITY.md](OBSERVABILITY.md) §3. |
| **DynamicRanges** | Legacy table from `drafts/GTO_Solver_Data_1.py`. Not active in canonical pipeline. |

## E

| Term | Meaning |
|------|---------|
| **Effective stack** | Min stack between two contesting players — caps how much can go in. |
| **EHS (Effective Hand Strength)** | Probability your current hand wins or improves to win; common card-abstraction signal. |
| **Equity** | Probability of winning the pot at showdown given current information; Monte Carlo–computed in `poker_hand_analysis.py`. |
| **EV (Expected Value)** | Probability-weighted result of an action. Stored in `GTO_Solutions.expected_value`. |
| **Exploitability** | Milli-big-blinds per game (mbb/g) a worst-case opponent extracts. See [GTO_THEORY_AND_SOLVERS.md](GTO_THEORY_AND_SOLVERS.md) §6. |
| **Exploitative play** | Deviating from Nash to profit against a known opponent model. |

## F

| Term | Meaning |
|------|---------|
| **Fish** | Loose-passive recreational player: VPIP 40 %+, PFR < 12 %, almost never folds. Synonym: calling station, whale, recreational. The primary exploit target. In code: `FishPolicy` (`fold_prob ≈ 0.5 %`, `call_prob ≈ 92 %`). |
| **Fold equity** | Pot won by inducing folds × probability of folds. |
| **Frequency** | Probability that a strategy assigns to an action in an info-set. |
| **`final_equity`** | River-equity column in `Results`; equals `river_equity` post-showdown. |

## G

| Term | Meaning |
|------|---------|
| **GDPR** | EU General Data Protection Regulation — see [SECURITY_AND_COMPLIANCE.md](SECURITY_AND_COMPLIANCE.md) §2. |
| **GG / GGPoker** | Poker network; hand histories ship as zipped folders of `.txt`. |
| **Golden hand** | A hand-history file committed as a fixture with known parser output. See [TESTING_AND_QA.md](TESTING_AND_QA.md) §5. |
| **GTO (Game Theory Optimal)** | Strategy that is unexploitable; in NLH it’s an idealized target, not what most solver outputs are. |
| **GTO+** | Commercial post-flop solver, value alternative to PioSOLVER. |
| **GTO Wizard** | Web product + APIs for GTO study; the 2026 Benchmark uses it for HUNL evaluation. |

## H

| Term | Meaning |
|------|---------|
| **Hand2Note (H2N)** | Tracker software with a proprietary range-research engine. |
| **Hand history (HH)** | Text/JSON record of a single hand. See [HAND_HISTORY_FORMATS.md](HAND_HISTORY_FORMATS.md). |
| **HH JSON / OHH** | [Open Hand History](https://hh-specs.handhistory.org/) — community JSON spec. |
| **Hero** | The player whose perspective the hand history is from; flagged via `Players.is_hero`. |
| **HM2 / HM3** | Holdem Manager 2 / 3 — popular hand-history trackers, store data in PostgreSQL. |
| **HUD** | Heads-up display — overlay on a poker client showing opponent stats. |
| **HUNL** | Heads-up no-limit. |
| **HU LHE** | Heads-up limit hold’em — solved by CFR+ to within statistical noise. |

## I

| Term | Meaning |
|------|---------|
| **ICM** | Independent Chip Model — converts tournament chip stacks to $EV; relevant to SpinGPT-style work. |
| **Imitation learning / behavioral cloning** | Supervised learning of `(state → action)` from logged games. |
| **Implied odds** | Pot odds adjusted for likely future bets won when a draw hits. |
| **Information set (info-set)** | All histories indistinguishable to the acting player. The unit of CFR. |
| **iPoker** | Poker network. Some HH variants are XML. |

## J

| Term | Meaning |
|------|---------|
| **JSON / OHH** | Community Open Hand History format. |

## K

| Term | Meaning |
|------|---------|
| **KS-statistic (Kolmogorov–Smirnov)** | Test for distribution shift; used in drift detection. |

## L

| Term | Meaning |
|------|---------|
| **LAG (Loose-Aggressive)** | Player style: VPIP 25–35 %, PFR 18–28 %, AF ≥ 2.5. Wide opening range combined with frequent barrels — applies constant pressure. A deliberate **skilled** strategy, not a fish variant. Distinguished from Maniac by having some hand-selection logic. In code: `LAGPolicy` (`fold_mul=0.65`, `aggro_mul=1.45`). |
| **Last-iterate convergence** | Property of newer policy-gradient/regret algorithms where the *current* (not averaged) strategy converges. |
| **Libratus** | First HU NL bot to beat top humans; used MCCFR blueprint + nested sub-game solving + self-improver (Brown & Sandholm, 2018). |
| **LLM (Large Language Model)** | In poker AI: PokerGPT, SpinGPT, ToolPoker, Readable Minds (2024–2026). See [SELF_LEARNING_AND_RESEARCH.md](SELF_LEARNING_AND_RESEARCH.md). |

## M

| Term | Meaning |
|------|---------|
| **Maniac** | Extreme LAG: VPIP 40 %+, PFR 35 %+, AF > 4. Raises constantly regardless of hand strength. A primary exploit target alongside the fish, but for different reasons (over-bluffs rather than over-calls). In code: `ManiacPolicy` (`fold_mul=0.3`, `aggro_mul=2.2`). |
| **mbb/g** | Milli-big-blinds per game; standard exploitability unit. |
| **MCCFR (Monte-Carlo CFR)** | CFR variants that sample subtrees rather than enumerating them. |
| **MCCFR+** | MCCFR combined with CFR+ regret update; the *intended* algorithm in `db/GTO_Solver_Data.py`. |
| **Membership inference** | Attack that infers whether a row was in the training set. Privacy concern for shared model weights. |
| **Model card** | Document describing a model’s intended use, data, metrics, limitations. |
| **MonkerSolver** | Commercial multiway / PLO solver. |
| **MP (Middle Position)** | Seat label for 6-max poker (UTG / MP / CO / BTN / SB / BB). |

## N

| Term | Meaning |
|------|---------|
| **Nash equilibrium** | Joint strategy where no player can profitably deviate unilaterally. |
| **Net result** | Player profit/loss for a hand in dollars (`Results.net_result`). |
| **NLH / NLHE** | No-Limit Hold’em (variant of poker). |
| **Nit (Rock)** | Tight-passive player: VPIP < 18 %, PFR < 14 %, folds almost everything. Waits only for premium hands; almost never applies aggression. Exploited by stealing frequently. Synonyms: rock, super-nit. In code: `NitPolicy` (`fold_mul=2.2`, `aggro_mul=0.3`). |

## O

| Term | Meaning |
|------|---------|
| **OHH** | Open Hand History (JSON) — see [HAND_HISTORY_FORMATS.md](HAND_HISTORY_FORMATS.md). |
| **OpenSpiel** | DeepMind reference library for game-theoretic algorithms (Kuhn/Leduc CFR demos). |
| **Opponent modeling** | Predicting opponents’ strategies from observed actions to exploit them. |

## P

| Term | Meaning |
|------|---------|
| **PFR (Pre-Flop Raise)** | Fraction of dealt hands the player raised pre-flop. |
| **phevaluator** | Fast C++ 7-card hand evaluator with Python bindings. |
| **PioSOLVER** | Industry-standard post-flop NLH solver. |
| **Playstyle** | Discrete label (TAG, LAG, Nit, …) assigned by `populate_exploitability.py`. |
| **Pluribus** | Multiplayer (6-max) NLH bot that beat pros (Brown & Sandholm, 2019). |
| **PokerKit** | Modern Python poker library. |
| **PokerStars** | Poker network; reference text format for hand histories. |
| **PokerTracker (PT4)** | Tracker software, `.txt` import, PostgreSQL backend. |
| **Position** | Seat relative to the dealer button: UTG / MP / CO / BTN / SB / BB. |
| **Pot odds** | `to_call / (pot + to_call)`. |
| **Profile** | Persona / parameter set applied to a base policy (TAG / LAG / exploit). |

## Q

| Term | Meaning |
|------|---------|
| **QFR (Quasi-Finite Regret)** | Recent gradient-based equilibrium-finding family ([ICLR 2025 QFR paper](https://www.mit.edu/~gfarina/2025/iclr25_qfr/iclr25_qfr.pdf)). |

## R

| Term | Meaning |
|------|---------|
| **Rake** | Fee taken from each pot by the room. |
| **Range** | Set of hands a player could be holding given observed actions. |
| **Reach probability** | Probability a player’s strategy reaches an info-set; weights regret updates. |
| **Regret matching** | Convert positive regrets into next-iteration strategy probabilities. |
| **Reservoir sampling** | Online uniform sample method used in Single-Deep-CFR average policy training. |
| **River** | The fifth and final community card. |
| **RTA (Real-Time Assistance)** | Software giving in-game advice during real-money play; ToS-prohibited on most rooms. |

## S

| Term | Meaning |
|------|---------|
| **SAR (Subject Access Request)** | GDPR right to receive a copy of personal data. |
| **SB** | Small blind. |
| **SD-CFR** | Single Deep CFR — Deep CFR variant with reservoir-sampled average policy. |
| **Selenium** | Browser automation library used by `convert/hand_parser.py`. |
| **Set-mining** | Calling preflop with a small pair hoping to flop a set. |
| **Showdown** | Players reveal cards at the river to determine the winner. |
| **Sim / simulator** | Internal NLH game engine for offline play. |
| **Slumbot** | Public HUNL benchmark bot from CMU (LBR-style baseline). |
| **SMOTE** | Synthetic Minority Over-sampling — used in `drafts/GTO_Solver_Data_1.py`. |
| **SPR (Stack-to-Pot Ratio)** | `effective_stack / pot`; controls commitment. |
| **SQLCipher** | Encrypted SQLite. |
| **Steal attempt** | Open-raise from CO/BTN/SB with the intent to win the blinds uncontested. |
| **Sub-game / sub-tree solving** | Re-solve the local game tree in real time around the current decision (DeepStack / Libratus). |

## T

| Term | Meaning |
|------|---------|
| **TAG (Tight-Aggressive)** | Player style: VPIP 15–25 %, PFR 12–20 %, AF 2–4. Selective preflop range + consistent aggression with strong holdings. The canonical "winning reg" style at mid-stakes cash games. In code: `TagPolicy` (`fold_mul=1.35`, `aggro_mul=1.2`). |
| **TexasSolver** | Open-source AGPL post-flop solver (`bupticybee/TexasSolver`). |
| **TexasSolverGPU** | GPU-accelerated successor. |
| **ToolPoker** | LLM-poker work that calls external solvers as tools (arXiv 2602.00528). |
| **ToS (Terms of Service)** | Usually prohibits bot play / RTA on third-party clients. |
| **Translation (action)** | Mapping an off-tree bet to the nearest abstracted size. |
| **Treys** | Python card library used by `db/poker_hand_analysis.py`. |
| **Turn** | The fourth community card. |

## U

| Term | Meaning |
|------|---------|
| **UTG (Under The Gun)** | First seat to act preflop after the blinds. |

## V

| Term | Meaning |
|------|---------|
| **Value bet** | A bet made expecting to be called by worse hands. |
| **Variance reduction** | Techniques (e.g. AIVAT, all-in EV) to lower the standard deviation of evaluation estimators. |
| **VPIP** | Voluntarily Put $ In Pot. See [POKER_METRICS_GLOSSARY.md](POKER_METRICS_GLOSSARY.md). |

## W

| Term | Meaning |
|------|---------|
| **WAL (Write-Ahead Log)** | SQLite journaling mode required for high-throughput inserts. |
| **Weak-Tight Reg** | Plays few pots (tight) but applies little postflop pressure (passive). Not as extreme as a Nit — participates in more hands but rarely bets for value or bluffs. Exploited by betting big when they call and by not folding to their rare aggression. In code: `PassiveRegPolicy` (`fold_mul=1.6`, `aggro_mul=0.55`). |
| **W$SD (Won at Showdown)** | Probability of winning when reaching showdown. |
| **WTSD (Went To Showdown)** | Probability of reaching showdown given the river. |
| **Whale** | Loose-passive recreational player (high VPIP, low PFR). Synonym: fish. |

## X

| Term | Meaning |
|------|---------|
| **XML hand history** | Older / iPoker-style format, supported by some PT4 / HM2 importers. |

---

Cross-references: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) · [POKER_METRICS_GLOSSARY.md](POKER_METRICS_GLOSSARY.md) · [GTO_THEORY_AND_SOLVERS.md](GTO_THEORY_AND_SOLVERS.md) · [SELF_LEARNING_AND_RESEARCH.md](SELF_LEARNING_AND_RESEARCH.md) · [SECURITY_AND_COMPLIANCE.md](SECURITY_AND_COMPLIANCE.md).
