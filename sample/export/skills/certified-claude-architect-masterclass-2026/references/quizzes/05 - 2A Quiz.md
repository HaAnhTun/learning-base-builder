# 2A Quiz

> Course: Claude Certified Architect (CCAR-F) - 2026 Exam Prep · D2: Tool Design & MCP - Tool Design Fundamentals · 16 questions · pass mark 70% · ANSWER KEY INCLUDED: show a question and its choices first, reveal the answer only after the learner replies

## Question 1

A developer builds an agent with two tools: one named `search_orders` and one named `lookup_products`. Both descriptions simply restate the tool name with no additional detail. A user asks 'Can you find my recent purchases?' and the agent consistently routes to the wrong tool. What is the root cause of this misrouting?

A. The descriptions give Claude no semantic basis to distinguish the tools, so routing is unreliable.
B. The agent has too many tools registered, causing ambiguity across the full catalog.
C. The tool names are too similar, causing Claude to pick arbitrarily between them.
D. The input schemas are not defined, so Claude cannot form the call correctly.

**Answer:** A
**Explanation:** Claude performs semantic matching between the user's request and each tool's description. Tool names are hints, but descriptions carry the routing weight. When descriptions are vague or simply restate the name, Claude has no semantic basis to distinguish tools and misroutes. Writing precise, complete descriptions is the lever the developer controls to fix routing accuracy.

## Question 2

An engineer reviews a production agent log and notices Claude sometimes calls a `send_email` tool when the user asked to retrieve inbox messages, and sometimes calls no tool at all for the same type of request. Which pair of routing outcomes does this log describe?

A. Fallback and misroute — Claude asked for clarification on some requests and guessed wrong on others.
B. Correct call and no-call — the agent succeeded on some turns and silently skipped others.
C. Misroute and no-call — both caused by descriptions that fail to capture intent accurately.
D. No-call and fallback — the tool descriptions were so vague that Claude always declined to act.

**Answer:** C
**Explanation:** The deck defines four routing outcomes: correct call, misroute (wrong tool called), no-call (no tool matched), and fallback (Claude asks for clarification). Calling `send_email` for a retrieve request is a misroute; calling no tool at all is a no-call. Both trace back to description quality as the controllable variable.

## Question 3

A team ships a tool with this description: 'Retrieves order history. Does not handle refunds or returns.' A second tool description reads: 'Manages order modifications including refunds and cancellations.' A user asks to cancel an order and Claude consistently picks the second tool. What technique made the correct routing reliable?

A. The exclusion clause in the first description tells Claude that cancellations are out of scope for it.
B. The tools were ordered in the context window so the second one appears closest to the request.
C. The first tool's description includes a purpose statement, which signals retrieval intent to Claude.
D. The second tool name contains 'modifications', which matches 'cancel' semantically.

**Answer:** A
**Explanation:** The deck teaches a three-part description pattern: what the tool does, when to use it, and what it does NOT handle. The exclusion clause in the first tool ('does not handle refunds or returns') separates it from the second tool, giving Claude an unambiguous boundary to route around. Without that exclusion, both tools would appear equally valid for a cancellation request.

## Question 4

During pre-deployment testing, an engineer sends three types of requests to a new tool: one the tool should handle, one it should not handle, and one that could plausibly match two different tools. What testing pattern does this represent, and what failure mode does each test type expose?

A. Schema test, format test, and output test — verifying argument formation across input types.
B. Load test, regression test, and unit test — standard software testing patterns applied to tool routing.
C. Positive, negative, and disambiguation tests — covering correct selection, misroute prevention, and specificity-based wins.
D. Smoke test, edge-case test, and stress test — confirming the tool works under varied conditions.

**Answer:** C
**Explanation:** The deck defines three structured testing patterns. A positive test confirms correct selection and argument formation. A negative test confirms Claude routes elsewhere or asks for clarification rather than guessing. A disambiguation test confirms the right tool wins on description specificity, not position. Together they give evidence-based confidence across varied inputs.

## Question 5

A developer defines a parameter as `type: string` with the description 'the user ID'. In production, Claude occasionally populates this field with a numeric account number instead of a UUID, causing API calls to fail. What schema change most directly prevents this?

A. Rename the parameter from `user_id` to `uuid` so the name signals the expected format.
B. Move the format specification into the tool-level description rather than the parameter description.
C. Add the field to the required array so Claude always attempts to populate it.
D. Rewrite the description to specify UUID format, source (session token), and hyphen structure.

**Answer:** D
**Explanation:** The deck teaches that parameter descriptions are read by Claude at inference time as micro-prompts. A description like 'the user ID' is technically accurate but underspecified — Claude doesn't know the format, source, or length. A strong description stating the exact format (UUID, hyphenated, 32 hex characters) and source (session token) removes ambiguity and directly improves argument quality.

## Question 6

