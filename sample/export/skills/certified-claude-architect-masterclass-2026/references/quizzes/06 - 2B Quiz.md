# 2B Quiz

> Course: Claude Certified Architect (CCAR-F) - 2026 Exam Prep · D2: Tool Design & MCP - Building MCP Servers · 13 questions · pass mark 70% · ANSWER KEY INCLUDED: show a question and its choices first, reveal the answer only after the learner replies

## Question 1

A platform team builds an MCP server that exposes internal knowledge base documents. Six months later, the company adopts a different AI model from a different vendor. The team reports the MCP server required no changes to work with the new model. What MCP design property explains this?

A. The MCP server cached the capability list so it didn't need to re-register tools for the new model.
B. MCP is vendor-neutral: any compliant model uses the same interface without requiring server changes.
C. The server translated its capabilities into a format specific to each model at connection time.
D. Anthropic and the new vendor co-maintain MCP, so both models share the same internal tool-calling API.

**Answer:** B
**Explanation:** MCP is an open, vendor-neutral standard. Servers don't know which model consumes them, and clients don't know which vendor built the server. Because both sides follow the same protocol contract, switching the AI model on the client side requires no server-side changes — the server continues to expose capabilities through the same interface regardless of who is consuming them.

## Question 2

A startup has three separate teams: one owns a database layer, one owns a search service, and one owns the AI application. The database team upgrades their storage system. Which MCP property ensures the AI application team's code doesn't break?

A. Capability lists are versioned, so the client pins to the previous version until the team manually updates.
B. The AI application team subscribes to a database change feed and automatically rebuilds its adapter on each upgrade.
C. The MCP protocol contract stays stable when underlying implementation changes, so the client sees no difference.
D. The MCP client polls the database server on every request to detect interface changes before routing.

**Answer:** C
**Explanation:** In MCP's client-server model, the server exposes capabilities through a stable protocol contract. When the database team upgrades their underlying implementation, they update their MCP server. As long as the server's capability contract stays the same, the client sees no change — it interacts with the protocol, not the implementation. This contract-first design is how MCP reduces coupling across large organizations.

## Question 3

A product manager asks an engineer to build a feature that automatically loads the current company policy document into every compliance conversation before Claude responds. Which MCP primitive fits this requirement, and who controls it?

A. A prompt, controlled by the user, who selects a compliance template that pre-populates the conversation.
B. A tool, controlled by the application, which the host calls before each turn to retrieve and load the document.
C. A resource — the host application injects the document into context automatically before generation.
D. A tool, controlled by the model, which Claude calls when it determines a compliance question is being asked.

**Answer:** C
**Explanation:** Resources are URI-addressable data objects the host application injects into context. Because the decision to load the policy document is made by the application based on business logic (all compliance conversations), not by Claude at reasoning time and not by the user explicitly, this is an application-controlled resource. The host pulls it via resources/read and injects it before generation.

## Question 4

During a CCA-F study session, a candidate is asked: 'Who decides when an MCP tool gets called?' They answer: 'The host application triggers tool calls based on routing rules.' Is this correct?

A. No — the user must explicitly select a tool from a list before Claude can call it.
B. Yes — the application calls tools on every turn and injects the results into Claude's context as resources.
C. Yes — the host routes requests to tools based on keyword rules before passing results to Claude.
D. No — the model decides when to call a tool based on its own reasoning about the conversation.

**Answer:** D
**Explanation:** Tools are model-controlled: the AI model itself decides when and whether to invoke a tool based on its in-context reasoning about what the conversation requires. The host application does not trigger tool calls. The deck explicitly distinguishes this from resources (application-controlled) and prompts (user-controlled).

## Question 5

A developer builds an MCP server and adds a new tool in application code that runs after the `run()` call. When a connected client requests the capability list, the new tool doesn't appear. What is the cause?

A. The client cached the capability list from a previous session and needs to reconnect to pick up new tools.
B. The tool was registered after run() was called, missing the capability list sent at connection time.
C. The stdio transport doesn't support dynamic tool registration, so the tool must be added via HTTP/SSE instead.
D. The server inspector filters out newly added tools until the server is restarted to prevent session inconsistencies.

**Answer:** B
**Explanation:** MCP capability negotiation happens when the client first connects. The server sends the complete list of registered tools at that moment. Any tool added after run() is called is not part of the handshake and remains invisible to the client for that session. All tools must be registered before run() is invoked.

## Question 6

An MCP server handles multiple simultaneous client connections. A developer writes a tool handler that uses a synchronous file-reading library to load large documents. Users report that all requests slow to a crawl whenever the file tool is called. What is the most direct fix?

A. Increase the server's worker process count so each client connection gets a dedicated process.
B. Register the file tool as a resource instead of a tool so the host controls when it's loaded and avoids concurrency.
C. Switch from stdio transport to HTTP/SSE so the server can handle concurrent connections in parallel threads.
D. Use an async file library or wrap the sync call with run_in_executor to avoid blocking the event loop.

**Answer:** D
**Explanation:** The MCP Python SDK uses asyncio for concurrency. A synchronous I/O call inside a handler blocks the entire event loop, stalling every other in-flight request. The correct fix is to use an async I/O library (e.g., aiofiles) or wrap the synchronous call with run_in_executor so it runs in a thread pool and doesn't block the loop.

## Question 7

A developer writes the following docstring for an MCP tool: `'Handles data.'` In testing, Claude rarely calls the tool even when the task clearly matches the tool's actual capability. What is the most likely cause?

