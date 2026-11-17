# Demo script — 20 minutes, no slides

**Purpose:** show the software to an investor or a technical reviewer without hiding what it does not do.
**Audience:** mixed. Assume one person in the room will ask "what breaks at scale".
**Rule:** every claim said out loud during the demo is either visible on the screen or already published in
`docs/SCALE.md`, `docs/TESTING.md` or `docs/EVALUATION.md`.

All records are **synthetic** and labelled `SYNTHETIC-DEMO` in the interface. Say this once, early — at 02:00 — and
never apologise for it.

---

## 0. Pre-flight (15 minutes before, do not skip)

| Check | Command / action | Pass condition |
|---|---|---|
| Database up | `docker compose up -d db cache` | `docker compose ps` shows `db` healthy |
| Schema current | `cd backend && alembic upgrade head` | no pending migrations |
| Synthetic data | `python -m app.seed` (or restart API — seed runs at startup) | returns `seeded` or `already_seeded` |
| API up | `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000` | `/api/docs` loads |
| Console up | `cd frontend && npm run dev` | login screen renders at `:5173` |
| Sign-in works | `admin@gotham-demo.in` / `Gotham@2026` | dashboard loads in under 3 s |
| Assistant works | Ask *"Summarise the condition of Bridge Mahanadi-03"* | an answer with at least one citation |
| Second tenant works | sign out, sign in as `disaster@gotham-demo.in` | different tenant, same districts |
| Screen share | 1440×900, browser zoom 100%, notifications off | no personal tabs visible |
| Fallback ready | `frontend/e2e/screenshots/*.png` open in a second window | if the stack dies, you can finish the story |

**If the stack will not start, do not debug it in front of the investor.** Switch to the screenshots, say plainly
"the demo environment did not come up, here is the same flow captured from a passing browser run this week", and
offer a re-run inside 24 hours.

---

## 1. The opening (2 minutes)

Say this before touching the keyboard:

> "Everything you are about to see runs on synthetic data. There is no customer, no pilot and no signed partner. What
> exists is the software, and a set of measurements about how it behaves. I will show you both, and I will tell you
> what is missing. If you want to stop and interrogate a number, stop me."

Then: "Three things I want you to judge — whether the data model matches how Indian administration actually works,
whether the governance is real or painted on, and whether the assistant refuses when it should."

---

## 2. Sign-in and the tenant boundary (2 minutes)

**Do:** open the login page. Show the four demo accounts. Sign in as `analyst@gotham-demo.in`.

**Say:** "Two tenants exist in this demo, an infrastructure directorate and a disaster coordination cell. Everything
is scoped by tenant before any query runs — not filtered afterwards, scoped. I will prove that at the end by signing
in as the other one."

**What to point at:** the role chip in the top bar; the clearance label on the session.

**Do not:** talk about the login screen's styling. It is not the product.

---

## 3. Overview — the operational picture (3 minutes)

**Do:** land on the overview. Read one number aloud, then click into the exception queue under
**Operational Intelligence**.

**Say:** "This is the page a district collector's office would keep open during a cyclone. Assets, exceptions,
who owns each one, and what has been decided. The exception queue is advisory — the platform recommends and records,
it does not act. That is a boundary, not a gap."

**What an investor should notice:** every card has a number and a provenance, not a chart for decoration.

---

## 4. Knowledge graph — the thing a spreadsheet cannot do (4 minutes)

**Do:** **Knowledge Graph** → wait for layout → click a node → evidence panel opens.

**Say:** "Twenty entities, fourteen relationships — small on purpose. The point is not the size, it is that each edge
carries a type and a source. Clicking a node shows why these two things are connected, and the citation behind it.
At 1 M rows the entity list query is 0.14 ms; the graph has been exercised at 300,000 edges."

**Say the limitation here, unprompted:** "One-hop adjacency. No pathfinding, no temporal graph. Deep traversal is a
post-seed problem."

**If asked "is this Palantir?":** "Same category of problem, 16.3% of the capability, and I publish that number —
`docs/ASSESSMENT_VS_GOTHAM.md`. The wedge is Indian administrative structure, not a Gotham clone."

---

## 5. Geospatial — district-anchored, honest about it (3 minutes)

**Do:** **Geospatial Explorer** → hover a cluster → open a feature → toggle the heatmap.

