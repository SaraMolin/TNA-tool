"""
Calculate summary metrics from manually filled evaluation results.

Reads output/evaluation_results.csv and computes aggregated metrics
for the Results table in the thesis.

Usage:
    python -m evaluation.calculate_summary
"""
from __future__ import annotations

import csv
import statistics
from pathlib import Path

THRESHOLD = 0.78
INPUT_FILE = Path("output/evaluation_results.csv")

SCORE_COLUMNS = [
    "sts_score_1", "sts_score_2", "sts_score_3", "sts_score_4",
    "sts_score_5", "sts_score_6", "sts_score_7", "sts_score_8",
]


def load_rows(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        sample = f.read(1024)
        f.seek(0)
        delimiter = ";" if ";" in sample.split("\n")[0] else ","
        return list(csv.DictReader(f, delimiter=delimiter))


def summarise(rows: list[dict]) -> None:
    all_scores: list[float] = []
    unmatched_count = 0
    sections_run = 0
    per_section: list[dict] = []

    for row in rows:
        section_scores: list[float] = []
        row_unmatched = 0
        for col in SCORE_COLUMNS:
            val = row[col].strip()
            if val == "":
                continue
            if val.lower() == "none" or val == "0":
                row_unmatched += 1
                unmatched_count += 1
            else:
                try:
                    score = float(val)
                    section_scores.append(score)
                    all_scores.append(score)
                except ValueError:
                    pass

        if section_scores or row_unmatched > 0:
            sections_run += 1

        mean_score = round(statistics.mean(section_scores), 3) if section_scores else None
        pct_above = (
            round(sum(1 for s in section_scores if s >= THRESHOLD) / len(section_scores) * 100, 1)
            if section_scores else None
        )

        per_section.append({
            "section": row["sektion"],
            "generated": row["genererade_subtasks"],
            "n_scores": len(section_scores),
            "mean_sts": mean_score,
            "pct_above": pct_above,
        })

    total_subtasks = len(all_scores) + unmatched_count
    mean_sts_total = round(statistics.mean(all_scores), 3) if all_scores else None
    above_threshold = sum(1 for s in all_scores if s >= THRESHOLD)
    pct_total = round(above_threshold / len(all_scores) * 100, 1) if all_scores else None

    print("\n========== RESULTS PER SECTION ==========")
    print(f"{'Section':<45} {'Scores':>7} {'Mean STS':>10} {f'>= {THRESHOLD}':>8}")
    print("-" * 75)
    for s in per_section:
        mean_str = f"{s['mean_sts']:.3f}" if s["mean_sts"] is not None else "—"
        pct_str  = f"{s['pct_above']}%"   if s["pct_above"] is not None else "—"
        print(f"{s['section']:<45} {s['n_scores']:>7} {mean_str:>10} {pct_str:>8}")

    print("\n========== AGGREGATED SUMMARY (for Results table) ==========")
    print(f"  Sections analysed:                  {sections_run}")
    print(f"  Total generated subtasks:           {total_subtasks}")
    print(f"  Subtasks without GT match:          {unmatched_count}")
    print(f"  Mean STS score (all subtasks):      {mean_sts_total}")
    print(f"  Subtasks >= {THRESHOLD}:                 {pct_total}%")
    print()


def main() -> None:
    if not INPUT_FILE.exists():
        print(f"File not found: {INPUT_FILE}")
        return
    rows = load_rows(INPUT_FILE)
    summarise(rows)


if __name__ == "__main__":
    main()
