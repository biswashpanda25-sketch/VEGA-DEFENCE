"""GOTHAM INDIA — pre-seed pitch deck builder (python-pptx).

Design intent: the deck should look like the product — dark, dense, quiet, and confident.
Every number on a slide traces to docs/ or a public source listed in the appendix.
"""
import math
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

HERE = Path(__file__).parent
CHARTS = HERE / "charts"
SHOTS = Path("/home/user/gotham-india/frontend/e2e/screenshots")
OUT = HERE / "GOTHAM_INDIA_PreSeed_Deck.pptx"

# ---------------------------------------------------------------- palette
BG = RGBColor(0x0B, 0x0F, 0x14)
PANEL = RGBColor(0x14, 0x1B, 0x24)
CARD = RGBColor(0x18, 0x20, 0x29)
LINE = RGBColor(0x26, 0x31, 0x3D)
AMBER = RGBColor(0xE8, 0xB0, 0x4B)
TEAL = RGBColor(0x5F, 0xB3, 0xA1)
BLUE = RGBColor(0x5B, 0x8F, 0xD6)
RED = RGBColor(0xD9, 0x70, 0x5B)
WHITE = RGBColor(0xF4, 0xF7, 0xFA)
BODY = RGBColor(0xC6, 0xCF, 0xDA)
MUTED = RGBColor(0x8C, 0x99, 0xA8)

FONT = "Segoe UI"
W = Inches(13.333)
H = Inches(7.5)
ML = Inches(0.72)
CW = 11.89  # content width in inches

prs = Presentation()
prs.slide_width = W
prs.slide_height = H
BLANK = prs.slide_layouts[6]


# ---------------------------------------------------------------- primitives
def new_slide(bg=BG):
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = bg
    return s


def rect(s, x, y, w, h, fill=CARD, line=LINE, radius=0.03, shadow=False):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shp = s.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(0.75)
    if radius:
        try:
            shp.adjustments[0] = radius
        except Exception:
            pass
    shp.shadow.inherit = False
    shp.text_frame.word_wrap = True
    return shp


def tx(s, x, y, w, h, paras, anchor=MSO_ANCHOR.TOP, margins=(0, 0, 0, 0)):
    """paras: list of dicts {t, size, color, bold, space, align, spacing, font}"""
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Inches(margins[0])
    tf.margin_right = Inches(margins[1])
    tf.margin_top = Inches(margins[2])
    tf.margin_bottom = Inches(margins[3])
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = p.get("align", PP_ALIGN.LEFT)
        if p.get("space") is not None:
            para.space_after = Pt(p["space"])
        if p.get("spacing"):
            para.line_spacing = p["spacing"]
        run = para.add_run()
        run.text = p["t"]
        f = run.font
        f.name = p.get("font", FONT)
        f.size = Pt(p.get("size", 13))
        f.bold = p.get("bold", False)
        f.italic = p.get("italic", False)
        f.color.rgb = p.get("color", BODY)
    return box


def kicker(s, text, color=AMBER, y=0.52, x=None):
    tx(s, x if x is not None else 0.72, y, 9.0, 0.3,
       [{"t": text.upper(), "size": 10.5, "color": color, "bold": True}])


def _fit_size(text, w_in, candidates):
    """Largest font size in `candidates` at which `text` fits on a single line."""
    for size in candidates:
        chars = w_in * 72 / (0.575 * size)
        if len(text) <= chars:
            return size
    return candidates[-1]


def heading(s, text, y=0.82, size=30, w=11.9):
    size = _fit_size(text, w, [size, 28, 26, 24, 22])
    tx(s, 0.72, y, w, 0.9, [{"t": text, "size": size, "color": WHITE, "bold": True, "spacing": 0.95}])


def subhead(s, text, y=1.62, w=11.2, size=14.5, color=BODY):
    """Shrinks to keep a subhead on one line so it can never collide with the content below."""
    size = _fit_size(text, w, [size, 13.5, 12.5, 11.5, 10.5])
    tx(s, 0.72, y, w, 0.6, [{"t": text, "size": size, "color": color, "spacing": 1.15}])


def footer(s, idx, note="GOTHAM INDIA  ·  Pre-seed  ·  Confidential"):
    rect(s, 0.72, 7.02, CW, 0.012, fill=LINE, line=None, radius=0)
    tx(s, 0.72, 7.1, 8.0, 0.25, [{"t": note, "size": 8.5, "color": MUTED}])
    tx(s, 11.6, 7.1, 1.0, 0.25, [{"t": str(idx), "size": 8.5, "color": MUTED, "align": PP_ALIGN.RIGHT}])


def _text_height(parts, size, width_in, gap_pt=5.0):
    """Estimate rendered height (inches) of a paragraph list."""
    cpl = max(10, int(width_in * 72 / (0.52 * size)))
    total = 0.0
    for t in parts:
        lines = max(1, math.ceil(len(t) / cpl))
        total += lines * size * 1.33 / 72
    total += (len(parts) - 1) * gap_pt / 72
    return total


def card(s, x, y, w, h, title=None, body=None, accent=AMBER, body_size=11.5, title_size=10.5,
         min_size=8.6):
    rect(s, x, y, w, h)
    rect(s, x, y, 0.035, h, fill=accent, line=None, radius=0)
    px = x + 0.22
    inner = w - 0.44
    if title:
        tx(s, px, y + 0.15, inner, 0.3, [{"t": title.upper(), "size": title_size, "color": accent,
                                          "bold": True, "space": 0}])
    if body:
        avail = h - (0.58 if title else 0.3)
        size = body_size
        while size > min_size and _text_height(body, size, inner) > avail:
            size -= 0.4
        paras = [{"t": b, "size": round(size, 1), "color": BODY, "space": 4, "spacing": 1.1}
                 for b in body]
        tx(s, px, y + (0.5 if title else 0.16), inner, avail, paras)


def kpi(s, x, y, w, label, value, note=None, color=AMBER, vsize=30):
    tx(s, x, y, w, 0.25, [{"t": label.upper(), "size": 9, "color": MUTED, "bold": True}])
    tx(s, x, y + 0.23, w, 0.55, [{"t": value, "size": vsize, "color": color, "bold": True, "spacing": 0.9}])
    if note:
        tx(s, x, y + 0.23 + vsize / 72 * 1.25, w, 0.5,
           [{"t": note, "size": 9.5, "color": MUTED, "spacing": 1.1}])


