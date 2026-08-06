from __future__ import annotations

import pandas as pd

from core.config import Settings, load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def _freshness_report_path(settings: Settings, name: str):
    return settings.paths.quality_dir / f"freshness_{name}.json"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    """Corruption flow: corrupt baseline -> evaluate -> quality -> repair from raw -> re-evaluate -> compare."""
    settings = load_settings()
    run_date = now_utc()

    _require(
        settings.paths.baseline_metrics.exists(),
        "Baseline metrics not found. Run script/run_phase1.py first.",
    )
    _require(
        settings.paths.clean_csv.exists(),
        "Baseline clean dataset not found. Run script/run_phase1.py first.",
    )
    _require(
        settings.paths.raw_records_json.exists(),
        "Raw records not found. Run baseline with source fetch first.",
    )

    baseline_metrics = read_json(settings.paths.baseline_metrics)
    print(f"[corruption] Loaded baseline metrics: {baseline_metrics}")

    baseline_df = pd.read_csv(settings.paths.clean_csv)
    corrupted_df = corrupt_clean_dataframe(baseline_df, settings.paths.corruption_log)
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))
    print(f"[corruption] Corrupted {len(corrupted_df)} rows -> {settings.paths.corrupted_clean_csv}")

    corrupted_index = LocalEmbeddingIndex.build(corrupted_df, settings, settings.paths.corrupted_embeddings_json)
    corrupted_bundle = evaluate_pipeline(
        settings,
        corrupted_index,
        settings.paths.eval_testset,
        settings.paths.corrupted_metrics,
        settings.paths.corrupted_answers,
    )
    print(f"[corruption] Corrupted metrics: {corrupted_bundle.summary}")

    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted")
    corrupted_freshness = build_freshness_report(
        corrupted_df, settings, _freshness_report_path(settings, "corrupted")
    )
    print(f"[corruption] Corrupted quality checks: {corrupted_quality}")

    repaired_df = build_clean_dataframe(load_raw_records(settings.paths.raw_records_json), run_date)
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, repaired_df.to_dict(orient="records"))
    print(f"[corruption] Repaired {len(repaired_df)} rows from raw -> {settings.paths.repaired_clean_csv}")

    repaired_index = LocalEmbeddingIndex.build(repaired_df, settings, settings.paths.repaired_embeddings_json)
    repaired_bundle = evaluate_pipeline(
        settings,
        repaired_index,
        settings.paths.eval_testset,
        settings.paths.repaired_metrics,
        settings.paths.repaired_answers,
    )
    print(f"[corruption] Repaired metrics: {repaired_bundle.summary}")

    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired")
    repaired_freshness = build_freshness_report(repaired_df, settings, _freshness_report_path(settings, "repaired"))
    print(f"[corruption] Repaired quality checks: {repaired_quality}")

    generate_corruption_report(
        settings.paths.comparison_report,
        baseline_metrics,
        corrupted_bundle.summary,
        repaired_bundle.summary,
        corrupted_quality,
        repaired_quality,
        corrupted_freshness,
        repaired_freshness,
    )
    print(f"[corruption] Comparison report written -> {settings.paths.comparison_report}")
