# 4C Quiz

> Course: Claude Certified Architect (CCAR-F) - 2026 Exam Prep · D4: Prompt Engineering - Structured Output & Evaluation · 13 questions · pass mark 70% · ANSWER KEY INCLUDED: show a question and its choices first, reveal the answer only after the learner replies

## Question 1

A schema for contract extraction marks `counterparty_name` as required. In testing, the engineer discovers that some contracts do not name a counterparty at all — they reference only a contract number. Claude fills the field with a plausible company name rather than leaving it empty. What schema design mistake caused this?

A. Marking the field required when source data may be absent, pressuring the model to fabricate a value.
B. Failing to add an enum constraint on the field, which left the model free to choose arbitrary string values.
C. Using a nested schema for the counterparty, which introduced additional compliance risk at each nested level.
D. Omitting a field description, which gave the model no guidance on how to populate the counterparty name.

**Answer:** A
**Explanation:** Marking a field required when the input does not always contain extractable data for it creates pressure for the model to produce a plausible value rather than surface an absence, leading to hallucinated output.

## Question 2

A team building an invoice extraction schema wants reliable date values across thousands of varied invoices. Some invoices write dates as `June 4 2026`, others as `04-06-2026`, and others as `06/04/26`. The schema currently has a `invoice_date` string field with no description. What schema design change would most directly reduce inconsistent date formats in extraction output?

A. Mark the field as optional so the model is not pressured to normalize a date it cannot confidently read.
B. Change the field type from string to integer to force the model to output a numeric timestamp instead of a formatted date string.
C. Add a second field `invoice_date_raw` to preserve the source form alongside the parsed date for downstream reconciliation.
D. Add a field description specifying the expected format (e.g., ISO 8601) so the model normalizes all date variants consistently.

**Answer:** D
**Explanation:** Field descriptions are the primary lever for guiding extraction decisions. Specifying the exact expected format — such as ISO 8601 — in the description prevents the model from adapting to the varied surface forms in source documents.

## Question 3

An extraction pipeline processes legal complaints with two distinct entity types: plaintiffs and defendants, each requiring name, role, and address. A single large tool schema with all fields combined is producing compliance errors and confusing entity boundaries. What architectural pattern does the deck recommend?

A. Add more detailed field descriptions to the single large schema to clarify the entity boundary for the model.
B. Switch to JSON mode, which handles large flat output shapes more reliably than tool use for multi-entity documents.
C. Combine all fields into a single nested object under one tool call to give the model a unified structure to populate at once.
D. Define separate extraction tools for plaintiff and defendant entities so each schema is independently validated and focused.

**Answer:** D
**Explanation:** Composing separate focused tools for logically distinct entities keeps each schema small, reduces the model's simultaneous constraint load, and allows each tool call to be independently validated. Overloading a single schema degrades compliance.

## Question 4

A financial data extraction pipeline passes schema validation on every run but occasionally routes transactions to the wrong account because an extracted `account_type` value is structurally valid yet semantically incorrect — the model inferred the wrong category from ambiguous source text. Which validation layer is missing from this pipeline?

A. Business rule or semantic validation, which verifies values satisfy domain logic beyond structural correctness.
B. Retry logic, which would catch the error by re-extracting until the value stabilizes across multiple attempts.
C. Schema validation, which should be extended to include stricter type checking for string fields like account_type.
D. Citation instructions, which would force the model to produce a source passage alongside every extracted field.

**Answer:** A
**Explanation:** Schema validation is deterministic and catches structural failures but cannot verify that values are meaningful. Business rule validation checks domain logic, and semantic validation confirms that extracted values are consistent with the source text — both are needed to catch failures that pass schema checks.

## Question 5

An extraction pipeline fails validation and the engineer sends a re-prompt that reads: 'Your previous response was incorrect. Please try again.' The model returns another structurally valid but still wrong extraction. What re-prompt design principle did the engineer violate?