def bullets(s, x, y, w, items, size=12.5, gap=8, color=BODY, marker="—", avail=None):
    if avail:
        flat = []
        for it in items:
            flat.extend(it if isinstance(it, tuple) else [it])
        while size > 8.6 and _text_height(flat, size, w, gap) > avail:
            size -= 0.4
    paras = []
    for it in items:
        if isinstance(it, tuple):
            head, rest = it
            paras.append({"t": f"{marker}  {head}", "size": size, "color": WHITE, "bold": True,
                          "space": 2, "spacing": 1.12})
            paras.append({"t": f"     {rest}", "size": size - 0.8, "color": color, "space": gap,
                          "spacing": 1.12})
        else:
            paras.append({"t": f"{marker}  {it}", "size": size, "color": color, "space": gap,
                          "spacing": 1.12})
    tx(s, x, y, w, 4.0, paras)


def pic(s, path, x, y, w=None, h=None):
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    return s.shapes.add_picture(str(path), Inches(x), Inches(y), **kw)


def source(s, text, y = 6.72):
    tx(s, 0.72, y, CW, 0.3, [{"t": text, "size": 8, "color": RGBColor(0x5E, 0x6A, 0x78), "spacing": 1.05}])


# ================================================================ 1. COVER
s = new_slide()
pic(s, CHARTS / "title_bg.png", 0, 0, w=13.333)
rect(s, 0, 0, 13.333, 7.5, fill=RGBColor(0x0B, 0x0F, 0x14), line=None, radius=0)
# re-tint above the screenshot for legibility
shp = s.shapes[-1]
shp.fill.solid()
shp.fill.fore_color.rgb = RGBColor(0x0B, 0x0F, 0x14)
shp.fill.transparency = 0.62

rect(s, 0.95, 1.55, 0.06, 1.05, fill=AMBER, line=None, radius=0)
tx(s, 1.25, 1.5, 9.0, 0.4, [{"t": "SOVEREIGN INTELLIGENCE  ·  DECISION SUPPORT", "size": 11.5,
                             "color": AMBER, "bold": True}])
tx(s, 1.22, 1.92, 10.5, 1.3, [{"t": "GOTHAM INDIA", "size": 54, "color": WHITE, "bold": True, "spacing": 0.9}])
tx(s, 1.25, 2.95, 9.6, 1.0, [{"t": "Decision support for the hours that decide outcomes.",
                              "size": 19, "color": BODY, "spacing": 1.1}])
tx(s, 1.25, 3.55, 9.4, 0.9, [{"t": "A working platform for Indian disaster response and public-infrastructure "
                                  "operations — auditable, sovereign-deployable, and measured.",
                              "size": 12.5, "color": MUTED, "spacing": 1.15}])

rect(s, 1.25, 4.72, 4.6, 1.15, fill=None, line=AMBER, radius=0.02)
tx(s, 1.45, 4.86, 4.2, 0.3, [{"t": "PRE-SEED", "size": 9.5, "color": AMBER, "bold": True}])
tx(s, 1.45, 5.08, 4.4, 0.45, [{"t": "₹6 Cr  ·  18 months", "size": 21, "color": WHITE, "bold": True}])
tx(s, 1.45, 5.48, 4.3, 0.3, [{"t": "range ₹4–8 Cr", "size": 9.5, "color": MUTED}])

tx(s, 6.35, 4.78, 5.9, 1.0, [
    {"t": "This is not a concept deck.", "size": 13, "color": WHITE, "bold": True, "space": 4},
    {"t": "The platform runs today: 61 automated tests on two databases, a 1,000,000-record "
          "benchmark, and a tamper-evident audit trail. Demo on request — we will hand you the laptop.",
     "size": 11, "color": MUTED, "spacing": 1.15}])

tx(s, 1.25, 6.55, 9.0, 0.3, [{"t": "Confidential · November 2026 · All demonstration data is synthetic",
                              "size": 9, "color": RGBColor(0x5E, 0x6A, 0x78)}])

# ================================================================ 2. ONE SLIDE
s = new_slide()
kicker(s, "The whole pitch on one slide")
heading(s, "India funds innovation. It rarely buys it.", y=1.0, size=27)

cols = [
    ("The gap", AMBER, [
        "Institutional data is spread across departments, spreadsheets and WhatsApp groups.",
        "During cyclone response, decisions worth ₹crores are taken without a shared, auditable picture.",
        "Existing tools are either bespoke SI projects or foreign platforms India cannot audit or host.",
    ]),
    ("What we built", TEAL, [
        "A working decision-support platform: ingestion, entity resolution, knowledge graph, cases, "
        "evidence-cited AI, geospatial search, and a hash-chained audit trail.",
        "Runs on PostgreSQL + PostGIS; deploys inside a state data centre.",
        "Measured, not described: 61 tests, 1M-record benchmark, security controls tested.",
    ]),
    ("What we need", BLUE, [
        "₹6 Cr for 18 months to convert a working platform into two paid pilots and one annual licence.",
        "Two design partners — a state disaster authority and a public-sector asset owner.",
        "Founders, plus four engineers and one partnerships lead.",
    ]),
]
x = 0.72
for title, color, items in cols:
    card(s, x, 2.15, 3.83, 3.15, title=title, body=items, accent=color, body_size=11.2)
    x += 4.03

rect(s, 0.72, 5.6, CW, 0.85, fill=PANEL, line=LINE)
tx(s, 0.95, 5.77, 11.4, 0.6, [{"t": "Why us, in one line: ", "size": 12, "color": AMBER, "bold": True},
                              {"t": "we are the rare team that shipped the hard parts first — audit, "
                                    "clearances, entity resolution, scale — instead of the screens.",
                               "size": 12, "color": BODY}])
footer(s, 2)

# ================================================================ 3. PROBLEM
s = new_slide()
kicker(s, "Problem")
heading(s, "The expensive failure is coordination, not data.")
subhead(s, "India has the money and the mandate. What it lacks is a shared operational picture that "
           "survives an audit.", y=1.6, w=10.5)

kpi(s, 0.72, 2.35, 2.6, "SDRF released, FY2026", "₹13,579 Cr", "to 27 states for immediate relief", AMBER, 24)
kpi(s, 3.55, 2.35, 2.6, "NDRF released, FY2026", "₹2,024 Cr", "for disasters beyond state capacity", AMBER, 24)
kpi(s, 6.38, 2.35, 2.9, "Domestic capital buy", "₹1.39 L Cr", "reserved for Indian industry, FY27", TEAL, 24)
kpi(s, 9.5, 2.35, 3.0, "iDEX purchase orders", "45", "from 619 engaged startups", RED, 24)

tx(s, 0.72, 3.72, 11.9, 0.3, [{"t": "THREE FAILURE MODES WE SEE IN EVERY DISTRICT REVIEW", "size": 10,
                               "color": MUTED, "bold": True}])
