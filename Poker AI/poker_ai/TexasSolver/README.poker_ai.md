# TexasSolver in this repo

Vendored **source** from [bupticybee/TexasSolver](https://github.com/bupticybee/TexasSolver) (AGPL-3.0). The poker_ai stack does **not** build this tree by default; it runs the official **console** release as a subprocess teacher for **HU postflop** (Phase 7).

**Full documentation:** [docs/PHASE7_SOLVER_BRIDGE.md](../docs/PHASE7_SOLVER_BRIDGE.md) · [docs/PHASES_0_7_COMPLETE_GUIDE.md](../docs/PHASES_0_7_COMPLETE_GUIDE.md) · [docs/COMMANDS_PHASES_0_7.md](../docs/COMMANDS_PHASES_0_7.md).

## Connect to poker_ai

| Step | Command |
|------|---------|
| Install binary (OS zip from GitHub) | `python -m poker_ai solve install-texas` |
| Re-download if corrupt | `python -m poker_ai solve install-texas --force` |
| Register browser download | `python -m poker_ai solve register-texas --zip PATH` |
| Register local build | `python -m poker_ai solve register-texas --exe PATH` |
| Check discovery | `python -m poker_ai solve texas-status` |
| Fill teacher cache (HU) | `python -m poker_ai solve grid --n-spots 200 --backend texas` |
| Train HU student | `python -m poker_ai train student` |

PowerShell wrapper: `.\scripts\install_texassolver.ps1`  
Bash wrapper: `./scripts/install_texassolver.sh`

Python bridge: `src/poker_ai/solver/bridge/texas.py` (input `.txt` format, JSON parse, subprocess with `-r` resources).  
Install/discovery: `src/poker_ai/solver/bridge/install_texas.py`, `paths.py`.

## Paths (default)

| Path | Contents |
|------|----------|
| `TexasSolver/` (this tree) | Vendored C++ source + `resources/` |
| `artifacts/third_party/texassolver/` | Downloaded zip + unpacked release |
| `artifacts/third_party/texassolver/install.json` | `executable`, `resource_dir`, version |
| `artifacts/solver_cache/` | Cached teacher spots (`backend=texas` or `mock`) |

**Override:** `POKER_AI_TEXAS_SOLVER_EXE` in `.env` or shell.

## Source vs binary

| | Vendored `TexasSolver/` | Release `console_solver.exe` |
|--|-------------------------|------------------------------|
| Purpose | Reference, optional CMake build | Phase 7 teacher subprocess |
| In git | Yes (source) | No (gitignored under `artifacts/`) |
| Required for `backend=texas` | No (unless you build and `register-texas --exe`) | Yes (via `install-texas` or register) |

## Troubleshooting

**`BadZipFile: File is not a zip file`**

- Often a **truncated** download (~5 MB on Windows; valid Windows zip **~41 MB**).
- Fix: delete `artifacts/third_party/texassolver/TexasSolver-v0.2.0-Windows.zip`, run `install-texas --force`, or download from [releases](https://github.com/bupticybee/TexasSolver/releases/download/v0.2.0/TexasSolver-v0.2.0-Windows.zip) and `register-texas --zip`.

**`texas-status` shows `installed=no`**

- Run `install-texas` or `register-texas`; vendored source alone is not enough without a built binary.

**`driver_available=False`**

- Executable missing or `resources/compairer/card5_dic_sorted.txt` not found; check `texas-status` paths.

## Multi-way

TexasSolver is **not** used for `n_active >= 3`. Use Phase 7b (`train multiway-student`) and optional Phase 7c Monker — see [docs/PHASE7B_POLICY_ROUTER.md](../docs/PHASE7B_POLICY_ROUTER.md).

## License

Do not commit downloaded binaries. AGPL applies to teacher outputs (`backend=texas` in cache). See `docs/PHASE7_SOLVER_BRIDGE.md`.
