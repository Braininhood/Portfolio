# Style encoder v1

Player **tendency embedding** from betting sequences in your SQLite hand library (Phase 6).

## Metrics (held-out)

| Metric | Value |
|--------|-------|
| k-NN top-1 (player ID) | 1.0 |
| k-NN top-5 (player ID) | 1.0 |
| Final loss | 1.73 |
| Val windows | 5,135 |
| Train windows | 49,136 |

See `metrics.json` in this directory for `finished_at`, `device`, and wall time.

## Training

| Setting | Value |
|---------|--------|
| Seed | 42 |
| Device | CUDA (when available) |
| Parameters | 3,030,720 |
| Embedding dim | 128 |
| Style dim | 64 |
| Transformer depth | 2 |
| Heads | 4 |

Config: `config.json` in this directory.

## Data

- **Your imported hands only** — windows sampled from the local database after ingest.
- Player IDs are pseudonymous slots (`player_uid_slots`: 16,384); no external player database.

## Use

- Opponent profiling on **Players** page.
- Optional style nudges for policy / league evaluation.

## License / compliance

- **MIT** — trained on user-owned local data only.
- No third-party model weights.

## Limitations

- High k-NN accuracy on small val player sets does not guarantee live-table read accuracy.
- Sparse villains (few hands) produce weak embeddings.
- Does not infer hole cards — action-sequence style only.