modes = [
    ("Nobody agrees on the record", "Three departments hold three versions of the same shelter, road or "
                                    "warehouse. Reconciliation happens in a meeting, after the decision."),
    ("Nothing is traceable", "Six weeks later, no one can reconstruct who knew what, when, and on what "
                             "evidence the order was issued."),
    ("Yesterday's data, today's decision", "Inventories and asset conditions are updated in monthly returns "
                                           "while the event moves in hours."),
]
x = 0.72
for t, b in modes:
    card(s, x, 4.1, 3.83, 1.75, title=t, body=[b], accent=RED, body_size=11)
    x += 4.03

tx(s, 0.72, 6.12, 11.9, 0.5, [{"t": "The cost is not software. It is duplicated relief, misallocated inventory, "
                                    "and decisions no institution can defend afterwards.",
                               "size": 12, "color": WHITE, "italic": True}])
source(s, "Sources: MHA/PIB SDRF & NDRF releases FY2025-26; MoD budget documents FY2026-27; "
          "iDEX/DIO public statements (Feb 2025 – 2026).", y=6.62)
footer(s, 3)

# ================================================================ 4. WHY NOW
s = new_slide()
kicker(s, "Why now")
heading(s, "Three things changed in the last eighteen months.")

rows = [
    ("01", "The mandate became statutory",
     "The Disaster Management (Amendment) Act, 2025 creates a National Disaster Database and requires states "
     "to maintain their own. A database mandate is a buying trigger — and an integration contract.",
     AMBER),
    ("02", "The procurement door opened",
     "GeM Startup Runway removes prior-turnover, prior-experience and EMD requirements for recognised "
     "startups; MoD reserved ₹1.39 lakh crore of capital acquisition for domestic industry. The entry cost "
     "for a small vendor has never been lower.",
     TEAL),
    ("03", "The build cost collapsed",
     "PostgreSQL/PostGIS, open models and commodity compute let a five-person team ship what needed forty "
     "people in 2019. We are the evidence: this platform was built in months, not years.",
     BLUE),
]
y = 1.9
for num, t, b, color in rows:
    rect(s, 0.72, y, CW, 1.35)
    tx(s, 0.95, y + 0.3, 0.8, 0.6, [{"t": num, "size": 22, "color": color, "bold": True}])
    tx(s, 1.85, y + 0.22, 3.3, 0.9, [{"t": t, "size": 14, "color": WHITE, "bold": True, "spacing": 1.05}])
    tx(s, 5.25, y + 0.2, 7.1, 1.0, [{"t": b, "size": 11.2, "color": BODY, "spacing": 1.16}])
    y += 1.52

rect(s, 0.72, 6.5, CW, 0.42, fill=PANEL, line=None)
tx(s, 0.95, 6.56, 11.4, 0.3, [{"t": "Read together: a legal requirement to hold the data, a low-cost route to "
                                   "sell into it, and a build cost that finally fits a small team.",
                               "size": 10.5, "color": AMBER, "bold": True}])
footer(s, 4)

# ================================================================ 5. WHAT WE BUILT
s = new_slide()
kicker(s, "What exists today", TEAL)
heading(s, "A working platform — not a prototype.")
subhead(s, "Five screens out of fifteen. Every screen reads live data from the database; nothing is mocked.",
        y=1.55, w=11.0)

shots = [(CHARTS / "shot_02-overview.png", 0.72, 2.05, 3.85),
         (CHARTS / "shot_03-graph.png", 4.72, 2.05, 3.85),
         (CHARTS / "shot_03-governance.png", 8.72, 2.05, 3.85)]
for path, x, y, w in shots:
    if path.exists():
        pic(s, path, x, y, w=w)
        rect(s, x, y, w, 2.17, fill=None, line=LINE, radius=0)

labels = [("Operational overview", "live counts, scoped by tenant and clearance"),
          ("Knowledge graph", "entities, relationships, provenance on every edge"),
          ("Governance console", "audit-chain verification, clearances, MFA")]
x = 0.72
for t, b in labels:
    tx(s, x, 4.32, 3.85, 0.25, [{"t": t, "size": 10.5, "color": WHITE, "bold": True}])
    tx(s, x, 4.55, 3.85, 0.3, [{"t": b, "size": 9, "color": MUTED}])
    x += 4.0

rect(s, 0.72, 5.0, CW, 0.012, fill=LINE, line=None, radius=0)
evidence = [("61", "automated tests\non SQLite and PostgreSQL"),
            ("1M", "records benchmarked\nwith published latencies"),
            ("0", "unsupported claims\nin the AI evaluation set"),
            ("3", "independently fixed\nscale defects, documented")]
x = 0.72
for v, l in evidence:
    tx(s, x, 5.18, 2.9, 0.6, [{"t": v, "size": 32, "color": AMBER, "bold": True}])
    tx(s, x, 5.82, 2.9, 0.5, [{"t": l, "size": 9.5, "color": BODY, "spacing": 1.1}])
    x += 3.0
source(s, "Full evidence: docs/TESTING.md, docs/SCALE.md, docs/EVALUATION.md in the repository.", y=6.6)
footer(s, 5)

# ================================================================ 6. HOW IT WORKS
s = new_slide()
kicker(s, "Architecture")
heading(s, "Five stages, one auditable record.", y=0.8, size=28)
subhead(s, "Every stage writes to the same append-only audit chain, so an analyst, a reviewer and an auditor "
           "see the same history.", y=1.5, w=11.2)

stages = [("Ingest", "CSV, XLSX, JSON, documents. Provenance, quality score and duplicate detection on entry.",
           AMBER),
          ("Resolve", "Fuzzy entity resolution with trigram blocking; merges are human-approved and reversible.",
           AMBER),
          ("Relate", "Relationships require evidence and a provenance class — asserted, inferred or imported.",
           TEAL),
          ("Analyse", "Cases, findings, graph and geospatial search; every view filtered by tenant and clearance.",
           TEAL),
          ("Decide", "AI answers cite source records or refuse; approvals are signed, timed and audited.", BLUE)]
x = 0.72
for i, (t, b, color) in enumerate(stages):
    rect(s, x, 2.05, 2.15, 1.75)
    rect(s, x, 2.05, 2.15, 0.05, fill=color, line=None, radius=0)
    tx(s, x + 0.18, 2.2, 1.8, 0.3, [{"t": f"0{i+1}", "size": 10, "color": color, "bold": True}])
    tx(s, x + 0.18, 2.45, 1.8, 0.3, [{"t": t, "size": 14, "color": WHITE, "bold": True}])
    tx(s, x + 0.18, 2.82, 1.8, 1.1, [{"t": b, "size": 9.5, "color": BODY, "spacing": 1.12}])
    if i < 4:
        tx(s, x + 2.2, 2.85, 0.3, 0.3, [{"t": "›", "size": 20, "color": MUTED}])
    x += 2.42

