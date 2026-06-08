# In-package documentation (`poker_ai/docs/`)



Long-form specifications, compliance, and the canonical **roadmap** live in the repository **`doc/`** directory (sibling of `poker_ai/`).



## Start here



| Doc | Use when |

|-----|----------|

| **[PHASES_0_7_COMPLETE_GUIDE.md](PHASES_0_7_COMPLETE_GUIDE.md)** | Full Phases 0–7 summary: routing, TexasSolver, Monker, paths, troubleshooting, tests |

| **[COMMANDS_PHASES_0_7.md](COMMANDS_PHASES_0_7.md)** | Copy-paste CLI commands per phase (living cheat sheet) |

| **[../../doc/ROADMAP.md](../../doc/ROADMAP.md)** | Exit criteria, phase status, future Phases 8+ |



## Per-phase detail



| Note | Topic |

|------|--------|

| [PHASE4_EQUITY.md](PHASE4_EQUITY.md) | Phase 4 equity — FFT/range-vs-range, `multiway.py` extension |

| [PHASE5_HHFORMER.md](PHASE5_HHFORMER.md) | Phase 5 HHFormer — train CLI, artifacts, embeddings |

| [PHASE6_SOLVER.md](PHASE6_SOLVER.md) | Phase 6 CFR/MCCFR — `--production`, HU + 6-max JSONs |

| [PHASE7_SOLVER_BRIDGE.md](PHASE7_SOLVER_BRIDGE.md) | Phase 7 TexasSolver bridge + HU distilled student |

| [PHASE7B_POLICY_ROUTER.md](PHASE7B_POLICY_ROUTER.md) | Phase 7b HU vs multi-way `RouterPolicy` |

| [PHASE7C_MONKER.md](PHASE7C_MONKER.md) | Phase 7c Monker JSON teacher (optional, licensed) |

| [PHASE8_STYLE.md](PHASE8_STYLE.md) | Phase 8 style embeddings + exploit policy |

| [COMMANDS_PHASE8.md](COMMANDS_PHASE8.md) | Phase 8 CLI cheat sheet |

| [PHASE9_LEAGUE.md](PHASE9_LEAGUE.md) | Phase 9 league — schedules, promotion, training path |

| [COMMANDS_PHASE9.md](COMMANDS_PHASE9.md) | Phase 9 CLI cheat sheet |

| [PHASES_0_9_STATUS.md](PHASES_0_9_STATUS.md) | Phases 0–9 done vs open checklist |

| [CLI_WEB_PARITY.md](CLI_WEB_PARITY.md) | CLI ↔ web matrix (v1 + v2, 27 job types) |

| [V2_IMPLEMENTATION_GUIDE.md](V2_IMPLEMENTATION_GUIDE.md) | v2 shipped — blueprint, AIVAT, replay league, diagnostics (CLI + web) |

| [LEAGUE_ARCHETYPES.md](LEAGUE_ARCHETYPES.md) | Frozen baseline roster |

| [../TexasSolver/README.poker_ai.md](../TexasSolver/README.poker_ai.md) | Vendored TexasSolver source + install/register commands |



## Changelog



| Date | Change |

|------|--------|

| 2026-05-20 | Added `PHASES_0_7_COMPLETE_GUIDE.md`; expanded index for Phases 7b/7c |
| 2026-05-21 | Phase 8: `PHASE8_STYLE.md`, `COMMANDS_PHASE8.md` |
| 2026-05-24 | Phase 9: `PHASE9_LEAGUE.md`, `--until-hours`, Texas grid fixes, promotion validated |
| 2026-06-02 | Doc sync: Phase 4 backfill, 7 gates, 8/9/10 preflop, style-in-league, promotion gates, `PHASES_0_9_STATUS` |
| 2026-06-02 | v2: `V2_IMPLEMENTATION_GUIDE.md` — dual CLI/web plan for streams A–D |
| 2026-06-05 | v2 shipped: Streams A–D complete; `taskNavigation.ts`; docs sync (CLI_WEB_PARITY, PHASES_0_9_STATUS, ROADMAP) |


