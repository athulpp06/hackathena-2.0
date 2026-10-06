"""
test_evaluation_integrity.py - Enforces strict separation between training and evaluation data.
Fails if any holdout text or near-duplicate (token Jaccard >= 0.8) appears in training data or training seeds.
"""

import os
import re
import csv
import pathlib
import pytest

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "data"
TRAIN_SEEDS_DIR = DATA_DIR / "real_world" / "train_seeds"
HOLDOUT_DIR = DATA_DIR / "real_world" / "holdout"


def _tokenize(text: str) -> set[str]:
    """Tokenize and normalize text for lexical overlap analysis."""
    text_clean = re.sub(r"[^\w\s]", " ", text.lower())
    tokens = text_clean.split()
    return set(tokens)


def _jaccard(set_a: set[str], set_b: set[str]) -> float:
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def _load_texts(directory: pathlib.Path) -> list[tuple[str, str]]:
    texts = []
    for csv_file in directory.glob("*.csv"):
        with open(csv_file, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                text = row.get("text", "").strip()
                if text:
                    texts.append((csv_file.name, text))
    return texts


def test_no_exact_or_near_duplicate_overlap():
    """Verify 0% overlap or near-duplicate leakage between train_seeds and holdout."""
    assert TRAIN_SEEDS_DIR.exists(), f"Train seeds directory missing: {TRAIN_SEEDS_DIR}"
    assert HOLDOUT_DIR.exists(), f"Holdout directory missing: {HOLDOUT_DIR}"

    train_samples = _load_texts(TRAIN_SEEDS_DIR)
    holdout_samples = _load_texts(HOLDOUT_DIR)

    assert len(train_samples) >= 150, f"Expected >= 150 training seeds, found {len(train_samples)}"
    assert len(holdout_samples) >= 120, f"Expected >= 120 holdout samples, found {len(holdout_samples)}"

    train_tokens = [(fname, text, _tokenize(text)) for fname, text in train_samples]
    holdout_tokens = [(fname, text, _tokenize(text)) for fname, text in holdout_samples]

    violations = []

    for h_fname, h_text, h_tok in holdout_tokens:
        h_norm = " ".join(sorted(h_tok))
        for t_fname, t_text, t_tok in train_tokens:
            t_norm = " ".join(sorted(t_tok))
            # 1. Exact token match
            if h_norm == t_norm:
                violations.append(f"EXACT OVERLAP:\nHoldout ({h_fname}): {h_text}\nTrain ({t_fname}): {t_text}")
                continue

            # 2. Near duplicate Jaccard >= 0.8
            sim = _jaccard(h_tok, t_tok)
            if sim >= 0.80:
                violations.append(
                    f"NEAR DUPLICATE (Jaccard {sim:.2f} >= 0.80):\n"
                    f"Holdout ({h_fname}): {h_text}\n"
                    f"Train ({t_fname}): {t_text}"
                )

    assert not violations, f"Data contamination detected ({len(violations)} pairs):\n" + "\n\n".join(violations[:5])


def test_train_pipeline_does_not_load_holdout():
    """Verify static source code of train_pipeline.py never touches holdout directory."""
    train_script = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "train_pipeline.py"
    content = train_script.read_text(encoding="utf-8")

    assert "holdout" not in content.lower(), "train_pipeline.py must NEVER reference 'holdout' data!"
    assert "train_seeds" in content, "train_pipeline.py must use 'train_seeds' for training augmentation."