tx(s, 0.72, 4.28, 5.6, 0.3, [{"t": "WHY THIS ARCHITECTURE WINS GOVERNMENT DEALS", "size": 9.5,
                              "color": MUTED, "bold": True}])
left = ["Runs inside a state data centre — PostgreSQL and PostGIS, no foreign SaaS dependency.",
        "Clearance levels (INTERNAL → RESTRICTED → PROTECTED) are enforced in the data layer, not the UI.",
        "Hash-chained audit that a CAG or RTI audit can verify independently."]
right = ["Every retrieval is scoped before ranking: an analyst cannot be shown what they may not read.",
         "Synthetic-data-safe for demonstration; production data never leaves the buyer's environment.",
         "Interoperable by design: it is a layer above existing departmental systems, not a replacement."]
bullets(s, 0.72, 4.6, 5.7, left, size=10.5, gap=6)
bullets(s, 6.75, 4.6, 5.7, right, size=10.5, gap=6)
footer(s, 6)

# ================================================================ 7. WEDGE
s = new_slide()
kicker(s, "Go to market", AMBER)
heading(s, "One buyer, one budget line, one state.")
subhead(s, "Odisha: 30 districts, a coastline that meets a cyclone most years, and a state government that has "
           "already invested in disaster preparedness.", y=1.55, w=11.0)

card(s, 0.72, 2.05, 3.7, 2.2, title="Who pays", accent=AMBER, body=[
    "OSDMA / SDMA — holds the state disaster plan and mitigation budget.",
    "Board of Revenue & SRC — owns relief logistics and the state EOC.",
    "District collectors — first responder by law, own the district plan.",
])
card(s, 4.62, 2.05, 3.7, 2.2, title="From which line", accent=TEAL, body=[
    "State IT / e-governance budget for platform deployments.",
    "SDMF — ₹4,571 Cr released nationally in FY2025-26.",
    "District disaster funds for last-mile readiness.",
])
card(s, 8.52, 2.05, 4.09, 2.2, title="Through which door", accent=BLUE, body=[
    "GeM Startup Runway — no prior turnover or experience requirement.",
    "State RFP or limited tender for a ₹25–50 lakh pilot.",
    "iDEX/ADITI only if the requirement is defence-adjacent.",
])

tx(s, 0.72, 4.55, 11.9, 0.3, [{"t": "THE LAND-AND-EXPAND PATH", "size": 9.5, "color": MUTED, "bold": True}])
path = [("Paid pilot", "₹25–50 L · 3–6 months", "One district, one use case, real data."),
        ("State licence", "₹1.5–4 Cr / year", "State-wide deployment + support + training."),
        ("Adjacent states", "₹1.5–4 Cr each", "Same ontology, different geography."),
        ("Asset registries", "₹1–2 Cr / year", "PSU and municipal asset operations.")]
x = 0.72
for i, (t, v, b) in enumerate(path):
    rect(s, x, 4.9, 2.85, 1.5)
    tx(s, x + 0.18, 5.0, 2.5, 0.28, [{"t": t, "size": 11.5, "color": WHITE, "bold": True}])
    tx(s, x + 0.18, 5.3, 2.5, 0.28, [{"t": v, "size": 10.5, "color": AMBER, "bold": True}])
    tx(s, x + 0.18, 5.62, 2.5, 0.7, [{"t": b, "size": 9.5, "color": MUTED, "spacing": 1.1}])
    if i < 3:
        tx(s, x + 2.87, 5.35, 0.3, 0.3, [{"t": "›", "size": 16, "color": MUTED}])
    x += 3.05
source(s, "Budget figures: MHA/PIB SDRF-NDRF-SDMF-NDMF releases FY2025-26; Odisha SDMP public documents.", y=6.6)
footer(s, 7)

# ================================================================ 8. MARKET
s = new_slide()
kicker(s, "Market", TEAL)
heading(s, "A deliberately unglamorous number — built bottom-up.")
subhead(s, "We would rather defend ₹550 crore a year than be laughed at for quoting a percentage of a "
           "trillion-dollar forecast.", y=1.5, w=11.2)

pic(s, CHARTS / "market.png", 0.66, 2.05, w=7.2)
card(s, 8.1, 2.0, 4.5, 1.5, title="Serviceable, India", accent=AMBER, body=[
    "36 states/UTs, 780 districts, central agencies, 110 municipal corporations, PSU asset owners."])
tx(s, 8.3, 3.62, 4.1, 0.9, [{"t": "₹550 Cr / yr", "size": 25, "color": AMBER, "bold": True}])
tx(s, 8.3, 4.05, 4.1, 0.5, [{"t": "≈ $66 M recurring + services, FY2027 prices", "size": 9.5, "color": MUTED}])

card(s, 8.1, 4.45, 4.5, 1.05, title="Obtainable in 36 months", accent=TEAL, body=[
    "3 states + 2 PSU asset owners ≈ ₹12 Cr ARR."])
card(s, 8.1, 5.6, 4.5, 1.05, title="Adjacent expansion", accent=BLUE, body=[
    "Defence logistics only with a sponsor; allied governments."])
source(s, "Bottom-up: buyer count × realistic annual contract value. Assumptions are itemised in the financial "
          "model delivered with this pack.", y=6.62)
footer(s, 8)

# ================================================================ 9. BUSINESS MODEL
s = new_slide()
kicker(s, "Business model")
heading(s, "Land with a pilot. Earn a licence. Keep it for a decade.")

rows = [("Paid pilot", "₹25–50 lakh", "3–6 months, defined deliverables, one district or one PSU division.", AMBER),
        ("Implementation", "₹50 L – 2 Cr", "Data integration, ontology mapping, training, on-premise deployment.", TEAL),
        ("Annual licence + support", "₹1.5–4 Cr / yr", "Platform, updates, support SLA, security patching.", BLUE),
        ("Renewal expectation", "5+ years", "Data gravity and audit history make replacement expensive for the buyer.", MUTED)]
y = 1.95
for t, v, b, color in rows:
    rect(s, 0.72, y, 7.6, 1.02)
    rect(s, 0.72, y, 0.04, 1.02, fill=color, line=None, radius=0)
    tx(s, 0.95, y + 0.18, 2.6, 0.3, [{"t": t, "size": 12, "color": WHITE, "bold": True}])
    tx(s, 0.95, y + 0.52, 2.6, 0.3, [{"t": b, "size": 8.8, "color": MUTED, "spacing": 1.05}], )
    tx(s, 3.85, y + 0.28, 2.0, 0.4, [{"t": v, "size": 15, "color": color, "bold": True}])
    y += 1.15

