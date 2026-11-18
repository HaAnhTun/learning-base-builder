# Claude Certified Architect (CCAR-F) - 2026 Exam Prep

- Nguồn: udemy (luvina.udemy.com/course/certified-claude-architect-masterclass-2026/)
- Ngôn ngữ: en
- Đơn vị xuất: chapter
- Số bài: 136 · Số file: 21

## 01 - Welcome.md

- Chapter 1: Welcome
  - 1. Welcome to the Course
  - 2. Quick Conversation About the Course

## 02 - D1 Agentic Architecture - Foundations.md

- Chapter 2: D1: Agentic Architecture - Foundations
  - 3. Agents, Workflows, and Chatbots — What's Actually Different
  - 4. Tool Use as the Foundation of Agency
  - 5. Perception, Reasoning, Action, and Observation
  - 6. Loop Control — Stopping, Iterating, and Escalating
  - 7. Quick Check-In
  - 8. When Workflows Outperform Agents
  - 9. Choosing the Right Architecture

## 03 - D1 Agentic Architecture - Task Decomposition & Planning.md

- Chapter 3: D1: Agentic Architecture - Task Decomposition & Planning
  - 10. Breaking Complex Goals Into Actionable Subtasks
  - 11. Decomposition Patterns — Hierarchical, Sequential, and Parallel
  - 12. Sequential Pipelines — Design and Tradeoffs
  - 13. Parallel Execution — Fan-Out, Fan-In, and Synchronization
  - 14. Adaptive Planning — Updating the Plan Mid-Execution
  - 15. Handling Ambiguity and Incomplete Specifications

## 04 - D1 Agentic Architecture - Multi-Agent Orchestration.md

- Chapter 4: D1: Agentic Architecture - Multi-Agent Orchestration
  - 16. The Orchestrator Role — Directing, Delegating, and Aggregating
  - 17. Subagent Design — Scope, Authority, and Isolation
  - 18. Multi Agent Topology and Selection
  - 19. Designing Agent-to-Agent Message Schemas
  - 20. Handoff Protocols and Continuity Across Agents
  - 21. In-Context State vs. External Memory
  - 22. Session Continuity Across Turns and Failures

## 05 - D1 Agentic Architecture - Reliability & Human Oversight.md

- Chapter 5: D1: Agentic Architecture - Reliability & Human Oversight
  - 23. Multi-Agent Cost and Fit
  - 24. Tool Errors, Reasoning Errors, and Environment Errors
  - 25. Error Detection — Identifying Failures Before They Cascade
  - 26. Retry Logic — When to Retry, When to Abort
  - 27. Fallback Chains and Graceful Degradation
  - 28. Why Prompts Are Not Sufficient for High-Stakes Paths
  - 29. Designing Programmatic Validation and Enforcement Layers
  - 30. Hook Lifecycle Events
  - 31. Interruption Points and Review Workflows

## 06 - D2 Tool Design & MCP - Tool Design Fundamentals.md

- Chapter 6: D2: Tool Design & MCP - Tool Design Fundamentals
  - 32. How Claude Selects Tools — The Role of Descriptions
  - 33. Writing Tool Descriptions That Route Correctly
  - 34. Designing Tool Input Schemas for Precision and Reliability
  - 35. Required vs. Optional Parameters, Enums, and Constraints
  - 36. Strict Tool Use and Valid Inputs
  - 37. Returning Useful Errors from Tools
  - 38. Tool Retry Logic and Partial Success Patterns
  - 39. Tool Scoping per Agent — Why Less Is More
  - 40. Selection Heuristics and Tool-Selection Failures
  - 41. Controlling Tool Selection
  - 42. Tool Search for Large Catalogs

## 07 - D2 Tool Design & MCP - Building MCP Servers.md

- Chapter 7: D2: Tool Design & MCP - Building MCP Servers
  - 43. What MCP Is and Why It Exists
  - 44. Tools, Resources, and Prompts — The Three MCP Primitives
  - 45. Building Your First MCP Server in Python
  - 46. Defining and Exposing Tools via MCP
  - 47. Defining and Exposing Resources
  - 48. MCP Prompt Templates — Design and Use Cases
  - 49. Implementing MCP Clients and Connecting to Servers

## 08 - D2 Tool Design & MCP - MCP Production & Built-in Tools.md

- Chapter 8: D2: Tool Design & MCP - MCP Production & Built-in Tools
  - 50. STDIO Transport — Local Servers and Process Communication
  - 51. StreamableHTTP Transport — Remote Servers and Production Deployment
  - 52. Letting Servers Make LLM Calls Through the Client
  - 53. Notifications, Roots, and Progress Reporting
  - 54. Tool Boundaries, Access Scoping, and Least Privilege
  - 55. MCP in Production — Authentication, Versioning, and Reliability
  - 56. The Built-in Toolset — What Ships with Claude
  - 57. Choosing Built-in vs Custom — Boundaries and Tradeoffs

## 09 - D3 Claude Code - Architecture & Setup.md

- Chapter 9: D3: Claude Code - Architecture & Setup
  - 58. What Claude Code Is and How It Works
  - 59. The Tool System — Reads, Bash, Edits, and Web Search
  - 60. Starting a Project — Setup, Onboarding Claude to a Codebase
  - 61. Adding and Managing Context Effectively
  - 62. Claude Code Permission Modes

## 10 - D3 Claude Code - CLAUDE.md Configuration.md

