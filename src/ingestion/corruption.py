from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from core.utils import write_csv, write_json
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import load_raw_records


_RANDOM_STATE = 42
_STALE_DATE = "2000-01-01"
_NOISE = " zxqv n0ise ### irrelevant-token "


def _sample_indices(index: pd.Index, fraction: float, random_state: int) -> list:
    """Return a reproducible non-empty sample when records are available."""
    if index.empty:
        return []
    count = max(1, round(len(index) * fraction))
    return list(pd.Series(index, index=index).sample(n=count, random_state=random_state).tolist())


def _rebuild_embedding_text(df: pd.DataFrame) -> None:
    """Keep derived columns consistent after the source fields are corrupted."""
    summary = df["summary"].fillna("").astype(str)
    authors = df.get("authors_joined", pd.Series("Unknown Author", index=df.index)).fillna("Unknown Author").astype(str)
    df["summary_chars"] = summary.str.len()
    df["text_for_embedding"] = (
        "Title: "
        + df["title"].fillna("").astype(str)
        + " | Authors: "
        + authors
        + " | Summary: "
        + summary
    )


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: Path | str) -> pd.DataFrame:
    """Return a reproducibly corrupted copy of a cleaned papers DataFrame.

    The scenarios intentionally violate the quality and freshness assumptions used by
    the observability checks. ``df`` is never mutated, so it remains usable as the
    baseline dataset for the repair/comparison flow.
    """
    required_columns = {"paper_id", "title", "summary", "published"}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        raise ValueError(f"Cannot corrupt cleaned data; missing columns: {sorted(missing_columns)}")

    corrupted = df.copy(deep=True).reset_index(drop=True)
    original_count = len(corrupted)
    log: dict[str, object] = {
        "original_record_count": original_count,
        "scenarios": {},
    }

    # 1. Remove 25% of the newest papers to simulate loss of recently ingested data.
    drop_count = round(original_count * 0.25)
    if drop_count:
        newest = pd.to_datetime(corrupted["published"], errors="coerce")
        drop_indices = list(newest.sort_values(ascending=False, na_position="last").index[:drop_count])
        dropped_ids = corrupted.loc[drop_indices, "paper_id"].astype(str).tolist()
        corrupted = corrupted.drop(index=drop_indices).reset_index(drop=True)
    else:
        dropped_ids = []
    log["scenarios"]["drop_latest_records"] = {
        "fraction": 0.25,
        "affected_count": len(dropped_ids),
        "paper_ids": dropped_ids,
    }

    # 2. Blank summaries. The sample is fixed to make metrics comparable across runs.
    blank_indices = _sample_indices(corrupted.index, 0.15, _RANDOM_STATE)
    corrupted.loc[blank_indices, "summary"] = ""
    log["scenarios"]["blank_summary"] = {
        "fraction": 0.15,
        "affected_count": len(blank_indices),
        "paper_ids": corrupted.loc[blank_indices, "paper_id"].astype(str).tolist(),
    }

    # 3. Add visibly meaningless tokens to otherwise non-blank summaries.
    noise_candidates = corrupted.index.difference(blank_indices)
    noise_indices = _sample_indices(noise_candidates, 0.15, _RANDOM_STATE + 1)
    corrupted.loc[noise_indices, "summary"] = (
        corrupted.loc[noise_indices, "summary"].fillna("").astype(str) + _NOISE
    ).str.strip()
    log["scenarios"]["text_noise_injection"] = {
        "fraction": 0.15,
        "affected_count": len(noise_indices),
        "paper_ids": corrupted.loc[noise_indices, "paper_id"].astype(str).tolist(),
    }

    # 4. Truncate titles to eight characters (within the requested 5--10 range).
    title_indices = _sample_indices(corrupted.index, 0.15, _RANDOM_STATE + 2)
    corrupted.loc[title_indices, "title"] = corrupted.loc[title_indices, "title"].fillna("").astype(str).str.slice(0, 8)
    log["scenarios"]["title_truncation"] = {
        "target_length": 8,
        "affected_count": len(title_indices),
        "paper_ids": corrupted.loc[title_indices, "paper_id"].astype(str).tolist(),
    }

    # 5. Make a subset stale and update age_days so freshness monitors detect it.
    stale_indices = _sample_indices(corrupted.index, 0.15, _RANDOM_STATE + 3)
    corrupted.loc[stale_indices, "published"] = _STALE_DATE
    today = pd.Timestamp.now().normalize()
    published = pd.to_datetime(corrupted["published"], errors="coerce")
    corrupted["age_days"] = (today - published).dt.days.clip(lower=0).fillna(0).astype(int)
    log["scenarios"]["stale_published_date"] = {
        "replacement_date": _STALE_DATE,
        "affected_count": len(stale_indices),
        "paper_ids": corrupted.loc[stale_indices, "paper_id"].astype(str).tolist(),
    }

    _rebuild_embedding_text(corrupted)

    # 6. Duplicate 10% of rows after other corruption is applied.
    duplicate_indices = _sample_indices(corrupted.index, 0.10, _RANDOM_STATE + 4)
    duplicates = corrupted.loc[duplicate_indices].copy()
    corrupted = pd.concat([corrupted, duplicates], ignore_index=True)
    log["scenarios"]["add_duplicate_rows"] = {
        "fraction": 0.10,
        "affected_count": len(duplicates),
        "paper_ids": duplicates["paper_id"].astype(str).tolist(),
    }
    log["final_record_count"] = len(corrupted)
    log["duplicate_paper_id_count"] = int(corrupted["paper_id"].duplicated().sum())

    write_json(Path(output_log_path), log)
    return corrupted


def repair_from_raw_records(
    raw_records_path: Path | str,
    run_date: datetime,
    output_csv_path: Path | str,
    output_json_path: Path | str,
) -> pd.DataFrame:
    """Rebuild and persist the clean dataset from the immutable raw snapshot.

    Repair is deliberately a full re-clean rather than a best-effort edit of the
    corrupted data: this restores dropped records as well as every modified field.
    """
    records = load_raw_records(Path(raw_records_path))
    repaired = build_clean_dataframe(records, run_date)
    write_csv(repaired, Path(output_csv_path))
    write_json(Path(output_json_path), repaired.to_dict(orient="records"))
    return repaired
