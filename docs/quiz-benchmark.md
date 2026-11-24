# Kết quả benchmark quiz CCA-F (nâng cấp skill từ đề thi)

Mục tiêu: dùng 360 câu luyện thi CCA-F (`sample/input/anthropic-claude-certified-architect-3-full-practice-exams`) làm bài kiểm tra có đáp án để tìm quy tắc mà Claude thực sự còn thiếu, rồi viết quy tắc đó vào skill. Tài liệu này không chứa nội dung câu hỏi hay đáp án.

## Giao thức

- Đề 1-3 để học, đề 4 để kiểm tra, đề 5-6 giữ kín (**chưa dùng**).
- Claude làm đề mù: file đề không có đáp án hay giải thích, không dùng công cụ nào ngoài đọc đúng một file đề. Đã kiểm tra lại từng lệnh của các agent: mỗi agent chỉ đọc file đề của mình.
- Mỗi model chạy 3 lượt. Câu multi-select chỉ đúng khi chọn đủ và đúng tập đáp án.
- Luật viết quy tắc: chỉ viết cho mẫu quyết định mà Claude sai ≥ 30% số câu huấn luyện của mẫu đó (câu tính là sai khi sai ở ≥ 2/3 lượt); mẫu đúng ≥ 90% thì không viết.

## Kết quả (không skill, 240 câu x 3 lượt)

| Model | Đề 1 | Đề 2 | Đề 3 | Đề 4 |
|---|---|---|---|---|
| Sonnet 5.5 | 60, 60, 60 | 60, 60, 60 | 60, 60, 60 | 59, 59, 59 |
| Haiku 5.5 | 60, 60, 60 | 60, 60, 59 | 60, 60, 60 | 59, 59, 59 |

(Số câu đúng trên 60 mỗi lượt.)

- Câu sai ổn định duy nhất ở cả hai model: câu 30 của đề 4 (mẫu "giao việc khám phá dài cho subagent chỉ đọc").
- Tỉ lệ sai cao nhất trên mọi mẫu quyết định tập học: 0%. Không mẫu nào đạt ngưỡng 30%.

## Kết luận

- Không có khoảng trống kiến thức mà skill có thể lấp, kể cả với model nhỏ (Haiku). Do đó không viết thêm quy tắc, không chạy tiếp các giai đoạn viết/kiểm tra/chạy đề kín.
- Ba skill kiến thức vẫn là tham chiếu gọi tay (`disable-model-invocation`). Kết quả này khớp hai vòng A/B trước (tác vụ viết prompt, nén ngữ cảnh, kế hoạch điều phối): baseline của Claude đã ở mức trần.
- Giới hạn của kết luận: chọn đúng đáp án khi đọc đề chưa chắc bằng làm đúng khi làm việc thật; các câu hỏi có thể đã nằm trong dữ liệu huấn luyện; chỉ thử hai model.
- Chi phí: khoảng 3 triệu token cho cả hai model (53 agent).
