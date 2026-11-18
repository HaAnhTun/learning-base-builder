# 3B Quiz

> Course: Claude Certified Architect (CCAR-F) - 2026 Exam Prep · D3: Claude Code - CLAUDE.md Configuration · 9 questions · pass mark 70% · ANSWER KEY INCLUDED: show a question and its choices first, reveal the answer only after the learner replies

## Question 1

A team has a project-level CLAUDE.md committed to their repository, a user-level CLAUDE.md on each developer's machine, and a shared team config file symlinked into each project. When a developer opens Claude Code, how are these three files handled?

A. All three files are loaded simultaneously at session start and applied together; precedence only resolves direct conflicts.
B. Project-level config is loaded first; user-level and team-level configs are only loaded if the project-level file explicitly imports them.
C. Only the highest-precedence file is loaded; lower-priority files are ignored to avoid instruction conflicts.
D. Each level is loaded sequentially; later levels overwrite earlier ones so only the last-loaded file's instructions remain active.

**Answer:** A
**Explanation:** Claude Code loads all applicable CLAUDE.md files simultaneously at session start — user-level, project-level, and team-level all apply at once. They are additive by default: instructions at different levels that don't conflict both apply. Precedence only kicks in when instructions directly conflict, with project-level overriding user-level.

## Question 2

A developer adds a rule to their ~/.claude/CLAUDE.md requiring verbose response formatting for every Claude Code session. Three months later a colleague reports that their sessions are not verbose at all, even on the same project. What explains the discrepancy?

A. User-level config is personal scope — it applies only to one developer's sessions and is invisible to all other contributors.
B. User-level config requires a sync command to propagate settings to other team members' machines.
C. Project-level config automatically overrides all user-level formatting instructions, removing verbosity for everyone.
D. CLAUDE.md files are cached at session creation and do not update until the developer manually refreshes them.

**Answer:** A
**Explanation:** User-level config lives at ~/.claude/CLAUDE.md and applies only to the individual developer's sessions across all their projects. It is not visible to teammates. Project-level config, committed to source control, is the correct location for instructions that should apply consistently to all contributors.

## Question 3

A developer is troubleshooting why their Claude Code sessions produce different output than a teammate's on the same project. They want to verify which CLAUDE.md instructions are actually active. What practical verification approach does the deck describe?

A. Restart the development environment so Claude Code reloads all config files from a clean state before diagnosing.
B. Check the team's Git history to confirm the project-level CLAUDE.md was not modified since the last session.
C. Export both CLAUDE.md files as JSON, diff them programmatically, and flag any line that appears in only one file as a potential conflict.
D. Ask Claude Code which CLAUDE.md instructions it is following, review session initialization output, and test conflicting instructions explicitly.

**Answer:** D
**Explanation:** The deck describes three verification approaches: asking Claude Code directly ('What CLAUDE.md instructions are you following?'), reviewing the session initialization output to see which files were loaded, and explicitly setting conflicting instructions at different levels and confirming that project-level wins. These are especially useful when debugging inconsistent behavior between developers.

## Question 4

A team adds a CLAUDE.md file inside their /infrastructure directory specifying Terraform naming conventions and never-delete rules for live resources. The project root CLAUDE.md has a global security rule requiring all API calls to be logged. When Claude Code is working inside /infrastructure, which rules apply?

A. Only the /infrastructure CLAUDE.md applies; the root config is suspended while Claude Code works inside a subdirectory.
B. The root config overrides the /infrastructure config because project-level instructions have higher precedence than subdirectory instructions.
C. The /infrastructure rules apply first; the root rules are applied only if the subdirectory file has no instruction covering a given behavior.
D. Both the root security rule and the infrastructure-specific Terraform rules apply together when working in /infrastructure.

**Answer:** D
**Explanation:** Subdirectory CLAUDE.md files add rules on top of the parent config — they do not replace it. When Claude Code is working inside /infrastructure, both the global security rule from the root and the Terraform-specific rules from the subdirectory config are active simultaneously.

## Question 5

A team wants to enforce React hooks conventions inside /frontend without those rules affecting backend or infrastructure developers. They place a CLAUDE.md inside /frontend with hooks naming rules and component co-location requirements. What is the mechanism that scopes these rules to /frontend only?

A. The developer must run a /scope command inside the /frontend directory to register the file before it takes effect.
B. Placement is the mechanism — dropping CLAUDE.md inside /frontend causes Claude Code to load it automatically when working in that path.
C. The root CLAUDE.md must reference /frontend/CLAUDE.md explicitly using an import directive for the scoped rules to activate.
D. The /frontend CLAUDE.md must declare a scope header listing each file path it governs for Claude Code to recognize its boundaries.

