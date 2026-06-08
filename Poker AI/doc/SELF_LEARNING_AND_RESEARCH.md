# Self-learning poker AI — research landscape and professional practice

This note summarizes **how modern NLH agents learn**, what “self-learning” means at different scales, and **how to apply it intelligently** in a product like this repo (hand DB + analysis + future sim). It is **not** a recipe to run superhuman bots on a laptop; it is a **map of ideas, papers, and engineering choices**.

---

## 1. What “self-learning” can mean (taxonomy)

| Mode | Data | Objective | Typical use |
|------|------|-----------|-------------|
| **Self-play** | Agent vs itself (or league) | Improve policy / approximate Nash | Pluribus-style training; CFR iterations |
| **Offline RL / imitation** | **Human or solver logs** | Predict actions or values; distill | Your `hand/` + DB rows → supervised heads |
| **Counterfactual regret (CFR family)** | Game rules + sampling | Minimize regret per **information set** | Tabular MCCFR+; **Deep CFR** with nets |
| **Blueprint + real-time refinement** | Precomputed abstraction + live subgame | Close exploitability at decision time | Libratus-style nested solving |
| **Opponent-conditioned play** | Opponent stats / clusters | Maximize EV vs population, not NE | Exploitability tables; style models |

A **clever** system **combines** these: e.g. **self-play** for a strong prior, **logged hands** for realism and population alignment, **opponent model** for exploitation caps.

---

## 2. Landmark systems (context, not copy-paste recipes)

### Heads-up NLHE — imperfect information “solved” class

