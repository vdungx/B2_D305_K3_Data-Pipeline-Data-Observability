# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Đào Đức Mạnh |
| MSSV | 2A202601833 |
| Khóa/Lớp | Khóa 3 / D305 |
| Tên nhóm | B2 |
| Vai trò chính | Data Corruption & Repair |
| Repository | `B2_D305_K3_Data-Pipeline-Data-Observability` |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

Tôi phụ trách mô phỏng các lỗi dữ liệu có chủ đích để kiểm tra khả năng phát hiện và phục hồi của pipeline RAG. Phần tích hợp orchestration, đánh giá và tạo báo cáo so sánh do Thành viên 5 thực hiện; pipeline đó sử dụng trực tiếp output corruption của tôi.

| Module/deliverable | File/hàm phụ trách | Input | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Data corruption | `src/ingestion/corruption.py` — `corrupt_clean_dataframe` | Clean DataFrame | Corrupted DataFrame và `data/results/corruption_log.json` | Hoàn thành |
| Repair helper | `src/ingestion/corruption.py` — `repair_from_raw_records` | Raw records snapshot, ngày chạy | Repaired DataFrame, CSV và JSON | Hoàn thành |
| Public API | `src/ingestion/__init__.py` | Hàm repair | Import dùng cho pipeline | Hoàn thành |

Hỗ trợ tích hợp: kiểm tra contract giữa output corruption và `src/pipelines/corruption_flow.py`: pipeline ghi dataset corrupted, tạo index `papers-corrupted`, chạy quality/freshness checks; repair được xây dựng lại từ `data/raw/crossref_records.json`.

## 3. Kết quả theo vai trò

| Nhiệm vụ | File/hàm/artifact | Kết quả | Cách xác minh |
| --- | --- | --- | --- |
| Xóa bản ghi mới nhất | `corrupt_clean_dataframe`; `corruption_log.json` | Xóa 6/24 bản ghi (25%) | Log có `drop_latest_records.affected_count = 6` |
| Làm hỏng nội dung và metadata | Cùng hàm trên | 3 summary rỗng, 2 summary nhiễu, 3 title bị cắt, 3 ngày xuất bản bị đổi về 2000-01-01 | Log và dataset corrupted |
| Tạo duplicate | Cùng hàm trên | Thêm 2 dòng trùng, tổng dataset sau corruption là 20 dòng | `duplicate_paper_id_count = 2` |
| Phục hồi từ raw snapshot | `repair_from_raw_records` | Tái tạo 24 dòng cleaned, không trùng, không stale | `papers_clean_repaired.csv/json`, `quality/repaired.json` |

Artifact quan trọng là [`data/results/corruption_log.json`](../data/results/corruption_log.json). File này lưu seed-independent record IDs và số lượng bị tác động cho từng scenario, giúp truy vết chính xác nguyên nhân của các cảnh báo observability.

## 4. Giải thích kỹ thuật

### Vấn đề cần giải quyết

Pipeline RAG có thể vẫn chạy dù dữ liệu bị mất, rỗng, trùng hoặc cũ. Vì vậy cần tạo lỗi có kiểm soát để chứng minh hai điểm: quality/freshness checks nhận diện được dữ liệu xấu và chất lượng retrieval/answer thực sự suy giảm.

### Cách triển khai

`corrupt_clean_dataframe` tạo bản sao sâu của baseline DataFrame để không làm thay đổi baseline. Hàm cố định random state để cùng input luôn tạo cùng một corruption set, giúp so sánh metrics có thể tái lập. Sáu scenario được áp dụng như sau:

1. Sắp xếp `published` giảm dần, loại 25% bản ghi mới nhất.
2. Làm rỗng 15% `summary`.
3. Chèn token vô nghĩa vào summary khác với nhóm rỗng.
4. Cắt title còn 8 ký tự, nằm trong ngưỡng yêu cầu 5–10 ký tự.
5. Đổi một nhóm `published` thành `2000-01-01` và tính lại `age_days` để freshness check phát hiện được.
6. Nối thêm 10% dòng đã biến đổi để tạo duplicate `paper_id`.

