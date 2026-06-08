# Novel techniques — what makes `poker_ai/` unique

This document collects the **clever, professional, sometimes genuinely novel** technical levers behind the new project. Each section gives:

- **Why** it’s interesting / unique.
- **How** it works (math + pseudocode).
- **What** to build, in this repo, to ship it.
- **Where** it slots into the [ROADMAP.md](ROADMAP.md).

> Hard rules carried forward from the rest of the project: **no external AI services**, **local-first**, **reproducible**, **owned data only**. Every technique below is implementable on a single workstation.

The order matches the roadmap so you can read straight through.

---

## 1. HHFormer — a poker-specific foundation model trained from scratch

**Where:** Phase 5 of the roadmap.
**Status (May 2026):** **Done** in `poker_ai/` — pretrain (`train hhformer`), embed export (`features hhformer-embed`), optional Phase 4 equity on embed, ingest hook (`--train-hhformer`). Production run on ~31k hands: MAP 80.5 %, SOP AUC 0.97, probe 0.79, ~7 min on RTX 5070 + CUDA. **Phase 6 (done):** tabular CFR+ / MCCFR, `solve preflop`, stacked policies — [PHASE6_SOLVER.md](../poker_ai/docs/PHASE6_SOLVER.md). **Phase 7 (shipped):** TexasSolver bridge + mock teacher, solver cache, `train student`, `DistilledPolicy` — [PHASE7_SOLVER_BRIDGE.md](../poker_ai/docs/PHASE7_SOLVER_BRIDGE.md). **Not yet:** HTTP API, exploit/style policies (Phase 8). To our knowledge, no public open-source NLH project ships a transformer pretrained directly on hand-history sequences; PokerGPT / SpinGPT use *generic* LLMs — HHFormer is **task-native**, ~5 M params, laptop-trainable.

### 1.1 Why

A pretrained, poker-specific encoder gives **every downstream head** (action prediction, hand strength, opponent classification, decision quality) a head start without ever calling an external LLM. Embeddings are also the foundation of the style encoder (§5) and the distilled student (§3).

### 1.2 Tokenisation

Each hand becomes a sequence of mixed tokens:

```
[CLS] [STAKE=NL10] [SEATS=6] [POS=BTN] [STACK=100bb]
[ACT=raise|2.5bb|seat=BTN] [ACT=fold|seat=SB] [ACT=call|seat=BB]
[FLOP=Ah Kd 7c] [POT=5.5bb]
[ACT=check|seat=BB] [ACT=bet|0.66pot|seat=BTN] [ACT=fold|seat=BB]
[SHOWDOWN=BTN]
```

A token is `(type, value)` where types are `STAKE / SEATS / POS / STACK / ACT / STREET / CARD / POT / SHOWDOWN`. The vocabulary is closed and small (~1 500 tokens), allowing a 64-dim embedding table.

### 1.3 Architecture

```python
class HHFormer(nn.Module):
    def __init__(self, vocab=1500, dim=256, depth=6, heads=8, max_len=256):
        super().__init__()
        self.tok = nn.Embedding(vocab, dim)
        self.pos = nn.Embedding(max_len, dim)
        self.blocks = nn.ModuleList([
            PreLNTransformerBlock(dim, heads, ff_mult=4) for _ in range(depth)
        ])
        self.ln = nn.LayerNorm(dim)
        self.head_act  = nn.Linear(dim, vocab)   # MAP head
        self.head_card = nn.Linear(dim, 52)      # MCP head
        self.head_show = nn.Linear(dim, 9)       # SOP head: winner seat (1..9)
```

Pre-LN transformer for training stability, RoPE optional for sequence length flexibility. ~10 M params total — fits comfortably in 8 GB GPU memory.

### 1.4 Pretraining objectives

Three jointly trained self-supervised tasks:

