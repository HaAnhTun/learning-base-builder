# 5D Quiz

> Course: Claude Certified Architect (CCAR-F) - 2026 Exam Prep · D5: Context Management - Confidence, Sampling & Provenance · 11 questions · pass mark 70% · ANSWER KEY INCLUDED: show a question and its choices first, reveal the answer only after the learner replies

## Question 1

An extraction pipeline assigns a single record-level score of 0.87 to a completed form. A downstream team uses that score to auto-accept the record. Later they discover the address field was incorrect. What does this illustrate about record-level scoring?

A. The model was over-confident on every field in the record, a systematic error that calibration on a labeled validation set would have uncovered.
B. The aggregate score concealed a low-confidence field; per-field scoring would have routed only that field to human review.
C. The review threshold was set too high for this record type, causing borderline-scored records to pass through without any inspection.
D. The extraction schema omitted a confidence sibling for the address field, so no score was emitted for it during extraction.

**Answer:** B
**Explanation:** The deck explains the coarse-confidence problem: a strong aggregate score can conceal individual fields with low confidence. In the example, the address field may have been at 0.40 while other fields were high, pulling the overall score to 0.87 and masking the weakness. Per-field scores would have routed the address field to human review while letting confident fields pass.

## Question 2

An engineer designs an extraction schema where every field object contains both a `value` key and a `confidence` key. The model populates them in a single inference call. What does the deck identify as the main design decision this approach requires?

A. Deciding which fields get a confidence sibling, based on the consequence if that field is extracted incorrectly.
B. Calibrating the 0.0-to-1.0 confidence scale so that the model's emitted scores align with its true internal probability distribution.
C. Choosing whether to run a dedicated second inference pass after extraction is complete to generate the confidence scores.
D. Establishing the routing threshold before extraction begins, so the schema itself can pre-filter which fields are eligible for scoring.

**Answer:** A
**Explanation:** The deck describes schema-based elicitation of per-field confidence: adding a confidence sibling alongside each value key lets the model emit both in one call. The key design decision is choosing which fields receive a confidence sibling, driven by downstream risk. High-stakes fields like dates, monetary amounts, and entity identifiers are the natural starting points.

## Question 3

A team sets their routing threshold at 0.90 based on the model's self-reported confidence, skipping calibration. In production they find that many auto-accepted fields contain errors. What does the deck identify as the failure that caused this outcome?

A. The team used the model's scores without calibration, so the threshold reflected stated confidence rather than real accuracy.
B. The validation set used for calibration was drawn from unrepresentative documents, skewing the accuracy measurements.
C. The schema did not include confidence siblings for the fields that failed, so no scores were emitted for them.
D. The routing threshold of 0.90 was set too low, allowing uncertain fields with borderline scores to auto-accept without review.

**Answer:** A
**Explanation:** The deck describes the calibration trust problem: a model may report 0.90 on fields where it is actually only 60% accurate. Routing thresholds set on uncalibrated scores auto-accept fields the model is wrong about, letting errors into production without any flag. Calibration on a labeled validation set reveals this mismatch before thresholds drive real decisions.

## Question 4

A content moderation system processes ten thousand items daily. One output category is rare but has a 20% error rate; four common categories each have roughly 2% error rates. A team samples purely at random. What problem does the deck predict will occur?

A. The low aggregate error rate will dominate summary dashboards, causing the model to appear more accurate than it truly is overall.
B. Reviewers will become desensitized by the flood of correct items, making them likely to approve rare errors without scrutiny.
C. The rare category will surface only sporadically, letting its elevated error rate stay invisible behind common-category volume.
D. The high-error category will automatically trigger the stakes-weighting lane and receive extra review without any explicit configuration.

**Answer:** C
**Explanation:** The deck explains that random sampling reflects the model's existing output distribution. Rare categories generate proportionally few reviews even when their error rate is much higher than common ones. The result is that the high-risk rare category appears only sporadically in the review queue, error patterns go undetected, and per-category quotas are the fix.

## Question 5

A team wants to apply all three stratification dimensions from the deck simultaneously. A single item scores below the confidence threshold, falls into an underrepresented category, and also carries a high-stakes classification. How should the queue treat this item relative to other pending items?

A. The system should escalate the item to a senior reviewer and pause normal queue processing until the decision is made.
B. The item should be routed through the stakes lane only, since stakes weighting overrides confidence-based routing.
C. The item should enter the standard confidence queue, since category and stakes adjustments only apply to high-confidence outputs that would otherwise bypass review.
D. The item should receive the highest queue priority because it carries three independent risk signals simultaneously.

**Answer:** D
**Explanation:** The deck explains that confidence, category, and stakes are three independent stratification dimensions. When all three overlap on a single item — low confidence, underrepresented category, and high stakes — the item carries multiple independent signals of elevated risk and should be ranked highest in the review queue. The deck states that when signals overlap, those items should be prioritized highest.

## Question 6

A reviewer working in a review queue corrects a wrongly extracted entity name and submits the correction. Beyond releasing the corrected output downstream, what does the deck say this edit action produces for the model team?

