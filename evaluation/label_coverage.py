"""
Label coverage report — compares sections across GT, chunks, and STS results.

Derives the analyzed section automatically from output/latest_analysis.json
(longest common breadcrumb prefix of all traceability paths), then prints
a 4-column table scoped to that section:

  COL 1  GT section_or_chapter  (from groundtruth_sts.json, filtered to scope)
  COL 2  Chunk section_or_chapter  (from chunks.json, filtered to scope)
  COL 3  analysis_section  (from sts_results.json)
  COL 4  gt_section  (from sts_results.json)

Also saves a PNG plot to output/label_coverage.png.

Usage:
    python -m evaluation.label_coverage
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

ANALYSIS_PATH = Path("output/latest_analysis.json")
GROUNDTRUTH_PATH = Path("goldlabels/groundtruth_sts.json")
STS_RESULTS_PATH = Path("output/sts_results.json")
CHUNKS_DIR = Path("chunks")

COL_WIDTH = 48


def _derive_selected_section(analysis: dict) -> str:
    """
    Returns the deepest common breadcrumb prefix across all traceability
    section_or_chapter values in the analysis output.
    """
    paths = []
    for task in analysis.get("tasks", []):
        for sub in task.get("subtasks", []):
            soc = sub.get("traceability", {}).get("section_or_chapter", "")
            if soc:
                paths.append([s.strip() for s in soc.split("›")])

    if not paths:
        return ""

    common = paths[0]
    for parts in paths[1:]:
        new = []
        for a, b in zip(common, parts):
            if a == b:
                new.append(a)
            else:
                break
        common = new

    return " › ".join(common)


def _derive_doc_title(analysis: dict) -> str:
    for task in analysis.get("tasks", []):
        for sub in task.get("subtasks", []):
            title = sub.get("traceability", {}).get("document_title", "")
            if title:
                return title
    return ""


def _filter_gt_subtasks(groundtruth: dict, leaf: str) -> list[dict]:
    """GT subtasks whose section_or_chapter contains the leaf segment."""
    results = []
    leaf_lower = leaf.lower()
    for task in groundtruth.get("tasks", []):
        for sub in task.get("subtasks", []):
            soc = sub.get("section_or_chapter", "")
            segments = [s.strip().lower() for s in soc.split(">")]
            if any(leaf_lower in seg for seg in segments):
                results.append({
                    "subtask_name": sub.get("subtask_name", ""),
                    "section_or_chapter": soc,
                })
    return results


def _filter_chunks(doc_title: str, leaf: str) -> list[str]:
    """Unique section_or_chapter values from chunks.json matching the leaf."""
    chunks_file = CHUNKS_DIR / doc_title / "chunks.json"
    if not chunks_file.exists():
        return []

    with open(chunks_file, encoding="utf-8") as f:
        data = json.load(f)

    leaf_clean = leaf.strip()
    seen: set = set()
    sections = []
    for chunk in data.get("chunks", []):
        soc = chunk.get("section_or_chapter", "")
        breadcrumb = chunk.get("breadcrumb", [])
        breadcrumb_match = any(item.strip() == leaf_clean for item in breadcrumb)
        soc_match = leaf_clean in soc
        if (breadcrumb_match or soc_match) and soc not in seen:
            seen.add(soc)
            sections.append(soc)

    return sections


def _cell(text: str) -> str:
    text = str(text)
    if len(text) > COL_WIDTH:
        text = text[: COL_WIDTH - 1] + "…"
    return text.ljust(COL_WIDTH)


def _separator() -> str:
    return "-+-".join(["-" * COL_WIDTH] * 4)


def report():
    for path in (ANALYSIS_PATH, GROUNDTRUTH_PATH, STS_RESULTS_PATH):
        if not path.exists():
            print(f"Fil saknas: {path}")
            return

    with open(ANALYSIS_PATH, encoding="utf-8") as f:
        analysis = json.load(f)
    with open(GROUNDTRUTH_PATH, encoding="utf-8") as f:
        groundtruth = json.load(f)
    with open(STS_RESULTS_PATH, encoding="utf-8") as f:
        sts = json.load(f)

    selected_section = _derive_selected_section(analysis)
    doc_title = _derive_doc_title(analysis)
    leaf = selected_section.split("›")[-1].strip() if selected_section else ""

    print()
    print(f"  Analyserat avsnitt : {selected_section or '(okänt)'}")
    print(f"  Dokument           : {doc_title or '(okänt)'}")
    print(f"  Matchningssegment  : {leaf or '(okänt)'}")
    print()

    gt_items = _filter_gt_subtasks(groundtruth, leaf)
    chunk_sections = _filter_chunks(doc_title, leaf)
    sts_results = sts.get("results", [])

    n_rows = max(len(gt_items), len(chunk_sections), len(sts_results))

    header = (
        _cell("GT section_or_chapter")
        + " | "
        + _cell("Chunk section_or_chapter")
        + " | "
        + _cell("analysis_section")
        + " | "
        + _cell("gt_section")
    )
    print(header)
    print(_separator())

    for i in range(n_rows):
        # Column 1 — GT subtask name + section
        if i < len(gt_items):
            gt = gt_items[i]
            col1_text = f"[{gt['subtask_name']}] {gt['section_or_chapter']}"
        else:
            col1_text = ""

        # Column 2 — chunk section_or_chapter
        col2_text = chunk_sections[i] if i < len(chunk_sections) else ""

        # Column 3 — analysis_section
        col3_text = sts_results[i].get("analysis_section", "") if i < len(sts_results) else ""

        # Column 4 — gt_section (best match or no match)
        if i < len(sts_results):
            matches = sts_results[i].get("matches", [])
            if matches:
                best = matches[0]
                col4_text = f"{best['gt_section']} ({best['similarity_score']})"
            else:
                col4_text = "(no match)"
        else:
            col4_text = ""

        print(
            _cell(col1_text)
            + " | "
            + _cell(col2_text)
            + " | "
            + _cell(col3_text)
            + " | "
            + _cell(col4_text)
        )

    print(_separator())
    print(f"  GT-sektioner i scope   : {len(gt_items)}")
    print(f"  Chunk-sektioner i scope: {len(chunk_sections)}")
    print(f"  STS-resultat           : {len(sts_results)}")
    skipped = sts.get("skipped_gt_subtasks", [])
    if skipped:
        print(f"  Hoppade GT-subtasks    : {len(skipped)} ({', '.join(skipped[:3])}{'...' if len(skipped) > 3 else ''})")
    print()


def _wrap(text: str, width: int = 32) -> str:
    """Wrap text to fit in a table cell."""
    return "\n".join(textwrap.wrap(str(text), width=width)) if text else ""


def plot(
    selected_section: str,
    gt_items: list,
    chunk_sections: list,
    sts_results: list,
    output_path: Path,
):
    col_headers = [
        "Ground Truth — Expected Section",
        "Source Chunk — Sent to LLM",
        "LLM Output — Referenced Section",
        "Most Similar Ground Truth Section",
    ]

    n_rows = max(len(gt_items), len(chunk_sections), len(sts_results), 1)

    cell_data: list[list[str]] = []
    row_has_match: list[bool] = []  # True = matched, False = no match, None = empty

    for i in range(n_rows):
        # Col 1
        if i < len(gt_items):
            gt = gt_items[i]
            c1 = f"[{gt['subtask_name']}]\n{gt['section_or_chapter']}"
        else:
            c1 = ""

        # Col 2
        c2 = chunk_sections[i] if i < len(chunk_sections) else ""

        # Col 3
        c3 = sts_results[i].get("analysis_section", "") if i < len(sts_results) else ""

        # Col 4
        if i < len(sts_results):
            matches = sts_results[i].get("matches", [])
            if matches:
                best = matches[0]
                c4 = f"{best['gt_section']}\n(score: {best['similarity_score']})"
                row_has_match.append(True)
            else:
                c4 = "(no match)"
                row_has_match.append(False)
        else:
            c4 = ""
            row_has_match.append(None)

        cell_data.append([
            _wrap(c1, 30),
            _wrap(c2, 30),
            _wrap(c3, 30),
            _wrap(c4, 30),
        ])

    # Estimate row heights based on wrapped line counts
    row_heights = []
    for row in cell_data:
        max_lines = max(len(cell.split("\n")) for cell in row) if any(row) else 1
        row_heights.append(max(max_lines * 0.22, 0.5))

    col_widths = [0.28, 0.22, 0.22, 0.28]
    fig_width = 20
    fig_height = sum(row_heights) + 1.6

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis("off")

    # Header background
    header_colors = ["#2c3e50"] * 4
    row_colors = []
    for i, has_match in enumerate(row_has_match):
        if has_match is True:
            row_colors.append(["#eafaf1", "#eaf4fb", "#eaf4fb", "#eafaf1"])
        elif has_match is False:
            row_colors.append(["#fef9e7", "#eaf4fb", "#eaf4fb", "#fdecea"])
        else:
            row_colors.append(["#f8f9fa"] * 4)

    table = ax.table(
        cellText=cell_data,
        colLabels=col_headers,
        colWidths=col_widths,
        loc="center",
        cellLoc="left",
    )

    table.auto_set_font_size(False)
    table.set_fontsize(8.5)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#cccccc")
        cell.set_linewidth(0.5)
        cell.PAD = 0.04

        if row == 0:
            cell.set_facecolor(header_colors[col])
            cell.set_text_props(color="white", fontweight="bold", fontsize=9)
            cell.set_height(0.06)
        else:
            data_row = row - 1
            cell.set_facecolor(row_colors[data_row][col])
            cell.set_height(row_heights[data_row] / fig_height)
            # Grey out empty cells
            if cell.get_text().get_text() == "":
                cell.set_facecolor("#f0f0f0")

    # Title and legend
    fig.suptitle(
        f"Label Coverage — {selected_section}",
        fontsize=12,
        fontweight="bold",
        y=0.98,
        color="#2c3e50",
    )

    match_patch = mpatches.Patch(color="#eafaf1", label="Match hittad")
    no_match_patch = mpatches.Patch(color="#fdecea", label="Ingen match")
    fig.legend(
        handles=[match_patch, no_match_patch],
        loc="lower right",
        fontsize=8,
        framealpha=0.8,
    )

    plt.tight_layout(rect=[0, 0.02, 1, 0.96])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Plot sparad till {output_path}")


def report():
    for path in (ANALYSIS_PATH, GROUNDTRUTH_PATH, STS_RESULTS_PATH):
        if not path.exists():
            print(f"Fil saknas: {path}")
            return

    with open(ANALYSIS_PATH, encoding="utf-8") as f:
        analysis = json.load(f)
    with open(GROUNDTRUTH_PATH, encoding="utf-8") as f:
        groundtruth = json.load(f)
    with open(STS_RESULTS_PATH, encoding="utf-8") as f:
        sts = json.load(f)

    selected_section = _derive_selected_section(analysis)
    doc_title = _derive_doc_title(analysis)
    leaf = selected_section.split("›")[-1].strip() if selected_section else ""

    print()
    print(f"  Analyserat avsnitt : {selected_section or '(okänt)'}")
    print(f"  Dokument           : {doc_title or '(okänt)'}")
    print(f"  Matchningssegment  : {leaf or '(okänt)'}")
    print()

    gt_items = _filter_gt_subtasks(groundtruth, leaf)
    chunk_sections = _filter_chunks(doc_title, leaf)
    sts_results = sts.get("results", [])

    # ── terminal table ──────────────────────────────────────────────────────
    n_rows = max(len(gt_items), len(chunk_sections), len(sts_results))

    header = (
        _cell("GT section_or_chapter")
        + " | "
        + _cell("Chunk section_or_chapter")
        + " | "
        + _cell("analysis_section")
        + " | "
        + _cell("gt_section")
    )
    print(header)
    print(_separator())

    for i in range(n_rows):
        if i < len(gt_items):
            gt = gt_items[i]
            col1_text = f"[{gt['subtask_name']}] {gt['section_or_chapter']}"
        else:
            col1_text = ""

        col2_text = chunk_sections[i] if i < len(chunk_sections) else ""
        col3_text = sts_results[i].get("analysis_section", "") if i < len(sts_results) else ""

        if i < len(sts_results):
            matches = sts_results[i].get("matches", [])
            if matches:
                best = matches[0]
                col4_text = f"{best['gt_section']} ({best['similarity_score']})"
            else:
                col4_text = "(no match)"
        else:
            col4_text = ""

        print(
            _cell(col1_text)
            + " | "
            + _cell(col2_text)
            + " | "
            + _cell(col3_text)
            + " | "
            + _cell(col4_text)
        )

    print(_separator())
    print(f"  GT-sektioner i scope   : {len(gt_items)}")
    print(f"  Chunk-sektioner i scope: {len(chunk_sections)}")
    print(f"  STS-resultat           : {len(sts_results)}")
    skipped = sts.get("skipped_gt_subtasks", [])
    if skipped:
        print(f"  Hoppade GT-subtasks    : {len(skipped)} ({', '.join(skipped[:3])}{'...' if len(skipped) > 3 else ''})")
    print()

    # ── plot ────────────────────────────────────────────────────────────────
    plot(
        selected_section=selected_section or "(okänt avsnitt)",
        gt_items=gt_items,
        chunk_sections=chunk_sections,
        sts_results=sts_results,
        output_path=Path("output/label_coverage.png"),
    )


if __name__ == "__main__":
    report()