A. The server inspector is filtering the tool from the capability list due to a missing return type annotation.
B. The tool's JSON Schema is missing required field annotations, so the model can't construct a valid call.
C. The vague docstring gives no signal about when the tool fits, causing it to lose the routing competition.
D. The decorator registers the tool with the function name, which doesn't match how users phrase requests.

**Answer:** C
**Explanation:** In the MCP Python SDK, the function's docstring becomes the tool description that the model reads when deciding whether to invoke the tool. A vague description like 'handles data' gives the model nothing to match against specific user requests. The deck teaches that the docstring is one of the most important pieces of text written for a server — specificity in descriptions directly determines routing reliability.

## Question 8

A tool handler performs a database query and returns 50 rows of customer records, each with six fields. A second tool in the same pipeline needs to parse those records. What return format should the handler use?

A. A plain string serialized from the rows, because the MCP SDK doesn't support dict returns from tool handlers.
B. A JSON-serializable dict, because the downstream tool needs to parse structured multi-field records.
C. An error dict with isError: true, because large result sets should be paginated before being returned.
D. A plain string formatted as a human-readable table, because the model can extract fields from prose.

**Answer:** B
**Explanation:** The deck distinguishes two return formats: plain text for results the model reads and summarizes, and JSON-serializable dicts for multi-field records or data that another tool will consume. Because the records have multiple fields and a downstream tool must parse them, a structured dict return is the correct choice — the SDK serializes it to JSON automatically.

## Question 9

A host application needs to provide Claude with an always-current copy of a live API response that changes every few minutes. The team doesn't want to poll on every conversation turn. Which MCP mechanism is designed for this scenario?

A. A prompt template that includes the API endpoint URL so users can request fresh data manually when needed.
B. Static resource caching, where the server stores the last known response and serves it until restarted.
C. Resource subscriptions: the client registers interest in a URI and gets notified when content changes.
D. A tool that the model calls on every turn to retrieve the latest API response before generating a reply.

**Answer:** C
**Explanation:** MCP supports resource subscriptions: a client registers interest in a specific URI after the first retrieval. When the server detects the resource has changed, it sends a notification to the subscribed client, which then re-fetches the updated content. This keeps dynamic resources fresh without polling on every request.

## Question 10

A compliance team wants all analysts to run the same structured audit workflow each time they start a regulatory review, with the ability to fill in the regulation name and scope before beginning. They don't want analysts to compose the prompt themselves. Which MCP primitive fits this requirement?

A. An MCP tool that the model calls when it detects a compliance-related question in the conversation.
B. A system prompt injected by the application that hardcodes the audit workflow for all conversations.
C. An MCP prompt template with typed arguments for regulation and scope, chosen by each analyst at start.
D. An MCP resource that injects the audit methodology document into context before every compliance conversation.

**Answer:** C
**Explanation:** MCP prompt templates are reusable, parameterized instructions stored on a server that users select to pre-populate an interaction. They're user-controlled: a human explicitly chooses the template and fills in arguments (regulation name, scope) before the session starts. This is precisely the pattern for compliance workflows where consistency matters and per-analyst ad-hoc prompting is undesirable.

## Question 11

A team has a popular MCP prompt template called `security-review`. They need to roll out an improved version without immediately breaking existing users who rely on the current template. Which versioning strategy does the deck describe as the simplest way to do this?

A. Embed the new prompt body in the client application code so it bypasses the server's template management entirely.
B. Overwrite the existing `security-review` template with the new body; clients automatically receive the update on next use.
C. Register the new template as `security-review-v2`, keeping both entries available so existing users aren't disrupted.
D. Delete the old template and require users to manually reload the server to discover the replacement.

**Answer:** C
**Explanation:** The deck covers three versioning strategies: appending a version number to the name (creating coexisting entries), passing version as a runtime argument resolved server-side, and using a deprecation flag to warn clients before removing old templates. Any of these could fit, but name-based versioning (e.g., security-review-v2) is the simplest approach that lets old and new templates coexist without breaking current users.

## Question 12

An agent framework connects to three MCP servers simultaneously — one for file operations, one for web search, and one for database queries. At runtime, the language model selects a tool named 'search', which exists on both the web-search server and the database server. What prevents the wrong server from receiving the call?

A. The model selects the correct server by reading each server's capability list before invoking the tool.
B. The server with the higher protocol version number is given priority when two servers expose the same tool name.
C. The client uses namespace prefixes tied to each server's registered name to distinguish tools with identical names across different servers.
D. The client re-runs the discovery pass each time a collision is detected and picks the server that responded first.

**Answer:** C
**Explanation:** MCP clients register each server with a unique name. When tool names collide across servers, namespace prefixes derived from the server name disambiguate the call. The client — not the model — resolves which server owns a given tool, making routing transparent and collision-free.

## Question 13

A developer calls list_tools() right after the MCP handshake completes and finds the expected tool is missing. What is the most accurate explanation of why catching this problem at discovery time is valuable, according to the deck?

A. Finding the mismatch at discovery prevents a runtime error that would otherwise surface only when the model attempts to invoke the absent tool.
B. Missing tools trigger a protocol fallback that routes the call to the next registered server without raising an error.
C. Discovery results are broadcast to the model so it can update its internal tool index before making any call.
D. The client re-runs list_tools() automatically on each tool call, so catching the gap at initialization is redundant.

**Answer:** A
**Explanation:** Discovery runs once per session immediately after the handshake. list_tools() returns names, schemas, and descriptions. Catching a missing tool here avoids a silent runtime error later when the model tries to call a tool the server never exposed.
