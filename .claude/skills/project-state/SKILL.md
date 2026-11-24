---
name: project-state
description: Keeps a project's working state in .claude/state/ so each new session resumes without the user re-explaining. Use when starting or resuming work in a project, when a task finishes, a decision is made, before an irreversible action, when a Stop hook asks for a state update, or when the user asks to set up, load or check project state (init, resume, status).
argument-hint: "init | resume | status"
---

- `.claude/state/STATE.md`: hot state, at most 80 lines. A SessionStart hook injects it into every session (startup, resume, clear, compact).
- `.claude/state/DECISIONS.md`: cold log, append-only. Read it when a past decision matters.
- `.claude/state/archive/YYYY-MM.md`: Done items that aged out of STATE.md.

Hooks (`scripts/state_hook.py`): SessionStart injects the state and flags it STALE when older than 14 days or 30+ commits behind. Stop blocks once per session when STATE.md is over 80 lines, fails the structure check (`python ${CLAUDE_SKILL_DIR}/scripts/state_hook.py check` runs it on demand), or project files changed after it (the state directory and `.claude/worktrees` are ignored), and blocks at the end of every turn while a state file holds a secret, but only once per chain of stop-hook continuations (`stop_hook_active` ends the chain), so remove the value at the first block. Hooks fail open: an erroring or timed-out hook lets the stop proceed, so keep secrets out of state files yourself. PreCompact tells the summary to keep the state.

Map the user's argument to one mode. No argument: run **update**.

## init

1. Run `python ${CLAUDE_SKILL_DIR}/scripts/install.py` from the project root. It creates the state files, merges the three hooks into `.claude/settings.json` and writes the working-agreement block into `CLAUDE.md`. Done when it prints `project-state installed`.
2. Fill STATE.md from the repo itself: README, CLAUDE.md, `docs/`, `git log -15`, the top-level tree, the package manifest. Write `?` for anything the repo does not say.
3. Settle every `?` with the user, one AskUserQuestion batch at a time, recommended answer first (the grilling style). Done when Goal & scope has no `?` and the user confirmed the draft.
4. Tell the user in their language: STATE.md is injected from the next session on. An interactive Claude Code session holds project hooks back until the workspace trust dialog is accepted; under `claude -p` or the SDK the folder counts as trusted and committed hooks run, so install them only in repositories the user trusts.

## resume

The hook has normally injected STATE.md already. When it is not in context, read `.claude/state/STATE.md`.

1. Check it against reality: `git status --short`, `git log -5 --oneline`.
2. Reply with 2-3 lines in the user's language: what is in progress, what comes next.
3. Ask before acting only when the request contradicts the state, or the state is STALE or disagrees with git.

Done when the first reply names the in-progress item and the next step.

## status

Report in the user's language: line count against the 80-line cap, `updated:` age, commits since `head:` (`git rev-list --count <head>..HEAD`), then the In progress and Next items. Done when the report is given.

## update

Run at each milestone: a task finished, a decision made, a plan changed, before an irreversible action, when a Stop hook asks.

1. Re-read STATE.md immediately before writing; another session may have changed it.
2. Rewrite the affected blocks in place instead of appending; stale lines are worse than missing ones.
3. Set `updated:` to today and `head:` to `git rev-parse --short HEAD`.
4. Move finished work to Done as a line that starts with its date [CCAR 18] in YYYY-MM-DD form [practice] and ends with its evidence (the command run and its result). [Anthropic harness article] Move Done items beyond the 10 newest to `archive/YYYY-MM.md`. [CCAR 18] Keep Next ordered, at most 7; the 10 and the 7 are defaults. [practice]
5. Append a decision to DECISIONS.md only when it is costly to reverse, would surprise a newcomer without its context, and was chosen over real alternatives; record date, decision, why, alternatives rejected. [D5] [CCAR 18] (mattpocock/skills, MIT: domain-modeling)
6. Write the Last session block: done, left half-done, first thing to do next.

Done when STATE.md is within 80 lines, both header lines are current, and every decision from this session that passes the step 5 gate is in DECISIONS.md. When a Stop hook blocked on a secret, replace the value with a pointer to where it lives.

## What belongs where

- Store what a fresh session cannot rediscover: goal, decisions with their reasons, dead ends, naming conventions, constraints, open questions. [CCAR 18]
- Point to specs, plans, commits and files by path or id; the repo already holds their content. Git, code and config are the source of truth for what they say. [CCAR 04] [D5] [CCAR 18] (mattpocock/skills, MIT: handoff)
- Claim "done" only with evidence; the evidence is what the next session trusts. [Anthropic harness article]
- Leave state files uncommitted until the user asks; the user decides when to commit.
- CLAUDE.md wins any conflict with the state files. [CCAR 18]
