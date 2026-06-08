# Playbook — automated runner

**Active runner:** `scripts/run_playbook_full.py`

```powershell
cd "D:\Poker AI\poker_ai"
Get-Content reports\playbook_logs\playbook_status.json
Get-Content reports\playbook_logs\playbook_full.log -Tail 15
```

## Pipeline order

| Step | Job | Log |
|------|-----|-----|
| 1 | Equity backfill (full) | `equity_backfill.log` |
| 2 | `train multiway-student --row-limit 500000` | `multiway_train.log` |
| 3 | `league run --until-hours 6` (background) | `league_6h.log` |
| 4 | `solve preflop --positions 8max/9max/10max --production` | `preflop_*.log` |
| 5 | Phase 1 ingest perf test | `phase1_perf.log` |

## Already complete

- Phase 10 verify (5/5)
- Phase 7b unit tests (11/11)
- Student validate (MSE + p99)
- SQLite lock fixes + datasheet UI (restart `serve` to load)

## Tips

- Only one heavy DB job at a time; the full runner sequences backfill → train.
- League runs in parallel with preflop solves (mostly CPU).
- Do not start duplicate backfill/train from Tasks while the runner is active.
