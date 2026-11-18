# 5A Quiz

> Course: Claude Certified Architect (CCAR-F) - 2026 Exam Prep · D5: Context Management - The Context Window · 12 questions · pass mark 70% · ANSWER KEY INCLUDED: show a question and its choices first, reveal the answer only after the learner replies

## Question 1

A team is building a RAG-based customer support agent. Before any user message arrives, the system loads a 1,200-token system prompt, injects three retrieved document chunks averaging 800 tokens each, and appends the last ten conversation turns. A developer argues that output tokens are fine to ignore since they are small. Which statement best describes the actual token accounting?

A. Every component counts: system prompt, history, retrieved chunks, and the model's output tokens all reduce the available context budget.
B. Input tokens from the system prompt, history, and documents all count, but output tokens are separate and do not reduce available input headroom.
C. Retrieved document chunks are excluded from token limits because they are injected after the main prompt is processed by the model.
D. Only the current user message and the model's response count; system prompts and retrieved chunks are preprocessed before the limit applies.

**Answer:** A
**Explanation:** The context window limit applies to every component of the request: system prompt, conversation history, retrieved documents, tool schemas, and the model's own output tokens. Output tokens also count against the window and are typically billed at a higher rate. Ignoring any component risks unexpected failures or truncation in production.

## Question 2

An agent handles customer sessions that can run 30+ turns. In load testing the team discovers that responses late in a session become inconsistent, ignoring constraints stated at turn five even though those turns are technically still within the context window. The context window is not yet full. What phenomenon explains this behavior?

A. Context degradation causes the model to give weaker attention to middle-positioned content, reducing recall even when the tokens are present.
B. The model rewrites the system prompt internally after each turn, causing earlier instructions to be silently overwritten by later ones.
C. The API is automatically truncating the oldest messages once the session exceeds a fixed turn count, silently dropping the early constraints.
D. JSON and structured formats in the injected documents are consuming extra tokens, pushing the context past its effective limit faster than expected.

**Answer:** A
**Explanation:** As the context window approaches its maximum, models empirically show lower recall for content that appeared early or in the middle of the context. The model technically has access to the tokens, but its attention mechanism distributes differently at very long contexts, causing inconsistent instruction-following even before the hard limit is reached.

## Question 3

A production agent has a stable 8,000-token system prompt that is repeated verbatim on every one of its 2,000 daily requests. A developer wants to reduce API costs. Which optimization offers the highest return for this specific scenario?

A. Enabling streaming responses so that output tokens begin arriving sooner and reduce the user's perceived latency.
B. Marking the stable system prompt as cacheable so each subsequent request reuses the stored KV at a reduced rate.
C. Splitting the system prompt into multiple smaller prompts sent in parallel requests to reduce per-request token load.
D. Switching to a smaller model tier to reduce per-token rates across all requests.

**Answer:** B
**Explanation:** When a large, stable system prompt is repeated across thousands of requests, marking it as cacheable means the first request computes the KV cache and every subsequent request reuses it. Cached tokens are billed at a significantly lower rate and time-to-first-token drops because prefix computation is skipped — delivering both cost and latency improvements simultaneously.

## Question 4

A developer is designing a document Q&A agent. To ensure accuracy, they plan to inject all ten retrieved document chunks into the context on every query, reasoning that more context provides more complete information. A colleague argues this approach may actively hurt quality. What is the strongest argument for the colleague's position?

A. Injecting all ten chunks increases output token count because the model generates longer responses when given more source material.
B. Irrelevant chunks compete with relevant content for model attention, diluting the signal and potentially lowering response accuracy.
C. Larger context windows are only available on higher-tier models, so the agent would need to be upgraded before this approach is viable.
D. The latency cost of processing ten chunks will exceed the API's time-to-first-token limit, causing requests to time out.

