# Decisions
Append-only. One entry per decision: date, decision, why, alternatives rejected.

## 2026-11-24 State lives in the repo, not in Claude memory
Why: CCAR 18 (scratchpad with decision log, current state, open questions), diffable, travels with the repo. Rejected: Claude Code memory dir (machine-bound), tickets per task (too heavy for solo work).

## 2026-11-24 Hot/cold split: STATE.md (<=80 lines, auto-injected) + DECISIONS.md (read on demand) + archive/
Why: CCAR 04/18 hot vs cold state; only STATE.md costs context each session. Rejected: one file (decision log would grow and lose reasons).

## 2026-11-24 SessionStart hook injects STATE.md verbatim on startup|resume|clear|compact; CLAUDE.md block holds pointers only
Why: @import loads in full every launch and does not reduce context cost; summaries lose identifiers and decisions (CCAR 16). additionalContext capped at 10,000 chars, so STATE.md is cut at 8,000. Rejected: digest-only injection, no injection after compact.

## 2026-11-24 Stop hook blocks once per session on stale state, over-cap state, or a secret
Why: SessionEnd cannot block, so the end-of-session write is instruction-driven and the hook is the safety net; stop_hook_active prevents loops. Secrets block every time (without echoing the value). Rejected: soft nudge only, no hook.

## 2026-11-24 Hooks as exec-form `python` + args in .claude/settings.json; scripts live inside the skill folder
Why: one source, no copy to keep in sync; `python` verified on this machine. Rejected: settings.local.json (not shared), copying scripts to .claude/hooks/.

## 2026-11-24 Four skills, workspace-local; agent never commits state
Why: user wants easy audit now. Skills: project-state, context-discipline, prompt-craft, agent-orchestration. Rejected: 3 skills (merging prompt-craft), 5 skills (separate resume).

## 2026-11-24 Source tags: every rule carries [CCAR NN] or [practice]
Why: user audits rules against the course. A reviewer-fix pass once deleted all tags to dodge findings; restored and verified against the lessons. Exam trivia and version-specific numbers are left out.
