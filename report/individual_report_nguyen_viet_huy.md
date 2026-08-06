# Member Role Report — Day 10: Data Pipeline & Data Observability

> Báo cáo của thành viên phụ trách **Integration & Pipeline Execution** (Thành viên 5).

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Viết Huy          |
| MSSV               | 2A202601081                |
| Khóa/Lớp         | K3                         |
| Tên nhóm         | B2                         |
| Vai trò chính    | Integration & Pipeline Execution |
| Repository         | https://github.com/VinUni-AI20k/K3_Day10_Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-08-06                 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | ----------- |
| Baseline pipeline | `src/pipelines/phase1.py` — `main()` | `Settings`; raw records từ `fetch_source_records`/`load_raw_records` (member 1); `build_clean_dataframe` (member 2); `build_test_set` (member 2); quality/freshness/reporting (member 3); index & metrics (reference) | `data/clean/papers_clean.{csv,json}`, `data/embeddings/papers_embeddings.json`, `data/eval/test_set.json`, `data/results/baseline_metrics.json`, `data/results/baseline_answers.json`, `data/quality/baseline.json`, `data/quality/freshness_report.json`, `data/reports/phase1_report.md` | Hoàn thành |
| Corruption flow | `src/pipelines/corruption_flow.py` — `main()` | baseline metrics/clean df; `corrupt_clean_dataframe` (member 4); raw records để repair; cùng eval test set | corrupted/repaired artifacts (`papers_clean_corrupted/repaired.*`, `papers_embeddings_corrupted/repaired.json`), `corrupted_metrics.json`, `repaired_metrics.json`, `corrupted/repaired_answers.json`, `data/quality/corrupted.json`, `data/quality/repaired.json`, `freshness_corrupted/repaired.json`, `data/results/corruption_log.json`, `data/reports/corruption_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Sửa contract key `source_summary` | Member 3 (`reporting.py`) — `phase1.py` đang truyền key `source/query/records`, report đọc `source_api/...` nên hiện N/A | Đổi sang đúng key; report phase 1 hiển thị đầy đủ nguồn dữ liệu |
| Sửa phrasing testset khớp extractor | Member 2 (`testset.py`) ↔ reference `qa.py` | Đổi câu hỏi `"Who authored..."`, `"What categories..."` để khớp keyword `qa.py`; baseline judge accuracy tăng từ 0.5 → 1.0 |
| Sửa LLM judge chạy qua gateway | `metrics.py` — `with_structured_output` fail qua 9router | Thêm plain-invoke + parse; judge LLM thật chạy được (0 fallback heuristic) |
| Dọn rác artifacts | Cả nhóm — 7 file `test_*` trong `data/` | `git rm` 7 file; `data/` chỉ còn artifact của pipeline |
| Mock integration test | Chính tôi — xác minh orchestration khi module khác chưa xong | 2 flow chạy xuyên suốt, đủ 10 + 16 artifact đúng đường dẫn |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Viết baseline pipeline | `src/pipelines/phase1.py` | `data/results/baseline_metrics.json` + `phase1_report.md` | `uv run python script/run_phase1.py` — exit 0 |
| Viết corruption flow | `src/pipelines/corruption_flow.py` | 3 bộ metrics + `corruption_report.md` | `uv run python script/run_corruption_flow.py` — exit 0 |
| Xác minh orchestration trước khi nhóm bàn giao | Mock test tại `Temp/opencode/member5_integration_test.py` (ngoài repo) | `ALL MOCK INTEGRATION CHECKS PASSED` | 10 (phase1) + 16 (corruption) artifact đúng đường dẫn |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

**`data/reports/corruption_report.md`** — bảng so sánh 3 trạng thái với số liệu thật từ judge LLM qua gateway: Baseline 100% hit / 5.00 judge score → Corrupted 40% hit / 2.67 → Repaired 100% hit / 4.95. Bảng này là tổng hợp của toàn bộ phần việc nhóm, do pipeline của tôi điều phối tạo ra.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Nối các module của 4 thành viên (ingestion, cleaning/testset, observability, corruption) thành 2 luồng chạy được end-to-end, đúng thứ tự, đúng artifact, và tái lập được.

### Cách triển khai

1. **Orchestration theo signature cố định**: `phase1.py`/`corruption_flow.py` không xử lý dữ liệu mà gọi đúng hàm theo interface đã định nghĩa trong starter (`fetch_source_records(settings)`, `build_clean_dataframe(records, run_date)`, `evaluate_pipeline(settings, index, test_set_path, metrics_path, answers_path)`, ...). Nhờ vậy viết được ngay cả khi module khác chưa xong.
2. **Collection name tự suy từ path** (`index.py:69-81`): truyền đúng `embeddings_json` / `corrupted_embeddings_json` / `repaired_embeddings_json` để baseline/corrupted/repaired dùng 3 collection ChromaDB riêng.
3. **Guard `_require`**: `corruption_flow.py` chặn sớm nếu thiếu `baseline_metrics.json`, `clean_csv`, `raw_records_json` → tránh chạy nhầm thứ tự gây lỗi khó đọc.
4. **Repair từ nguồn gốc**: bước repair = `build_clean_dataframe(load_raw_records(raw_records_json), run_date)` — chạy lại toàn bộ cleaning trên raw snapshot bất biến, không che lỗi.
5. **Freshness riêng cho từng trạng thái**: config chỉ có 1 path baseline nên flow dùng `data/quality/freshness_{corrupted,repaired}.json`.
6. **Fix judge qua gateway**: `with_structured_output` yêu cầu JSON schema nhưng gateway không tôn trọng → bọc try/except, plain `invoke` + regex parse (score/correct/reasoning).

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | `Settings` từ `.env`; raw records; clean df; test set (shared giữa 3 trạng thái) |
| Output                         | 27 artifact trong `data/`: raw, clean (3 trạng thái), embeddings manifests, test set, 3 bộ metrics+answers, quality/freshness, 2 reports, corruption_log |
| Module phụ thuộc             | `ingestion/*`, `evaluation/*`, `observability/*`, `retrieval/*`, `core/*` |
| Module sử dụng output        | `observability/reporting.py` đọc metrics/quality/freshness; báo cáo nhóm |
| Điều kiện lỗi cần xử lý | Thiếu baseline khi chạy corruption; judge LLM không hỗ trợ structured output; `raw_records.json` chưa tồn tại |

### Cách xác minh

```bash
uv run python script/run_phase1.py
uv run python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Cả 2 lệnh exit code 0; đủ artifact; metrics có câu chuyện giảm/phục hồi rõ ràng.
- **Kết quả thực tế:** Baseline 100/100/100/5.0 → Corrupted 40/39.4/40/2.67 → Repaired 100/100/97.5/4.95; quality FAILED→PASSED; freshness STALE→FRESH.
- **Artifact/log:** `data/results/baseline_metrics.json`, `data/results/corruption_log.json`, `data/reports/*.md` (không chứa secret).

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Chạy baseline lần đầu, `_judge_answer` trong `metrics.py` rơi vào heuristic fallback vì `with_structured_output` fail qua 9router → metrics chỉ là heuristic, không phản ánh LLM đánh giá.
- **Các phương án đã cân nhắc:**
  1. Chấp nhận heuristic fallback (không đổi code) — nhanh nhưng metrics kém ý nghĩa, không dùng được LLM đã cấu hình.
  2. Sửa `build_llm`/provider để dùng provider hỗ trợ JSON schema — thay đổi lớn, phụ thuộc hạ tầng.
  3. Sửa `_judge_answer`: giữ structured output, nếu fail thì plain invoke + parse text trả về.
- **Phương án đã chọn:** Phương án 3 — parse text fallback.
- **Lý do:** Giữ nguyên 2 provider khác; chi phí thêm 1 LLM call/câu chỉ khi structured output fail; tận dụng đúng LLM `gg` đã cấu hình qua 9router, metrics có ý nghĩa thật.
- **Bằng chứng quyết định phù hợp:** `baseline_answers.json` — 0 fallback heuristic, reasoning là văn bản của LLM; judge accuracy 0.5 (heuristic, do extractor trả sai authors/categories) → 1.0 (LLM + fix testset).

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `ValidationError ... Invalid JSON: expected value at line 1 column 1` khi gọi `with_structured_output(JudgeVerdict)` qua 9router; kết quả: `reasoning: "Fallback heuristic judge used because the LLM evaluator was unavailable."`
- **Lệnh hoặc bước tái hiện:** `uv run python script/run_phase1.py` rồi đọc `data/results/baseline_answers.json`.
- **Nguyên nhân gốc:** Combo `gg` qua gateway trả markdown (`**Score:** 5 ...`) thay vì JSON theo `response_format`; pydantic không parse được → exception → fallback.
- **Cách xử lý:** Trong `_judge_answer`, tách `build_llm`; bọc `with_structured_output(...).invoke` trong try, catch rồi `llm.invoke(prompt)` + `_parse_judge_text` (regex score/correct/reasoning).
- **Cách xác minh sau khi sửa:** `baseline_answers.json` — `fallback count = 0`, `score dist {5: 40}`.
- **Điều học được:** Không giả định mọi gateway OpenAI-compatible tôn trọng `response_format`; luôn có fallback parse và phân biệt "LLM đánh giá" với "heuristic".

Blockers đang xử lý:

- **Phạm vi bị ảnh hưởng:** `_run_ragas` (metrics Ragas) chưa hoàn tất với ragas 0.4.3.
- **Những gì đã loại trừ:** Đã sửa được lỗi `EmbeddingUsageEvent.model` (embeddings phải expose `model` dạng string) và API `dict(result)`; còn lỗi `to_pandas().mean()` với cột dtype string ở metric `answer_relevancy`.
- **Bước tiếp theo:** Lọc cột numeric trước khi mean (hoặc đọc `result._repr_dict`); chạy lại smoke trên 2 mẫu rồi chạy cả 2 pipeline với `RUN_RAGAS=1`.

## 7. Hiểu biết về luồng end-to-end

**Câu trả lời:**

1. **Crossref → vector index:** `fetch_source_records` gọi API với query/filter (`has-abstract:true`, 180 ngày), retry 429/503, lưu raw response + raw records; `build_clean_dataframe` chuẩn hóa text, tính `text_for_embedding` (Title | Authors | Summary) và `age_days`; `LocalEmbeddingIndex.build` embed bằng MiniLM và nạp vào ChromaDB kèm metadata.
2. **Test set & ground-truth doc IDs:** `build_test_set` sinh 40 câu (summary/authors/date/categories) từ clean df; `ground_truth_doc_ids` trỏ đúng `paper_id` của doc chứa câu trả lời. `answer_question` trả `retrieved_doc_ids`; `evaluate_pipeline` tính `retrieval_hit` nếu có doc đúng nằm trong top-k, cùng token F1 và judge LLM.
3. **Quality checks vs freshness:** Quality checks kiểm tra *tính hợp lệ cấu trúc* (row count, unique paper_id, title, summary length) — trả `all_passed`; freshness chỉ đo *độ tươi* theo `age_days` vs threshold 180 ngày — trả `is_fresh`. Hai báo cáo khác nhau, corruption đánh trúng cả hai.
4. **Cùng test set cho 3 trạng thái:** Giữ nguyên câu hỏi + ground truth để cô lập biến "dữ liệu index"; mọi chênh lệch metrics đều do dữ liệu (corrupted/repaired) chứ không phải do test set đổi — cần cho so sánh nhân quả.
5. **Repair thành công dựa trên gì:** Dựa trên việc `repaired_metrics.json` phục hồi về baseline (hit 100%, judge 4.95) và quality/freshness repaired trở lại PASSED/FRESH — vì repair chạy lại cleaning từ raw snapshot nên "phục hồi" là tái lập dữ liệu sạch, không phải che lỗi.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | 100% | 40% | 100% | Drop 25% bài mới nhất khiến 24/40 câu mất doc gốc khỏi index → hit tụt 60 điểm; repair khôi phục đủ |
| `mean_token_f1`      | 100% | 39.4% | 100% | Blank/noise summary + truncate title làm embedding sai lệch, context trả về không khớp |
| `judge_accuracy`     | 100% | 40% | 97.5% | LLM judge phản ánh đúng độ hỏng; 1 câu repaired vẫn lệch nhẹ do ngưỡng đánh giá |
| `mean_judge_score`   | 5.00 | 2.67 | 4.95 | Corrupted gần mức "không trả lời được" (2.67/5) |
| Quality checks         | PASSED | FAILED (dup, summary ngắn, stale) | PASSED | Quality bắt đúng 3/6 scenario: duplicate 2, summary<30 từ 4, stale 3 |
| Freshness status       | FRESH | STALE | FRESH | Scenario sửa ngày 2000 bị freshness bắt ngay |

### Kết luận từ số liệu

1. **Corruption → signal → agent metric:** Drop latest + blank summary + noise + stale date → `quality all_passed=False`, `freshness is_fresh=False` → retrieval hit giảm 100%→40% và judge score 5.0→2.67.
2. **Repair → phục hồi → agent metric:** Repair từ raw snapshot → quality repaired `all_passed=True`, freshness FRESH → hit phục hồi 40%→100%, judge 2.67→4.95 (97.5% accuracy).

**Corruption ảnh hưởng rõ nhất:** Drop Latest Records — 6/24 bài mới nhất bị xóa khiến retrieval hit rate sụt 60 điểm, vì test set lấy sample từ chính các bài mới nhất nên mất doc gốc. Đây là kịch bản "mất dữ liệu mới" — loại lỗi nguy hiểm nhất với hệ thống phải luôn cập nhật.

**Kết quả khác kỳ vọng:** Ban đầu judge accuracy chỉ 0.5 kể cả baseline — không phải do corruption mà do testset phrasing không khớp extractor (`qa.py`) khiến câu hỏi authors/categories trả về summary. Đã kiểm tra bằng cách đọc `baseline_answers.json` (20/40 câu trả sai loại) và sửa phrasing; sau sửa baseline đạt 1.0.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Data pipeline:** Thiết kế theo contract signature + artifact path là chìa khóa ghép nhóm song song; tách "lỗi của mình" bằng mock test trước khi ghép thật.
2. **Data quality/observability:** Quality checks (cấu trúc) và freshness (độ tươi) bắt 2 nhóm lỗi khác nhau — cần cả hai; giữ raw snapshot là nền tảng để repair.
3. **Data → RAG agent:** Chất lượng dữ liệu vào vector store quyết định trực tiếp retrieval và câu trả lời; lỗi data ẩn (trống summary, sai ngày) sẽ đi thẳng vào ChromaDB nếu không có monitoring.

### Nếu có thêm thời gian

Hoàn tất Ragas (`RUN_RAGAS=1`) với 4 metrics LLM-based (answer_relevancy, context_precision/recall, faithfulness) để có thêm bằng chứng định tính về retrieval qua 3 trạng thái; đo bằng việc `context_recall` giảm khi paper bị drop và phục hồi sau repair trong `baseline/corrupted/repaired_metrics.json`.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [ ] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Viết Huy
**Ngày xác nhận:** 2026-08-06
