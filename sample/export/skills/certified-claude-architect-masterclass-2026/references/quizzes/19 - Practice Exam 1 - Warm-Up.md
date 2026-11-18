# Practice Exam 1 - Warm-Up

> Course: Claude Certified Architect (CCAR-F) - 2026 Exam Prep · Practice Exams · 60 questions · pass mark 72% · ANSWER KEY INCLUDED: show a question and its choices first, reveal the answer only after the learner replies

## Question 1 [D1]

A Code Generation team has a task: rename a variable consistently across a codebase. Which architectural class fits BEST?

A. An agent that decides which occurrences to rename based on context
B. A deterministic workflow with find-and-replace as a fixed step
C. A conversational chatbot that asks the developer about each occurrence
D. A multi-agent system with one agent per file

**Answer:** B
**Explanation:** Consistent rename across a codebase is a deterministic operation — find every reference, replace it. Tooling exists for this and a workflow wraps the tool. No runtime decisions are required; agentic adaptation has no role.
**Why not A:** The requirement is consistent rename across all occurrences — there is no decision about which to rename. Adding agentic logic introduces variance that could miss occurrences a deterministic find-replace would catch.
**Why not C:** Per-occurrence prompting is unworkable for any non-trivial codebase. Deterministic refactoring tools are the established right answer for consistent renames.
**Why not D:** Per-file agents add coordination cost without benefit. A single workflow runs the rename across files; multi-agent is justified by parallelism in heavier tasks, not by file count alone.

## Question 2 [D1]

A Code Generation team's programmatic guardrail blocks dangerous operations but produces unclear error messages, frustrating the agent and users. Which CCA-F-consistent design improvement MOST directly applies?

A. Make guardrail error messages informative — explain what was blocked, why, and what alternative actions are permitted
B. Remove the guardrail in order to eliminate the error messages
C. Make the guardrail silent so that it blocks the action without telling the agent, since hiding the block keeps the agent from trying to reason its way around the rule
D. Just increase the overall strictness of the guardrail across the board

**Answer:** A
**Explanation:** Unclear guardrail errors produce frustration and ineffective agent recovery. CCA-F guidance favors informative error messages that explain the block and suggest alternatives. The agent can then replan within the allowed scope rather than retrying the blocked action.
**Why not B:** Removing the guardrail eliminates the protection. The fix is better error messages, not removal.
**Why not C:** Silent blocks leave the agent confused about what failed. CCA-F guidance favors informative communication, not silence.
**Why not D:** Increased strictness worsens user frustration without improving message clarity. The fix is message quality, not strictness.

## Question 3 [D4]

A Customer Support Agent's prompt says 'Verify the customer's identity before sharing account details.' The model sometimes shares partial details without verification. Which change BEST hardens the rule?

A. Lower temperature so the model is less likely to share details prematurely, since a calmer sampler tends to withhold sensitive account data by default
B. Add 'verify thoroughly and completely' to the existing prompt so the model takes verification seriously
C. Specify the verification steps — confirm full name plus last 4 of SSN plus billing ZIP — and refuse account details until all three match
D. Wrap account details in an <account> XML tag in the response

**Answer:** C
**Explanation:** 'Verify identity' is interpretable; the model can treat partial signals as sufficient. Enumerating the three required match conditions and the refusal default until all three match converts the rule into a structural gate the model can enforce reliably.
**Why not A:** Determinism does not impose a verification protocol. The model deterministically shares partial details on the same unstated rule.
**Why not B:** Adverbs do not introduce rules. The model still infers what 'thorough verification' is, with the same variance.
**Why not D:** Output tagging does not prevent sharing; it only labels what was already shared.

## Question 4 [D1]

A Multi-Agent Research team has a workflow that retrieves and summarizes news on five topics every morning. Stakeholders want to occasionally add new topics that are not in the predetermined set. Which architectural change is MOST consistent with CCA-F guidance?

A. Replace the workflow with a conversational chatbot that takes topic requests
B. Replace the workflow entirely with an agent so it can go off and discover brand-new topics entirely on its own at runtime
C. Run the workflow five times in parallel for the original topics and add a new workflow for new topics
D. Add a parameter to the workflow so the topic list can be configured per run, keeping the workflow class

**Answer:** D
**Explanation:** Adding configurable inputs to a workflow preserves the workflow class while supporting new topics. The fetch-summarize sequence is still fixed; only the topic input varies. A parameterized workflow is the simplest change that meets the requirement without unjustified architectural escalation.
**Why not A:** Conversational does not deliver scheduled morning summaries — it responds to user turns. The requirement is automated delivery; conversational is the wrong class.
**Why not B:** Stakeholders supply the topics; the agent does not need to discover them. Replacing the workflow with an agent adds discovery capability that the requirement does not ask for, paying agentic cost for no benefit.
**Why not C:** Forking the workflow per topic group is unnecessary duplication. A single parameterized workflow handles both groups with one code path; duplication is cost without benefit.

## Question 5 [D1]

A Customer Support Agent team is asked: under which condition is a conversational system the right architectural fit?

A. When the team wants to standardize on using Claude's single largest available model for it
B. When the feature is response-only — no tool use, no state changes, no iteration required
C. When the team wants to log every user message
D. When the team wants the feature to take action quickly

**Answer:** B
**Explanation:** Conversational systems fit when the feature is purely response-driven: take a user input, return an answer, no external action. FAQ-style answers, definitions, and tone-shaping fit; anything requiring tool use or state changes does not.
**Why not A:** Model choice is independent of architectural class. Conversational and agentic features can both use any Claude model; this option does not describe a conversational-fit condition.
**Why not C:** Logging is achievable in all classes. Log requirements do not determine architectural class; both workflows and agents can produce equivalent message logs.
**Why not D:** Taking action quickly suggests external operations, which the conversational class does not perform. Speed is a property of both classes; action-taking is not part of conversational class fit.

## Question 6 [D2]

A Multi-Agent Research team's MCP server exposes 30 tools. The team wants to keep the server maintainable as the tool set grows. Which architectural practice BEST supports long-term maintenance?

A. Limit the server to 10 tools and create additional servers for additional tools
B. Put all 30 tool definitions in a single file so the server has one source of truth
C. Have each tool implement its own logging, error formatting, and input validation independently for maximum flexibility, so every domain team can tune its tools' behavior without being constrained by a shared handler's conventions
D. Group tools into modules by domain (search, analysis, export) and register each module's tools through a shared handler with consistent error semantics

**Answer:** D
**Explanation:** Modular grouping with shared handler conventions keeps a growing tool set comprehensible: per-domain modules group related tools, and shared handler scaffolding ensures consistent error semantics, logging, and validation across tools. This scales to dozens of tools without per-tool boilerplate drift.
**Why not A:** A fixed 10-tool cap is an arbitrary constraint that pushes complexity into multi-server orchestration unnecessarily. Modular code organization within one server scales much further than 10 tools without architectural fragmentation.
**Why not B:** A single file scales poorly past about a dozen tools — review burden, merge conflicts, and inconsistency creep all increase. Modular grouping with shared conventions is the standard mitigation.
**Why not C:** Per-tool independent implementations produce drift in error messages, log fields, and validation strictness — exactly the maintainability problem the team is trying to avoid. Shared handler scaffolding is the antidote.

## Question 7 [D2]

A Customer Support Agent's host application uses an MCP client to connect to a server. The team asks how the client surfaces server-exposed prompts to the user. Which behavior is the typical pattern?

A. Prompts cannot be surfaced to the user — they are server-internal only
B. Prompts are surfaced to the model on every turn so the model can use them autonomously, treating each prompt as just another capability it may invoke whenever it judges the template relevant to the current task
C. Prompts are emailed to the user when the session starts, so the user receives the catalog out of band and selects from it later
D. The host application renders prompts in a UI surface like a slash menu or command palette, letting the user pick a prompt and supply its arguments before the prompt's content enters the conversation

**Answer:** D
**Explanation:** Prompts in MCP are user-driven primitives, and the standard pattern is for the host application to render them in a UI affordance — slash menu, command palette, sidebar — where the user can browse, pick, and parameterize. Once invoked, the prompt's content (often a template with the user's arguments) enters the conversation as a turn. This places initiation with the user, which is the whole reason prompts exist as a distinct primitive.
**Why not A:** Prompts are designed for user-facing exposure. Treating them as server-internal contradicts the protocol's intent.
**Why not B:** Auto-surfacing to the model collapses prompts into tool-like semantics, defeating the user-driven invocation that makes prompts a distinct primitive. Prompts belong in user-facing UI surfaces.
**Why not C:** There is no email mechanism in MCP. Prompts are surfaced in the host's UI.

## Question 8 [D5]

A CI/CD Integration agent's vulnerability scanner returns 0 issues. The scanner's last update was 18 months ago. Which D5 reliability concern is MOST relevant?

A. Stale scanner definitions can return false negatives — empty results may reflect outdated knowledge, not absence of issues
B. Treat 0 issues as conclusive, since vulnerability data is static and an 18-month-old definition set is just as valid as a current one for this purpose
C. Re-run the scanner with the same definitions to confirm
D. Lower the scanner's reporting threshold so more candidate issues surface

