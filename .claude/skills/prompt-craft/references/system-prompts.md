# System prompts and standing instructions

Applies to system prompts and CLAUDE.md-style files: text that sits behind every turn.

## Placement

- Stable content goes in the standing prompt: role, standing rules, format defaults, background knowledge needed on every response. Changing content goes in the per-request turn: the request, dynamic data, per-request variables. [CCAR 13]
- Dynamic data inside the standing prompt loses cache efficiency and is reprocessed every exchange. Standing rules placed in a single turn can be overridden or ignored later in a multi-turn conversation. [CCAR 13]
- Persistent behaviour (tone, audience, scope, format defaults) belongs in the standing prompt; a one-off structure belongs in the turn where it will not linger. [CCAR 14]
- A standing prompt is paid for on every request: start with what correctness needs, trim what is redundant or over-prescriptive, measure consistency after each trim. [CCAR 13]

Done when every line sits in the place that matches how often it changes. [CCAR 13]

## Sections

Cover five jobs; a missing section is filled by model defaults that may not match intent. [CCAR 13]

1. Role: expertise and communication style. [CCAR 13]
2. Context: background for the whole session (domain knowledge, policy, reference data). [CCAR 13]
3. Instructions: task steps, response format, workflow behaviour. [CCAR 13]
4. Constraints: prohibited topics, tone limits, length limits. [CCAR 13]
5. Examples: how the instructions turn into output, placed last so they illustrate rules already stated. [CCAR 13]

Role first, because it frames how every later instruction is read. Instructions before constraints. Long reference material above the query. [CCAR 13]

## Role, persona, context

- Role sets what the model is good at and how it reasons; persona adds a name, a voice and stylistic rules, and is optional. Role needs no name or personality. [CCAR 13]
- Role and persona change framing, not capability: a role does not supply facts the model lacks and does not bypass safety behaviour. Supply the facts as injected context. [CCAR 13]
- Make persona rules specific ("warm tone, under 200 words, no jargon, acknowledge the concern before the solution"); "friendly and professional" leaves room to drift. [CCAR 13]
- Inject facts the model cannot know (internal policy, the user's record, the uploaded document) directly into the prompt. Injected data that is buried or contradicts training priors may be ignored: test that it is used. [CCAR 13]

## Conflicts and redundancy

- Audit for pairs of rules that can apply at once ("be concise" with "always explain your reasoning") and rewrite them as conditionals: "Be concise unless the user asks for an explanation." [CCAR 13]
- State each rule once, in the right place. Repeating a rule in the standing prompt and again in every turn adds noise, not strength. [CCAR 14]
- Steer with the lightest control that reliably gives the shape needed. State one rule per condition, as a conditional, and leave the content room it needs. [CCAR 13, 14]

## Testing a standing prompt

Run SKILL.md step 7 and `references/testing-prompts.md`, with these cases added: varied phrasings, adversarial inputs that try to contradict the constraints, boundary inputs (very long, empty, a sudden topic switch mid-session). For a role, add topic switches, use of the injected data, and a persona-override attempt. [CCAR 13]

Done when the prompt holds under varied phrasings, adversarial inputs and boundary inputs, and the last edit broke no earlier case. [CCAR 13]

## Untrusted content

XML tags give clarity, not injection defence: treat tool and document content as untrusted and give the agent least privilege. [CCAR 13]