| Objective | Sketch | Loss |
|-----------|--------|------|
| **Masked Action Prediction (MAP)** | Mask 15 % of `ACT=` tokens; predict from context. | `cross_entropy` |
| **Masked Card Prediction (MCP)** | Mask board cards; predict suit and rank. | `cross_entropy` |
| **Showdown Outcome Prediction (SOP)** | Pool the `[CLS]` token, predict winning seat for showdown hands. | `cross_entropy` |

Loss = `λ_map · L_map + λ_mcp · L_mcp + λ_sop · L_sop`. Default `(0.6, 0.2, 0.2)`.

### 1.5 Why this is enough

- Action prediction forces the model to internalise **strategy priors** (someone who 3-bet is unlikely to fold to a min-raise).
- Card prediction forces **board structure** awareness.
- Showdown prediction forces **end-to-end credit assignment**.

### 1.6 Validation

- MAP top-1 accuracy ≥ 65 % on a held-out set of 2 k hands.
- A linear probe on `[CLS]` reproduces hand-strength categories with AUC ≥ 0.55.
- Frozen embeddings improve the student net (§3) MSE by ≥ 20 % vs. training the student from scratch.

### 1.7 Risks

- **Small data.** 19 k hands is tiny for a transformer. Mitigations: aggressive masking ratios (25 % vs. 15 %), data augmentation (mirror seat order, equivalent suit permutations), random subsequence cropping.
- **Distribution narrowness.** All staged hands come from one or two sites. Add public OHH samples and synthetic CFR rollouts during pretraining.

---

## 2. Range-vs-Range exact equity in milliseconds

**Where:** Phase 4 of the roadmap.
**Status:** Monte Carlo equity is everywhere; **batched, range-aware, FFT-accelerated** range-vs-range equity is rare in open source.

### 2.1 The primitive

Each NLH player range is a vector `R ∈ ℝ^1326` (one entry per starting hand combo) with `‖R‖_1 = 1`. Two ranges `R_A`, `R_B`, plus a fixed board `B`, define a tractable equity:

\[
\mathrm{eq}(R_A, R_B, B) = \frac{1}{Z(B)} \sum_{a, b} R_A[a]\,R_B[b]\,\mathbb{1}[a \cap b \cap B = \varnothing]\,W(a, b, B)
\]

where `W(a, b, B) ∈ {0, 0.5, 1}` is the showdown outcome and `Z(B)` enforces normalised card-removal. Naively `O(1326²)` ≈ 1.76 M comparisons per board.

### 2.2 Tricks that move it from seconds to milliseconds

1. **Block matrix factorisation.** Decompose ranges into pocket-pair / suited / offsuit blocks; many `1326×1326` interactions vanish by symmetry, leaving ~250 k effective comparisons.
2. **Precomputed showdown table.** For all 7-card combinations of `(a, b, B)` with `|B|=5`, precompute `W` once into a packed lookup. Updating cards: `phevaluator` evaluates the 7-card hand in ~250 ns.
3. **Card-removal via inclusion–exclusion.** Maintain a 52-bit mask of dead cards; reject combos by AND.
4. **FFT-accelerated convolution** for action-frequency-weighted ranges. When mixing strategies (mixed `R = α·R_value + (1-α)·R_bluff`), the resulting equity transform is a convolution of the two distributions over equity buckets — `numpy.fft` evaluates this in ~ms even for fine bucketings.

### 2.3 Pseudocode

```python
def equity_range_vs_range(R_A: np.ndarray, R_B: np.ndarray, board: tuple[int, ...]) -> float:
    """Exact equity of range A vs range B on a fixed flop/turn/river."""
    dead = mask_from_cards(board)
    valid_combos_A = nonzero_combos(R_A, dead)
    valid_combos_B = nonzero_combos(R_B, dead)

    # Precompute equity buckets per combo against board (single 5/6/7-card eval).
    bucket_A = np.array([rank_class(c, board) for c in valid_combos_A])
    bucket_B = np.array([rank_class(c, board) for c in valid_combos_B])

    weight = R_A[valid_combos_A][:, None] * R_B[valid_combos_B][None, :]
    overlap = combo_overlap_matrix(valid_combos_A, valid_combos_B)  # 0 if share a card
    win = (bucket_A[:, None] > bucket_B[None, :]).astype(float)
    tie = (bucket_A[:, None] == bucket_B[None, :]).astype(float) * 0.5

    Z = (weight * overlap).sum()
    return float(((weight * overlap) * (win + tie)).sum() / Z) if Z > 0 else 0.5
```