Sau các thay đổi, hàm tính lại `summary_chars` và `text_for_embedding`; do đó embedding index phản ánh đúng dữ liệu hỏng thay vì dùng text helper cũ. Log được ghi bằng `write_json` và gồm fraction, số dòng, `paper_id` bị ảnh hưởng, số dòng cuối cùng và số duplicate.

Repair không chỉnh sửa từng trường trên dataset hỏng. `repair_from_raw_records` đọc snapshot raw, gọi `load_raw_records` và `build_clean_dataframe`, rồi ghi CSV/JSON. Cách này đồng thời phục hồi các dòng bị drop và tất cả trường bị sửa sai.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input corruption | DataFrame cleaned có `paper_id`, `title`, `summary`, `published`; dùng thêm `authors_joined`, `age_days` nếu có |
| Output corruption | DataFrame corrupted cùng schema, `text_for_embedding` và trường dẫn xuất đã cập nhật; JSON log |
| Input repair | `data/raw/crossref_records.json`, `run_date`, output CSV/JSON paths |
| Output repair | Cleaned DataFrame được tái tạo từ raw, `papers_clean_repaired.csv/json` |
| Module phụ thuộc | `core.utils`, `ingestion.crossref`, `ingestion.cleaning` |
| Module sử dụng output | `pipelines/corruption_flow.py`, retrieval index, evaluation và observability |
| Điều kiện lỗi | Thiếu một trong `paper_id`, `title`, `summary`, `published` thì ném `ValueError` thay vì tạo dữ liệu không hợp lệ |

### Cách xác minh

```bash
uv run python script/run_phase1.py
uv run python script/run_corruption_flow.py
```

Kết quả thực tế của corruption flow: dataset baseline 24 dòng trở thành 20 dòng corrupted; quality checks failed, freshness stale; repair khôi phục 24 dòng. Artifacts: `data/clean/papers_clean_corrupted.csv`, `data/clean/papers_clean_repaired.csv`, `data/results/corruption_log.json`.

## 5. Quyết định kỹ thuật quan trọng

- **Bối cảnh:** Có thể repair bằng cách vá trực tiếp DataFrame corrupted hoặc rebuild từ raw snapshot.
- **Các phương án:** (1) vá từng summary/title/date và xóa duplicate; (2) đọc raw snapshot rồi clean lại toàn bộ.
- **Phương án chọn:** Rebuild từ raw snapshot.
- **Lý do:** Repair theo raw khôi phục cả bản ghi mới bị drop, không cần đoán giá trị ban đầu, và tạo cùng schema/logic cleaning như baseline. Đây là cách có tính audit và reproducibility cao hơn.
- **Bằng chứng:** repaired có 24 dòng, quality `all_passed = true`, freshness `is_fresh = true`, retrieval hit rate và token F1 đều quay lại 1.00.

## 6. Một lỗi/blocker đã xử lý

- **Triệu chứng:** Sau khi thêm duplicate, số summary rỗng quan sát trong quality report là 4 thay vì 3 lần thao tác blank summary.
- **Nguyên nhân gốc:** Một trong hai dòng được duplicate thuộc nhóm summary đã bị làm rỗng; quality check đếm trên dataset cuối cùng nên tính cả bản sao.
- **Cách xử lý:** Log tách rõ `blank_summary.affected_count = 3` khỏi `add_duplicate_rows.affected_count = 2`; kiểm thử dùng điều kiện “ít nhất 3 summary rỗng” trên output cuối.
- **Xác minh:** `data/quality/corrupted.json` báo 4 summary ngắn, đồng thời `corruption_log.json` truy được 3 tác động blank ban đầu và 2 duplicate.
- **Điều học được:** Cần phân biệt số record trực tiếp bị thao tác với số violation quan sát sau khi các scenario chồng lấp.

## 7. Hiểu biết về luồng end-to-end