card(s, 8.6, 1.95, 4.0, 2.2, title="Unit economics at licence", accent=AMBER, body=[
    "Gross margin 70–75% once deployed (hosting is the buyer's).",
    "Early deployments run 45–55% because services dominate year one.",
    "CAC is relationship-led: ~₹6–10 lakh per state, mostly travel and time.",
])
card(s, 8.6, 4.3, 4.0, 2.0, title="Why buyers renew", accent=TEAL, body=[
    "The audit history lives here — switching means losing the record.",
    "Training and process are built around the workflow.",
    "Procurement cost of change exceeds the licence cost.",
])
footer(s, 9)

# ================================================================ 10. COMPETITION
s = new_slide()
kicker(s, "Competition")
heading(s, "Four alternatives, and what each one can't do.")

# 2x2
ox, oy, w2, h2 = 0.72, 2.0, 6.4, 3.55
rect(s, ox, oy, w2, h2, fill=PANEL, line=LINE, radius=0)
rect(s, ox + w2 / 2, oy, 0.012, h2, fill=LINE, line=None, radius=0)
rect(s, ox, oy + h2 / 2, w2, 0.012, fill=LINE, line=None, radius=0)
tx(s, ox, oy + h2 - 0.32, 3.0, 0.25, [{"t": "BESPOKE  →", "size": 8.5, "color": MUTED, "bold": True}])
tx(s, ox + w2 - 1.3, oy + h2 - 0.32, 1.2, 0.25, [{"t": "PRODUCT", "size": 8.5, "color": MUTED,
                                                  "bold": True, "align": PP_ALIGN.RIGHT}])
tx(s, ox + 0.12, oy + 0.1, 1.4, 0.25, [{"t": "FOREIGN", "size": 8.5, "color": MUTED, "bold": True}])
tx(s, ox + 0.12, oy + h2 / 2 + 0.14, 1.6, 0.25, [{"t": "SOVEREIGN", "size": 8.5, "color": MUTED, "bold": True}])
tx(s, ox + 0.55, oy + 0.55, 2.4, 0.6, [{"t": "Palantir,\nforeign COTS", "size": 10.5, "color": MUTED}])
tx(s, ox + w2 / 2 + 0.4, oy + 0.55, 2.6, 0.6, [{"t": "Global SaaS\nanalytics", "size": 10.5, "color": MUTED}])
tx(s, ox + 0.55, oy + h2 / 2 + 0.55, 2.5, 0.6, [{"t": "TCS / Infosys /\nNIC custom builds", "size": 10.5, "color": MUTED}])
# our dot
dot = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(ox + w2 / 2 + 1.55), Inches(oy + h2 / 2 + 1.05), Inches(0.22), Inches(0.22))
dot.fill.solid(); dot.fill.fore_color.rgb = AMBER; dot.line.fill.background(); dot.shadow.inherit = False
tx(s, ox + w2 / 2 + 1.85, oy + h2 / 2 + 0.98, 1.6, 0.35, [{"t": "GOTHAM INDIA", "size": 10.5,
                                                            "color": AMBER, "bold": True}])

rect(s, 0.72, 5.72, 6.4, 0.9, fill=PANEL, line=LINE)
tx(s, 0.92, 5.85, 6.0, 0.65, [
    {"t": "The quadrant is nearly empty. ", "size": 10.5, "color": AMBER, "bold": True},
    {"t": "The closest product-shaped rival is foreign; the closest sovereign option is a bespoke build. "
          "That gap is the whole thesis.", "size": 10, "color": BODY, "spacing": 1.1}])

comp = [("Foreign platforms", "Best-in-class, but priced in dollars, hosted abroad, and unauditable by an Indian "
                              "auditor. Procurement and data-residency friction is our opening.", RED),
        ("System integrators", "They build it as a project, then leave. No product roadmap, no reuse across states, "
                               "and reinvention every tender.", RED),
        ("Departmental tools", "Excel, WhatsApp, a GIS dashboard nobody maintains. Zero cost, zero accountability, "
                               "and they fail exactly when the stakes are highest.", RED),
        ("Status quo", "The real competitor. Beaten by making the first pilot cheaper and faster than a committee "
                       "meeting to discuss it.", MUTED)]
x = 7.35
y = 2.0
for t, b, color in comp:
    rect(s, x, y, 5.25, 0.95)
    tx(s, x + 0.2, y + 0.12, 4.9, 0.25, [{"t": t, "size": 11, "color": WHITE, "bold": True}])
    tx(s, x + 0.2, y + 0.4, 4.9, 0.5, [{"t": b, "size": 8.8, "color": BODY, "spacing": 1.05}])
    y += 1.02
footer(s, 10)

# ================================================================ 11. MOAT
s = new_slide()
kicker(s, "Moat", TEAL)
heading(s, "What actually defends this — and what doesn't.")
subhead(s, "At pre-seed a moat is mostly a head start plus a switching cost. We will name both honestly.", y=1.55)

moats = [("Audit and clearance architecture", "Strong now",
          "Hash-chained audit, field-level redaction and clearance enforcement are hard to retrofit and are the "
          "first thing a security reviewer asks about. Competitors bolt these on late.", TEAL),
         ("Administrative ontology", "Compounding",
          "Districts, departments, schemes, funds and asset classes modelled the way Indian administration actually "
          "works. Each deployment deepens it; a generalist cannot buy this.", AMBER),
         ("Evidence discipline", "Differentiating",
          "Answers that cite the record or refuse. Cheap to demo, expensive to retrofit onto an LLM wrapper — and "
          "the first thing that destroys trust in a pilot.", AMBER),
         ("Deployment entrenchment", "Not yet earned",
          "Once the audit history, training and workflows live here, replacement is painful. This is a moat we "
          "will only have after the first renewal — we are not counting it today.", MUTED)]
x = 0.72
for t, status, b, color in moats:
    rect(s, x, 2.1, 2.9, 2.42)
    tx(s, x + 0.2, 2.25, 2.5, 0.3, [{"t": status.upper(), "size": 8.5, "color": color, "bold": True}])
    tx(s, x + 0.2, 2.55, 2.5, 0.62, [{"t": t, "size": 12.5, "color": WHITE, "bold": True, "spacing": 1.05}])
    tx(s, x + 0.2, 3.28, 2.5, 1.8, [{"t": b, "size": 9.6, "color": BODY, "spacing": 1.14}])
    x += 3.03

rect(s, 0.72, 4.85, CW, 1.1, fill=PANEL, line=LINE)
tx(s, 0.95, 5.0, 11.4, 0.85, [
    {"t": "What is not a moat: ", "size": 11.5, "color": AMBER, "bold": True},
    {"t": "the AI. Any team can call a model. The defensible assets are the ontology, the audit trail and the "
          "deployment — which is precisely why we built those first instead of a prettier chat box.",
     "size": 11, "color": BODY, "spacing": 1.12}])
footer(s, 11)

