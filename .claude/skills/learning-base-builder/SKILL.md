---
name: learning-base-builder
description: Personal learning base from Udemy transcripts. Use to log in to Udemy, fetch or import course transcripts, export clean Markdown for NotebookLM, extract and rank course vocabulary, extract structured knowledge, review AI results, or show learning-base stats.
argument-hint: "login | fetch [<url|slug|id>] | import <folder> | clean <course> | export notebooklm <course> | vocab candidates|evaluate|enrich|export <course> | knowledge extract|enrich|export <course> | review <course> --mode vocab|knowledge | stats"
---

Engine CLI: run `python -m engine <command>` from the project root. `python -m engine <command> --help` is the source of truth for arguments. Spec: `docs/SPEC.md`.

Map the user's argument to one command, run it, and report the engine's output in the user's language.

## login

`python -m engine login` opens a real Chrome/Edge window and waits up to 10 minutes. Tell the user before running it: a browser window will open, sign in to Udemy there yourself; the token is saved automatically. Run it in the foreground with a 600000 ms timeout. Done when it prints that the token was saved.

## fetch

1. No course given: run `python -m engine fetch`, show the enrolled-course list, ask which one.
2. Run `python -m engine fetch <course> [--lang ...]`. It downloads only the requested languages into `data/input/<slug>/<locale>/` (one `_manifest.json` per locale folder), then imports each. Default language is `en`; pass `--lang` only when the user names other languages.
3. Done when the import line prints. Report counts plus `skipped` reasons from each locale's manifest when any lectures were skipped.
4. On "Token Udemy hết hạn" → run the **login** step, then retry fetch once. On "Bị chặn ... Cloudflare" → report it; retrying immediately rarely helps.

## import

`python -m engine import <folder>` — a course folder (all locales) or one locale folder. Registers files, then writes the Clean Dataset (`data/clean/<course>/<language>/*.json`: sentences with timestamps + paragraphs). Re-importing is safe: unchanged files (same SHA-256) are skipped; changed files are re-cleaned and their extracted data marked stale.

## clean

`python -m engine clean <course> [--force]` — re-clean a course (`<course>` = slug). `--force` re-cleans everything, e.g. after changing `clean.*` settings.

## export notebooklm

`python -m engine export notebooklm <course> [--by chapter|course|lesson] [--lang en]` — no AI. Writes Markdown + `index.md` to `data/export/notebooklm/<course>/<lang>/`. Default one file per chapter (fits NotebookLM's 50-source free tier). Tell the user the folder path and to upload the `.md` files themselves; relay any source-limit warnings.

## vocab

1. `python -m engine vocab candidates <course>` — deterministic (spaCy, ~20–30 s per 140 lessons). Uses `learner.cefr_level` from config; if it is null, ask the user (A2/B1/B2/C1) and pass `--level`.
2. **evaluate** = the runner loop below with mode `vocab_eval` and prepare command `python -m engine vocab prepare <course> [--limit N]`, ingest command `python -m engine vocab ingest <course>`.
3. **enrich** = the runner loop below with mode `vocab_enrich`, prepare command `python -m engine vocab enrich-prepare <course>`, ingest command `python -m engine vocab enrich-ingest <course>` (instructions file `vocab-enrich.md`). Adds part of speech, Vietnamese translations of the definition and example, and a usage note to the study list only.
4. `python -m engine vocab export <course>` → `data/export/vocabulary/<course>/`: `vocabulary.csv` (all selected terms), `vocabulary.json`/`.md` (study list: importance ≥ `vocabulary.export_min_importance`, most important and longest first).

To study, tell the user to open `study/index.html` in a browser and load `vocabulary.json` / `knowledge.json`.

## knowledge

1. **extract** = the runner loop below with mode `knowledge_extract`, prepare command `python -m engine knowledge prepare <course> [--lessons 1-10,15] [--limit N]`, ingest command `python -m engine knowledge ingest <course>`. One task per lesson (long lessons are pre-split into parts).
2. **enrich** = the runner loop below with mode `knowledge_enrich`, prepare command `python -m engine knowledge enrich-prepare <course>`, ingest command `python -m engine knowledge enrich-ingest <course>` (instructions file `knowledge-enrich.md`). Adds importance, a recall question and a natural re-translation to every item; run it after extract.
3. `python -m engine knowledge export <course>` → `data/export/knowledge/<course>/knowledge.{json,md}` (items with importance ≥ `knowledge.export_min_importance`).

## Runner loop (vocab evaluate|enrich / knowledge extract|enrich) — SPEC §9.2

Repeat until `prepare` reports 0 pending tasks or a round makes no progress:
1. Run the mode's prepare command.
2. `python -m engine ai batches <mode> <course>` → JSON `{model, max_parallel, batches: [[task paths]]}`.
3. For each batch spawn one Agent with `model` = the JSON's `model` (Haiku by default), at most `max_parallel` at a time, in the background. Prompt (fill in the reference file and paths):
   > You are an extraction worker for the project at <project root>. Read the instructions file <project root>/.claude/skills/learning-base-builder/references/<vocab-eval.md | vocab-enrich.md | knowledge-extract.md | knowledge-enrich.md> and the Vietnamese guide <project root>/.claude/skills/learning-base-builder/references/translation-vi.md. Process these task files in order: <absolute paths>. For each, write the result JSON to the task's `result_path` (relative to the project root) with the Write tool, exactly as the instructions say, then check it parses with `python -c "import json,sys; json.load(open(sys.argv[1], encoding='utf-8'))" <result_path>` and fix the file if it does not. Every title and content needs every language listed in output_languages. Give every task the same care as the first one. Write every translation, question and score yourself — scripts that generate them (word lists, templates, rules) produce garbage. Do not read or modify other project files; do not run the engine. Reply with one line only: `done <written>/<total>`.
4. When all agents of the round finish, run the mode's ingest command. Tasks that failed validation are re-armed by the next prepare (max `ai.max_retries` retries) and then reported as failed.

Keep task contents out of this conversation: never read task or result files yourself; only relay the engine's summaries.

## review

`python -m engine review list <course> --mode vocab|knowledge` prints items marked `needs_review` as JSON. Show them to the user in small groups; record each decision with `python -m engine review approved|rejected <course> --mode … --id <id> [--edits '{"field": "value"}']`. Decisions survive regeneration.

## stats

`python -m engine stats`.

## Token secrecy

The Udemy access_token in `config.local.yaml` (or env `UDEMY_ACCESS_TOKEN`) grants full account access. Keep it out of the conversation: leave `config.local.yaml` unread and unprinted, and pass it to nothing but the engine.
