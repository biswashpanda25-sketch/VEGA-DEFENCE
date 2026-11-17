# Investor FAQ

**GOTHAM INDIA · pre-seed, ₹6 Cr (range ₹4–8 Cr) · 18 months to a first paid licence**

Answers are written to be said out loud in a meeting. Where the honest answer is uncomfortable, it is the answer
here rather than a softer version on a slide. Numbers in `₹Cr`/`₹L` come from
`pitch/GOTHAM_INDIA_Financial_Model.xlsx`; capability numbers from `docs/ROADMAP_TO_60.md`.
Figures marked **EXT** are externally reported — see `SOURCES.md`.

---

## A. The round

**A1. What exactly am I buying?**
A working decision-support platform for disaster response and public infrastructure — ontology, geospatial
analysis, graph, governance, audit, grounded AI — plus eighteen months of a funded team to turn it into two paid
deployments and one annual licence. At a ₹30 Cr post-money cap, ₹1 Cr buys 3.33%.

**A2. Why ₹6 Cr and not ₹3 Cr or ₹15 Cr?**
The plan costs ₹5.56 Cr (use of funds) and the round carries ₹0.44 Cr of contingency. At a ₹4 Cr round the same plan
runs **12.9 months** instead of 18 — it ends before the first licence can be signed, which is the only milestone that
matters. A ₹15 Cr round would not accelerate a government procurement cycle; it would only buy a bigger team before
anyone has paid us.

**A3. Is the range ₹4–8 Cr real, or is it a negotiating position?**
Real, with a stated consequence. ₹4 Cr: one pilot, no licence inside the window, 13 months (see the runway table on
the Assumptions sheet). ₹6 Cr: full plan. ₹8 Cr: full plan plus ₹2.4 Cr uncommitted for a second state or a second
deployment team. We would rather raise ₹6 Cr and hit the gates than ₹8 Cr and drift.

**A4. SAFE or equity, and what does the cap mean?**
SAFE-or-equity at a **₹24–36 Cr post-money cap**, i.e. 16.7–25.0% dilution for ₹6 Cr. We are not incorporated yet;
incorporation is gate M2. If a bridge is faster, we will take a SAFE on the same cap with a most-favoured-nation
clause, and convert at the priced round.

**A5. 25% dilution at pre-seed is a lot. Defend it.**
Founders end up at 65–73.3% depending on cap, before the ESOP pool is created. The dilution buys two paid
deployments and a licence; if we hit the M18 gates, the seed is illustrated at ₹18 Cr on a ₹90 Cr post-money, which
puts founders at ~56% after the seed and our pre-seed investors at ~16%. If we miss the gates, the dilution is the
least of the problems.

**A6. What is the ESOP pool and when is it created?**
10% post-round, created at this round rather than at seed — investors usually insist, and doing it now costs the
founders, not the incoming investor. Advisors are paid from a separate advisory allocation, not from the employee
pool.

**A7. How long is the money meant to last, and what if it doesn't?**
19.4 months of runway at the base spend rate; the plan spends 18 and finishes with **₹1.14 Cr** in the bank. Kill
criteria are written down for month 9 (slide 15): no signed design partner and no paid pilot means we stop spending
and return the balance rather than extend.

**A8. What are you personally putting in?**
Founder stipends are ₹1.0 lakh per month each for 18 months — below market by design, and ₹36 lakh of the budget is
that decision. Time is full-time and exclusive from month 1.

---

## B. Traction and status (the uncomfortable section)

**B9. What do you actually have?**
Working software: ingestion, ontology, graph, geospatial, cases with evidence refs and reviewer approval,
clearance-based access, hash-chained audit with a verify endpoint, TOTP MFA, and a grounded question-answering path
that cites the record or refuses. 61 backend tests pass on SQLite and PostgreSQL, 27/27 browser checks pass, and
latency is measured at 1 M rows. Everything in that sentence is reproducible in the repository.

**B10. Do you have customers?**
No. No signed customer, no LOI, no design partner, no pilot, no revenue. The demo runs on synthetic data. Slide 12
says this in a box labelled "does not exist yet" and slide 16 leads with the risk that no design partner
materialises.

**B11. Then why invest now rather than at seed?**
Because what is left is procurement and deployment, not invention, and both are cheaper to de-risk with ₹6 Cr than
with a seed cheque after a failed attempt at it. You are buying the eighteen months in which the first licence either
happens or doesn't. That is a real risk and it is priced at a ₹30 Cr cap, not a ₹100 Cr one.

**B12. What has actually been validated then?**
Two things, both narrow. First, engineering: the performance and security work is measured, not asserted (1 M rows,
1.05 ms spatial KNN, hash-chain verification endpoint). Second, the problem statement: the Disaster Management
(Amendment) Act 2025 mandates a national and state disaster databases (**EXT**) — the buyer now has a legal reason to
hold exactly the data this platform organises. What is unvalidated is willingness to pay.

