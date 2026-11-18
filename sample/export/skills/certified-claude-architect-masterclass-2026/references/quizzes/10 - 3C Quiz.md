# 3C Quiz

> Course: Claude Certified Architect (CCAR-F) - 2026 Exam Prep · D3: Claude Code - Slash Commands, Skills & Subagents · 13 questions · pass mark 70% · ANSWER KEY INCLUDED: show a question and its choices first, reveal the answer only after the learner replies

## Question 1

A developer creates a file named deploy-review.md and places it in .claude/commands/ at the project root. She then runs /deploy-review in a Claude Code session. According to the deck, how does Claude Code determine the command keyword, and what does it do when the command is invoked?

A. The command keyword comes from a name field inside the Markdown file's YAML frontmatter block, not from the filename on disk.
B. Claude Code prompts the developer to choose a keyword alias on the first invocation and then persists that alias mapping for future sessions.
C. The filename becomes the keyword with no registration needed; invoking it runs the Markdown content as a prompt.
D. The filename sets the keyword, but the command must also be listed in a commands.json registry file before Claude Code will activate it.

**Answer:** C
**Explanation:** Custom slash command keywords are set entirely by the filename — no registration or configuration is required. When the command is invoked, Claude Code reads the Markdown file and treats its contents as a prompt for that session. Renaming the file changes the command keyword.

## Question 2

A developer wants to create a slash command that her entire 12-person team can access as soon as they pull the latest changes from the repo, with no extra steps required. According to the deck, which approach accomplishes this?

A. Put the file in ~/.claude/commands/ on a shared network drive so team members can each copy it to their local home directories.
B. Add the command file to the project README and provide step-by-step instructions for each team member to create it in their local environment.
C. Commit the file to .claude/commands/ in version control — every developer who pulls the repo has it automatically.
D. Add a reference to the command in CLAUDE.md so Claude Code registers it as a shared project-wide command available to all contributors.

**Answer:** C
**Explanation:** Project-level commands live in .claude/commands/ inside the project and are committed to version control. Every developer who clones or pulls the repo has access automatically — no manual sharing or configuration is required. User-level commands in ~/.claude/commands/ are personal and do not leave the individual's machine.

## Question 3

A team's command library contains a single command called /do-everything that reviews the pull request, runs the test suite, and generates a deployment summary all in one template. Developers report inconsistent output across runs. According to the deck, what is the core design problem and the recommended fix?

A. The command template exceeds Claude Code's context window limit and must be broken into sequential shorter files that each load and run separately on invocation.
B. The command file is missing a required YAML frontmatter block that tells Claude Code which task to prioritize when multiple are listed in the template.
C. The command logic is correct but the file must be relocated from .claude/commands/ to ~/.claude/commands/ to prevent unintended team invocations.
D. The template covers too many tasks; splitting into /review-pr, /run-tests, and /generate-deployment-summary produces consistent, predictable output.

**Answer:** D
**Explanation:** The deck's primary design rule for slash commands is narrow scope: each command should do exactly one clearly defined task. A command that tries to review, test, and deploy in one template gives Claude conflicting signals, produces unpredictable output, and is hard to debug. The fix is to split it into focused, composable commands.

## Question 4

A platform team wants to ensure that every developer across a 500-person organization has access to a /review-for-compliance command without relying on each team to copy the file into their own repos. According to the deck, which distribution mechanism enables this?

A. Posting the command file in a shared internal documentation system and linking it from the onboarding guide ensures all developers have access.
B. Committing the command to a single shared monorepo and requiring all teams to add it as a git submodule propagates it organization-wide.
C. Each developer must copy the command file to their ~/.claude/commands/ directory using a bootstrap script run at onboarding.
D. Managed settings configured by administrators push the command to every user in the organization automatically without per-repo setup.

**Answer:** D
**Explanation:** For organization-wide distribution, managed settings allow administrators to configure commands centrally and push them to every user automatically. Users cannot accidentally delete or override these org-level commands. This is distinct from project-level version control distribution, which requires each repo to include the file.

## Question 5

