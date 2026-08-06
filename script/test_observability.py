import sys
from pathlib import Path
import pandas as pd

# Thêm src vào sys.path để import các module local
project_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(project_dir / "src"))

from core.config import load_settings
from observability.quality import run_data_quality_checks, build_freshness_report
from observability.reporting import generate_phase1_report, generate_corruption_report

def main():
    print("=== Khởi chạy kiểm thử cục bộ cho Observability (Thành viên 3) ===")
    
    # 1. Load settings
    settings = load_settings(project_dir=project_dir)
    print("Đã tải cấu hình thành công.")
    
    # 2. Tạo dữ liệu giả lập (Mock Clean DataFrame)
    clean_data = {
        "paper_id": ["10.1001/paper1", "10.1002/paper2", "10.1003/paper3"],
        "title": ["Agentic RAG Systems: A Survey", "Advanced Ingestion Pipelines for LLMs", "Observability in AI Workflows"],
        "summary": [" ".join(["word"] * 35)] * 3,  # 35 từ (đáp ứng điều kiện >= 30)
        "published": ["2026-05-01", "2026-06-01", "2026-07-01"],
        "age_days": [60, 30, 5]  # nhỏ hơn freshness threshold (180 ngày)
    }
    df_clean = pd.DataFrame(clean_data)
    
    # Tạo dữ liệu giả lập bị lỗi (Mock Corrupted DataFrame)
    corrupted_data = {
        "paper_id": ["10.1001/paper1", "10.1001/paper1", ""],  # Trùng lặp và rỗng
        "title": ["Agentic RAG Systems: A Survey", "", "Observability in AI Workflows"],  # Tiêu đề rỗng
        "summary": [" ".join(["word"] * 35), "short summary", ""],  # Tóm tắt quá ngắn và rỗng
        "published": ["2026-05-01", "2000-01-01", "2026-07-01"],  # Ngày xuất bản quá cũ
        "age_days": [60, 9000, 5]  # Lỗi thời (stale)
    }
    df_corrupted = pd.DataFrame(corrupted_data)

    print("\n--- 1. Chạy Quality Checks ---")
    # Chạy checks trên dữ liệu sạch
    clean_quality = run_data_quality_checks(df_clean, settings, "test_clean_quality")
    print(f"Clean quality all_passed: {clean_quality['all_passed']}")
    
    # Chạy checks trên dữ liệu lỗi
    corrupted_quality = run_data_quality_checks(df_corrupted, settings, "test_corrupted_quality")
    print(f"Corrupted quality all_passed: {corrupted_quality['all_passed']}")
    
    print("\n--- 2. Chạy Freshness Report ---")
    clean_freshness = build_freshness_report(df_clean, settings, settings.paths.quality_dir / "test_clean_freshness.json")
    print(f"Clean freshness is_fresh: {clean_freshness['is_fresh']}")
    
    corrupted_freshness = build_freshness_report(df_corrupted, settings, settings.paths.quality_dir / "test_corrupted_freshness.json")
    print(f"Corrupted freshness is_fresh: {corrupted_freshness['is_fresh']}")

    print("\n--- 3. Chạy Sinh Báo Cáo Markdown ---")
    # Tạo mock metrics
    mock_metrics = {
        "retrieval_hit_rate": 0.90,
        "mean_token_f1": 0.78,
        "judge_accuracy": 0.85,
        "mean_judge_score": 4.2,
        "ragas": {
            "answer_relevancy": 0.88,
            "faithfulness": 0.82
        }
    }
    
    mock_corrupted_metrics = {
        "retrieval_hit_rate": 0.40,
        "mean_token_f1": 0.35,
        "judge_accuracy": 0.30,
        "mean_judge_score": 1.8,
        "ragas": {
            "skipped": "Skipped due to poor quality data"
        }
    }
    
    mock_repaired_metrics = {
        "retrieval_hit_rate": 0.89,
        "mean_token_f1": 0.77,
        "judge_accuracy": 0.84,
        "mean_judge_score": 4.1,
        "ragas": {
            "answer_relevancy": 0.87,
            "faithfulness": 0.81
        }
    }

    # Xuất báo cáo pha 1
    phase1_report_path = settings.paths.project_dir / "data" / "reports" / "test_phase1_report.md"
    generate_phase1_report(
        phase1_report_path,
        source_summary={"source_api": "Crossref REST API", "source_query": "agentic RAG", "source_filter": "from-pub-date:2026-02-07", "max_results": 24, "fetched_records": 24},
        metrics=mock_metrics,
        quality=clean_quality,
        freshness=clean_freshness
    )
    print(f"Đã xuất báo cáo Phase 1 thử nghiệm tại: {phase1_report_path}")

    # Xuất báo cáo so sánh đối chiếu
    comparison_report_path = settings.paths.project_dir / "data" / "reports" / "test_corruption_report.md"
    generate_corruption_report(
        comparison_report_path,
        baseline_metrics=mock_metrics,
        corrupted_metrics=mock_corrupted_metrics,
        repaired_metrics=mock_repaired_metrics,
        corrupted_quality=corrupted_quality,
        repaired_quality=clean_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=clean_freshness
    )
    print(f"Đã xuất báo cáo So sánh thử nghiệm tại: {comparison_report_path}")
    print("\n=== Tất cả kiểm thử cục bộ hoàn tất thành công! ===")

if __name__ == "__main__":
    main()