**B13. How big is the team today?**
Effectively one engineer working full days, and the plan hires eleven seats over eighteen months. The deck's team
slide is honest about that; the first two hires are both senior engineers, not salespeople.

---

## C. The product and the technology

**C14. What does the platform actually do?**
Four surfaces, all in the demo: an operational overview across districts and assets; a graph view of entity
relationships with provenance-typed edges; a geospatial view anchored to district boundaries; and an assistant that
answers from the record with citations and refuses when the evidence is not there. Underneath: 12 tables, 43 API
endpoints, PostgreSQL 17 + PostGIS, and a governance layer that enforces clearance and records every read of a
sensitive field.

**C15. Is this just an LLM wrapper?**
No, and that is a design decision with a cost: the assistant is deliberately the weakest surface in the product. The
defensible assets are the administrative ontology, the audit chain and the deployment. A wrapper has none of those.

**C16. What is your capability against a Gotham-class system?**
**16.3%**, self-assessed area by area in `docs/ROADMAP_TO_60.md` and `docs/ASSESSMENT_VS_GOTHAM.md`. It was 7.2%
before the Phase-A/B work. We publish the number because investors find it out anyway; the interesting question is
which 16% — ontology, audit, access control and geospatial are relatively strong; pipelines, workflow and writeback
are thin. Appendix slide 21 lists what is absent.

**C17. Why should that 16.3% be defensible?**
Because building it was mostly knowledge work about Indian administrative structure, not compute. The entity model,
the clearance ladder, the evidence discipline and the refusal behaviour are slow to replicate and cheap to extend.
The AI is not the moat; the interface between the AI and the record is.

**C18. What breaks at 10 million records?**
We do not know, and we say so on slide 18. 1 M rows is measured; partitioning, connection pooling and multi-node
deployment are not. The 504 ms tenant overview is already slow at 1 M and is the known-unfixed item.

**C19. Can it run offline / on-premise?**
That is the deployment model we sell: a district or state wants the data inside its own perimeter. Docker Compose
today; hardened appliance images are a month-10 deliverable, funded by the "Deployment & pilots" line.

**C20. What about data protection and DPDP?**
Purpose-bound field redaction, clearance enforcement, tenant isolation, and an append-only audit chain are built.
A DPDP compliance assessment, source-code escrow and an external penetration test are **budgeted, not done**
(₹0.46 Cr of the round). Slide 19 lists exactly what an empanelment audit will still demand.

**C21. What is the biggest technical risk?**
Not performance — integration. A state's data arrives as Excel, PDFs and a legacy portal. The connector work is
funded but unproven, and it is the most likely reason a pilot slips a quarter.

---

## D. Market and go-to-market

**D22. How big is the market, really?**
**₹550 Cr/yr serviceable**, bottom-up: 36 state/UT authorities × ₹4 Cr, 780 districts × ₹20 L, 5 central agencies ×
₹10 Cr, 110 urban local bodies × ₹1 Cr, 60 PSU asset owners × ₹1.5 Cr. That is ≈ **$6.6 M**. It is deliberately small
and honest: a top-down "public safety software" number would be ten times larger and mean nothing.

**D23. ₹550 Cr is small. Why would a VC care?**
A generalist VC probably shouldn't, and the appendix says so. This is a ₹12 Cr ARR business in year five at 3 states
and 2 PSUs — interesting to a strategic investor or an angel who wants sovereign software to exist in India,
uninteresting as a venture-scale outcome unless it expands into infrastructure asset intelligence beyond disasters,
which is the second product and not funded by this round.

