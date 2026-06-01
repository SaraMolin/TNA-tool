"""
HITL Activity Diagram — generates a UML-style activity diagram of the
Human-In-The-Loop TNA system, suitable for academic papers.

Usage:
    python -m evaluation.hitl_diagram
Output:
    output/hitl_activity_diagram.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUTPUT_PATH = Path("output/hitl_activity_diagram.png")

# ── Layout constants ───────────────────────────────────────────────────────────
FIG_W, FIG_H = 9, 14.5
LANE_W = 4.0          # width of each swim lane
LANE_GAP = 0.1        # gap between lanes
LEFT_X = 0.7          # left edge of left lane
MID_X = LEFT_X + LANE_W + LANE_GAP   # left edge of right lane
RIGHT_X = MID_X + LANE_W

HUMAN_CX = LEFT_X + LANE_W / 2       # centre-x of Human lane
SYS_CX   = MID_X  + LANE_W / 2       # centre-x of System lane

BOX_W  = 2.9          # activity box width
BOX_H  = 0.52         # activity box height
DIAM_S = 0.42         # decision diamond half-size

LANE_COLOR   = "#f5f5f5"
BORDER_COLOR = "#cccccc"
BOX_COLOR    = "white"
BOX_EDGE     = "#333333"
ARROW_COLOR  = "#222222"
FONT_SIZE    = 8.5
HEADER_SIZE  = 10


def box(ax, cx, cy, text, width=BOX_W, height=BOX_H, style="round,pad=0.05"):
    """Draw a rounded-rectangle activity node."""
    patch = FancyBboxPatch(
        (cx - width / 2, cy - height / 2),
        width, height,
        boxstyle=style,
        linewidth=1.2,
        edgecolor=BOX_EDGE,
        facecolor=BOX_COLOR,
        zorder=3,
    )
    ax.add_patch(patch)
    ax.text(cx, cy, text, ha="center", va="center",
            fontsize=FONT_SIZE, zorder=4, wrap=True,
            multialignment="center",
            fontfamily="sans-serif")


def diamond(ax, cx, cy, text):
    """Draw a decision diamond."""
    s = DIAM_S
    xs = [cx,     cx + s, cx,     cx - s, cx]
    ys = [cy + s, cy,     cy - s, cy,     cy + s]
    ax.fill(xs, ys, color=BOX_COLOR, edgecolor=BOX_EDGE, linewidth=1.2, zorder=3)
    ax.text(cx, cy, text, ha="center", va="center",
            fontsize=FONT_SIZE - 0.5, zorder=4, fontfamily="sans-serif")


def start_node(ax, cx, cy, r=0.18):
    circle = plt.Circle((cx, cy), r, color="#222222", zorder=4)
    ax.add_patch(circle)


def end_node(ax, cx, cy, r_outer=0.22, r_inner=0.13):
    outer = plt.Circle((cx, cy), r_outer, color="#222222", zorder=4)
    inner = plt.Circle((cx, cy), r_inner, color="white", zorder=5)
    ax.add_patch(outer)
    ax.add_patch(inner)


def arrow(ax, x1, y1, x2, y2, label="", label_side="right"):
    """Draw a vertical or horizontal arrow."""
    ax.annotate(
        "",
        xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="-|>",
            color=ARROW_COLOR,
            lw=1.2,
            mutation_scale=12,
        ),
        zorder=2,
    )
    if label:
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        dx = 0.18 if label_side == "right" else -0.18
        ax.text(mx + dx, my, label, fontsize=FONT_SIZE - 1,
                ha="left" if label_side == "right" else "right",
                va="center", color="#555555", fontfamily="sans-serif", zorder=5)


def cross_lane_arrow(ax, x_from, y_from, x_to, y_to):
    """Elbow arrow: down to mid-y, then horizontal to target lane."""
    y_mid = (y_from + y_to) / 2
    ax.plot([x_from, x_from], [y_from, y_mid], color=ARROW_COLOR, lw=1.2, zorder=2)
    ax.annotate("", xy=(x_to, y_to),
                xytext=(x_from, y_mid),
                arrowprops=dict(arrowstyle="-|>", color=ARROW_COLOR,
                                lw=1.2, mutation_scale=12,
                                connectionstyle="arc3,rad=0.0"), zorder=2)


def draw():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, FIG_H)
    ax.axis("off")

    # ── Swim lane backgrounds ──────────────────────────────────────────────
    lane_top    = FIG_H - 0.5
    lane_bottom = 0.4

    for lx, label in [(LEFT_X, "Human (Analyst)"), (MID_X, "System")]:
        bg = mpatches.FancyBboxPatch(
            (lx, lane_bottom), LANE_W, lane_top - lane_bottom,
            boxstyle="round,pad=0.05",
            linewidth=1,
            edgecolor=BORDER_COLOR,
            facecolor=LANE_COLOR,
            zorder=0,
        )
        ax.add_patch(bg)
        ax.text(lx + LANE_W / 2, lane_top - 0.22, label,
                ha="center", va="center",
                fontsize=HEADER_SIZE, fontweight="bold",
                fontfamily="sans-serif", color="#222222", zorder=1)

    ax.plot([MID_X, MID_X], [lane_bottom, lane_top],
            color=BORDER_COLOR, lw=1, zorder=1)

    # ── Node y-positions (top → bottom) ───────────────────────────────────
    y_start   = FIG_H - 1.1
    y_upload  = y_start   - 0.85
    y_ingest  = y_upload  - 1.05
    y_preproc = y_ingest  - 1.05
    y_select  = y_preproc - 1.05
    y_prompt  = y_select  - 0.95   # Human: configure / adjust prompt
    y_trigger = y_prompt  - 0.95   # Human: trigger analysis
    y_filter  = y_trigger - 1.00
    y_llm     = y_filter  - 1.00
    y_sim     = y_llm     - 1.00   # System: evaluate semantic similarity
    y_dec     = y_sim     - 1.00   # System: score ≥ threshold? (diamond)
    # YES  → review in Human lane at same y as y_dec
    y_review  = y_dec              # Human: review & accept
    y_correct = y_dec     - 1.00   # Human: review output (NO branch)
    y_export  = y_correct - 0.90
    y_end     = y_export  - 0.75

    cx_mid = (HUMAN_CX + SYS_CX) / 2

    # ── Nodes ─────────────────────────────────────────────────────────────
    start_node(ax, cx_mid, y_start)

    box(ax, HUMAN_CX, y_upload,  "Upload PDF\n& select document type")
    box(ax, SYS_CX,   y_ingest,  "Ingest PDF\n& convert to Markdown")
    box(ax, SYS_CX,   y_preproc, "Preprocess: remove tables / ToC\nextract headings → create chunks")
    box(ax, HUMAN_CX, y_select,  "Select chapter\n& subsection")
    box(ax, HUMAN_CX, y_prompt,  "Configure /\nadjust prompt")
    box(ax, HUMAN_CX, y_trigger, "Trigger analysis\n(\"Kör analys\")")
    box(ax, SYS_CX,   y_filter,  "Filter chunks by selection\n& send to LLM (Azure OpenAI)")
    box(ax, SYS_CX,   y_llm,     "LLM generates structured TNA\n(tasks → subtasks → steps)")
    box(ax, SYS_CX,   y_sim,     "Evaluate semantic similarity\nvs ground truth")
    diamond(ax, SYS_CX, y_dec,   "Score ≥\nthreshold?")
    box(ax, HUMAN_CX, y_review,  "Review & accept results")
    box(ax, HUMAN_CX, y_correct, "Review output\n(score below threshold)")
    box(ax, HUMAN_CX, y_export,  "Download Excel export")
    end_node(ax, cx_mid, y_end)

    # ── Arrows ────────────────────────────────────────────────────────────
    # Start → Upload
    arrow(ax, cx_mid, y_start - 0.18, HUMAN_CX, y_upload + BOX_H / 2)

    # Upload → Ingest (cross-lane)
    cross_lane_arrow(ax, HUMAN_CX, y_upload - BOX_H / 2, SYS_CX, y_ingest + BOX_H / 2)

    # Ingest → Preprocess
    arrow(ax, SYS_CX, y_ingest - BOX_H / 2, SYS_CX, y_preproc + BOX_H / 2)

    # Preprocess → Select (cross-lane)
    cross_lane_arrow(ax, SYS_CX, y_preproc - BOX_H / 2, HUMAN_CX, y_select + BOX_H / 2)

    # Select → Configure prompt
    arrow(ax, HUMAN_CX, y_select - BOX_H / 2, HUMAN_CX, y_prompt + BOX_H / 2)

    # Configure prompt → Trigger
    arrow(ax, HUMAN_CX, y_prompt - BOX_H / 2, HUMAN_CX, y_trigger + BOX_H / 2)

    # Trigger → Filter (cross-lane)
    cross_lane_arrow(ax, HUMAN_CX, y_trigger - BOX_H / 2, SYS_CX, y_filter + BOX_H / 2)

    # Filter → LLM
    arrow(ax, SYS_CX, y_filter - BOX_H / 2, SYS_CX, y_llm + BOX_H / 2)

    # LLM → Similarity evaluation
    arrow(ax, SYS_CX, y_llm - BOX_H / 2, SYS_CX, y_sim + BOX_H / 2)

    # Similarity → Decision
    arrow(ax, SYS_CX, y_sim - BOX_H / 2, SYS_CX, y_dec + DIAM_S)

    # Decision → Review: YES goes LEFT (horizontal) to Human lane
    ax.annotate("", xy=(HUMAN_CX + BOX_W / 2, y_review),
                xytext=(SYS_CX - DIAM_S, y_dec),
                arrowprops=dict(arrowstyle="-|>", color=ARROW_COLOR,
                                lw=1.2, mutation_scale=12,
                                connectionstyle="arc3,rad=0.0"), zorder=2)
    ax.text((SYS_CX - DIAM_S + HUMAN_CX + BOX_W / 2) / 2,
            y_dec + 0.15, "Yes", fontsize=FONT_SIZE - 1,
            ha="center", va="bottom", color="#555555", fontfamily="sans-serif")

    # Review → Export
    arrow(ax, HUMAN_CX, y_review - BOX_H / 2, HUMAN_CX, y_export + BOX_H / 2)

    # Decision → Correction: NO goes DOWN in System lane then crosses left
    arrow(ax, SYS_CX, y_dec - DIAM_S, SYS_CX, y_correct,
          label="No", label_side="right")
    ax.annotate("", xy=(HUMAN_CX + BOX_W / 2, y_correct),
                xytext=(SYS_CX, y_correct),
                arrowprops=dict(arrowstyle="-|>", color=ARROW_COLOR,
                                lw=1.2, mutation_scale=12), zorder=2)

    # Review output → loop back up to Configure prompt (left side of Human lane)
    lx_loop = LEFT_X + 0.12
    ax.plot(
        [HUMAN_CX - BOX_W / 2, lx_loop, lx_loop, HUMAN_CX - BOX_W / 2 - 0.02],
        [y_correct, y_correct, y_prompt, y_prompt],
        color=ARROW_COLOR, lw=1.0, zorder=2,
    )
    ax.annotate("", xy=(HUMAN_CX - BOX_W / 2, y_prompt),
                xytext=(HUMAN_CX - BOX_W / 2 - 0.02, y_prompt),
                arrowprops=dict(arrowstyle="-|>", color=ARROW_COLOR,
                                lw=1.0, mutation_scale=11), zorder=2)

    # Export → End
    arrow(ax, HUMAN_CX, y_export - BOX_H / 2, cx_mid, y_end + 0.22)

    # ── Title ─────────────────────────────────────────────────────────────
    ax.text(FIG_W / 2, FIG_H - 0.22,
            "Activity Diagram — Human-In-The-Loop TNA System",
            ha="center", va="center",
            fontsize=11, fontweight="bold",
            fontfamily="sans-serif", color="#111111")

    plt.tight_layout(pad=0)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Diagram sparad till {OUTPUT_PATH}")


if __name__ == "__main__":
    draw()
