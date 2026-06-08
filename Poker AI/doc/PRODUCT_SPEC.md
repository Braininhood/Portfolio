# Product specification — universal NLH AI instrument

> **⚠ Legacy scope:** This document describes the **existing `convert/` + `db/` scripts**. The new canonical product is being built from scratch at `D:\Poker AI\poker_ai\` — see [POKER_AI_BLUEPRINT.md](POKER_AI_BLUEPRINT.md) for the target architecture, [ROADMAP.md](ROADMAP.md) for the phased plan, and [NOVEL_TECHNIQUES.md](NOVEL_TECHNIQUES.md) for the unique technical levers (HHFormer, distilled student, style embeddings, local self-play league, BOCPD, symbolic explainer). The new project is **fully local** and uses **no external AI services**.

## Vision (target)

A **single instrument** for No-Limit Hold’em that can:

1. **Ingest** hands from **many sources** — not only `.txt`: plain text (multiple sites), HTML, archives, JSON ([Open Hand History](https://hh-specs.handhistory.org/)), XML where applicable, plus **tracker DBs** (HM2, etc.). See [HAND_HISTORY_FORMATS.md](HAND_HISTORY_FORMATS.md).
2. **Normalize** them into one **canonical model** (positions, stacks, streets, actions, results).
3. **Analyze** (equity, tendencies, exploitability, bankroll, “decision quality”).
4. **Advise or simulate** with **configurable personas** (TAG / LAG / exploit-heavy / human-like noise).
5. **Learn** offline (retrain) and optionally **adapt** online within safe bounds — see [SELF_LEARNING_AND_RESEARCH.md](SELF_LEARNING_AND_RESEARCH.md) for CFR / self-play / log-supervision and evaluation practice.
6. **Operate** at **6, 7, 8, and 9–10** seats without forking the codebase.

## What the code does today (verified)

| Capability | Where | Notes |
|------------|--------|--------|
| Scrape HM web “convert” URLs | `convert/hand_parser.py` | Selenium + Chrome; `BASE_URL` Holdem Manager hand viewer; saves `hand_{id}.txt` to `SAVE_PATH`. |
| Filter lines / keep hands with Hero result | `convert/filter.py` | Reads `hand_*.txt` from `input_dir`, writes to `hand\2`. |
| HTML `<br />` / suit images → text | `convert/convert.py` | Poker Stars–style lines; overwrites files in `hand_directory`. |
| Nicknames → positions; simplify pots | `convert/converter.py` | `d:\hand\4` → `d:\hand\5`. |
| File-level stats (VPIP-style aggregates) | `convert/analizer.py` | Glob `D:\hand\hand_*.txt` (path in script). |
| **Core DB build** | `db/poker_hand_analysis.py` | **`main()` resets** `Games`, `Players`, `Hands`, `Actions`, `Results`; parses `FOLDER_PATH` (`d:/hand/5/`); **Treys** Monte Carlo equity (`NUM_SIMULATIONS`); stores `num_players` from first line. |
| MCCFR-style + GTO table rows | `db/GTO_Solver_Data.py` | **`GTOSolverData`**: **`reset_database()` drops `GTO_Solutions` only**; **`create_tables()`** creates **`GTO_Solutions`**; **`process_hand(hand_id)`** per row in `Games`. Uses **Deuces** for strength. **No `DynamicRanges` table** in this file (only in `drafts/GTO_Solver_Data_1.py`). |
| Exploitability metrics + NN | `db/populate_exploitability.py` | Drops/recreates **`Exploitability`**; SQL aggregates from `Players`/`Actions`/`Results`; PyTorch + sklearn scaler. |
| Bankroll summary | `db/Bankroll_Tracking.py` | Drops/recreates **`Bankroll_Tracking`**; hero-focused aggregates. |
| Bot decision labels + NN | `db/Bot_Performance.py` | `Bot_Performance`, `Training_Metrics`; small MLP on EV/result/exploitability features. |
| “Live” adjustment rows + NN | `db/Live_Adjustments.py` | Drops/recreates **`Live_AI_Adjustments`**; heuristic reasons + 8→2 net. |
| Opponent rollup + NN | `db/Opponent_Profiles.py` | Drops/recreates **`Opponent_Profiles`**. |
| Card string QA vs DB | `validate_card_data.py` | **Deuces** on `Hands.hero_cards` / `board_cards`. |

## Gaps vs “universal instrument”

- **No unified config:** `DB_PATH` / folders differ (`d:/hand`, `D:\hand`, `d:\hand`).
- **No runtime API:** nothing like `decide(game_state) → action` for a live or sim engine; scripts are **batch / DB–centric**.
- **No dashboard** in-repo (docs only propose options).
- **No HM2 adapter** in code yet (design only).
- **Two eval libraries:** **Treys** (`poker_hand_analysis.py`) vs **Deuces** (`GTO_Solver_Data.py`, `validate_card_data.py`) — universal tool should **standardize on one** card representation.
- **Multi-way / 7–9 handed:** `Games.num_players` exists, but parsers and `get_active_players_by_street` logic assume **player_id sets align with `1..num_players`**; **needs tests** for non–6-max samples.
- **Destructive runs:** several scripts **`DROP TABLE`** on startup — not safe for incremental “data lake” use until refactored.

## Human-like profiles & self-learning (design)

- **Profiles:** map to **post-processing or logits** on top of a base policy (future `policy/` module); today, **heuristics + separate NNs** in `Live_Adjustments` / `Opponent_Profiles` are prototypes, not a single profile engine.
- **Self-learning:** today = **re-run scripts** on growing SQLite + train small nets inside those scripts; universal tool should add **versioned datasets**, **train jobs**, and **model registry** (see roadmap).

## Compliance / “antibot”

A professional **universal** product targets **analysis, training sims, and integrations you control**. Real-time assistance or bots on third-party clients is typically **ToS / legally sensitive**; architecture should assume **compliant data paths** (owned hand histories, HM2 export on user machine, private sim).

See [ROADMAP.md](ROADMAP.md) for ordered engineering work.
