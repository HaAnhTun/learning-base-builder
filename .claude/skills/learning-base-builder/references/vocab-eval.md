# Task: vocab_eval (prompt version vocab_eval-v1)

You evaluate vocabulary candidates extracted from one course's English transcript, for a Vietnamese learner whose
English level is `input.learner_level`. Each task file is JSON with `input.candidates[]` and an `output_schema`.

## Procedure

For each task file path you were given:
1. Read the task JSON.
2. Judge every candidate in `input.candidates` (never skip one, never add one).
3. Write the result JSON to the task's `result_path` (project-relative) with the Write tool — the file must contain
   only the JSON object `{"results": [...]}` that matches `output_schema` exactly (no extra keys, no comments).

When all files are written, reply with one line only: `done <written>/<total>`.

## Per-candidate fields

| Field | Rule |
|---|---|
| `key` | Copy the candidate's `key` exactly. |
| `selected` | `true` if the term is worth studying for this learner in this course (see below). |
| `term_type` | `acronym`, `abbreviation`, `technical_term` (domain term/product/protocol), `collocation` (natural multi-word phrase), `phrasal_verb`, `academic` (formal/academic general word), `general` (other single word). Fix the preliminary `type` if wrong. |
| `importance` | Integer 0–100, rubric below. Give unselected terms a low score (≤ 30). |
| `reason` | ≤ 15 English words: why selected or not. |
| `vietnamese_meaning` | Short Vietnamese meaning **as used in this course** (keep technical terms in English inside the Vietnamese, e.g. "lời gọi công cụ (tool call)"). Required when selected; may be `null` otherwise. |
| `english_definition` | One concise English definition in this course's context. Required when selected; may be `null` otherwise. |
| `expansion` | Full form for acronyms/abbreviations you are sure of (e.g. MCP → "Model Context Protocol"); otherwise `null`. |
| `cefr_level` | Only for `general`/`academic` single words when reasonably certain (A1–C2); otherwise `null`. |
| `example_refs` | 1–2 `ref` values copied from the candidate's `contexts` whose sentence shows the term clearly. Empty list only if no context uses it. Never invent refs. |
| `confidence` | 0–1: how sure you are about selection and meaning. Below 0.7 means "please have a human check". |

## When to select

Select when the term is any of:
- a domain term, acronym, product or protocol name central to the course (e.g. "context window", "MCP", "tool call");
- a collocation or phrasal verb a {learner_level} learner would benefit from (e.g. "spin up", "edge case", "wrap up");
- an academic/less common word above the learner's level (e.g. "idempotent", "orchestration", "mitigate").

Do **not** select:
- everyday words the learner already knows at their level (e.g. for B2: "important", "example", "big");
- fragments or meaningless phrases from transcript noise (e.g. "exactly what", "right choice", "next thing");
- speech-recognition errors / misspellings (e.g. "clod code" for "Claude Code") — reason: "ASR error of <correct term>";
- names of people, the course itself, or filler.

## Importance rubric (keep scores comparable across batches)

| Score | Meaning | Example |
|---|---|---|
| 90–100 | Core concept of the whole course; the learner cannot follow without it | "context window", "MCP" in a Claude architecture course |
| 70–89 | Important recurring domain term or very useful technical collocation | "tool call", "system prompt", "rate limit" |
| 50–69 | Useful term that appears in some lessons, or a valuable phrasal verb/academic word | "exponential backoff", "spin up", "mitigate" |
| 30–49 | Nice to know; minor term or general word slightly above level | "granular", "boilerplate" |
| 0–29 | Not selected / noise / already known | "thing", "exactly what" |
