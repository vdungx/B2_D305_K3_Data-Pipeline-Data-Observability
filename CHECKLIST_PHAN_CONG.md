# Checklist Phân Công Công Việc Chi Tiết (Nhóm 5 Thành Viên)
## Bài Lab: Data Pipeline & Data Observability (Day 10)

---

## 👤 Thành viên 1: Đàm Lê Minh Quân (Source Ingestion)
**Phụ trách chính**: `src/ingestion/crossref.py`


- [ ] **1. Tìm hiểu cấu trúc dữ liệu Crossref API**
  - Đọc tài liệu Crossref API (`https://api.crossref.org/works`).
  - Nắm rõ các trường: `DOI`, `title`, `abstract`, `author`, `subject`, `published-print`, `URL`, `publisher`.

- [ ] **2. Hoàn thành hàm `parse_crossref_payload(payload: dict) -> list[PaperRecord]`**
  - [ ] Duyệt qua danh sách `payload["message"]["items"]`.
  - [ ] Trích xuất `paper_id` (DOI) và `title`. Bỏ qua bản ghi nếu thiếu một trong hai.
  - [ ] Làm sạch chuỗi abstract: Xóa các thẻ HTML/XML như `<jats:p>`, `</jats:p>` và chuẩn hóa khoảng trắng.
  - [ ] Trích xuất danh sách `authors` (`given` + `family` name).
  - [ ] Trích xuất `categories` (từ `subject` hoặc `container-title`) và xác định `primary_category`.
  - [ ] Parse ngày xuất bản `published` về định dạng ISO `YYYY-MM-DD`.
  - [ ] Lấy `abs_url`, `pdf_url` (nếu có link PDF) và `comment` (publisher).
  - [ ] Trả về danh sách đối tượng `PaperRecord`.

- [ ] **3. Hoàn thành hàm `fetch_source_records(settings: Settings) -> list[PaperRecord]`**
  - [ ] Khởi tạo tham số query từ `settings.source_query`, `settings.source_filter`, `settings.max_results`.
  - [ ] Gửi request HTTP GET kèm User-Agent hợp lệ.
  - [ ] Cài đặt retry với exponential backoff khi gặp lỗi HTTP `429` (Rate limit) hoặc `503`.
  - [ ] Lưu payload thô vào `settings.paths.raw_api_response` (`data/raw/crossref_response.json`).
  - [ ] Gọi `parse_crossref_payload` và lưu danh sách records vào `settings.paths.raw_records_json` (`data/raw/crossref_records.json`).

- [ ] **4. Hoàn thành hàm `load_raw_records(path: Path) -> list[PaperRecord]`**
  - [ ] Đọc file JSON snapshot và map các dict thành danh sách `PaperRecord`.

- [ ] **5. Kiểm thử thành phần (Verification)**
  - Chạy thử nghiệm hàm ingestion và kiểm tra 2 file sinh ra trong `data/raw/`.

---

## 👤 Thành viên 2: Trần Văn Dũng (Data Cleaning & Test Set)
**Phụ trách chính**: `src/ingestion/cleaning.py`, `src/evaluation/testset.py`

- [x] **1. Hoàn thành hàm `build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame` trong `cleaning.py`**
  - [x] Chuẩn hóa các trường văn bản (`title`, `summary`, `authors`, `categories`).
  - [x] Parse ngày xuất bản và tính cột `age_days = (run_date - published).days`.
  - [x] Tạo các cột helper quan trọng:
    - `authors_joined`: Chuỗi nối tên các tác giả bằng dấu phẩy.
    - `categories_joined`: Chuỗi nối các danh mục.
    - `summary_chars`: Số lượng ký tự của summary.
    - `text_for_embedding`: Đoạn văn tổng hợp (Title + Summary + Authors + Categories) dùng để tạo vector embedding.
  - [x] Loại bỏ bản ghi trùng lặp (`drop_duplicates` theo `paper_id`).
  - [x] Lọc bỏ các dòng chất lượng kém (summary quá ngắn < 30 từ hoặc null).
  - [x] Sắp xếp DataFrame theo ngày xuất bản giảm dần.
  - [x] Xuất DataFrame ra `data/clean/papers_clean.csv` và `data/clean/papers_clean.json`.

