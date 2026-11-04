# Task: vocab_enrich (prompt version vocab_enrich-v2)

You add learning details to vocabulary a Vietnamese learner (level `input.learner_level`) will study from one course.
Each task file is JSON with `input.terms[]`; every term has `key`, `term`, `type`, `vi` (short Vietnamese meaning),
`en` (English definition in the course's context) and `example` (an original sentence from the course, or null).

## Procedure

For each task file path you were given:
1. Read the task JSON (and, once, the Vietnamese guide `translation-vi.md` next to this file).
2. Produce one result per term (never skip one, never add one).
3. Write `{"results": [...]}` to the task's `result_path` (project-relative) with the Write tool — exactly the
   fields below, no extra keys, no comments — then check it parses with
   `python -c "import json,sys; json.load(open(sys.argv[1], encoding='utf-8'))" <result_path>` and fix it if needed.

When all files are written, reply with one line only: `done <written>/<total>`.

## Fields

| Field | Rule |
|---|---|
| `key` | Copy the term's `key` exactly. |
| `vi` | The short Vietnamese meaning (≤ 8 words) of the term **in this course**. Start from the given `vi`; rewrite it when it is a literal or everyday-sense translation ("business rules" → "quy tắc nghiệp vụ", not "quy tắc kinh doanh"). |
| `part_of_speech` | One of: `noun`, `verb`, `adjective`, `adverb`, `noun phrase`, `verb phrase`, `phrasal verb`, `acronym`, `other` — as the term is used in the example/definition. |
| `definition_vi` | A faithful, natural Vietnamese translation of `en` (the full definition, not just the short meaning). Keep established technical terms in English in parentheses where helpful, e.g. "…cửa sổ ngữ cảnh (context window)…". |
| `example_vi` | Natural Vietnamese translation of `example`; `null` only when `example` is null. |
| `usage_note` | Optional ≤ 25 Vietnamese words that help learning: a common collocation, a confusable word, or the typical pattern (e.g. "thường đi với: *call a tool*, *tool use*"). `null` when nothing useful to add. |

Every Vietnamese field follows `translation-vi.md`: translate the meaning, keep technical terms in English, then
re-read the Vietnamese alone and rewrite anything that reads word by word.
