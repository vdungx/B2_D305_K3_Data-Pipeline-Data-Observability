from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Runs data quality checks on the papers DataFrame.

    Saves the report to settings.paths.quality_dir / {report_name}.json.
    """
    row_count = len(df)
    row_count_passed = row_count > 0
    row_count_msg = f"Passed: Found {row_count} records." if row_count_passed else "Failed: DataFrame is empty."

    # Paper ID checks
    if 'paper_id' in df.columns:
        null_paper_ids = int(df['paper_id'].isnull().sum() + (df['paper_id'].astype(str).str.strip() == '').sum())
        paper_id_non_null_passed = null_paper_ids == 0
        paper_id_non_null_msg = f"Passed: 0 null/empty paper_ids." if paper_id_non_null_passed else f"Failed: Found {null_paper_ids} null or empty paper_ids."
        
        paper_id_unique_passed = bool(df['paper_id'].is_unique)
        paper_id_unique_msg = "Passed: All paper_ids are unique." if paper_id_unique_passed else "Failed: Duplicate paper_ids found."
    else:
        paper_id_non_null_passed = False
        paper_id_non_null_msg = "Failed: Column 'paper_id' is missing."
        paper_id_unique_passed = False
        paper_id_unique_msg = "Failed: Column 'paper_id' is missing."

    # Title checks
    if 'title' in df.columns:
        null_titles = int(df['title'].isnull().sum() + (df['title'].astype(str).str.strip() == '').sum())
        title_non_null_passed = null_titles == 0
        title_non_null_msg = f"Passed: 0 null/empty titles." if title_non_null_passed else f"Failed: Found {null_titles} null or empty titles."
    else:
        title_non_null_passed = False
        title_non_null_msg = "Failed: Column 'title' is missing."

    # Summary length check (minimum 30 words)
    if 'summary' in df.columns:
        word_counts = df['summary'].fillna('').astype(str).apply(lambda x: len(x.split()))
        short_summaries = int((word_counts < 30).sum())
        summary_length_passed = short_summaries == 0
        summary_length_msg = "Passed: All summaries meet the minimum length (>= 30 words)." if summary_length_passed else f"Failed: Found {short_summaries} summaries shorter than 30 words."
    else:
        summary_length_passed = False
        summary_length_msg = "Failed: Column 'summary' is missing."

    # Freshness check
    if 'age_days' in df.columns:
        stale_count = int((df['age_days'] > settings.freshness_threshold_days).sum())
        freshness_passed = stale_count == 0
        freshness_msg = f"Passed: 0 stale papers found (threshold: {settings.freshness_threshold_days} days)." if freshness_passed else f"Failed: Found {stale_count} stale papers."
    else:
        freshness_passed = False
        freshness_msg = "Failed: Column 'age_days' is missing."

    all_passed = bool(
        row_count_passed
        and paper_id_non_null_passed
        and paper_id_unique_passed
        and title_non_null_passed
        and summary_length_passed
        and freshness_passed
    )

    report = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "report_name": report_name,
        "total_records": row_count,
        "checks": {
            "row_count_check": {
                "passed": row_count_passed,
                "observed": row_count,
                "message": row_count_msg
            },
            "paper_id_non_null_check": {
                "passed": paper_id_non_null_passed,
                "observed": int(df['paper_id'].isnull().sum() + (df['paper_id'].astype(str).str.strip() == '').sum()) if 'paper_id' in df.columns else 0,
                "message": paper_id_non_null_msg
            },
            "paper_id_unique_check": {
                "passed": paper_id_unique_passed,
                "observed": paper_id_unique_passed,
                "message": paper_id_unique_msg
            },
            "title_non_null_check": {
                "passed": title_non_null_passed,
                "observed": int(df['title'].isnull().sum() + (df['title'].astype(str).str.strip() == '').sum()) if 'title' in df.columns else 0,
                "message": title_non_null_msg
            },
            "summary_length_check": {
                "passed": summary_length_passed,
                "observed": int((df['summary'].fillna('').astype(str).apply(lambda x: len(x.split())) < 30).sum()) if 'summary' in df.columns else 0,
                "message": summary_length_msg
            },
            "freshness_check": {
                "passed": freshness_passed,
                "observed": int((df['age_days'] > settings.freshness_threshold_days).sum()) if 'age_days' in df.columns else 0,
                "message": freshness_msg
            }
        },
        "all_passed": all_passed
    }

    report_path = settings.paths.quality_dir / f"{report_name}.json"
    write_json(report_path, report)
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path: Path | str) -> dict[str, Any]:
    """Generates the data freshness report and saves it to report_path."""
    total_rows = len(df)
    
    if total_rows == 0:
        latest_published = "N/A"
        oldest_published = "N/A"
        stale_rows = 0
        is_fresh = True
    else:
        # Check if 'published' column exists and find min/max
        if 'published' in df.columns:
            # Drop na and parse as string to make it JSON serializable
            published_series = df['published'].dropna().astype(str)
            if not published_series.empty:
                latest_published = str(published_series.max())
                oldest_published = str(published_series.min())
            else:
                latest_published = "N/A"
                oldest_published = "N/A"
        else:
            latest_published = "N/A"
            oldest_published = "N/A"
            
        if 'age_days' in df.columns:
            stale_rows = int((df['age_days'] > settings.freshness_threshold_days).sum())
        else:
            stale_rows = 0
            
        is_fresh = bool(stale_rows == 0)

    report = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "is_fresh": is_fresh
    }

    write_json(Path(report_path), report)
    return report
