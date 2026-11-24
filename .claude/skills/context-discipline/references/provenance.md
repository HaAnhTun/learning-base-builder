# Provenance and conflicting sources

## Claim-to-source record [CCAR 19]

Each claim keeps:

- the claim text
- the identifiers of every source that supports it, stable across edits and moves (`path@<sha>:line`, URL, document id)
- optionally, a confidence per source

Place the pointer next to the claim. A closing source list says which sources exist, not which sentence came from which; accept it only for low-stakes output where review time is short.

## Labeling inputs [CCAR 13]

- One block per document with its own source id (and index when instructions refer to documents by position).
- When only some documents should inform a part of the answer, name them ("document 2", "source A") rather than "the documents" or "the context"; vague references are a main cause of output bleed (a claim credited to the wrong source).

## Verify

- Check a risk-weighted sample of claims against their pointers; follow the pointer, read the passage, judge whether it supports the claim. [CCAR 19]
- For high-stakes output, check every citation before finalising. A fabricated citation has a plausible title, author and date; the document either does not support the claim or does not exist.
- A self-reported confidence is the model's opinion. Trust it only after comparing it with known correct answers; re-check after a prompt or model change. [CCAR 19]

## Conflicts [CCAR 19]

1. **Detect before synthesising**: find passages on the same topic, then test whether one contradicts the other.
2. **Annotate**: "Source A says the policy changed in 2022; Source B says 2019; unresolved." Averaging two claims into a vague middle, or silently picking one, hides the choice from the reader.
3. **Resolve with a stated rule**:
   - prefer newer: facts that evolve (versions, prices, regulations)
   - prefer authoritative: fix the source hierarchy in advance (official standard over blog)
   - escalate to the user: when neither rule settles it and the stakes are high
4. **Log** the conflicting claims with their source ids, the rule applied, the claim chosen and the one discarded, so a later reader sees a decision, not false consensus.

Where to show it, by stakes: inline beside the claim for high stakes, a footnote or collapsible note for medium, a closing conflict summary for a full-document review.

Repo facts: when a state note or doc disagrees with code, git or config, report the disagreement and apply the precedence in `.claude/skills/project-state/SKILL.md` (What belongs where; CLAUDE.md, then code, git and config, then state notes) instead of picking silently.
