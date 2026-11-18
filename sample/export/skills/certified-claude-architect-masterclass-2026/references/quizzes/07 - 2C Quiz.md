# 2C Quiz

> Course: Claude Certified Architect (CCAR-F) - 2026 Exam Prep · D2: Tool Design & MCP - MCP Production & Built-in Tools · 15 questions · pass mark 70% · ANSWER KEY INCLUDED: show a question and its choices first, reveal the answer only after the learner replies

## Question 1

A team is building a Claude Code integration that adds a custom MCP server providing local file search. The server binary will always run on the same machine as Claude Code. Which transport type fits this scenario, and what key characteristic makes it appropriate?

A. StreamableHTTP transport, because HTTP clients are more portable and work on both local and remote hosts.
B. StreamableHTTP transport, because it supports SSE streaming which Claude Code requires to display tool results.
C. STDIO transport, because it encrypts messages between the client and server using TLS over the pipe.
D. STDIO transport, because it spawns the server as a child process over OS pipes with no network configuration needed.

**Answer:** D
**Explanation:** STDIO spawns the server as a child process communicating over stdin/stdout with no network stack required. It is the correct fit when client and server share a machine and a trust boundary. The deck identifies Claude Code's native MCP transport as STDIO, making it the reference model for exactly this pattern.

## Question 2

A developer notices that after a long agent session using STDIO transport, a tool call early in the session produced a result that a later tool call reads from memory without re-querying. Why does this work correctly under STDIO transport?

A. STDIO keeps one server process alive for the entire session, so in-memory state from any tool call remains accessible to subsequent calls.
B. STDIO shares a global state object across all connected clients on the host, so any previous session's results remain available.
C. The MCP client caches every tool response during the session and injects cached values when the same tool is called again.
D. STDIO serializes tool call results to a local cache file automatically, which later calls read instead of re-querying.

**Answer:** A
**Explanation:** STDIO ties one server process to one client session. In-memory state persists across all tool calls within that session because the process stays alive from open to close. No serialization to a database is needed between calls.

## Question 3

A platform team plans to deploy an MCP server that will be shared by a dozen internal tools running on separate machines. They need TLS, authentication, and the ability to push incremental results during long operations. Which transport fits, and which streaming mechanism does it use?

A. StreamableHTTP transport, which uses WebSockets rather than SSE to deliver bidirectional streaming to all clients.
B. STDIO transport with SSE enabled, which extends the pipe model to support streaming across network boundaries.
C. StreamableHTTP transport, which uses Server-Sent Events to push incremental results over a long-lived HTTP connection.
D. A separate SSE transport, which the deck identifies as the dedicated streaming peer to StreamableHTTP.

**Answer:** C
**Explanation:** StreamableHTTP runs the MCP server as an HTTP service accessible over a network, supports multiple concurrent clients, and uses Server-Sent Events (SSE) for streaming incremental results. It is the correct transport whenever clients and the server are on different hosts or more than one user needs access.

## Question 4

A solution architect is deciding between stateless and session-based state for a new StreamableHTTP MCP server that must scale horizontally across multiple instances behind a load balancer. Which model should she choose, and why?

A. Stateless HTTP, because any server instance can handle any request without coordination when no per-client state is stored.
B. Session-based state, because the MCP protocol requires a persistent token for all multi-turn tool interactions over HTTP.
C. Session-based state, because the load balancer can route each client to the same instance using the session token.
D. Stateless HTTP, because it stores session context in the SSE event stream instead of on the server.

**Answer:** A
**Explanation:** Stateless HTTP means each request carries all needed context; no per-client state is stored on the server. Any instance in a load-balanced pool can handle any request without coordination. Session-based state requires sticky sessions or a shared backend, which adds complexity and limits horizontal scalability.

## Question 5

An MCP server performs complex document analysis and needs LLM reasoning mid-operation, but the organization's policy requires that all model credentials stay centralized with the client owner. How does MCP sampling address this requirement?

A. The server generates its own model call and submits the result to the client for policy review before returning to the tool caller.
B. The server uses its own API key but routes every call through a shared logging proxy that the client monitors.
C. The client pre-loads the server with a temporary API token at session start, which the server uses directly for model calls.
D. The server sends a createMessage request to the client, which calls the LLM using its own credentials and returns the result over MCP.

