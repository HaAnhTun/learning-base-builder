# Task: knowledge_extract (prompt version knowledge_extract-v2)

You turn one lesson transcript (or one part of a long lesson) into structured, hierarchical knowledge.
Each task file is JSON: `input.sentences[]` (`id`, `text`), `input.paragraph_starts` (sentence ids where a pause-based
paragraph starts — hints only), `input.part` (`start`/`end` sentence ids you own, `index`/`of`),
`input.readonly_context` (sentences before your part: context only, never cite them), `input.output_languages`,
and `output_schema`.

## Procedure

For each task file path you were given:
1. Read the task JSON.
2. Segment the sentences into topics by meaning, extract knowledge items, and write the result JSON to the task's
   `result_path` (project-relative) with the Write tool. The file must contain only `{"topics": [...]}` matching
   `output_schema` exactly (no extra keys, no comments).

When all files are written, reply with one line only: `done <written>/<total>`.

## Segmentation

- Topics are **consecutive, non-overlapping** ranges of sentence ids, in order, inside `[part.start, part.end]`.
  Ranges are inclusive, so each topic starts at the previous topic's `sentence_end + 1` — a sentence belongs to
  exactly one topic. Together they should cover nearly all sentences (intro/outro chit-chat may be its own topic).
- Cut where the subject changes, never in the middle of an explanation. Typical lesson: 2–6 topics.
- Use a subtopic (one level only, optional) when a topic clearly has distinct parts; subtopic ranges lie inside
  their topic.
- Titles are short noun phrases describing the content (e.g. "Context window limits"), not "Introduction" unless
  it really is one.

## Knowledge items (attach each to the deepest topic/subtopic containing its sentences)

| `item_type` | Use for | Notes |
|---|---|---|
| `concept` | A named idea the lesson introduces or relies on | `concept_name` required (English, canonical name, e.g. "Model Context Protocol") |
| `definition` | An explicit definition / what something is | `concept_name` required |
| `key_point` | An important claim, rule or takeaway | |
| `process` | Steps or how something works | `content` per language is a **list of steps** |
| `example` | A concrete example the instructor gives | |
| `advantage` / `disadvantage` | Pros / cons of an approach | |
| `relation` | How two concepts relate | `relation` = `{"from", "to", "type"}`, type ∈ is_a, part_of, uses, compared_with, alternative_to, related_to |
| `warning` | Pitfalls, limits, exam traps, "don't do X" | |

- `item_type` must be exactly one of the nine values above — nothing else (no "feature", "tip", "note").
- `title` and `content` are objects with exactly one entry per language in `input.output_languages`
  (e.g. `{"en": "...", "vi": "..."}`).
- **Vietnamese (`vi`) must read as natural Vietnamese** — follow `translation-vi.md` next to this file. Keep in English only proper names, product names and
  established technical terms (MCP, client, server, tool call, prompt, context window, sampling…); translate every
  ordinary word. Good: "Một MCP server được thiết kế tốt nên không lưu trạng thái (stateless) và chỉ tập trung vào
  nghiệp vụ của nó." Bad: "Một well-designed MCP server là stateless và tập trung vào domain của nó."
  Vietnamese titles are translated too ("Vì sao cần sampling", not a copy of the English title).
- `content`: 1–3 sentences, faithful to the transcript, in your own words. Do not add facts the lesson does not state.
- `concept_name` (English canonical name) is required for `concept` and `definition`; `relation` is required for
  `relation`; otherwise both are `null`.
- `sentence_start`/`sentence_end`: the smallest range that supports the item, and it must lie inside the range of
  the topic/subtopic that contains the item.
- `confidence` (0–1, on topics, subtopics and items): below 0.7 means "please have a human check".
- Prefer quality over quantity: typically 5–12 items per lesson; skip trivia, greetings, course logistics and
  restatements of the same point.
