# Group Report — Day 10: Data Pipeline & Data Observability

> Dùng mẫu này cho báo cáo chung của nhóm 3–5 thành viên. Thay toàn bộ nội dung trong dấu `[ ]` bằng thông tin và kết quả thực tế. Xóa các dòng hướng dẫn không còn cần thiết trước khi nộp.

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K3              |
| Tên nhóm         | B2     |
| Repository         | https://github.com/vdungx/B2_D305_K3_Data-Pipeline-Data-Observability.git |
| Ngày hoàn thành | [2026-08-06]               |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Đàm Lê Minh Quân | 2A202601451 | Source Ingestion | `src/ingestion/crossref.py`, `data/raw/crossref_records.json` |
| 2 | Trần Văn Dũng | 2A202601859 | Data Cleaning & Test Set | `src/ingestion/cleaning.py`, `src/evaluation/testset.py`, `data/clean/papers_clean.csv`, `data/eval/test_set.json` |
| 3 | Lê Văn Đông | 2A202601851 | Observability & Reporting | `src/observability/quality.py`, `src/observability/reporting.py`, `data/quality/`, `data/reports/` |
| 4 | Đào Đức Mạnh | 2A202601833 | Corruption & Repair | `src/ingestion/corruption.py`, `data/clean/papers_clean_corrupted.csv`, `data/results/corruption_log.json` |
| 5 | Nguyễn Viết Huy | 2A202601081 | Integration & Comparison | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`, `script/` |

## 2. Tóm tắt kết quả

Viết từ 150–250 từ, trả lời ngắn gọn:

- Nhóm đã hoàn thành những phần nào?
- Baseline pipeline đã tạo ra các artifact nào?
- Corruption nào ảnh hưởng rõ nhất đến data quality hoặc agent?
- Repair đã phục hồi được chỉ số nào?
- Blocker hoặc giới hạn quan trọng nhất còn lại là gì?

**Tóm tắt của nhóm:**

Nhóm B2 (K3) đã hoàn thành xây dựng và vận hành thành công Data Pipeline & Data Observability cho hệ thống RAG Agent bài báo học thuật. Trong Pha Baseline, dữ liệu thô từ Crossref API (24 bản ghi) được làm sạch, bóc tách thẻ HTML/XML, trích xuất thông tin tác giả và danh mục, chuẩn hóa ngày xuất bản ISO và tính độ tươi dữ liệu (`age_days`). Dữ liệu sạch được indexed vào ChromaDB Vector Store (`papers-baseline`) và đánh giá trên bộ 40 câu hỏi kiểm thử cố định (Frozen Evaluation Set). 

Trong Pha Corruption, nhóm đã giả lập 6 kịch bản lỗi dữ liệu ngầm (drop bản ghi mới, trống summary, tiêm nhiễu text, truncate title, sửa ngày xuất bản cũ về năm 2000, tạo dòng trùng lặp). Hệ thống Data Quality Checks và Freshness Monitoring ngay lập tức phát hiện các lỗi bất thường và kích hoạt cảnh báo đỏ. Hiệu năng RAG Agent bị suy giảm nghiêm trọng (Retrieval Hit Rate và Judge Score sụt giảm). Sau khi thực thi quy trình Repair phục hồi từ bản ghi thô nguyên bản (`data/raw/`), toàn bộ chất lượng dữ liệu và hiệu năng RAG Agent đã được khôi phục về mức ban đầu.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

Điều chỉnh sơ đồ dưới đây nếu cách triển khai thực tế của nhóm khác starter:

```text
Crossref API
    -> raw response/raw records
    -> cleaning và data modeling
    -> embedding + ChromaDB index
    -> evaluation baseline
    -> quality/freshness reports
    -> corruption
    -> re-index và re-evaluate
    -> repair từ dữ liệu nguồn
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| --- | --- | --- | --- | --- |
| Ingestion | Crossref API / Settings | Fetch data với retry/backoff, parse sang `PaperRecord` | `data/raw/crossref_records.json` | Quân (1) |
| Cleaning & Test set | `list[PaperRecord]` từ Quân (1) | Normalize text, calculate `age_days`, tạo `text_for_embedding`, tạo test set 4 loại Q&A | `data/clean/papers_clean.csv`, `data/eval/test_set.json` | Dũng (2) |
| Observability | Clean/Corrupted DataFrame từ Dũng (2) & Mạnh (4) | Data Quality checks, Freshness monitoring, xuất báo cáo Markdown | `data/quality/freshness_report.json`, `data/reports/*.md` | Đông (3) |
| Corruption & Repair | Clean DataFrame từ Dũng (2) & Raw records từ Quân (1) | Simulate 6 dạng corruption, log hỏng dữ liệu, repair khôi phục từ raw | `data/clean/papers_clean_corrupted.csv`, `data/results/corruption_log.json` | Mạnh (4) |
| Orchestration | Modules từ TV 1, 2, 3, 4 | Điều phối Phase 1 Baseline & Corruption Flow, Index ChromaDB, E2E Evaluation | `data/results/baseline_metrics.json`, `data/results/repaired_metrics.json` | Huy (5) |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | `openrouter` |
| `LLM_MODEL`                | `gc/gemini-2.5-flash` |
| Embedding model              | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 |
| Retrieval`top_k`           | 4 |
| Freshness threshold          | 180 ngày |
| Random seed, nếu có        | 42 |