**Answer:** B
**Explanation:** The scoping mechanism for subdirectory CLAUDE.md files is placement. Dropping a CLAUDE.md inside a subfolder is all that is required — Claude Code loads it automatically when operating within that directory path. No registration step, no manifest entry, and no additional configuration is needed.

## Question 6

A team lead reviews a CLAUDE.md file submitted by a new engineer. The file contains a detailed paragraph explaining what Python list comprehensions are, a note that Black handles all formatting, and a one-line bullet specifying the team's custom test coverage threshold of 85%. She approves only one of these entries. Which entry is correct to keep, and why?

A. The Python list comprehension explanation, because Claude Code benefits from explicit syntax reminders in every session.
B. The Black formatting note, because documenting existing tooling in CLAUDE.md creates a reliable redundant layer.
C. The 85% coverage threshold, because it is a repo-specific team decision Claude Code cannot know from training data.
D. All three entries, because CLAUDE.md should be comprehensive to handle cases where tools or training data are unavailable.

**Answer:** C
**Explanation:** CLAUDE.md should contain only repo-specific decisions Claude Code cannot infer from training data. The coverage threshold is a team-specific decision that must be explicitly encoded. General Python syntax knowledge (list comprehensions) is already known to Claude Code, and formatting rules duplicated from Black create conflicting sources of truth. Both should be cut.

## Question 7

An engineering manager asks her team why their Claude Code sessions seem to miss certain CLAUDE.md directives inconsistently. Upon review, the CLAUDE.md is a 2,000-word narrative document with rules embedded in paragraphs rather than bullets. According to the deck, what is the most likely reason the rules are being missed?

A. Rules in prose are harder to isolate under context pressure; concise one-directive-per-line bullets are more reliably followed.
B. Narrative CLAUDE.md files must be paired with a companion directive-only file before Claude Code will reliably act on the rules they contain.
C. Narrative documents are skipped by Claude Code unless they are scoped to a subdirectory CLAUDE.md rather than placed at the project root.
D. CLAUDE.md imposes a hard per-session token budget that silently truncates narrative content before all rules can be loaded into context.

**Answer:** A
**Explanation:** The deck teaches that verbose narrative documentation consumes context space and makes individual rules harder to identify and follow under context pressure. Concise bullet directives — one rule per line — are more reliably followed because they are harder to miss and faster to process. The recommended format is a style guide checklist, not a design document.

## Question 8

A frontend team is building a CLAUDE.md for their React monorepo. They want Claude Code to follow their CSS module conventions, approved state management library, and accessibility standards. A colleague suggests putting all of these in the root CLAUDE.md. According to the deck, where do frontend-specific directives belong and why?

A. In the root CLAUDE.md using conditional sections tagged by file extension so they only apply when editing .tsx files.
B. In a separate slash command file so frontend conventions are invoked only when the developer explicitly requests a frontend review.
C. In a frontend subdirectory CLAUDE.md, because these rules are framework-specific and only apply to that part of the codebase.
D. In the root CLAUDE.md to ensure all contributors see them regardless of which part of the repo they are editing.

**Answer:** C
**Explanation:** The deck teaches that frontend-specific rules — component naming, CSS methodology, state management, accessibility — apply only to frontend code and don't belong in the root CLAUDE.md that governs the entire repo. Scoping them to a subdirectory CLAUDE.md keeps them relevant to the context where they apply and avoids polluting the root with framework-specific rules.

## Question 9

A backend team's CLAUDE.md includes their API versioning strategy, error response format, and ORM-vs-raw-SQL policy. A new hire notices that it also includes a rule stating 'follow REST best practices' and another reminding Claude Code how HTTP status codes work. According to the deck's guidance, which entries should be removed?

A. The REST note and HTTP status reminder, because Claude Code already knows general web standards from training data.
B. The ORM-vs-raw-SQL policy, because the choice is self-evident from the existing codebase and need not be restated.
C. The API versioning strategy, because framework conventions automatically handle versioning and repeating it in CLAUDE.md is redundant.
D. The error response format, because Claude Code draws on a universal error-format convention from training data unless a linter rule overrides it.

**Answer:** A
**Explanation:** The deck's backend pattern covers project-specific rules: this project's API design choices, its database query policy, and its error response format. General knowledge like REST conventions and HTTP semantics is something Claude Code already knows from training. Encoding it wastes context tokens and adds noise without adding value.
