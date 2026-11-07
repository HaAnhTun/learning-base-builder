# Task: knowledge_enrich (prompt version knowledge_enrich-v1)

You turn knowledge items already extracted from course lessons into study cards for a Vietnamese learner (level
`input.learner_level`). Each task file is JSON with `input.languages` (e.g. `["en", "vi"]`) and `input.lessons[]`;
each lesson has `topics[]` (`key`, `title_en`, `items[]`), each item has `key`, `type`, `title_en`, `content_en`
(a string, or a list of steps for `process`) and sometimes `concept`.

## Procedure

For each task file path you were given:
1. Read the task JSON (and, once, the Vietnamese guide `translation-vi.md` next to this file).
2. Produce one entry per topic and one per item — every key in the input, no new keys.
3. Write `{"topics": [...], "items": [...]}` to the task's `result_path` (project-relative) with the Write tool,
   matching `output_schema` exactly, then check it parses with
   `python -c "import json,sys; json.load(open(sys.argv[1], encoding='utf-8'))" <result_path>` and fix it if needed.

When all files are written, reply with one line only: `done <written>/<total>`.

## Topics

`{"key": "t…", "title": {<each non-English language>: "…"}}` — the topic title translated naturally.

## Items

| Field | Rule |
|---|---|
| `key` | Copy the item's `key` exactly. |
| `importance` | Integer 0–100: how much this item is worth studying, judged against the whole lesson and course (scale below). |
| `question` | `{<every language in input.languages>: "…"}` — one active-recall question whose answer is this item's content, specific enough to have one answer ("Vì sao MCP server nên không lưu trạng thái?", not "MCP server là gì?" when the item is about statelessness). For `process`: "Các bước để …?". |
| `title` | `{<each non-English language>: "…"}` — `title_en` translated naturally; a concept name becomes a Vietnamese phrase with the English name in parentheses ("Khép vòng phản hồi (loop closure)"). |
| `content` | `{<each non-English language>: …}` — `content_en` translated naturally; a list with the same steps for `process`. |

Example item (a `process` with three steps in `content_en`):

```json
{"key": "i123", "importance": 88,
 "question": {"en": "What are the steps to add an MCP server?", "vi": "Các bước để thêm một MCP server?"},
 "title": {"vi": "Thêm một MCP server"},
 "content": {"vi": ["Cài đặt server", "Đăng ký server với client", "Khởi động lại client"]}}
```

`content.vi` of a `process` is a JSON list with one string per step, exactly as many steps as `content_en`.

### Importance scale

| Score | Meaning |
|---|---|
| 90–100 | Core of the course or exam: definition of a central concept, a rule to remember, an exam trap. |
| 70–89 | Important supporting point: key process, main pros/cons, a warning with real consequences. |
| 50–69 | Useful detail or a clear example that makes a concept concrete. |
| 0–49 | Not worth a card: course logistics, reviews/greetings, anecdotes, restatements of another item, obvious facts. |

Score by **comparing the items of the same lesson**: first pick the 2–4 items a learner must remember from it
(85+), then rank the rest below them. In a typical lesson about a quarter of the items score 85+, half score 60–84,
and the rest fall lower; an item that repeats another item's point scores below 50. Items below 50 are left out
of the study files by the engine, so the score decides what the learner studies — still return every item, low
scores included.

## Language

Every `vi` text is full Vietnamese with diacritics ("Bên gửi xác nhận bên nhận đã sẵn sàng…"); the engine rejects
`vi` text written in English.

Every non-English text follows `translation-vi.md`: translate the meaning, keep technical terms in English, then
re-read the Vietnamese alone and rewrite anything that reads word by word. Keep the facts of `title_en`/`content_en`;
add nothing the English does not say.
