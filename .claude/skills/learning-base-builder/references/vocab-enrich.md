# Task: vocab_enrich (prompt version vocab_enrich-v3)

You write one study card per term for a Vietnamese software engineer (English level `input.learner_level`) learning
the vocabulary of one IT/AI course. Each task file is JSON with `input.terms[]`; every term has `key`, `term`, `type`,
`vi` (a first Vietnamese meaning), `en` (English definition in the course's context) and `context` (a sentence from
the course that uses the term, or null). `context` shows how the course uses the term — the card's example is a new
sentence you write.

## Procedure

For each task file path you were given:
1. Read the task JSON (and, once, the Vietnamese guide `translation-vi.md` next to this file).
2. Write one card per term (never skip one, never add one), looking at each term's own `en` and `context`.
3. Write `{"results": [...]}` to the task's `result_path` (project-relative) with the Write tool — exactly the
   fields below, no extra keys, no comments — then check it parses with
   `python -c "import json,sys; json.load(open(sys.argv[1], encoding='utf-8'))" <result_path>` and fix it if needed.

When all files are written, reply with one line only: `done <written>/<total>`.

## Fields

| Field | Rule |
|---|---|
| `key` | Copy the term's `key` exactly. |
| `ipa` | American IPA between slashes, e.g. `/ˌmælˈfɔːrmd/`. Required for a plain single word (`malformed`, `orchestrator`, `workflow`); for a phrase or hyphenated compound (`few-shot`) give it only if you are sure of every part, otherwise `null`; `null` for an acronym read letter by letter (MCP, API) and for code identifiers (`createMessageRequest`). |
| `meaning` | Vietnamese meaning **as used in this course**: 1–3 short glosses separated by commas, ≤ 15 words, ending with a period ("Sai định dạng, bị lỗi cấu trúc, không đúng chuẩn."). Start from `vi`/`en`; never use the everyday sense when the course means the technical one. |
| `part_of_speech` | One of: `noun`, `verb`, `adjective`, `adverb`, `noun phrase`, `verb phrase`, `phrasal verb`, `acronym`, `other` — as the course uses the term. |
| `domain` | `IT`, `AI` or `AI/IT` — where the usage below belongs. |
| `domain_usage` | One line in Vietnamese on how the term is used in that field: a typical collocation with its meaning (`Malformed JSON = JSON sai cấu trúc.`) or a short explanation (`Bảng so sánh hiệu năng giữa các hệ thống, mô hình hoặc thuật toán.`). |
| `example_en` | A new, short (≤ 15 words), natural English sentence from everyday IT/AI work that contains the term (`The request is malformed.`). Not copied from `context`. |
| `example_vi` | Natural Vietnamese translation of `example_en`. |
| `compare` | When learners often confuse the term with a similar word: `<Other> = <nghĩa>; <Term> = <nghĩa>` (`Reason = Lý do; Rationale = Lập luận giải thích tại sao lựa chọn đó hợp lý.`). Otherwise `null`. |

## Examples

```json
{"key": "malformed", "ipa": "/ˌmælˈfɔːrmd/", "meaning": "Sai định dạng, bị lỗi cấu trúc, không đúng chuẩn.",
 "part_of_speech": "adjective", "domain": "IT", "domain_usage": "Malformed JSON = JSON sai cấu trúc.",
 "example_en": "The request is malformed.", "example_vi": "Yêu cầu có định dạng không hợp lệ.", "compare": null}
{"key": "rationale", "ipa": "/ˌræʃəˈnæl/", "meaning": "Lý do, cơ sở lập luận, sự giải thích cho một quyết định.",
 "part_of_speech": "noun", "domain": "IT", "domain_usage": "Design rationale = Cơ sở lý do lựa chọn thiết kế.",
 "example_en": "Explain your rationale.", "example_vi": "Hãy giải thích cơ sở lập luận của bạn.",
 "compare": "Reason = Lý do; Rationale = Lập luận giải thích tại sao lựa chọn đó hợp lý."}
{"key": "benchmark table", "ipa": null, "meaning": "Bảng đối chuẩn, bảng so sánh hiệu suất.",
 "part_of_speech": "noun phrase", "domain": "IT",
 "domain_usage": "Bảng so sánh hiệu năng giữa các hệ thống, mô hình hoặc thuật toán.",
 "example_en": "Compare the results in the benchmark table.",
 "example_vi": "So sánh kết quả trong bảng benchmark.", "compare": null}
```

## Language

Every Vietnamese field is real Vietnamese with diacritics and follows `translation-vi.md`: translate the meaning,
keep established technical terms in English, then re-read the Vietnamese alone and rewrite anything that reads word
by word. Copy names and acronyms exactly as the term writes them.
