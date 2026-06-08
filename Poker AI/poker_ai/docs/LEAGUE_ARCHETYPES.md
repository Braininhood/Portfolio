# League frozen archetypes (Phase 9)

Scripted opponents for self-play scoring. They are **action reweighting** over `HeuristicPolicy` (or fixed call/fold tables), not database-derived VPIP — useful for stable league baselines and exploit drills.

## Research basis

Common live-poker taxonomy (tight/loose × passive/aggressive):

| Archetype | Style | Typical live stats (approx.) | Exploit lever |
|-----------|--------|------------------------------|---------------|
| **TAG** | Tight-aggressive | VPIP 15–22%, PFR 12–18% | Respect 3-bets; attack blind defense |
| **LAG** | Loose-aggressive | VPIP 25–35%, PFR 20–28% | Trap; call down lighter |
| **NIT / Rock** | Tight-passive | VPIP &lt;14%, low PFR | Steal blinds; fold to their aggression |
| **Calling station** | Loose-passive | VPIP 40%+, PFR 5–10% | Value bet; bluff rarely |
| **Fish** | Loose-passive+ | Very high VPIP, min-raise rare | Same as station, thinner value |
| **Maniac** | Ultra-LAG | Extreme VPIP/PFR | Call down; let them bluff off |
| **Passive reg** | Weak-tight | Low aggression postflop | Pressure when they show weakness |

Sources: [Pokerology — 6 player styles](https://www.pokerology.com/poker/strategy/playing-styles/), [PokerStrategy — five types](https://www.pokerstrategy.com/strategy/bss/five-player-types/), [PokerCoaching — playing styles](https://pokercoaching.com/blog/different-poker-players/).

## League agent IDs

| `agent_id` | Policy class | Role |
|------------|--------------|------|
| `main_agent` | `RouterPolicy` via `load_best_policy()` | Headline |
| `main_exploiter` | `ManiacPolicy` | Placeholder exploiter |
| `league_exploiter` | CFR stacked or `LAGPolicy` | Historic-beater slot |
| `tag` | `TagPolicy` | Frozen |
| `lag` | `LAGPolicy` | Frozen |
| `nit` | `NitPolicy` | Frozen |
| `rock` | `RockPolicy` (= nit) | Frozen |
| `call_station` | `CallStationPolicy` | Frozen |
| `fish` | `FishPolicy` | Frozen |
| `passive_reg` | `PassiveRegPolicy` | Frozen |
| `random` | `RandomPolicy` | Frozen |
| `distilled_gto` | Same as main snapshot | Frozen |
| `cfr_stacked` | `StackedPolicy` | Frozen (if artifact) |

## Not in league yet

- **GTO wizard** — needs solver-balanced policy, not heuristics
- **Per-player style embeddings** (Phase 8) — wired in `play_hand` but not passed by `league run`
- **Trained `main_exploiter`** — Phase 11 continual loop