**Answer:** B
**Explanation:** Irrelevant tokens are not neutral filler — they compete with relevant content for the model's limited attention. Including loosely relevant chunks dilutes the signal from the truly relevant ones, can introduce contradictory passages that cause inconsistent responses, and may reduce instruction-following precision. High retrieval precision produces better results than maximum volume.

## Question 5

An agentic pipeline runs customer onboarding sessions that can span 40 turns. The pipeline uses rolling history summarization to stay within the context window. After 20 turns, the agent incorrectly uses an old rate limit that the user explicitly corrected at turn 12. No error is surfaced. Which summarization property is the direct cause?

A. The agent's system prompt does not include the current rate limit, so the model defaulted to a hardcoded fallback value on every turn.
B. Summarization compresses older turns into narrative, silently dropping exact numeric values like rate limits with no error signal.
C. The model's context window was exceeded, causing the turn-12 correction to be hard-truncated from the history.
D. Compounding loss from multiple summarization passes caused the session goal itself to be forgotten, making the rate limit irrelevant.

**Answer:** B
**Explanation:** History summarization trades specificity for fluency and does so silently — the model does not flag what was compressed away. Numeric limits like rate limits are among the four most vulnerable fact categories and are frequently compressed to vague narrative like 'a limit was mentioned,' causing the agent to revert to an earlier or hallucinated value without any visible error.

## Question 6

A long-running support agent stores extracted facts in a persistent block. Early in a session the customer's plan tier is recorded as Basic; mid-session they upgrade to Premium and a new entry is written. Using the append-only update strategy from this lesson, what problem can arise?

A. The new Premium entry silently overwrites Basic, erasing the record of the customer's earlier tier.
B. The block is discarded at each summarization pass, so no extracted facts survive into later turns.
C. The block compresses older entries into a summary, reintroducing the specificity loss it was meant to prevent.
D. Both the old Basic entry and the new Premium entry coexist, so the agent may read the outdated value.

**Answer:** D
**Explanation:** Deck 100 contrasts two update strategies: append-only grows by adding entries and never overwrites, so an outdated value can coexist with the new one and be read back as stale.

## Question 7

A conversational agent tracks a mutable configuration value — the user's chosen retry limit — that gets updated mid-session. The developer must choose between an append-only persistent block and a replace-on-conflict block. The current correct value is what matters; historical values are not needed. Which design choice fits the requirement and why?

A. Neither strategy is suitable; mutable configuration values should be stored in the system prompt, not in a persistent fact block.
B. Either strategy works equally well; the choice only affects block size, not whether the correct value is available to the agent.
C. Append-only is correct because preserving each stated value prevents the agent from ever losing a value the user provided.
D. Replace-on-conflict is correct because only the current value matters and it stays compact by dropping superseded entries.

**Answer:** D
**Explanation:** The choice between update strategies turns on whether the history of a fact's values matters. For mutable configuration like a retry limit, only the latest correct value is needed, making replace-on-conflict the right fit — it keeps the block compact and the current value authoritative. Append-only would preserve old incorrect values and grow the block unnecessarily.

## Question 8

A team builds a persistent fact block and injects it as a separate system block. During debugging they discover that a downstream step failed because it needed a field that the extraction pass had previously recorded as null for that category. They have no log of what the extractor found. What would have made this failure immediately diagnosable?

A. Injecting the fact block at the top of the user turn instead of as a system block would have surfaced the missing field earlier in context.
B. Instructing the extraction prompt to output explicit null for missing categories confirms the extractor ran and found nothing.
C. Using the replace-on-conflict strategy instead of append-only would have preserved the original value and made it retrievable later.
D. Running a round-trip validation check after every extraction would have caught the missing field and triggered a re-extraction before it propagated.

**Answer:** B
**Explanation:** The deck specifies that the extraction prompt should instruct the model to output null for any category where nothing was stated in the turn. This explicit null is the signal that the extractor ran and found nothing, rather than leaving uncertainty about whether the category was checked. Without it, a missing field is indistinguishable from an extractor that never ran the check.

