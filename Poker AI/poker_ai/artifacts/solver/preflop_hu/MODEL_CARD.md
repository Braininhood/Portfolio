# Preflop CFR — heads-up (HU)

Tabular **CFR+** preflop chart for two-player pots (open, 3-bet, 4-bet trees).

## Artifact

- File: `artifacts/solver/preflop_hu_real.json` (or legacy `preflop_hu.json`)
- Format: JSON strategy map (`info_key` → action frequency vector)
- Version tag in JSON: `0.1.0`

## Training / solve config

| Setting | Typical value |
|---------|----------------|
| Algorithm | CFR+ on abstracted preflop game |
| Iterations | 50,000 |
| Equity mode | `real` (Monte Carlo samples per node) |
| Equity MC samples | 2,000 |

Re-run: **Tasks → solve preflop** (HU) or `python -m poker_ai solve preflop`.

## Data

- No neural weights — strategy table only.
- Built from the product’s abstract preflop game tree (not from a third-party hand-history corpus).

## Evaluation

- Target: exploitability reported in JSON (`exploitability_mbb`; negative sentinel when not computed).
- Used by HU bots and simulators before postflop student / heuristic policy.

## License / compliance

- **MIT** (this repository’s solver output).
- Not derived from TexasSolver postflop trees; independent tabular CFR artifact.

## Limitations

- HU structure only — not valid for 6-max open ranges without the 6-max chart.
- Assumes standard blind/ante abstraction configured at solve time.
- Does not encode opponent-specific exploits; GTO-ish baseline only.
