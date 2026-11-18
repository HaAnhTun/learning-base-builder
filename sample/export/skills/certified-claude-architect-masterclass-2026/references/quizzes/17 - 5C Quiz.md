# 5C Quiz

> Course: Claude Certified Architect (CCAR-F) - 2026 Exam Prep · D5: Context Management - Cross-Session Knowledge & Coherence · 10 questions · pass mark 70% · ANSWER KEY INCLUDED: show a question and its choices first, reveal the answer only after the learner replies

## Question 1

A developer starts a new Claude Code session on a long-running project. The agent re-explores an approach that was ruled out two sessions ago and contradicts a naming convention the team settled earlier. What mechanism does the deck say would have prevented this?

A. A more detailed CLAUDE.md with all naming conventions spelled out as standing rules.
B. A scratchpad file in the repo that the agent reads at session start, containing decisions and dead ends from prior sessions.
C. Longer context windows so the agent can retain more conversation history across sessions.
D. Committing all exploratory code branches to git so the agent can inspect what was tried before.

**Answer:** B
**Explanation:** The deck describes the cross-session problem: every new session opens with a blank context window, making prior decisions and explored dead ends invisible. A scratchpad file read at session start restores that continuity, ensuring the agent respects recorded conventions and does not re-explore what has already been ruled out. The other options are real software practices but not the mechanism the deck teaches for this specific problem.

## Question 2

A developer closes a Claude Code session without updating the scratchpad. The next session reads that same scratchpad and, acting on its outdated contents, makes a decision that contradicts work done in the skipped session. The deck identifies this as a consequence of which failure?

A. Overly broad scratchpad scope — too many fields made it hard for the agent to find the relevant decision.
B. Missing end-of-session write — the scratchpad was not updated, so the next session inherited stale state.
C. Credential leak — sensitive data in the scratchpad caused the agent to use incorrect context.
D. Missing session-start read — the agent never loaded the scratchpad at the beginning of the new session.

**Answer:** B
**Explanation:** The deck teaches that the scratchpad discipline has two halves: reading at session start and writing at session end. Skipping the end-of-session write means the next session inherits stale state. The deck explicitly states that a stale scratchpad is worse than no scratchpad because the agent trusts outdated information. The failure here is the missing write, not a structural problem with the file's format.

## Question 3

After six weeks of active development, a scratchpad file has grown from 50 to 600 lines. The agent begins citing approaches that were ruled out a month ago. Which scratchpad hygiene failure does the deck say this illustrates?

A. Credential exposure — sensitive data in the scratchpad confused the agent's context resolution.
B. A CLAUDE.md conflict — stable rules in CLAUDE.md overrode the scratchpad and caused the regression.
C. The graveyard failure mode — resolved entries were never pruned, so stale notes propagated into current decisions.
D. Missing session-start read — the agent never loaded the scratchpad and defaulted to earlier training priors.

**Answer:** C
**Explanation:** The deck defines the graveyard failure mode as entries accumulating without removal until the file reflects everything that was ever true about the project, including things no longer true. The agent treats all of it as current state. The fix is a line-cap with a pruning trigger, removing resolved entries at the end of the session that resolves them. The other options describe related hygiene issues but not the specific failure the scenario presents.

## Question 4

A scratchpad file contains an entry from last week stating 'use module A for caching.' Today's CLAUDE.md says 'use module B for caching — decision finalized.' The agent is about to start a new session. According to the deck, which source takes precedence and why?

A. Whichever file the agent reads first determines which instruction it follows.
B. The conflict should be flagged to the developer; neither file should be trusted until a human resolves it.
C. The scratchpad takes precedence — it is more recent and reflects the last session's decisions.
D. CLAUDE.md takes precedence — it holds stable rules and the scratchpad entry is superseded session state.

**Answer:** D
**Explanation:** The deck draws an explicit boundary: CLAUDE.md holds stable rules that apply across all sessions and changes rarely; the scratchpad holds evolving session state that changes every session. When they conflict, CLAUDE.md wins. That priority must be stated explicitly in CLAUDE.md itself so the agent does not try to reconcile contradictions in unpredictable ways.

## Question 5

A main agent is investigating a large codebase to locate the request-signing logic. After spawning a subagent, the agent receives a response containing the relevant file path, the function name, and a two-sentence summary — nothing else. What characteristic of this interaction best illustrates the delegation pattern working correctly?

A. The subagent's reads stayed inside its disposable context and were discarded on return, keeping the parent's context clean.
B. The subagent finished faster than inline discovery would have, reducing the total wall-clock latency of the overall task.
C. The subagent used only read-only tools, which prevented it from making any unintended changes to the codebase during the search.
D. The subagent flagged its uncertainty so the parent could choose whether to verify the finding before acting on the result.