# ================================================================ 12. TRACTION
s = new_slide()
kicker(s, "Traction", RED)
heading(s, "What is real, and what is not.")
subhead(s, "You will hear this from us first: there is no revenue, no signed customer and no incorporated "
           "entity yet. Here is exactly what does exist.", y=1.5, w=11.3)

have = ["A production-shaped platform that runs end to end on synthetic data — 15 screens, 61 automated tests, "
        "green on both SQLite and PostgreSQL 17 + PostGIS.",
        "A published 1,000,000-record benchmark, including the slow paths we have not fixed yet.",
        "Security controls a procurement reviewer actually asks for: clearance-based access, hash-chained audit "
        "with tamper detection, MFA, failed-login throttling.",
        "A documented capability assessment against the category leader — we score ourselves at 16.3%, and we "
        "publish the rubric."]
missing = ["Revenue, pilots, LOIs or named prospects.",
           "A registered company, DPIIT recognition, or an ESOP pool.",
           "Security empanelment, STQC certification or any accreditation claim.",
           "A named founding team on this slide — see the next one; we have deliberately not dressed it up."]

rect(s, 0.72, 2.0, 5.85, 2.75)
tx(s, 0.95, 2.15, 5.4, 0.3, [{"t": "EXISTS TODAY", "size": 9.5, "color": TEAL, "bold": True}])
bullets(s, 0.95, 2.5, 5.4, have, size=10.2, gap=6, marker="+", avail=2.15)
rect(s, 6.78, 2.0, 5.83, 2.75)
tx(s, 7.0, 2.15, 5.4, 0.3, [{"t": "DOES NOT EXIST", "size": 9.5, "color": RED, "bold": True}])
bullets(s, 7.0, 2.5, 5.4, missing, size=10.2, gap=6, marker="×", avail=2.15)

tx(s, 0.72, 4.92, 11.9, 0.3, [{"t": "WHAT THIS PAGE SHOULD SAY AT MONTH 18", "size": 9.5, "color": MUTED,
                              "bold": True}])
targets = [("2", "paid pilots delivered"), ("1", "annual licence signed"), ("₹3–6 Cr", "contracted or in pipeline"),
           ("1", "named reference customer")]
x = 0.72
for v, l in targets:
    rect(s, x, 5.22, 2.87, 0.78)
    tx(s, x + 0.18, 5.3, 2.5, 0.3, [{"t": v, "size": 15, "color": WHITE, "bold": True}])
    tx(s, x + 0.18, 5.62, 2.5, 0.3, [{"t": l, "size": 9, "color": MUTED}])
    x += 3.02

rect(s, 0.72, 6.2, CW, 0.5, fill=PANEL, line=LINE)
tx(s, 0.95, 6.29, 11.4, 0.35, [{"t": "Why we lead with this: ", "size": 10.5, "color": AMBER, "bold": True},
                               {"t": "every number in this deck can be reproduced in a room with a laptop. "
                                     "Diligence will find the gaps anyway — better that we hand you the list.",
                                "size": 10.5, "color": BODY}])
footer(s, 12)

# ================================================================ 13. TEAM
s = new_slide()
kicker(s, "Team")
heading(s, "The honest version of the team slide.")
subhead(s, "This page is a template because we will not invent credentials. Fill it with your names, and keep the "
           "gaps visible — investors forgive a gap they can see.", y=1.5, w=11.3)

for i, (role, note) in enumerate([
        ("[FOUNDER NAME]", "Role · years in [domain] · what you shipped before"),
        ("[CO-FOUNDER NAME]", "Role · why you are the pair for this problem"),
        ("[ADVISOR NAME]", "Institutional credibility: former [cadre / service / PSU role]")]):
    x = 0.72 + i * 4.03
    rect(s, x, 2.15, 3.83, 1.75)
    rect(s, x, 2.15, 3.83, 0.05, fill=MUTED, line=None, radius=0)
    tx(s, x + 0.22, 2.35, 3.4, 0.35, [{"t": role, "size": 13, "color": MUTED, "bold": True}])
    tx(s, x + 0.22, 2.75, 3.4, 0.8, [{"t": note, "size": 9.8, "color": BODY, "spacing": 1.15}])

tx(s, 0.72, 4.1, 11.9, 0.3, [{"t": "THE GAP THAT MATTERS, AND HOW WE CLOSE IT", "size": 9.5, "color": MUTED,
                              "bold": True}])
gaps = [("No institutional insider", "Hire or advise-in a retired IAS/IPS officer or a former OSDMA official with "
                                     "procurement experience. Budgeted: ₹12–18 lakh a year."),
        ("No certification", "External security audit in month 2–5; STQC/empanelment pathway scoped with a "
                             "consultant. Budgeted in use of funds, not gestured at."),
        ("Thin bench", "Four engineers by month 6, two of them senior. Until then, scope is deliberately narrow: "
                       "one state, one workflow, one buyer.")]
x = 0.72
for t, b in gaps:
    card(s, x, 4.45, 3.83, 1.6, title=t, body=[b], accent=RED, body_size=9.8)
    x += 4.03
footer(s, 13)

# ================================================================ 14. USE OF FUNDS
s = new_slide()
kicker(s, "Use of funds")
heading(s, "₹6 crore, eighteen months, one licence.")
subhead(s, "Pre-seed money buys focus: no sales team, no office, no marketing, no second product. Every line below is "
           "a formula in the attached model, not a round number chosen to look reasonable.", y=1.32, w=11.6)
pic(s, CHARTS / "funds.png", 0.6, 1.98, w=4.45)

items = [("Engineering & product — ₹2.60 Cr · 43%",
          "Two founders, four engineers, an analyst, QA, a designer. Platform hardening, connectors, "
          "offline deployment automation."),
         ("Deployment & pilots — ₹1.00 Cr · 17%",
          "Two district EOC deployments, on-premise hardware, engineers on site. This is why we win against "
          "a SaaS link."),
         ("Go-to-market — ₹0.81 Cr · 14%",
          "One Delhi-based partnerships lead, travel to Bhubaneswar and Delhi, tender responses, demo "
          "environments."),
         ("Security & compliance — ₹0.46 Cr · 8%",
          "Two external penetration tests, ISO 27001, CERT-In empanelment preparation, DPDP documentation."),
         ("Data & infrastructure — ₹0.44 Cr · 7%",
          "Cloud, staging, backups, and the hazard, GIS and imagery layers the product runs on."),
         ("Legal, IP, incorporation — ₹0.25 Cr · 4%",
          "Private limited formation, IP assignment, ESOP pool, trademark."),
         ("Contingency — ₹0.44 Cr · 7%",
          "Procurement slippage, a third pen test, a hire two months early. First line to go if the round is "
          "₹4 Cr.")]
