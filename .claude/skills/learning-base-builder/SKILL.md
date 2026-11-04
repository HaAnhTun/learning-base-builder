---
name: learning-base-builder
description: Personal learning base from Udemy transcripts. Use to log in to Udemy, fetch or import course transcripts, export clean Markdown for NotebookLM, or show learning-base stats.
argument-hint: "login | fetch [<url|slug|id>] [--lang] | import <folder> | clean <course> | export notebooklm <course> [--by chapter|course|lesson] | stats"
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

## stats

`python -m engine stats`.

## Token secrecy

The Udemy access_token in `config.local.yaml` (or env `UDEMY_ACCESS_TOKEN`) grants full account access. Keep it out of the conversation: leave `config.local.yaml` unread and unprinted, and pass it to nothing but the engine.
