from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json



def build_test_set(df: pd.DataFrame, output_path: str | Path) -> list[dict[str, Any]]:
    """Build evaluation test set from cleaned DataFrame and write to JSON file."""
    if df.empty:
        items = []
        write_json(Path(output_path), items)
        return items

    # Select representative papers (limit up to 10 papers for evaluation)
    sample_df = df.head(10) if len(df) >= 10 else df
    items: list[dict[str, Any]] = []
    question_idx = 1

    for _, row in sample_df.iterrows():
        paper_id = str(row["paper_id"])
        title = str(row["title"])
        summary = str(row["summary"])
        authors = str(row.get("authors_joined", ""))
        categories = str(row.get("categories_joined", ""))
        published = str(row.get("published", ""))

        # 1. Summary Question
        if summary:
            gt_summary = first_sentence(summary) or summary[:200]
            items.append(
                {
                    "id": f"q_{question_idx:03d}",
                    "question_type": "summary",
                    "question": f"What is the main finding or summary of the paper titled '{title}'?",
                    "ground_truth": gt_summary,
                    "ground_truth_doc_ids": [paper_id],
                }
            )
            question_idx += 1

        # 2. Authors Question
        if authors:
            items.append(
                {
                    "id": f"q_{question_idx:03d}",
                    "question_type": "authors",
                    "question": f"Who authored the paper titled '{title}'?",
                    "ground_truth": authors,
                    "ground_truth_doc_ids": [paper_id],
                }
            )
            question_idx += 1

        # 3. Date Question
        if published:
            items.append(
                {
                    "id": f"q_{question_idx:03d}",
                    "question_type": "date",
                    "question": f"When was the paper '{title}' published?",
                    "ground_truth": published,
                    "ground_truth_doc_ids": [paper_id],
                }
            )
            question_idx += 1

        # 4. Categories Question
        if categories:
            items.append(
                {
                    "id": f"q_{question_idx:03d}",
                    "question_type": "categories",
                    "question": f"What categories does the paper titled '{title}' cover?",
                    "ground_truth": categories,
                    "ground_truth_doc_ids": [paper_id],
                }
            )
            question_idx += 1

    write_json(Path(output_path), items)
    return items