**Answer:** D
**Explanation:** Sampling allows a server to request an LLM call by sending a createMessage request to the client. The client holds the credentials and calls the model on the server's behalf, returning the result. The server never holds its own API key, satisfying the centralization requirement.

## Question 6

A server sends a createMessage request with an intelligenceLevel hint of 'high' and lists two preferred model names. The client's policy restricts all calls to a single approved model that is not on the server's list. What happens?

A. The client uses its policy-approved model regardless of the server's hints, because client policy always overrides server preferences.
B. The request fails with an error because the server's preferred models are not available on the client.
C. The client negotiates with the server to agree on a mutually acceptable model before proceeding with the call.
D. The server's intelligenceLevel hint of 'high' triggers an automatic escalation to the client's most capable available model.

**Answer:** A
**Explanation:** Model preference hints in a sampling request are suggestions, not hard requirements. The client is always free to honor, substitute, or override them based on its own policy. Client policy takes precedence; the server cannot force a specific model.

## Question 7

An MCP server tool processes a large file upload and sends periodic updates during execution. A developer debugging a separate issue also wants to see which sub-steps completed. Which notification types should the server emit, and for what purpose?

A. Progress notifications tied to the operation token for user-facing status, and log notifications with severity levels for diagnostic sub-step visibility.
B. Progress notifications for both purposes, because they include an optional message field that can carry diagnostic text.
C. A single log notification type that carries both a numeric counter and diagnostic text, covering both use cases in one message.
D. Log notifications for both purposes, because severity levels allow filtering for user-relevant events separately from debug-level messages.

**Answer:** A
**Explanation:** Progress notifications carry a numeric value and progressToken tied to the operation, designed for user-facing progress indicators. Log notifications carry severity-tagged diagnostic text for debugging and observability. Both are appropriate here: progress for the user's feedback, logs for the developer's diagnostic view.

## Question 8

A team deploys an MCP server that handles file operations. They want to ensure the server can only read from a specific project directory and cannot access any other path on the machine. Which MCP mechanism enforces this boundary?

A. The server declares a path_scope field in its tool schema, which the client enforces at the OS level before handler execution.
B. The client sends a roots list containing only the approved directory URI, giving the server access to that path and nothing else.
C. The client configures an OS-level permission mask on the server process that prevents reads outside the approved directory.
D. The developer sets a file_access: restricted flag in the server's initialization config, which restricts all operations to the declared base path.

**Answer:** B
**Explanation:** Roots are a list of filesystem URIs the client explicitly grants to a server. The server has no implicit access to any path; access exists only where the client sends a roots grant. Servers that declare the roots capability are expected to treat these paths as hard boundaries.

## Question 9

An MCP server accepts a free-form string argument for a database filter field. During a security review, the team identifies that this allows the model to craft arbitrary SQL-like patterns that downstream code does not escape. What design change best addresses this at the tool definition level?

A. Grant the tool narrower database credentials so that even if a crafted input reaches the database, it can only affect one table.
B. Add a runtime sanitization step inside the handler that escapes SQL wildcards after the argument has been accepted by the schema.
C. Enable MCP roots for the database path to restrict which tables the tool is permitted to query at the protocol level.
D. Replace the free-form string argument with an enum of approved filter values so the server rejects any input outside that set before the handler runs.

**Answer:** D
**Explanation:** The deck identifies overly permissive schemas — accepting free-form strings where an enum would work — as a common scoping mistake. Replacing the free-form argument with an enum of valid values causes the server to reject out-of-range inputs before any handler logic runs, eliminating the injection surface.

## Question 10

A company operates an MCP server where multiple tools all authenticate to backend systems using one shared credential set. A security auditor flags this as a concern. What principle does this violate, and what is the recommended fix?

A. Shared credentials violate least privilege; each tool should have its own credentials scoped only to the systems its function requires.
B. Shared credentials violate separation of duties; the fix is to rotate credentials on a shorter schedule to limit exposure windows.
C. The auditor is describing a defense-in-depth gap; the fix is to add input sanitization at the server boundary to prevent misuse of shared credentials.
D. Shared credentials are acceptable if the server enforces server-side authorization checks before every tool invocation.

**Answer:** A
**Explanation:** The deck identifies shared credentials as a common scoping mistake: when all tools share one credential, compromising any tool exposes every system those credentials can reach. Least privilege requires each tool to have credentials scoped only to its specific function.

## Question 11

