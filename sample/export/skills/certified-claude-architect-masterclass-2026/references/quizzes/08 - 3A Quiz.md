# 3A Quiz

> Course: Claude Certified Architect (CCAR-F) - 2026 Exam Prep · D3: Claude Code - Architecture & Setup · 5 questions · pass mark 70% · ANSWER KEY INCLUDED: show a question and its choices first, reveal the answer only after the learner replies

## Question 1

A developer runs Claude Code on a task to refactor a payment module and walks away. Twenty minutes later they return to find Claude Code has rewritten five files, deleted two deprecated helpers, and updated three test files — all autonomously. Which characteristic of Claude Code best explains this behavior?

A. Claude Code operates as an autonomous agent that loops through planning, tool calls, and observation until the task is done.
B. Claude Code mirrors the behavior of IDE plugins, but with write access enabled by default.
C. Claude Code retains memory of prior sessions and resumes where it left off when given a similar task.
D. Claude Code batches all file changes into a single commit after analyzing the full codebase at startup.

**Answer:** A
**Explanation:** Claude Code is an agentic CLI that executes multi-step tasks autonomously using a planning loop — it plans, calls a tool, observes the result, and repeats until the task is complete. This is fundamentally different from IDE plugins or chat tools, which respond to individual keystrokes or single prompts without taking further autonomous action.

## Question 2

During a code review, a teammate notices that Claude Code replaced an entire 400-line utility file when the task only required updating one function signature. What should have been used instead, and why?

A. Read should have been used first to load the file into context before any modification was attempted.
B. Edit should have been used because it performs a targeted find-and-replace, leaving the rest of the file intact.
C. Agent should have been used to delegate the change to a subagent with a fresh context window.
D. WebSearch should have been used to retrieve the correct function signature before applying any change.

**Answer:** B
**Explanation:** Edit performs a scoped find-and-replace on an existing file, leaving everything else intact. Write overwrites the entire file — if lines are omitted from the new content, they are permanently gone. For modifications to existing code, Edit is the correct tool because it is targeted and safe.

## Question 3

A Claude Code workflow fails midway because a library's API changed after Claude Code's training cutoff. The developer needs Claude Code to look up the updated method signature from the library's official docs. Which tool handles this, and what does it return?

A. WebSearch retrieves current documentation and returns the results as text for Claude Code to read and reason about.
B. Read fetches the library's remote documentation URL and loads its full content into the session context.
C. Bash executes a curl command that fetches the docs page and returns the full HTML to the session.
D. Agent spawns a subagent that downloads the library source and scans it for the updated signature.

**Answer:** A
**Explanation:** WebSearch lets Claude Code query the web for information that goes beyond its training data, such as current documentation, recent API changes, and new library versions. Results are returned as text that Claude Code reads and reasons about before acting.

## Question 4

A new engineer joins a team and runs /init on an unfamiliar repository before their first session. After /init completes, a senior engineer tells them the file is not ready to use yet. What does the /init command produce, and what still needs to happen?

A. /init produces a finalized CLAUDE.md that is ready for the whole team to use without further changes.
B. /init runs a one-time scan and deletes itself after creating a permanent project configuration in source control.
C. /init connects to the project's CI pipeline to pull tested configuration from the last passing build.
D. /init produces a starter CLAUDE.md draft based on repo analysis; the team must review, correct inaccuracies, and add team-specific rules before using it.

**Answer:** D
**Explanation:** /init analyzes the repo and auto-generates a starter CLAUDE.md with detected project name, key files, languages, and suggested rules. This output is a starting point derived from automated analysis — not a finished configuration. The team must verify detected data, add team conventions, and remove noise before the file is adopted.

## Question 5

A developer is about to start a debugging task and mentions fifteen files to Claude Code 'just to be thorough.' A colleague suggests this approach may actually hurt performance. According to the deck, why does over-including context produce worse results?

A. Mentioning extra files forces Claude Code to switch to WebSearch mode, which is slower than direct file reads.
B. Large context loads cause the Agent tool to automatically spawn subagents, splitting the task in unpredictable ways.
C. Over-inclusion fills the context window with low-signal files, which can push out high-value content and leaves less space for actual task work.
D. Claude Code refuses to process sessions with more than ten files mentioned, returning an error to the developer.

**Answer:** C
**Explanation:** Every file mentioned adds tokens to the finite context window. When the window fills, earlier content is compacted or dropped — including content that mattered. A smaller, accurate context window consistently outperforms a large, noisy one because Claude Code has more working space for the actual task and less irrelevant material competing for attention.