Không dán nội dung API key hoặc file `.env` vào báo cáo.

### Lệnh cài đặt

Chỉ giữ lại cách nhóm đã dùng.

```bash
uv sync
```

Hoặc:

```bash
python -m pip install -e .
```

### Lệnh chạy

Baseline:

```bash
uv run python script/run_phase1.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_phase1.py
```

Corruption flow:

```bash
uv run python script/run_corruption_flow.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công | 2026-08-06 09:50 | `data/results/baseline_metrics.json` |
| Corruption flow   | Thành công | 2026-08-06 09:55 | `data/reports/corruption_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | Crossref REST API (`https://api.crossref.org/works`) |
| Query/filter                | Query: `agentic retrieval augmented generation large language model`, Filter: `from-pub-date:2024-02-08,has-abstract:true` |
| Thời điểm lấy dữ liệu | 2026-08-06 |
| Số record nhận được    | 24 |
| Cơ chế retry/backoff      | HTTP GET request với exponential backoff cho status codes 429 (Rate limit) & 503, max 3 retries |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` | String | Có | Mã định danh DOI bài báo | Drop record nếu rỗng |
| `title` | String | Có | Tiêu đề bài báo | Bóc sạch XML/HTML tags, drop nếu rỗng |
| `summary` | String | Có | Tóm tắt/Abstract bài báo | Bóc sạch XML/HTML tags, lọc bỏ nếu < 100 ký tự |
| `authors` | List[String] | Không | Danh sách tác giả | Gộp thành `authors_joined`, mặc định "Unknown Author" |
| `categories` | List[String] | Không | Chủ đề / danh mục | Gộp thành `categories_joined`, mặc định "General" |
| `published` | String | Có | Ngày xuất bản YYYY-MM-DD | Parse ngày chuẩn ISO, dùng run_date nếu thiếu |
| `age_days` | Integer | Có | Khoảng cách tuổi dữ liệu (ngày) | `max(0, (run_date - published).days)` |
| `text_for_embedding` | String | Có | Văn bản hợp nhất cho Vector Embeddings | `Title: [title] | Authors: [authors] | Summary: [summary]` |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Lọc bỏ bản ghi thiếu title/DOI hoặc summary < 100 ký tự | Completeness / Validity | 0 | Kiểm tra `papers_clean.csv` |
| Bóc sạch các thẻ HTML/XML (`<jats:p>`, `<b>`) | Validity / Consistency | 24 | Regex clean check trong `cleaning.py` |
| Loại bỏ các bản ghi trùng lặp theo `paper_id` và `title` | Uniqueness | 0 | `df.drop_duplicates()` |

Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:

Dữ liệu thô từ Crossref API được gọt bỏ các thẻ HTML/XML rác trong tiêu đề và tóm tắt. Nhóm sử dụng `paper_id` (DOI) làm document ID duy nhất trong vector database. Cột `text_for_embedding` được tổng hợp chuẩn hóa theo định dạng `Title: [title] | Authors: [authors_joined] | Summary: [summary]` giúp MiniLM embedding capture đầy đủ cả ngữ nghĩa tiêu đề, tác giả và nội dung tóm tắt. Cột `age_days` được tính từ ngày xuất bản đến `run_date` nhằm giám sát chỉ số Data Freshness.

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | 40 |
| Các`question_type`                    | `summary`, `authors`, `date`, `categories` |
| Ground-truth document ID                 | Trích xuất trực tiếp từ `paper_id` tương ứng của bản ghi sạch |
| Embedding model                          | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection                  | ChromaDB / Collection `papers-baseline` |
| Retrieval`top_k`                       | 4 |
| LLM provider/model                       | OpenRouter / `gc/gemini-2.5-flash` |

| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` (Frozen Evaluation Set) |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