y = 1.95
for t, b in items:
    tx(s, 5.5, y, 7.2, 0.24, [{"t": t, "size": 10.8, "color": WHITE, "bold": True}])
    tx(s, 5.5, y + 0.24, 7.2, 0.38, [{"t": b, "size": 8.9, "color": MUTED, "spacing": 1.06}])
    y += 0.615

source(s, "Seven categories, ₹6.00 Cr, variance to the round ₹0.00 — reconciled to the P&L line by line in the "
          "attached .xlsx, which also carries three revenue scenarios and the monthly cashflow.", y=6.6)
footer(s, 14)

# ================================================================ 15. PLAN
s = new_slide()
kicker(s, "Plan")
heading(s, "Eighteen months, seven gates.", y=0.8, size=28)
subhead(s, "Each gate has a number attached. If a gate fails, we say so and change the plan — we do not move the "
           "goalposts.", y=1.5, w=11.2)
pic(s, CHARTS / "timeline.png", 0.62, 1.95, w=8.5)

gates = [("M2", "Incorporated, DPIIT, GeM + iDEX registered"),
         ("M5", "Security audit passed; findings closed"),
         ("M8", "Two design partners signed (LOI)"),
         ("M11", "Paid pilot #1 live on partner data"),
         ("M14", "Paid pilot #2; renewal intent documented"),
         ("M17", "First annual licence signed"),
         ("M18", "Seed-ready: ₹3–6 Cr contracted/pipeline")]
y = 1.9
for m, g in gates:
    tx(s, 9.45, y, 0.7, 0.26, [{"t": m, "size": 10, "color": AMBER, "bold": True}])
    tx(s, 10.15, y, 2.45, 0.5, [{"t": g, "size": 8.8, "color": BODY, "spacing": 1.05}])
    y += 0.54

rect(s, 0.72, 5.85, CW, 0.62, fill=PANEL, line=LINE)
tx(s, 0.95, 5.98, 11.4, 0.4, [{"t": "Kill criteria, stated now: ", "size": 10.5, "color": RED, "bold": True},
                              {"t": "if by month 9 there is no signed design partner and no paid pilot, we stop "
                                    "spending and return the balance rather than extend the runway.",
                               "size": 10.5, "color": BODY}])
footer(s, 15)

# ================================================================ 16. RISKS
s = new_slide()
kicker(s, "Risks", RED)
heading(s, "What could kill this, and what we do about it.")

risks = [("No design partner materialises", "Fatal",
          "90-day founder-led outreach: 10 state departments, 5 PSUs, 3 OEMs. Offer a free 60-day pilot to one "
          "district to create the first reference.", RED),
         ("Procurement takes 12–18 months", "High",
          "Bridge with paid pilots and private-sector buyers (insurers, logistics) who sign in weeks, not fiscal "
          "years.", AMBER),
         ("Security clearance / empanelment", "High",
          "Start the audit and paperwork in month 2. Until it exists we do not claim it — buyers check.", AMBER),
         ("Incumbent SI undercuts on price", "Medium",
          "Partner as a sub-contractor to the SI rather than fight them: they need a product, we need their "
          "contract vehicle.", TEAL),
         ("A single sponsor leaves", "Medium",
          "Never more than 40% of revenue from one department; parallel state pipeline from month 12.", TEAL)]
y = 1.9
for t, sev, mit, color in risks:
    rect(s, 0.72, y, CW, 0.92)
    tx(s, 0.95, y + 0.14, 4.1, 0.3, [{"t": t, "size": 11.5, "color": WHITE, "bold": True}])
    tx(s, 0.95, y + 0.46, 4.1, 0.3, [{"t": sev.upper() + " SEVERITY", "size": 8, "color": color, "bold": True}])
    tx(s, 5.3, y + 0.2, 7.1, 0.6, [{"t": mit, "size": 10, "color": BODY, "spacing": 1.1}])
    y += 1.0
footer(s, 16)

# ================================================================ 17. ASK
s = new_slide()
kicker(s, "The ask", AMBER)
heading(s, "₹6 crore to turn a working platform into a bought one.", y=0.85, size=28)

card(s, 0.72, 1.95, 5.7, 2.35, title="The round", accent=AMBER, body=[
    "₹6 Cr for 18 months of runway (range ₹4–8 Cr accepted).",
    "SAFE or equity at a ₹24–36 Cr post-money cap — 17–25% dilution.",
    "Use: 43% engineering, 17% deployment and pilots, 14% go-to-market, 19% security, data and legal, 7% buffer.",
    "What it buys: two paid pilots and one annual licence.",
], body_size=10.5)
card(s, 6.62, 1.95, 5.99, 2.35, title="What we need beyond money", accent=TEAL, body=[
    "Intros to OSDMA, a state IT secretary, or a PSU asset owner — one warm introduction beats fifty cold emails.",
    "A security reviewer who will tell us what an empanelment audit will actually ask.",
    "Discipline: a board member who will hold us to the month-9 kill criteria.",
], body_size=11)

rect(s, 0.72, 4.75, CW, 1.0, fill=PANEL, line=AMBER)
tx(s, 0.95, 4.9, 11.4, 0.75, [
    {"t": "The five-minute version: ", "size": 12, "color": AMBER, "bold": True},
    {"t": "India has a legal mandate for institutional data, a procurement route for startups and a coordination "
          "problem that costs crores every monsoon. We built the hard part and measured it. Six crore buys the "
          "first two paid deployments.", "size": 11.5, "color": BODY, "spacing": 1.14}])

tx(s, 0.72, 6.0, 5.5, 0.3, [{"t": "[FOUNDER NAME]", "size": 11, "color": WHITE, "bold": True}])
tx(s, 0.72, 6.28, 5.5, 0.3, [{"t": "[email]  ·  [phone]  ·  Bhubaneswar, Odisha", "size": 10, "color": MUTED}])
tx(s, 6.6, 6.0, 6.0, 0.3, [{"t": "Due-diligence pack included with this deck", "size": 10, "color": WHITE,
                            "bold": True}])
tx(s, 6.6, 6.28, 6.0, 0.3, [{"t": "Financial model · investor FAQ · data-room checklist · live demo script",
                             "size": 9.5, "color": MUTED}])
footer(s, 17)

# ================================================================ APPENDIX A1
s = new_slide()
kicker(s, "Appendix · engineering evidence", TEAL)
heading(s, "Benchmarked at one million records.", y=0.85, size=27)
subhead(s, "PostgreSQL 17 + PostGIS 3.5, schema built by migration, measured through the real HTTP stack. The red "
           "bar is a known limitation we have not fixed.", y=1.45, w=11.6)
