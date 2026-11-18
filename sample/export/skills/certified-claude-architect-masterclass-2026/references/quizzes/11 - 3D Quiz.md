# 3D Quiz

> Course: Claude Certified Architect (CCAR-F) - 2026 Exam Prep · D3: Claude Code - Hooks, SDK & CI/CD · 9 questions · pass mark 70% · ANSWER KEY INCLUDED: show a question and its choices first, reveal the answer only after the learner replies

## Question 1

A security team wants to prevent Claude Code from executing any Bash command that matches a known-dangerous pattern during an agentic session. They need this enforcement to be deterministic and impossible to override via prompt instructions. Which hook type and mechanism achieves this?

A. A Notification hook that routes blocked command alerts to the security team's Slack channel before Claude executes them.
B. A CLAUDE.md instruction listing prohibited commands, which Claude Code enforces deterministically at every session.
C. A PostToolUse hook that logs the dangerous command and asks Claude to roll back the action if the pattern matches.
D. A PreToolUse hook that inspects the Bash command and returns exit code 2 when a dangerous pattern is detected.

**Answer:** D
**Explanation:** PreToolUse is the only hook type that can block a tool call before it executes. An exit code of 2 signals Claude Code to halt the call, while other non-zero exits are non-blocking errors. Because hooks run at the shell level outside Claude's context, they fire deterministically regardless of Claude's reasoning and cannot be overridden by prompt instructions, making them the correct mechanism for mandatory safety enforcement.

## Question 2

A practitioner writes a PreToolUse hook script that should block file writes to a protected directory and allow all other writes. During testing they run it against five sample inputs from the terminal and verify the exit codes. Which additional testing step does the deck specifically recommend before deploying the hook to a live session?

A. Confirm that the script file exists at the registered settings path; a resolvable path means the hook is ready for a live session.
B. Add stderr messages for each blocking exit and use dry-run mode to observe hook behavior before enabling enforcement.
C. Register the hook in a test project first; if Claude completes all assigned tasks normally in that project, the exit code logic is verified.
D. Run the hook once against a live destructive command; if it blocks successfully in production, the exit code logic is confirmed correct.

**Answer:** B
**Explanation:** Beyond verifying exit codes with sample inputs, the deck recommends using a dry-run mode (where the hook logs what it would block without exiting non-zero) to observe behavior across real session conditions, and adding explicit messages to stderr for every blocking exit so that blocked calls are diagnosable. A silently blocking hook is indistinguishable from Claude refusing to act without stderr diagnostics.

## Question 3

A team debates whether to register a hook as an inline one-liner in settings or as a standalone script file. The hook logic must compare an incoming Bash command against a 30-item policy blocklist and return a status code based on the match. Which approach does the deck recommend and why?

A. An inline command is preferred for performance; external script files add measurable file I/O overhead on every hook invocation.
B. An external script file is preferred — it can be tested independently, version-controlled, and updated as the policy list evolves.
C. Inline commands are preferred because they consolidate all hook configuration in a single settings file without external file dependencies.
D. Either approach is equivalent for a 30-item blocklist; the correct choice depends entirely on team coding style preferences.

**Answer:** B
**Explanation:** Inline commands are appropriate for simple one-liners like logging a tool name. Any logic involving conditionals, comparisons against a list, or external service calls should be in an external script file. Script files can be run independently with test inputs, version-controlled, diffed, and shared across sessions — making them far more maintainable as complexity grows.

## Question 4

A team wants every Python file Claude Code writes or edits to be automatically reformatted with Black without requiring any manual step. They have confirmed that Black is installed and the files are already saved to disk before the formatter needs to run. Which hook type and trigger should they configure?

A. Stop hook — it fires once at the end of the session and runs Black across all files modified during the turn.
B. PostToolUse on Write or Edit calls — the hook fires after the file is saved, letting Black reformat the already-written file.
C. Notification hook — it routes a formatting request to an external CI system that applies Black and commits the changes.
D. PreToolUse on Write calls — the hook runs Black on the pending content before Claude saves it, ensuring the file is formatted on disk from the start.

**Answer:** B
**Explanation:** The auto-format pattern uses a PostToolUse hook triggered on Write or Edit tool calls. PostToolUse fires after the file is already saved to disk, so the formatter can operate on the real saved file. PreToolUse would fire before the write, meaning the file does not yet exist in its new form and cannot be formatted.

## Question 5

A team runs automated agentic pipelines that sometimes take 20 minutes to complete. Developers currently poll the terminal to check whether a run has finished. They want a hook that fires exactly once when the agent finishes its execution loop and dispatches a Slack message with the task name and outcome. Which hook type fits this requirement?