**Answer:** A
**Explanation:** The delegation pattern isolates verbose discovery work inside a disposable subagent context. The parent benefits because all the intermediate file reads and dead ends never cross the context boundary — only the structured finding arrives. The return contract defines what that finding looks like, and a narrow, structured response is the signal that the contract was honored.

## Question 6

A team debates whether to spawn a subagent to look up the value of a single well-known configuration key in a file they already have open. What guidance from the delegation pattern applies here?

A. The team should spawn a subagent to preserve the parent's token budget for higher-priority reasoning work.
B. The answer depends on whether the configuration file has changed recently; stale files always justify a subagent to ensure accuracy.
C. Delegation overhead — latency, tokens, and coordination — is not worth it for a single known-location lookup; read the file inline.
D. Delegation is appropriate here because even small lookups benefit from a disposable context that isolates noise from the parent.

**Answer:** C
**Explanation:** The deck establishes a rough breakeven at three or more sequential file reads. Below that threshold the latency, token cost, and coordination overhead of spawning a subagent outweighs the context-cleanliness benefit. A single known-location lookup is the clearest case where inline discovery is cheaper and simpler.

## Question 7

A team writes a subagent prompt that says: 'Investigate the authentication module and explain how it works.' The subagent returns a multi-paragraph narrative. Which failure mode does this illustrate, and what does the deck identify as its root cause?

A. Scope creep, where the subagent exceeded its specified directories and returned extra findings the parent had not requested.
B. Blind trust, where the parent forwarded a large, unverified output downstream without spot-checking any of its claims.
C. Tool palette overflow, where giving the subagent write access caused it to generate side effects rather than a clean answer.
D. Wall-of-text return, caused by an open-ended prompt with no defined return shape or stop condition.

**Answer:** D
**Explanation:** The deck names the wall-of-text return as the first of three common failure modes. A narrative response defeats the purpose of delegation by re-polluting the parent's context. All three failure modes share the same root cause: insufficient specification in the original prompt, specifically the absence of a defined return shape and stop condition.

## Question 8

A subagent prompt specifies: the question to answer, the directories to search, the format of the response (one file path plus one function name), and a rule to stop after reading five files. Which element of a well-formed subagent prompt does the stop rule represent?

A. The stop condition — the rule telling the subagent when to return what it has rather than continuing its search.
B. The trust boundary — the parent-side rule to treat any subagent output as a hypothesis that may require independent verification.
C. The scope constraint — the directive specifying which parts of the repository the subagent is permitted to search.
D. The return shape — the format specification governing what the subagent delivers at the conclusion of its investigation.

**Answer:** A
**Explanation:** The deck identifies four elements a well-formed subagent prompt must include: the question, the scope, the return shape, and the stop condition. The stop condition tells the subagent when to return what it has rather than continuing to search, preventing late and overly verbose returns on hard lookups.

## Question 9

A production personal assistant needs to resume a user's weeks-old conversation with full context on their ongoing goals, while also giving the model precise access to the last few exchanges. Which memory strategy does the deck recommend for this requirement?

A. Use goal anchoring alone, re-stating the user's original objectives at the start of each turn to prevent goal drift.
B. Store the complete conversation history in an external database and reload all prior turns at the start of each session.
C. Inject a persisted summary header at each API call's start while keeping the last N turns verbatim in context.
D. Apply full summarization to compress all prior turns into a single compact paragraph before each new session opens.

**Answer:** C
**Explanation:** The deck describes the hybrid memory pattern as the most practical approach for systems needing both recency and long-term continuity. It combines a persisted session summary header (injected at the top of each API call) with the last N turns kept verbatim in context. This gives the model grounded prior context for cross-session continuity and precise access to recent exchanges simultaneously.

## Question 10

A long-running code co-pilot session has drifted away from its original refactoring goal after a sequence of tangential questions. Which technique from the deck most directly addresses this drift problem?

A. Apply full summarization to compress the accumulated tangential turns before the next exchange begins.
B. Re-state the user's original refactoring goal at the start of each turn to keep the model anchored to the intended task.
C. Apply the sliding window technique to retain only the most recent turns and discard the tangential history.
D. Switch to external memory so the tangential turns are stored outside the context window and no longer influence the model.

**Answer:** B
**Explanation:** The deck names three coherence techniques for long sessions: the session header pattern, explicit state tracking, and goal anchoring. Goal anchoring re-states the user's original goal at the start of each turn and is described as the simplest technique and often the most effective for multi-step workflows where scope creep is the primary risk.
