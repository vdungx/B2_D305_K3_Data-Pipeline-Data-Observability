# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Dũng |
| MSSV | TV2 |
| Khóa/Lớp | K3 |
| Tên nhóm | Nhóm 5 Thành Viên |
| Vai trò chính | Thành viên 2: Data Cleaning & Test Set |
| Repository | `B2_D305_K3_Data-Pipeline-Data-Observability` |
| Ngày hoàn thành | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Data Cleaning | `src/ingestion/cleaning.py` (`build_clean_dataframe`) | `list[PaperRecord]` từ Ingestion (Quân - TV1) | `data/clean/papers_clean.csv`, `papers_clean.json` | Hoàn thành |
| Frozen Test Set Builder | `src/evaluation/testset.py` (`build_test_set`) | Cleaned `pd.DataFrame` từ `papers_clean.json` | `data/eval/test_set.json` (40 Q&A benchmark samples) | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Định dạng Schema & Text for Embedding | Đông (TV 3) & Huy (TV 5) | Đảm bảo các trường `text_for_embedding`, `authors_joined`, `categories_joined`, `age_days` có sẵn và nhất quán cho Observability và Vector Store Indexing. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Xây dựng pipeline làm sạch dữ liệu bài báo học thuật | `src/ingestion/cleaning.py` | Tạo `papers_clean.csv` và `papers_clean.json` (24 bản ghi sạch, bóc HTML tag, tính `age_days`, tạo `text_for_embedding`) | `python -c "from ingestion.cleaning import build_clean_dataframe"` |
| Tạo bộ câu hỏi kiểm thử cố định (Frozen Evaluation Set) | `src/evaluation/testset.py` | Tạo `data/eval/test_set.json` với 40 câu hỏi phủ hợp 4 dạng `summary`, `authors`, `date`, `categories` | `python -c "from evaluation.testset import build_test_set"` |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Dữ liệu thô trích xuất từ Crossref REST API có độ nhiễu cao: chứa nhiều thẻ XML/HTML (như `<jats:p>`, `<b>`), danh sách tác giả bị lồng ghép (nested dicts), ngày xuất bản chưa chuẩn hóa và thiếu thông tin độ tươi (`age_days`). Nếu nạp trực tiếp dữ liệu thô này vào ChromaDB Vector Store, chất lượng embedding và khả năng trả lời của RAG Agent sẽ bị suy giảm nghiêm trọng.

### Cách triển khai
1. **Hàm `build_clean_dataframe` (`src/ingestion/cleaning.py`)**:
   - Sử dụng Regex `re.sub(r"<[^>]+>", "", raw_text)` để làm sạch toàn bộ các thẻ HTML/XML.
   - Chuẩn hóa danh sách tác giả và danh mục thành chuỗi phẳng cách nhau bởi dấu phẩy (`authors_joined`, `categories_joined`).
   - Parse ngày xuất bản về ISO `%Y-%m-%d` và tính `age_days = max(0, (run_date - published_date).days)`.
   - Tạo cột `text_for_embedding` theo cấu trúc: `Title: [title] | Authors: [authors] | Summary: [summary]`.
   - Lọc bỏ các dòng rác (`summary_chars < 100`) và drop trùng lặp theo `paper_id` & `title`.

2. **Hàm `build_test_set` (`src/evaluation/testset.py`)**:
   - Duyệt qua tập dữ liệu sạch `papers_clean.json`.
   - Tự động sinh ra 4 loại câu hỏi thực tế: `summary` (tóm tắt), `authors` (tác giả), `date` (ngày công bố), `categories` (chủ đề).
   - Đảm bảo mỗi mẫu tuân thủ đúng schema: `id`, `question_type`, `question`, `ground_truth`, `ground_truth_doc_ids`.

### Input, Output và Contract

| Thành phần | Mô tả |
| --- | --- |
| Input | `list[PaperRecord]` từ `src/ingestion/crossref.py` |
| Output | `data/clean/papers_clean.csv`, `papers_clean.json`, `data/eval/test_set.json` |
| Module phụ thuộc | `src/ingestion/crossref.py` (Quân - TV 1) |
| Module sử dụng output | `src/observability/quality.py` (Đông - TV 3), `src/ingestion/corruption.py` (Mạnh - TV 4), `src/pipelines/phase1.py` (Huy - TV 5) |

---

## 5. Xác minh (Verification)

```bash
$env:PYTHONPATH="src"; .\.venv\Scripts\python.exe -c "
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

- **Kết quả thực tế**:
  - `Cleaned rows`: 24 bài báo đạt chuẩn.
  - `Test set count`: 40 câu hỏi được tạo và lưu thành công tại `data/eval/test_set.json`.