**D24. Who is the buyer, precisely?**
Three, in order: a **state disaster-management authority** (Odisha's OSDMA, under the Board of Revenue & SRC),
**district collectors** who own the emergency operations centre, and a **PSU asset owner** (rail, power, port) with
an asset registry problem. One budget line each, one procurement route each.

**D25. Why Odisha first?**
Because the founder is in Bhubaneswar, because Odisha has a genuine disaster-management apparatus with a history of
adopting new systems after cyclones, and because a first reference in a state that is *known* for disaster
preparedness is worth more in Delhi than five cold meetings. It is a wedge, not a market.

**D26. How do you sell into government without a sales team?**
GeM Startup Runway (no prior turnover, prior experience or EMD; 10–15 day payment cycles — **EXT**) and iDEX for the
defence-adjacent route. One Delhi-based partnerships lead, founder-led selling, and a paid pilot priced at ₹25–50 L
that a district can authorise without a tender.

**D27. What is the sales cycle and what happens if nothing closes in 12 months?**
Nine to eighteen months for a licence; three to four months for a paid pilot once there is a warm introduction.
That is why the plan requires two pilots by month 14 and no licence before month 17. If nothing closes by month 9,
the kill criteria apply.

**D28. What about the large systems integrators?**
They own the contract vehicles and are our channel, not our competitor — slide 20 says this plainly. A product layer
makes their delivery cheaper; we would rather be sub-contracted by an SI into a state deal than fight them for it.

**D29. Why won't Palantir, or an Indian SI, simply do this?**
Palantir has no Indian government footprint, no domestic data-residency story and no interest in a ₹4 Cr state
contract. Indian SIs build bespoke projects, not products, because they are paid by the hour. The gap is a product
company that sells into Indian public procurement at Indian prices.

---

## E. Business model and unit economics

**E30. How do you make money?**
Three lines: a **paid pilot** (₹25–50 L, 3–6 months), **implementation** (₹50 L–2 Cr, paid with the licence) and an
**annual licence** (₹1.5–4 Cr/yr). Gross margin is 70–75% at licence, 45–55% in year one when services dominate. CAC
is ₹6–10 lakh per state, almost entirely travel and founder time.

**E31. What does the base case actually produce in 18 months?**
**₹3.70 Cr** of revenue: two pilots at ₹35 L (₹0.70 Cr), one licence at ₹2.20 Cr, and ₹0.80 Cr of implementation.
ARR exiting month 18 is ₹2.20 Cr. EBITDA turns positive in month 17 — the month the licence books — and is negative
in every other month. We are not pretending that is recurring profitability yet.

**E32. Isn't a single licence 60% of your revenue? Concentration risk?**
Yes. One licence is 59% of eighteen-month revenue. Mitigation is procedural, not rhetorical: no more than 40% of
revenue from one department by year three, and a parallel state pipeline from month 12 (slide 16, risk 5).

**E33. What is the renewal story?**
Switching cost, not lock-in: the audit history, the trained staff workflows and the integration all live in the
platform, so replacement means losing the record. That is a moat we will have *after* the first renewal — slide 11
puts "deployment entrenchment" in a box marked "not yet earned".

**E34. Path to profitability?**
Not in this round. At ₹2.5 Cr of annual licence revenue with a 5–6 person team, the business is roughly
break-even; that is 18–24 months beyond this plan, and the seed round is what funds the gap.

---

## F. Risks

**F35. Top three things that kill this.**
(1) No design partner materialises — fatal severity, mitigated by 90 days of founder-led outreach and one free
60-day pilot to create a reference. (2) Procurement takes 12–18 months — mitigated by paid pilots and private buyers
(insurers, logistics) who sign in weeks. (3) Security empanelment is slower than planned — mitigated by starting the
paperwork in month 2 and never claiming certification we do not hold.

**F36. What if a state asks for something you cannot build?**
We say no to scope that breaks the audit model, and we price the rest. The product boundary is on slide 21: no
surveillance, no individual tracking, no targeting capability, no fabricated data, and consequential decisions stay
human. That boundary has cost us at least one conversation and it is worth more than that conversation.

**F37. What happens if you are not the winner in this category?**
An acquisition by an SI, a defence-electronics prime or a data-platform company is the realistic floor, at a price
driven by the reference customer and the ontology, not by the technology. We are not modelling that outcome and we
are not promising it; it is simply more likely than a zero.

**F38. Governance — who watches the money?**
A monthly investor update (cash, burn, gate status, pipeline), an annual audit from month 6, budgeted in the "Legal,
IP" line, and a board seat offered to the lead investor. Cash leaves on milestones, not on a schedule.

---

## G. People and process

**G39. Who is on the team?**
Currently one engineer-founder full-time; the second founder's seat is open and is the first conversation after the
round, not a placeholder to be filled later. Slide 13 shows the plan rather than implying a team that does not exist.

**G40. Why are you the person to do this?**
The software exists and its limits are documented by the person who wrote it. That is the entire claim. No prior
government-sales exit, no defence-industry pedigree.

**G41. What does an investor do that money alone doesn't?**
Three things, from slide 17: an introduction to OSDMA, a state IT secretary or a PSU asset owner; a security
reviewer who will say what an empanelment audit actually asks; and a board member willing to enforce the month-9 kill
criteria on the founders who wrote them.

**G42. What is the process from here?**
Two weeks: technical demo (20 minutes, no slides), the model walked line by line, then references. Data room is
assembled and indexed — see `DATA_ROOM_CHECKLIST.md` — with the gaps listed in public rather than discovered in
diligence. Indicative term sheet is a two-page SAFE or a priced seed instrument; we will sign the first credible
offer at or above the floor of the range rather than run an auction for three months.

---

## H. If you only remember four numbers

| Number | What it is |
|---|---|
| **16.3%** | Measured capability against a Gotham-class system — published, not hidden |
| **₹6 Cr / 18 months** | The round that reaches a first paid licence; ₹4 Cr reaches month 13 instead |
| **₹550 Cr** | Serviceable market per year, built bottom-up from named buyers |
| **₹0.00** | Variance between the use of funds and the round, and between the model and the P&L |
