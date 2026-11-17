# Sources — every number in the deck, and where it came from

**Pack version:** November 2026 · **Owner:** founder · **Rule:** if a figure appears on a slide or in the model and
is not in this file, it does not go in front of an investor.

Two kinds of numbers are used in this pack, and they must never be mixed up:

| Kind | Marked as | Standard of proof |
|---|---|---|
| **Externally reported** | `EXT` | Published source, dated, URL recorded. Trend direction matters more than the third digit. |
| **Measured on our own machine** | `OWN` | Reproducible command and artefact path in this repository. If it cannot be re-run, it is not cited. |
| **Modelled** | `MODEL` | Derived in `pitch/GOTHAM_INDIA_Financial_Model.xlsx` from an input in this file. |

Where two public sources disagree, both are recorded and the more conservative number is used on the slide.

---

## 1. Policy and mandate (slides 3, 4, 8)

| # | Figure used | Value | Source | URL | Dated | Slide |
|---|---|---|---|---|---|---|
| 1.1 | Disaster Management (Amendment) Act, 2025 | Assent 29 Mar 2025; in force 9 Apr 2025; statutory NCMC and High Level Committee; **National Disaster Database** mandated, states required to maintain their own; SDRF creation enabled; NDRF raised to 16 battalions | `EXT` — Legacy IAS notes, PolicyEdge summary of the Act | legacyias.com · policyedge.in | Act 2025; pages accessed Nov 2026 | 4, 7, 21 |
| 1.2 | State Disaster Response Fund, FY2026 | **₹13,578.80 Cr** allocated to **27 states** | `EXT` — Union Budget FY2025-26 disaster-management allocation summary | policyedge.in | Budget FY26 | 4, 8 |
| 1.3 | National Disaster Response Fund, FY2026 | **₹2,024 Cr** (a second source states ₹2,189 Cr — the lower figure is used) | `EXT` — as 1.2 | policyedge.in | Budget FY26 | 8 |
| 1.4 | State Disaster Mitigation Fund | **₹4,571 Cr** released | `EXT` — as above | policyedge.in | FY26 | 8 |
| 1.5 | National Disaster Mitigation Fund | **₹372 Cr** | `EXT` — as above | policyedge.in | FY26 | — (model only) |
| 1.6 | Defence budget, FY2026-27 | **₹7.85 lakh crore**; **₹1.39 lakh crore** (75% of capital acquisition) reserved for domestic industry | `EXT` — SEAFUND defence-startup landscape | seafund.in/article/defence-startups-in-india/ | FY27 budget | 4, 8 |
| 1.7 | Defence production and exports | FY25-26 production **₹1.78 lakh crore**; exports **₹38,424 Cr** | `EXT` — as 1.6 | seafund.in | FY26 | 8 |

**Interpretation, stated as ours not the source's:** a statutory database mandate plus a funded state line item is the
closest thing to a guaranteed buying trigger in Indian public procurement. The slide says this; the sources above do
not.

---

## 2. Procurement and market (slides 4, 7, 8, 20)

| # | Figure used | Value | Source | URL | Dated | Slide |
|---|---|---|---|---|---|---|
| 2.1 | GeM gross merchandise value, FY26 | **₹5.03 lakh crore**; MSE share ₹2.36 lakh crore (47.1%); **startups just over ₹19,000 crore (<4%)**; only ~10% of recognised startups have ever transacted on GeM | `EXT` — YourStory analysis of GeM FY26 data | yourstory.com/2026/09/india-funds-its-startups-why-wont-buy-from-them | Sep 2026 | 8 |
| 2.2 | The "1% earmark" arithmetic | 1% of ₹5.03 lakh crore ≈ **₹5,000 Cr / yr** — stated on the slide as arithmetic, not as a policy proposal | `MODEL` (simple arithmetic on 2.1) | — | — | 8 |
| 2.3 | GeM Startup Runway | No prior turnover, prior experience or EMD for recognised startups; 10–15 day payment cycles; free DPIIT-startup registration closed in under 48 h | `EXT` — BestStartup.in, DD India coverage of the Runway | beststartup.in · ddindia.co.in | 2025–26 | 4, 7, 15 |
| 2.4 | iDEX funnel | **549** problem statements · **619** startups engaged · **430** development contracts · **45** purchase orders worth **₹2,326 Cr** | `EXT` — Rajwardhan Shinde, *India's defence and security startups* (iDEX/DIO figures); The Reel Stars, Oct 2026 | rajwardhan27.substack.com/p/indias-defence-and-security-startups · thereelstars.com | Oct 2026 | 8, 20 |
| 2.5 | iDEX + ADITI outlay | **₹1,248.78 Cr** | `EXT` — SEAFUND, as 1.6 | seafund.in | 2026 | 4 |
| 2.6 | Research and development scheme | **₹1 lakh crore** RDI scheme announced Jul 2025 | `EXT` — The Reel Stars | thereelstars.com | Jul 2025 | 4 |
| 2.7 | Defence-tech funding in India | Cumulative **$432 Mn+**; ~**71%** in drones and counter-drone; 89% of funded companies use AI | `EXT` — Inc42 data as compiled by SEAFUND | seafund.in | 2026 | 20 |
| 2.8 | Defence-tech funding trend | ₹27 Cr (2016) → ₹1,653 Cr (2025); ₹5,248 Cr across 211 rounds | `EXT` — Rajwardhan Shinde | rajwardhan27.substack.com | 2025 data | 8 |