A developer is deciding how to handle a recurring 5-step code review workflow that every team member runs at least twice a day. Currently each person re-describes the steps inline at the start of every session. She is considering either a slash command or a skill. According to the deck's build decision framework, what determines whether this workflow warrants a skill?

A. A skill is appropriate only when the workflow must fire completely invisibly so individual team members remain unaware that it has executed.
B. High frequency, high complexity, and high reusability all justify a skill; a low score on any one factor suggests a simpler mechanism.
C. The workflow qualifies for a skill only when it is designed to fire on an event-based trigger rather than a user-typed phrase in conversation.
D. A skill is warranted whenever a workflow recurs, since frequent repetition by itself is enough to justify building one.

**Answer:** B
**Explanation:** The deck's framework evaluates three factors: frequency (does the workflow appear often enough to justify formal definition), complexity (is it multi-step enough that a reusable template adds value), and reusability (will it benefit more than one user or session). A workflow that scores high on all three is a strong skill candidate.

## Question 6

A team lead is choosing between a skill and a subagent for a new workflow. The workflow needs to produce a structured report autonomously, working through multiple files independently and returning results when complete. According to the deck, which mechanism is the correct choice and why?

A. A slash command with $ARGUMENTS, because it provides the flexibility to pass file references at invocation time for independent processing.
B. A skill, because skills are specifically designed to run multi-step workflows autonomously without requiring user input mid-task.
C. A CLAUDE.md rule, because always-on configuration gives the workflow unconditional access to the files it needs across all sessions.
D. A subagent, because it is an autonomous worker with its own context and tools that runs independently and reports back when done.

**Answer:** D
**Explanation:** The deck distinguishes skills as passive instruction templates that Claude Code follows when a trigger fires — the skill is the recipe, not a worker. Subagents are active autonomous processes with their own context, tools, and scope that run independently and report back when done. A workflow that must run autonomously and independently belongs with a subagent.

## Question 7

An architect is designing a Claude Code workflow where a parent agent decomposes a complex codebase audit into smaller tasks and delegates each to a separate session. When a subagent is spawned via the Agent tool, which statement correctly describes what context it receives from the parent?

A. The subagent inherits all files the parent has read, but not the parent's tool call history.
B. The subagent shares a read-only snapshot of the parent's context window for the task duration.
C. The subagent starts with an empty context window; the parent must explicitly pass what it needs.
D. The subagent receives a copy of the parent's full conversation history up to the point of spawning.

**Answer:** C
**Explanation:** Claude Code subagents start with an empty context window. The parent must explicitly pass every piece of information the subagent needs. Nothing from the parent's conversation, loaded files, or prior work transfers automatically — context isolation is a deliberate architectural feature that prevents context bleed.

## Question 8

A parent agent spawns a subagent to analyze API surface coverage across a microservices codebase. The subagent returns a two-paragraph prose summary. The parent agent tries to process the result but produces inconsistent downstream behavior across runs. What design flaw does this scenario illustrate?

A. The subagent was spawned using the /agents command instead of the Agent tool, which produces unstructured output by default.
B. The subagent returned an undefined output format — natural language prose cannot be reliably parsed by the parent agent.
C. The subagent was given too much context, causing its context window to overflow and truncate the response.
D. The parent agent failed to pass the correct tool permissions, preventing the subagent from reading all relevant files.

**Answer:** B
**Explanation:** When a subagent's output format is not explicitly defined, it typically returns natural language prose. Prose cannot be reliably parsed by a parent agent and produces inconsistent results across runs. The fix is specifying an exact schema — JSON fields, named sections, and success/failure indicators — in the task description before spawning.

## Question 9

A workflow architect is deciding whether to delegate a quick variable rename across a single file to a subagent. The rename is unambiguous and the file is already in the parent's context. Which principle from the deck should guide the decision?

A. A subagent should always be used for file edits to keep the parent's context window available for orchestration work.
B. The task should stay inline; delegation overhead exceeds the value for a simple, context-dependent change.
C. The decision depends on parent write permissions; delegate when permissions are sufficient, otherwise spawn a subagent.
D. Subagents should be preferred for any single-file task to enforce context isolation consistently across all operations.