- **DeepStack** ([Moravčík et al., *Science* 2017](https://www.science.org/doi/10.1126/science.aam6960)) — continual re-solving, deep value networks, **depth-limited search** with learned evaluations. Shows how **decomposition** beats brute-force full tree.
- **Libratus** ([Brown & Sandholm, *Science* 2018](https://www.science.org/doi/10.1126/science.aao1733); [IJCAI overview PDF](https://www.ijcai.org/proceedings/2017/0004.pdf)) — **blueprint** from improved MCCFR, **nested subgame solving** during play, and a **self-improver** that patches weaknesses opponents found. Key lesson: **training and deployment are two different loops**.

### Multiplayer (6-max) NLHE

- **Pluribus** ([Brown & Sandholm, *Science* 2019](https://www.science.org/doi/10.1126/science.aay2400); [Meta AI blog](https://ai.meta.com/blog/pluribus-first-ai-to-beat-pros-in-6-player-poker/)) — trained with **self-play against five copies** of itself; strong **multiplayer** equilibrium reasoning (not just HU). Relevant to your **6–8+** seat goal.

### Neural + CFR (scalable learning)

- **Deep CFR** ([Brown et al., ICML 2019](https://proceedings.mlr.press/v97/brown19b.html); [PDF](https://proceedings.mlr.press/v97/brown19b/brown19b.pdf)) — uses networks to approximate advantages / strategies so you are not limited to **small abstractions**. Addresses the **abstraction–equilibrium chicken-and-egg** problem: good abstractions need equilibrium knowledge, which is expensive without abstraction.

Follow-on directions (search keywords): **Single Deep CFR (SD-CFR)** ([arXiv:1901.07621](https://arxiv.org/abs/1901.07621)), **RLCFR** ([arXiv:2009.06373](https://arxiv.org/abs/2009.06373)), **RL-CFR** for action abstraction ([arXiv:2403.04344](https://arxiv.org/abs/2403.04344)), **Hierarchical Deep CFR** ([OpenReview](https://openreview.net/pdf?id=wa7Ostlgxs)).

---

## 3. Professional / “clever” engineering ideas (product-grade)

### A. Separate **representation**, **solver**, and **deployment**

1. **Information state** encoding (public tree + private cards + action history) — stable across bet discretizations.
2. **Action abstraction** (bucketing bet sizes) — NLH is continuous; every serious system **abstracts** or uses **parametric** policies. RL-CFR lines explicitly study **learning** abstraction choices.
3. **Policy at runtime** — may be distilled net, not full CFR tree.

### B. Measure what you ship: **exploitability** and **baselines**

- Academic systems report **exploitability** (how much a worst-case opponent wins per hand) or performance vs **fixed benchmarks** (e.g. public HUNL bots).
- For your stack: define **internal baselines** — random, “always call,” a simple TAG script, and **regression** on fixed seeds whenever you change the net or DB pipeline.

### C. Use **your hand DB** as supervision (realistic “self-learning”)

- **Imitation / behavioral cloning** from logs: predict **line + sizing bucket** from features (position, SPR, board texture, stack). Classic NLH reference direction: generalization from logs ([IJCAI 2013](https://www.ijcai.org/Proceedings/13/Papers/457.pdf)).
- **Residual learning**: start from **GTO-ish** or CFR blueprint outputs in `GTO_Solutions`, learn **corrections** toward population or toward exploit model — smaller data need than pure self-play.

### D. Opponent modeling without going off the rails

- **Population statistics** (your `Exploitability` / `Opponent_Profiles` direction) → **conditional policy** or **restricted** exploit weights so the agent does not **overfit** one fish line.
- Recent applied work: adaptive multiplayer policies with **style modeling** (e.g. [Springer *Neural Computing and Applications* 2025](https://link.springer.com/article/10.1007/s00521-025-11262-x)) — same theme as classic **opponent modeling** ([UoA publications](https://poker.cs.ualberta.ca/publications/AAMAS13-modelling.pdf)).

### E. **Continual** learning = process, not one script

- **Version** datasets and models; **freeze** production weights; **promote** only after A/B in sim.
- **Catastrophic forgetting**: keep a **replay buffer** of stratified hands (strong/weak buckets, all streets).
- **Distribution shift**: when the room or player pool changes, **drift monitors** on feature statistics beat blind retrain.

### F. Compute realism

- Full-game self-play at Pluribus scale is **cluster-scale**. For a universal **instrument**, prefer: **small sim + strong eval**, **distillation**, **league** of small agents, and **incremental** DB-driven retrains — aligned with [ROADMAP.md](ROADMAP.md) Phase 7.

---

## 4. Mapping to **this repository** (honest)

| Research idea | Today in repo | Next step |
|---------------|---------------|-----------|
| CFR / regret | `MCCFRPlus` in `GTO_Solver_Data.py` (heuristic, DB-backed) | Tighter link to formal info-sets; tests; optional Deep CFR module |
| Neural heads | Several small PyTorch models in `db/*.py` | Unified `train/` job, shared features, metrics |
| Self-play | Not present | Env + league in `policy/` / `sim/` |
| Logged-hand learning | Implicit via DB + nets | Labeled `(state, action)` from `Actions` + supervised loss |
| Subgame solving | Not present | Optional “local re-solve” stub behind API |

---

## 5. Ethics and scope (professional)

Self-learning poker AI is **dual-use**: legitimate for **research, training sims, and analysis on owned data**. Building tools to **violate site ToS** or **deceive** humans at real-money tables is a separate (and harmful) product class. Design **eval harnesses** and **terms of use** accordingly.

---

## 6. Reading order (curated)

1. Pluribus — [Meta blog](https://ai.meta.com/blog/pluribus-first-ai-to-beat-pros-in-6-player-poker/) then [Science paper](https://www.science.org/doi/10.1126/science.aay2400).  
2. Deep CFR — [ICML 2019 page](https://proceedings.mlr.press/v97/brown19b.html).  
3. Libratus system overview — [IJCAI 2017 PDF](https://www.ijcai.org/proceedings/2017/0004.pdf).  
4. DeepStack — [Science](https://www.science.org/doi/10.1126/science.aam6960).  

For **log-driven** NLH: [Decision generalisation from game logs (IJCAI 2013)](https://www.ijcai.org/Proceedings/13/Papers/457.pdf).

---

## 7. 2024–2026 research snapshot (web review, March 2026)

Recent work reinforces three themes for a **universal NLH instrument**: (1) **CFR and hybrids** remain the backbone for strong defensive play; (2) **LLMs** are interesting for interfaces and data—but need **solvers/tools** or heavy fine-tuning for GTO-level play; (3) **evaluation** is finally getting **API-grade** baselines and **variance reduction**.

### LLMs + poker (2024–2026)

- **PokerGPT** ([arXiv:2401.06781](https://arxiv.org/abs/2401.06781), Jan 2024) — end-to-end **multi-player** NLHE with a **lightweight LLM** + RLHF-style training from textual game records; positions itself against raw CFR cost at scale.
- **SpinGPT** ([arXiv:2509.22387](https://arxiv.org/abs/2509.22387); v2 dated Feb 2026) — **Spin & Go** (3-player) via **SFT** on expert decisions + **RL** on solver-generated hands; reports high **agreement with solver** actions and HU results vs **Slumbot** in paper experiments. Motivation: CFR complexity and **non–two-player** payoff structure (mentions **ICM** / tournament effects).
- **How Far Are LLMs from Professional Poker Players?** + **ToolPoker** ([arXiv:2602.00528](https://arxiv.org/abs/2602.00528), 2026) — systematic study: LLMs trail **CFR+ / DeepCFR**-class baselines; diagnoses **heuristic bias**, **factual errors**, and **knowing–doing gaps**. **ToolPoker** routes decisions through **external solver APIs** so actions stay GTO-consistent while the model explains—aligned with your roadmap’s “FastAPI + tools” direction.
- **Readable Minds** ([arXiv:2604.04157](https://arxiv.org/abs/2604.04157), 2026) — extended **multiplayer NLHE** with LLM agents; argues **persistent memory** enables emergent **theory-of-mind**-like notes and exploitation that can **deviate from strict TAG/GTO** adherence—relevant to “human-like profiles,” not as a substitute for audited solver policies.

### Beyond pure Nash / long-horizon play

- **Beyond Game Theory Optimal: Profit-Maximizing Poker Agents** ([OpenReview](https://openreview.net/forum?id=Xh0s29VtbH)) — explicitly combines **GTO / CFR strength** with **exploitative adaptation** in HU and multi-way NLHE (workshop track; verify citations before building on it alone).
- **Implicit Strategic Optimization (ISO)** ([arXiv:2602.08041](https://arxiv.org/abs/2602.08041), 2026) — **6-player NLHE** and long-horizon framing: **prediction-aware** policy updates when payoffs depend on evolving **meta-game** context (reputation, adaptation), not only per-hand EV.

### Equilibrium computation (theory + scaling, 2024–2026)

- **RL-CFR** for **action abstraction** ([arXiv:2403.04344](https://arxiv.org/abs/2403.04344), 2024) — RL chooses abstraction features in extensive-form games including NLHE-style settings.
- **Nash Policy Gradient (NashPG)** ([arXiv:2510.18183](https://arxiv.org/abs/2510.18183), 2025) — policy-gradient family with refined regularization toward **exact** Nash in two-player zero-sum settings; reports scaling toward **NLHE-scale** domains in the abstract.
- **Quadratic programming / complementarity for multiplayer imperfect information** ([arXiv:2509.25618](https://arxiv.org/abs/2509.25618), 2025) — alternative computational angle for **small** multiplayer toy games; watch for follow-ons to larger poker abstractions.
- **Last-iterate / refined equilibria** — e.g. adaptive regret toward **extensive-form perfect equilibrium** refinements ([arXiv:2508.07699](https://arxiv.org/abs/2508.07699), 2025); **regularized policy gradients** with convergence statements (e.g. [ICLR 2025 QFR PDF](https://www.mit.edu/~gfarina/2025/iclr25_qfr/iclr25_qfr.pdf), [NeurIPS-style policy gradient convergence](https://openreview.net/forum?id=VYY5sG4EMm)) — useful when you mix **gradient** methods with **CFR** tooling.

### Benchmarking (2026) — product-relevant

- **GTO Wizard Benchmark** ([arXiv:2603.23660](https://arxiv.org/abs/2603.23660), March 2026) — **public API** for HUNL evaluation vs a **strong proprietary agent** (paper reports large margin over **Slumbot** / ACPC lineage); integrates **AIVAT** variance reduction so fewer hands reach significance. Includes a **leaderboard** and evaluation of **frontier LLMs** (still far below the benchmark in reported experiments). Client: [github.com/gtowizard-ai/researcher-api-client](https://github.com/gtowizard-ai/researcher-api-client).

**Takeaway for this repo:** treat **2026 benchmarks** as the new bar for “does our bot measure up?” alongside internal sims; treat **LLMs** as **orchestration + UX + opponent text**, not as the sole policy, unless you adopt a **ToolPoker-style** solver bridge.

---

## 8. See also

- [ARCHITECTURE.md](ARCHITECTURE.md) — current modules.  
- [ROADMAP.md](ROADMAP.md) — Phases 2–4 (features, policy API, profiles), Phase 7 (learning loop).  
- [PRODUCT_SPEC.md](PRODUCT_SPEC.md) — vision vs code today.