pic(s, CHARTS / "bench.png", 0.66, 2.0, w=7.5)
card(s, 8.4, 2.0, 4.2, 1.25, title="Also measured", accent=TEAL, body=[
    "Load: 39,000 rows/sec. Index build: 14 seconds. Graph traversal at 300,000 edges."])
card(s, 8.4, 3.4, 4.2, 1.25, title="Bugs the benchmark found", accent=AMBER, body=[
    "JIT overhead (+180 ms per query), a PostGIS index the planner never used, and unbounded retrieval."])
card(s, 8.4, 4.8, 4.2, 1.25, title="Not yet proven", accent=RED, body=[
    "10 million records, partitioning, connection pooling, multi-node deployment."])
tx(s, 0.72, 6.2, 11.9, 0.4, [{"t": "Reproduce it: backend/tests/scale.py and bench_scale.py in the repository.",
                              "size": 9.5, "color": MUTED}])
footer(s, 18)

# ================================================================ APPENDIX A2
s = new_slide()
kicker(s, "Appendix · security posture", BLUE)
heading(s, "The controls a procurement reviewer will ask about.", y=0.85, size=26)
controls = [("Clearance-based access", "INTERNAL / RESTRICTED / PROTECTED enforced in the data layer; "
                                        "above-clearance reads return 404, not 403 — existence is not disclosed."),
            ("Tamper-evident audit", "Every action is hash-chained; a single edited row breaks verification and "
                                     "names the record. Verifiable by an external auditor."),
            ("Purpose-bound fields", "Contact fields are redacted unless a stated purpose and sufficient clearance "
                                     "are present; the purpose is written into the audit row."),
            ("MFA + throttling", "TOTP enrolment and enforced sign-in challenge; failed-attempt throttling."),
            ("Tenant isolation", "Every query is scoped before ranking, including search and AI retrieval."),
            ("Not claimed", "We hold no STQC/empanelment/ISO certification. We do not claim compliance we have "
                            "not been audited for.")]
y = 1.75
for t, b in controls:
    rect(s, 0.72, y, 5.8, 0.78)
    tx(s, 0.92, y + 0.1, 5.4, 0.24, [{"t": t, "size": 10.5, "color": WHITE, "bold": True}])
    tx(s, 0.92, y + 0.34, 5.4, 0.4, [{"t": b, "size": 8.5, "color": BODY, "spacing": 1.05}])
    y += 0.84
card(s, 6.85, 1.75, 5.76, 2.4, title="What an empanelment audit will still demand", accent=RED, body=[
    "External penetration test report and remediation evidence.",
    "Source-code escrow and secure SDLC documentation.",
    "Data-residency and DPDP Act compliance assessment.",
    "Incident response runbook and on-call commitments.",
    "We have budgeted for these; we do not have them yet.",
], body_size=10)
card(s, 6.85, 4.3, 5.76, 1.75, title="Boundaries written into the product", accent=TEAL, body=[
    "No surveillance, no individual tracking, no targeting or intercept capability.",
    "No fabricated data: every demonstration record is labelled synthetic in the interface.",
    "Consequential decisions stay human — the platform recommends and records, it does not act.",
], body_size=10)
footer(s, 19)

# ================================================================ APPENDIX A3
s = new_slide()
kicker(s, "Appendix · comparables", MUTED)
heading(s, "What the category leader proves — and what it doesn't.", y=0.85, size=26)
subhead(s, "Palantir FY2025: $4.48 B revenue, 54% government. The lesson is that sovereign decision software is a "
           "durable business; the warning is that it took twenty years and a defence relationship to get there.",
        y=1.5, w=11.6)

comp_rows = [("Palantir (FY2025)", "$4.48 B revenue · 54% government · ~$354 B market cap · 4,429 staff",
              "Proves the category. Not our comparable at pre-seed; nobody in India buys at that price."),
             ("Indian defence-tech", "$432 M raised cumulatively; ~71% of it drones and counter-drone",
              "Capital is flowing, and it is concentrated in hardware. Software decision layers are under-built."),
             ("iDEX ecosystem", "619 startups engaged · 430 contracts · 45 purchase orders",
              "The conversion gap is the opportunity: buyers need deployable product, not more prototypes."),
             ("Indian IT services", "Large SI incumbents own the contract vehicles",
              "They are our channel, not our enemy — a product layer makes their delivery cheaper.")]
y = 2.25
for name, fact, why in comp_rows:
    rect(s, 0.72, y, CW, 0.95)
    tx(s, 0.95, y + 0.15, 2.9, 0.3, [{"t": name, "size": 11, "color": WHITE, "bold": True}])
    tx(s, 3.95, y + 0.15, 4.5, 0.5, [{"t": fact, "size": 9.2, "color": AMBER, "spacing": 1.05}])
    tx(s, 8.6, y + 0.15, 3.85, 0.65, [{"t": why, "size": 9, "color": BODY, "spacing": 1.05}])
    y += 1.03
source(s, "Sources: Palantir FY2025 10-K; Inc42 defence-tech landscape; iDEX/DIO statements, Feb 2025–2026.", y=6.6)
footer(s, 20)

# ================================================================ APPENDIX A4
s = new_slide()
kicker(s, "Appendix · the line we do not cross", AMBER)
heading(s, "Why we bound the product — and why that sells.", y=0.85, size=27)

left_card = [("We will build", TEAL, [
    "Coordination, logistics, asset condition, evidence-cited analysis, audit and reporting for civilian "
    "institutions.",
    "Decision support where a named human approves every consequential action.",
    "Systems that can be inspected by the institution that buys them.",
]), ("We will not build", RED, [
    "Weapons, targeting, strike planning or fire-control integration.",
    "Surveillance, covert tracking of individuals, or interception.",
    "Credential theft, intrusion tooling, or anything that requires breaking the law to demonstrate.",
])]
y = 1.85
for title, color, items in left_card:
    rect(s, 0.72, y, 5.75, 1.85)
    tx(s, 0.95, y + 0.15, 5.2, 0.3, [{"t": title.upper(), "size": 10, "color": color, "bold": True}])
    bullets(s, 0.95, y + 0.5, 5.2, items, size=10.2, gap=6, avail=1.25)
    y += 2.05

card(s, 6.8, 1.85, 5.81, 4.05, title="Why this is commercial, not just ethical", accent=AMBER, body=[
    "Indian institutional buyers — and their legal advisers — are far more likely to sign with a vendor whose "
    "capability boundary is written down than one who says yes to everything.",
    "A narrow scope means a shorter security review, a cheaper audit and a defensible contract.",
    "It also means we will lose deals to vendors who say yes to surveillance work. That is a trade we make "
    "deliberately, and it is written into the product, not just this page.",
], body_size=11)
footer(s, 21)

prs.save(OUT)
print(f"saved {OUT} with {len(prs.slides.__iter__.__self__._sldIdLst)} slides")
