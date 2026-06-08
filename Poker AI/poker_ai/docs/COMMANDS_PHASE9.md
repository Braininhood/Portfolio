# Phase 9 — Self-play league commands

> **Roadmap:** [doc/ROADMAP.md](../../doc/ROADMAP.md) §Phase 9 · **Guide:** [PHASE9_LEAGUE.md](PHASE9_LEAGUE.md) · **Router:** [PHASE7B_POLICY_ROUTER.md](PHASE7B_POLICY_ROUTER.md)

## League schedules

| Goal | Command |
|------|---------|
| Quick smoke | `python -m poker_ai league run --hours 0.05 --hands-per-matchup 60 --workers 8` |
| **Run until wall clock** (recommended for long jobs) | `python -m poker_ai league run --until-hours 6 --hands-per-matchup 200 --workers 16` |
| Until + HU | `python -m poker_ai league run --until-hours 2 --until-hu --table-sizes hu,6max,9max --workers 16` |
| Round-robin once (fast, not 6 h) | `python -m poker_ai league run --hours 6 --hands-per-matchup 500 --table-sizes hu,6max,9max --workers 16` |
| Multi-way only (until default) | `python -m poker_ai league run --until-hours 1` |
| Leaderboard | `python -m poker_ai league leaderboard` |
| List checkpoints | `python -m poker_ai league checkpoints` |

**Flags**

| Flag | Meaning |
|------|---------|
| `--hours` | Wall **cap** for round-robin (stops when all pairings done or time up) |
| `--until-hours` | Keep random matchups until wall clock elapses |
| `--until-hu` | In until mode, include HU (default until = 6max+9max only) |
| `--hands-per-matchup` | Round-robin total per pair, or **batch size** per job in until mode |
| `--table-sizes` | `hu,6max,9max` or `2,6,9` |
| `--workers` | `0` = ~75% CPUs; `1` = serial |

## Promotion check

```powershell
python -c "import json; d=json.load(open('reports/league_leaderboard.json')); print('promoted',d.get('promoted')); m=next(r for r in d['leaderboard'] if r['agent_id']=='main_agent'); frozen={'tag','lag','nit','rock','call_station','fish','passive_reg','random','cfr_stacked','distilled_gto'}; bad=[r for r in d['leaderboard'] if r['agent_id'] in frozen and r['elo']>=m['elo']]; print('main_elo',m['elo'],'hands',m['hands'],'aivat_p',m['aivat_pvalue']); print('frozen_not_beaten',bad)"
```

Pass: `promoted True`, `main_elo >= 1550`, `frozen_not_beaten []`, `aivat_p < 0.05`.

## Pre-league training (quality)

```powershell
cd "D:\Poker AI\poker_ai"

# Texas-only teacher cache (see PHASE7_SOLVER_BRIDGE.md)
python -m poker_ai solve grid --n-spots 1024 --backend texas --cache-dir artifacts/solver_cache_texas_only --continue-on-error --texas-threads 2

python -m poker_ai train student --epochs 50 --device auto --cache-dir artifacts/solver_cache_texas_only
python -m poker_ai train multiway-student --epochs 25 --row-limit 50000 --device auto

python -c "from poker_ai.policy.distilled_policy import load_best_policy; print(load_best_policy().name)"
```

## Reports

`reports/league_leaderboard.json`: `schedule`, `promoted`, `hands_played`, `wall_sec`, per-agent Elo / AIVAT / `formats` / brain-switch counters.

## Exit criteria (roadmap)

- [x] Main Elo ≥ +50 vs 1500 and beats every frozen baseline (validated May 2026)
- [x] AIVAT p &lt; 0.05 over ≥ 1000 hands with `promoted: true`
- [x] Optional roadmap literal “6 h” wall — playbook ~6.07 h (`--until-hours 6`; web **Until 6 hours** preset)
