# Bộ skill làm việc với AI (agent-skills)

`.claude/skills/` có một skill chạy tự động (`project-state`) và ba skill tham chiếu gọi tay. Hai vòng thử A/B (100 agent) không cho thấy ba skill tham chiếu làm Claude làm việc tốt hơn đáng kể, nên chúng được đặt `disable-model-invocation: true`: không tốn context mỗi phiên, gọi tay khi cần. Nguồn kiến thức: khóa CCAR (Certified Claude Architect), mỗi quy tắc gắn nhãn `[CCAR NN]` (số bài) hoặc `[practice]` (thực hành tốt nhưng khóa không nói).

| Skill | Việc làm | Cách dùng |
|---|---|---|
| `project-state` | Giữ state làm việc trong repo, tự nạp ở đầu phiên, tự cập nhật | Tự động: hook đầu phiên, cập nhật khi xong task/chốt quyết định; `/project-state init\|resume\|status` |
| `context-discipline` | Ngân sách context, cắt tỉa output, giao việc khám phá cho subagent, fact block, nguồn trích dẫn | Gọi tay: `/context-discipline` |
| `prompt-craft` | Viết prompt, system prompt, brief cho subagent, output có cấu trúc, retry | Gọi tay: `/prompt-craft` |
| `agent-orchestration` | Chọn 1 hay nhiều agent, fan-out, xử lý lỗi, duyệt của người, checkpoint, đặt chỉ dẫn vào đúng tầng | Gọi tay: `/agent-orchestration` |

## Ánh xạ domain CCA-F

| Domain CCA-F | Nằm ở đâu | Cơ chế mượn từ mattpocock/skills (MIT) |
|---|---|---|
| D1 Agentic Architecture & Orchestration | `agent-orchestration` (mục Review hai trục độc lập, fan-out, lỗi, duyệt của người, checkpoint) | `code-review`: hai reviewer song song ở ngữ cảnh sạch, kiểm đầu vào một lần trước khi tản agent, không gộp kết quả |
| D2 Tool Design & MCP | Ngoài phạm vi (chỉ áp dụng khi tự xây agent bằng SDK/API) | - |
| D3 Claude Code Configuration & Workflows | `agent-orchestration/references/layer-choice.md` (đặt chỉ dẫn vào CLAUDE.md, rules, skill, subagent hay hook) | `git-guardrails-claude-code`: ví dụ luật "không bao giờ" thực thi bằng hook PreToolUse fail-closed |
| D4 Prompt Engineering & Structured Output | `prompt-craft` | - |
| D5 Context Management & Reliability | `context-discipline` (cây quyết định ở ranh giới phase) và `project-state` (state xuyên phiên) | `ask-matt`: cây quyết định ranh giới phase; `domain-modeling`: cổng 3 điều kiện cho DECISIONS.md; `handoff`: tham chiếu chứ không sao chép |

Mỗi thẻ mượn có nhãn domain `[D1..D5]`, nhãn nguồn `[CCAR NN]` hoặc `[practice]`, và dòng ghi nguồn `(mattpocock/skills, MIT: <skill>)`. Nội dung được viết lại cho khớp skill, không chép nguyên văn.

## Luồng state

- `.claude/state/STATE.md` (≤80 dòng): mục tiêu, trạng thái, việc đang làm, việc kế tiếp, việc đã xong, câu hỏi mở, ghi chú, tóm tắt phiên trước. Hook SessionStart nạp nguyên văn vào mọi phiên (startup, resume, clear, compact).
- `.claude/state/DECISIONS.md`: nhật ký quyết định (ngày, quyết định, lý do, phương án bỏ). Chỉ thêm mục, đọc khi cần.
- `.claude/state/archive/`: phần Done đã cũ.
- Hook Stop chặn dừng đúng một lần nếu file làm việc đổi mà STATE.md chưa cập nhật, hoặc STATE.md quá 80 dòng. Nếu state chứa chuỗi giống secret thì chặn mỗi lần, không in giá trị ra.
- Hook Stop còn kiểm **cấu trúc** STATE.md (đủ 8 mục bắt buộc, có `updated:` và `head:`, Done ≤10 mục, Next ≤7 mục) trong cùng lần nhắc một-lần-mỗi-phiên. Chạy tay: `python .claude/skills/project-state/scripts/state_hook.py check` in báo cáo (số dòng, cấu trúc, độ tươi, vị trí secret, không bao giờ in giá trị secret).
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