**Answer:** A
**Explanation:** A scanner is only as good as its definitions; 18 months of un-updated definitions miss every vulnerability discovered in that window. The empty result reflects the scanner's blind spots more than the codebase's actual safety. CCA-F architects check freshness of the data sources behind absence claims before treating absence as evidence.
**Why not B:** Vulnerability databases evolve daily. Stale definitions catastrophically miss the latest threats. Treating 0 as conclusive in this context is the high-risk failure mode.
**Why not C:** Re-running with the same stale definitions returns the same 0. Freshness is the gap; repetition cannot bridge it.
**Why not D:** Lowering thresholds in stale definitions still cannot detect vulnerabilities the scanner does not know about. The fix is freshness, not threshold tuning.

## Question 9 [D2]

A CI/CD Integration MCP server exposes a `run_shell` tool. A reviewer flags it as too permissive. Which hardening change is MOST important before this server ships to production?

A. Add a description noting that the agent should only use safe commands
B. Replace the open shell with an allowlist of permitted commands and validated argument shapes, enforced server-side before any execution
C. Log every shell command for post-hoc review so operators can audit exactly what the agent executed and catch any dangerous invocations after the session completes
D. Require user confirmation before each shell invocation in the client UI, so a human reviews and approves every command the agent proposes to run, putting a person in the loop on the riskiest possible tool

**Answer:** B
**Explanation:** Arbitrary shell execution is the canonical example of a too-broad MCP capability. The mitigation is an allowlist enforced server-side: only specific commands with specific argument shapes are permitted, and every invocation is validated against the list before execution. This is the difference between a shippable production tool and an arbitrary RCE primitive.
**Why not A:** Description-level guidance does not constrain what the tool can actually execute — a confused or prompt-injected agent will issue dangerous commands regardless. Enforcement belongs server-side.
**Why not C:** Logging is a detective control — it tells you after the fact what happened. The reviewer's concern is preventive: that the tool can execute too much. Allowlisting prevents; logging only records.
**Why not D:** User confirmation can complement allowlisting but does not replace it — users approve too quickly under time pressure and a single bad confirmation can be catastrophic. Server-side allowlisting is the foundational preventive control.

## Question 10 [D3]

A Customer Support Agent team wants Claude Code's every tool call logged to a central file with timestamp and arguments. Which hook BEST fits?

A. A PostToolUse hook that logs tool call details to the file and exits 0
B. A PreToolUse hook that captures the call details and exits with code 2, since blocking is how the hook ensures it sees and records every tool invocation
C. A Stop hook, since it logs activity neatly at the end of each task and gives one consolidated record rather than scattered per-call entries
D. Skip hooks entirely, since Claude Code already logs every tool call by default to /var/log/claude with timestamps and arguments included

**Answer:** A
**Explanation:** PostToolUse fires after every tool call with details available. Logging plus exit 0 produces an auditable trail without blocking. This is one of the most common documented hook patterns.
**Why not B:** Exit 2 blocks every tool call. The team wants to log, not block.
**Why not C:** Stop fires at task completion, not per tool call. Per-call logging needs PostToolUse.
**Why not D:** Claude Code does not log tool calls to /var/log/claude by default; no such default logging exists. Centralized per-call logging has to be built, and a PostToolUse hook is the documented mechanism for it.

## Question 11 [D4]

A Multi-Agent Research orchestrator prompt says 'Combine subagent findings into a final report.' Final reports omit some findings without explanation. Which change BEST ensures every finding appears?

A. Lower temperature to reduce the omission variance so the same findings survive each run
B. Increase max_tokens so all findings have room to fit, since omissions are caused by the model running out of output space on long reports
C. Require: enumerate every finding ID in an appendix, mark each as included/excluded with a one-sentence rationale
D. Concatenate all subagent outputs verbatim so nothing can be dropped in synthesis

**Answer:** C
**Explanation:** Omission without explanation comes from 'combine' being underspecified. Requiring an ID-by-ID accounting plus rationale for exclusion makes coverage auditable: missing findings are visible, and the model must justify each exclusion rather than dropping them silently.
**Why not A:** Determinism does not impose coverage. The model deterministically omits the same findings.
**Why not B:** Token capacity is rarely the cause of omission — the model still chooses to omit. Larger budgets do not impose coverage rules.
**Why not D:** Verbatim concatenation eliminates synthesis entirely — and that is the orchestrator's job. The fix is to add coverage rules to synthesis, not to skip it.

## Question 12 [D5]

A Code Generation agent escalates when a generated patch fails its test suite three times in a row. The team observes the agent's recent failed patches sometimes contain partial progress. Which adjustment to the handoff BEST captures this?

A. Discard the failed patches and pass only the original task, since a clean restart avoids confusing the reviewer with broken code
B. Include the most recent failed patch and the test failure log in the structured handoff
C. Auto-revert the failed patches and re-run silently
D. Pass only the running count of failed attempts to the reviewer queue

**Answer:** B
**Explanation:** A reviewer often needs to see the work-in-progress to decide whether to refine, redirect, or start over. Including the most recent patch and the failure log preserves the agent's progress in the handoff so the human can build on it. Without these fields the reviewer starts from scratch and the agent's effort is wasted.
**Why not A:** Discarding the work loses signal about where the agent got stuck. The reviewer has to re-derive what already failed; the agent's attempts are diagnostic data.
**Why not C:** Auto-revert delays human input that the trigger demands. After three failures the trigger has fired specifically because the agent is unable to make progress.
**Why not D:** A count without content is not actionable. The reviewer needs to see what was attempted to decide what to do.

## Question 13 [D1]

A Data Extraction agent processes batches over multiple sessions. Which BEST describes when external memory is the right fit per CCA-F guidance?

A. When state must persist beyond a single session or grow beyond what fits in the context window
B. Whenever the team happens to have database infrastructure available, since the presence of a database is what makes external memory the natural choice
C. Only when the system is running on the largest Claude model
D. Never, because in-context memory handles all of the state

**Answer:** A
**Explanation:** External memory fits when durability (cross-session) or scale (beyond context window) is required. CCA-F guidance favors external memory for these properties; in-context cannot satisfy them. Single-session state can use either, with retrieval overhead favoring in-context.
**Why not B:** Infrastructure availability is not the design driver. The driver is durability and scale needs; matching to needs is the framework.
**Why not C:** Model choice is independent of memory choice. External memory fits durability/scale needs regardless of model.
**Why not D:** In-context cannot handle durable or large state. CCA-F guidance favors external memory for these cases; never-external misses the framework.

## Question 14 [D1]

A Data Extraction agent is tasked to extract all line items from quarterly filings and store them as audited records. Midway, a required source API returns a permanent schema-change error. The agent replans, finds a looser scraping path that succeeds, and completes, but the records now skip the mandatory audit validation. An architect reviewing the incident must identify the core replanning defect. What is the MOST accurate diagnosis?

A. The agent should never replan after a tool error; it should halt immediately and escalate every failure to a human reviewer
B. The replan satisfied the immediate obstacle but was not validated against the original goal constraint requiring audited records
C. The agent misclassified the error; a permanent schema-change error should have been retried with exponential backoff until it cleared
D. The agent used in-context memory for the audit records when it should have used semantic memory for similarity recall

**Answer:** B
**Explanation:** Replanning must be checked against original goal constraints; here the new plan resolved the API failure but silently dropped the mandatory audit-validation requirement. A non-negotiable constraint like audit validation should also be programmatically enforced so no replan can bypass it, and a permanent error should escalate rather than be routed around.
**Why not A:** Blanket halting destroys the adaptivity that justifies an agent and floods humans with recoverable errors. The defect is unconstrained replanning, not replanning itself.
**Why not C:** Exponential backoff is for transient errors; retrying a permanent schema change never succeeds and wastes resources. This misreads the error class and ignores the constraint-violation issue.
**Why not D:** Memory type is irrelevant to the failure; the records were stored but skipped validation. Semantic memory addresses similarity retrieval, not constraint enforcement.

## Question 15 [D4]

A CI/CD Integration prompt asks Claude to recommend whether to merge a PR. Recommendations are sometimes 'merge' and sometimes 'consider merging.' Reviewers want a binary decision. Which change BEST enforces a binary verdict?

A. Add 'be decisive and commit to a single verdict' to the prompt so it stops hedging
B. Lower temperature to 0 so the recommendation is more confident, since a deterministic verdict reads as decisive and that is what reviewers want
C. Require the response to end with exactly one of: VERDICT: MERGE or VERDICT: HOLD — with no other terminal phrasing allowed
D. Use prefilling to start the response with 'I recommend' so it opens decisively

**Answer:** C
**Explanation:** The hedging comes from the absence of a binary output rule. Specifying an exact terminal phrase from a two-option set converts the recommendation into a parseable binary decision that CI can act on programmatically, with no ambiguity.
**Why not A:** Decisiveness adjective does not enumerate the allowed verdict set.
**Why not B:** Temperature does not introduce a binary rule. The model deterministically hedges with low temperature too.
**Why not D:** Prefilling anchors the opening but does not constrain the terminal verdict — hedging can still appear later.

## Question 16 [D2]

A Customer Support Agent orchestrator has 12 tools today. The team wants to know the most important signal that they're approaching the partitioning threshold. Which observable signal BEST indicates impending degradation?

A. The raw number of tools exceeds ten, which the team adopts as a hard rule so that partitioning is triggered by a simple count anyone can check without inspecting traces
B. Total tokens spent on the tool definitions exceeds five thousand, which the team can measure precisely and treat as the clean numeric tripwire for when the catalog has grown too large to route reliably
C. The orchestrator starts making wrong tool selections, redundant calls (calling the same tool twice for the same intent), or routing-drift across similar queries — all observable in traces
D. The orchestrator's average end-to-end response time increases, since a slower agent is the most visible symptom that the growing tool catalog has started to overwhelm the single routing step

