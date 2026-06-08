# Poker metrics glossary — formulas, ranges, and repo specifics

This is the **professional reference** for every statistic the codebase produces or should produce. Each entry has:

- **Definition** — what the stat measures, in plain language.
- **Industry formula** — how PokerTracker / HM2 / GTO Wizard compute it (so dashboards line up with what players already know).
- **Sample-size guidance** — when the metric is meaningful.
- **Reference ranges** — typical 6-max NL cash values; treat as orientation, not gospel.
- **Repo specifics** — where it’s computed (`db/*.py`), how it differs from the industry formula, and the bug fixes needed to converge.

> All percentages are stored as fractions (`0..1`) by the SQLite scripts, but humans read them as `%`. Multiply by 100 before showing in any UI.

---

## 1. Pre-flop tendency stats

### 1.1 VPIP — Voluntarily Put $ In Pot

- **Definition.** Fraction of hands where a player **voluntarily** put chips in preflop (any call/raise that wasn’t a forced blind/ante).
- **Industry formula.**
  \[
  \mathrm{VPIP} = \frac{\#\{\text{hands with preflop call or raise (not just blind)}\}}{\#\{\text{hands dealt in}\}}
  \]
- **Sample size.** ≥ 500 hands for a stable read; 100 hands is a directional “feel.”
- **Typical 6-max NL ranges.**

  | Pool/style | VPIP |
  |---|---|
  | Solid reg / TAG | 22 – 27 % |
  | LAG | 28 – 35 % |
  | Loose-passive (whale) | 40 %+ |
  | Nit | < 18 % |

- **Repo specifics.** `populate_exploitability.py` defines:

  ```sql
  vpip = COUNT(action_type IN ('Raise','Call','Bet')) / COUNT(*)
  ```

  This counts **all streets**, not just preflop, and uses *actions* as the denominator (not hands). It is therefore an **action-frequency**, not the canonical VPIP. **Fix:**

  ```sql
  -- canonical, hand-anchored VPIP for a single player_id (in this repo)
  WITH first_voluntary AS (
    SELECT DISTINCT a.hand_id, a.player_id
    FROM Actions a
    WHERE a.street = 'Preflop'
      AND a.action_type IN ('Call','Raise')   -- NOT 'Bet'; preflop bet = blind
  )
  SELECT p.player_id,
         COUNT(DISTINCT fv.hand_id) * 1.0
           / NULLIF(COUNT(DISTINCT p.hand_id),0) AS vpip_canonical
  FROM Players p
  LEFT JOIN first_voluntary fv USING (hand_id, player_id)
  GROUP BY p.player_id;
  ```

### 1.2 PFR — Pre-Flop Raise

- **Definition.** Fraction of hands where the player **raised** preflop (open-raise, isolation, or 3-bet+).
- **Industry formula.** `# hands with at least one preflop raise / # hands dealt in`.
- **Reference ranges (6-max NL).**

  | Style | PFR |
  |---|---|
  | TAG | 18 – 23 % |
  | LAG | 24 – 30 % |
  | Maniac | 35 %+ |
  | Nit | < 12 % |

- **VPIP/PFR gap.** `VPIP − PFR` ≈ how often the player **only calls** preflop. Pros target ≤ 4 %.
- **Repo specifics.** `populate_exploitability.py` denominator is `COUNT(*)` over **all actions**, not hands. Use the canonical fix above with `AND a.action_type='Raise'`.

### 1.3 3-bet rate (`three_bet_rate`)

- **Definition.** Fraction of opportunities where the player re-raised preflop (3-bet+).
- **Industry formula.** `# preflop 3-bets / # opportunities to 3-bet (someone raised in front of you and the action got to you)`.
- **Reference ranges.** 7 – 12 % for solid regs; 4 – 6 % for nits; > 14 % is exploit-heavy.
- **Repo specifics.** `populate_exploitability.py` proxy:

  ```sql
  three_bet_rate = COUNT(action_type='Raise' AND street='Preflop' AND position IN ('SB','BB'))
                 / COUNT(street='Preflop' AND position IN ('SB','BB'))
  ```

  This restricts to SB/BB and ignores whether *someone raised first*. It is closer to **“blind defense raise rate”** than 3-bet rate. **Fix:** use a window function (or self-join) to flag actions where `MIN(action_id WHERE action_type='Raise') < current.action_id` on the same street.

### 1.4 Steal attempt rate (`steal_attempt_rate`)

- **Definition.** Fraction of hands where the player open-raised from CO/BTN/SB when folded to.
- **Reference ranges.** CO 28–35 %, BTN 40–55 %, SB 30–45 % at solid 6-max NL.
- **Repo specifics.** Proxy in `populate_exploitability.py`:

  ```sql
  steal_attempt_rate = COUNT(action='Raise' AND street='Preflop' AND position IN ('BTN','CO'))
                     / COUNT(street='Preflop' AND position IN ('BTN','CO'))
  ```

  Misses two key conditions: **(a)** action folded to the steal seat, and **(b)** SB stealing into BB. Use a window function over `Actions` ordered by `action_id` to require all earlier preflop actions are folds.

---

## 2. Post-flop tendency stats

### 2.1 Aggression Factor (AF)

- **Definition.** Ratio of aggressive to passive lines post-flop.
- **Industry formula.**
  \[
  \mathrm{AF} = \frac{\#\text{Bets} + \#\text{Raises}}{\#\text{Calls}}
  \]
- **Reference ranges.** 1.5 – 2.5 balanced, > 3 over-aggressive, < 1 passive.
- **Sample size.** AF stabilizes after ~1 000 post-flop decisions.
- **Repo specifics.** `populate_exploitability.py` divides by `Call` count without restricting to post-flop streets — preflop calls inflate the denominator. **Fix:** add `WHERE a.street IN ('Flop','Turn','River')` in both numerator and denominator.

### 2.2 Aggression Frequency (AFq)

- **Definition.** `(Bets+Raises) / (Bets+Raises+Calls+Checks)`. Bounded in [0,1] — preferred over AF for ML features.
- **Reference ranges.** 0.40 – 0.55 balanced; > 0.65 over-aggressive.
- **Repo:** not yet computed. Add as a derived column in `Exploitability`.

### 2.3 C-bet (continuation bet) percentages

- **Definition.** When the player was the preflop aggressor and is first to act on the next street: probability they **bet**.
- **Industry formula (per street).**
  \[
  \mathrm{Cbet}_{\text{flop}} = \frac{\#\{\text{flops where PFR seat bets first}\}}{\#\{\text{flops reached as PFR}\}}
  \]
- **Reference ranges (heads-up post-flop, 6-max NL).**

  | Texture | Flop cbet | Turn cbet | River cbet |
  |---|---|---|---|
  | Dry (e.g. Q73r) | 60 – 80 % | 40 – 60 % | 30 – 45 % |
  | Wet (e.g. T98ss) | 30 – 45 % | 25 – 40 % | 25 – 40 % |
  | Pool average | 55 – 65 % | 40 – 50 % | 30 – 40 % |

- **Repo specifics.** `populate_exploitability.py` computes:

  ```sql
  cbet_<street> = Bet on <street> / actions on <street>
  ```

  This is a **bet frequency**, *not* a c-bet. A c-bet requires preceding preflop aggression context. **Fix:** add a `Hands.preflop_aggressor_id` column populated by `poker_hand_analysis.py`, then condition on `player_id = preflop_aggressor_id` and on “first to act” using `Actions.action_id` ordering.

### 2.4 Fold-to-cbet (`fold_to_cbet`)

- **Definition.** When facing a c-bet: probability the player folds.
- **Reference ranges.** 45 – 55 % typical; > 65 % exploitably tight; < 35 % exploitably calling.
- **Repo specifics.** Proxy is folds on Flop/Turn/River divided by all actions on those streets. Doesn’t require an actual c-bet to have happened. **Fix:** flag actions where the preceding action *on the same street* is a `Bet` from a different player.

### 2.5 Showdown win % (`showdown_win`, WTSD$, W$SD)

- **WTSD (went to showdown).** Probability hand reaches showdown given river was reached.
- **W$SD (won $ at showdown).** Probability of winning the pot at showdown.
- **Reference ranges.** WTSD 25 – 30 % winning regs; W$SD 50 – 55 % is balanced, > 55 % usually means too tight (folding equity earlier), < 45 % too loose at showdown.
- **Repo specifics.** `Exploitability.showdown_win = won_pot>0 / showdowns` ≈ W$SD only. WTSD is not stored.

---

## 3. EV and bankroll metrics

### 3.1 Big blinds per 100 hands (BB/100)

- **Definition.** Net profit per 100 hands, normalized in big blinds.
- **Industry formula.**
  \[
  \mathrm{BB/100} = \frac{\sum \text{net\_result (in BB)}}{\#\text{hands}} \times 100
  \]
- **Pro benchmarks.** 6-max NL50 winners typically 4 – 8 BB/100; NL200+ shrinks to 1 – 4 BB/100; high-stakes pros sometimes < 1 BB/100.
- **Repo specifics.** `Bankroll_Tracking.py` computes net_result in **dollars**, then divides by `total_hands/100`. To get BB/100, divide each `net_result` by `Games.big_blind` first.

### 3.2 Pot odds, equity needed, and implied odds

- **Pot odds.** `to_call / (pot + to_call)` — the equity threshold to break even on a call.
- **Implied odds adjustment.** Add expected future winnings to the numerator when set-mining or chasing draws against deep-stack opponents.
- **Repo:** `Actions.bet_to_pot_ratio` is logged; pot odds can be derived as `amount_to_call / (pot_after)`. Add a view:

  ```sql
  CREATE VIEW v_pot_odds AS
  SELECT a.*,
         ROUND(a.amount * 1.0 / NULLIF(a.pot_after,0), 4) AS pot_odds_offered
  FROM Actions a;
  ```

### 3.3 SPR — Stack-to-Pot Ratio

- **Definition.** `effective_stack / pot` at the start of a street; controls how committable a hand is.
- **Reference buckets.** SPR < 4 → commit-friendly, 4–10 → standard, > 13 → "deep" play.
- **Repo:** not stored. Easy compute from `Actions.effective_stack / Actions.pot_before` at the first action of a street.

### 3.4 EV (expected value) and EV-adjusted win rate

- **Definition.** Probability-weighted result of an action, ignoring runout luck.
- **Variance reduction.** Use **AIVAT** (see [OBSERVABILITY.md](OBSERVABILITY.md)) to compare two policies on the same hands with up to 85 % less variance — published technique now standard in benchmarks like the [GTO Wizard Benchmark](https://arxiv.org/abs/2603.23660).
- **Repo:** `GTO_Solver_Data.calculate_ev` returns a per-street dict combining MCCFR+ counterfactual values with actual `net_result`. Stored in `GTO_Solutions.expected_value`.

### 3.5 Rake-adjusted win rate

- **Definition.** Pre-rake winrate minus the share of pot taken by the house.
- **Repo:** `Bankroll_Tracking.py` approximates with `SUM(big_blind * 0.1)` — this is a **fudge**, not actual rake from the hand history. Replace with `SUM(rake_dollars)` once you parse `Results: $X pot ($Y rake)` lines (see `convert/converter.py` for the regex).

---

## 4. Solver / GTO terminology used in the repo

| Term | Meaning | Where it shows up |
|------|---------|-------------------|
| Information set (info-set) | All histories indistinguishable to a given player at a decision (own cards + public history). | `MCCFRPlus` keys in `GTO_Solver_Data.py`. |
| Counterfactual value (CFV) | Expected value of an info-set assuming the player reaches it (others play strategy). | `_calculate_counterfactual_value`. |
| Regret | CFV difference between a fixed action and current strategy. | `update_regret`. |
| Regret matching | Convert positive regrets into next iteration’s strategy. | `get_strategy`. |
| Exploitation | Deviating from Nash to profit against a specific opponent model. | `Live_Adjustments.py`. |
| Exploitability | mbb/g (milli-big-blinds per game) a worst-case opponent can extract from the strategy. | `Exploitability` (note: the table’s value is an **NN-predicted score**, not a formal mbb/g exploitability). |
| Nash equilibrium | Joint strategy where no player can profitably deviate. | `calculate_nash_equilibrium` (heuristic mix, not a true equilibrium solve). |

See [GTO_THEORY_AND_SOLVERS.md](GTO_THEORY_AND_SOLVERS.md) for the underlying math and a comparison with commercial solvers.

---

## 5. Player-style classifiers

`apps/api/routers/players.py::_player_type()` maps (VPIP, PFR, AF) to the discrete
labels shown on the Players page and opponent profile cards.

### 5.1 Priority-ordered decision tree (current implementation)

```python
def _player_type(vpip, pfr, af) -> str:
    if vpip > 0.40 and af > 4.0:    return "Maniac"
    if vpip > 0.40 and pfr < 0.12:  return "Fish (Loose-Passive)"
    if vpip > 0.32 and af > 2.5:    return "LAG (Loose-Aggressive)"
    if vpip < 0.18 and pfr < 0.14:  return "Nit (Rock)"
    if vpip < 0.26:                  return "TAG (Tight-Aggressive)"
    if af > 3.0:                     return "Aggro Reg"
    return "Balanced Reg"
```

### 5.2 Reference table

| Label | VPIP | PFR | AF | Exploit approach |
|---|---|---|---|---|
| **Maniac** | > 40 % | any | > 4 | Tighten range, call down lighter, let them bluff off stack |
| **Fish (Loose-Passive)** | > 40 % | < 12 % | low | Value-bet thin, never bluff, pot-control with marginal hands |
| **LAG (Loose-Aggressive)** | 32-40 % | 18-28 % | > 2.5 | Float in position, 3-bet light, check-raise draws |
| **Nit (Rock)** | < 18 % | < 14 % | low | Steal often, fold to their rare aggression |
| **TAG (Tight-Aggressive)** | 15-26 % | 12-20 % | 2-4 | Avoid dominated spots, 3-bet for value and fold equity |
| **Aggro Reg** | 26-40 % | moderate | > 3 | Widen call-downs, look for check-raise spots |
| **Balanced Reg** | 26-40 % | moderate | 1.5-3 | Mix strategies; look for population tendencies |

### 5.3 Baseline archetype policies (league / sim)

The frozen bots used in league play and the live sim follow the same taxonomy.
Parameters are in `poker_ai/src/poker_ai/league/agents/baselines.py`:

| Agent key | Display name | fold_mul | aggro_mul | VPIP target |
|---|---|---|---|---|
| `tag` | TAG (Tight-Aggressive) | 1.35 | 1.20 | ~15-22 % |
| `lag` | LAG (Loose-Aggressive) | 0.65 | 1.45 | ~25-35 % |
| `nit` | Nit (Rock) | 2.20 | 0.30 | < 14 % |
| `fish` | Fish (Loose-Passive) | -- | -- | 40 %+ (call 92 %, fold 0.5 %) |
| `maniac` | Maniac (Ultra-Aggressive) | 0.30 | 2.20 | 40 %+ (raises constantly) |
| `passive_reg` | Weak-Tight Reg | 1.60 | 0.55 | ~15-22 % (no pressure) |

> Validate classifier thresholds against your own pool -- at 25NL Zoom the TAG cluster
> sits closer to VPIP 22 % / PFR 18 % than the theoretical cutoffs above.
---

## 6. Sample-size matrix (how many hands you need)

| Metric | Hands for ±2 % CI |
|--------|-----------------------|
| VPIP / PFR | ~ 600 |
| 3-bet | ~ 2 000 |
| Cbet flop | ~ 1 000 (per street) |
| Fold-to-cbet | ~ 1 500 |
| AF | ~ 1 000 post-flop decisions |
| WTSD / W$SD | ~ 4 000 |
| BB/100 | **≥ 100 000** for a 1 BB/100 confidence interval at typical NLHE variance (~ 100 BB SD per 100 hands). |

> Players who report 5 BB/100 “over 5 k hands” are reporting noise. Use **AIVAT** (see [OBSERVABILITY.md](OBSERVABILITY.md)) when comparing bots to cut the required sample by ~10×.

---

## 7. Industry references (read these once)

- **PokerTracker 4 stats glossary** — [pokertracker.com/guides/PT4](https://www.pokertracker.com/guides/PT4/)
- **Holdem Manager 2 stats** — [hm2faq.holdemmanager.com](http://hm2faq.holdemmanager.com/) (older but defines every column)
- **Hand2Note metric definitions** — [hand2note.com/help](https://hand2note.com/help/)
- **GTO Wizard glossary** — [gtowizard.com/learn](https://gtowizard.com/learn) (modern, ranges)
- **Statistical caveats / variance** — [Quantitative Poker (all-in adjusted SD)](http://www.quantitativepoker.com/2011/02/all-in-adjusted-standard-deviation-and.html)

---

## 8. See also

- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) — exact columns and types where these stats land.
- [GTO_THEORY_AND_SOLVERS.md](GTO_THEORY_AND_SOLVERS.md) — solver-side metrics (exploitability mbb/g, AIVAT).
- [OBSERVABILITY.md](OBSERVABILITY.md) — how to monitor stat drift across a real player pool.