## Question 9

An agent orchestrates a five-step order fulfillment workflow. Each step calls a different internal API that returns a structured response with roughly 60 fields. The agent needs only two to four fields per call. After building the workflow, the team notices accuracy degrading and latency rising. What is the most likely architectural cause?

A. The context window is being exceeded because five API responses together exceed the model's hard token limit, causing request failures.
B. The model tier chosen lacks the context window capacity required for five sequential tool calls, so a higher-tier model is needed.
C. Full API payloads from each step accumulate in the shared context, stacking noise layers that dilute relevant signal and slow later reasoning.
D. JSON-formatted API responses tokenize inefficiently, and five responses together create disproportionate tokenization overhead that strains the model.

**Answer:** C
**Explanation:** In a chained workflow, each untrimmed API response deposits its full payload into the shared context. After five calls, the context holds five layers of unreduced noise. The model must attend to all of it when reasoning on later steps, diluting the signal from relevant fields and causing accuracy degradation. Token cost and latency also increase with every additional untrimmed call.

## Question 10

A team builds a UI dashboard that shows reviewers only the three fields relevant to each tool response, filtering out the other 77 fields. After deployment, the agent's accuracy remains unchanged. A senior engineer says the trim was applied in the wrong place. What does she mean?

A. The dashboard should display all 80 fields so reviewers can catch any trim errors before they affect the model.
B. The dashboard filtering should also compress the responses into natural-language summaries before passing them to the model.
C. Display trim only hides noise from humans; the model still receives the full 80-field payload in context, so accuracy is unaffected.
D. The three-field allowlist is too narrow; the model needs at least 10–15 fields per call to reason accurately about order fulfillment steps.

**Answer:** C
**Explanation:** Display-layer trimming hides noise from human reviewers but does nothing for the model — the full payload still enters the agent's context window on every call. Model accuracy depends on what the model sees in context, not on what the UI shows. Trim must be applied at the tool wrapper, before the output enters context, to actually improve signal-to-noise ratio for the agent.

## Question 11

An agent integrates with a third-party logistics API that changes its response schema monthly — fields get renamed, nested objects are restructured, and new metadata fields are added regularly. The agent needs only three fields per call. Which trim strategy is most appropriate?

A. Model-driven summarization routes the payload through a lightweight model that extracts only the needed fields for any schema.
B. No trimming is needed because the lost-in-the-middle effect only applies to static documents, not to structured API responses.
C. Field-level filtering with a fixed allowlist of three fields, updated manually each month when the schema changes.
D. Reference indirection storing each full response externally and letting the agent fetch on demand when it needs those specific fields.

**Answer:** A
**Explanation:** Field-level filtering requires a stable, versioned schema — when fields are renamed or restructured, a fixed allowlist silently misses them and the agent fails in hard-to-trace ways. Model-driven summarization routes the raw payload through a small model that reads whatever structure arrives and extracts what the agent needs, making it the correct choice when the schema changes frequently.

## Question 12

An agent's trim layer drops 55 of 60 fields from every tool response. Three weeks into production, a downstream workflow step begins failing with a 'missing required field' error. The developer needs to determine which call first caused the problem and whether the field was ever present in tool responses. What production artifact makes this immediately diagnosable?

A. Re-calling the original tool with the same input to check whether the missing field appears in a fresh response confirms availability.
B. The model's response log, which would show whether the model referenced the missing field in its reasoning steps before the failure occurred.
C. The system prompt's allowlist definition, which shows which fields were originally permitted when the trim layer was configured.
D. The trim audit log, which records every discarded field per call so the developer can trace exactly when the missing field was dropped.

**Answer:** D
**Explanation:** A trim audit log is a structured record of every field discarded by the trim layer on each call. When a downstream step fails because a needed field was dropped, the audit log identifies exactly which call discarded it and what was kept, eliminating guesswork and the need to re-call the original tool to recover the data.