### 2.4 Use cases unlocked

- Live solver-style **frequency overlays** in the dashboard replayer.
- Fast **EV deltas** for proposed sizings without re-running TexasSolver.
- Inputs to a CFR+ that operates on **continuous** range vectors instead of bucketed abstractions.

### 2.5 Validation

- AA vs random preflop equity: `0.852 ± 1e-3`.
- Two 100-combo ranges on a fixed flop: < 50 ms.
- Cache hit re-runs: < 1 ms.

---

## 3. Solver-distilled student — TexasSolver as your overnight teacher

**Where:** Phase 7.
**Status:** **Shipped** in `poker_ai/` (`solve grid`, `train student`, `DistilledPolicy`). Industry products (GTO Wizard) have done this internally for years; this repo packages it for the open community with AGPL-aware caching and HHFormer-conditioned students.

### 3.1 The pipeline

```
TexasSolver (offline)  →  parquet cache (boards × trees × ranges)  →  student transformer
        ↑                                                                        ↓
   curated grid                                                       online inference < 10 ms
```

### 3.2 Curated grid

Pick 10 k spots that cover:

- 6 board textures × 5 SPR buckets × 6 positions × 3 stack depths × 4 sizing trees.
- Curated preflop ranges (RFI / 3-bet / 4-bet / call) from the heuristic policy.

Run TexasSolver overnight; emit `(state_features, action_frequencies)` rows.

### 3.3 Student head on HHFormer

```python
class StudentHead(nn.Module):
    def __init__(self, dim=256, n_actions=5):
        super().__init__()
        self.mlp = nn.Sequential(nn.Linear(dim, 512), nn.GELU(), nn.Linear(512, n_actions))

    def forward(self, hhformer_cls, state_extras):
        # state_extras: position one-hot, SPR bucket, board texture, sizing tree id
        x = torch.cat([hhformer_cls, state_extras], dim=-1)
        return torch.softmax(self.mlp(x), dim=-1)
```

Train via behavioral cloning on the cached parquet (`MSE` on frequencies, `KL` on log-probs). Optional LoRA fine-tune of HHFormer.

### 3.4 Why this is clever and ethical

- **Local + offline**: TexasSolver runs once on your machine; the student carries the value forever.
- **AGPL respected**: outputs derived from TexasSolver are noted in the model card; students should not be redistributed without complying with AGPL on the *teacher* artifacts.
- **Inference speed**: < 10 ms per call — fast enough for a live dashboard or a sim.

### 3.5 Validation

- 1 000 random spots: student MSE on frequencies ≤ 0.05 vs. teacher.
- Inference latency p99 < 10 ms on a CPU.
- Distilled policy beats the heuristic baseline by ≥ 15 BB/100 over 10 k hands of league play.

---

## 4. Style embeddings via contrastive learning

**Where:** Phase 8.
**Status:** Most poker AI uses VPIP/PFR/AF as opponent features (low-dimensional, stat-based). A **learned dense opponent embedding** trained contrastively is closer to modern recommender / search systems and is novel for poker.

### 4.1 The trick

For each opponent we maintain windows of recent actions. Train a small encoder so that **two windows from the same player** map close in embedding space, while **windows from different players** are pushed apart (SimCLR-style InfoNCE loss).

### 4.2 Sketch

```python
def style_loss(embeds_a, embeds_b, temperature=0.07):
    """SimCLR loss: same-player pairs are diagonal; different-player are off-diagonal."""
    z = nn.functional.normalize(torch.cat([embeds_a, embeds_b], dim=0), dim=1)
    logits = (z @ z.T) / temperature
    n = embeds_a.size(0)
    targets = torch.cat([torch.arange(n, 2*n), torch.arange(0, n)]).to(z.device)
    return nn.functional.cross_entropy(logits, targets)
```

