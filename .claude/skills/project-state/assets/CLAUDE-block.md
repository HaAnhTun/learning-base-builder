<!-- project-state:begin -->
## Working agreement (project-state)
- Session state lives in `.claude/state/STATE.md`, loaded automatically at session start. Decisions and rejected options live in `.claude/state/DECISIONS.md`. This file wins any conflict with them.
- Update STATE.md at each milestone: a task finished (with its verification evidence), a decision made, before any irreversible action. Rewrite its blocks to stay within 80 lines, and record where a secret lives, never its value.
- Keep context lean: delegate verbose discovery to a subagent that returns a short answer, and carry decisions and constraints forward instead of transcripts. Details: skill `context-discipline`.
- Write every prompt and subagent brief with the task, only the relevant context, the output format and the constraints. Details: skill `prompt-craft`.
- Default to one agent. Add agents for independent, parallel, high-value work, and keep the orchestrator accountable for the plan and for errors. Details: skill `agent-orchestration`.
- Enforce high-stakes constraints with hooks or code; prompt wording alone is probabilistic.
<!-- project-state:end -->