**Answer:** C
**Explanation:** The empirical signals of tool-count overload are wrong selections, redundant calls (the model picks the same tool twice because it can't tell which is right), and routing drift (similar queries produce different selections). All are observable in traces. When these signals appear, the orchestrator's tool catalog has outgrown reliable single-agent selection and partitioning becomes the right move.
**Why not A:** No hard rule exists at 10 tools — the threshold is empirical and depends on tool overlap. Trace signals beat numeric rules.
**Why not B:** Token cost is a related concern but not the primary signal — selection quality degrades before token cost becomes a problem. Trace-based selection signals are earlier and more meaningful.
**Why not D:** Latency is affected by other factors (slow tools, queueing). Selection-quality signals in traces are more diagnostic of tool-count overload.

## Question 17 [D3]

A CI step running `claude -p` with --dangerously-skip-permissions needs the ANTHROPIC_API_KEY to be available. What is the recommended way to provide this in a CI environment?

A. Hardcode the API key in the CI pipeline YAML file for simplicity, since CI configurations are typically not public
B. Store in CI secret management; inject as ANTHROPIC_API_KEY at runtime
C. Pass the API key as a -p argument: `claude -p 'API_KEY=sk-... Review this code'`
D. Run `claude login` before the -p step to authenticate interactively and cache credentials for subsequent runs

**Answer:** B
**Explanation:** CI secret management systems (GitHub Actions secrets, GitLab CI variables, AWS Secrets Manager, HashiCorp Vault, etc.) are designed for this purpose: secrets are stored encrypted, access-controlled, and injected as environment variables at runtime without appearing in logs or configuration files. ANTHROPIC_API_KEY is the environment variable Claude Code reads for authentication.
**Why not A:** Hardcoding API keys in CI configuration files is a security risk — YAML files are often committed to version control and may be accessible to a broader audience than intended. CI secret management is the correct approach.
**Why not C:** Embedding the API key in the -p argument exposes it in process lists, CI logs, and shell history. The environment variable mechanism is the secure approach.
**Why not D:** Interactive login is not viable in CI — there is no human to complete the authentication flow. Environment variable injection of ANTHROPIC_API_KEY is the correct non-interactive authentication method.

## Question 18 [D1]

A Multi-Agent Research orchestrator is asked to decompose a task with both research and writing concerns. Which decomposition shape is MOST consistent with CCA-F guidance?

A. One single combined subagent that performs both the research work and all of the writing together within just one single combined call
B. Separate subagents for research and writing because they require different capabilities and operate on different inputs
C. Many small subagents each handling one paragraph
D. One subagent doing research and the orchestrator doing all writing

**Answer:** B
**Explanation:** Research and writing are distinct concerns with different inputs (sources versus structured findings) and different capabilities (search versus generation). CCA-F guidance favors decomposition by concern when capabilities differ — each subagent specializes, and the orchestrator handles the handoff between them.
**Why not A:** Combining distinct concerns in one subagent loses specialization. The two phases have different inputs and different success criteria; combining them weakens both.
**Why not C:** Per-paragraph subagents over-decompose — paragraphs are too small to carry research or writing concerns independently. The natural decomposition is by phase, not by output paragraph.
**Why not D:** The orchestrator's role is coordination, not direct content production. Pushing writing into the orchestrator violates the role boundary and conflates orchestration with execution.

## Question 19 [D1]

A Customer Support Agent team has a decomposition that produces correct outcomes but with high latency. Which decomposition adjustment MOST likely improves latency without sacrificing correctness?

A. Reduce the model temperature to make subagents faster
B. Combine every one of the separate subtasks together into one single very large subtask instead
C. Identify independent subtasks and run them in parallel rather than sequentially
D. Use a smaller model for slow subagents

**Answer:** C
**Explanation:** Latency improves when independent subtasks run in parallel rather than sequentially. CCA-F guidance distinguishes truly independent subtasks (parallel) from dependent ones (sequential); identifying parallel-eligible subtasks is the standard latency optimization.
**Why not A:** Temperature affects sampling, not wall-clock time. Lower temperature does not reduce latency; the latency lever is parallelism on independent subtasks.
**Why not B:** One large subtask loses the controllability and recovery benefits of decomposition. Latency may or may not improve depending on overhead; correctness can degrade because intermediate validation is lost.
**Why not D:** Smaller models may run faster per call but can produce lower-quality output that triggers retries — net latency may not improve. The structural lever is parallelism, which is more reliable than model swapping.

## Question 20 [D4]

A Customer Support Agent's tool-use extraction has a 'priority' enum [low, medium, high]. The business adds 'urgent' as a fourth level. Which migration approach MOST aligned with schema-evolution discipline?

A. Add 'urgent' to the enum, regenerate the schema, update few-shot examples to demonstrate when urgent applies, and run the test dataset to confirm prior cases still classify correctly
B. Add the new 'urgent' value to the enum silently and deploy it, since a single additive enum value is low-risk and cannot affect how existing tickets are classified
C. Keep the three existing levels and use 'high' as a proxy for urgent, since reusing an existing value avoids a schema change, keeps the most pressing tickets flagged, and leaves the consumers that depend on the schema untouched
D. Lower temperature for accurate urgent classification, since a more deterministic setting helps the model assign the new urgency level correctly across tickets

**Answer:** A
**Explanation:** Enum extension is a typical evolution: add to enum, update examples to teach when to use, regression-test prior cases. The combination ensures the new value is recognized, used appropriately, and doesn't disrupt prior categorizations. This is the schema-as-code discipline.
**Why not B:** Skips regression testing.
**Why not C:** Loses semantic resolution.
**Why not D:** Determinism doesn't introduce new categories.

## Question 21 [D4]

A CI/CD Integration tool uses few-shot examples to teach Claude to classify build failures into three categories: configuration errors, test failures, and dependency issues. Examples cover all three categories, but Claude misclassifies failures that span two categories. Which example design addition BEST addresses this?

A. Add one or more examples where a failure spans two categories, showing the correct multi-label output
B. Add instructions specifying that failures can belong to multiple categories
C. Add a tiebreaker rule: when in doubt, classify as configuration error to ensure a single deterministic output
D. Use extended thinking so Claude reasons about ambiguous failures before classifying

**Answer:** A
**Explanation:** Multi-label examples directly demonstrate that outputs can span categories, teaching Claude the correct behavior for ambiguous failures through demonstration rather than instruction alone.
**Why not B:** An instruction helps but is less reliable than a demonstrated example of a multi-category output — examples teach the pattern more effectively.
**Why not C:** A default tie-breaking rule masks the multi-label capability instead of teaching it — ambiguous failures should be classified accurately, not defaulted.
**Why not D:** Extended thinking aids reasoning but does not teach the multi-label output pattern — examples are the correct mechanism for demonstrating valid output structures.

## Question 22 [D3]

A Data Extraction team's project-level CLAUDE.md grew bloated as multiple owners added rules. The team is debating splitting it across files. Which split-strategy is MOST aligned with the hierarchy model?

A. Encode the split as SKILL.md files instead of CLAUDE.md sections
B. Distribute the rules across several CLAUDE.md files all at the repository root and rely on a documented load order to combine them in sequence
C. Move some rules to user-level CLAUDE.md to lighten the project file
D. Use subdirectory CLAUDE.md files for path-specific rules and keep root CLAUDE.md focused on global conventions

**Answer:** D
**Explanation:** Subdirectory CLAUDE.md naturally scopes rules to the paths they apply to, which removes irrelevant noise from sessions touching only certain folders. The root keeps cross-project rules; subdirectory files own path-specific behavior.
**Why not A:** Skills are not a substitute for standing rules. CLAUDE.md split by subdirectory is the documented mechanism for path-scoped rules.
**Why not B:** There is no documented multi-file load at the root. Only one CLAUDE.md applies per tier at each location. Splitting by path via subdirectories is the documented approach.
**Why not C:** Moving rules to user-level changes their scope and precedence, which is rarely correct for team standards. The split should preserve scope, not change it.

## Question 23 [D3]

A Developer Productivity team accepts the /init-generated CLAUDE.md without changes. Which characterization of /init output BEST informs whether to ship it as-is?

A. It is auto-updated by Claude Code on every commit, so any manual edits a team makes are wasted effort that the next scaffold pass will silently overwrite
B. It is exam-validated and ready for team-wide rollout without modification
C. It is a starting point — teams should review and refine before adopting it as the project standard
D. It is encrypted and cannot be edited safely — teams must regenerate to make changes

**Answer:** C
**Explanation:** /init produces a scaffold based on automatic repository analysis. It is intentionally a draft: teams need to add conventions, remove noise, and tighten language before relying on it as the project standard. Treating the generated draft as a finished standard skips the review that makes it trustworthy.
**Why not A:** /init does not auto-update on commits. Once generated, the file is static unless someone edits it. Manual refinement is the expected workflow.
**Why not B:** /init has no exam-validation step. It is a generated draft, and using it without review propagates whatever the scaffolder inferred — often imprecise for a real team's standards.
**Why not D:** CLAUDE.md is plain Markdown and is meant to be edited. Treating it as encrypted or regen-only misrepresents the file format.

## Question 24 [D3]

A Customer Support Agent maintainer asks whether starting a new Claude Code session in the same repo will recall context from the previous session. What is the correct CCA-F answer?

A. Yes — but only if the user keeps the terminal window open between sessions
B. Yes — Claude Code maintains a rolling persistent memory across sessions for each repository, so reopening the same repo restores the prior conversation automatically
C. No — Claude Code has no persistent cross-session memory by default; only CLAUDE.md and initial prompts carry forward
D. Yes — the Claude API caches conversational state under each repo's path for 24 hours

**Answer:** C
**Explanation:** Claude Code sessions are bounded by their own context window. Across sessions, the only durable inputs are CLAUDE.md content and what the user provides in initial prompts. Conversational state from a prior session does not persist automatically.
**Why not A:** Keeping a terminal open does not carry context across distinct sessions. Within one session, context persists; across sessions, it does not without explicit reload.
**Why not B:** There is no built-in cross-session conversational memory. Treating sessions as if they automatically remember prior work is the canonical mistake on this topic.
**Why not D:** Prompt caching applies to repeated prompt prefixes within a short window; it is not a 24-hour repo-keyed conversational memory. Conflating cache behavior with session memory is a known trap.

## Question 25 [D2]

A Developer Productivity team uses Claude's built-in tools (web_search, code-execution) alongside a custom MCP-exposed company-knowledge tool. They want consistent observability — every tool call should appear in their tracing system. Where is observability integration BEST implemented?

A. At the host application layer — wrap every tool dispatch (built-in or MCP) with the same tracing instrumentation, so all calls flow through one observability point regardless of tool origin
B. Integrate observability only inside the MCP tools, since Claude's built-in tools already produce their own tracing and do not need the team to add any further instrumentation to appear in the tracing system
C. Inside the model — instruct the agent to log a trace event before and after every tool call
D. On the network layer — log all HTTP requests from the agent and reconstruct traces from that

**Answer:** A
**Explanation:** The host application is the layer that dispatches both built-in and MCP tool calls, so it's the natural integration point for unified tracing. Wrapping at the dispatch layer means every call — built-in or MCP — gets the same tracing fields, the same trace IDs, and the same correlation logic. This avoids two parallel observability paths and keeps traces coherent across tool types.
**Why not B:** Built-in tools may produce some logs but not the team's tracing fields, trace IDs, or correlation. Unified observability requires the host to instrument both paths equivalently.
**Why not C:** Model-emitted tracing is unreliable (depends on compliance, costs tokens, lacks trace IDs). Observability belongs at the dispatch layer where it can be enforced deterministically.
**Why not D:** Network-layer reconstruction misses STDIO MCP calls (no network traffic) and built-in tools that don't go through a single network point. Dispatch-layer instrumentation is the universal integration point.

## Question 26 [D2]

A customer support platform uses MCP: the AI calls a ticket-lookup function, the app injects the account record into each session, and the user selects a formal-reply style template. A new engineer asks why three primitives are needed instead of one universal capability type. What is the BEST architectural justification?

A. Using three primitives reduces the number of JSON Schema definitions the server must maintain for each exposed capability.
B. Each primitive has a distinct controller: model, application, or user. Merging them would blur accountability and make access-scoping impossible to enforce.
C. Separating primitives allows the server to cache tool results, resource data, and prompt templates independently for better performance.
D. Three primitives let the client rotate credentials separately for each capability type during an active session.

**Answer:** B
**Explanation:** The three-primitive model encodes ownership. Merging primitives would make it impossible to apply different authorization and injection policies to model-invoked actions, host-injected data, and user-chosen templates.
**Why not A:** Schema complexity is not the driver for the three-primitive split. The distinction is about control planes and ownership, not schema count reduction.
**Why not C:** Caching is an implementation detail. The three primitives exist to encode distinct ownership and control planes, not to optimize cache strategies.
**Why not D:** Credential rotation is not the rationale for the three-primitive split. Access scoping and control-plane ownership are the key architectural reasons.

## Question 27 [D5]

A Data Extraction team's review interface shows reviewers the agent's output with confidence scores but not the input context. Reviewers struggle to evaluate decisions without seeing what the agent saw. Which adjustment BEST fits?

A. Have reviewers approve or reject based on the confidence scores alone, since a calibrated confidence number already encodes everything a reviewer needs to judge whether the output is trustworthy
B. Include the agent's input context (or a faithful summary) in the review interface alongside the output and scores
C. Reduce the confidence threshold so that reviewers are shown noticeably fewer cases to evaluate
D. Hide the agent's output from reviewers and have them re-derive the correct answer independently from scratch

**Answer:** B
**Explanation:** Reviewers cannot evaluate decisions without seeing the input the agent reasoned over. The review interface must include the input context — the original record, the relevant fields, the supporting documents — so the reviewer can validate the agent's reasoning, not just the output. The structured handoff payload should include this context.
**Why not A:** Confidence-only review is rubber-stamping — reviewers cannot independently evaluate without seeing the input.
**Why not C:** Fewer cases routed does not help reviewers evaluate the cases they do see. The fix is in the review interface, not the routing volume.
**Why not D:** Hiding the output discards useful information and forces re-derivation. Reviewers should see both input and output to evaluate the decision.

## Question 28 [D5]

A Data Extraction pipeline sends 80KB of CSV rows plus a 2KB extraction schema to Claude. The schema is appended LAST. Extraction quality is inconsistent and rows in the middle of the CSV are often missed. Which change addresses BOTH issues?

A. Increase the model's max output tokens to allow longer responses
B. Place the schema at the start, then chunk the CSV across multiple calls
C. Wrap each CSV row in XML tags to make boundaries explicit
D. Run the extraction at temperature 0 to make output deterministic so every CSV row is read in a fixed order and none can be skipped

**Answer:** B
**Explanation:** Putting the schema at the prompt start anchors structural rules where attention is strongest. Chunking the CSV addresses the lost-in-the-middle row dropout: rows that would have been mid-context in one giant call become beginning- or end-context in their own smaller calls, restoring per-row attention.
**Why not A:** Output token ceilings cap generation length but do not change input attention. Larger output budget cannot recover rows the model never attended to in the input.
**Why not C:** XML wrapping aids parsing of structured prose but does not solve mid-context attention decay across an 80KB input. Rows in the middle of a single huge prompt remain underweighted regardless of tagging.
**Why not D:** Determinism does not improve recall on under-attended input rows. The same temperature-0 run will consistently miss the same mid-context rows.

## Question 29 [D2]

A Code Generation team designs a `run_command` tool that takes shell-like arguments. They want to constrain what Claude can pass without rewriting the tool for every new project. Which schema design BEST balances flexibility with safety?

A. Take a base64-encoded command string for transport safety, then decode and execute it, so the wire-level payload stays clean while the model still controls the command
B. Take a single freeform `command_string` parameter and let the model construct any shell command it judges appropriate, since a flexible string adapts to every new project without a schema change and trusts the model to pick safe commands
C. Take an array of arguments and join them with spaces, accepting whatever the model passes
D. Use a discriminated-union schema with a `command_type` enum and per-type argument shapes (e.g., type=test → test_runner enum + test_path; type=build → build_target enum), validated server-side against an allowlist for each type

**Answer:** D
**Explanation:** Discriminated unions with per-type argument shapes give Claude a constrained, well-typed selection space for each command class. Each type has its own allowlist of acceptable arguments, validated server-side. This balances flexibility (new command types can be added) with safety (no escape into arbitrary shell). It's the standard pattern for safe parameterized command execution.
**Why not A:** Encoding for transport does nothing for execution-time safety — the decoded command can still be arbitrary. The allowlist-by-type is what bounds the actual capability.
**Why not B:** Freeform command strings are functionally arbitrary code execution — the canonical antipattern for safe tool design. Even with description-level guidance, an agent can be tricked or confused into emitting dangerous commands.
**Why not C:** Array-of-args is structurally tidier than a freeform string but still permits arbitrary shell semantics — the safety boundary needs to be in the allowed command set, not the surface syntax.

## Question 30 [D1]

Which of the following BEST captures why CCA-F guidance favors task decomposition for complex Code Generation work?

A. Decomposition controls scope per step, enables recovery from partial failure, and supports targeted validation
B. Decomposition mainly makes the overall system look considerably more impressive and sophisticated in the architecture diagrams shown to leadership
C. Decomposition reduces the number of Claude API calls required
D. Decomposition makes the system run faster regardless of dependency structure

**Answer:** A
**Explanation:** Decomposition's value comes from three properties: scoped per-step control, recovery from partial failure, and validation at meaningful boundaries. CCA-F guidance pairs decomposition with these operational benefits — they are the reasons decomposition is favored over monolithic execution.
**Why not B:** Aesthetic impressiveness is not a CCA-F design driver. Decomposition is favored for operational reasons — controllability, recovery, validation — not for diagram complexity.
**Why not C:** Decomposition typically increases the number of API calls, not decreases. The benefit is operational properties (control, recovery, validation), not call count reduction.
**Why not D:** Decomposition helps latency only when dependencies allow parallelism. Sequential decomposition may not reduce wall time; the value is in operational properties, not unconditional latency wins.

## Question 31 [D3]

A CI/CD Integration pipeline launches Claude Code to triage a failing test. The job logs show Claude reading the failing test, then the test source, then the production module under test, then the recent git diff. Which characterization BEST describes what is happening?

A. Claude is running a hardcoded developer-authored script that fetches the files in a fixed order, since any sequence the developer can predict in advance is a deterministic script rather than runtime reasoning
B. Claude is fetching files via a router workflow that classifies the failure type first
C. Claude is running parallel Reads as a fan-out and the logs are merely interleaved
D. Claude is iterating its agentic loop — selecting each next Read based on observations from prior tool results

**Answer:** D
**Explanation:** Claude Code runs a perceive-plan-act-observe loop. Each Read result updates context, and the next tool call is selected dynamically against the goal of triaging the test failure. The investigative chain is exactly that loop in action.
**Why not A:** A fixed-order fetch would be a deterministic workflow. Claude Code is selecting each next file based on what it learned from the previous one, which is adaptive tool selection, not a fixed script.
**Why not B:** A router workflow has a fixed branching topology decided up front. Claude Code chose its investigative path interactively across iterations of its loop, not via a single classify-then-branch dispatch step.
**Why not C:** The described sequence is causal: the test source choice depends on the failing test's imports. Fan-out parallelism requires independent subtasks, not a chain where each step's target comes from the prior step's content.

## Question 32 [D4]

A Data Extraction pipeline runs extract, then validate against business rules, then re-prompt on failure. The team adds an MCP tool call inside the validation step that occasionally times out, and they currently treat every validation-step failure identically by re-prompting the model. Extraction quality is fine but the loop wastes calls re-prompting on tool timeouts. Which refinement BEST fixes this?

A. Remove the validation step's tool call so the loop only ever evaluates the model's extracted content
B. Re-prompt the model on every validation-step failure since re-prompting eventually resolves all errors, and a fresh generation will eventually clear a tool timeout the same way it clears a content mistake
C. Distinguish transient tool errors from extraction-content failures, retrying the tool with backoff but re-prompting only on content errors
D. Lower temperature on the extraction step so the validation tool call stops timing out

**Answer:** C
**Explanation:** A tool timeout is a transient infrastructure error suited to retry with exponential backoff, whereas an extraction that violates business rules is a content failure suited to re-prompting the model. Conflating the two wastes model calls re-prompting on a timeout that no prompt change can fix. Separating the error categories aligns the retry strategy with the actual failure type.
**Why not A:** Dropping the tool removes a legitimate business-rule check; the timeout is a reliability concern to manage with retry, not a reason to delete validation logic.
**Why not B:** Re-prompting cannot fix a tool timeout, which is an infrastructure fault unrelated to the model's output. Treating all failures identically is exactly the waste being reported.
**Why not D:** Temperature affects the model's sampling, not the MCP tool's response time. It has no effect on infrastructure timeouts in the validation step.

## Question 33 [D4]

A Customer Support Agent team's evaluation runs in CI and blocks merge on regression. The team also wants to track gradual drift over weeks. Which architectural approach BEST supports both?

A. Keep the CI gate (per-commit, fast, hard-fail) and add a separate periodic full-evaluation job (daily or weekly) that captures trend metrics over time
B. Run the full evaluation only in the CI gate, since a single per-commit run covers both the merge-blocking decision and any longer-term trend the team cares about
C. Run only the periodic evaluation job, since a daily or weekly full run catches regressions and drift alike without the overhead of a per-commit CI gate
D. Lower temperature to prevent the gradual drift, since a more deterministic setting keeps the scores steady over weeks and removes the need for trend tracking

**Answer:** A
**Explanation:** Two complementary loops: CI gates per-commit on hard regressions (fast feedback, block-on-regression); periodic full-evaluation tracks longer-term trends (drift, slow degradation). They serve different decision timescales. Together they cover acute regressions and gradual drift.
**Why not B:** CI loops are short; longer trends need separate cadence.
**Why not C:** Loses fast per-commit feedback.
**Why not D:** Drift can have many causes; monitoring is the answer.

## Question 34 [D2]

A Developer Productivity team's MCP server tool sometimes wants to return very rich content — formatted Markdown plus a code block plus an image. Which return mechanism BEST supports this?

A. Concatenate everything into one large text string with inline references to the image, so the whole rich response travels as a single block the model can read top to bottom without juggling separate items in the result's content array at all on its way back
B. Return multiple content items in the tool result's content array — a text item with the Markdown, a separate text item with the code block, and an image item with the binary — the client passes the array to the model intact
C. Make three separate tool calls, one returning the Markdown, one returning the code block, and one returning the image, so each content type comes back cleanly typed in its own dedicated response
D. Rich content is not supported in MCP tool responses at all, so the tool has to flatten everything down to plain text and drop the image, returning only what the protocol's text-only result shape can carry

**Answer:** B
**Explanation:** MCP tool result content arrays support multiple typed items per response — text, image, resource references. Returning multiple items lets a single tool produce mixed-type rich content (Markdown summary + code block + image). The client passes the array to the model, which sees all items in order. This is the protocol's mechanism for rich tool returns.
**Why not A:** Single-string concatenation loses the structured shape and forces the model to parse mixed content from prose. Multi-item arrays preserve the typed structure.
**Why not C:** Multiple tool calls multiply roundtrips for content that belongs together. The content array carries mixed content in one response.
**Why not D:** MCP supports rich content via the content array. Assuming plain text only misrepresents the protocol.

## Question 35 [D2]

A Developer Productivity team wants to ship an MCP server that runs on each developer's local machine and is launched as a child process by the IDE. Which MCP transport is the BEST fit?

A. gRPC transport — high-performance RPC with protocol buffers, giving the IDE a strongly typed, low-latency binary channel to the locally running server process
B. StreamableHTTP transport — the IDE connects to a localhost HTTP endpoint on a configured port, since a stable network socket gives the editor a cleaner reconnect story than a subprocess whose stdin and stdout it must manage
C. WebSocket transport — bidirectional message stream over a long-lived connection
D. STDIO transport — the IDE launches the server as a subprocess and communicates over its standard input and output streams

**Answer:** D
**Explanation:** STDIO transport is the canonical choice for locally-hosted MCP servers launched as subprocesses by the host application. There is no network exposure, no authentication required, and process lifecycle is naturally tied to the host. This is the default fit for desktop and IDE integrations.
**Why not A:** gRPC is not an MCP transport. MCP's protocol uses JSON-RPC over STDIO or StreamableHTTP.
**Why not B:** StreamableHTTP is supported on localhost but introduces port management, lifecycle decoupling, and a network attack surface that STDIO avoids. STDIO is simpler and safer for a process the IDE is already responsible for launching.
**Why not C:** WebSocket is not one of MCP's supported transports. MCP supports STDIO and StreamableHTTP.

## Question 36 [D1]

Which of the following is the MOST common reason to over-engineer a Data Extraction feature as agentic when a workflow would have sufficed?

A. Treating tool use as the signal for agentic architecture even when the tool sequence is fixed
B. Choosing the wrong Claude model for the specific task at hand when first setting up the feature
C. Not configuring any system prompt at all for the feature
D. Using JSON mode instead of free-form output

**Answer:** A
**Explanation:** Conflating tool use with agentic architecture is the most common over-engineering pattern. Workflows commonly call tools in fixed sequences; tool use does not justify agentic complexity. CCA-F principles emphasize that the discriminator is runtime decision-making, not tool presence.
**Why not B:** Model choice is independent of architectural class — choosing a model does not over-engineer the architecture. This option does not describe the over-engineering pattern.
**Why not C:** Missing system prompts are a prompt-engineering issue, not an architectural choice. This does not describe the workflow-to-agent over-engineering pattern.
**Why not D:** Output format choice is orthogonal to architectural class. JSON mode is used in both workflows and agents; this option does not describe architectural over-engineering.

## Question 37 [D3]

A CI/CD Integration job uses Claude Code to attempt a refactor. Halfway through, Claude detects that a precondition is unmet and stops without making changes. Which characterization of the execution model BEST fits the stop behavior?

A. The -p flag forces stop at the first uncertain step regardless of task state
B. Claude Code crashed silently and the user should restart the session immediately
C. Only hooks can stop the loop, so without a registered hook Claude must always continue running until it produces a final answer no matter how impossible the precondition makes the task
D. The agentic loop can terminate at any iteration when Claude judges progress impossible — early stops are part of the model, not a failure

**Answer:** D
**Explanation:** Claude Code's loop terminates on task completion, on error, or on an explicit decision that progress is not possible. Stopping when a precondition fails is exactly the third — a deliberate termination by the model, not a bug or hook fault.
**Why not A:** -p controls interactivity, not uncertainty thresholds. It does not force the loop to halt at the first uncertain step; that decision is the model's.
**Why not B:** A deliberate halt with an explanatory message is not a crash. Restarting without addressing the precondition would just reproduce the same halt.
**Why not C:** The loop can self-terminate via Claude's own judgment. Hooks are one mechanism for stopping but not the only one; the model's own decision is also a valid termination path.

## Question 38 [D5]

A Customer Support Agent platform routes 10% of cases to human review using random sampling. The team wants to improve calibration quality. Which sampling refinement BEST fits?

A. Stratify by confidence bucket and customer segment so each stratum is represented proportionally in the review sample
B. Increase the random sampling rate to thirty percent, since a larger random sample naturally draws in more of every kind of case and therefore improves calibration coverage across the board
C. Route only Enterprise-tier cases to review, since those are the highest-value segment to get right
D. Reduce the random sampling rate down to one percent so reviewers have far fewer cases to work through daily

**Answer:** A
**Explanation:** Random sampling reproduces production distribution and may under-represent rare combinations. Stratified sampling by confidence bucket and customer segment ensures each stratum contributes to calibration and quality monitoring. Calibration becomes accurate across all sub-populations, not just the common ones.
**Why not B:** More random sampling still under-represents rare strata proportionally. Stratification is structurally better than larger random samples.
**Why not C:** Single-segment routing misses other segments' calibration signal. Stratification covers all segments.
**Why not D:** Smaller random samples worsen rare-stratum coverage. The direction is toward stratification, not toward less sampling.

## Question 39 [D4]

A Multi-Agent Research synthesizer uses evaluator-optimizer: a generator produces a synthesis, an evaluator scores it, the generator revises. The loop occasionally runs indefinitely. Which change BEST prevents infinite loops?

A. Use only a quality threshold without any iteration cap, since terminating as soon as quality is met is the cleanest stopping rule and an iteration limit is redundant
B. Trust the evaluator-optimizer loop to terminate on its own, since a well-designed quality signal will naturally converge and stop the generator from revising endlessly
C. Lower temperature on the generator, since a more deterministic setting makes each revision change less and brings the loop to a stable output sooner
D. Set explicit convergence criteria — a quality threshold AND a maximum iteration count — terminate on either condition met

**Answer:** D
**Explanation:** Without a maximum iteration limit, an evaluator-optimizer loop can run indefinitely whenever the quality threshold is never reached. Explicit convergence criteria, a quality threshold plus a maximum iteration count, bound the loop: either condition met terminates it. Without both, the loop has no guaranteed termination.
**Why not A:** Quality threshold alone may never be reached; iteration cap is the safety net.
**Why not B:** The infinite-loop failure mode shows it doesn't.
**Why not C:** Doesn't bound iteration.

## Question 40 [D1]

Which of the following BEST describes the role of ambiguity handling in a Multi-Agent Research orchestrator?

A. Always proceed without asking, because asking interrupts the user's flow
B. Detect when the orchestrator's task is under-specified and either clarify, route to a default with disclosure, or escalate
C. Always refuse ambiguous tasks because ambiguity is inherently unsafe
D. Ambiguity handling is the user's responsibility rather than the system's, since the user authored the under-specified request and can restate it

**Answer:** B
**Explanation:** Ambiguity handling at the orchestrator covers detection, response, and escalation. CCA-F guidance favors three canonical responses: clarification, default-with-disclosure, or escalation — depending on context. Silent guessing is the anti-pattern.
**Why not A:** Always-proceed is the silent-guess anti-pattern. Some ambiguity is significant enough to warrant interruption; the design must support that case.
**Why not C:** Always-refuse is over-strict and gives up tasks that have reasonable defaults. The design framework includes refusal only as one of several responses, not as the universal answer.
**Why not D:** Pushing all ambiguity handling to the user produces poor UX. The orchestrator must take some responsibility — detecting ambiguity, choosing a response, and surfacing the decision.

## Question 41 [D1]

Which of the following BEST captures CCA-F guidance on naming subagents?

A. Names should be sequential, like agent-1 and agent-2, to avoid biasing the model with role-laden labels, since neutral identifiers keep the agents interchangeable
B. Names should be generic so the subagents can be reused across scopes
C. Names do not matter at all as long as the underlying code works
D. Names should reflect the subagent's scoped responsibility, not generic capability — 'refund-processor' rather than 'helper'

**Answer:** D
**Explanation:** Scope-reflecting names make the orchestrator-subagent model's structure explicit. CCA-F guidance favors names that describe responsibility — 'refund-processor', 'ticket-classifier' — over generic names like 'helper' or 'agent' which obscure scope.
**Why not A:** Sequential names lose all information about responsibility. CCA-F guidance favors descriptive names that communicate scope to readers.
**Why not B:** Generic names obscure scope and complicate the orchestrator-subagent contract. CCA-F guidance favors scope-specific names; reuse comes from capability-based design, not from name genericness.
**Why not C:** Names affect readability and team coordination on multi-agent systems. CCA-F guidance treats names as part of the design clarity, not as cosmetic.

## Question 42 [D5]

A Code Generation agent generates a refactor proposal that says 'matches the pattern used in module X.' Reviewers find the claim is false — module X uses a different pattern. Which provenance practice would have caught this BEFORE review?

A. Raise the temperature on the agent's pattern claims to encourage more diverse and creative refactor suggestions
B. Trust the agent's pattern-matching claim without verification, since the agent examined module X while drafting the proposal and is therefore well-positioned to judge whether the patterns truly match
C. Forbid the agent from making any claims that reference patterns used in other modules of the codebase
D. Require the agent to cite specific functions or files in module X and validate the citations against actual code

**Answer:** D
**Explanation:** Vague 'matches the pattern' claims are unverifiable and frequently hallucinated. Requiring specific citations and validating them catches the failure before review. The validation can be automated (does the cited function exist? does it actually match?) closing the gap with code rather than relying on reviewer vigilance.
**Why not A:** Temperature is unrelated to verifiability. Provenance validation is the structural fix.
**Why not B:** Trust without verification is the failure mode the scenario demonstrates.
**Why not C:** Forbidding cross-module claims removes useful refactoring signal. Verification preserves the claim's value.

## Question 43 [D1]

A Code Generation team uses PreToolUse hooks for input validation. The team finds that some inputs that should be blocked pass through, while some that should pass are blocked. Which CCA-F-consistent diagnosis MOST directly applies?

A. Just remove the hook and accept all of the incoming inputs as-is
B. Hooks are inherently inaccurate and cannot be trusted
C. Hook validation logic is miscalibrated — refine matching rules against ground-truth examples of both should-pass and should-block inputs
D. Block all of the inputs in order to prevent any false negatives, since rejecting everything guarantees no malicious input ever slips past the hook undetected

**Answer:** C
**Explanation:** Miscalibrated hooks produce both false positives (over-block) and false negatives (under-block). CCA-F guidance favors calibrating hook logic against ground-truth examples — known should-pass and should-block inputs — to refine matching rules toward correctness.
**Why not A:** Removing the hook eliminates the validation. The fix is calibration, not removal.
**Why not B:** Hooks are as accurate as their logic. CCA-F guidance treats miscalibration as a refinable property, not inherent inaccuracy.
**Why not D:** Blocking all inputs is over-strict — false positives go to maximum. The fix balances both directions, not maximizes one.

## Question 44 [D5]

A Data Extraction agent queries a regulatory database and receives a successful HTTP 200 response with an empty JSON array []. The agent must decide whether to report 'no regulatory filings found' or investigate further. Which approach is MOST correct?

A. Report 'no regulatory filings found' since HTTP 200 with an empty array is a valid empty result.
B. Treat the empty array as a possible database error and retry the query.
C. Escalate to a human reviewer because an empty result from a regulatory database is inherently suspicious.
D. Query a backup database to confirm the empty result before reporting it.

**Answer:** A
**Explanation:** HTTP 200 confirms the database was reachable and executed the query successfully. An empty JSON array is an authoritative empty result: the system is saying there are no matching records. This is the correct distinction from an access failure: the database was accessible and returned a definitive result.
**Why not B:** An HTTP 200 response with an empty array is a successful query with zero results — not an error. Retrying a successful query wastes resources and does not change the authoritative empty result.
**Why not C:** Escalating on any empty result would create excessive false escalations. Empty regulatory results are legitimate for entities that have never filed. Escalation criteria should be policy-defined, not based on result content.
**Why not D:** While cross-validation is appropriate in high-stakes domains, it should be driven by policy (e.g., for high-value entities), not triggered automatically on any empty result. HTTP 200 is already an authoritative confirmation of system reachability.

## Question 45 [D4]

A Data Extraction prompt has 11 explicit criteria for field handling but no rule for what to do when a field is missing. Outputs sometimes substitute null, sometimes empty string, sometimes the literal word 'unknown.' Which change MOST directly stabilizes missing-field handling?

A. Lower temperature so the missing-field choice becomes deterministic, since a stable sampler settles on one consistent marker for absent fields each run
B. Drop missing fields from the output entirely so no ambiguous marker is needed
C. Add the 12th criterion: 'Missing fields must use null; never empty string, never sentinel strings'
D. Use JSON mode so the output is always syntactically valid for parsers

**Answer:** C
**Explanation:** Eleven criteria leave an obvious gap at the 12th case. Specifying the explicit missing-value representation plus the explicit forbidden alternatives closes the gap. The model now has a complete rule set and downstream parsers receive consistent missing-field markers.
**Why not A:** Determinism on no rule produces deterministic ambiguity per input.
**Why not B:** Dropping fields changes the output schema and breaks downstream consumers expecting a fixed field list.
**Why not D:** JSON mode accepts null, empty string, and 'unknown' as valid string values. It does not pick one.

## Question 46 [D2]

A Customer Support Agent orchestrator dispatches refund work to a refund-subagent. The refund-subagent has access to the refund API tool. The orchestrator also has the refund API tool registered to handle emergency direct refunds. What concrete cost does this duplication impose?

A. The orchestrator's tool registry consumes roughly twice the memory due to the duplicate tool definitions being held in both the orchestrator's and the subagent's registries simultaneously throughout the session's lifetime
B. Duplicate registrations cause the MCP protocol to reject the session at startup
C. The subagent's calls will be routed to the orchestrator's tool handler instead of its own
D. The orchestrator may invoke the refund tool directly for routine cases, bypassing the audit logging and review steps the refund-subagent layer adds — meaning compliance-relevant context is lost

**Answer:** D
**Explanation:** When a subagent wraps a tool with additional layers (audit logging, eligibility checks, review), duplicating the underlying tool at the orchestrator level lets the orchestrator skip those layers. The duplication's concrete cost is the loss of the wrapper's compliance and quality controls on every direct-call path. Partitioning only works when the orchestrator cannot skip the subagent.
**Why not A:** Memory cost is negligible and not the meaningful concern. The architectural cost — losing the subagent's wrapping controls — is the real impact.
**Why not B:** Tools are scoped per agent — the same tool name on the orchestrator and subagent does not produce a session-level conflict. The cost is architectural and operational, not a hard failure.
**Why not C:** Each agent's tools are dispatched to its own handlers. There is no cross-routing between orchestrator and subagent.

## Question 47 [D3]

A Developer Productivity team builds an SDK-driven service that runs many short Claude Code sessions to triage incoming tickets. They need each session bounded in duration, the team's project CLAUDE.md and custom slash commands honored, structured JSON returned for downstream routing, and per-session observability. The architect must design how these requirements compose through the SDK. Which design BEST satisfies all of them?

A. Use the SDK but disable CLAUDE.md so sessions start faster, and reconstruct any needed instructions in the prompt each time
B. Call the Claude API per ticket with the routing schema in the prompt, since CLAUDE.md and slash commands transfer automatically to API calls and the model loads the project configuration the same way a Claude Code session does
C. Run each session under the project working directory with a session time limit, request structured output, and instrument the SDK for per-session telemetry
D. Skip session time limits and rely on ticket volume staying low so sessions naturally finish quickly

**Answer:** C
**Explanation:** SDK-driven sessions honor the project's CLAUDE.md and custom slash commands when run in the project context, satisfying configuration inheritance. A session time limit bounds duration, requesting structured output yields routable JSON, and instrumenting the SDK gives the per-session observability needed for reliability. Each requirement maps to an SDK capability rather than to the raw model API.
**Why not A:** Disabling CLAUDE.md discards the team's standing project instructions and slash commands, which the requirement explicitly needs honored. Re-injecting them per prompt is brittle and duplicates the configuration hierarchy.
**Why not B:** The Claude API does not load CLAUDE.md or custom slash commands; those are Claude Code session constructs. Configuration would silently be ignored, breaking the team's expected triage behavior.
**Why not D:** Hoping volume stays low is not a duration bound; a single stuck session can run unbounded and starve the service. A programmatic time limit is required for the bounded-duration requirement.

## Question 48 [D1]

A Multi-Agent Research team has been told that their report-generation system needs to support both daily fixed reports and ad-hoc deep-dive analyses. Which architectural pattern MOST cleanly satisfies both requirements?

A. A single agent that handles both the daily fixed reports and the open-ended ad-hoc deep dives together
B. A workflow for the daily fixed reports and an agent for ad-hoc deep dives, with a router between them
C. A single workflow that handles both daily reports and deep dives
D. Two separate products with no shared infrastructure

**Answer:** B
**Explanation:** Different requirements warrant different classes. Daily fixed reports fit a workflow; ad-hoc deep dives fit an agent. The router classifies the request type and dispatches accordingly — CCA-F's canonical hybrid pattern.
**Why not A:** A single agent inherits agentic variance and cost on the daily fixed reports where they have no benefit. The workflow's strengths on predetermined cases are lost; the hybrid preserves them.
**Why not C:** Deep dives require runtime adaptation that a workflow's fixed sequence cannot provide. The workflow cannot handle the deep-dive requirement on its own.
**Why not D:** Full separation duplicates infrastructure without benefit. The hybrid shares infrastructure for routing, logging, and orchestration while keeping the architectural classes separate where they matter — at the feature level.

## Question 49 [D3]

A Multi-Agent Research team wants -p runs to read CLAUDE.md from a specific path, not the working directory's default. Which characterization BEST fits?

A. Pass a --claude-md=PATH flag to point the run at a specific file explicitly, since the CLI accepts an option that overrides where it looks for the configuration
B. Set the working directory to the project root before invoking -p — CLAUDE.md discovery follows the working directory hierarchy
C. Copy the CLAUDE.md into a hardcoded path that the run always reads from, staging the file there before each invocation so discovery lands on the right one
D. Accept that -p ignores CLAUDE.md regardless of its location, so the team has no real way to control which configuration a non-interactive run picks up

**Answer:** B
**Explanation:** Claude Code resolves CLAUDE.md by location. The working directory determines what is in scope. Set the cwd (cd or the runner's working directory) to the desired project root and the hierarchy resolves correctly.
**Why not A:** There is no --claude-md flag; the CLI does not accept an option that points CLAUDE.md discovery at an arbitrary file. Discovery follows the working directory hierarchy instead.
**Why not C:** Setting the working directory is cleaner than copying. The hierarchy is location-based.
**Why not D:** -p honors CLAUDE.md. Location and working directory drive discovery.

## Question 50 [D4]

A Customer Support Agent prompt instructs Claude to 'apologize when the customer is upset.' Some responses apologize for routine inquiries, others miss apologies after genuine complaints. Which change BEST calibrates the apology behavior?

A. Lower temperature to make the apology choice deterministic on each run
B. Always apologize first to be safe, since leading with an apology guarantees no upset customer is ever missed even on routine inquiries and the courtesy rarely offends
C. Use few-shot with two upset and two non-upset tickets so the model learns the boundary
D. Specify trigger conditions for apology — explicit complaint, service failure mentioned, frustration phrasing — and one canonical apology sentence

**Answer:** D
**Explanation:** 'Upset' is a subjective inference. Naming three observable trigger conditions plus a canonical apology phrase gives the model both a clear gate (when to apologize) and a controlled response (how to apologize), eliminating both over- and under-apology.
**Why not A:** Determinism does not introduce a trigger rule. The model deterministically follows an unstated rule, producing the same drift.
**Why not B:** Always-apology becomes performative and annoys customers with routine inquiries. The fix is calibration, not maximalism.
**Why not C:** Four examples cannot span the upset spectrum. Edge cases still get inconsistent treatment without a stated trigger rule.

## Question 51 [D5]

A Data Extraction script reports 'context window limit exceeded' on roughly 5% of records — typically the longest ones. Which is the BEST short-term mitigation while a more permanent chunking refactor is built?

A. Detect oversize records and split them into two halves processed independently
B. Skip records that exceed the window and log them as failed, since dropping the longest five percent preserves throughput while the refactor lands
C. Retry oversize records with exponential backoff, since the limit errors look transient and spacing the retries out tends to let the record through
D. Lower max_tokens to make room for the oversized input

**Answer:** A
**Explanation:** Splitting just the long records keeps the normal path unchanged while preventing overflow on the 5% tail. It is an incremental fix that buys time for the proper chunking refactor without rebuilding the entire pipeline.
**Why not B:** Silently skipping records is data loss — exactly the high-stakes failure pattern D5 reliability teaches architects to avoid. A short-term mitigation must still process the records, not drop them.
**Why not C:** Context overflow is deterministic, not transient. The same oversize record will overflow on every retry; backoff cannot help.
**Why not D:** Lowering output budget marginally helps but does not address a 5% tail of records that exceed input limits by significant margins. Splitting addresses the root cause.

## Question 52 [D4]

A Data Extraction team has two pipelines using the same Claude model with different system prompts — one for invoices, one for purchase orders. Both prompts are nearly identical except for the schema names. A developer suggests consolidating them into one prompt that handles both via a runtime flag. Which assessment is MOST accurate?

A. Routing logic must always live in the system prompt for consolidation to work
B. Consolidation is always better because it reduces maintenance overhead
C. Two separate user messages on one consolidated prompt achieve the same isolation as two prompts, since distinct turns keep the contexts logically apart
D. Consolidation increases prompt complexity and risks cross-document interference; keep specialized system prompts unless the deduplication win is large

**Answer:** D
**Explanation:** Specialized system prompts isolate each task's scope, examples, and edge cases, preventing one document type's rules from influencing the other. Consolidation forces the model to branch on a flag, which is itself an additional source of routing error. Specialization is the safer architecture unless duplication cost dominates.
**Why not A:** Routing logic in the system prompt is exactly the pattern that introduces the cross-document interference described. It is not a fix; it is the trade-off.
**Why not B:** Always-statements are red flags. Maintenance reduction is real but trades off against branching complexity and cross-document interference.
**Why not C:** User messages do not isolate system-prompt context. Whatever guidance both invoices and POs receive in the consolidated system prompt influences both extractions.

## Question 53 [D1]

A Multi-Agent Research platform team is documenting decomposition guidelines for the entire org. The team wants a small set of properties that uniformly apply across feature types. Which set MOST cleanly captures CCA-F guidance?

A. Always use the maximum decomposition the orchestrator can manage
B. Decompose the work strictly by team ownership, by the total file count, by the line count, and by the overall number of API calls that get made each run
C. Decompose by natural concerns, right-size each subtask, make dependencies explicit, scope to downstream needs, and design boundaries for validation
D. Always use one giant subtask to avoid coordination overhead

**Answer:** C
**Explanation:** The five properties cover the CCA-F decomposition design space: concerns drive natural boundaries; right-sizing addresses over/under-decomposition; explicit dependencies enable correct sequencing; scoping prevents waste; validation-aligned boundaries support recovery. The set uniformly applies across feature types.
**Why not A:** Maximum decomposition over-decomposes — coordination cost grows faster than control benefit. CCA-F guidance is about balance, not maxima.
**Why not B:** Team ownership, file count, line count, and API count are not CCA-F design axes. They impose organizational or mechanical structure on technical work that should be decomposed by natural concerns.
**Why not D:** One giant subtask under-decomposes — controllability, recovery, and validation all suffer. CCA-F guidance is about balance, not minima.

## Question 54 [D1]

Which of the following Data Extraction scenarios MOST clearly requires explicit ambiguity handling?

A. An extraction agent encounters a document with an ambiguous field name that could match two different schema fields
B. An extraction agent finds all required fields cleanly mapped but should still run ambiguity handling defensively on every document
C. An extraction agent that has been upgraded to the latest Claude model
D. An extraction agent that is simply running at a high temperature

**Answer:** A
**Explanation:** Field-name ambiguity is a case where the agent's interpretation directly affects extracted values. CCA-F guidance favors explicit ambiguity handling — either clarification, validation, or recording the interpretation — when interpretation choice changes outputs.
**Why not B:** Clean mapping is the absence of ambiguity. No special handling is needed when the agent has unambiguous extraction signals.
**Why not C:** Model version does not by itself create or resolve ambiguity. Ambiguity handling is needed when the document structure is genuinely ambiguous, regardless of model.
**Why not D:** Temperature affects sampling variance, not the presence of ambiguity. Ambiguity is a property of the input; temperature does not eliminate it.

## Question 55 [D3]

A Code Generation team implements a PreToolUse safety hook that blocks Bash commands matching dangerous patterns (`rm -rf`, `DROP TABLE`, `format C:`). A developer notices that the hook is also blocking legitimate commands that happen to contain these substrings. What is the root cause and fix?

A. The hook is case-sensitive — adding case-insensitive matching would prevent false positives.
B. The hook should run PostToolUse instead of PreToolUse — post-execution pattern matching avoids blocking legitimate commands.
C. Substring matching false-positives on legitimate commands — use specific regex with word boundaries
D. The hook should maintain a whitelist of allowed commands — only listed commands execute, all others are blocked.

**Answer:** C
**Explanation:** Substring matching (e.g., blocking any command containing 'rm -rf') will false-positive on commands like `echo 'Do not run rm -rf'` or `grep 'rm -rf' file.txt`. More precise patterns — using regex word boundaries, checking that 'rm -rf' is a command invocation rather than a string argument, or requiring the pattern to appear at the command start — reduce false positives while maintaining safety coverage.
**Why not A:** Case sensitivity is a secondary consideration. The root cause of false positives from substring matching is pattern specificity — matching the substring `rm -rf` inside a longer, safe command string. The fix requires more precise pattern matching, not case handling.
**Why not B:** Switching to PostToolUse defeats the safety purpose — the dangerous command would execute before the hook checks it. The fix is to make the PreToolUse pattern matching more precise, not to change the hook event.
**Why not D:** A strict allowlist blocks all commands not explicitly whitelisted, which is far more restrictive than needed and prevents Claude Code from running legitimate commands. The goal is to block specific dangerous patterns, not restrict all Bash usage. Improving pattern specificity resolves the false positive problem without switching to a restrictive allowlist model.

## Question 56 [D2]

A Multi-Agent Research tool accepts an `embedding_model` parameter as a free-text string. Claude passes valid model names roughly 80% of the time but occasionally passes outdated or non-existent ones, causing failures. The team maintains a list of supported models. Which schema change BEST eliminates the invalid-model calls?

A. Accept any string for embedding_model and have the server reject invalid or outdated names with a clear error message, so the agent learns from the failure and the supported-models list stays enforced at the server boundary
B. Add a description note that lists all the supported embedding models, so Claude can read the note and pick a currently valid name from it on each call
C. Type the parameter as an enum with the current supported model names, regenerated from the supported-models list whenever the list changes
D. Pin the parameter to one default model and remove the model choice entirely, so the agent can never pass an invalid name because it no longer selects the model at all

**Answer:** C
**Explanation:** Enums constrain the parameter to a closed set of valid values at the schema layer, and Claude treats the enum values as the allowed options. Regenerating the enum from the team's supported-models list whenever it changes keeps the schema in sync with reality. The validator also rejects non-enum values as a hard backstop. This is the canonical pattern for closed-set parameters.
**Why not A:** Server-side rejection burns a tool call and forces a retry when an enum could have prevented the invalid call at write time. Move the constraint left.
**Why not B:** Description notes are weaker than schema-level enums — Claude must read and follow them every call. Enums make the rule enforceable at validation.
**Why not D:** Removing the choice loses the agent's legitimate ability to pick different models for different tasks. The team wants valid choices, not no choices.

## Question 57 [D3]

A Code Generation team wants to know what /compact does inside Claude Code. Which description is MOST accurate?

A. It permanently archives the session to disk for later replay
B. It summarizes earlier turns in the current session to free context while preserving the thread
C. It disables CLAUDE.md mid-session to reduce token usage by roughly 50%, trading away project rules for a smaller context footprint
D. It moves the accumulated session state to a configured MCP server for offloaded storage, freeing the local context window by relocating history to the external service

**Answer:** B
**Explanation:** /compact is the built-in command for in-session compaction. It replaces older verbose turns with a summary, freeing context to continue the session. The thread is preserved but at lower fidelity for older content.
**Why not A:** /compact operates within the live session to manage context; it is not an archive-to-disk command. Session preservation across sessions is a different problem.
**Why not C:** /compact does not disable CLAUDE.md. CLAUDE.md is part of standing configuration; /compact targets accumulated conversational history.
**Why not D:** /compact has no MCP involvement. It is a local in-session summarization, not an external offload mechanism.

## Question 58 [D3]

A Code Generation user wants to start a session with a precise problem statement plus three reference files already in context. Which approach BEST achieves that under Claude Code's session model?

A. Use the Claude API directly with file attachments, because Claude Code itself cannot ingest local files into a running session and must defer to the raw API for any content loading
B. Embed the entire content of all three files inside CLAUDE.md so every session preloads them
C. Open the session, ask Claude to Read the three files, and then state the problem — the loop loads them on demand
D. Configure a PreToolUse hook to inject the three files before each tool call

**Answer:** C
**Explanation:** Claude Code's loop ingests files via Read when asked. Issuing explicit Read calls at the top of the session ensures the three reference files are in context before Claude reasons about the problem. This is the natural mapping of the session model to the requirement.
**Why not A:** Claude Code ingests files via Read at any point in a session. Suggesting it cannot is incorrect and ignores the core tool model.
**Why not B:** Inlining three full files into CLAUDE.md inflates every session's context, even sessions that do not need them. The on-demand Read pattern keeps CLAUDE.md lean while still satisfying the immediate session.
**Why not D:** Hooks run shell-level scripts; they are not a clean way to seed initial context. Explicit Reads at session start are simpler, observable, and free of hook-specific failure modes.

## Question 59 [D1]

A Customer Support Agent team has documented a customer-onboarding workflow in prose but the agent occasionally skips steps. Which CCA-F-consistent design improvement MOST directly applies?

A. Strengthen the prose instructions with much more detail, since a more thorough natural-language description will reliably get the agent to follow the workflow steps
B. Define the workflow as code — explicit sequence with programmatic enforcement of step ordering, not just prose documentation
C. Just trust the agent to follow the workflow eventually on its own
D. Simply remove the workflow requirement from the system altogether

**Answer:** B
**Explanation:** Prose-documented workflows are probabilistic — the agent may skip steps under varied inputs. CCA-F guidance favors workflow-as-code with programmatic enforcement: explicit sequence, gated transitions, and validated state. The workflow is a structure, not just documentation.
**Why not A:** More detailed prose remains probabilistic. CCA-F guidance favors workflow-as-code for enforcement; prose is documentation, not enforcement.
**Why not C:** Trust without enforcement is the failure mode the team is observing. CCA-F guidance favors structural enforcement of workflow definitions.
**Why not D:** Removing the workflow eliminates the team's process. The fix is enforcement, not abandonment.

## Question 60 [D4]

A Customer Support Agent pipeline extracts order IDs and refund amounts from emails into a JSON object. In testing, roughly 15% of responses omit the 'amount' field or return it as a string instead of a number. The team wants to reduce that error rate without replacing the model. Which retry strategy is most aligned with CCA-F validation-retry principles?

A. Re-run the identical prompt automatically up to three times and accept whichever response first passes a JSON schema check, logging each failed attempt for offline review.
B. Feed the specific validation failure reason back into the next prompt and cap retries at a fixed budget, escalating when the budget is exhausted.
C. Use a second model call to critique the first response, then return the critique to a human for final correction.
D. Raise the retry budget to unlimited retries so every response eventually passes schema validation.

**Answer:** B
**Explanation:** This is the canonical validation-retry loop: (1) validate output against schema, (2) inject the specific failure reason into the retry prompt so the model can self-correct, (3) enforce a retry budget to bound latency and cost, and (4) escalate when the budget is exhausted.
**Why not A:** Retrying without changing the input gives the model the same ambiguous signal and typically yields the same error. The failure reason must be fed back into the next attempt to change the model's behavior.
**Why not C:** A multi-pass reviewer pattern can improve quality but it is a review step, not a retry loop. Sending critiques to humans by default defeats the purpose of automated validation for a structured-extraction task.
**Why not D:** Unlimited retries remove cost and latency controls. Retry budgets exist precisely to cap runaway loops; when the budget is exhausted the system should escalate rather than retry indefinitely.