A. The re-prompt should have asked the model to regenerate the entire output from scratch rather than correcting the failing fields.
B. The re-prompt should have switched from tool use to JSON mode on the retry to reduce structural constraints on the model.
C. The re-prompt did not name the specific failure or re-include the source text, leaving the model without actionable guidance.
D. The re-prompt should have lowered the temperature to zero to force a deterministic extraction on the second attempt.

**Answer:** C
**Explanation:** Effective re-prompts include the specific validation error, re-inject the relevant source text so the model extracts from evidence rather than memory, and instruct the model to correct only the failing fields. Vague 'try again' instructions give the model no more information than the original prompt.

## Question 6

A pipeline processes thousands of daily insurance claim forms. After deployment, the team observes that one in fifty claims fails schema validation and requires manual rework. The validation loop retries indefinitely until the output passes. What retry budget design principle is being violated?

A. The pipeline should skip schema validation entirely and route all outputs to human review to avoid any automated retry overhead.
B. There is no hard cap on retries, which risks runaway cost and hides systemic prompt problems that should trigger escalation.
C. The validation gate should be relaxed to accept partially valid JSON so that fewer outputs need to be retried.
D. The retry prompt is too specific, giving the model too many correction targets and causing it to fail repeatedly on different fields.

**Answer:** B
**Explanation:** A retry budget is a hard cap on attempts — typically two to three — before escalating or returning a structured error. Unlimited retries risk runaway cost and can mask systemic prompt failures that should trigger investigation rather than infinite looping.

## Question 7

A content generation pipeline retry loop produces outputs that pass format validation on the third attempt but are drifting further from the intended meaning with each successive retry. Which technique does the deck recommend to break a pattern of structurally valid but semantically degrading retries?

A. Raise the temperature slightly and reframe the instruction on each retry to break the model out of the same failure path.
B. Log the failure and silently return the most recent output, since it passes format validation even if semantically imperfect.
C. Increase the retry budget to ten attempts to give the model more opportunities to converge on a semantically correct output.
D. Switch from format validation to schema-only validation so the model has fewer constraints to satisfy on each retry.

**Answer:** A
**Explanation:** When a model gets stuck producing outputs that look valid but degrade semantically, identical retries don't help. A small temperature bump and slight prompt reframing inject variance to break the failure path, while escalating when repeated semantic failures appear signals a prompt design issue.

## Question 8

A team ships a multi-pass review pipeline for a legal summarization tool. The reviewer model is the same model that generates the summaries. After several weeks, engineers notice the reviewer frequently approves summaries that human reviewers later flag as missing key clauses. What architectural limitation explains this?

A. Self-review has built-in confirmation bias; the model rates its own phrasing as intentional and approves flawed output.
B. Multi-pass review adds too much latency for legal documents, causing the reviewer to time out before completing its evaluation.
C. The summarization model is too small to perform meaningful semantic evaluation of its own output in a reviewer role.
D. The reviewer prompt lacks a completeness checklist, so the model approves outputs without checking for required sections.

**Answer:** A
**Explanation:** Self-review uses the same model for both generation and review. The model tends to rate its own outputs favorably — confirmation bias — because it recognizes its own phrasing as intentional. Cross-review uses a different model for an independent perspective, which is more valuable in high-stakes contexts.

## Question 9

A product team is designing a reviewer prompt for a medical triage summarization tool and drafts: 'Review this output and identify any issues.' In testing, the reviewer returns vague feedback like 'the tone could be improved' that does not drive useful revisions. What change does the deck recommend to fix this?

A. Lower the reviewer's temperature to near zero so it consistently identifies the same issues across every review pass.
B. Switch from self-review to a stronger cross-review model, which will produce more detailed feedback from the same open-ended prompt.
C. Remove the reviewer pass and rely on the revision call alone to self-correct without an intermediate critique step.
D. Replace the open-ended instruction with an explicit checklist, each item having a pass/fail condition.

