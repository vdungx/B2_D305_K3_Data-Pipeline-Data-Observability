# 📊 Báo Cáo Giám Sát Dữ Liệu Pha Baseline (Phase 1)

> [!NOTE]
> Báo cáo này tổng hợp kết quả của pha Baseline chạy trên dữ liệu sạch được thu thập và làm sạch từ nguồn Crossref API.

## 1. 🔍 Tóm tắt nguồn dữ liệu (Source Summary)
| Thuộc tính | Giá trị |
| :--- | :--- |
| **Nguồn dữ liệu (Source API)** | Crossref REST API |
| **Truy vấn (Query)** | `agentic retrieval augmented generation large language model` |
| **Bộ lọc (Filter)** | `from-pub-date:2026-02-07,has-abstract:true` |
| **Số lượng bản ghi tối đa (Max Results)** | 24 |
| **Số lượng bản ghi lấy được** | 24 |

## 2. 📈 Chỉ số đánh giá Baseline (Retrieval & Generation Metrics)
Dưới đây là kết quả đánh giá hệ thống RAG sử dụng dữ liệu sạch:

* **🎯 Tỉ lệ tìm kiếm trúng (Retrieval Hit Rate):** `100.00%`
* **✍️ Điểm tương đồng từ vựng (Mean Token F1):** `100.00%`
* **🤖 Độ chính xác đánh giá (Judge Accuracy):** `90.00%`
* **⭐ Điểm trung bình đánh giá (Mean Judge Score):** `4.70 / 5.0`

### 🔍 Chi tiết đánh giá bổ sung (Ragas Metrics)
*Set RUN_RAGAS=1 to enable the slower Ragas pass.*

## 3. 🛡️ Kiểm định chất lượng dữ liệu (Data Quality Checks)
Tổng hợp trạng thái kiểm tra chất lượng dữ liệu của DataFrame đã được làm sạch:

* **Trạng thái chung:** 🟢 **PASSED (Tất cả bài kiểm tra)**
* **Thời gian kiểm định:** `2026-08-06T11:16:41.708141`
* **Tổng số bản ghi kiểm định:** `24`

| Tên kiểm tra (Check Name) | Trạng thái (Status) | Kết quả quan sát (Observed) | Thông báo (Message) |
| :--- | :---: | :---: | :--- |
| **Row Count** | 🟢 **PASSED** | `24` | Passed: Found 24 records. |
| **Paper ID Non-Null** | 🟢 **PASSED** | `0` | Passed: 0 null/empty paper_ids. |
| **Paper ID Unique** | 🟢 **PASSED** | `True` | Passed: All paper_ids are unique. |
| **Title Non-Null** | 🟢 **PASSED** | `0` | Passed: 0 null/empty titles. |
| **Summary Min Length** | 🟢 **PASSED** | `0` | Passed: All summaries meet the minimum length (>= 30 words). |
| **Freshness Check** | 🟢 **PASSED** | `0` | Passed: 0 stale papers found (threshold: 180 days). |

## 4. 🕒 Báo cáo độ tươi dữ liệu (Data Freshness Report)
* **Trạng thái độ tươi:** 🟢 **FRESH (Dữ liệu tươi mới)**
* **Ngày xuất bản mới nhất (Latest Published Date):** `2026-08-01`
* **Ngày xuất bản cũ nhất (Oldest Published Date):** `2026-02-13`
* **Số lượng dòng cũ/lạc hậu (Stale Rows):** `0`
* **Tổng số dòng dữ liệu (Total Rows):** `24`
