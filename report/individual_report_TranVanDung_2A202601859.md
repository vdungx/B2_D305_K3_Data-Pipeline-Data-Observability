# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Trần Văn Dũng             |
| MSSV               | 2A202601859                     |
| Khóa/Lớp         | K3              |
| Tên nhóm         | Nhóm B2     |
| Vai trò chính    | Thành viên 2: Data Cleaning & Test Set                 |
| Repository         | https://github.com/vdungx/B2_D305_K3_Data-Pipeline-Data-Observability.git |
| Ngày hoàn thành | 2026-08-06               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Data Cleaning      | `src/ingestion/cleaning.py`<br>(`build_clean_dataframe`) | `list[PaperRecord]` từ Ingestion (Quân - TV1) | `data/clean/papers_clean.csv`, `papers_clean.json` (24 bản ghi chuẩn hóa) | Hoàn thành |
| Frozen Test Set Builder | `src/evaluation/testset.py`<br>(`build_test_set`) | Cleaned `pd.DataFrame` từ `papers_clean.json` | `data/eval/test_set.json` (40 câu hỏi kiểm thử cố định 4 dạng Q&A) | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Định dạng Schema & Text for Embedding | Lê Văn Đông (TV 3) & Nguyễn Viết Huy (TV 5) | Đảm bảo các trường `text_for_embedding`, `authors_joined`, `categories_joined`, `age_days` có sẵn và nhất quán cho Observability Quality Checks và Vector Store Indexing. |
| Phục hồi dữ liệu (Repair Flow) | Đào Đức Mạnh (TV 4) | Cung cấp hàm `build_clean_dataframe` làm lõi cho quy trình Phục hồi dữ liệu (`repair_from_raw_records`) từ raw snapshots. |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Xây dựng pipeline làm sạch dữ liệu bài báo học thuật | `src/ingestion/cleaning.py` | Tạo `papers_clean.csv` và `papers_clean.json` (24 bản ghi sạch, bóc HTML tag, tính `age_days`, tạo `text_for_embedding`) | `python -c "from ingestion.cleaning import build_clean_dataframe"` |
| Tạo bộ câu hỏi kiểm thử cố định (Frozen Evaluation Set) | `src/evaluation/testset.py` | Tạo `data/eval/test_set.json` với 40 câu hỏi phủ hợp 4 dạng `summary`, `authors`, `date`, `categories` | `python -c "from evaluation.testset import build_test_set"` |

Output cụ thể phụ trách:
Đã hoàn thành 2 artifact dữ liệu cốt lõi: `data/clean/papers_clean.json` (24 bài báo học thuật đã bóc sạch XML/HTML, parse ngày ISO chuẩn và tính độ tươi dữ liệu) và `data/eval/test_set.json` (40 câu hỏi Q&A chuẩn hóa đóng vai trò làm Frozen Benchmark duy nhất cho toàn bộ hệ thống).

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Dữ liệu thô trích xuất từ Crossref REST API có độ nhiễu cao: chứa nhiều thẻ XML/HTML (như `<jats:p>`, `<b>`), ký tự mã hóa HTML Entities (`&amp;`, `&lt;`), danh sách tác giả bị lồng ghép (nested dicts), ngày xuất bản chưa chuẩn hóa và thiếu thông tin độ tươi (`age_days`). Nếu nạp trực tiếp dữ liệu thô này vào ChromaDB Vector Store, chất lượng embedding và khả năng trả lời của RAG Agent sẽ bị suy giảm nghiêm trọng.

### Cách triển khai

1. **Hàm `build_clean_dataframe` (`src/ingestion/cleaning.py`)**:
   - Sử dụng `html.unescape()` và Regex `re.sub(r"<[^>]+>", "", raw_text)` để bóc sạch toàn bộ thẻ HTML/XML và giải mã ký tự đặc biệt.
   - Chuẩn hóa danh sách tác giả và danh mục thành chuỗi phẳng cách nhau bởi dấu phẩy (`authors_joined`, `categories_joined`).
   - Parse ngày xuất bản về ISO `%Y-%m-%d` và tính `age_days = max(0, (run_date - published_date).days)` (đảm bảo không bị âm).
   - Tạo cột `text_for_embedding` theo cấu trúc: `Title: [title] | Authors: [authors] | Summary: [summary]`.
   - Lọc bỏ các dòng tóm tắt rác (`summary_chars < 100`) và drop trùng lặp theo `paper_id` & `title`.

2. **Hàm `build_test_set` (`src/evaluation/testset.py`)**:
   - Duyệt qua tập dữ liệu sạch `papers_clean.json`.
   - Tự động sinh ra 4 loại câu hỏi thực tế: `summary` (tóm tắt nội dung), `authors` (tác giả), `date` (ngày công bố), `categories` (chủ đề bài báo).
   - Đảm bảo mỗi mẫu tuân thủ đúng schema: `id`, `question_type`, `question`, `ground_truth`, `ground_truth_doc_ids`.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | `list[PaperRecord]` trích xuất từ Crossref REST API |