**Answer:** B
**Explanation:** Delegation overhead — the cost of spawning, context-loading, coordinating, and processing results — is real. For simple, fast tasks that the parent can handle inline and that require the parent's full context, delegation overhead exceeds the value gained. Subagents are appropriate for work that is truly independent, benefits from parallel execution, or needs scope isolation.

## Question 10

A developer is about to ask Claude Code to rename a widely used interface type across 40 source files. Before typing the request, they want Claude to show the full list of affected files and its approach before touching anything. What is the most reliable way to trigger this behavior?

A. Claude automatically enters plan mode for any refactor spanning more than ten files, so no explicit trigger is needed.
B. Add the phrase 'show me the plan first' at the end of the request; Claude will detect this and enter plan mode reliably.
C. Type /plan before the request; Claude enters read-only mode, produces a proposal, and waits for approval.
D. Open a new session and describe only the intent; Claude defaults to planning before executing in all fresh sessions.

**Answer:** C
**Explanation:** The explicit /plan command is the most reliable trigger for plan mode. It tells Claude to enter a read-only thinking phase, produce an ordered proposal listing steps, files, and risks, and wait for approval before writing anything. Relying on implicit detection is less predictable and may result in direct execution without a proposal.

## Question 11

A Claude Code plan for a schema migration lists 22 ordered steps and references files by category ('the models directory') rather than by explicit name. A developer is reviewing it before approving. According to the deck, what problems should the developer flag before approving?

A. The developer should approve the plan and let execution surface any missing files, then re-plan from those findings.
B. The plan is fine; any plan that lists over ten steps with named categories demonstrates sufficient detail for a large refactor.
C. The plan is too long to review and uses vague category references instead of explicit file names; both need correction.
D. Only the vague file references matter; step count does not affect plan reviewability according to the deck.

**Answer:** C
**Explanation:** A well-formed plan should list ordered discrete steps (five to eight is the reviewable sweet spot), name every file explicitly rather than using vague category references, and call out risks and assumptions. Vague file references and excessive step counts are both signals to push back and ask for a more specific plan before approving.

## Question 12

Partway through executing an approved plan, Claude discovers that a configuration file the plan depended on does not exist at the expected path. Instead of stopping, Claude silently adjusts its approach and continues writing code. According to the deck, what failure is this and how should it be addressed?

A. Claude silently improvised; the fix is instructing Claude to stop and surface any deviation before continuing.
B. A PostToolUse hook should be used to flag writes to files that were not listed in the approved plan.
C. The plan should have been shorter; a plan with fewer steps would not have exposed the missing file assumption mid-execution.
D. A full re-plan is unnecessary here; minor unexpected file states should always be patched inline without interrupting execution.

**Answer:** A
**Explanation:** Silent improvisation — where Claude encounters a divergence from the plan and adapts without surfacing it — is the most common plan-mode failure. The result is code that does not match the approved plan. The fix is a behavioral instruction before execution begins: tell Claude to stop and explicitly surface any divergence rather than working around it.

## Question 13

A team wants to increase reliability on a complex database migration plan by having a subagent first inspect the schema and return findings, then using those findings to build the plan, and adding a pre-execution check on each step before Claude runs it. Which plan-mode pairing pattern does this describe?

A. This is the staged human review pattern, where the developer approves after each individual step rather than once at the start of the plan.
B. Using subagents for investigation bypasses plan mode entirely; plan mode and subagent investigation are mutually exclusive workflows.
C. A subagent gathers context before planning, and pre-execution hooks validate each step — this describes plan-mode pairing.
D. Pre-execution hooks replace the approval gate in this pattern; once hooks are in place the developer no longer needs to review the plan.

**Answer:** C
**Explanation:** Plan-mode pairing combines plan mode with other mechanisms for higher reliability. Using a subagent to investigate before planning keeps investigation and planning separate, resulting in a richer information base. Adding pre-execution hooks validates steps before Claude runs them. These two layers (subagent investigation + hook validation) stack with human approval to catch different failure classes.