A. A PreToolUse hook on the first tool call of the next session fires before new work begins, signaling that the previous run has finished.
B. A Stop hook fires at the end of each agent turn and can dispatch a Slack message with task name and outcome.
C. A PostToolUse hook on the final tool call in the pipeline fires after the last action and can reliably trigger the Slack message.
D. A Notification hook fires when Claude emits an alert event, which includes the natural end-of-pipeline signal, and can push to Slack directly.

**Answer:** B
**Explanation:** The Stop hook fires when Claude reaches the end of its execution loop for a given turn — once per agent turn. This makes it the natural trigger for completion signals. It fires after all tool calls for the turn are finished, so the hook can evaluate the full outcome and include task name, duration, and success or failure status in a notification payload.

## Question 6

A data-engineering team wants to trigger a Claude Code session automatically whenever a new data pipeline fails in production. The session should read failure logs, propose a fix, and write its output to a monitoring dashboard — all without any developer present. Which approach fits this use case and why?

A. Use the Claude Code CLI in interactive mode and pipe its terminal output to the dashboard via a shell redirect.
B. Use the Claude Code CLI with a custom shell script that restarts the session after each failure event to simulate automation.
C. Use the Claude Code SDK to create a programmatic session, inject the failure logs as context, and stream output to the dashboard.
D. Call the Claude API directly and pass the failure logs as a prompt, then parse the completion for the fix proposal.

**Answer:** C
**Explanation:** The Claude Code SDK is the right tool when code, not a human, must drive a session. It lets an application create and manage sessions programmatically, inject context, and stream output — exactly what an automated failure-response pipeline needs. The CLI is interactive and human-driven. The direct API handles single model calls with no agent loop or tool orchestration.

## Question 7

A developer is building a code-review bot that opens an SDK session when a pull request is created. Midway through the review, a new requirement comes in and the developer wants to redirect the agent to focus on security issues only — without losing the context already accumulated. What SDK capability supports this?

A. Append a follow-up prompt mid-session to redirect the agent while keeping accumulated context intact.
B. Open a second parallel SDK session dedicated to security and merge its output with the first session's results manually.
C. Restart the session with a new system prompt scoped to security issues and pass the pull-request files again.
D. Update the tool permission set at runtime to restrict the agent to security-related tools only.

**Answer:** A
**Explanation:** The SDK allows follow-up prompts to be appended mid-session to redirect the agent without restarting it. This preserves all context the session has already accumulated. Restarting a session or creating a new one discards that state. Tool permission changes affect what the agent can do, not what it already knows.

## Question 8

A DevOps engineer adds a Claude Code step to a GitHub Actions workflow. After deploying, she notices every run of the workflow hangs for exactly 360 seconds before the runner kills it. No output is ever written to the log. What is the most likely cause?

A. The ANTHROPIC_API_KEY was not injected as an environment variable, so Claude Code silently retried authentication until the timeout.
B. The -p flag was omitted, so Claude Code entered interactive mode and blocked waiting for input that never arrived.
C. The workflow granted excessive tool permissions, and Claude Code spent the timeout period executing unintended file-write operations.
D. GitHub Actions does not support stdout capture from Claude Code, so the output buffer filled and the process stalled.

**Answer:** B
**Explanation:** Without the -p flag, Claude Code defaults to interactive mode and waits for terminal input that a CI/CD runner can never provide. The job blocks silently until the runner's timeout fires. The -p flag switches Claude Code to non-interactive mode, causing it to accept the prompt, execute the task, write to stdout, and exit with a status code.

## Question 9

A CI pipeline invokes Claude Code with -p to generate a changelog entry from recent commit messages and then feeds the result into a release-notes step. During a test run, the release-notes step fails because it received a plain error message instead of the expected JSON. Which practice would prevent this failure?

A. Set a timeout on the Claude Code pipeline step so a stalled task does not block the release-notes step indefinitely.
B. Store the ANTHROPIC_API_KEY in a plaintext environment variable in the workflow file to ensure authentication succeeds every run.
C. Check the exit code after the Claude Code step and retry the invocation automatically on any non-zero result.
D. Validate the JSON shape of Claude Code's stdout before passing it to the release-notes step, and fail the pipeline if the shape is wrong.

**Answer:** D
**Explanation:** The deck teaches that Claude Code may return a plain message instead of structured data when something goes wrong, so you must validate the output's shape before using it downstream. Checking the exit code signals whether the task succeeded, but does not verify the output format. Retrying on non-zero exits and setting timeouts are separate resilience concerns.