Bộ câu hỏi kiểm thử được đóng băng cố định (Frozen Evaluation Set) nhằm tạo ra một thước đo cố định (Baseline Benchmark) duy nhất. Điều này bảo đảm rằng mọi sự sụt giảm hay phục hồi của các chỉ số `retrieval_hit_rate`, `token_f1`, và `judge_accuracy` qua 3 pha (Baseline, Corrupted, Repaired) đều xuất phát từ chất lượng dữ liệu thay vì do thay đổi bộ câu hỏi.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | Có | Đã tải 24 bản ghi thô từ Crossref API |
| Cleaned dataset          | `data/clean/`                        | Có | `papers_clean.csv` & `papers_clean.json` (24 bài chuẩn hóa) |
| Embedding manifest/index | `data/embeddings/`                   | Có | Manifest và ChromaDB Vector index |
| Evaluation set           | `data/eval/`                         | Có | `test_set.json` (40 câu hỏi đóng băng) |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có | Kết quả đánh giá pha Baseline |
| Quality/freshness        | `data/quality/`                      | Có | Báo cáo Data Quality và Freshness report |
| Baseline report          | `data/reports/phase1_report.md`      | Có | Báo cáo Markdown Baseline |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |     100.00% | Tỉ lệ tìm thấy đúng văn bản đạt tuyệt đối trên dữ liệu sạch |
| `mean_token_f1`      |     88.50% | Điểm tương đồng từ vựng cao giữa câu trả lời và ground-truth |
| `judge_accuracy`     |     95.00% | Tỉ lệ câu trả lời được LLM Judge đánh giá là chính xác |
| `mean_judge_score`   |     4.75 / 5.0 | Điểm đánh giá trung bình chất lượng câu trả lời |
| Ragas, nếu có        | N/A | Bỏ qua để tối ưu tốc độ thực thi (bật bằng `RUN_RAGAS=1`) |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| Row Count Check | Completeness | Total rows > 0 | PASSED (24 records) | `data/quality/baseline_quality.json` |
| Paper ID Non-Null Check | Completeness | 0 null/empty paper_ids | PASSED (0 nulls) | `data/quality/baseline_quality.json` |
| Paper ID Unique Check | Uniqueness | All paper_ids unique | PASSED (Unique) | `data/quality/baseline_quality.json` |
| Title Non-Null Check | Validity | 0 null/empty titles | PASSED (0 nulls) | `data/quality/baseline_quality.json` |
| Summary Length Check | Validity | Summary words >= 30 | PASSED (All >= 30 words) | `data/quality/baseline_quality.json` |
| Freshness Check | Timeliness | age_days <= 180 days | PASSED (0 stale papers) | `data/quality/freshness_report.json` |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | Cleaned Dataset (`papers_clean.json`) |
| Timestamp mới nhất       | `2026-08-01` |
| Ngưỡng freshness         | `180 ngày` |
| Trạng thái baseline      | `FRESH (Dữ liệu tươi mới)` |
| Lý do                     | Tất cả 24 bài báo đều có `age_days <= 180` ngày so với thời điểm thực thi |


## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| Drop Latest Records | Xóa 25% bài báo mới nhất xuất bản năm 2026 | 6 | Row count giảm, Freshness sụt giảm | Retrieval Hit Rate giảm mạnh trên câu hỏi bài mới | Tải lại từ `data/raw/crossref_records.json` |
| Blank Summary | Đặt rỗng `summary = ""` cho 15% bản ghi | 4 | Summary Length Check FAILED | Context embedding rỗng, LLM Judge Score giảm còn 1/5 | Re-extract abstract từ raw records |
| Text Noise Injection | Thêm chuỗi rác/gibberish vào summary | 5 | Validity / Relevance FAILED | Vector distance méo mó, F1 score suy giảm | Làm sạch lại text từ nguồn thô gốc |
| Title Truncation | Cắt ngắn tiêu đề bài báo còn 5-10 ký tự | 5 | Title Length Check WARNING | Mất thông tin tiêu đề, Retrieval mis-match | Reset lại tiêu đề đầy đủ từ raw data |
| Stale Date Alteration | Đổi ngày xuất bản về năm 2000 | 5 | Freshness Check FAILED | Trạng thái Freshness báo đỏ STALE | Parse lại ISO date gốc từ raw snapshot |
| Duplicate Rows | Nhân đôi 3 bản ghi trong dataframe | 3 | Paper ID Unique Check FAILED | Duplicated contexts returned | Thực thi `drop_duplicates(subset=['paper_id'])` |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Ghi nhận đầy đủ 6 kịch bản hỏng dữ liệu, số bản ghi bị tác động và các tham số nhiễu tương ứng.

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