1. Crossref API được lưu thành raw response/records, sau đó cleaning chuẩn hóa thành DataFrame có `text_for_embedding`; embedding MiniLM nạp text này vào ChromaDB.
2. Test set chứa câu hỏi, ground truth và `ground_truth_doc_ids`. Retrieval hit rate đo khả năng lấy đúng document; token F1 và LLM judge đánh giá câu trả lời so với ground truth.
3. Quality checks kiểm tra tính hợp lệ/cấu trúc như unique ID, summary đủ dài; freshness monitoring tập trung vào tuổi dữ liệu, ngày mới nhất/cũ nhất và số dòng stale.
4. Dùng cùng test set cho ba trạng thái giúp metrics chỉ phản ánh tác động của dữ liệu/index, không bị nhiễu bởi tập câu hỏi khác nhau.
5. Repair thành công khi artifacts repaired được tạo từ raw, checks và freshness trở lại pass/fresh, đồng thời metrics phục hồi gần baseline.

## 8. Phân tích kết quả

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.4000 | 1.0000 | Giảm 60 điểm phần trăm, phục hồi hoàn toàn |
| `mean_token_f1` | 1.0000 | 0.3942 | 1.0000 | Giảm 60.58 điểm phần trăm, phục hồi hoàn toàn |
| `judge_accuracy` | 1.0000 | 0.4000 | 0.9750 | Repair phục hồi gần hoàn toàn; còn chênh 1/40 mẫu |
| `mean_judge_score` | 5.0000 | 2.6750 | 4.9500 | Giảm mạnh khi corrupted, phục hồi gần baseline |
| Quality checks | PASS | FAIL | PASS | Corrupted lỗi unique ID, summary length và freshness |
| Freshness status | FRESH | STALE | FRESH | Corrupted có 3 stale rows |

Chuỗi bằng chứng thứ nhất: corruption (mất 6 record mới, blank/noise/truncated text, stale date, duplicate) → quality failed và freshness stale → retrieval hit rate giảm từ 1.00 xuống 0.40, token F1 giảm xuống 0.3942.

Chuỗi bằng chứng thứ hai: rebuild cleaned data từ raw snapshot → 24 dòng hợp lệ, unique, fresh → retrieval hit rate và token F1 quay lại 1.00; judge accuracy 0.975 và judge score 4.95, gần baseline.

Lỗi ảnh hưởng rõ nhất là tổ hợp drop latest records và blank summary vì vừa làm mất hẳn document cần truy xuất, vừa xóa ngữ cảnh semantic. Các scenario khác đảm bảo quality/freshness monitoring cũng phát hiện lỗi. Việc judge accuracy không quay lại 1.00 có thể do đánh giá LLM/judge trên một mẫu; metric retrieval và token F1 đã phục hồi hoàn toàn nên không kết luận repair bị lỗi chỉ từ chênh lệch 1 mẫu.

## 9. Điều học được và hướng cải thiện

1. Raw snapshot là artifact thiết yếu: nó cho phép rollback/rebuild mà không cần gọi lại API và không phụ thuộc dữ liệu hỏng.
2. Quality và freshness cần được đo riêng: dataset có thể còn dòng và có schema hợp lệ nhưng vẫn stale hoặc có summary vô dụng.
3. Đánh giá RAG phải gắn với dữ liệu: metrics giảm rõ sau corruption, nên observability không chỉ là kiểm tra kỹ thuật mà ảnh hưởng trực tiếp đến trải nghiệm agent.

Nếu có thêm thời gian, tôi sẽ bổ sung unit tests tham số hóa cho từng scenario, bao gồm dataset nhỏ, giá trị `published` không parse được và xác minh log/derived columns. Cải thiện sẽ được đo bằng coverage các scenario và tính ổn định của output với cùng random seed.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần Data Corruption & Repair tôi phụ trách.
- [x] Các kết luận metrics đều trỏ đến artifact trong `data/`.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo không sao chép báo cáo chung; nội dung tập trung vào module corruption/repair.

**Họ và tên:** Đào Đức Mạnh
**Ngày xác nhận:** 2026-08-06
