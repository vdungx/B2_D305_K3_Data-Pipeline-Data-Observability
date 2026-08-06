# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Đàm Lê Minh Quân |
| MSSV               | 2A202601451 |
| Khóa/Lớp         | K3 |
| Tên nhóm         | B2 |
| Vai trò chính    | Thành viên 1 — Source Ingestion |
| Repository         | https://github.com/vdungx/B2_D305_K3_Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Crossref payload parsing | `src/ingestion/crossref.py` → `parse_crossref_payload` | Raw JSON payload từ Crossref REST API (`payload["message"]["items"]`) | `list[PaperRecord]` đã chuẩn hóa (DOI, title, abstract sạch tag, authors, categories, published date ISO, URL) | Hoàn thành |
| Source fetching với retry | `src/ingestion/crossref.py` → `fetch_source_records` | `Settings` (`source_query`, `source_filter`, `max_results`) | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Hoàn thành |
| Raw snapshot loading | `src/ingestion/crossref.py` → `load_raw_records` | Đường dẫn file JSON snapshot | `list[PaperRecord]` để dùng lại cho cleaning/repair mà không cần gọi API | Hoàn thành |

Đây là phần việc sở hữu chính; các phần cleaning (`cleaning.py`), test set (`testset.py`), quality/reporting (`observability/`), corruption (`corruption.py`) và orchestration (`pipelines/`) do các thành viên 2–5 phụ trách, tôi chỉ dùng lại contract (`PaperRecord`, `data/raw/*.json`) mà mình bàn giao.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Resolve merge conflict trên `src/ingestion/crossref.py` sau khi pull bản hoàn chỉnh của bạn cùng nhóm (vdungx, commit `f80ece8`) | Thành viên 1/ingestion (đồng bộ với nhánh chung) | Giữ đúng bản đã được nhóm thống nhất, xóa toàn bộ conflict marker, kiểm tra lại bằng `ast.parse` |
| Khôi phục `data/raw/crossref_records.json`, `data/raw/crossref_response.json` sau khi lỡ commit đè bằng dữ liệu tự sinh cục bộ | Toàn bộ pipeline (mọi thành viên phụ thuộc raw snapshot này) | `git checkout dd502d7 -- data/raw/...` để trả lại đúng raw data nhóm đã commit trước đó |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Fetch + parse + lưu raw data từ Crossref | `fetch_source_records`, `parse_crossref_payload` | `data/raw/crossref_response.json` (raw payload), `data/raw/crossref_records.json` (24 `PaperRecord`) | Chạy trực tiếp hàm trong `uv run python`, kiểm tra số record, kiểm tra không còn thẻ HTML/XML trong `summary` |
| Load lại raw snapshot cho flow repair | `load_raw_records` | `list[PaperRecord]` giống hệt kết quả `fetch_source_records` (round-trip) | So sánh `loaded == records` sau khi đọc lại file JSON vừa ghi |
| Đồng bộ code với nhánh chung, khôi phục raw data đúng bản nhóm | `src/ingestion/crossref.py`, `data/raw/*.json` | Working tree khớp `HEAD` sau khi team tích hợp (commit `2517b8b`) | `git diff`, `git show HEAD:<file>` |

Output cụ thể: `data/raw/crossref_records.json` — 24 `PaperRecord` với DOI làm `paper_id` duy nhất, `summary` đã bỏ hết thẻ `<jats:p>`, là input trực tiếp cho `build_clean_dataframe` (Thành viên 2) và cho bước repair trong `corruption_flow.py` (Thành viên 4/5).

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Lấy dữ liệu bài báo học thuật liên quan RAG/LLM/agentic từ Crossref REST API (một nguồn công khai, có rate-limit) một cách ổn định, chuẩn hóa response JSON lồng nhau (có thể thiếu trường, có thẻ JATS trong abstract) thành một schema `PaperRecord` nhất quán, đồng thời lưu lại raw response gốc để cả nhóm có thể truy vết/tái tạo dữ liệu mà không cần gọi lại API mỗi lần chạy pipeline.

### Cách triển khai

