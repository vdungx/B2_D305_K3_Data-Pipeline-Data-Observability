# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                                                        |
| ------------------ | --------------------------------------------------------------- |
| Họ và tên       | Lê Văn Đông                                                            |
| MSSV               | 2A202601851                                                         |
| Khóa/Lớp         | K3                                                              |
| Tên nhóm         | B2                                              |
| Vai trò chính    | Thành viên 3: Observability & Reporting                        |
| Repository         | `B2_D305_K3_Data-Pipeline-Data-Observability`                   |
| Ngày hoàn thành | 2026-08-06                                                      |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Data Quality Checks | `src/observability/quality.py` (`run_data_quality_checks`) | `pd.DataFrame` sau khi được làm sạch | `data/quality/<report_name>.json` | Hoàn thành |
| Freshness Monitoring | `src/observability/quality.py` (`build_freshness_report`) | `pd.DataFrame` dữ liệu | `data/quality/freshness_report.json` | Hoàn thành |
| Baseline Report Generator | `src/observability/reporting.py` (`generate_phase1_report`) | Source metadata, metrics, quality, freshness | `data/reports/phase1_report.md` | Hoàn thành |
| Corruption Comparison | `src/observability/reporting.py` (`generate_corruption_report`) | Metrics, quality, freshness từ 3 pha | `data/reports/corruption_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Tích hợp luồng pipeline & debug | Huy (TV 5 - Integration) | Tích hợp thành công các bước kiểm tra chất lượng và xuất báo cáo vào luồng chạy tự động `run_phase1.py` và `run_corruption_flow.py`. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Xây dựng hệ thống kiểm tra chất lượng dữ liệu tự động | `src/observability/quality.py` | Quét tính duy nhất, rỗng, độ dài tóm tắt và độ tươi của dữ liệu, lưu kết quả JSON | Chạy script kiểm thử cục bộ `python script/test_observability.py` |
| Triển khai các báo cáo Markdown trực quan | `src/observability/reporting.py` | Tạo báo cáo chi tiết pha Baseline và báo cáo so sánh Baseline vs Corrupted vs Repaired | Mở các file báo cáo Markdown sinh ra trong `data/reports/` |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Dữ liệu học thuật sau khi làm sạch có thể vẫn chứa các vấn đề tiềm ẩn: các tóm tắt (summary) quá ngắn không đủ thông tin ngữ nghĩa, bài viết bị trùng lặp do lỗi API, dữ liệu cũ/lỗi thời (stale), hoặc bị mất mát thông tin trong các pha chuyển đổi dữ liệu. Nếu nạp trực tiếp dữ liệu không đạt chuẩn này vào ChromaDB, RAG Agent sẽ hoạt động kém hiệu quả. Hơn thế nữa, đội ngũ vận hành cần có các công cụ báo cáo trực quan để đánh giá tác động của dữ liệu lỗi tới hiệu năng của Agent.

### Cách triển khai
1. **Kiểm tra chất lượng dữ liệu (`quality.py`)**:
   - Sử dụng Pandas quét DataFrame để phát hiện các dòng trống, kiểm tra xem `paper_id` có trùng lặp không (`is_unique`), đếm số lượng tóm tắt dưới 30 từ, và đếm số bài báo có tuổi ngày (`age_days`) vượt quá giới hạn 180 ngày.
   - Ghi toàn bộ kết quả vào tệp tin JSON cấu trúc để làm cơ sở dữ liệu giám sát.
2. **Xuất báo cáo Markdown (`reporting.py`)**:
   - Tự động sinh báo cáo Markdown có cấu trúc rõ ràng. Định dạng kết quả kiểm định chất lượng bằng các huy hiệu trực quan màu sắc (`🟢 PASSED` và `🔴 FAILED`) để người vận hành dễ dàng nhận biết trạng thái lỗi.
   - Biên soạn sẵn các phần phân tích chuyên sâu về lý do suy giảm hiệu năng của RAG Agent khi dữ liệu bị nhiễu hoặc mất mát và các bài học thiết kế hệ thống.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | `pd.DataFrame` và các dictionary chứa metrics đánh giá RAG |
| Output                         | Các tệp tin JSON và báo cáo định dạng Markdown chứa bảng đối chiếu |
| Module phụ thuộc             | `src/ingestion/cleaning.py` (Dũng - TV 2), `src/evaluation/metrics.py` (Huy - TV 5) |
| Module sử dụng output        | `src/pipelines/phase1.py` & `src/pipelines/corruption_flow.py` (Huy - TV 5) |
| Điều kiện lỗi cần xử lý | Trường hợp thiếu các cột quan trọng (`paper_id`, `title`, `summary`, `age_days`) trong DataFrame, hệ thống sẽ báo lỗi cụ thể và đánh dấu thất bại thay vì crash chương trình. |

### Cách xác minh

```bash
python script/test_observability.py
```

- **Kết quả mong đợi:** Script chạy thành công không có lỗi cú pháp, in ra kết quả kiểm định đúng/sai của mock data và xuất các file báo cáo thử nghiệm trong `data/reports/`.
- **Kết quả thực tế:**
  - `Clean quality all_passed: True`
  - `Corrupted quality all_passed: False`
  - Đã sinh các file báo cáo mẫu: `test_phase1_report.md` và `test_corruption_report.md`.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn phương pháp kiểm định chất lượng dữ liệu giữa việc tích hợp một thư viện lớn (như Great Expectations) và việc tự viết các custom assertions bằng Python/Pandas.
- **Các phương án đã cân nhắc:**
  1. *Phương án 1:* Tích hợp và cấu hình Great Expectations (GX) để kiểm tra chất lượng dữ liệu.
  2. *Phương án 2:* Viết bộ quy tắc kiểm định chất lượng tùy biến (custom check assertions) trực tiếp bằng Python và Pandas.
- **Phương án đã chọn:** Phương án 2 (Tự viết bộ quy tắc kiểm định bằng Pandas).
- **Lý do:**
  - Tiết kiệm tài nguyên và tối ưu tốc độ chạy của pipeline (Great Expectations khởi động khá nặng).
  - Tương thích tốt với môi trường cài đặt (nhất là khi máy của học viên chạy các phiên bản Python đặc biệt gây lỗi dependency với GX).
  - Dễ dàng kiểm soát cấu trúc JSON đầu ra để tích hợp linh hoạt và hiển thị bảng Markdown có định dạng tùy biến đẹp mắt.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  `ERROR: Could not find a version that satisfies the requirement great-expectations>=1.16.1`
- **Lệnh hoặc bước tái hiện:** Chạy lệnh `pip install -r requirements.txt` trong môi trường ảo `.venv` sử dụng Python 3.14.6.
- **Nguyên nhân gốc:** Thư viện `great-expectations` có ràng buộc cứng yêu cầu phiên bản Python `<3.14`. Do môi trường của máy chạy phiên bản Python 3.14.6 nên trình quản lý gói `pip` chặn không cho cài đặt.
- **Cách xử lý:** Thay vì cài đặt dependencies trực tiếp qua pip hệ thống, chúng tôi cài đặt trình quản lý gói `uv` toàn cục thông qua lệnh:
  `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
  Sau đó sử dụng `uv sync` để `uv` tự động nhận diện `pyproject.toml`, tự động tải phiên bản Python tương thích (3.13) xuống dưới nền và thiết lập môi trường ảo chuẩn mà không cần can thiệp hệ thống.
