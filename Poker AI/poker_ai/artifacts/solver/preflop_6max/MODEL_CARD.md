# Preflop CFR — 6-max

Tabular **CFR+** preflop chart for six-handed ring games (RFI, vs-open, 3-bet branches).

## Artifact

- File: `artifacts/solver/preflop_cfr.json`
- Format: JSON strategy map (`info_key` → action frequency vector)
- Version tag in JSON: `0.1.0`

## Training / solve config

| Setting | Typical value |
|---------|----------------|
| Algorithm | CFR+ on abstracted 6-max preflop game |
| Iterations | 50,000+ (see JSON `iterations`) |
| Positions | UTG … BB abstracted per solve profile |

Re-run: **Tasks → solve preflop** (6-max) or `python -m poker_ai solve preflop` with 6-max profile.

## Data

- No neural weights — strategy table only.
- Produced locally from the engine’s preflop abstraction; user supplies their own DB for import/replay, not bundled corpora.

## Evaluation

- Exploitability metric in JSON when available.
- Consumed by 6-max sim, league, and play-vs-AI preflop routing.

## License / compliance

- **MIT** (repository artifact).

## Limitations

- Not a full tournament product (ICM, payouts, table balancing out of scope).
- Chart is only as accurate as the configured rake/stack/ante abstraction.
- HU-specific spots should use `preflop_hu` instead.