A team is deploying an MCP server via StreamableHTTP for internal teams. Their security policy requires that clients prove identity before accessing any tool, and that access be revocable per client without redeploying the server. Which authentication mechanism does the MCP specification recommend?

A. API keys passed in request headers, because they are simpler to implement and sufficient for internal team deployments.
B. Session cookies issued during the initial handshake, which identify the client for subsequent requests within the same session.
C. Mutual TLS, which authenticates both client and server using certificates and satisfies all production security requirements.
D. OAuth 2.0, which the MCP specification designates for StreamableHTTP servers, supporting scoped tokens and standard revocation.

**Answer:** D
**Explanation:** The MCP specification names OAuth 2.0 as the standard authentication mechanism for production StreamableHTTP servers. OAuth supports per-client tokens with scopes and standard revocation flows — capabilities that API keys and mTLS do not provide as cleanly.

## Question 12

An MCP server team removes a tool that several client teams depend on and renames another with different argument types. What versioning approach does the deck recommend to avoid breaking existing clients?

A. Introduce the changes without a version change and notify client teams directly, because semantic versioning is optional for internal deployments.
B. Issue a major version bump, serve both old and new versions during a migration window, and send deprecation notices before retiring the old version.
C. Apply a minor version bump, because the removed tool can be reconstructed by clients that still need it using the new argument names.
D. Apply only a patch version bump and document the changes in release notes; clients can update at their own pace.

**Answer:** B
**Explanation:** Removing tools or changing required argument names/types are breaking changes that require a major version bump. A migration window — serving both old and new versions simultaneously — gives existing clients time to adapt before the old version is retired.

## Question 13

An architect is designing a Claude-powered research assistant that issues multiple web queries per user request. After initial testing, users report noticeable delays in responses. Which characteristic of the web_search built-in tool best explains this behavior?

A. web_search carries a cold-start overhead on each invocation because it spins up an ephemeral container to process the query.
B. web_search adds a full network round-trip per query, and that latency compounds across multiple searches in a single request.
C. web_search constructs queries internally from context, so the model spends extra time interpreting the request before issuing any network call.
D. web_search is computationally expensive per result because it must render, encode, and transmit each snippet before returning it.

**Answer:** B
**Explanation:** The deck explicitly covers cost and latency as real architectural factors. web_search adds a full round-trip for each query, and that latency compounds when multiple searches fire per request. The architect needs to account for this in the latency budget, or consider a custom tool backed by a faster internal service.

## Question 14

A developer is building a Claude-based workflow that queries the company's internal customer database and logs every tool call to a compliance audit trail. After reviewing options, the team considers using the web_search built-in for its zero-schema convenience. Which two conditions from the decision framework most directly rule out this choice?

A. The workflow requires a domain-specific schema, and built-in tools can never be combined with custom tools in one workflow.
B. Built-in tools evolve between model releases, and pinning behavior through system prompts is insufficient for a compliance-sensitive workflow.
C. The web_search tool adds too much query latency for a real-time customer-facing workflow, and the internal dataset exceeds provider rate limits.
D. The internal database sits behind a private network boundary, and the audit trail needs per-call traceability built-ins cannot give.

**Answer:** D
**Explanation:** The deck lists four conditions that signal a custom tool is required: domain-specific schemas, internal APIs behind a private network, regulated data that must not leave a controlled environment, and audit trail requirements that built-ins cannot expose. Querying an internal database and logging every call each trigger a distinct condition, making a built-in the wrong choice regardless of convenience.

## Question 15

An architect plans a hybrid Claude deployment where web_search handles public research and a custom MCP server handles proprietary data. To speed up development, the developer names the custom MCP tool 'web_search' so it shares the same routing logic. What problem does the deck warn this will cause?

A. The hybrid pattern breaks down because built-in tools and custom MCP servers cannot coexist in the same API request when any names overlap.
B. The custom tool's schema will fail validation immediately because the API rejects any tool definition that duplicates a reserved built-in name.
C. The model's routing becomes unpredictable — it may invoke the wrong implementation, and the issue only surfaces at runtime rather than during schema validation.
D. The custom MCP server will always take precedence over the built-in, silently replacing web_search behavior for all public research queries.

**Answer:** C
**Explanation:** The deck describes the override pitfall: when a custom tool shares a name with a built-in, the model's routing becomes unpredictable. It may invoke the wrong implementation without any reliable error message identifying which version ran, and the issue only surfaces at runtime rather than during schema validation. The fix is always to use distinct names.