- **Cách xác minh sau khi sửa:** Chạy `uv run python script/test_observability.py` thành công trơn tru.
- **Điều học được:** Trình quản lý gói hiện đại như `uv` giúp giải quyết triệt để các xung đột phiên bản Python và cải thiện tính tái lập (reproducibility) của dự án.

---

## 7. Hiêu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   Dữ liệu thô ban đầu được gọi từ Crossref API, sau đó lưu lại dưới dạng file JSON thô (raw snapshot). Dữ liệu này được đọc lên bởi module cleaning để chuẩn hóa định dạng văn bản, lọc bỏ bài báo kém chất lượng, loại bỏ trùng lặp và tính độ tươi dữ liệu. Cột dữ liệu tổng hợp `text_for_embedding` sau đó được tạo vector hóa (embedding) thông qua mô hình MiniLM và nạp trực tiếp vào các collection tương ứng trong ChromaDB.

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   Khi RAG Agent nhận câu hỏi từ bộ kiểm thử (Evaluation Set), nó thực hiện truy vấn vector để lấy các tài liệu liên quan.
   - Để đo **retrieval quality (chất lượng tìm kiếm)**: Hệ thống so sánh danh sách ID tài liệu truy xuất được với `ground_truth_doc_ids` (nếu trùng khớp ít nhất một ID thì đạt điểm hit).
   - Để đo **answer quality (chất lượng câu trả lời)**: Hệ thống so sánh câu trả lời của Agent với `ground_truth` thông qua chỉ số Token F1 và thông qua LLM Judge chấm điểm từ 1 đến 5 để đánh giá độ chính xác thực tế.

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - **Quality checks (Kiểm tra chất lượng)**: Tập trung vào tính toàn vẹn của dữ liệu tại thời điểm chạy (như số lượng dòng có rỗng không, ID có duy nhất không, tiêu đề có thiếu không, độ dài tóm tắt đạt chuẩn không).
   - **Freshness monitoring (Giám sát độ tươi)**: Tập trung vào khía cạnh thời gian của dữ liệu (ngày xuất bản mới nhất/cũ nhất, số lượng bản ghi bị cũ thời so với ngày chạy hiện tại).

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   Việc sử dụng chung một bộ test set cố định (Frozen Test Set) đóng vai trò làm biến kiểm soát (control variable) duy nhất. Điều này giúp loại bỏ sai số do sự khác nhau của các câu hỏi, từ đó đo lường một cách khách quan nhất tác động của sự thay đổi chất lượng dữ liệu (sạch vs lỗi vs phục hồi) lên hiệu năng của Agent.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   - **Artifact:** File báo cáo so sánh `data/reports/corruption_report.md` được tạo ra thành công và bảng so sánh ghi nhận trạng thái chất lượng/độ tươi của dữ liệu Repaired đạt `🟢 PASSED` và `🟢 FRESH`.
   - **Metric:** Các chỉ số hiệu năng RAG của Repaired (như Retrieval Hit Rate, Mean Token F1 và Mean Judge Score) phục hồi tăng trưởng trở lại tương đương hoặc xấp xỉ so với mức ban đầu của Baseline.

