"""Charts for the GOTHAM INDIA pre-seed deck. Dark theme, transparent backgrounds."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from PIL import Image, ImageEnhance

OUT = Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)

BG = "#0B0F14"
AMBER = "#E8B04B"
TEAL = "#5FB3A1"
BLUE = "#5B8FD6"
RED = "#D9705B"
GREY = "#7C8899"
TEXT = "#D7DEE7"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "text.color": TEXT,
    "axes.labelcolor": TEXT,
    "xtick.color": GREY,
    "ytick.color": GREY,
    "axes.edgecolor": "#2A3542",
    "figure.facecolor": "none",
    "axes.facecolor": "none",
    "savefig.facecolor": "none",
})


def save(fig, name):
    fig.savefig(OUT / name, dpi=220, bbox_inches="tight", transparent=True)
    plt.close(fig)


def market():
    labels = ["State / UT\ndecision support", "District EOC\nlayer", "Central agencies\n(MHA, NDMA, NDRF)",
              "Urban local\nbodies", "PSU asset\nregistries"]
    vals = [144, 156, 50, 110, 90]
    fig, ax = plt.subplots(figsize=(7.6, 3.5))
    bars = ax.bar(labels, vals, color=[AMBER, AMBER, TEAL, TEAL, TEAL], width=0.62)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 5, f"\u20b9{v} Cr", ha="center", va="bottom",
                color=TEXT, fontsize=11, fontweight="bold")
    ax.set_ylim(0, 190)
    ax.set_ylabel("\u20b9 crore / year", fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", labelsize=9.5, length=0)
    ax.tick_params(axis="y", labelsize=9, length=0)
    ax.grid(axis="y", color="#1E2833", linewidth=0.8)
    ax.set_axisbelow(True)
    save(fig, "market.png")


def funds():
    labels = ["Engineering & product", "Deployment & pilots", "Go-to-market", "Security & compliance",
              "Data & infrastructure", "Legal / IP", "Contingency"]
    vals = [43, 17, 14, 8, 7, 4, 7]
    colors = [AMBER, BLUE, TEAL, "#9C8AD1", "#B08D57", GREY, "#3A4656"]
    fig, ax = plt.subplots(figsize=(4.4, 4.0))
    wedges, _ = ax.pie(vals, colors=colors, startangle=90, counterclock=False,
                       wedgeprops=dict(width=0.34, edgecolor=BG, linewidth=2))
    ax.text(0, 0.12, "\u20b96.0 Cr", ha="center", va="center", fontsize=17, fontweight="bold", color="#FFFFFF")
    ax.text(0, -0.18, "18 months", ha="center", va="center", fontsize=10, color=GREY)
    ax.legend(wedges, [f"{l}  {v}%" for l, v in zip(labels, vals)], loc="center left",
              bbox_to_anchor=(1.0, 0.5), frameon=False, fontsize=9.5, labelcolor=TEXT,
              handlelength=0.9, handleheight=0.9)
    save(fig, "funds.png")


def funnel():
    stages = ["Problem statements", "Startups engaged", "Contracts signed", "Purchase orders"]
    vals = [549, 619, 430, 45]
    fig, ax = plt.subplots(figsize=(7.4, 3.2))
    y = list(range(len(stages)))
    colors = [GREY, GREY, BLUE, AMBER]
    bars = ax.barh(y, vals, color=colors, height=0.55)
    for b, v in zip(bars, vals):
        ax.text(v + 12, b.get_y() + b.get_height() / 2, f"{v:,}", va="center", fontsize=12,
                fontweight="bold", color=TEXT)
    ax.set_yticks(y)
    ax.set_yticklabels(stages, fontsize=10.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 820)
    ax.spines[["top", "right", "bottom"]].set_visible(False)
    ax.tick_params(axis="both", length=0)
    ax.set_xticks([])
    save(fig, "funnel.png")


def bench():
    names = ["Spatial radius search\n(PostGIS KNN)", "Entity list,\npage 1", "Universal search",
             "AI answer\n(cited)", "Tenant overview\n(full scan)"]
    vals = [1.05, 0.14, 28.4, 59.4, 504.0]
    colors = [AMBER, AMBER, TEAL, TEAL, RED]
    fig, ax = plt.subplots(figsize=(7.6, 2.9))
    bars = ax.bar(names, vals, color=colors, width=0.55)
    ax.set_yscale("log")
    ax.set_ylim(0.08, 1600)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v * 1.2, f"{v:g} ms", ha="center", fontsize=10.5,
                fontweight="bold", color=TEXT)
    ax.set_ylabel("p50 latency (ms, log)", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", labelsize=8.5, length=0)
    ax.grid(axis="y", color="#1E2833", linewidth=0.8)
    ax.set_axisbelow(True)
    save(fig, "bench.png")


def timeline():
    rows = [
        ("Incorporate, DPIIT, GeM / iDEX", 0, 2, GREY),
        ("External security audit + DPDP posture", 2, 5, BLUE),
        ("Two design partners (LOI)", 3, 8, BLUE),
        ("Paid pilot #1 live", 7, 11, AMBER),
        ("Paid pilot #2", 10, 14, AMBER),
        ("First annual licence", 13, 17, TEAL),
        ("Seed round readiness", 15, 18, TEAL),
    ]
    fig, ax = plt.subplots(figsize=(8.4, 3.0))
    for i, (label, start, end, color) in enumerate(rows):
        ax.add_patch(FancyBboxPatch((start, i - 0.26), end - start, 0.52,
                                    boxstyle="round,pad=0.02,rounding_size=0.12",
                                    linewidth=0, facecolor=color, alpha=0.9))
        ax.text(end + 0.3, i, label, va="center", fontsize=9.5, color=TEXT)
    ax.set_xlim(0, 34)
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.set_yticks([])
    ax.set_xticks(range(0, 19, 3))
    ax.set_xticklabels([f"M{m}" for m in range(0, 19, 3)], fontsize=9)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", color="#1E2833", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.invert_yaxis()
    save(fig, "timeline.png")


def title_bg():
    src = Path("/home/user/gotham-india/frontend/e2e/screenshots/02-overview.png")
    img = Image.open(src).convert("RGB")
    img = ImageEnhance.Brightness(img).enhance(0.28)
    img = ImageEnhance.Color(img).enhance(0.5)
    img.save(OUT / "title_bg.png")


if __name__ == "__main__":
    market(); funds(); funnel(); bench(); timeline(); title_bg()
    print("charts written:", sorted(p.name for p in OUT.iterdir()))
