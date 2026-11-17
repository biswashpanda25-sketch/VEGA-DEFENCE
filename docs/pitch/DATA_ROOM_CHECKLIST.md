# Data room checklist

**Status as of November 2026.** This list is deliberately published with the gaps visible. An investor who finds a
missing item in this file has confirmed what we told them; an investor who finds a missing item during diligence has
found something we concealed.

Status key: **HAVE** · **PARTIAL** (exists, not investor-grade) · **MISSING** (must be created before a term sheet)
· **N/A** (does not apply yet, with reason).

---

## 1. Pitch pack itself

| Item | Status | Location / action |
|---|---|---|
| Pitch deck, 21 slides | **HAVE** | `pitch/GOTHAM_INDIA_PreSeed_Deck.pptx` (+ PDF in `pitch/render/`) |
| Financial model, 9 sheets, live formulas | **HAVE** | `pitch/GOTHAM_INDIA_Financial_Model.xlsx` |
| Every external figure with URL and date | **HAVE** | `docs/pitch/SOURCES.md` |
| Investor FAQ, 42 questions | **HAVE** | `docs/pitch/INVESTOR_FAQ.md` |
| Demo script | **HAVE** | `docs/pitch/DEMO_SCRIPT.md` |
| One-page PDF summary | **HAVE** | `pitch/GOTHAM_INDIA_OnePager.pdf` — slide 2 extracted standalone |

---

## 2. Corporate and legal

| Item | Status | Location / action |
|---|---|---|
| Certificate of incorporation | **MISSING** | Not incorporated. Gate M2 of the plan. **State this before an investor asks.** |
| Articles / MoA | **MISSING** | Draft with counsel in month 1; budgeted in Legal & IP (₹0.25 Cr) |
| PAN, TAN, GST registration | **MISSING** | Follows incorporation |
| DPIIT startup recognition | **MISSING** | Needed for GeM Startup Runway; free, ~48 h, do it the week after incorporation |
| Statutory registers (shareholders, directors) | **MISSING** | Create with incorporation |
| Board / shareholder resolutions | **MISSING** | N/A pre-incorporation; template on file from month 2 |
| Founders' agreement | **MISSING** | Four-year vesting, one-year cliff, reverse vesting on founder shares — sign before the money lands |
| IP assignment deeds from founders | **MISSING** | Must be executed at incorporation; every line of code currently sits with an individual |
| Trademark application | **MISSING** | "GOTHAM INDIA" may be contested; get a clearance search before filing, and be willing to rename |
| ESOP scheme document | **MISSING** | 10% pool is modelled; paperwork at month 2 |
| Advisor agreements | **MISSING** | Equity-for-access advisors, 2-year quarterly vesting |
| Convertible instrument / SAFE template | **MISSING** | Counsel-drafted; investor-friendly version acceptable |

---

## 3. Financial

| Item | Status | Location / action |
|---|---|---|
| Financial model with three scenarios | **HAVE** | `pitch/GOTHAM_INDIA_Financial_Model.xlsx` |
| Use-of-funds reconciliation to the round | **HAVE** | Use of funds rows 17 and 21 must both read `0.00` |
| Cap table with three caps and ESOP | **HAVE** | Cap table sheet — founder split is a placeholder, fill it in |
| Cap table, fully diluted, with instrument terms | **PARTIAL** | Needs the SAFE/equity instrument and the advisor grants in one sheet |
| Bank statements | **MISSING** | No company account yet; personal spend to date is uncapitalised |
| Audited accounts | **N/A** | Pre-revenue, pre-incorporation. First audit at month 6 of operations |
| Spend-to-date log | **MISSING** | Reconstruct from personal accounts now — investors will ask what has been spent and by whom |
| Monthly management accounts template | **MISSING** | Create the tab before month 2, so month 6's audit has a trail |
| Burn and runway tracker, updated monthly | **MISSING** | One page per month: cash in, cash out, closing balance, gate status |
| Tax filings | **N/A** | After incorporation |

---

## 4. Product and engineering

| Item | Status | Location / action |
|---|---|---|
| Source code access (read-only repo invite) | **HAVE** | Given on request; history is the evidence |
| Architecture document | **HAVE** | `docs/ARCHITECTURE.md` |
| API reference | **HAVE** | `docs/API.md`, plus `/api/docs` on a running instance |
| Known issues and limitations | **HAVE** | `docs/KNOWN_ISSUES.md` |
| Capability assessment vs a Gotham-class system | **HAVE** | `docs/ASSESSMENT_VS_GOTHAM.md`, `docs/ROADMAP_TO_60.md` (16.3%, per-area) |
| Test evidence | **HAVE** | `docs/TESTING.md` — 61 backend tests on SQLite and PostgreSQL, 27/27 browser checks |
| Scale evidence | **HAVE** | `docs/SCALE.md`, `docs/scale_results.json`, `docs/scale_endpoint_bench.json` — 1 M rows, p50 per endpoint |
| AI evaluation | **HAVE** | `docs/EVALUATION.md`, `docs/ai_eval_results.json` — recall 1.00, groundedness 0.73, unsupported claims 0.00 |
| Reproducible benchmark scripts | **HAVE** | `backend/tests/scale.py`, `backend/tests/bench_scale.py`, `backend/tests/eval_ai.py` |
| Product screenshots | **HAVE** | `frontend/e2e/screenshots/`, `docs/screenshots/` |
| Live demo environment | **HAVE** | Docker Compose; see `DEMO_SCRIPT.md` §0 |
| Roadmap with dates | **PARTIAL** | `docs/ROADMAP_TO_60.md` has sequencing, not committed dates — do not invent dates |
| Third-party licence inventory (SBOM) | **MISSING** | Generate before the security review; a procurement reviewer will ask |
| Data provenance statement for the demo set | **HAVE** | Every seeded record is labelled `SYNTHETIC-DEMO` (`backend/app/seed.py`) |

