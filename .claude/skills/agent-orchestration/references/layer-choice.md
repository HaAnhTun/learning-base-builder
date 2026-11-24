# Layer choice

Open from SKILL.md section 10 when placing an instruction in CLAUDE.md, a rule, a skill, a subagent, a slash command or a hook.

## Decision

Ask who the instruction is for and how it should load. [CCAR 10] Take the first match. [practice]
1. Must be enforced even if the model ignores it (irreversible, financial, security)? Hook or code; org-wide and non-overridable: managed policy. [CCAR 05, 10, 12]
2. Must hold every session for everyone as guidance? CLAUDE.md (project file, committed). [CCAR 10]
3. Follows a file type or folder? Path-scoped rule (`.claude/rules/`) or subdirectory CLAUDE.md; either loads when a matching file is read. [CCAR 10]
4. A procedure Claude should pull in when a request matches? Skill. [CCAR 11]
5. A shortcut typed by hand? Slash command. [CCAR 11]
6. Work that should run independently, in parallel or with other permissions? Subagent. [CCAR 11]

Done when: no layer copies another layer's text (a command extends CLAUDE.md instead of duplicating it); a hard constraint may appear twice, as guidance in the prompt and as enforcement in a hook or code. [CCAR 05, 11]

## When to choose each

- CLAUDE.md: always-on facts and rules the model cannot infer. Past roughly 200 lines adherence drops, so move file-type and folder conventions into path-scoped rules or subdirectory files. Put security directives early and explicit. Team standards go in the committed project file; personal tone and shortcuts go in user or local config. Running notes belong in `project-state`. [CCAR 10]
- Skill: recurring multi-step procedures worth loading by description match. Matched by description and when_to_use, or restricted to file locations by a paths field; the user can also invoke it directly by name. Disabling model invocation is a frontmatter option: check the current skills documentation. [practice] A rule that applies everywhere is CLAUDE.md. [CCAR 11]
- Slash command: a narrow manual shortcut. Do not copy CLAUDE.md text into the command; extend it, so the two cannot drift. [CCAR 11]
- Subagent: a worker with its own context, tools and scope that reports back, where a skill is a recipe Claude follows itself. [CCAR 11] Spawn criteria: SKILL.md section 1; brief template: `prompt-craft`.
- Hook: deterministic behaviour at a lifecycle moment. A hook enforces only when it blocks: exit code 2 on a blocking event such as PreToolUse feeds its message back to Claude, while exit 1 or any other non-zero code is a non-blocking warning and the action proceeds. PostToolUse reacts after the action and cannot undo it. [CCAR 05, 12] Check the current hook documentation for which events block and how each signals. [practice] Scope test-run hooks to relevant paths. [CCAR 12]
- Keeping Claude Code's tools from reading a file (.env, secrets/): add a Read deny rule in settings.json permissions; a deny in any settings layer beats any allow, and .gitignore does not hide files. Deny does not stop a subprocess Claude runs, so for a hard guarantee add a PreToolUse hook or OS-level protection. [CCAR 10, 12]
