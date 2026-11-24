# Delegation brief for discovery

Brief template and prompt wording: `prompt-craft`. Whether to delegate and the spot-check: SKILL.md step 3.

## Scope and stop inputs

- Scope: directories or file types to search, and which to ignore.
- Stop condition: when to return what it has instead of searching on.
- Pass the facts that bear on the question from the fact block and nothing more; the subagent starts with an empty window.

## Return contract [CCAR 18]

- Default shape: file path, line number, brief summary. Enough to act on, nothing the parent did not ask for.
- State the length cap in the brief; an uncapped answer carries the verbosity back into the parent.
- Findings the parent will cite later carry a stable source id (document id, URL, commit id, or `path@<sha>:line`), so provenance survives the hand-off. [CCAR 19]

## Failure modes, all caused by an under-specified brief [CCAR 18]

| Failure | Cause | Fix in the brief |
| --- | --- | --- |
| Wall-of-text return | No return shape or cap | Add shape and cap |
| Scope creep: extra findings nobody asked for | No scope or stop condition | Add scope and stop condition |
| Blind trust: errors flow downstream | Result used unchecked | Spot-check critical findings |
