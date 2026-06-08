# Security and compliance — operating a poker AI responsibly

Poker AI is **dual-use**: legitimate as a study tool, sim engine, and analytics platform; problematic if pointed at live real-money tables on third-party clients. This file is the **professional baseline** for what to do (and not do) so the project remains useful, lawful, and shippable in 2025–2027.

This is **engineering guidance**, not legal advice. For anything in production, get a lawyer in your jurisdiction to sign off.

---

## 1. Threat model — what you are protecting

| Asset | Concern |
|-------|---------|
| **Hand history files** | Contain **personal data** (player nicknames, IPs in some site exports, gameplay patterns). |
| **SQLite database** | Aggregates the above plus model outputs; high re-identification risk if leaked. |
| **Trained models** | May leak training-set membership (membership-inference attacks); copyright on training data may apply. |
| **Solver outputs / strategy tables** | Often **derived from copyrighted commercial solvers** if you bridge to PioSOLVER / GTO+. |
| **Selenium scraping credentials / session cookies** | If you ever scrape sites you have an account on. |
| **API keys** for HM2 / GTO Wizard / OpenAI / etc. | Standard secret-handling. |

The hostile actors you should plan for:

1. **Casual data leak** (laptop stolen, repo accidentally pushed public).
2. **Online client integrity** — your tool reading screen state of a third-party real-money client.
3. **Model exfiltration** — someone querying your `apps/api` for free strategies.
4. **Regulatory audit** — EU AI Act / GDPR review on a deployed product.

---

## 2. GDPR & data protection — hand histories *do* contain personal data

Under the EU GDPR (and equivalent UK / Brazil / California regimes), a **player nickname plus playing pattern at a specific stake/time** is personal data because it can re-identify the human. Even if a nickname is a pseudonym, GDPR explicitly covers pseudonymous data.

### 2.1 Practical hardening