The encoder is a small transformer over `(player_uid, last_K_actions)`; it shares the HHFormer tokenizer and embedding table.

### 4.3 What you can do with it

- **Live exploitation**: cross-attention from the policy net into the opponents’ style vectors at the decision time, smoothly interpolating between GTO (mean vector) and exploit (specific opponent).
- **Player retrieval**: kNN search over a 64-dim space gives "show me opponents like this fish from last Tuesday".
- **Drift signal**: a player whose style vector moves > δ between months has changed their game.

### 4.4 Validation

- kNN over style embeddings retrieves the same `player_uid` from a held-out window with > 60 % top-5 accuracy.
- Exploit policy beats the GTO baseline by ≥ 5 BB/100 against scripted exploitable opponents under AIVAT.

---

## 5. Local self-play league — AlphaStar mechanics on a laptop

**Where:** Phase 9.
**Status:** Cluster-scale leagues are well-known (AlphaStar, OpenAI Five). A **local, AIVAT-accelerated league** that meaningfully improves a poker agent on a single machine is uncommon.

### 5.1 Population slots

| Slot | Goal | Update cadence |
|------|------|----------------|
| `main_agent` | The headline player; we want this to improve. | Trained every cycle. |
| `main_exploiter` | Trained to **beat the current main**. | Resets every N cycles. |
| `league_exploiter` | Trained to **beat any historic checkpoint**. | Continuous. |
| `frozen_baselines` | Random, always-call, TAG, calling station, maniac. | Static. |

### 5.2 Match scheduling

Round-robin with priority: pairings that resolve uncertainty about Elo / AIVAT EV first. AIVAT-corrected results require ~10× fewer hands than naive Monte Carlo for the same significance.

### 5.3 Promotion gate

A new `main_agent` checkpoint is promoted only if:

1. `AIVAT_EV(new vs old) > 0` with `p < 0.05` over `≥ 1 000` hands.
2. `Elo(new) ≥ Elo(old) + 25`.
3. New beats every `frozen_baseline`.

If any check fails, rollback (`poker_ai models rollback main_agent`).

### 5.4 Why this works locally

- 1 000 hands of self-play take a few seconds with the distilled student (§3).
- AIVAT (§7 of [OBSERVABILITY.md](OBSERVABILITY.md)) collapses the variance.
- Models are tiny; whole population fits in RAM.

---

## 6. Bayesian Online Changepoint Detection (BOCPD) for opponent regimes

**Where:** Phase 11.
**Status:** Standard algorithm in time-series; **novel application** to live poker exploitation.

### 6.1 Why

A single VPIP number averages over a player who was tight in the morning and on tilt at night. BOCPD detects **regime changes** in the action distribution as they happen. The dashboard then shows a timeline like:

```
2026-05-10 14:00–17:00  TAG (VPIP 22%, PFR 18%)
2026-05-10 17:01–17:43  TILT (VPIP 41%, PFR 9%)   ← regime change
2026-05-10 17:44–19:00  TAG-RETURN (VPIP 24%, PFR 19%)
```

### 6.2 Algorithm

Adams & MacKay (2007) BOCPD: track a posterior over **run length** `r_t` (time since last changepoint); update with the predictive probability of the new observation under the assumed model (a Dirichlet-categorical for action distributions works well).

### 6.3 Sketch

```python
def bocpd_update(P, hazard, x_t, model):
    """
    P: P(r_{t-1} = i) for i in 0..t-1
    hazard: P(changepoint at t | run length)  (constant 1/τ is fine)
    x_t: observation at t (action category)
    model: posterior predictive p(x_t | r_{t-1})
    """
    growth = P * model.predict(x_t) * (1 - hazard)
    cp = (P * model.predict(x_t) * hazard).sum()
    P_new = np.concatenate([[cp], growth])
    P_new /= P_new.sum()
    model.update(x_t)
    return P_new
```

Run one BOCPD per `player_uid`. Threshold the posterior probability of `r_t = 0` to flag a regime change in real time.