A schema declares a `report_date` parameter as `type: string` with no additional constraints. Claude sometimes generates values like '2025-06-01', other times '01 Jun 2025', and occasionally 'last Monday'. What JSON Schema property most directly eliminates this variation?

A. Marking `report_date` as required so Claude always includes a value in the call.
B. Renaming the parameter to `iso_date` to signal the expected format through the name alone.
C. Adding a `pattern` or `format: date-time` constraint that enforces a specific date structure.
D. Adding the field to the tool-level description as a bullet point listing acceptable date formats.

**Answer:** C
**Explanation:** The deck explains that JSON Schema constraint properties like `format`, `pattern`, `minLength`, and `maxLength` tighten what Claude can generate. Adding `format: date-time` or a `pattern` requiring ISO 8601 structure removes free-form date interpretation, ensuring Claude always generates a consistently structured value that downstream code can parse reliably.

## Question 7

A batch-processing tool marks five parameters as required: `customer_id`, `date_range`, `output_format`, `locale`, and `timezone`. In production, Claude occasionally hallucinates plausible-but-wrong `locale` and `timezone` values when they aren't mentioned in the conversation. What design principle does this violate?

A. The schema lacks enum constraints on locale and timezone, allowing Claude to generate free-form strings.
B. The tool is receiving too many parameters, causing Claude to confuse which fields apply to which tool.
C. The parameter descriptions are too short to communicate valid locale and timezone formats to Claude.
D. The required set includes fields that have sensible defaults, so Claude hallucinates values it cannot find in context.

**Answer:** D
**Explanation:** The deck warns that marking a field required when the tool can function without it pressures Claude to hallucinate a value when the information isn't in context. Fields like `locale` and `timezone` that can default sensibly should be optional with declared defaults. A lean required set produces more reliable calls because Claude only has to supply values it actually has access to.

## Question 8

A support-ticket tool has a `priority` parameter declared as `type: string`. In practice, Claude generates values like 'urgent', 'URGENT', 'high-priority', and 'critical' — all of which break the routing handler that checks for exact matches. What schema change eliminates this variation with the least implementation overhead?

A. Mark `priority` as optional with a default of 'medium' so Claude omits it when uncertain.
B. Add an `enum` constraint listing the only acceptable values so Claude always picks from the fixed set.
C. Add a `pattern` regex constraint that accepts any capitalization of the valid words.
D. Rename the parameter to `priority_level` to signal that only standard levels are valid.

**Answer:** B
**Explanation:** The deck explains that declaring a parameter as an enum array forces Claude to pick one of the listed values rather than generating a free-form string. Adding `enum: ['low', 'medium', 'high']` to the priority field means Claude always outputs one of those exact strings, making the routing handler deterministic and eliminating the need for a normalization step.

## Question 9

A tool returns HTTP 200 with a JSON body `{ 'status': 'ok', 'error': 'record not found' }` when a lookup fails. Claude proceeds as if the operation succeeded and returns a fabricated result to the user. What error design mistake caused this?

A. The tool returned a success status with the error inside the body, so Claude treated the call as successful.
B. The error message 'record not found' is too vague for Claude to identify the right recovery action.
C. The error_code field used a generic string instead of a stable machine-readable code.
D. The tool did not include a suggested_action field, so Claude defaulted to treating the call as successful.

**Answer:** A
**Explanation:** The deck explicitly calls out this pattern as a common error design mistake: returning a success status (HTTP 200) while burying the error in the response body. Claude may not inspect the body for a hidden error field and will treat the call as successful. A failure should use a failure status with a structured error response so Claude can immediately identify that recovery is needed.

## Question 10

An agent repeatedly calls a `send_notification` tool after receiving an `INVALID_RECIPIENT` error, sending duplicate notifications to incorrect addresses. Which error design element, if present, would most directly prevent this retry loop?

A. A `context` block identifying which parameter contained the invalid value.
B. A `retry_after` delay value that forces Claude to wait before retrying the call.
C. A stable `error_code` string that uniquely identifies the failure type for routing logic.
D. A `suggested_action: ask_user` field signaling that the input is invalid and the user must correct it.

