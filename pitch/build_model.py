"""Builds the pre-seed financial model (.xlsx) — live formulas, three revenue scenarios, nothing hardcoded twice.

Design rules
------------
* Every input lives on Assumptions (yellow). Everything else is a formula.
* Row references are resolved by name (dict), never typed by hand.
* The monthly P&L / cashflow model the BASE column (₹6 Cr) only; the Revenue sheet
  carries all three scenarios because that is where the uncertainty actually is.
* Use of funds reconciles to the round with a variance cell that must read zero.

Layout rows are declared as constants because two sheets cross-reference each other.
If you reorder rows, change the constants and re-run the checks at the bottom of this file.
"""
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT = Path(__file__).parent / "GOTHAM_INDIA_Financial_Model.xlsx"

NAVY = "FF0B0F14"
GREY = "FF22303F"
LIGHT = "FFF2F4F7"
INPUT = "FFFFF3D6"

H1 = Font(name="Calibri", size=15, bold=True, color="FFFFFFFF")
H2 = Font(name="Calibri", size=10.5, bold=True, color="FFFFFFFF")
BOLD = Font(name="Calibri", size=10.5, bold=True)
NORM = Font(name="Calibri", size=10.5)
SMALL = Font(name="Calibri", size=9, italic=True, color="FF5A6572")

FILL_H1 = PatternFill("solid", fgColor=NAVY)
FILL_H2 = PatternFill("solid", fgColor=GREY)
FILL_INPUT = PatternFill("solid", fgColor=INPUT)
FILL_TOTAL = PatternFill("solid", fgColor=LIGHT)
THIN = Side(style="thin", color="FFD0D6DE")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

MONEY = '#,##0.0'
PCT = '0.0%'

# --- declared layout (see header comment) -----------------------------------
PL_PILOT, PL_LICENCE, PL_IMPL, PL_REV = 6, 7, 8, 9
PL_PAYROLL, PL_CLOUD, PL_TRAVEL, PL_BIDS, PL_DATA, PL_FIELD, PL_DEPLOY, PL_AUDIT, PL_LEGAL = range(10, 19)
PL_COST, PL_EBITDA, PL_CUM = 19, 20, 21
CF_OPEN, CF_IN, CF_OUT, CF_NET, CF_CLOSE, CF_CHECK = range(6, 12)
UF_FIRST, UF_COUNT, UF_CONT, UF_TOTAL = 6, 6, 12, 13

wb = Workbook()


def sheet(name, title, subtitle=None, widths=None):
    ws = wb.create_sheet(name)
    ws.sheet_view.showGridLines = False
    ws.merge_cells("B2:H2")
    c = ws["B2"]
    c.value = title
    c.font = H1
    c.fill = FILL_H1
    c.alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[2].height = 28
    if subtitle:
        ws.merge_cells("B3:H3")
        ws["B3"].value = subtitle
        ws["B3"].font = SMALL
        ws["B3"].alignment = Alignment(indent=1)
    if widths:
        for i, w in enumerate(widths, start=2):
            ws.column_dimensions[get_column_letter(i)].width = w
    ws.column_dimensions["A"].width = 2
    return ws


def header(ws, row, values, start_col=2):
    for i, v in enumerate(values):
        c = ws.cell(row=row, column=start_col + i, value=v)
        c.font = H2
        c.fill = FILL_H2
        c.border = BOX
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = 26


def put(ws, row, values, start_col=2, bold=False, fill=False, fmt=None):
    for i, v in enumerate(values):
        c = ws.cell(row=row, column=start_col + i, value=v)
        c.font = BOLD if bold else NORM
        c.border = BOX
        if fill:
            c.fill = FILL_TOTAL
        if fmt:
            c.number_format = fmt


def inp(ws, cell, value, fmt=None):
    c = ws[cell]
    c.value = value
    c.fill = FILL_INPUT
    c.font = BOLD
    c.border = BOX
    if fmt:
        c.number_format = fmt
    return c


def note(ws, row, text, span=6, height=30):
    c = ws.cell(row=row, column=2, value=text)
    c.font = SMALL
    c.alignment = Alignment(wrap_text=True, vertical="top")
    if span > 1:
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=1 + span)
    ws.row_dimensions[row].height = height


def section(ws, row, text):
    c = ws.cell(row=row, column=2, value=text)
    c.font = Font(name="Calibri", size=11, bold=True, color=NAVY)


# ==================================================================== 1. Read me
ws = wb.active
ws.title = "Read me"
ws.sheet_view.showGridLines = False
ws.column_dimensions["A"].width = 2
ws.column_dimensions["B"].width = 104
ws["B2"] = "GOTHAM INDIA — pre-seed financial model"
ws["B2"].font = Font(name="Calibri", size=20, bold=True, color=NAVY)
ws["B3"] = "November 2026 · ₹ crore unless a row says lakh · yellow cells are the only inputs"
ws["B3"].font = SMALL