**Say:** "Points anchored to real district geography, clustered, with a heatmap. What is missing is polygons and time —
no flood extent polygons, no temporal playback. An operational buyer will ask for both; they are on the roadmap, not
in the build."

**What to point at:** the feature count badge. It is the honest denominator for "how much data is on screen".

---

## 6. The assistant — where it refuses (4 minutes)

**Do:** **AI Assistant** → ask *"Summarise the condition of Bridge Mahanadi-03"* → let the answer appear with
citations. Then ask a question with **no** supporting record, e.g. *"How many people died in the 1999 super cyclone in
Jagatsinghpur?"*

**Say:** "First answer: cites the records it used. Second answer: it declines, because no authorised record supports
it. That refusal is the product. An assistant that invents a casualty figure in a disaster room is worse than no
assistant."

**Then the measurement:** "Grounding is evaluated, not asserted: retrieval recall 1.00, citation coverage 1.00,
groundedness 0.73, unsupported-claim rate 0.00, permission-leakage 0.00 across 11 cases — `docs/EVALUATION.md`,
reproducible with `python -m tests.eval_ai`. Groundedness 0.73 is the weakest of those numbers and it is the one I
would spend the next quarter on."

---

## 7. Governance and audit — the part that closes deals (4 minutes)

**Do:** **Governance** → show the classification ladder and the redaction rule. Then **Security & Audit** → open the
audit explorer → filter to the assistant query you just ran. Then open `/api/audit/verify` in a browser tab while
signed in as `admin@gotham-demo.in`.

**Say:** "Every sensitive read is written to an append-only, hash-chained log. `/audit/verify` recomputes the chain and
names the first broken link — that is what a security reviewer will ask you to prove, and most products cannot. A
single edited row breaks verification."

**Say what is not there:** "No ISO 27001, no STQC, no CERT-In empanelment, no external penetration test yet — that is
budgeted at ₹0.46 Cr in the round and it is the gate at month 5. Slide 19 lists exactly what an audit will demand."

---

## 8. Tenant isolation, proven live (2 minutes)

**Do:** sign out. Sign in as `disaster@gotham-demo.in`. Open the same graph view.

**Say:** "Same product, same districts, different records. The scope is applied in the data layer. Nothing from the
other tenant is visible, and that is enforced on the query, not on the render."

**Do not:** claim row-level security in Postgres. It is application-level scoping plus tenant columns today;
`docs/KNOWN_ISSUES.md` says so.

---

## 9. Close (2 minutes)

Three sentences, then stop talking:

1. "That is the product: an operational picture, an evidence-bound assistant, and a governance layer an auditor can
   verify."
2. "Scaled worst-first: 16.3% capability, 1 M records measured, 61 tests, 27 browser checks, and a 504 ms page that I
   have not fixed."
3. "The round is ₹6 Cr for eighteen months, ending in one paid licence or a return of the balance. The model is a
   spreadsheet you can open line by line while I am still in the room."

---

## 10. Five questions I will invite, because the answers are good

| Question | Answer in one breath |
|---|---|
| "What is actually hard here?" | The ontology and the audit discipline. Anyone can call a model; matching Indian administrative structure and proving what was read is slow work. |
| "What breaks at 10 M records?" | Unknown; partitioning, pooling and multi-node are unproven, and the 504 ms tenant overview is already the weak page. |
| "Why won't a big SI just build it?" | They are paid by the hour and build per-project. A product layer makes their delivery cheaper; that is why they are a channel. |
| "What is the riskiest assumption in the plan?" | That a district will pay ₹25–50 L for a pilot inside four months of a warm introduction. Everything downstream depends on it. |
| "What would make you walk away from this?" | The month-9 kill criteria — no design partner and no paid pilot means we stop spending and return the balance. |

---

## 11. Things not to do on this call

- Do not claim certification, empanelment, accreditation, a customer, an LOI or a partner. None exist.
- Do not say "AI predicts". It answers grounded questions and refuses.
- Do not show the 504 ms page and call it fast.
- Do not use the words "India's Palantir".
- Do not promise a delivery date for polygons, temporal playback, workflow writeback or 10 M-row scale. Those are
  roadmap items with no committed dates.
- Do not improvise a market number. If it is not in `docs/pitch/SOURCES.md`, say "I will send you the source line".
