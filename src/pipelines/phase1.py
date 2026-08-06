from __future__ import annotations

import os

from core.config import Settings, load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def _load_or_fetch_records(settings: Settings) -> list:
    records_path = settings.paths.raw_records_json
    if settings.refresh_source or not records_path.exists():
        return fetch_source_records(settings)
    return load_raw_records(records_path)


def _run_agent_demo(settings: Settings, index: LocalEmbeddingIndex) -> None:
    if os.getenv("RUN_AGENT_DEMO", "").lower() not in {"1", "true", "yes"}:
        return
    try:
        from retrieval.agent import build_agent, run_agent_question

        agent = build_agent(settings, index)
        test_set = read_json(settings.paths.eval_testset)
        demo = [
            {"question": item["question"], "answer": run_agent_question(agent, item["question"])}
            for item in test_set[:3]
        ]
        write_json(settings.paths.demo_answers, demo)
        print(f"[phase1] Agent demo wrote {len(demo)} answers to {settings.paths.demo_answers}")
    except Exception as exc:  # pragma: no cover
        print(f"[phase1] Agent demo skipped: {exc}")


def main() -> None:
    """Baseline pipeline: fetch/load raw -> clean -> index -> eval -> quality/freshness -> report."""
    settings = load_settings()
    run_date = now_utc()

    records = _load_or_fetch_records(settings)
    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "source_filter": settings.source_filter,
        "max_results": settings.max_results,
        "fetched_records": len(records),
    }
    print(f"[phase1] Loaded {len(records)} raw records from {settings.source_api}")

    clean_df = build_clean_dataframe(records, run_date)
    write_csv(clean_df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, clean_df.to_dict(orient="records"))
    print(f"[phase1] Cleaned {len(clean_df)} rows -> {settings.paths.clean_csv}")

    index = LocalEmbeddingIndex.build(clean_df, settings, settings.paths.embeddings_json)
    print(f"[phase1] Index built in collection {index.collection_name}")

    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        build_test_set(clean_df, settings.paths.eval_testset)
        print(f"[phase1] Test set written -> {settings.paths.eval_testset}")

    bundle = evaluate_pipeline(
        settings,
        index,
        settings.paths.eval_testset,
        settings.paths.baseline_metrics,
        settings.paths.baseline_answers,
    )
    print(f"[phase1] Baseline metrics: {bundle.summary}")

    quality = run_data_quality_checks(clean_df, settings, "baseline")
    freshness = build_freshness_report(clean_df, settings, settings.paths.freshness_report)
    print(f"[phase1] Quality checks: {quality}")

    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary,
        bundle.summary,
        quality,
        freshness,
    )
    print(f"[phase1] Report written -> {settings.paths.baseline_report}")

    _run_agent_demo(settings, index)
