# 📊 Báo Cáo So Sánh Đối Chiếu Hiệu Năng & Chất Lượng Dữ Liệu
## So sánh: Baseline vs Corrupted (Dữ liệu lỗi) vs Repaired (Dữ liệu phục hồi)

> [!IMPORTANT]
> Báo cáo này so sánh hiệu năng của RAG Agent, chất lượng dữ liệu và độ tươi dữ liệu qua 3 giai đoạn của pipeline để chứng minh tác động của chất lượng dữ liệu tới hệ thống AI.

## 1. ⚔️ Bảng so sánh chỉ số tổng hợp (Comparison Matrix)

| Chỉ số / Trạng thái | Giai đoạn Baseline (Sạch) | Giai đoạn Corrupted (Lỗi) | Giai đoạn Repaired (Phục hồi) |
| :--- | :---: | :---: | :---: |
| **🎯 Retrieval Hit Rate** | `100.00%` | `40.00%` | `100.00%` |
| **✍️ Mean Token F1** | `100.00%` | `39.42%` | `100.00%` |
| **🤖 Judge Accuracy** | `100.00%` | `40.00%` | `90.00%` |
| **⭐ Mean Judge Score** | `5.00 / 5.0` | `2.65 / 5.0` | `4.70 / 5.0` |
| **🛡️ Quality Checks Status** | `🟢 **PASSED (All)**` | 🔴 **FAILED** | 🟢 **PASSED (All)** |
| **🕒 Freshness Status** | `🟢 **FRESH**` | 🔴 **STALE** | 🟢 **FRESH** |

## 2. 🔍 Phân tích tác động của việc lỗi dữ liệu (Performance Degradation Analysis)
Khi chèn lỗi vào tập dữ liệu sạch (Corrupted Data), chúng ta quan sát thấy các hiện tượng sau:
1. **Suy giảm chất lượng tìm kiếm (Retrieval Hit Rate giảm):** Việc xóa các bài viết mới nhất (Drop Latest) và chèn nhiễu ký tự (Text Noise) vào phần tóm tắt làm cho thuật toán tạo vector embedding không biểu diễn chính xác được ngữ nghĩa của tài liệu. Ngoài ra, việc làm trống tóm tắt (Blank Summary) khiến RAG agent hoàn toàn không tìm thấy ngữ cảnh cần thiết.
2. **Suy giảm độ chính xác của câu trả lời (Mean Token F1 và Judge Score giảm mạnh):** Khi ngữ cảnh được truy xuất bị thiếu hoặc sai lệch do tiêu đề bị cắt ngắn (Title Truncation), LLM không có đủ thông tin chính xác và dẫn đến hiện tượng ảo tưởng (hallucination) hoặc từ chối trả lời, khiến điểm do LLM đánh giá (Judge Score) sụt giảm nghiêm trọng.
3. **Cảnh báo từ hệ thống Observability:** Hệ thống lập tức kích hoạt cảnh báo đỏ trên các bài kiểm tra chất lượng như số lượng bản ghi trùng lặp, bài viết thiếu tóm tắt, tiêu đề quá ngắn và độ tươi dữ liệu (do bị sửa đổi ngày xuất bản về năm 2000).

## 3. 🛠️ Đánh giá hiệu quả của quá trình phục hồi (Recovery Analysis)
Sau khi thực hiện quy trình Phục hồi dữ liệu (Repair Flow):
1. **Khôi phục dữ liệu sạch hoàn chỉnh:** Việc đọc lại bản ghi thô từ nguồn gốc (Raw Snapshots) và chạy lại pipeline làm sạch tiêu chuẩn giúp khôi phục toàn bộ các trường bị lỗi, loại bỏ hoàn toàn các dòng trùng lặp và sửa lại ngày xuất bản chính xác.
2. **Khôi phục hiệu năng RAG Agent:** Chỉ số **Retrieval Hit Rate** và **Mean Judge Score** đã tăng trưởng trở lại về mức ban đầu của pha Baseline. Điều này chứng minh rằng việc phục hồi dữ liệu trực tiếp từ nguồn thô là giải pháp triệt để để đưa hệ thống RAG hoạt động ổn định trở lại.

## 4. 🧠 Bài học kinh nghiệm & Đề xuất về Data Observability
1. **Tầm quan trọng của Data Observability:** Nếu không có các bộ kiểm tra chất lượng tự động, các lỗi dữ liệu ngầm (như trống summary, sai ngày tháng) sẽ đi thẳng vào Vector Store mà không ai hay biết, trực tiếp làm hỏng trải nghiệm của khách hàng sử dụng RAG agent.
2. **Giám sát liên tục (Continuous Monitoring):** Việc giám sát độ tươi (freshness) và số lượng bản ghi trùng lặp giúp phát hiện sớm các lỗi đứt gãy pipeline từ phía API của đối tác thứ ba (Crossref).
3. **Thiết lập cơ chế phục hồi tự động (Auto-recovery):** Giữ bản ghi thô (raw snapshot) là một thiết kế hệ thống quan trọng để cho phép phục hồi dữ liệu bất cứ lúc nào mà không cần gọi lại API nguồn nhiều lần, tránh giới hạn băng thông (rate limit).