A. An audit log entry capturing reviewer identity and decision timestamp, but no signal of value for improving the model's future performance.
B. A labeled correction pair drawn from a real production failure, usable for future model fine-tuning or calibration.
C. A bypass record that marks this input class for expedited automatic processing on all future occurrences of the same pattern.
D. A positive confirmation signal indicating the model had handled this input type correctly before the reviewer's intervention.

**Answer:** B
**Explanation:** The deck describes each reviewer action as a labeled data point. An edit creates an original-plus-correction pair drawn from a real production input and labeled by a domain expert. The deck calls these edit corrections high-value training data because they come from real inputs rather than curated datasets and capture specific failures, making them more useful for fine-tuning or calibration than positive examples alone.

## Question 7

A medical documentation pipeline uses a review queue to inspect low-confidence outputs before they reach clinicians. The product team proposes returning a placeholder to the clinician immediately and fulfilling the reviewed output later. What concern does the deck raise about this approach for this use case?

A. Using a placeholder first requires defining a bypass policy, which introduces accountability gaps before the review queue is operational.
B. Asynchronous review inevitably raises queue depth because reviewers consistently process deferred items more slowly than live ones.
C. Asynchronous review is categorically prohibited in any pipeline that processes personally identifiable health information under HIPAA.
D. When sign-off requires the verified output first, a placeholder won't work; the latency model must reflect this before deployment.

**Answer:** D
**Explanation:** The deck distinguishes synchronous review (downstream consumer waits for a decision) from asynchronous review (a placeholder is returned immediately and the actual output is delivered later). It warns that async requires the downstream system to handle deferred fulfillment, and specifically notes that a medical documentation system needing the correct output before a clinician signs off cannot use a placeholder. Latency model design must happen before deployment.

## Question 8

A team is building a synthesis pipeline that aggregates ten regulatory documents into a single compliance report. A senior reviewer wants to be able to verify any individual sentence in the output against the source document that supports it — without reading the entire report. Which citation approach satisfies this requirement?

A. Append a bibliography listing all source documents at the end of each paragraph
B. Add a numbered footnote section at the end of the full document for all sources
C. Store all source identifiers in a backend schema and omit them from the readable output
D. Place inline citations directly next to each claim so any sentence can be verified

**Answer:** D
**Explanation:** Inline citations sit next to each individual claim and let a reviewer verify any sentence independently against its source. End-of-paragraph lists identify which sources informed a paragraph but cannot tell the reviewer which specific sentence came from which source, so per-claim verification is impossible.

## Question 9

A compliance analyst reviews a synthesis report and notices that every claim cites a plausible-looking source. When she follows several of the source pointers, she finds that some cited documents either do not exist or do not actually support the claims made. What provenance failure mode does this illustrate, and what is the recommended remedy?

A. Schema misconfiguration — resolved by adding confidence scores to each source record
B. Black-box synthesis — resolved by switching to end-of-paragraph citation lists
C. The averaging antipattern — resolved by applying prefer-newer to pick the correct source
D. Fabricated citation — resolved by a verification workflow that checks each source pointer

**Answer:** D
**Explanation:** A fabricated citation occurs when a model attaches a plausible-looking but inaccurate or nonexistent source reference to a claim. Because the output looks properly sourced, reviewers who do not verify the pointer will accept the claim as fact. The remedy is a structured verification workflow that follows source pointers and confirms the cited document actually supports each claim.

## Question 10

A synthesis pipeline processes two source documents that make incompatible claims about a policy's effective date. The pipeline selects the claim from one document, discards the other without logging the choice, and presents the selected date as settled fact. A downstream team later makes a compliance decision based on this output. What problem does this scenario illustrate?

A. Prefer-newer misconfiguration — the newer document's claim was not selected correctly
B. The averaging antipattern — a silent source choice that hid the conflict from readers
C. A fabricated citation — the pipeline invented a source reference that did not exist
D. A conflict log failure — the resolution strategy was not recorded in the audit trail

**Answer:** B
**Explanation:** The averaging antipattern occurs when a synthesis system silently picks one of two conflicting claims and presents it as settled fact without revealing that a competing source existed. The reader has no way to know a choice was made, which can lead to confident decisions built on undisclosed uncertainty.

## Question 11

A knowledge management team is designing a multi-source synthesis pipeline for regulatory compliance reporting. Their source corpus includes government standards bodies, secondary industry guides, and vendor white papers. They need a defined rule set for resolving conflicts when sources disagree. Which combination of resolution strategies does this lesson prescribe?

A. Prefer-newer, prefer-authoritative, and escalate-to-human for unresolvable cases
B. Inline annotation, footnote surfacing, and end-of-document conflict summary
C. Prefer-longer, prefer-cited, and discard-both when two sources disagree on a fact
D. Semantic similarity scoring, entailment checking, and confidence weighting

**Answer:** A
**Explanation:** The three named resolution strategies are prefer-newer (use the more recent document), prefer-authoritative (use the higher-ranked source per a defined authority hierarchy), and escalate-to-human (route the conflict to a reviewer when automated rules cannot resolve it reliably). Each has a specific use case, and a responsible pipeline defines all three before conflicts arise.
