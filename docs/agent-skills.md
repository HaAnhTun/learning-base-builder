# Bộ skill làm việc với AI (agent-skills)

`.claude/skills/` có một skill chạy tự động (`project-state`) và ba skill tham chiếu gọi tay. Hai vòng thử A/B (100 agent) không cho thấy ba skill tham chiếu làm Claude làm việc tốt hơn đáng kể, nên chúng được đặt `disable-model-invocation: true`: không tốn context mỗi phiên, gọi tay khi cần. Nguồn kiến thức: khóa CCAR (Certified Claude Architect), mỗi quy tắc gắn nhãn `[CCAR NN]` (số bài) hoặc `[practice]` (thực hành tốt nhưng khóa không nói).

| Skill | Việc làm | Cách dùng |
|---|---|---|
| `project-state` | Giữ state làm việc trong repo, tự nạp ở đầu phiên, tự cập nhật | Tự động: hook đầu phiên, cập nhật khi xong task/chốt quyết định; `/project-state init\|resume\|status` |
| `context-discipline` | Ngân sách context, cắt tỉa output, giao việc khám phá cho subagent, fact block, nguồn trích dẫn | Gọi tay: `/context-discipline` |
| `prompt-craft` | Viết prompt, system prompt, brief cho subagent, output có cấu trúc, retry | Gọi tay: `/prompt-craft` |
| `agent-orchestration` | Chọn 1 hay nhiều agent, fan-out, xử lý lỗi, duyệt của người, checkpoint, đặt chỉ dẫn vào đúng tầng | Gọi tay: `/agent-orchestration` |

## Luồng state

- `.claude/state/STATE.md` (≤80 dòng): mục tiêu, trạng thái, việc đang làm, việc kế tiếp, việc đã xong, câu hỏi mở, ghi chú, tóm tắt phiên trước. Hook SessionStart nạp nguyên văn vào mọi phiên (startup, resume, clear, compact).
- `.claude/state/DECISIONS.md`: nhật ký quyết định (ngày, quyết định, lý do, phương án bỏ). Chỉ thêm mục, đọc khi cần.
- `.claude/state/archive/`: phần Done đã cũ.
- Hook Stop chặn dừng đúng một lần nếu file làm việc đổi mà STATE.md chưa cập nhật, hoặc STATE.md quá 80 dòng. Nếu state chứa chuỗi giống secret thì chặn mỗi lần, không in giá trị ra.
- Cảnh báo `STALE` khi state quá 14 ngày hoặc repo đã đi quá 30 commit so với `head:` đã ghi.
- Agent không tự commit state; bạn quyết định khi nào commit.

## Cài vào dự án khác

```bash
python .claude/skills/project-state/scripts/install.py <thư-mục-dự-án>
```

Copy thư mục `.claude/skills/` sang dự án trước. Lệnh trên tạo khung state, gộp hook vào `.claude/settings.json` (giữ nguyên các khóa khác) và thêm khối "Working agreement" vào `CLAUDE.md`. Sau đó mở phiên mới và chạy `/project-state init` để agent điền thông tin dự án.

Lưu ý: hook chỉ chạy sau khi bạn chấp nhận hộp thoại workspace trust; hook gọi `python`, nên máy cần `python` trong PATH.

## Kiểm thử

```bash
python -m pytest tests/test_state_hook.py tests/test_state_install.py
```
