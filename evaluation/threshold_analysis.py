"""
Threshold analysis — calibrates a cosine similarity threshold using all
pairwise comparisons within the ground truth dataset.

Methodology:
  1. Encode all GT subtasks (subtask_name + steps) with the sentence-transformer.
  2. Compute cosine similarity for every unique pair (n*(n-1)/2 pairs).
  3. Label each pair: positive (1) = same section leaf, negative (0) = different.
  4. Sweep thresholds 0→1 and compute F1 at each point.
  5. Report max-F1 threshold + save a two-panel PNG.

Usage:
    python -m evaluation.threshold_analysis
"""
from __future__ import annotations

import json
import itertools
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sentence_transformers import SentenceTransformer

from evaluation.sts_evaluator import subtask_to_text, cosine_similarity

GROUNDTRUTH_PATH = Path("goldlabels/groundtruth_sts.json")
OUTPUT_PNG = Path("output/threshold_analysis.png")
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"


def _leaf(section_or_chapter: str) -> str:
    """Return the deepest segment of a '>' separated path."""
    return section_or_chapter.split(">")[-1].strip()


def load_gt_subtasks(path: Path) -> list[dict]:
    """Load GT subtasks that have a section_or_chapter."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    subtasks = []
    for task in data.get("tasks", []):
        for sub in task.get("subtasks", []):
            soc = sub.get("section_or_chapter", "").strip()
            if not soc:
                continue
            subtasks.append({
                "name": sub.get("subtask_name", ""),
                "steps": sub.get("steps", []),
                "section": soc,
                "leaf": _leaf(soc),
            })
    return subtasks


def compute_pairs(subtasks: list[dict], embeddings: np.ndarray) -> tuple[list, list]:
    """Return (scores, labels) for all unique pairs."""
    scores, labels = [], []
    for i, j in itertools.combinations(range(len(subtasks)), 2):
        score = cosine_similarity(embeddings[i], embeddings[j])
        label = 1 if subtasks[i]["leaf"] == subtasks[j]["leaf"] else 0
        scores.append(score)
        labels.append(label)
    return scores, labels


def find_best_threshold(
    scores: list[float], labels: list[int]
) -> tuple[float, float, float, float]:
    """Sweep thresholds and return (best_t, precision, recall, f1)."""
    scores_arr = np.array(scores)
    labels_arr = np.array(labels)
    thresholds = np.arange(0.0, 1.01, 0.01)

    best_t, best_f1, best_p, best_r = 0.0, 0.0, 0.0, 0.0
    for t in thresholds:
        preds = (scores_arr >= t).astype(int)
        tp = int(((preds == 1) & (labels_arr == 1)).sum())
        fp = int(((preds == 1) & (labels_arr == 0)).sum())
        fn = int(((preds == 0) & (labels_arr == 1)).sum())
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        if f1 > best_f1:
            best_f1, best_t, best_p, best_r = f1, float(t), precision, recall

    return best_t, best_p, best_r, best_f1


def plot(
    scores: list[float],
    labels: list[int],
    best_t: float,
    best_p: float,
    best_r: float,
    best_f1: float,
    n_pos: int,
    n_total: int,
    output_path: Path,
):
    scores_arr = np.array(scores)
    labels_arr = np.array(labels)
    pos_scores = scores_arr[labels_arr == 1]
    neg_scores = scores_arr[labels_arr == 0]

    thresholds = np.arange(0.0, 1.01, 0.01)
    f1_vals, prec_vals, rec_vals = [], [], []
    for t in thresholds:
        preds = (scores_arr >= t).astype(int)
        tp = int(((preds == 1) & (labels_arr == 1)).sum())
        fp = int(((preds == 1) & (labels_arr == 0)).sum())
        fn = int(((preds == 0) & (labels_arr == 1)).sum())
        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        f1_vals.append(f)
        prec_vals.append(p)
        rec_vals.append(r)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 9))
    fig.suptitle(
        "Semantic Similarity Threshold Calibration\n"
        f"Ground truth: {n_total} pairs  ({n_pos} positive / {n_total - n_pos} negative)",
        fontsize=12,
        fontweight="bold",
        color="#2c3e50",
    )

    # ── Panel 1: Score distributions ───────────────────────────────────────
    bins = np.linspace(0, 1, 41)
    ax1.hist(neg_scores, bins=bins, alpha=0.55, color="#e74c3c", label="Negative pairs (different section)")
    ax1.hist(pos_scores, bins=bins, alpha=0.7, color="#27ae60", label="Positive pairs (same section)")
    ax1.axvline(best_t, color="#2c3e50", linewidth=1.8, linestyle="--",
                label=f"Recommended threshold: {best_t:.2f}")
    ax1.set_xlabel("Cosine Similarity", fontsize=10)
    ax1.set_ylabel("Number of pairs", fontsize=10)
    ax1.set_title("Score Distribution: Positive vs Negative Pairs", fontsize=10)
    ax1.legend(fontsize=9)
    ax1.set_xlim(0, 1)
    ax1.grid(axis="y", alpha=0.3)

    # ── Panel 2: F1 / Precision / Recall curves ────────────────────────────
    ax2.plot(thresholds, f1_vals, color="#2c3e50", linewidth=2, label="F1")
    ax2.plot(thresholds, prec_vals, color="#2980b9", linewidth=1.4, linestyle="--", label="Precision")
    ax2.plot(thresholds, rec_vals, color="#e67e22", linewidth=1.4, linestyle="--", label="Recall")
    ax2.axvline(best_t, color="#2c3e50", linewidth=1.8, linestyle="--",
                label=f"Max F1 = {best_f1:.3f} @ {best_t:.2f}")
    ax2.scatter([best_t], [best_f1], color="#2c3e50", zorder=5, s=60)
    ax2.annotate(
        f"  P={best_p:.2f}  R={best_r:.2f}  F1={best_f1:.2f}",
        xy=(best_t, best_f1),
        fontsize=8.5,
        color="#2c3e50",
    )
    ax2.set_xlabel("Threshold", fontsize=10)
    ax2.set_ylabel("Score", fontsize=10)
    ax2.set_title("F1 / Precision / Recall vs Threshold", fontsize=10)
    ax2.legend(fontsize=9)
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1.05)
    ax2.grid(alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Plot sparad till {output_path}")


def analyse():
    if not GROUNDTRUTH_PATH.exists():
        print(f"Fil saknas: {GROUNDTRUTH_PATH}")
        return

    print(f"Laddar modell: {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)

    subtasks = load_gt_subtasks(GROUNDTRUTH_PATH)
    print(f"GT-subtasks med section: {len(subtasks)}")

    texts = [subtask_to_text(s["name"], s["steps"]) for s in subtasks]
    print("Kodar texter ...")
    embeddings = model.encode(texts, show_progress_bar=True)

    print("Beräknar par-similarities ...")
    scores, labels = compute_pairs(subtasks, embeddings)

    n_pos = sum(labels)
    n_total = len(labels)
    print(f"Totalt par: {n_total}  |  Positiva: {n_pos}  |  Negativa: {n_total - n_pos}")

    best_t, best_p, best_r, best_f1 = find_best_threshold(scores, labels)

    print()
    print("=" * 50)
    print(f"  Rekommenderad tröskel (max F1) : {best_t:.2f}")
    print(f"  Precision @ tröskel            : {best_p:.3f}")
    print(f"  Recall    @ tröskel            : {best_r:.3f}")
    print(f"  F1        @ tröskel            : {best_f1:.3f}")
    print("=" * 50)
    print()
    print("  Obs: Tröskeln är kalibrerad mot paraphrase-multilingual-mpnet-base-v2")
    print("  och svensk militärtext. Byt modell → kalibrera om.")
    print()

    plot(scores, labels, best_t, best_p, best_r, best_f1, n_pos, n_total, OUTPUT_PNG)


if __name__ == "__main__":
    analyse()