**Answer:** D
**Explanation:** Open-ended reviewer instructions produce vague, inconsistent critiques. An explicit checklist with clear pass/fail conditions for each item, plus a structured critique format naming which check failed and why, produces actionable feedback that drives concrete revisions.

## Question 10

A team runs the full eval suite after every prompt change and tracks four metrics. After a recent edit, pass rate rose from 82% to 89%, but three cases that previously passed are now failing. How should the team interpret this result?

A. The change is a net regression because previously passing cases now fail, and the new version should not be deployed until regressions are resolved.
B. The result is ambiguous and the team should run spot-checks on the failing cases to judge severity before deciding on deployment.
C. The team should add the three failing cases to the dataset as known failures and re-run evals to recalibrate the baseline.
D. The change is acceptable because pass rate improved and three failures represent a small fraction of the total eval suite.

**Answer:** A
**Explanation:** A fix that raises pass rate while introducing newly failing cases is not a net improvement — it has traded one set of problems for another. The regression rate (fraction of previously passing cases now failing) must be zero or declining before a change is promoted to production. Catching regressions before deploy is always cheaper than discovering them from users.

## Question 11

A prompt engineer wants to decide when to run the full eval suite during a development cycle. Which policy is most consistent with the eval-driven workflow taught in this deck?

A. Run evals before every deployment, after any dataset update, and on a regular schedule to catch model-level drift.
B. Run evals only before major prompt rewrites, since minor wording changes are unlikely to affect overall pass rate meaningfully.
C. Run evals after deployment to validate that the change performs as expected on real user traffic instead of synthetic test cases.
D. Run evals whenever pass rate from the prior cycle dropped below a team-defined threshold, to focus effort on declining prompts.

**Answer:** A
**Explanation:** The deck identifies three mandatory triggers: before every deployment (no exceptions for small changes), after any dataset update (to recalibrate baseline metrics), and on a regular schedule to surface model-level drift even when no prompt changed. Skipping evals on 'small' changes is explicitly called out as a failure mode.

## Question 12

A team is building an eval suite for a summarization prompt that produces free-form paragraph outputs. They need to grade outputs against a quality rubric. Which grading approach is most appropriate, and what additional step does the deck require before trusting the scores?

A. Use model-based grading with a scoring rubric, then calibrate by comparing grader output to human labels on a representative sample.
B. Use exact-match grading against a reference summary stored in the test dataset, since summaries should converge on known correct outputs.
C. Use code-based regex grading to check whether required keywords appear in the summary output, then track pass rate across eval runs.
D. Use model-based grading and treat the scores as ground truth once the grading prompt has been written and version-controlled.

**Answer:** A
**Explanation:** Code-based grading only applies when correctness is expressible as a rule; free-form summaries require model-based grading. However, model-graded scores overstate precision without calibration against human judgments. Calibration involves human-labeling a representative sample, comparing grader output, calculating agreement rate, and adjusting the rubric where systematic disagreements appear.

## Question 13

A team is bootstrapping a test dataset for a new customer-facing prompt before any production traffic exists. Which dataset construction strategy does this deck recommend as a common starting path?

A. Wait until production traffic accumulates, then sample real user inputs and label them as the primary dataset source.
B. Use only handcrafted cases and avoid synthetic generation because model-generated test inputs may replicate the same biases as the prompt under test.
C. Begin with handcrafted cases targeting known failure modes, then expand with synthetic generation, and add production samples once the system is live.
D. Generate the full dataset synthetically from the prompt's topic area to maximize coverage before any manual case writing.

**Answer:** C
**Explanation:** The deck describes three dataset sources — handcrafted, synthetic, and production-sampled — and notes that most mature suites combine all three. The recommended bootstrap path when no production data exists is to start with handcrafted cases targeting known failure modes, expand coverage quickly with synthetic generation, and add production samples once the system is live.
