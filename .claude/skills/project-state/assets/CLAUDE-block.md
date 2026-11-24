<!-- project-state:begin -->
## Working agreement (project-state)
- Session state lives in `.claude/state/STATE.md`, loaded automatically at session start. Decisions and rejected options live in `.claude/state/DECISIONS.md`. This file wins any conflict with them.
- Update STATE.md at each milestone: a task finished (with its verification evidence), a decision made, before any irreversible action. Rewrite its blocks to stay within 80 lines, and record where a secret lives, never its value.
- Enforce high-stakes constraints with hooks or code; prompt wording alone is probabilistic.
<!-- project-state:end -->
