# Hand history sources and file types (beyond `hand/*.txt`)

Your repo today ingests **normalized plain text** after `convert/` (see `db/poker_hand_analysis.py`). In the wild, NLH hands arrive in **many containers**; a universal instrument should **normalize everything to one internal model** (your `Games` / `Players` / `Hands` / `Actions` / `Results` or a future **Open Hand History** layer).

---

## 1. Plain text (`.txt`) — primary interchange

| Variant | Typical use |
|---------|-------------|
| **PokerStars-style** block text | PokerStars, Chico, many skins; de facto standard for trackers. |
| **Site-specific text** | GGPoker (often **`.txt`** inside a downloaded **`.zip`** from PokerCraft), 888, Party, WPN, etc. — same *idea* (line-based log), different headers/parsing rules. |
| **Extensionless `HHyyyymmdd`** | Reported for some **PokerStars** installs (one file per day). **PokerTracker** import docs often expect **`.txt`** for recognition — you may **rename** or symlink to `.txt` for PT4-style tools. |

**HM2 export:** FAQ states exported hands are **`.txt`** (from Database Manager filters or right-click export). Same for many “export for replayer” workflows.

**Practical rule:** treat ingest as **“text / UTF-8”** first; file extension is a hint, not the parser.

---

## 2. HTML / email / clipboard

| Variant | Notes |
|---------|--------|
| **HTML with `<br />`, suit `<img>`** | Your `convert/convert.py` already targets this: split on `<br />`, strip tags, map suits. |
| **Email bodies** | Same HTML or text; PT4 has “import from email” flows for some rooms — content is still text/HTML underneath. |

---

## 3. Archives (`.zip`, `.gz`, …)

Rooms (e.g. **GGPoker** downloads) ship **compressed folders of `.txt`**. Universal ingest should:

1. Expand archive to a temp dir.  
2. Walk all `*.txt` (and optionally extensionless `HH*` files).  
3. Run **room detector** → correct parser.

---

## 4. XML

Some networks ship or shipped **XML** hand logs (forum threads discuss **PokerTracker** and XML specs for certain providers). **HM2** discussions mention **iPoker**-style originals as XML in import contexts.

**Approach:** small `ingest/xml/` parser per network, output same canonical rows as text parser.

---

## 5. JSON — especially **Open Hand History (OHH)**

There is a community **Open Hand History** specification for structured hands (JSON), with examples for PokerStars-style cash games:

- [Open Hand History — overview](https://hh-specs.handhistory.org/)
- [Example: Hold’em cash (PokerStars)](https://hh-specs.handhistory.org/examples/holdem-cash-hand-pokerstars)

**Why support JSON:** stable schema for APIs, converters, and ML pipelines without regex fragility.

**Approach:** optional path `ingest/ohh/` — map OHH JSON → your SQLite schema (or store raw JSON in a `hands_raw` blob column + parsed flag).

Libraries/tools in the ecosystem (for research; verify licenses and maintenance before depending on them):

- [PokerHistoryParser](https://pkrhistoryparser.readthedocs.io/) — Python, some site coverage, JSON output.  
- [Open Hand History (ohh)](https://github.com/homanp/ohh) — TypeScript reference implementation.  
- [poker-log-parser](https://pypi.org/project/poker-log-parser/) — multi-site text → structured / OHH-related output.

---

## 6. Not “files” — tracker databases

| System | Storage | How to “use all” |
|--------|---------|------------------|
| **HM2** | Local **PostgreSQL** | Read-only SQL adapter → canonical tables (see [DASHBOARD_AND_INTEGRATIONS.md](DASHBOARD_AND_INTEGRATIONS.md)). |
| **HM3 / PT4** | Postgres / SQLite variants | Same adapter idea; **schema differs** — versioned mappers. |
| **Hand2Note**, etc. | Proprietary / SQL | Export to **text/JSON** when no stable SQL contract. |

---

## 7. Recommended ingest architecture (future)

```
ingest/
  detectors/     # sniff site from first lines or JSON `gameNumber`
  parsers/
    pokerstars_text.py
    gg_text.py
    ohh_json.py
    hm2_sql.py
  normalize/     # → HandRecord (internal) → SQLite upsert
```

**“Use all”** means: **one `HandRecord`**, many front-door parsers, same DB and same downstream **GTO / exploitability / bots**.

---

## 8. Mapping to this repository today

| Source | Today | Next step |
|--------|--------|-----------|
| Your **`hand/5` .txt** | `poker_hand_analysis.parse_hand_file` | Golden tests per site. |
| HM2 **exported .txt** | Same pipeline after path config | None if format matches. |
| HM2 **Postgres** | Not in `poker_ai/` | Future HM2 integration (not current Phase 6 scope). |
| **JSON / OHH** | Not implemented | Add `ingest/ohh` + tests. |
| **ZIP bundles** | Not implemented | Pre-step before `filter.py`. |

---

## References (external)

- [PokerTracker 4 — importing hand histories](https://www.pokertracker.com/guides/PT4/tutorials/importing-hand-histories)  
- [HM2 FAQ — how are hands exported?](http://hm2faq.holdemmanager.com/questions/1461/How+to+export+hands)  
- [Open Hand History specs](https://hh-specs.handhistory.org/)