- [x] **2. Hoàn thành hàm `build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]` trong `testset.py`**
  - [x] Kiểm tra số lượng bản ghi tối thiểu ($\ge 5$).
  - [x] Chọn ngẫu nhiên/tiêu biểu các bài báo đại diện.
  - [x] Tạo bộ câu hỏi đa dạng phủ hợp 4 nhóm `question_type`:
    - `summary`: Câu hỏi về nội dung tóm tắt của bài báo.
    - `authors`: Câu hỏi về tác giả bài báo.
    - `date`: Câu hỏi về thời gian công bố.
    - `categories`: Câu hỏi về chủ đề / danh mục.
  - [x] Đảm bảo mỗi phần tử có đủ các trường: `id`, `question_type`, `question`, `ground_truth`, `ground_truth_doc_ids`.
  - [x] Lưu file JSON vào `data/eval/test_set.json`.

- [x] **3. Kiểm thử thành phần (Verification)**
  - Kiểm tra file `papers_clean.csv` có đầy đủ các cột và file `test_set.json` đúng format schema.

---

## 👤 Thành viên 3: Lê Văn Đông (Observability & Reporting)
**Phụ trách chính**: `src/observability/quality.py`, `src/observability/reporting.py`

- [x] **1. Hoàn thành `src/observability/quality.py`**
  - [x] **Hàm `run_data_quality_checks(df, settings, report_name)`**:
    - Kiểm tra tổng số dòng trong DataFrame ($>0$).
    - Kiểm tra cột `paper_id` không null và duy nhất (Unique).
    - Kiểm tra cột `title` không rỗng.
    - Kiểm tra độ dài summary đạt ngưỡng tối thiểu.
    - Kiểm tra độ tươi dữ liệu (`age_days <= settings.freshness_threshold_days`).
    - Lưu kết quả kiểm tra dạng JSON vào `data/quality/<report_name>.json`.
  - [x] **Hàm `build_freshness_report(df, settings, report_path)`**:
    - Xác định ngày mới nhất (`latest_published`) và cũ nhất (`oldest_published`).
    - Đếm số lượng dòng bị cũ/lạc hậu (`stale_rows`).
    - Tổng hợp trạng thái `is_fresh` (True/False).
    - Lưu báo cáo JSON vào `data/quality/freshness_report.json`.

- [x] **2. Hoàn thành `src/observability/reporting.py`**
  - [x] **Hàm `generate_phase1_report(...)`**:
    - Tổng hợp thông tin nguồn dữ liệu (Source Summary).
    - Thống kê kết quả đánh giá Baseline (Retrieval Hit Rate, Token F1, Judge Accuracy, Mean Judge Score).
    - Hiển thị kết quả Data Quality Checks và Freshness Status.
    - Xuất báo cáo định dạng Markdown tại `data/reports/phase1_report.md`.
  - [x] **Hàm `generate_corruption_report(...)`**:
    - Tạo bảng so sánh đối chiếu chi tiết 3 giai đoạn: **Baseline vs Corrupted vs Repaired**.
    - So sánh sự sụt giảm metrics khi dữ liệu bị lỗi và sự khôi phục khi được sửa chữa.
    - Đưa ra kết luận và bài học về tầm quan trọng của Data Observability.
    - Xuất báo cáo Markdown tại `data/reports/corruption_report.md`.

- [x] **3. Kiểm thử thành phần (Verification)**
  - Mở các file Markdown sinh ra và kiểm tra tính trực quan, chính xác của thông số.

---

## 👤 Thành viên 4: Đào Đức Mạnh (Data Corruption & Repair)
**Phụ trách chính**: `src/ingestion/corruption.py`

- [ ] **1. Hoàn thành hàm `corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame`**
  - [ ] Implement **Lỗi 1 (Drop Latest Records)**: Xóa $20-30\%$ số bài báo xuất bản gần nhất để mô phỏng mất mát dữ liệu mới.
  - [ ] Implement **Lỗi 2 (Blank Summary)**: Đặt rỗng summary cho $15\%$ số dòng.
  - [ ] Implement **Lỗi 3 (Text Noise Injection)**: Thêm từ vô nghĩa/nhiễu ký tự vào summary.
  - [ ] Implement **Lỗi 4 (Title Truncation)**: Cắt ngắn tiêu đề bài báo xuống còn 5-10 ký tự.
  - [ ] Implement **Lỗi 5 (Stale Published Date)**: Sửa ngày xuất bản thành năm 2000 để làm mất độ tươi.
  - [ ] Implement **Lỗi 6 (Add Duplicate Rows)**: Nhân đôi một số dòng dữ liệu.
  - [ ] Cập nhật lại cột `text_for_embedding` tương ứng với các biến đổi lỗi trên.
  - [ ] Ghi chi tiết các loại lỗi và số bản ghi bị tác động vào file log `data/results/corruption_log.json`.
  - [ ] Lưu DataFrame bị lỗi vào `data/clean/papers_clean_corrupted.csv` và `.json`.