### 6.4 What it changes

- Exploit policy gets a **fresh opponent embedding** when BOCPD signals a changepoint.
- Drift dashboard alerts on **regime instability** in the player pool.

---

## 7. Symbolic explanation engine — auditable, no LLM

**Where:** Phase 10.
**Status:** Most “explainable AI” for poker is either (a) a giant LLM hallucinating reasons, or (b) a one-line solver frequency. We do **deterministic, structured** explanations.

### 7.1 The contract

Every `Policy.propose(state)` is paired with `Policy.explain(state, decision) → str`. The string is generated by **template lookup** keyed by `(position, SPR_bucket, board_texture, action_bucket)`.

### 7.2 Example template

```yaml
# explain/templates/btn_open.yaml
match:
  position: BTN
  street: preflop
  action_bucket: open_raise_2_5x
  spr_bucket: deep
template: |
  BTN open {sizing} is GTO frequency {freq:.2f} over the top {range_pct}% of hands.
  SPR {spr:.1f} favors raise sizes ≤ pot; board not yet dealt.
  Recommendation: {recommendation}.
```

The engine fills `{sizing}, {freq}, {range_pct}, {spr}, {recommendation}` from the actual decision.

### 7.3 Why we do this

- **Auditable** — every explanation can be traced to a YAML rule.
- **No hallucination** — there is no generative model in the loop.
- **Fast** — sub-millisecond.
- **Compliance-friendly** — see [SECURITY_AND_COMPLIANCE.md](SECURITY_AND_COMPLIANCE.md) §3.3 (technical documentation under the EU AI Act).

### 7.4 Coverage

Templates are **unit-tested**: every `(position, SPR, action)` combination must match exactly one template; if not, the test fails and asks for a new template.

---

## 8. Differentiable depth-limited re-solver — DeepStack-lite

**Where:** Phase 13 (research extension).
**Status:** Local re-solving is well known (DeepStack, Libratus). A **packaged, differentiable, opt-in** re-solver triggered by `thinking_ms > 0` on a `Policy` call is rare in open source.

### 8.1 Sketch

```
state, opponent_styles  →  build small subgame tree  →  CFR+ for thinking_ms
                                                             ↓
                                                      leaf values from value_net
```

The subgame is bounded by depth (e.g. 1–2 streets ahead), bet sizes are restricted to the abstraction, and leaf values come from a small **value net** trained on solver outputs (the same teacher as §3).

### 8.2 Why differentiable

If the engine and the value net are both differentiable, the entire re-solve can be backpropagated through during training — useful for **policy distillation with subgame supervision**.

### 8.3 The user-facing knob

`thinking_ms` is exposed in the API:

```python
client.decide(state, profile_id="gto", thinking_ms=50)  # spend up to 50 ms re-solving
```

---

## 9. Conservative offline RL on logged hands (CQL)

