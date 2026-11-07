# Archive — trích xuất từ vựng và kiến thức bằng AI

Ngày lưu trữ: 2026-11-08. Quyết định của người dùng: không cần trích xuất từ vựng/kiến thức nữa — file Markdown
NotebookLM (`python -m engine export notebooklm <khóa>`) đã đủ để đưa vào LLM; phần còn lại của dự án là tải thêm
quiz/bài kiểm tra/tài liệu của khóa và đóng gói thành skill (`python -m engine export skill <khóa>`).

## Nội dung

| Thư mục | Là gì |
|---|---|
| `engine/vocab/`, `engine/knowledge/` | Vocabulary Mode và Knowledge Mode (prepare → subagent Haiku → ingest), gồm `enrich` |
| `engine/ai/` | AI orchestrator: task packet, cache, validate, chia lô cho subagent |
| `engine/normalizer.py`, `engine/exporter.py` | Chuẩn hóa thuật ngữ; xuất JSON/CSV/Markdown của hai mode |
| `study/` | App flashcard tĩnh (`index.html`) cho `vocabulary.json` / `knowledge.json` |
| `evaluations/report.py` | Báo cáo chất lượng khóa học |
| `skill-references/` | Hướng dẫn cho subagent (`vocab-*.md`, `knowledge-*.md`, `translation-vi.md`) |
| `tests/` | Test của các phần trên (129 test lúc lưu trữ) |
| `resources/` | Bảng tần suất từ tiếng Anh cho bước lọc từ phổ thông |
| `config-extraction.yaml` | Các khối `learner`, `vocabulary`, `knowledge`, `ai` của `config.yaml` |
| `data/vocabulary/`, `data/knowledge/` | Kết quả cuối cho khóa CCAR (từ vựng mức C1: 451 thẻ; kiến thức: 2.709 thẻ) |
| `data/work/` | Task packet và kết quả thô của subagent |
| `data/learning.db.extraction-snapshot` | Bản sao DB lúc lưu trữ (có đủ kết quả đã đánh giá) |

`data/learning.db` đang dùng vẫn giữ nguyên schema v6 (các bảng `vocab_*`, `knowledge_*`, `ai_task` còn đó nhưng không dùng).

## Khôi phục

```bash
git mv archive/engine/vocab engine/vocab
git mv archive/engine/knowledge engine/knowledge
git mv archive/engine/ai engine/ai
git mv archive/engine/normalizer.py engine/normalizer.py
git mv archive/engine/exporter.py engine/exporter.py
git mv archive/study study
git mv archive/evaluations evaluations
git mv archive/resources resources
git mv archive/tests/*.py tests/
git mv archive/skill-references/*.md .claude/skills/learning-base-builder/references/
```

Sau đó dán `config-extraction.yaml` vào `config.yaml`, thêm lại các lệnh `vocab`, `knowledge`, `ai`, `review` vào
`engine/__main__.py` (xem lịch sử git: commit "Archive AI extraction"), và cài `spacy>=3.8,<3.9` +
`en_core_web_sm` 3.8.0 (`playwright` nếu muốn chạy test app học).