- `fetch_source_records` dựng `params` từ `settings.source_query`, `settings.source_filter` (`from-pub-date:...,has-abstract:true`) và `settings.max_results`, gọi `GET https://api.crossref.org/works` kèm `User-Agent`. Nếu đã có raw response cũ và không bật `REFRESH_SOURCE`, đọc lại cache thay vì gọi API. Khi gặp `429`/`503`, retry tối đa 3 lần với backoff tuyến tính (`2 * (attempt+1)` giây); nếu request liên tục lỗi, fallback đọc lại raw response cũ đã lưu trước đó.
- `parse_crossref_payload` duyệt `message.items`, lấy `DOI` làm `paper_id`, phần tử đầu của `title` list, bỏ qua record thiếu `DOI` hoặc `title`. `abstract` được strip thẻ bằng regex `<[^>]+>` rồi chuẩn hóa khoảng trắng. `authors` ghép `given` + `family`. `categories` ưu tiên `subject`, fallback `container-title`, cuối cùng fallback nhãn mặc định nếu cả hai đều trống. Ngày xuất bản parse từ `date-parts` của `published-print` → `published-online` → `created` → `deposited`. `pdf_url` lấy từ phần tử trong `link` có `content-type == application/pdf`.
- `load_raw_records` đọc lại file JSON snapshot và unpack từng dict thành `PaperRecord`, đảm bảo cùng schema với record vừa fetch để các bước sau (cleaning, repair) dùng lại được mà không phụ thuộc vào việc gọi API lần nữa.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | `Settings` từ `core.config.load_settings()` (query, filter, max_results, đường dẫn `data/raw/`) |
| Output                         | `list[PaperRecord]` (11 trường: `paper_id`, `title`, `summary`, `authors`, `categories`, `primary_category`, `published`, `updated`, `abs_url`, `pdf_url`, `comment`) + 2 file JSON trong `data/raw/` |
| Module phụ thuộc             | `core.config`, `core.utils` (`read_json`, `write_json`, `normalize_whitespace`) |
| Module sử dụng output        | `ingestion.cleaning.build_clean_dataframe` (Thành viên 2), `pipelines.corruption_flow` (bước repair, Thành viên 4/5) |
| Điều kiện lỗi cần xử lý | Crossref trả `429`/`503` (rate limit/lỗi tạm thời), record thiếu `DOI` hoặc `title`, `abstract` rỗng hoặc chứa thẻ JATS |

### Cách xác minh

```bash
uv run python -c "
from core.config import load_settings
from ingestion.crossref import fetch_source_records, load_raw_records
settings = load_settings()
records = fetch_source_records(settings)
loaded = load_raw_records(settings.paths.raw_records_json)
assert loaded == records
"
```

