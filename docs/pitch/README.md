# Pitch pack — index and rules

**GOTHAM INDIA · sovereign decision support for disaster response and public infrastructure**
Pre-seed · ₹6 Cr (range ₹4–8 Cr) · 18 months to a first paid licence · November 2026

---

## What is in the pack

| File | What it is | Use it for |
|---|---|---|
| `pitch/GOTHAM_INDIA_PreSeed_Deck.pdf` | 21 slides, the document you send | The first read, the forward, the meeting |
| `pitch/GOTHAM_INDIA_OnePager.pdf` | Slide 2 on its own | The email attachment when a full deck is too much |
| `pitch/GOTHAM_INDIA_PreSeed_Deck.pptx` | Same deck, editable | Deck changes; **regenerate with `build_deck.py`, never hand-edit** |
| `pitch/GOTHAM_INDIA_Financial_Model.xlsx` | 9-sheet model, live formulas | Diligence; "show me the runway" |
| `docs/pitch/INVESTOR_FAQ.md` | 42 questions answered, hard ones included | Preparation; the answers you say out loud |
| `docs/pitch/SOURCES.md` | Every external number, URL and date, mapped to a slide | Any question that starts "where did you get…" |
| `docs/pitch/DATA_ROOM_CHECKLIST.md` | What exists, what is missing, what to fix before the first meeting | Diligence readiness; honest self-assessment |
| `docs/pitch/DEMO_SCRIPT.md` | 20-minute live demo, click by click, with failure handling | The technical call |

Study order, if someone has one hour: deck (15 min) → FAQ sections B and C (15 min) → model use-of-funds and cashflow
sheets (15 min) → `SOURCES.md` (15 min).

---

## The rules this pack follows

1. **The model is the source of truth.** Every rupee figure in the deck is a formula in
   `GOTHAM_INDIA_Financial_Model.xlsx`. If a slide number changes, the model changes first.
2. **Two reconciliation cells must read `0.00`.** Use of funds row 17 (model vs round) and row 21 (model vs P&L). If
   either is non-zero, the pack does not go out.
3. **Every external number has a line in `SOURCES.md`**, with a URL and a date. No line, no slide.
4. **Nothing is claimed that cannot be reproduced.** Capability 16.3%, 61 tests, 1 M-row latency, and the 504 ms page
   that is still slow — all published, including the bad ones.
5. **No customer, no LOI, no partner exists.** This is stated on slides 12, 16 and 21 and in the FAQ. It is not
   softened by implication anywhere else.

---

## Regenerating the pack

```bash
cd pitch
python3 make_charts.py     # charts/ — market, funds, funnel, bench, timeline, cover
python3 build_deck.py      # GOTHAM_INDIA_PreSeed_Deck.pptx, 21 slides
python3 build_model.py     # GOTHAM_INDIA_Financial_Model.xlsx, 9 sheets (formulas, no cached values)

# PDF + page renders for QA (needs LibreOffice and PyMuPDF)
soffice --headless --convert-to pdf --outdir render GOTHAM_INDIA_PreSeed_Deck.pptx
python3 -c "import pymupdf; d=pymupdf.open('render/GOTHAM_INDIA_PreSeed_Deck.pdf'); \
  [d[i].get_pixmap(dpi=110).save(f'render/s{i+1:02d}.png') for i in range(d.page_count)]"
```

To check the model's formulas actually resolve, recalculate a copy and read values — openpyxl writes formulas but does
not evaluate them:

```bash
soffice --headless --convert-to xlsx --outdir /tmp/recalc GOTHAM_INDIA_Financial_Model.xlsx
python3 -c "from openpyxl import load_workbook; wb=load_workbook('/tmp/recalc/GOTHAM_INDIA_Financial_Model.xlsx',\
data_only=True); print(wb['Use of funds']['C17'].value, wb['Use of funds']['C21'].value)"
# expected: 0 0
```

---

## Headline numbers (all traceable)

| | Value | Where |
|---|---|---|
| Round | ₹6.00 Cr base, range ₹4–8 Cr | Model · Assumptions D6 |
| Cap | ₹30 Cr post-money base, range ₹24–36 Cr | Model · Assumptions D7 |
| Dilution | 25.0% / 20.0% / 16.7% | Model · Cap table |
| Spend over 18 months | ₹5.56 Cr + ₹0.44 Cr contingency = ₹6.00 Cr | Model · Use of funds |
| Revenue over 18 months (base) | ₹3.70 Cr, ARR exiting ₹2.20 Cr | Model · Revenue |
| Closing cash at M18 | ₹1.14 Cr; runway 19.4 months at base burn | Model · Cashflow |
| Serviceable market | ₹550 Cr / yr ≈ $6.6 M, bottom-up | Model · Market |
| Capability vs Gotham-class | 16.3% | `docs/ROADMAP_TO_60.md` |
| Engineering evidence | 61 tests on 2 databases · 27/27 browser checks · 1 M rows | `docs/TESTING.md`, `docs/SCALE.md` |

---

## Known gaps in the pack (kept here on purpose)

- `[FOUNDER NAME]`, `[email]`, `[phone]` on slides 13 and 17 are placeholders.
- The founder split on the Cap table sheet is a placeholder (60/30/10 + advisor pool).
- Nothing is incorporated: no company, no bank account, no DPIIT recognition.
- No external penetration test, no ISO 27001, no CERT-In empanelment — budgeted, not held.

See `DATA_ROOM_CHECKLIST.md` §8 for the five fixes to make before the first investor meeting.