**Known inconsistency, recorded deliberately.** Public iDEX counts differ: one set reports **430 contracts / 43 purchase
orders**, another **548 development contracts / 45 purchase orders**. The deck uses 619 startups, 430 contracts and 45
purchase orders, and the source line on the slide is dated. If an investor quotes a different set, the answer is: *the
funnel shape is the point, and every published version of it shows the same 10:1 drop from contract to order.*

---

## 3. The comparable (slide 20)

| # | Figure used | Value | Source | URL | Dated | Slide |
|---|---|---|---|---|---|---|
| 3.1 | Palantir revenue, FY2025 | **$4.48 B** total; government **$2.40 B (54%)**; commercial $2.07 B | `EXT` — Mungo Mash financial summary; Stock Analysis on Net | mungomash.com/orgs/palantir/financials/ · stock-analysis-on.net | FY2025 10-K | 20 |
| 3.2 | Palantir revenue, FY2024 | **$2.87 B** | `EXT` — as above | — | FY2024 | 20 |
| 3.3 | Palantir headcount and R&D | **4,429** employees; R&D ~12% of revenue | `EXT` — as above | — | FY2025 | 20 |
| 3.4 | Palantir market capitalisation | **~$354 B**; ~112× 2026 earnings | `EXT` — Trefis | trefis.com | 2026 | 20 |
| 3.5 | Growth rates quoted in conversation, not on the slide | US commercial +137% YoY (Q4-25); US government +55% (2025) | `EXT` — Trefis | trefis.com | 2026 | — |

**What we do not claim:** no commercial relationship, partnership, reseller agreement or endorsement from Palantir
exists. The comparison is a capability and category comparison only. Slide 21 states this in the product's own words.

---

## 4. Measured on our own machine (`OWN`)

These are the only numbers in the pack that are ours. Each is reproducible with the command shown.

| # | Figure used | Value | Artefact | Reproduce |
|---|---|---|---|---|
| 4.1 | Capability index vs Gotham-class system | **16.3%** (was 7.2% before Phase A/B) | `docs/ROADMAP_TO_60.md` §1, `docs/RELEASE_NOTES.md` | read, not re-runnable — it is a self-assessment |
| 4.2 | Test suite | **61 passed in 19.4 s** (SQLite) and **61 passed in 20.8 s** (PostgreSQL 17 + PostGIS); **27/27** Playwright browser checks | `docs/TESTING.md` | `cd backend && python -m pytest tests -q` |
| 4.3 | Latency at 1 M rows (p50) | spatial KNN **1.05 ms** · entity list **0.14 ms** · universal search **28.4 ms** · AI answer **59.4 ms** · tenant overview **504 ms** | `docs/SCALE.md`, `docs/scale_results.json`, `docs/scale_endpoint_bench.json` | `python -m tests.scale --rows 1000000` then `python -m tests.bench_scale` |
| 4.4 | Ingest and index | **39,000 rows/sec**; index build **14 s**; graph traversal exercised at **300,000 edges** | `docs/SCALE.md`, `docs/benchmark_results.json` | `backend/tests/bench_scale.py` |
| 4.5 | AI grounding evaluation | Refusal-on-unsupported-answer behaviour measured per test case | `docs/EVALUATION.md`, `docs/ai_eval_results.json` | `python -m tests.eval_ai` |
| 4.6 | Application size | ~4,650 lines application code; 12 tables; 43 API endpoints; **zero** live enterprise integrations | `docs/ASSESSMENT_VS_GOTHAM.md` | read |
| 4.7 | Demo data | 20 entities, 14 relationships, 2 documents — **entirely synthetic** | `docs/ASSESSMENT_VS_GOTHAM.md`, demo seed script | reseed and count |