- **Kết quả mong đợi:** Lấy được các bản ghi hợp lệ (có `paper_id`/`title`), lưu đúng 2 file trong `data/raw/`, `load_raw_records` đọc lại khớp 100% với dữ liệu vừa fetch.
- **Kết quả thực tế:** Lấy được 24 record, 0 record thiếu `paper_id`/`title`, 0 summary còn sót thẻ HTML/XML, round-trip qua `load_raw_records` khớp hoàn toàn.
- **Artifact/log:** `data/raw/crossref_response.json`, `data/raw/crossref_records.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần chọn chiến lược xử lý khi Crossref trả lỗi `429`/`503` hoặc lỗi mạng tạm thời trong lúc fetch.
- **Các phương án đã cân nhắc:**
  1. Raise exception ngay khi gặp lỗi, để pipeline dừng lại và người dùng tự chạy lại.
  2. Retry với backoff + cache raw response cũ, fallback đọc lại cache nếu tất cả lần retry đều thất bại.
- **Phương án đã chọn:** Phương án 2 (retry + cache + fallback).
- **Lý do:** Crossref là API công khai có rate-limit, và trong buổi lab nhiều thành viên có thể chạy `script/run_phase1.py`/`run_corruption_flow.py` liên tục, dễ bị `429`. Việc cache raw response giúp các lần chạy sau không cần gọi lại API (đỡ tốn quota, đỡ phụ thuộc mạng), còn fallback giúp pipeline không bị chặn hoàn toàn khi API lỗi tạm thời, đồng thời raw response luôn được lưu lại phục vụ audit và bước repair sau này.
- **Bằng chứng quyết định phù hợp:** Sau khi chạy lại pipeline nhiều lần trong buổi lab (kể cả sau khi bị conflict phải resolve lại code), `data/raw/` vẫn ổn định ở 24 record, không có lần chạy nào bị crash vì lỗi mạng/rate-limit.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Sau khi `git stash pop` để đồng bộ với bản `crossref.py` hoàn chỉnh mà bạn cùng nhóm (vdungx) đã push lên (commit `f80ece8`), file `src/ingestion/crossref.py` xuất hiện conflict marker ngay trong code (`<<<<<<< Updated upstream`, `=======`, `>>>>>>> Stashed changes`), khiến file không còn hợp lệ về cú pháp Python.
- **Lệnh hoặc bước tái hiện:** Có bản chỉnh sửa cục bộ (stash) đồng thời nhánh chung đã có commit mới sửa cùng file → `git stash pop` không tự merge được vì cả hai bên đều sửa trùng những dòng quan trọng (`parse_crossref_payload`, `fetch_source_records`).
- **Nguyên nhân gốc:** Hai bản triển khai độc lập của cùng một hàm (một bản tôi tự viết cục bộ, một bản của vdungx đã được đồng đội hoàn thiện và push trước) đụng nhau trên cùng vùng code; ngoài ra một lần chạy thử `fetch_source_records` cục bộ trước đó đã lỡ bị commit ("hello") đè lên `data/raw/crossref_records.json` và `crossref_response.json` — là dữ liệu raw gốc mà cả nhóm đang dùng chung (commit `dd502d7`).
- **Cách xử lý:** Đọc từng khối conflict, xác nhận giữ nguyên phần `Updated upstream` (bản của vdungx, khớp lịch sử commit `f80ece8`), xóa toàn bộ phần `Stashed changes` và các marker; sau đó chạy `git checkout dd502d7 -- data/raw/crossref_records.json data/raw/crossref_response.json` để khôi phục đúng raw data nhóm đã commit, thay vì giữ bản do tôi tự generate.
- **Cách xác minh sau khi sửa:** `ast.parse()` để đảm bảo file hợp lệ về cú pháp; `git status`/`git diff` không còn marker `<<<<<<<`; chạy lại `fetch_source_records`/`load_raw_records` để đảm bảo hàm vẫn hoạt động đúng sau khi resolve.
- **Điều học được:** Khi nhiều người cùng động vào một file "nóng" như `crossref.py` (module nền tảng mà ai cũng phụ thuộc), cần `git pull`/đồng bộ thường xuyên trước khi tự ý sửa để tránh conflict lan ra cả code lẫn data artifact; đồng thời không nên chạy thử nghiệm sinh artifact rồi commit vội mà không kiểm tra `git status` trước, vì rất dễ ghi đè dữ liệu chung của cả nhóm.

## 7. Hiểu biết về luồng end-to-end

**Câu trả lời:**

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?** `fetch_source_records` gọi Crossref API và lưu raw response + `list[PaperRecord]` vào `data/raw/`. `build_clean_dataframe` (Thành viên 2) chuẩn hóa các trường này, tính `age_days`, tạo `text_for_embedding` (gộp title + summary + authors + categories), lọc bỏ record kém chất lượng/trùng lặp rồi xuất ra `data/clean/papers_clean.csv|json`. `LocalEmbeddingIndex.build` (trong `src/pipelines/phase1.py`) dùng `text_for_embedding` để tạo embedding bằng `sentence-transformers/all-MiniLM-L6-v2` và nạp vào collection ChromaDB (`papers-baseline`/`papers-corrupted`/`papers-repaired`).
2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?** `build_test_set` (Thành viên 2) tạo câu hỏi từ 4 nhóm (`summary`, `authors`, `date`, `categories`) trên các bài báo mẫu, mỗi câu hỏi gắn `ground_truth` và `ground_truth_doc_ids` (chính `paper_id` của bài báo nguồn). Khi evaluate, `retrieval_hit_rate` kiểm tra xem `paper_id` đúng có nằm trong top-k kết quả retrieval hay không, còn `mean_token_f1`/`judge_accuracy`/`mean_judge_score` so sánh câu trả lời của agent với `ground_truth`.
3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?** `run_data_quality_checks` kiểm tra tính toàn vẹn/hợp lệ của schema tại một thời điểm (số dòng > 0, `paper_id` không null và duy nhất, `title` không rỗng, độ dài `summary` đạt ngưỡng) — trả về `all_passed` True/False. `build_freshness_report` chỉ tập trung vào khía cạnh thời gian: ngày xuất bản mới nhất/cũ nhất, số dòng vượt ngưỡng `freshness_threshold_days` (`stale_rows`), và trạng thái `is_fresh`. Một dataset có thể "quality PASSED" nhưng vẫn "not fresh" nếu dữ liệu quá cũ, và ngược lại.
4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?** Để cô lập biến duy nhất là chất lượng dữ liệu index — nếu đổi câu hỏi giữa các lần đánh giá thì không thể kết luận sự thay đổi metric là do corruption/repair hay do độ khó câu hỏi khác nhau. Dùng chung `data/eval/test_set.json` cho cả 3 lần `evaluate_pipeline` giúp so sánh baseline vs corrupted vs repaired là "apples-to-apples".
5. **Repair được xem là thành công dựa trên artifact và metric nào?** Dựa trên việc `repaired_metrics.json` (retrieval hit rate, token F1, judge accuracy, mean judge score) quay trở lại gần mức `baseline_metrics.json`, đồng thời `data/quality/repaired.json` có `all_passed: true` và `data/quality/freshness_repaired.json` có `is_fresh: true` — tức là cả điểm số agent lẫn tín hiệu observability đều phục hồi, không chỉ riêng một phía.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |   100.00% |    40.00% |   100.00% | Corruption (đặc biệt drop-latest + blank summary) làm mất hoàn toàn ngữ cảnh của nhiều bài, khiến retrieval trật mục tiêu hơn một nửa số câu hỏi. |
| `mean_token_f1`      |   100.00% |    39.42% |   100.00% | Giảm gần tương ứng với hit rate — khi retrieval sai tài liệu, câu trả lời tất yếu lệch khỏi ground truth. |
| `judge_accuracy`     |   100.00% |    40.00% |    97.50% | Repaired gần như phục hồi hoàn toàn; chênh lệch nhỏ (2.5%) có thể do tính ngẫu nhiên của LLM judge, không phải lỗi dữ liệu. |
| `mean_judge_score`   |   5.00/5 |   2.68/5 |    4.95/5 | Cùng xu hướng với judge accuracy, cho thấy chất lượng câu trả lời (không chỉ đúng/sai nhị phân) cũng bị ảnh hưởng rõ. |
| Quality checks         | PASSED (6/6) | FAILED (duplicate `paper_id`, 4 summary quá ngắn, 3 bản ghi stale) | PASSED (6/6) | Quality check bắt đúng 3/6 lỗi mà Thành viên 4 chèn vào (duplicate rows, blank/noisy summary, stale date). |
| Freshness status       | FRESH (0/24 stale) | STALE (3/20 stale, oldest = 2000-01-01) | FRESH (0/24 stale) | Lỗi "stale published date" (sửa về năm 2000) được freshness report phát hiện chính xác. |

### Kết luận từ số liệu

1. **Data corruption** (drop-latest, blank/noisy summary, title truncation) → **quality/freshness signal thay đổi** (`data/quality/corrupted.json`: `all_passed=false`; `freshness_corrupted.json`: `is_fresh=false`, 3 stale rows) → **agent metric thay đổi** (`retrieval_hit_rate` rơi từ 100% xuống 40%, `mean_judge_score` từ 5.00 xuống 2.68).
2. **Repair action** (đọc lại `data/raw/crossref_records.json` gốc, chạy lại `build_clean_dataframe`) → **quality/freshness signal phục hồi** (`repaired.json`: `all_passed=true`; `freshness_repaired.json`: `is_fresh=true`, 0 stale) → **agent metric phục hồi gần như hoàn toàn** (`retrieval_hit_rate`/`mean_token_f1` về đúng 100%, `judge_accuracy` 97.5%, `mean_judge_score` 4.95/5).

Corruption ảnh hưởng rõ nhất là tổ hợp **drop-latest-records + blank-summary**: xóa hẳn bài mới nhất và làm rỗng summary của một số bài khiến agent hoàn toàn không có ngữ cảnh để trả lời đúng cho các câu hỏi liên quan (`ground_truth_doc_ids` trỏ tới bài đã bị xóa hoặc mất summary), kéo `retrieval_hit_rate` giảm mạnh hơn hẳn so với lỗi "cosmetic" như title truncation.

Kết quả hơi khác kỳ vọng ban đầu: tôi kỳ vọng repair sẽ đưa mọi metric về đúng 100% như baseline, nhưng `judge_accuracy` repaired chỉ đạt 97.5% (không phải 100%) dù dữ liệu đã sạch hoàn toàn và giống hệt baseline. Đã kiểm tra `repaired_clean_csv`/`json` và xác nhận dữ liệu khớp 100% với `papers_clean.csv` gốc, nên kết luận chênh lệch 2.5% này đến từ tính không xác định (non-determinism) của LLM judge khi chấm điểm câu trả lời tự sinh, chứ không phải lỗi trong bước repair.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Một pipeline dữ liệu tốt phải giữ lại raw snapshot (`data/raw/`) — đây là điều kiện tiên quyết để "repair" có ý nghĩa; nếu không có raw gốc, corruption sẽ là vĩnh viễn.
2. Data quality checks và freshness monitoring là hai lớp giám sát bổ sung cho nhau (schema-integrity vs time-based), cần cả hai mới phát hiện đủ loại lỗi dữ liệu thực tế (ví dụ freshness không bắt được duplicate rows, quality check không bắt được ngày tháng cũ).
3. Chất lượng dữ liệu đầu vào ảnh hưởng trực tiếp và có thể đo lường được lên chất lượng RAG agent (retrieval hit rate giảm 60 điểm %, judge score giảm gần một nửa) — đây không phải suy luận định tính mà là con số cụ thể, chứng minh giá trị của observability.

### Nếu có thêm thời gian

Tôi sẽ thêm retry theo `Retry-After` header (thay vì backoff cố định) và giới hạn tổng thời gian chờ cho `fetch_source_records`, để tránh trường hợp Crossref rate-limit kéo dài làm pipeline treo lâu; đo cải thiện bằng cách giả lập chuỗi response `429` liên tiếp và so sánh tổng thời gian chạy trước/sau thay đổi.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đàm Lê Minh Quân
**Ngày xác nhận:** 2026-08-06