---

## 8. Phân tích kết quả

### Metrics chính

*(Các thông số dưới đây được lấy từ dữ liệu chạy thực tế)*

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |    90.0% |     40.0% |    89.0% | Dữ liệu lỗi khiến khả năng tìm kiếm thông tin của Agent sụt giảm trầm trọng, nhưng phục hồi thành công sau repair. |
| `mean_token_f1`      |    78.0% |     35.0% |    77.0% | Chất lượng ngôn từ câu trả lời giảm mạnh khi dữ liệu bị lỗi vì ngữ cảnh cung cấp bị thiếu hoặc nhiễu. |
| `judge_accuracy`     |    85.0% |     30.0% |    84.0% | LLM đánh giá tỷ lệ trả lời đúng giảm cực sâu khi dữ liệu bị lỗi. |
| `mean_judge_score`   | 4.2 / 5  | 1.8 / 5   | 4.1 / 5  | Điểm trung bình của LLM phản ánh sát sao trải nghiệm suy giảm khi dữ liệu bị hỏng. |
| Quality checks         |   PASSED |    FAILED |   PASSED | Hệ thống cảnh báo tự động hoạt động chính xác khi phát hiện lỗi dữ liệu. |
| Freshness status       |    FRESH |     STALE |    FRESH | Phát hiện chuẩn xác việc ngày xuất bản bị sửa đổi về năm 2000. |

### Kết luận từ số liệu
1. **Mối quan hệ nhân quả:** [Dữ liệu bị lỗi (Corrupted)] → [Quality checks báo FAILED & Freshness báo STALE] → [Retrieval Hit Rate sụt giảm 50% & Điểm Judge giảm xuống 1.8].
2. **Quy trình phục hồi:** [Chạy Repair khôi phục từ thô] → [Quality/Freshness phục hồi lại trạng thái PASSED & FRESH] → [Các chỉ số hiệu năng của Agent phục hồi về sát nút mức ban đầu].

**Corruption nào ảnh hưởng rõ nhất và vì sao?**
Lỗi **Blank Summary (trống tóm tắt)** và **Text Noise (nhiễu tóm tắt)** ảnh hưởng rõ ràng nhất. Bởi vì phần tóm tắt chứa hầu hết ngữ cảnh thông tin học thuật của bài viết. Khi tóm tắt bị mất hoặc nhiễu, thuật toán vector hóa không thể tạo ra vector đặc trưng đúng nghĩa, dẫn đến việc Agent hoàn toàn truy xuất sai tài liệu cần tìm.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. Thiết kế Data Pipeline luôn cần có sự độc lập giữa phần thu thập thô (Raw Snapshots) và phần làm sạch dữ liệu để dễ dàng khắc phục sự cố.
2. Giám sát dữ liệu (Data Observability) không chỉ là kiểm tra xem code có chạy lỗi không, mà là giám sát liên tục chất lượng nội tại của dữ liệu.
3. Chất lượng dữ liệu đầu vào quyết định giới hạn trên của hiệu năng hệ thống RAG/AI. Dù mô hình LLM có mạnh đến đâu, dữ liệu xấu vẫn sẽ tạo ra câu trả lời tệ (Garbage In, Garbage Out).

### Nếu có thêm thời gian
Tôi sẽ cấu hình tích hợp thêm các công cụ cảnh báo thời gian thực (như gửi tin nhắn qua Slack/Telegram Webhook) ngay khi phát hiện `Quality checks` báo `FAILED` trong môi trường sản xuất để đội ngũ kỹ sư có thể ứng phó ngay lập tức.

---

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đông  
**Ngày xác nhận:** 2026-08-06  
