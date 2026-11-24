# Structured output

## Choose the mechanism

| Need | Use |
|---|---|
| The whole reply is data (extraction, a classification label) | schema-constrained structured output on the response [CCAR 15] |
| Arguments of a tool call must be well formed | strict tool use on the tool definition [CCAR 15] |
| Tone, scope, style, loose format | instructions in the standing prompt, optionally one example [CCAR 14] |

- Both schema features rest on the same schema machinery and the same supported subset; use both when a workflow makes validated calls and then returns a structured summary. [CCAR 15]
- No schema feature available: name the fields and value types in words, show one or two examples of the exact shape, and validate in code with a retry path. [CCAR 14, 15]
- Support depends on model and platform: check the current docs for the one in use (supported schema subset, limits). [CCAR 15]
- To force a format, use structured outputs, strict tool use, or an explicit format plus one example. Models from the 4.6 generation on reject a seeded partial assistant turn (prefill) with HTTP 400. [CCAR 14]

## What the guarantee covers

- Shape, not judgment. A vague field description still yields a wrong value inside a valid object. [CCAR 15]
- Two cases break it: a safety refusal and a max-tokens cutoff. Read the stop reason before parsing; on a cutoff, retry with a higher limit. [CCAR 15]
- Keywords outside the supported subset are not enforced during generation: the raw API rejects them, the SDK strips them into the description and validates afterwards. Treat them as suggestions, design them out (flatten recursion, inline references, keep patterns simple), and check those rules in code. [CCAR 15]
- Strict schemas share request-wide budgets (course figures: 20 strict tools, 24 optional parameters combined, 16 union-typed parameters, which include nullable types such as string or null); keep optional and nullable fields to those where absence is a valid result. The first call on a new schema is slower; structural or tool-set changes invalidate the cache, description edits do not. [CCAR 15]

## Schema design

- Mark a field required only when the data is present every time; a required field with no source data pressures the model into a plausible invented value. [CCAR 15]
- Make fields optional or nullable when absence is a valid result; that tells model and downstream code absence is expected. Choose null/omit when code branches on presence, a sentinel such as "unknown" when a uniform shape matters more. [CCAR 15]
- Use enums for any field that drives routing or classification. [CCAR 15]
- Write each description with: what the field means for this document type, the expected format (dates, identifiers, status codes), boundary cases (what counts and what does not), and priority when several candidates exist. [CCAR 15]
- Keep the schema flat where possible; nest objects or arrays of objects only as deep as the task needs, and define required versus optional separately for each nested object. [CCAR 15]
- Name fields for what they mean and put the format in the description. [CCAR 15]

Done when no field is vague, no required field can lack data, and every routing field is an enum. [CCAR 15]

## Test the schema

1. Missing field: input lacking a field yields null or omission, not an invented value. [CCAR 15]
2. Ambiguous input: two plausible matches resolve to the one the description prefers. [CCAR 15]
3. Type boundaries: very long strings, empty strings, zero, negative numbers. [CCAR 15]

Keep these as a small saved set per schema. [CCAR 15]

## Grounding

- Put the source text in the prompt and instruct extraction only from it; absence of evidence then gives an empty field instead of a fabricated one. [CCAR 15]
- Ask for the supporting passage per extracted field so unsupported values are visible. Label each source with an identifier in multi-document extraction. [CCAR 15]
- Combine grounding, citations and enum constraints; each addresses a different failure. [CCAR 15]

## Batch processing

Use the Message Batches API only for work nobody is waiting on (24-hour ceiling, about half the standard cost, no latency guarantee). [CCAR 15]

- Batch requests accept tool definitions, and the model can return a tool call, but a loop that needs your code to execute a tool and reply cannot run inside one batch (single turn, no round trip); split it into rounds or keep it synchronous. [CCAR 15]
- Server tools (web search, web fetch, code execution) run inside a batch request, because Anthropic executes them; only client-executed tools need the round trip. [practice]
- Give every request a `custom_id` and match results by it, never by position: results come back unordered and a positional read attaches data to the wrong record. [CCAR 15]
- Sample a small run first. [CCAR 15]
- Handle all four result states: succeeded, errored (validation error: fix the request; server error: retry), canceled, expired (resubmit). [CCAR 15]