---

## 5. Security and compliance

| Item | Status | Location / action |
|---|---|---|
| Security architecture and controls | **HAVE** | `docs/SECURITY.md` |
| Data governance and purpose binding | **HAVE** | `docs/DATA_GOVERNANCE.md` |
| Audit design and hash-chain verification | **HAVE** | `docs/AUDIT.md`, endpoint `GET /api/audit/verify` |
| Operations / incident basics | **HAVE** | `docs/OPERATIONS.md` |
| Threat model | **PARTIAL** | Exists in fragments across `SECURITY.md`; consolidate into one page |
| External penetration test | **MISSING** | Budgeted (₹0.46 Cr line). Gate at month 5. **Do not claim it exists.** |
| ISO 27001 certification | **MISSING** | Budgeted; 9–12 month process. Never implied on a slide |
| CERT-In empanelment | **MISSING** | Preparation starts month 2 |
| STQC / defence accreditation | **MISSING** | Out of scope for this round; iDEX route would trigger it |
| DPDP Act compliance assessment | **MISSING** | Budgeted; requires counsel, not just engineering |
| Incident response runbook | **PARTIAL** | `OPERATIONS.md` covers basics; a regulator will want a named responder and timelines |
| Source-code escrow arrangement | **MISSING** | Asked for by most state buyers; quote it before the first pilot |
| Sub-processor list | **MISSING** | Trivial to produce once hosting is decided |

---

## 6. Market and go-to-market

| Item | Status | Location / action |
|---|---|---|
| Bottom-up market sizing | **HAVE** | Model, Market sheet (₹550 Cr serviceable, ₹12 Cr obtainable) |
| Pricing and unit economics | **HAVE** | Model, Assumptions rows 23–27; slide 9 |
| Competitive landscape (2×2 and comparables) | **HAVE** | Deck slides 10 and 20 |
| Procurement-route memo: GeM Startup Runway, iDEX, state tender thresholds | **MISSING** | Write it — one page, it becomes the GTM playbook |
| Buyer map: OSDMA, Board of Revenue & SRC, district collectors, PSU asset owners | **MISSING** | Names, roles, budget lines; keep it out of the deck, in the room |
| Pipeline tracker | **MISSING** | Empty today. Create before the first meeting so it is not obviously new |
| LOIs / MOUs | **MISSING** | None. Stated on slide 12 |
| Signed contracts | **MISSING** | None. Stated on slide 12 |
| Reference customers | **MISSING** | None. The first pilot creates the first one |
| Case studies | **N/A** | None yet, by definition |

---

## 7. Team

| Item | Status | Location / action |
|---|---|---|
| Founder CVs, one page each | **MISSING** | Must exist before the second meeting; blanks on slide 13 must be filled |
| Role and hiring plan | **HAVE** | Model, Headcount sheet — 11 seats with start months |
| Org chart | **PARTIAL** | Derived from Headcount; draw it once |
| Advisor list and agreements | **MISSING** | Do not list advisors in a deck before they have signed |
| Employment / contractor templates | **MISSING** | Needed month 2 |
| Founder references | **MISSING** | Two each, with permission |

---

## 8. The five things to fix before the first investor meeting

1. **Fill the founder placeholders** on slide 13 and slide 17 (`[FOUNDER NAME]`, `[email]`, `[phone]`) and write the
   one-page CV. A deck with a blank name reads as a hobby project.
2. **Write the one-page procurement-route memo.** It is the single most credible document you can hand a strategic
   investor, and it costs an afternoon.
3. **Reconstruct the spend-to-date log** from personal accounts. "₹X spent by the founder, uncapitalised" is a
   normal pre-seed fact; being unable to produce the number is not.
4. **Run the model's two reconciliation cells** (use of funds rows 17 and 21) and confirm both read `0.00` before
   sending the file.
5. **Delete or date-stamp every unsourced number.** `SOURCES.md` is the whitelist; anything on a slide without a line
   in it should come off.

---

## 9. How the room is structured (once it exists)

```
01_corporate/      incorporation, statutory registers, founder agreements, IP assignment
02_financial/      model, cap table, spend log, bank statements, monthly accounts
03_product/        architecture, API, known issues, screenshots, demo environment notes
04_evidence/       TESTING.md, SCALE.md, EVALUATION.md, benchmark JSON, reproduce commands
05_security/       SECURITY.md, AUDIT.md, DATA_GOVERNANCE.md, pen test, DPDP, escrow
06_commercial/     market model, pricing, procurement memo, buyer map, pipeline
07_team/           CVs, hiring plan, advisor agreements
08_pitch/          deck (pptx + pdf), model, FAQ, sources, demo script, one-pager
```

Naming: `YYYY-MM-DD_<document>_v<n>.pdf`. Every folder gets a `README.md` with one line per file and its date, so an
investor can find anything in under a minute without asking.
