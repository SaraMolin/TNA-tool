"""
Semantic similarity evaluation: compares LLM-extracted subtasks against ground truth.

Usage:
    python -m evaluation.sts_evaluator
"""
from __future__ import annotations

import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

ANALYSIS_PATH = Path("output/latest_analysis.json")
GROUNDTRUTH_PATH = Path("goldlabels/groundtruth_sts.json")
OUTPUT_PATH = Path("output/sts_results.json")
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"


def subtask_to_text(name: str, steps: list) -> str:
    return name + ". " + " ".join(s.strip(".") + "." for s in steps)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def find_matches(ref_section: str, gt_subtasks: list) -> list:
    """Return list of (gt_subtask_dict, match_depth) for every GT subtask whose
    section_or_chapter path contains ref_section as a segment (case-insensitive).

    ref_section may itself be a hierarchical path using '›' as separator
    (as produced by the analysis pipeline). We extract the deepest segment
    and match it against segments in the GT path (split on '>').
    """
    # Extract the most specific (deepest) segment from the analysis path
    ref_segments = [s.strip() for s in ref_section.split("›")]
    ref = ref_segments[-1].lower()

    matches = []
    for subtask in gt_subtasks:
        gt_path = subtask.get("section_or_chapter", "")
        segments = [s.strip() for s in gt_path.split(">")]
        for depth, segment in enumerate(segments):
            if segment.lower() == ref:
                matches.append((subtask, depth))
                break
    return matches


def collect_gt_subtasks(groundtruth: dict) -> tuple[list, list]:
    """Return (subtasks_with_section, subtasks_without_section)."""
    with_section = []
    without_section = []
    for task in groundtruth.get("tasks", []):
        for subtask in task.get("subtasks", []):
            if subtask.get("section_or_chapter"):
                with_section.append(subtask)
            else:
                without_section.append(subtask)
    return with_section, without_section


def evaluate():
    print(f"Laddar modell: {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)

    with open(ANALYSIS_PATH, encoding="utf-8") as f:
        analysis = json.load(f)
    with open(GROUNDTRUTH_PATH, encoding="utf-8") as f:
        groundtruth = json.load(f)

    gt_subtasks_with_section, gt_subtasks_skipped = collect_gt_subtasks(groundtruth)

    skipped_names = [s["subtask_name"] for s in gt_subtasks_skipped]
    if skipped_names:
        print(f"\nHoppade GT-subtasks (saknar section_or_chapter): {len(skipped_names)}")
        for name in skipped_names:
            print(f"  – {name}")

    results = []
    unmatched_count = 0

    for task in analysis.get("tasks", []):
        for subtask in task.get("subtasks", []):
            subtask_name = subtask.get("subtask", "")
            steps_raw = subtask.get("steps", [])
            steps = [s["step"] for s in steps_raw if isinstance(s, dict)]
            analysis_text = subtask_to_text(subtask_name, steps)
            ref_section = subtask.get("traceability", {}).get("section_or_chapter", "")

            raw_matches = find_matches(ref_section, gt_subtasks_with_section)

            match_entries = []
            if raw_matches:
                texts_to_encode = [analysis_text] + [
                    subtask_to_text(
                        gt["subtask_name"],
                        gt.get("steps", [])
                    )
                    for gt, _ in raw_matches
                ]
                embeddings = model.encode(texts_to_encode, show_progress_bar=False)
                emb_analysis = embeddings[0]
                all_scored = []
                for i, (gt, depth) in enumerate(raw_matches):
                    gt_text = texts_to_encode[i + 1]
                    score = cosine_similarity(emb_analysis, embeddings[i + 1])
                    all_scored.append({
                        "gt_subtask_name": gt["subtask_name"],
                        "gt_section": gt["section_or_chapter"],
                        "match_depth": depth,
                        "gt_text": gt_text,
                        "similarity_score": round(score, 4),
                    })
                best = max(all_scored, key=lambda x: x["similarity_score"])
                match_entries = [best]
            else:
                unmatched_count += 1

            results.append({
                "analysis_subtask": subtask_name,
                "analysis_section": ref_section,
                "analysis_text": analysis_text,
                "matches": match_entries,
            })

    output = {
        "results": results,
        "skipped_gt_subtasks": skipped_names,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    _print_summary(results, skipped_names, unmatched_count)
    print(f"\nResultat sparat till {OUTPUT_PATH}")


def _print_summary(results: list, skipped: list, unmatched_count: int):
    print("\n" + "=" * 80)
    print(f"{'SUBTASK':<45} {'BEST MATCH GT-SUBTASK':<35} SCORE")
    print("=" * 80)
    for r in results:
        name = r["analysis_subtask"][:44]
        if r["matches"]:
            best = r["matches"][0]
            gt_name = best["gt_subtask_name"][:34]
            score = best["similarity_score"]
        else:
            gt_name = "–"
            score = "–"
        print(f"{name:<45} {gt_name:<35} {score}")
    print("=" * 80)
    print(f"Totalt: {len(results)} analysis-subtasks | {unmatched_count} utan match | "
          f"{len(skipped)} GT-subtasks hoppade")


if __name__ == "__main__":
    evaluate()