**Answer:** D
**Explanation:** The deck distinguishes user errors (bad input that won't be fixed by retrying) from system errors (transient failures where retry is appropriate). An INVALID_RECIPIENT is a user error — the caller supplied bad data. Including a `suggested_action` of `ask_user` would tell Claude to surface the problem rather than retry. Without this signal, Claude may default to retry behavior that is only appropriate for transient system errors.

## Question 11

A payment processing tool creates a new charge record on each invocation. During a network interruption, Claude retries the tool call and a customer is charged twice. What design change makes the tool safe to retry without this side effect?

A. Mark the payment tool as optional in the schema so Claude skips it when context is ambiguous.
B. Return a partial_success response so Claude knows the first call may have completed.
C. Add a circuit breaker so calls are blocked automatically after the first network failure.
D. Accept a caller-generated idempotency key and return the cached result for any duplicate call.

**Answer:** D
**Explanation:** The deck explains that idempotency is the property that calling a tool multiple times with the same input produces the same result. State-changing tools like payment charges are not idempotent by nature. The standard pattern is for the caller to generate a unique idempotency key per request; the tool stores the key and returns the original response on duplicate calls instead of executing again, preventing double charges.

## Question 12

A batch email tool processes 500 recipients. It succeeds on 490 and fails on 10 due to invalid addresses. The tool returns a generic `{ 'status': 'error' }` response. What response structure does the deck prescribe, and what does it enable?

A. Return HTTP 200 with a message field listing the invalid addresses in plain text.
B. Return a single error code with the count of failures so Claude knows the severity of the problem.
C. Return `partial_success` with a `succeeded` list and a `failed` list with per-item error codes.
D. Raise an exception and let the orchestrator decide whether to retry the full batch.

**Answer:** C
**Explanation:** The deck teaches that a batch tool that partially completes should return a `partial_success` status with a `succeeded` list (IDs that completed) and a `failed` list (per-item error codes and context). This structure lets Claude decide what to retry, what to skip, and what to surface. A generic error hides the succeeded items, risking re-execution of completed operations.

## Question 13

An orchestrator agent is configured with 40 tools covering retrieval, database writes, file operations, logging, and external API calls. The team notices Claude inconsistently routes between two retrieval tools and response latency has increased. Which architectural change does the deck recommend?

A. Decompose into specialist subagents where each receives only the tools its role requires.
B. Add more detailed descriptions to all 40 tools so Claude can distinguish them more accurately.
C. Increase the context window budget so all tool descriptions can load without crowding content.
D. Reorder the tool list so retrieval tools appear first and are evaluated with higher priority.

**Answer:** A
**Explanation:** The deck teaches that every tool description loads into context on every turn, whether used or not, consuming tokens and crowding out needed content. When two tools have overlapping scope and vague descriptions, routing becomes unpredictable. The recommended fix is the specialist subagent pattern: decompose roles so a retrieval subagent gets only search/fetch tools and a write subagent gets only mutation tools, keeping each agent's palette small enough that correct selection is always obvious.

## Question 14

A multi-agent system has a retrieval subagent, a write subagent, and an orchestrator. A logging tool that records structured output needs to be available across all three agents. A junior engineer proposes removing it from the retrieval and write subagents to keep palettes lean. What does the deck say about this?

A. The logging tool creates routing ambiguity and should be replaced with an out-of-band logging mechanism.
B. Logging is a cross-cutting tool that legitimately belongs on all agents producing observable output.
C. The logging tool should be consolidated into the orchestrator only, which relays log events from subagents.
D. Subagents should not perform logging; only the orchestrator needs visibility into workflow progress.

**Answer:** B
**Explanation:** The deck distinguishes tool bloat (tools that end up on agents by accident or convenience) from cross-cutting tools (tools whose scope is genuinely broader than one role). Logging is the clearest example: if every agent that produces output needs to emit structured logs, the logging tool is intentionally shared. The rule is to minimize by design, not eliminate shared tools that serve a genuine cross-agent purpose.

## Question 15

An agent palette contains two tools: `fetch_user_profile` and `get_account_details`. In testing, Claude alternates between them when asked to 'look up a customer.' The team adds a third tool without changing existing descriptions. What is the most likely root cause of the original routing problem?

A. The two tool descriptions overlap in vocabulary and scope, so neither has a clear relevance advantage.
B. The model is ignoring descriptions and routing based solely on function name similarity to the request.
C. The tool palette has grown too large, and the model struggles to score any single tool confidently.
D. Neither tool description closely matches the phrase 'look up a customer,' so the model fabricates a call.

**Answer:** A
**Explanation:** When two tools both look like valid candidates for a request, the model picks non-deterministically — alternating between them across turns. This is a two-good-matches failure, caused by descriptions that share vocabulary and scope without clearly distinguishing which tool wins for which request type. The fix is disambiguation patterns: distinct verbs and narrow scope boundaries in each description.

## Question 16

A team's database query tool begins receiving far fewer calls per hour despite no change in user request volume. The tool's description and implementation are unchanged, but a new search tool was added last week. What should the team investigate first?

A. Whether user request volume has declined for the specific query type that tool handles.
B. Whether the database query tool has a runtime error that silently prevents it from returning results.
C. Whether the tool's JSON Schema has become malformed and is excluded from the active palette.
D. Whether the new search tool's description overlaps the query tool's and diverts its traffic.

**Answer:** D
**Explanation:** Selection drift is the gradual degradation of routing accuracy as descriptions become stale or are outcompeted by new additions. The deck teaches teams to log every tool selection and alert when a tool's call rate drops significantly from baseline — exactly the symptom described. Investigating the new tool's description overlap with the query tool is the correct first move.