- [ ] **2. Xây dựng logic Repair (Phục hồi dữ liệu)**
  - Quy định luồng Repair: Đọc lại file bản ghi gốc `data/raw/crossref_records.json`, chạy lại pipeline clean từ Thành viên 2 để khôi phục dữ liệu sạch hoàn chỉnh.
  - Xuất DataFrame đã sửa lỗi vào `data/clean/papers_clean_repaired.csv` và `.json`.

- [ ] **3. Kiểm thử thành phần (Verification)**
  - Kiểm tra file log `corruption_log.json` ghi nhận chính xác các kịch bản hỏng dữ liệu.

---

## 👤 Thành viên 5: Nguyễn Viết Huy (Integration & Pipeline Execution)
**Phụ trách chính**: `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`

- [ ] **1. Hoàn thành `main()` trong `src/pipelines/phase1.py` (Baseline Pipeline)**
  - [ ] Bước 1: Load cấu hình `load_settings()`.
  - [ ] Bước 2: Gọi `fetch_source_records` hoặc `load_raw_records` (từ Thành viên 1).
  - [ ] Bước 3: Gọi `build_clean_dataframe` và lưu dữ liệu sạch (từ Thành viên 2).
  - [ ] Bước 4: Tạo Vector Index trong ChromaDB với collection `papers-baseline` (dùng `src/retrieval/index.py`).
  - [ ] Bước 5: Tạo hoặc đọc bộ kiểm thử `build_test_set` (từ Thành viên 2).
  - [ ] Bước 6: Chạy đánh giá RAG agent với `evaluate_pipeline(...)` và lưu `baseline_metrics.json`.
  - [ ] Bước 7: Thực hiện Data Quality checks và Freshness report (từ Thành viên 3).
  - [ ] Bước 8: Tạo báo cáo Markdown `phase1_report.md` (từ Thành viên 3).

- [ ] **2. Hoàn thành `main()` trong `src/pipelines/corruption_flow.py` (Corruption & Repair Flow)**
  - [ ] Bước 1: Load baseline metrics và dữ liệu sạch.
  - [ ] Bước 2: Gọi `corrupt_clean_dataframe` và lưu dữ liệu lỗi (từ Thành viên 4).
  - [ ] Bước 3: Rebuild Vector Index ChromaDB cho dữ liệu lỗi với collection `papers-corrupted`.
  - [ ] Bước 4: Đánh giá RAG agent trên dữ liệu lỗi sử dụng cùng test set $\rightarrow$ lưu `corrupted_metrics.json`.
  - [ ] Bước 5: Chạy Quality & Freshness checks trên dữ liệu lỗi.
  - [ ] Bước 6: Thực hiện Repair dữ liệu từ bản ghi gốc thô.
  - [ ] Bước 7: Build Vector Index ChromaDB cho dữ liệu đã phục hồi với collection `papers-repaired`.
  - [ ] Bước 8: Đánh giá RAG agent trên dữ liệu đã phục hồi $\rightarrow$ lưu `repaired_metrics.json`.
  - [ ] Bước 9: Chạy Quality & Freshness checks trên dữ liệu phục hồi.
  - [ ] Bước 10: Sinh báo cáo so sánh tổng hợp `corruption_report.md` (từ Thành viên 3).

- [ ] **3. Kiểm thử toàn bộ hệ thống (End-to-End Verification)**
  - [ ] Chạy lệnh `python script/run_phase1.py` kiểm tra mã thoát = 0.
  - [ ] Chạy lệnh `python script/run_corruption_flow.py` kiểm tra mã thoát = 0.
  - [ ] Rà soát lại tất cả các file artifacts sinh ra trong thư mục `data/`.