Nhóm triển khai quy trình Repair bằng cách đọc lại trực tiếp snapshot bản ghi thô ban đầu `data/raw/crossref_records.json` (Raw Ingestion Artifact do Quân - TV 1 thu thập) thay vì chỉnh sửa thủ công trên dataframe bị hỏng. Hàm `build_clean_dataframe` của Dũng - TV 2 được tái thực thi để bóc tách lại thẻ HTML/XML, parse ISO date chuẩn xác và tái tạo lại cột `text_for_embedding`. Kết quả làm sạch được lưu thành `papers_clean_repaired.csv` và ChromaDB Vector index được xây dựng lại (`papers-repaired`).

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |   100.00% |    55.00% |  100.00% |                  -45.00% |        +45.00% | Sụt giảm mạnh khi mất bản ghi/rỗng summary, phục hồi hoàn toàn sau Repair |
| `mean_token_f1`        |    88.50% |    42.10% |   88.50% |                  -46.40% |        +46.40% | F1 giảm sâu do context nhiễu/thiếu, phục hồi hoàn toàn sau Repair |
| `judge_accuracy`       |    95.00% |    40.00% |   95.00% |                  -55.00% |        +55.00% | LLM Judge đánh giá sai lệch cao ở Corrupted, phục hồi hoàn toàn sau Repair |
| `mean_judge_score`     | 4.75 / 5.0 | 2.10 / 5.0 | 4.75 / 5.0 |                    -2.65 |          +2.65 | Điểm Judge trung bình sụt giảm nghiêm trọng, phục hồi tuyệt đối sau Repair |
| Quality checks pass/fail | PASSED (All) | FAILED (3) | PASSED (All) | 3 Cảnh báo Đỏ | 100% PASSED | Phát hiện kịp thời lỗi unique, length và freshness |
| Freshness status         | FRESH | STALE | FRESH | Chuyển sang STALE | Phục hồi FRESH | Phát hiện chính xác 5 bản ghi bị sửa lùi ngày xuất bản |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. `Data Corruption (Mất bản ghi & Nhiễu text)` $\rightarrow$ `Observability Quality Checks FAILED` $\rightarrow$ `Retrieval Hit Rate giảm từ 100% xuống 55% & Judge Score giảm từ 4.75 xuống 2.10`.
2. `Repair Action (Phục hồi từ raw snapshot)` $\rightarrow$ `Observability Quality Checks & Freshness PASSED (All)` $\rightarrow$ `Retrieval Hit Rate & Judge Score phục hồi 100% về mức Baseline`.

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:

- **Triệu chứng:** Lỗi mã hóa Unicode (`charmap codec can't encode character`) khi in ký tự tiếng Việt ra console Windows PowerShell khi thực thi script báo cáo Observability.
- **Nguyên nhân:** Windows PowerShell mặc định sử dụng bảng mã CP1252 cho stdout thay vì UTF-8.
- **Cách xử lý:** Thiết lập biến môi trường `$env:PYTHONIOENCODING="utf-8"` và đảm bảo tất cả các hàm I/O mở file đọc/ghi luôn ghi rõ `encoding="utf-8"`.
- **Cách xác minh:** Thực thi lệnh `$env:PYTHONIOENCODING="utf-8"; python script/test_observability.py` và kiểm tra console xuất ra UTF-8 chuẩn xác.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Template-based Q&A Generator | Bộ câu hỏi kiểm thử sinh ra theo khung rập khuôn | Bổ sung module LLM Paraphraser để tự nhiên hóa câu hỏi |
| Đánh giá Ragas phụ thuộc mạng ngoài | Quá trình Ragas evaluation đôi khi bị nghẽn API | Bật chế độ chạy Ragas bất đồng bộ bằng `RUN_RAGAS=1` |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.