**The 504 ms tenant overview is a known, unfixed limitation** and is the red bar on appendix slide 18. It is not
rounded off, hidden, or excluded from the average.

---

## 5. Modelled figures (`MODEL`)

All from `pitch/GOTHAM_INDIA_Financial_Model.xlsx`. Change the yellow input, everything downstream moves.

| Figure | Value | Where in the model |
|---|---|---|
| Round, base case | ₹6.00 Cr (range ₹4–8 Cr) | Assumptions `D6` |
| Post-money cap, base case | ₹30 Cr (range ₹24–36 Cr) | Assumptions `D7` |
| Investor stake | 25.0% / 20.0% / 16.7% at ₹24 / 30 / 36 Cr | Cap table |
| ESOP pool created at this round | 10.0% post-round | Cap table `C9:E9` |
| Total spend, 18 months | **₹5.56 Cr** (₹556.3 lakh) | Use of funds, categories 6–11 |
| Contingency (residual) | **₹0.44 Cr** | Use of funds row 12 |
| Variance to the round | **₹0.00** — must read zero | Use of funds row 17 |
| Spend reconciliation (model vs P&L) | **₹0.00** — must read zero | Use of funds row 21 |
| Revenue over 18 months, base | **₹3.70 Cr** (0.70 pilots + 2.20 licence + 0.80 implementation) | Revenue `D11` |
| ARR exiting month 18, base | **₹2.20 Cr** | Revenue `D12` |
| Closing cash at month 18 | **₹1.14 Cr** (₹113.7 lakh) | Cashflow `U10` |
| Runway the round buys | **19.4 months** at base spend rate; plan uses 18 | Assumptions row 36 |
| Peak monthly burn | **₹0.69 Cr** in month 10 (field deployment lands) | Cashflow summary |
| Months a ₹4 Cr round funds | **12.9** — the reason ₹6 Cr is the ask, not a preference | Assumptions runway table |
| Monthly payroll at month 18 | **₹18.5 lakh** across 9 seats | Assumptions row 32 |
| Market, bottom-up | **₹550 Cr / yr ≈ $6.6 M** | Market sheet |
| Obtainable ARR, year five | **₹12 Cr** (3 states × ₹3 Cr + 2 PSUs × ₹1.5 Cr) | Market sheet |
| Pilot / implementation / licence prices | ₹25–50 L (base ₹35 L) / ₹50 L–2 Cr (base ₹80 L) / ₹1.5–4 Cr (base ₹2.2 Cr) | Assumptions rows 23, 27, 26 |

**Round-number discipline.** The deck prints two decimals so that the seven categories sum to exactly ₹6.00 Cr. The
model's "rounding difference" cell reports the gap; if somebody edits a slide number without editing the model, that
cell stops reading zero.

---

## 6. Claims we deliberately do **not** make

| Tempting claim | Why it is not in the deck |
|---|---|
| "India's Palantir" | Category confusion, and it invites a capability comparison we would lose at 16.3%. Slide 21 explains what we are instead. |
| "1% of a $X B market" | Replaced by a bottom-up table of named buyers with an ACV attached (Market sheet). |
| "In conversation with OSDMA / NDMA" | Not true. No conversation, no LOI, no partner. Slides 12 and 16 say so in those words. |
| "Government-approved / empanelled" | No STQC, no ISO 27001, no CERT-In empanelment. Slide 19 has a line that reads "Not claimed". |
| "AI that predicts disasters" | The product answers grounded questions and refuses when evidence is missing. That is narrower and more defensible. |
| "Proven at scale" | 1 M rows on one node. 10 M, partitioning and multi-node are on the "not yet proven" card. |
| Any Palantir relationship | None exists. |

---

## 7. Re-checking this file

Before sending the pack to a new investor:

1. Re-open the four highest-risk external figures (1.2 SDRF, 2.1 GeM startups, 2.4 iDEX funnel, 3.1 Palantir revenue)
   and confirm the source page still supports the number.
2. Re-run `python -m pytest tests -q` and `python -m tests.scale --rows 1000000`; update `docs/TESTING.md` and
   `docs/SCALE.md` if anything moved.
3. Re-open the model and confirm use-of-funds rows 17 and 21 both read `0.00`.
4. Update the "Dated" column. A source that has not been re-checked in twelve months is a liability.
