# Đánh giá chất lượng

```bash
python evaluations/report.py <slug> [--benchmark 4,28,52,88,112]
```

In báo cáo Markdown cho một khóa:

- **Task AI** theo mode và phiên bản prompt: số task `done / invalid / failed / pending / superseded`, tỉ lệ task phải chạy lại.
- **Từ vựng:** tỉ lệ ứng viên đã đánh giá (khớp ngữ cảnh hiện tại), tỉ lệ được chọn, tỉ lệ `needs_review`, phân bố loại và mức quan trọng.
- **Kiến thức** (chỉ bài trích bằng prompt hiện tại): số item mỗi bài, độ phủ câu của topic, trạng thái và loại item, số khái niệm/quan hệ.
- **Bộ benchmark:** 5 bài đại diện của khóa CCAR (bài 4, 28, 52, 88, 112 — rải qua các domain D1–D5) với số topic, số item và tiêu đề topic tiếng Việt để kiểm tra nhanh bằng mắt.

Dùng trước/sau khi đổi prompt (`prompt_version`) hoặc ngưỡng lọc để so sánh. Kết quả benchmark lần chạy 2026-11-05 nằm trong báo cáo cuối của phiên chạy đêm.
