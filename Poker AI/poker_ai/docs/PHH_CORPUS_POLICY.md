# PHH bulk corpus — ops policy and licence checklist

**Audience:** operators ingesting `hand/poker-hand-histories/` (PHH/PHHS trees).  
**Code:** `poker_ai/src/poker_ai/ingest/corpus_policy.py`, `ingest/phh_text.py`.

## What the parser does today

- Walks `**/*.phh` and `**/*.phhs` alongside normalized `hand_*.txt` and OHH JSON.
- Decodes **`variant = 'NT'`** (No-Limit Texas Hold'em in this ecosystem) into the same canonical store.
- Tags rows with `ingest_source = phh` and stable `external_ref` from tree path.
- Optional filters via env (see below).

## Operator policy toggles

| Env var | Effect |
|---------|--------|
| `POKER_AI_PHH_CASH_ONLY=1` | Skip MTT-like paths (`wsop/`, `tournament/`, …) |
| `POKER_AI_PHH_NO_OBFU=1` | Skip obfuscated / HandHQ paths |
| `POKER_AI_PHH_EXCLUDE_PATHS` | Comma fragments; path substring match → skip |
| `POKER_AI_PHH_MIN_TOTAL_ANTE` / `MAX` | Filter by per-hand total antes |
| `POKER_AI_INGEST_MAX_HANDS` / `--max-hands` | Dev slice without full-tree scan |

## Licence and compliance checklist (required before bulk production ingest)

Complete and retain with your deployment records (see [doc/SECURITY_AND_COMPLIANCE.md](../../doc/SECURITY_AND_COMPLIANCE.md) §2.4):

- [ ] **Rights confirmed** — You have permission to store and process the PHH tree for your use case (research, internal analytics, or licence from corpus maintainer).
- [ ] **Redistribution** — You will **not** republish raw PHH files or derived strategy tables built solely from third-party corpora without permission.
- [ ] **Personal data** — Player pseudonyms in PHH are treated as personal data; `player_uid` HMAC salting is enabled (`POKER_AI_PLAYER_UID_HMAC_SECRET`).
- [ ] **Scope** — Document which subtrees are in scope (cash vs MTT) and attach exclude list to `POKER_AI_PHH_EXCLUDE_PATHS` if needed.
- [ ] **Retention** — Raw PHH on disk ≤ 6 months unless archived under your privacy policy.
- [ ] **Attestation** — Operator name, date, and corpus version recorded in `reports/phh_ingest_attestation.json` (template below).

### Attestation template

```json
{
  "operator": "YOUR_ORG",
  "corpus_root": "hand/poker-hand-histories",
  "licence_basis": "research-only | purchased | public-domain | other",
  "licence_reference": "URL or contract id",
  "cash_only": true,
  "exclude_paths": ["wsop/"],
  "signed_at": "2026-06-02",
  "review_due": "2026-12-02"
}
```

Save to `poker_ai/reports/phh_ingest_attestation.json` (gitignored; not committed).

## Related docs

- [doc/ROADMAP.md](../../doc/ROADMAP.md) Phase 1 — bulk PHH policy
- [doc/DATASHEET.md](../../doc/DATASHEET.md) — product datasheet
- [PHASES_0_9_STATUS.md](PHASES_0_9_STATUS.md) — checklist