- Chapter 10: D3: Claude Code - CLAUDE.md Configuration
  - 63. The Three-Level CLAUDE.md Hierarchy
  - 64. Load Order and Conflict Resolution
  - 65. Subdirectory CLAUDE.md Files and Scoped Instructions
  - 66. Excluding Files and Content
  - 67. Path-Scoped Rules for Conventions
  - 68. Writing Instructions Claude Follows
  - 69. Common CLAUDE.md Patterns for Real Teams
  - 70. Quick Check-In

## 11 - D3 Claude Code - Slash Commands, Skills & Subagents.md

- Chapter 11: D3: Claude Code - Slash Commands, Skills & Subagents
  - 71. Creating and Structuring Custom Slash Commands
  - 72. Command Design Patterns and Team Distribution
  - 73. What Skills Are and When to Build Them
  - 74. Authoring Agent Skills
  - 75. Creating and Configuring Custom Subagents
  - 76. Designing Subagents for Delegation
  - 77. Hook Lifecycle Events
  - 78. Plan Mode — When and Why to Plan First
  - 79. Iterating on a Plan — Approve, Edit, Re-Plan

## 12 - D3 Claude Code - Hooks, SDK & CICD.md

- Chapter 12: D3: Claude Code - Hooks, SDK & CI/CD
  - 80. Real-World Hook Applications — Logging, Linting, Safety Nets
  - 81. The Claude Agent SDK — Session Control
  - 82. Claude Code in CI/CD Pipelines

## 13 - D4 Prompt Engineering - Writing Effective Prompts.md

- Chapter 13: D4: Prompt Engineering - Writing Effective Prompts
  - 83. Clarity, Specificity, and the Cost of Ambiguity
  - 84. Instruction Decomposition and Constraint Design
  - 85. The System Prompt — Purpose, Structure, and Best Practices
  - 86. Role Assignment, Persona Design, and Context Setting
  - 87. Using XML Tags to Structure Complex Prompts
  - 88. Document Structure Patterns for Multi-Part Tasks

## 14 - D4 Prompt Engineering - Advanced Prompting Techniques.md

- Chapter 14: D4: Prompt Engineering - Advanced Prompting Techniques
  - 89. Why Examples Work — Pattern Matching and Format Anchoring
  - 90. Designing High-Quality Few-Shot Examples
  - 91. Chain-of-Thought — Prompting for Visible Reasoning
  - 92. Extended Thinking — When and How to Use It
  - 93. Steering Model Output
  - 94. Temperature, top_p, and top_k Explained
  - 95. Designing Effective Multi-Turn Interactions
  - 96. Conversation State, Context Accumulation, Turn Management

## 15 - D4 Prompt Engineering - Structured Output & Evaluation.md

- Chapter 15: D4: Prompt Engineering - Structured Output & Evaluation
  - 97. JSON Mode and Schema-Constrained Output
  - 98. Schema Design for Reliable Extraction
  - 99. Structured Outputs Limits
  - 100. Using Tool Definitions to Extract Structured Data
  - 101. Validation Loops and Hallucination Prevention
  - 102. Validation Gates and Retry Strategy
  - 103. Multi-Pass Review — When One Pass Is Not Enough
  - 104. Building a Prompt Evaluation Workflow
  - 105. Test Dataset Generation and Model-Based Grading
  - 106. Batch Processing at Scale

## 16 - D5 Context Management - The Context Window.md

- Chapter 16: D5: Context Management - The Context Window
  - 107. How the Context Window Works — Tokens, Limits, and Tradeoffs
  - 108. Context Window Economics — Cost, Speed, and Quality
  - 109. Why Summaries Lose Facts
  - 110. Designing a Persistent Fact Block
  - 111. The Memory Tool for Persistence
  - 112. The Tool-Output Bloat Problem
  - 113. Trim Strategies — Filter, Summarize, Reference

## 17 - D5 Context Management - Multi-Agent Failure Modes.md

- Chapter 17: D5: Context Management - Multi-Agent Failure Modes
  - 114. When to Escalate — Trigger Design
  - 115. The Handoff Payload — What the Next Actor Needs
  - 116. Where to Catch the Error — Local or Up the Stack
  - 117. Designing the Propagation Contract
  - 118. The Silent Bug — When 'Nothing' Is Ambiguous
  - 119. Disambiguation Patterns and Tool-Wrapper Discipline

## 18 - D5 Context Management - Cross-Session Knowledge & Coherence.md

- Chapter 18: D5: Context Management - Cross-Session Knowledge & Coherence
  - 120. The Scratchpad Pattern — A Durable Memory Slot
  - 121. Designing a Healthy Scratchpad — Hygiene and Limits
  - 122. Why Delegate Discovery to a Subagent
  - 123. Delegation Mechanics — Prompts, Returns, and Failure Modes
  - 124. Long-Conversation Coherence, Compaction, and Session Memory
  - 125. Server-Side Compaction

## 19 - D5 Context Management - Confidence, Sampling & Provenance.md

- Chapter 19: D5: Context Management - Confidence, Sampling & Provenance
  - 126. Per-Field Confidence — Beyond a Single Score
  - 127. Calibrating with a Validation Set
  - 128. Stratified Sampling — Why Random Misses What Matters
  - 129. Routing Low-Confidence Output Through a Review Queue
  - 130. Quick Check-In
  - 131. Claim-to-Source Mappings — Why Every Sentence Needs a Source
  - 132. Conflict Annotation — Surfacing Disagreement in Synthesis

## 20 - Practice Exams.md

- Chapter 20: Practice Exams
  - 133. Before First Practice Exam
  - 134. After First Practice Exam
  - 135. Wrapping Up

## 21 - Bonus.md

- Chapter 21: Bonus
  - 136. BONUS