| Step | What to do | Where |
|------|-----------|-------|
| Pseudonymize on import | Hash nickname + room salt → opaque `player_uid`. Keep nickname only in a separate, encrypted lookup table. | `convert/filter.py` and `db/poker_hand_analysis.py` parser. |
| Drop sensitive header fields | Many sites embed `IP/country/city` or table name + handle. Strip these before SQLite ingest. | New `convert/redact.py`. |
| Encrypt the DB at rest | Use [SQLCipher](https://www.zetetic.net/sqlcipher/) (drop-in encrypted SQLite) or full-disk encryption. | DB layer. |
| Right to erasure | Provide a CLI / endpoint that deletes all rows for a `player_uid`. | `apps/api/routes/privacy.py`. |
| Data retention policy | Default: keep raw `hand/*.txt` ≤ 6 months unless explicitly archived. | Doc + cron. |
| Lawful basis | If you ever process other people’s hands (not your own), document the basis (typically *legitimate interest* + opt-out). | `PRIVACY_NOTICE.md` (committed). |

### 2.2 What never to commit to git

```
*.txt under hand/        # real player names + game logs
db/poker.db              # the production DB
.env                     # any credentials or paths to the above
artifacts/*.pt           # trained weights from real data (membership-inference)
```

Adopt this `.gitignore` baseline:

```
hand/
db/poker.db
*.db
*.db-wal
*.db-shm
.env
.env.*
artifacts/
secrets/
.secrets.baseline
*.pem
```

For test fixtures, use **synthetic** hand files with placeholder nicknames (`Player1`, `Player2`, …). See [TESTING_AND_QA.md](TESTING_AND_QA.md) §5.

### 2.3 Subject-access requests (SARs)

If anyone whose hand histories you store asks "what do you have on me?", be ready to:

1. Look up by `player_uid` (after the hash/salt step).
2. Export every row across `Players`, `Actions`, `Results`, `Exploitability`, `Bankroll_Tracking`, `Opponent_Profiles`, `Bot_Performance` for that `player_uid`.
3. Optionally fulfill a deletion request.

A simple SQL view is enough:

```sql
CREATE VIEW v_personal_data_export AS
SELECT 'Players'         AS source, * FROM Players          WHERE player_uid = :uid
UNION ALL SELECT 'Actions', * FROM Actions                  WHERE player_uid = :uid
-- repeat per table
;
```

---

### 2.4 PHH bulk corpus — licence and ingest attestation

The optional **`hand/poker-hand-histories/`** tree (PHH/PHHS) is **not** bundled with the installer. Operators who import it must:

1. Confirm **lawful basis** to store and process the corpus (licence, research exemption, or own data).
2. Complete the checklist in [poker_ai/docs/PHH_CORPUS_POLICY.md](../poker_ai/docs/PHH_CORPUS_POLICY.md).
3. Save a signed attestation to `poker_ai/reports/phh_ingest_attestation.json` (gitignored).
4. Set policy env vars (`POKER_AI_PHH_CASH_ONLY`, `POKER_AI_PHH_EXCLUDE_PATHS`, …) before bulk ingest.

Parser filters (`corpus_policy.py`) are **technical** gates only — they do **not** replace legal review.

---

## 3. EU AI Act (Regulation 2024/1689) — what changes in August 2026

The EU AI Act entered into force on **1 August 2024** with a phased rollout:

| Date | Milestone |
|------|-----------|
| 2 February 2025 | Article 5 prohibitions (manipulative AI, social scoring) applicable. |
| 2 August 2025 | Governance + GPAI obligations applicable. |
| **2 August 2026** | **High-risk AI system obligations applicable** (technical documentation, data governance, transparency, human oversight, conformity assessment). |
| 2 August 2027 | Final transitional rules expire. |

### 3.1 Where this codebase touches the Act

A **pure analysis tool** for owned hand histories is generally **outside** Annex III’s high-risk categories. But if you build any of the below into a deployable product, you may step into the high-risk regime:

- **Behavioural risk scoring** (e.g. labelling players as “problem gamblers”) → close to Annex III §8 (essential services / credit). Treat as high-risk by default.
- **Automated account decisions** (suspension, KYC) → likely high-risk.
- **Real-time advisor in a regulated gambling product** → could trigger transparency obligations under Article 50.

### 3.2 Article 5 “red lines” — never build these

- **Subliminal manipulation** beyond a person’s consciousness.
- **Exploiting cognitive vulnerabilities** of specific groups (age, disability, addiction).
- AI that "deceives" a person into believing they’re interacting with another human in a real-money setting without disclosure.

A bot that plays real-money cash poker against a human who **doesn’t know** it’s a bot is well into this territory. Always disclose AI participation in any deployed product.

### 3.3 Transparency & documentation baseline

Even if you’re below the high-risk threshold, the Act and its national implementations create a strong norm of **technical documentation** (Annex IV). Mirror it locally in this repo:

- A **model card** per shipped model (`artifacts/<name>/MODEL_CARD.md`):
  - Intended use, limitations, training data summary, evaluation metrics, fairness checks.
- A **product datasheet** for the application (`doc/DATASHEET.md`) — rendered in the dashboard at **`/datasheet`** (`GET /compliance/datasheet/content`); user-supplied import data only; no bundled training corpus in the installer.
- Optional **dataset datasheet** per hand-history corpus you import yourself (provenance, consent basis, redactions).
- A **conformance log** (`compliance/CHANGES.md`) when you change anything that touches user data.

Templates: [Hugging Face model card spec](https://huggingface.co/docs/hub/model-cards), [Datasheets for Datasets (Gebru et al., 2018)](https://arxiv.org/abs/1803.09010).

---

## 4. Online gambling regulation context (2026)

The 2026 picture, in three sentences:

1. **EU AI Act + GDPR + national gambling regulators** form a triple stack; large operators are already mapping AI features to high-risk categories.
2. AI used for **identity, fraud, payments, problem-gambling detection** is likely high-risk → conformity assessment required by 2026-08-02.
3. Operators are **liable even when the AI comes from a third-party vendor** — i.e. if you sell or license this stack to an operator, contractual indemnities and a "shared responsibility" model are non-negotiable.

References:
- [Lexology — Legal obligations for online gambling operators using AI](https://www.lexology.com/library/detail.aspx?g=f7da836c-e0af-427d-94bf-f1780a1bb309)
- [GamingMarkets — How the EU AI Act is reshaping the global gambling industry in 2026](https://gamingmarkets.com/eu-ai-act-global-gambling-industry-2026/)
- [Chapter III — High Risk AI Systems (EU AI Act)](https://www.euaiact.com/title/3)

---

## 5. Online client / Terms-of-Service risk

Most poker rooms (PokerStars, GGPoker, …) have **Terms of Service that prohibit**:

- Real-time assistance (RTA) by software during play.
- Multi-tabling automation, screen-scraping, or DLL injection.
- Sharing hand histories of *other* players in some jurisdictions.

What this means in practice:

- **You can analyze your own** downloaded HHs after the session — that is what HM2 / PT4 do.
- **You cannot run a live "decide()" assistant** that talks to a third-party real-money client without breaking ToS and (potentially) the law.
- **You should not document** circumvention techniques in this repo. If a feature description starts to read like “how to evade detection at room X”, it should be cut or moved to a private fork.

The product scope of this repo is **owned data + simulator + analysis**. Keep it that way.

---

## 6. Hand-history copyright and IP

| Source | Realistic stance |
|--------|------------------|
| Your own downloaded HHs | Yours to analyze; redistribution often constrained by site ToS. |
| HH databases shared online | Treat as low-trust, possibly unlicensed; avoid as training data unless provenance is clear. |
| Solver-generated strategy tables (Pio/GTO+/Monker) | Subject to the **vendor’s license**. Redistributing exported strategies is usually prohibited. |
| Open Hand History (OHH) example files | Permissive license per [hh-specs.handhistory.org](https://hh-specs.handhistory.org/). |
| TexasSolver outputs | TexasSolver is **AGPL-3.0** — derivative works that incorporate the binary or source must comply. Check before bundling. |

### 6.1 Output classification you should keep

For every model you train, log in the model card:

- Sources of training data (paths, dates, hash of fixed snapshot).
- License for each source.
- Whether outputs are intended for **private analysis only** (`internal-only`), **embedded in a deliverable** (`shipped`), or **redistributed** (`public`).

---

## 7. Secrets and credentials

Even today the repo doesn’t store credentials, but this is the right place to lock that in.

### 7.1 Never commit secrets

Adopt [`detect-secrets`](https://github.com/Yelp/detect-secrets) or [`gitleaks`](https://github.com/gitleaks/gitleaks) as a pre-commit hook:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks: [{ id: detect-secrets }]
```

### 7.2 Secret hierarchy

| Tier | Where | Examples |
|------|-------|----------|
| Local dev | `.env` (gitignored) | `DATABASE_URL`, `SCRAPE_BASE_URL`. |
| Shared dev | OS keychain or a 1Password / Bitwarden vault. | HM2 read-only Postgres user. |
| Prod / cloud | Cloud secret manager (AWS SM, GCP Secret Manager, HashiCorp Vault). | API keys, SQLCipher passphrase. |

### 7.3 Pydantic settings pattern

Use `pydantic-settings` to load `os.environ` and `.env` into a typed object. The schema itself is documented in [DASHBOARD_AND_INTEGRATIONS.md](DASHBOARD_AND_INTEGRATIONS.md).

---

## 8. API security (when `apps/api` exists)

Once FastAPI is exposed beyond `localhost`:

| Control | Library / approach |
|---------|--------------------|
| **Auth** | OAuth2 / OIDC via [Authlib](https://docs.authlib.org/) or proxy via Cloudflare Access / Tailscale Funnel. |
| **Rate limit** | [`slowapi`](https://github.com/laurentS/slowapi) middleware; per-IP and per-token. |
| **CSRF / CORS** | Pin allowed origins in `Settings.API_CORS_ORIGINS`; disable wildcard. |
| **Input validation** | Pydantic models with strict types; never accept raw SQL via query strings. |
| **Output filtering** | Strip personal data fields from responses unless caller has the `pii:read` scope. |
| **Audit log** | Append-only table or a separate write-only DB recording `(user_id, endpoint, params_hash, ts)`. |
| **Dependency scanning** | `pip-audit`, `safety`, GitHub Dependabot. |

---

## 9. Anti-bot measures for **your** service

If you run `apps/api`, you don’t want others scraping it. Layer:

1. Per-token rate limit (`slowapi`).
2. CAPTCHA on signup if user-facing.
3. Honeypot endpoints + alerting via [OBSERVABILITY.md](OBSERVABILITY.md).
4. Block known datacenter IP ranges from the public web UI (`fail2ban` or upstream WAF).

This is "anti-bot for **your** service" — orthogonal to *playing* poker bots.

---

## 10. Compliance checklist (review every quarter)

- [ ] No `.env`, `*.db`, `hand/`, or weights in the git index.
- [ ] `pre-commit run --all-files` passes (ruff, gitleaks, detect-secrets, mypy).
- [x] Every shipped model artifact has a `MODEL_CARD.md` (see `GET /models/{name}/card` and `doc/DATASHEET.md` table).
- [x] Product `doc/DATASHEET.md` published; per-corpus datasheets optional for operator-imported trees.
- [ ] Privacy notice mentions retention period and erasure path.
- [ ] If exposing to EU users — DPIA (Data Protection Impact Assessment) on file.
- [ ] CI runs `pip-audit` and fails on high-severity CVEs.
- [ ] Terms of service for the deployed app prohibit using outputs to power any **real-time assistant on third-party clients**.

---

## 11. References

- [GDPR text — EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj)
- [EU AI Act (Regulation 2024/1689)](https://eur-lex.europa.eu/eli/reg/2024/1689/oj)
- [EU AI Act — high-risk Annex III](https://www.euaiact.com/annex/3)
- [Datasheets for Datasets (Gebru et al.)](https://arxiv.org/abs/1803.09010)
- [Hugging Face Model Cards](https://huggingface.co/docs/hub/model-cards)
- [SQLCipher — encrypted SQLite](https://www.zetetic.net/sqlcipher/)

See also: [DASHBOARD_AND_INTEGRATIONS.md](DASHBOARD_AND_INTEGRATIONS.md) §“Compliance reminder”, [PRODUCT_SPEC.md](PRODUCT_SPEC.md) §“Compliance / antibot”, [OBSERVABILITY.md](OBSERVABILITY.md) §“Audit logs”.