| Output                         | `data/clean/papers_clean.csv`, `papers_clean.json`, `data/eval/test_set.json` |
| Module phụ thuộc             | `src/ingestion/crossref.py` (Đàm Lê Minh Quân - TV 1) |
| Module sử dụng output        | `src/observability/quality.py` (TV 3), `src/ingestion/corruption.py` (TV 4), `src/pipelines/phase1.py` (TV 5) |
| Điều kiện lỗi cần xử lý | Trường `published` thiếu/lỗi định dạng date; `summary` rỗng hoặc bị bọc thẻ XML phức tạp `<jats:p>`; danh sách tác giả rỗng `[]`. |

### Cách xác minh

```bash
$env:PYTHONPATH="src"; $env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe -c "
from datetime import datetime
from core.config import load_settings
from ingestion.crossref import fetch_source_records
from ingestion.cleaning import build_clean_dataframe
from evaluation.testset import build_test_set

settings = load_settings()
records = fetch_source_records(settings)
df_clean = build_clean_dataframe(records, datetime.now())
print('Cleaned rows:', len(df_clean))
test_set = build_test_set(df_clean, settings.paths.eval_testset)
print('Test set count:', len(test_set))
"
```

- **Kết quả mong đợi:** Cleaned rows = 24 bài báo; Test set count = 40 câu hỏi Q&A.
- **Kết quả thực tế:** Cleaned rows = 24 bài báo; Test set count = 40 câu hỏi.
- **Artifact/log:** `data/clean/papers_clean.csv` và `data/eval/test_set.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần chọn cấu trúc chuỗi văn bản lưu trong cột `text_for_embedding` dùng làm đầu vào cho mô hình Vector Embedding `all-MiniLM-L6-v2`.
- **Các phương án đã cân nhắc:**
  1. *Phương án 1*: Chỉ sử dụng trường `summary` thuần túy làm `text_for_embedding`.
  2. *Phương án 2*: Ghép chuỗi hợp nhất cấu trúc `Title: [title] | Authors: [authors_joined] | Summary: [summary]`.
- **Phương án đã chọn:** Phương án 2 (Ghép chuỗi hợp nhất tiêu đề, tác giả và tóm tắt).
- **Lý do:** Giúp mô hình vector biểu diễn được cả mặt từ vựng tiêu đề và thông tin tác giả, giúp Retriever đáp ứng chính xác các câu hỏi thuộc nhóm `authors`, `title` lẫn `summary` mà không bị trượt context.
- **Bằng chứng quyết định phù hợp:** Chỉ số `retrieval_hit_rate` trên tập dữ liệu sạch pha Baseline đạt tuyệt đối `100.00%` cho cả 40 câu hỏi kiểm thử.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `ValueError: time data '2026' does not match format '%Y-%m-%d'` khi parse ngày xuất bản từ bản ghi Crossref API.
- **Lệnh hoặc bước tái hiện:** Thực thi `build_clean_dataframe` với một số bản ghi sách/bài báo chỉ trả về năm xuất bản `YYYY` (ví dụ `"2026"`) từ API Crossref.
- **Nguyên nhân gốc:** Hàm `datetime.strptime` cố định định dạng `%Y-%m-%d` dẫn đến báo lỗi khi gặp chuỗi ngày tháng chỉ có 4 chữ số năm.
- **Cách xử lý:** Thêm bộ xử lý linh hoạt thử lần lượt các format `%Y-%m-%d`, `%Y/%m/%d`, và `%Y` (mặc định lấy `-01-01` nếu chỉ có năm).
- **Cách xác minh sau khi sửa:** Chạy lại hàm làm sạch dữ liệu với 24 bản ghi thô $\rightarrow$ 100% bản ghi được parse ISO chuẩn xác mà không gặp ngoại lệ.
- **Điều học được:** Khâu Data Ingestion từ nguồn bên ngoài luôn chứa dữ liệu bất thường; hàm cleaning phải bọc an toàn nhiều kịch bản parsing.

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   Dữ liệu thô JSON từ Crossref API được `crossref.py` thu thập $\rightarrow$ `cleaning.py` bóc HTML, parse ISO date, tính `age_days` và tạo `text_for_embedding` $\rightarrow$ Lưu `papers_clean.csv` $\rightarrow$ `sentence-transformers/all-MiniLM-L6-v2` tạo vector embeddings $\rightarrow$ Lưu index vào ChromaDB collection `papers-baseline`.

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   Bộ 40 câu hỏi trong `test_set.json` chứa `ground_truth_doc_ids` (chứa `paper_id` đáp án chuẩn). Retriever gửi câu hỏi vào ChromaDB lấy $top\_k=4$ văn bản. Nếu `ground_truth_doc_ids` nằm trong $top\_k$ $\rightarrow$ `retrieval_hit_rate = 1`. LLM Generator đọc context sinh câu trả lời, so sánh từ vựng với `ground_truth` để tính Token F1 và được LLM Judge chấm điểm.

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - *Quality checks* (`quality.py`): Kiểm tra tính toàn vẹn và hợp lệ tại một thời điểm (Completeness: row count, null check; Uniqueness: trùng paper_id; Validity: summary length).
   - *Freshness monitoring*: Kiểm tra tính kịp thời theo trục thời gian (`age_days <= threshold=180` ngày) để cảnh báo dữ liệu bị lỗi thời (stale).

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   Để tạo ra một thước đo cố định duy nhất (Frozen Benchmark). Việc giữ nguyên test set giúp đảm bảo mọi biến động sụt giảm hay phục hồi của `retrieval_hit_rate` và `judge_score` đều bắt nguồn từ chất lượng dữ liệu thay vì do thay đổi độ khó của câu hỏi.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   Repair thành công khi: Báo cáo `data/quality/repaired.json` đạt `all_passed: true` (100% PASSED) và các chỉ số RAG trong `repaired_metrics.json` (`retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy`) phục hồi 100% về mức Baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |   100.00% |    40.00% |  100.00% | Giảm mạnh do rỗng summary và xóa bài mới; phục hồi tuyệt đối sau Repair |
| `mean_token_f1`      |   100.00% |    39.42% |  100.00% | F1 giảm sâu do context thiếu/nhiễu; khôi phục hoàn toàn sau Repair |
| `judge_accuracy`     |    90.00% |    40.00% |    90.00% | LLM Judge đánh giá sai lệch khi dữ liệu hỏng; phục hồi hoàn toàn sau Repair |
| `mean_judge_score`   | 4.70 / 5.0 | 2.68 / 5.0 | 4.70 / 5.0 | Điểm Judge sụt giảm nghiêm trọng; phục hồi tuyệt đối về 4.70/5.0 |
| `ragas_context_precision` | 100.00% | 40.00% | 100.00% | Độ chính xác ngữ cảnh giảm từ 100% xuống 40%, phục hồi tuyệt đối |
| `ragas_context_recall` | 100.00% | 40.00% | 100.00% | Độ bao phủ ngữ cảnh giảm khi bị drop bài mới, phục hồi 100% |
| `ragas_faithfulness` | 100.00% | 42.00% | 100.00% | Tính trung thực giảm do nhiễu text & rỗng tóm tắt, phục hồi 100% |
| `ragas_answer_relevancy` | 94.50% | 41.50% | 94.50% | Độ liên quan câu trả lời suy giảm nghiêm trọng ở Corrupted |
| Quality checks         | PASSED (All) | FAILED (3) | PASSED (All) | Kích hoạt đúng 3 cảnh báo Đỏ (unique, length, freshness) ở Corrupted |
| Freshness status       | FRESH | STALE | FRESH | Cảnh báo STALE chính xác khi ngày bị lùi về năm 2000 |

### Kết luận từ số liệu

1. `[Data Corruption: Blank summary & Drop latest records]` $\rightarrow$ `[Quality check FAILED & Freshness STALE]` $\rightarrow$ `[Retrieval Hit Rate giảm từ 100% xuống 40% & Judge Score giảm từ 4.70 xuống 2.68]`.
2. `[Repair Action: Phục hồi dữ liệu từ raw snapshot]` $\rightarrow$ `[Quality checks & Freshness PASSED (All)]` $\rightarrow$ `[Retrieval Hit Rate & Judge Score phục hồi 100% về mức Baseline]`.

**Corruption nào ảnh hưởng rõ nhất và vì sao?**
Kịch bản **Drop Latest Records** (Xóa 25% bài mới nhất) và **Blank Summary** (Làm rỗng phần tóm tắt) ảnh hưởng nặng nhất đến Retrieval. Lý do: xóa mất bản ghi khiến Vector DB hoàn toàn không có dữ liệu để tìm; còn làm rỗng summary khiến vector embedding bị mất sạch ngữ cảnh ngữ nghĩa.

**Kết quả nào khác với kỳ vọng ban đầu?**
Ban đầu dự đoán khi bị truncate tiêu đề thì Hit Rate sẽ chỉ giảm nhẹ, nhưng thực tế khi kết hợp nhiều kịch bản hỏng cùng lúc, `judge_accuracy` giảm rất sâu về 40%, chứng minh RAG Agent bị ảnh hưởng cực kỳ nhạy cảm trước chất lượng dữ liệu đầu vào.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về Data Pipeline**: Dữ liệu thô từ bên ngoài luôn cần quy trình cleaning chuẩn hóa nghiêm ngặt trước khi indexed vào Vector Database.
2. **Về Data Quality / Observability**: Thấy rõ tầm quan trọng của hệ thống giám sát tự động (Quality checks & Freshness) để phát hiện sớm các lỗi dữ liệu ngầm trước khi nó làm hỏng RAG Agent.
3. **Về ảnh hưởng của Data đến RAG Agent**: Chất lượng dữ liệu quyết định trực tiếp hiệu năng RAG ("Garbage In, Garbage Out"); phục hồi dữ liệu trực tiếp từ raw snapshot là cách giải quyết triệt để nhất.

### Nếu có thêm thời gian

Tích hợp thêm module **LLM Paraphraser** vào `src/evaluation/testset.py` để sinh ra các câu hỏi đa dạng, tự nhiên hơn thay vì dùng các mẫu template cố định.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Trần Văn Dũng  
**Ngày xác nhận:** 2026-08-06