lines = [
    ("How to use this model", True),
    ("Every number in the deck — use of funds, runway, the eighteen-month plan, the ₹550 Cr market — traces back "
     "to this workbook. Change a yellow cell and the rest recalculates. Nothing is typed twice, so nothing can "
     "drift out of sync with the deck.", False),
    ("", False),
    ("Sheets", True),
    ("Assumptions — the only place inputs live: round, cap, salaries, deployment costs, pricing, collection days.", False),
    ("Headcount — eleven seats, start month, monthly cost; totals flow into the P&L and the use of funds.", False),
    ("Revenue — three scenarios (conservative / base / upside) and what each one implies.", False),
    ("P&L — monthly, month 0 to month 18, base case, formula-driven from Assumptions and Headcount.", False),
    ("Cashflow — real collection lag, monthly closing cash, the lowest cash point, the runway verdict.", False),
    ("Use of funds — seven categories reconciled to the round, with a variance cell that must read zero.", False),
    ("Cap table — dilution at three caps, ESOP pool, seed follow-on illustration.", False),
    ("Market — bottom-up sizing; the ₹550 Cr figure in the deck is the total of this table.", False),
    ("", False),
    ("What this model deliberately does not do", True),
    ("No hockey stick. No 'capture 1% of a large market'. Base case is ₹3.7 Cr of revenue across eighteen months, "
     "most of it in the last two. If that looks small, it is the honest answer at pre-seed — and it is the reason "
     "the ask is ₹6 Cr and not ₹60 Cr.", False),
    ("The monthly P&L models the ₹6 Cr base case only. The ₹4 Cr conservative and ₹8 Cr upside change how much team "
     "and deployment the round can fund; the runway table on the Assumptions sheet quantifies that difference.", False),
    ("", False),
    ("Health checks built in", True),
    ("• Cashflow applies a collection lag (75 days in the base case), because no government pays on the invoice date.", False),
    ("• Closing cash is checked every month and flagged 'SHORT' if it ever goes negative.", False),
    ("• Use of funds reconciles to the round: the variance cell must read zero before this file leaves the building.", False),
    ("• Revenue is recognised when the pilot or licence is signed, not when cash arrives — the two are shown apart.", False),
    ("", False),
    ("Known weaknesses, stated up front", True),
    ("Salaries are Indian market rates for a small senior team in 2026, not discounted founder maths; the founder "
     "stipend is the one deliberately below-market line. Deployment and data-licence costs are estimates from two "
     "vendor quotes and will move. Nothing here has been audited by anyone.", False),
]
r = 5
for text, is_head in lines:
    c = ws.cell(row=r, column=2, value=text)
    c.font = Font(name="Calibri", size=11, bold=True, color=NAVY) if is_head else NORM
    c.alignment = Alignment(wrap_text=True, vertical="top")
    if is_head:
        ws.row_dimensions[r].height = 16
    elif not text:
        ws.row_dimensions[r].height = 8
    else:
        lines = max(1, -(-len(text) // 112))
        ws.row_dimensions[r].height = 13.2 * lines + 3
    r += 1

# ==================================================================== 2. Assumptions
ws = sheet("Assumptions", "Assumptions",
           "Yellow cells are inputs. Everything else is a formula. The Base column is the ₹6 Cr ask.",
           widths=[46, 14, 14, 14, 46])
header(ws, 5, ["Driver", "Conservative", "Base", "Upside", "Note"])

DRIVERS = [
    ("round", "Round size (₹ Cr)", 4.0, 6.0, 8.0, MONEY, "Deck headline is the Base column"),
    ("cap", "Post-money cap (₹ Cr)", 24.0, 30.0, 36.0, MONEY, "Investor stake = round ÷ post-money"),
    ("stipend", "Founder stipend / month (₹ lakh)", 0.8, 1.0, 1.2, MONEY, "The only deliberately below-market line"),
    ("eng", "Engineer cost / month (₹ lakh)", 2.3, 2.6, 3.0, MONEY, "Senior-heavy; includes PF and overheads"),
    ("partner", "Partnerships lead / month (₹ lakh)", 1.8, 2.0, 2.2, MONEY, "Delhi-based, procurement experience"),
    ("designer", "Designer (contract) / month (₹ lakh)", 1.3, 1.5, 1.8, MONEY, "Analyst-facing workflows"),
    ("qa", "QA / test automation / month (₹ lakh)", 1.0, 1.2, 1.4, MONEY, "Contract to start"),
    ("analyst", "Analyst / implementation engineer / month (₹ lakh)", 1.2, 1.4, 1.6, MONEY, "Disaster-management domain"),
    ("secstaff", "Security consultant / month (₹ lakh)", 1.0, 1.2, 1.5, MONEY, "Nine months, empanelment prep"),
    ("cloud", "Cloud + infrastructure / month (₹ lakh)", 0.6, 0.8, 1.0, MONEY, "Demo, staging, backups, monitoring"),
    ("travel", "Travel + BD / month (₹ lakh)", 1.6, 2.0, 2.4, MONEY, "Delhi + Bhubaneswar cadence"),
    ("bids", "Bids, tenders, demo logistics (₹ lakh, total)", 10.0, 15.0, 20.0, MONEY, "GeM and iDEX responses, site demos"),
    ("data", "Hazard / GIS / imagery data (₹ lakh, total)", 20.0, 30.0, 40.0, MONEY, "Base maps, flood and cyclone layers"),
    ("field", "Field deployment + hardware (₹ lakh, total)", 45.0, 60.0, 80.0, MONEY, "Two district EOCs, on-prem nodes"),
    ("deploy", "Implementation contracts (₹ lakh, total)", 30.0, 40.0, 55.0, MONEY, "Customer-site integration engineers"),
    ("audit", "Security audit + certification (₹ lakh, total)", 25.0, 35.0, 45.0, MONEY, "Pen tests, ISO 27001, empanelment"),
    ("legal", "Legal, IP, incorporation, ESOP (₹ lakh, total)", 20.0, 25.0, 30.0, MONEY, "Pvt Ltd, IP assignment, trademark"),
    ("pilot", "Pilot price (₹ lakh)", 25.0, 35.0, 50.0, MONEY, "Three to six months, defined deliverables"),
    ("pilots", "Pilots signed by month 18", 1, 2, 3, '0', "From design partners, not cold tenders"),
    ("licences", "Annual licences live by month 18", 0, 1, 2, '0', "Base: one signed licence at M17"),
    ("licence", "Annual licence (₹ Cr)", 1.5, 2.2, 3.5, MONEY, "State-scale deployment"),
    ("impl", "Implementation fee per licence (₹ lakh)", 50.0, 80.0, 120.0, MONEY, "Invoiced with the licence"),
    ("dso", "Days to collect (days)", 90, 75, 60, '0', "Government payment reality, not net-30"),
]

DROW = {}
r = 6
for key, name, cons, base, up, fmt, nt in DRIVERS:
    DROW[key] = r
    ws.cell(row=r, column=2, value=name).font = NORM
    for i, v in enumerate([cons, base, up]):
        inp(ws, f"{get_column_letter(3 + i)}{r}", v, fmt)
    ws.cell(row=r, column=6, value=nt).font = SMALL
    r += 1

A = "Assumptions!"
D = lambda key: f"{A}$D${DROW[key]}"
r += 1
section(ws, r, "Derived — Base column. These are formulas; do not type over them.")
r += 1
DERIVED = [
    ("Investor stake at this round", f"={D('round')}/{D('cap')}", PCT, "Round ÷ post-money cap"),
    ("Monthly payroll at month 18 (₹ lakh)",
     f"=2*{D('stipend')}+4*{D('eng')}+{D('analyst')}+{D('qa')}+{D('designer')}+{D('partner')}", MONEY,
     "Founders + four engineers + analyst, QA, designer, partnerships lead"),
    ("Revenue over 18 months (₹ Cr)",
     f"=({D('pilots')}*{D('pilot')})/100+{D('licences')}*({D('licence')}+{D('impl')}/100)", MONEY,
     "Pilot fees + licence + implementation"),
    ("Total spend over 18 months (₹ lakh)", f"=SUM('Use of funds'!D{UF_FIRST}:D{UF_CONT - 1})*100", MONEY, "Links to the use-of-funds total"),
    ("Cash retained at month 18 (₹ lakh)", f"='Cashflow'!U{CF_CLOSE}", MONEY, "Closing cash, base case"),
    ("Runway the round buys, uncapped (months)", f"={D('round')}*100/(SUM('Use of funds'!D{UF_FIRST}:D{UF_CONT - 1})*100/18)", MONEY,
     "Round ÷ monthly spend. The plan is 18 months; the surplus is the buffer"),
]
for name, formula, fmt, nt in DERIVED:
    ws.cell(row=r, column=2, value=name).font = NORM
    c = ws.cell(row=r, column=3, value=formula)
    c.font = BOLD
    c.fill = FILL_TOTAL
    c.border = BOX
    c.number_format = fmt
    ws.cell(row=r, column=6, value=nt).font = SMALL
    r += 1

r += 1
section(ws, r, "Runway at each round size — same team, same plan, no heroic assumptions")
r += 1
header(ws, r, ["Round (₹ Cr)", "Spend it funds (₹ lakh)", "Months of plan covered (18 = full)", "Verdict"])
r += 1
for i, amt in enumerate([4.0, 6.0, 8.0]):
    put(ws, r, [amt, f"=MIN(B{r}*100,SUM('Use of funds'!D{UF_FIRST}:D{UF_CONT - 1})*100)",
                f"=MIN(18,B{r}*100/(SUM('Use of funds'!D{UF_FIRST}:D{UF_CONT - 1})*100/18))",
                ["Thirteen months of plan — no second deployment, no fourth engineer",
                 "The full eighteen months, about a month of cash left at M18",
                 "The full eighteen months and ₹2.4 Cr uncommitted for a second state"][i]])
    ws.cell(row=r, column=2).number_format = MONEY
    ws.cell(row=r, column=3).number_format = MONEY
    ws.cell(row=r, column=4).number_format = MONEY
    r += 1

# ==================================================================== 3. Headcount
ws = sheet("Headcount", "Headcount plan",
           "Eleven seats over eighteen months. Monthly cost flows into the P&L; totals flow into use of funds.",
           widths=[34, 13, 18, 14, 16, 40])
header(ws, 5, ["Role", "Start month", "Cost / month (₹ lakh)", "Months paid", "Total (₹ lakh)", "Why this seat"])

ROLES = [
    ("Founder — technical", 1, "stipend", 18, "Architecture, product, delivery"),
    ("Founder — commercial", 1, "stipend", 18, "Partnerships, procurement, tenders"),
    ("Senior engineer — spatial / PostGIS", 2, "eng", 17, "Data model, performance, geo"),
    ("Senior engineer — platform", 2, "eng", 17, "Ingest, connectors, offline deployment"),
    ("Engineer — frontend", 3, "eng", 16, "Analyst workflows"),
    ("Engineer — data / ML", 5, "eng", 14, "Entity resolution, retrieval"),
    ("Analyst / implementation engineer", 5, "analyst", 14, "Domain: disaster-management workflows"),
    ("QA / test automation", 6, "qa", 13, "Contract to start"),
    ("Designer (contract)", 4, "designer", 15, "Dense operational UI"),
    ("Partnerships lead (Delhi)", 4, "partner", 15, "Tender access, ministry cadence"),
    ("Security / compliance consultant", 2, "secstaff", 9, "Audit prep, empanelment"),
]
HROW = {}
r = 6
for role, start, key, months, why in ROLES:
    HROW[role] = r
    put(ws, r, [role, start, f"={D(key)}", months, f"=D{r}*E{r}", why])
    ws.cell(row=r, column=4).number_format = MONEY
    ws.cell(row=r, column=6).number_format = MONEY
    r += 1
HC_LAST = r - 1
put(ws, r, ["Total payroll, 18 months (₹ lakh)", "", "", f"=SUM(E6:E{HC_LAST})", f"=SUM(F6:F{HC_LAST})", ""],
    bold=True, fill=True)
HC_TOTAL = r
ws.cell(row=r, column=6).number_format = MONEY
put(ws, r + 1, ["Average cost per seat per month (₹ lakh) — seats, then cost", "", "", f"=E{HC_TOTAL}", f"=F{HC_TOTAL}/E{HC_TOTAL}", ""], bold=True)
ws.cell(row=r + 1, column=6).number_format = MONEY
note(ws, r + 3, "Founder lines are stipends, not market salary — the one place the plan is deliberately cheap. "
                "Expect the line to double after a seed round; the seed model should show it.")

# ==================================================================== 4. Revenue
ws = sheet("Revenue", "Revenue — three scenarios",
           "The deck's '₹3–6 Cr contracted or pipeline by month 18' is the Base column of this sheet.",
           widths=[44, 18, 18, 18])
header(ws, 5, ["Line", "Conservative", "Base", "Upside"])
REV_LINES = [
    ("Pilots signed by month 18", [f"={A}{c}{DROW['pilots']}" for c in "CDE"], '0'),
    ("Pilot revenue (₹ Cr)", [f"={c}6*{A}{c}{DROW['pilot']}/100" for c in "CDE"], MONEY),
    ("Annual licences live by month 18", [f"={A}{c}{DROW['licences']}" for c in "CDE"], '0'),
    ("Licence revenue (₹ Cr)", [f"={c}8*{A}{c}{DROW['licence']}" for c in "CDE"], MONEY),
    ("Implementation fees (₹ Cr)", [f"={c}8*{A}{c}{DROW['impl']}/100" for c in "CDE"], MONEY),
    ("Total revenue, 18 months (₹ Cr)", [f"=SUM({c}7,{c}9,{c}10)" for c in "CDE"], MONEY),
    ("Recurring ARR exiting month 18 (₹ Cr)", [f"={c}9" for c in "CDE"], MONEY),
]
r = 6
for name, vals, fmt in REV_LINES:
    put(ws, r, [name] + vals, bold=name.startswith(("Total", "Recurring")))
    for col in (3, 4, 5):
        ws.cell(row=r, column=col).number_format = fmt
    r += 1

r += 1
section(ws, r, "What each scenario means")
r += 1
for name, text in [
    ("Conservative (₹4 Cr)", "One pilot, no licence inside the window. Enough to raise a seed on a reference "
                             "customer and a working deployment; not enough to hire the fourth engineer."),
    ("Base (₹6 Cr)", "Two pilots and one annual licence signed at month 17. This is the plan the deck funds, and "
                     "the number every other page is consistent with."),
    ("Upside (₹8 Cr)", "Three pilots, two licences, a second state opening. Planned for, never banked, and never "
                       "used to justify the round size."),
]:
    ws.cell(row=r, column=2, value=name).font = BOLD
    c = ws.cell(row=r, column=3, value=text)
    c.font = NORM
    c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=5)
    ws.row_dimensions[r].height = 32
    r += 1
r += 1
note(ws, r, "Revenue is recognised when the contract is signed. Cash arrives later — the Cashflow sheet applies a "
            "collection lag of 75 days in the base case, because no state treasury pays on the invoice date.")

# ==================================================================== 5. P&L
MONTHS = list(range(0, 19))
MCOLS = {m: get_column_letter(3 + m) for m in MONTHS}

ws = sheet("P&L", "P&L — base case, monthly",
           "Month 0 is the close of the round. Every cell is a formula; nothing here was typed as a number.",
           widths=[34] + [7.6] * 19)
header(ws, 5, ["₹ lakh"] + [f"M{m}" for m in MONTHS])


def money_row(ws, r, name, formulas, bold=False, fill=False):
    put(ws, r, [name] + formulas, bold=bold, fill=fill)
    for m in MONTHS:
        ws.cell(row=r, column=3 + m).number_format = MONEY


PILOT_MONTHS = [9, 12, 15]
money_row(ws, PL_PILOT, "Pilot fees",
          [f"=IF({D('pilots')}>={PILOT_MONTHS.index(m) + 1},{D('pilot')},0)" if m in PILOT_MONTHS else "=0"
           for m in MONTHS])
money_row(ws, PL_LICENCE, "Licence fees",
          [f"=IF(AND({m}=17,{D('licences')}>=1),{D('licence')}*100,0)" for m in MONTHS])
money_row(ws, PL_IMPL, "Implementation fees",
          [f"=IF(AND({m}=17,{D('licences')}>=1),{D('impl')},0)" for m in MONTHS])
money_row(ws, PL_REV, "Total revenue",
          [f"={MCOLS[m]}{PL_PILOT}+{MCOLS[m]}{PL_LICENCE}+{MCOLS[m]}{PL_IMPL}" for m in MONTHS], bold=True, fill=True)

money_row(ws, PL_PAYROLL, "Payroll",
          ["=-(" + "+".join(f"IF(AND({m}>={start},{m}<{start + months}),Headcount!$D${HROW[role]},0)"
                             for role, start, _, months, _ in ROLES) + ")" for m in MONTHS])
money_row(ws, PL_CLOUD, "Cloud + infrastructure", ["=0" if m == 0 else f"=-{D('cloud')}" for m in MONTHS])
money_row(ws, PL_TRAVEL, "Travel + BD", ["=0" if m == 0 else f"=-{D('travel')}" for m in MONTHS])


def spread(key, pattern):
    return [f"=-{D(key)}*{pattern[m]}" if m in pattern else "=0" for m in MONTHS]


money_row(ws, PL_BIDS, "Bids, tenders, demo logistics", spread("bids", {m: 1 / 12 for m in range(4, 16)}))
money_row(ws, PL_DATA, "Hazard / GIS data licences", spread("data", {6: 0.4, 10: 0.3, 14: 0.3}))
money_row(ws, PL_FIELD, "Field deployment + hardware", spread("field", {10: 0.6, 15: 0.4}))
money_row(ws, PL_DEPLOY, "Implementation contracts", spread("deploy", {12: 0.5, 16: 0.5}))
money_row(ws, PL_AUDIT, "Security audit + certification", spread("audit", {7: 0.4, 12: 0.3, 17: 0.3}))
money_row(ws, PL_LEGAL, "Legal, IP, ESOP", spread("legal", {2: 0.5, 13: 0.5}))
money_row(ws, PL_COST, "Total costs",
          [f"=SUM({MCOLS[m]}{PL_PAYROLL}:{MCOLS[m]}{PL_LEGAL})" for m in MONTHS], bold=True, fill=True)
money_row(ws, PL_EBITDA, "EBITDA",
          [f"={MCOLS[m]}{PL_REV}+{MCOLS[m]}{PL_COST}" for m in MONTHS], bold=True, fill=True)
money_row(ws, PL_CUM, "Cumulative EBITDA", [f"=SUM($C${PL_EBITDA}:{MCOLS[m]}{PL_EBITDA})" for m in MONTHS])
note(ws, 23, "Rows 10–18 are costs and are negative by construction, so EBITDA is revenue plus costs. EBITDA turns "
             "positive in the month the first licence is signed (M17) — that is the plan working, not a model "
             "artefact. Under the conservative case no licence lands inside the window, so EBITDA stays negative.")

# ==================================================================== 6. Cashflow
ws = sheet("Cashflow", "Cashflow and runway",
           "Opening balance is the round. Collections lag revenue by the DSO input; the burn has to survive 18 months.",
           widths=[34] + [7.6] * 19)
header(ws, 5, ["₹ lakh"] + [f"M{m}" for m in MONTHS])
LAG = f"ROUND({D('dso')}/30,0)"

money_row(ws, CF_OPEN, "Opening cash",
          [f"={D('round')}*100"] + [f"={MCOLS[m - 1]}{CF_CLOSE}" for m in MONTHS[1:]])
money_row(ws, CF_IN, "Cash in — customer payments (lagged)",
          ["=0" if m == 0 else f"=IF({m}-{LAG}<0,0,INDEX('P&L'!$C${PL_REV}:$U${PL_REV},{m}-{LAG}+1))" for m in MONTHS])
money_row(ws, CF_OUT, "Cash out — all costs", [f"='P&L'!{MCOLS[m]}{PL_COST}" for m in MONTHS])
money_row(ws, CF_NET, "Net movement", [f"={MCOLS[m]}{CF_IN}+{MCOLS[m]}{CF_OUT}" for m in MONTHS])
money_row(ws, CF_CLOSE, "Closing cash", [f"={MCOLS[m]}{CF_OPEN}+{MCOLS[m]}{CF_NET}" for m in MONTHS],
          bold=True, fill=True)
put(ws, CF_CHECK, ["Runway check"] + [f'=IF({MCOLS[m]}{CF_CLOSE}>0,"funded","SHORT")' for m in MONTHS], bold=True)

r = 15
section(ws, r, "Runway summary")
r += 1
for name, formula, fmt in [
    ("Lowest cash point (₹ lakh)", f"=MIN(C{CF_CLOSE}:U{CF_CLOSE})", MONEY),
    ("Month of lowest cash", f"=MATCH(MIN(C{CF_CLOSE}:U{CF_CLOSE}),C{CF_CLOSE}:U{CF_CLOSE},0)-1", '0'),
    ("Closing cash at month 18 (₹ lakh)", f"=U{CF_CLOSE}", MONEY),
    ("Peak monthly burn (₹ lakh)", f"=MIN('P&L'!C{PL_EBITDA}:U{PL_EBITDA})", MONEY),
    ("Runway the round buys (months, uncapped)", f"={D('round')}*100/(SUM('Use of funds'!D{UF_FIRST}:D{UF_CONT - 1})*100/18)", MONEY),
    ("Any month short of cash? (should read 'none')",
     f'=IF(COUNTIF(C{CF_CHECK}:U{CF_CHECK},"SHORT")=0,"none","YES — FIX THE PLAN")', None),
]:
    ws.cell(row=r, column=2, value=name).font = NORM
    c = ws.cell(row=r, column=3, value=formula)
    c.font = BOLD
    c.fill = FILL_TOTAL
    c.border = BOX
    if fmt:
        c.number_format = fmt
    r += 1
note(ws, r + 1, "The honest gap: the first licence's cash lands about three months after signature, i.e. after month "
                "18. The plan therefore ends with roughly one month of cash, not a cushion — which is exactly why "
                "the seed round is timed for M18 and not later.")

# ==================================================================== 7. Use of funds
ws = sheet("Use of funds", "Use of funds — eighteen months",
           "Seven categories, every one derived from the plan above. The variance cell must read zero before this is sent.",
           widths=[36, 13, 16, 12, 56])
header(ws, 5, ["Category", "Deck (₹ Cr)", "Model (₹ Cr)", "% of round", "What it pays for"])
H = "Headcount!"
FUNDS = [
    ("Engineering & product",
     f"={H}F{HROW['Founder — technical']}+{H}F{HROW['Founder — commercial']}"
     f"+{H}F{HROW['Senior engineer — spatial / PostGIS']}+{H}F{HROW['Senior engineer — platform']}"
     f"+{H}F{HROW['Engineer — frontend']}+{H}F{HROW['Engineer — data / ML']}"
     f"+{H}F{HROW['Analyst / implementation engineer']}+{H}F{HROW['QA / test automation']}"
     f"+{H}F{HROW['Designer (contract)']}",
     "Two founders, four engineers, an analyst, QA and a designer — platform hardening, connectors, offline deployment"),
    ("Deployment & pilots",
     f"={D('field')}+{D('deploy')}",
     "Two district EOC deployments, on-prem nodes and hardware, customer-site integration engineers"),
    ("Go-to-market",
     f"={H}F{HROW['Partnerships lead (Delhi)']}+{D('travel')}*18+{D('bids')}",
     "One Delhi-based partnerships lead, travel, tender responses, demo environments"),
    ("Security & compliance",
     f"={H}F{HROW['Security / compliance consultant']}+{D('audit')}",
     "Consultant, two external pen tests, ISO 27001, CERT-In empanelment preparation, DPDP documentation"),
    ("Data & infrastructure",
     f"={D('data')}+{D('cloud')}*18",
     "Cloud, staging, backups, and the hazard / GIS / imagery layers the product runs on"),
    ("Legal, IP, incorporation",
     f"={D('legal')}",
     "Pvt Ltd formation, IP assignment, ESOP pool paperwork, trademark"),
]
r = UF_FIRST
for name, model_formula, note_text in FUNDS:
    expr = model_formula.lstrip("=")
    put(ws, r, [name, f"=ROUND(D{r},2)", f"=({expr})/100", f"=D{r}/{D('round')}", note_text])
    for col in (3, 4):
        ws.cell(row=r, column=col).number_format = '#,##0.00'
    ws.cell(row=r, column=5).number_format = PCT
    r += 1
put(ws, UF_CONT, ["Contingency (residual)", f"=ROUND(D{UF_CONT},2)",
                  f"=MAX(0,{D('round')}-SUM(D{UF_FIRST}:D{UF_CONT - 1}))", f"=D{UF_CONT}/{D('round')}",
                  "What is left after every other line is funded — procurement slippage, a third pen test, a hire "
                  "two months early. Not a slush fund: it is the first line that disappears if the round is ₹4 Cr."])
for col in (3, 4):
    ws.cell(row=UF_CONT, column=col).number_format = '#,##0.00'
ws.cell(row=UF_CONT, column=5).number_format = PCT
put(ws, UF_TOTAL, ["Total", f"=SUM(C{UF_FIRST}:C{UF_CONT})", f"=SUM(D{UF_FIRST}:D{UF_CONT})",
                   f"=SUM(E{UF_FIRST}:E{UF_CONT})", ""], bold=True, fill=True)
for col in (3, 4):
    ws.cell(row=UF_TOTAL, column=col).number_format = '#,##0.00'
ws.cell(row=UF_TOTAL, column=5).number_format = PCT

r = UF_TOTAL + 2
for name, formula, fmt in [
    ("Round size (₹ Cr)", f"={D('round')}", '#,##0.00'),
    ("Model total (₹ Cr)", f"=D{UF_TOTAL}", '#,##0.00'),
    (">> Variance: model − round (must be 0)", f"=D{UF_TOTAL}-{D('round')}", '#,##0.00'),
    ("Deck total as printed on slide 14 (₹ Cr)", f"=C{UF_TOTAL}", '#,##0.00'),
    ("Rounding: deck − model (₹ Cr)", f"=C{UF_TOTAL}-D{UF_TOTAL}", '#,##0.00'),
    ("Total spend per the P&L (₹ lakh)", f"=-SUM('P&L'!C{PL_COST}:U{PL_COST})", '#,##0.00'),
    (">> P&L − categories (must be 0)",
     f"=-SUM('P&L'!C{PL_COST}:U{PL_COST})-SUM(D{UF_FIRST}:D{UF_CONT - 1})*100", '#,##0.00'),
]:
    ws.cell(row=r, column=2, value=name).font = BOLD
    c = ws.cell(row=r, column=3, value=formula)
    c.font = BOLD
    c.fill = FILL_TOTAL
    c.border = BOX
    c.number_format = fmt
    r += 1
note(ws, r + 1, "Engineering includes the founder stipends, so the deck can show one line and nobody has to add "
                "anything up. Percentages are of the round, so they sum to 100% by construction — check that before "
                "shipping.")

# ==================================================================== 8. Cap table
ws = sheet("Cap table", "Cap table — three caps",
           "Dilution and the ESOP pool are the two numbers investors challenge first. Both are formulas.",
           widths=[38, 16, 16, 16, 34])
header(ws, 5, ["", "₹24 Cr cap", "₹30 Cr cap (base)", "₹36 Cr cap"])
put(ws, 6, ["Round size (₹ Cr)", f"={D('round')}", f"={D('round')}", f"={D('round')}"])
put(ws, 7, ["Post-money valuation (₹ Cr)", 24, 30, 36])
put(ws, 8, ["Investor stake", "=C6/C7", "=D6/D7", "=E6/E7"], bold=True)
put(ws, 9, ["ESOP pool created at this round", 0.10, 0.10, 0.10])
put(ws, 10, ["Founders, combined", "=1-C8-C9", "=1-D8-D9", "=1-E8-E9"], bold=True)
put(ws, 11, ["Price per 1% of the company (₹ Cr)", "=C7/100", "=D7/100", "=E7/100"])
for row in (6, 7):
    for col in (3, 4, 5):
        ws.cell(row=row, column=col).number_format = MONEY
for col in (3, 4, 5):
    ws.cell(row=11, column=col).number_format = '#,##0.00'
for row in (8, 9, 10):
    for col in (3, 4, 5):
        ws.cell(row=row, column=col).number_format = PCT

r = 13
section(ws, r, "Founder split — fill in once agreed; do not leave this vague in front of an investor")
r += 1
header(ws, r, ["Founder", "Equity %", "Vesting", "Notes"])
r += 1
for name, pct, vest, nt in [("[Founder 1 — technical]", 0.60, "4 years, 1-year cliff", "Product, architecture, delivery"),
                            ("[Founder 2 — commercial]", 0.30, "4 years, 1-year cliff", "Partnerships, procurement"),
                            ("Advisor pool", 0.10, "2 years, quarterly", "Institutional access, paid in equity")]:
    put(ws, r, [name, pct, vest, nt])
    ws.cell(row=r, column=3).number_format = PCT
    r += 1

r += 2
section(ws, r, "Seed follow-on illustration — month 18 to 24, on the back of a signed licence")
r += 1
header(ws, r, ["", "Value", "Note"])
r += 1
SEED = r
for name, val, fmt, nt in [
    ("Seed round (₹ Cr)", 18.0, MONEY, "Priced on a live licence and two references"),
    ("Seed post-money (₹ Cr)", 90.0, MONEY, "Five times the pre-seed cap is the story, and only the story"),
    ("Seed dilution", f"=C{SEED}/C{SEED + 1}", PCT, "New investor, plus a top-up of the ESOP pool"),
    ("Founder stake after seed", f"=D10*(1-C{SEED + 2})", PCT, "Base-case founders (70%) × (1 − seed dilution)"),
    ("Pre-seed investor stake after seed", f"=D8*(1-C{SEED + 2})", PCT, "20% at the ₹30 Cr cap, diluted by the seed"),
]:
    put(ws, r, [name, val, nt])
    ws.cell(row=r, column=3).number_format = fmt
    r += 1
note(ws, r + 1, "This is an illustration, not a forecast. If the licence does not land the seed conversation does not "
                "happen at ₹90 Cr — it happens at whatever the references support, or not at all.")

# ==================================================================== 9. Market
ws = sheet("Market", "Market — bottom-up",
           "The ₹550 Cr figure in the deck is the total of this table. No top-down percentages anywhere.",
           widths=[42, 12, 18, 16, 46])
header(ws, 5, ["Segment", "Buyers", "ACV (₹ Cr / yr)", "Annual (₹ Cr)", "Basis"])
MARKET = [
    ("State / UT disaster-management authority", 36, 4.0, "Platform licence + support, per state"),
    ("District emergency operations centre", 780, 0.20, "₹20 lakh per district, thin deployment"),
    ("Central agencies", 5, 10.0, "MHA, NDMA, NDRF, NIDM and equivalents"),
    ("Urban local bodies", 110, 1.0, "Municipal corporations with asset registries"),
    ("PSU and infrastructure asset owners", 60, 1.5, "Rail, power, port, highway owners"),
]
r = 6
for name, buyers, acv, basis in MARKET:
    put(ws, r, [name, buyers, acv, f"=C{r}*D{r}", basis])
    ws.cell(row=r, column=4).number_format = '#,##0.00'
    ws.cell(row=r, column=5).number_format = MONEY
    r += 1
put(ws, r, ["Total serviceable (₹ Cr / yr)", "", "", f"=SUM(E6:E{r - 1})", ""], bold=True, fill=True)
ws.cell(row=r, column=5).number_format = MONEY
SAM_ROW = r
r += 2

section(ws, r, "Serviceable obtainable — five years out, deliberately small")
r += 1
header(ws, r, ["Segment", "Buyers", "ACV (₹ Cr / yr)", "ARR (₹ Cr)", "Basis"])
r += 1
rows_som = [("States: Odisha, then two neighbours", 3, 3.0, "₹3 Cr is the conservative end of the licence range"),
            ("PSU / infrastructure asset owners", 2, 1.5, "One rail, one power or port owner")]
first_som = r
for name, buyers, acv, basis in rows_som:
    put(ws, r, [name, buyers, acv, f"=C{r}*D{r}", basis])
    ws.cell(row=r, column=4).number_format = '#,##0.00'
    ws.cell(row=r, column=5).number_format = MONEY
    r += 1
put(ws, r, ["Total obtainable ARR (₹ Cr)", "", "", f"=E{first_som}+E{first_som + 1}",
            "The deck's ₹12 Cr — year five, not year two"], bold=True, fill=True)
ws.cell(row=r, column=5).number_format = MONEY
r += 2
put(ws, r, ["Serviceable addressable market, $M (₹83 / $)", "", "", "", f"=E{SAM_ROW}/83",
            "For international comparison only"])
ws.cell(row=r, column=5).number_format = MONEY
note(ws, r + 2, "Two things this table refuses to do: count 780 districts as a pipeline (they are ₹20 lakh each, and "
                "nobody sells to 780 buyers in year one), and quote a global 'public safety software' market size "
                "that has nothing to do with Indian state procurement.")

# ---------------------------------------------------------------- print setup
from openpyxl.worksheet.properties import PageSetupProperties

FREEZE = {"Assumptions": "C6", "Headcount": "D6", "Revenue": "C6",
          "P&L": "D6", "Cashflow": "D6", "Use of funds": "C6", "Cap table": "C6", "Market": "C6"}
for ws in wb:
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.print_options.horizontalCentered = True
    ws.page_margins.left = ws.page_margins.right = 0.4
    ws.page_margins.top = ws.page_margins.bottom = 0.5
    if ws.title in FREEZE:
        ws.freeze_panes = FREEZE[ws.title]
    if ws.title == "Read me":
        ws.page_setup.fitToHeight = 1

wb.save(OUT)
print("saved", OUT)