**Where:** Phase 13.
**Status:** Behavioral cloning is the default for offline poker; **CQL** ([Kumar et al., 2020](https://arxiv.org/abs/2006.04779)) is rare for poker.

### 9.1 Why CQL

Naive offline RL on logged hands over-estimates the value of **out-of-distribution actions** (we never see what would have happened if we 3-bet, only what happened when we called). CQL adds a regulariser that pushes Q-values for OOD actions **down**, so the learned policy stays close to the data manifold.

### 9.2 Loss

\[
\mathcal{L}_{CQL}(\theta) = \alpha \,\Big( \mathbb{E}_{s \sim \mathcal{D}}[\log \sum_a \exp Q_\theta(s,a)] - \mathbb{E}_{(s,a) \sim \mathcal{D}}[Q_\theta(s,a)] \Big) + \mathcal{L}_{TD}(\theta)
\]

`α` controls conservatism. Rest is standard TD on the Bellman target.

### 9.3 What it gives us

A policy net trained from logs alone (no self-play needed) that **beats behavioral cloning** on AIVAT-corrected EV. Cheap to run; no league required.

---

## 10. Decision-time compute scaling

**Where:** Phase 13.
**Status:** Popular in 2025–2026 reasoning systems (chain-of-thought + tool use); applied to poker policies here.

### 10.1 The idea

Same model, three knobs:

| `thinking_ms` | What runs |
|--------------|-----------|
| 0 | Distilled student only (~ 1 ms). |
| 10–50 | Student + tiny depth-limited re-solver (§8). |
| 100+ | Full subgame solve over the bet abstraction. |

A user (or an automated process) can **trade latency for accuracy** at runtime, without any retraining.

### 10.2 Why it’s clever for poker

It cleanly bridges the offline (solver) and online (heuristic / student) worlds: when the spot is a routine open-raise, no thinking needed; when it’s a critical river decision, spend 100 ms re-solving locally.

---

## 11. Differentiable game engine

**Where:** Phase 2 (engine), exploited in Phase 13.
**Status:** A few research codebases (e.g. DiffStone) have toyed with differentiable game engines; **packaging** one inside a serious NLH product is rare.

### 11.1 Sketch

`engine.step(state, action)` accepts `Tensor` arguments for stack sizes, pot, and bet amounts. Outcomes (chips won/lost) are differentiable wrt these tensors. Hand evaluation is a non-differentiable lookup, so we **stop the gradient** at evaluation boundaries — but everything around it (sizing, betting tree exploration) is gradient-friendly.

### 11.2 What it unlocks

- **End-to-end policy gradient** on a small abstracted tree.
- **Sizing optimisation**: differentiate EV wrt the chosen bet amount in a fixed range.
- **Calibration**: differentiate AIVAT-style estimators wrt baseline parameters.

---

## 12. Putting the levers together

The strongest combination, for a solo developer aiming at a unique product:

```
Phase 5  HHFormer (foundation)
   ↓
Phase 7  Solver-distilled student head    ← the headline policy
   ↓
Phase 8  Style embeddings + cross-attention conditioning
   ↓
Phase 9  Local self-play league with AIVAT-gated promotions
   ↓
Phase 11 BOCPD + drift detection on the live pool
   ↓
Phase 13 Differentiable depth-limited re-solver via thinking_ms
```

This stack is:

- **Owned** end-to-end (no external AI).
- **Local** end-to-end (one workstation).
- **Auditable** end-to-end (templates, model cards, model registry).
- **New** in combination — no public open-source NLH AI we know of brings these levers together with this discipline.

That is the unique position the project occupies, and the technical case for building it from 0 to hero.

---

## 13. References

- HHFormer-style pretraining inspirations: [BERT](https://arxiv.org/abs/1810.04805), [SoundStream / W2v-BERT](https://arxiv.org/abs/2108.06209), [TabTransformer](https://arxiv.org/abs/2012.06678).
- Range-aware solver math: [Brown & Sandholm, *Libratus*, Science 2018](https://www.science.org/doi/10.1126/science.aao1733).
- Distillation lineage: [Hinton et al., *Distilling the Knowledge in a Neural Network*, 2015](https://arxiv.org/abs/1503.02531).
- Contrastive embeddings: [Chen et al., *SimCLR*, 2020](https://arxiv.org/abs/2002.05709).
- AlphaStar league: [Vinyals et al., *Nature*, 2019](https://www.nature.com/articles/s41586-019-1724-z).
- BOCPD: [Adams & MacKay, 2007](https://arxiv.org/abs/0710.3742).
- DeepStack continual re-solving: [Moravčík et al., *Science*, 2017](https://www.science.org/doi/10.1126/science.aam6960).
- CQL offline RL: [Kumar et al., 2020](https://arxiv.org/abs/2006.04779).

See also: [ROADMAP.md](ROADMAP.md), [POKER_AI_BLUEPRINT.md](POKER_AI_BLUEPRINT.md), [GTO_THEORY_AND_SOLVERS.md](GTO_THEORY_AND_SOLVERS.md), [SELF_LEARNING_AND_RESEARCH.md](SELF_LEARNING_AND_RESEARCH.md).
