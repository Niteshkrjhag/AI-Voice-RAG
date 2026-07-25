AI Engineer Assessment

Assessment Objective
Build working AI solutions from unstructured business data under real production constraints. Evaluation
prioritizes functional outcomes, measurable results, grounded responses, reliability, and the candidate's ability
to explain technical choices.
Timeline and Scope
• Submission deadline: within 48 hours of receiving the assessment.
• Submit working outcomes for all four questions.
• Questions 1 and 2 are connected: the voice agent must use the knowledge base built in Question 2.
• Recorded calls from Question 1 or 3 may be reused for Question 4.
• Prioritize a reliable core workflow over unnecessary features or visual polish.

Question 1 — Knowledge-Grounded Voice Agent
Objective: Build a functional voice agent for one use case: health-insurance lead qualification, business-loan
qualification, candidate screening, insurance renewal, or loan pre-due reminder.
Required Implementation
• Configure the voice platform and add the provided script and business rules.
• Connect the Question 2 knowledge base; do not hardcode all FAQs, objections, or policies in the system
prompt.
• Design conversation flow, qualification logic, grounded objection handling, unsupported-question
fallback, and human escalation.
• Provide a callable number or web calling interface.
• Record at least three test calls and submit transcripts and results.
Required Test Coverage
• Cooperative customer; objection; incomplete or conflicting details; out-of-scope question;
human-assistance request.
• The bot must state when information is unavailable instead of inventing an answer.
Optional Business Action
Implement one action such as lead creation, callback scheduling, preliminary eligibility, quotation request, mock
CRM summary, or escalation webhook.
Core evidence expected: working call flow, grounded answers, safe fallback, test recordings, transcripts, and
clear results.

Question 2 — Production-Ready Knowledge Base
Objective: Convert mixed business content into a structured, searchable, traceable knowledge base usable by
a voice agent, RAG system, Copilot, or smaller language model.
Input Types
Web pages, product and marketing content, policy or qualification rules, forms, tables, PDFs, duplicated
material, inconsistent terminology, and content containing PII.
Data Collection and Cleaning
• Explain website extraction and document parsing.
• Remove navigation text, headers, footers, repeated sections, and irrelevant content.
• Handle extraction failures and flag obvious source errors.
• Remove duplicate or near-duplicate information.
• Standardize headings, dates, terminology, categories, and form fields.
• Identify and protect personally identifiable information.
Knowledge-Base Design
• Document schema and sample records.
• Chunking strategy and metadata structure.
• Product/policy taxonomy and source tracking.
• Versioning, embedding/indexing approach, retrieval/ranking logic, and citation method.
Field Example
record_id kb_product_001
title Branch Partnership Benefits
content Operational, marketing, and technology support is provided to branch partners.
category / source partnership_benefits / website section
version / PII 1.0 / false

Retrieval Testing
• Submit at least five queries.
• For each: user question, retrieved chunk/record, source reference, relevance explanation, and verdict
(correct / partially correct / incorrect).
• Connect the knowledge base to the Question 1 voice bot or a simple retrieval interface.
• Demonstrate answers for product, policy, qualification, FAQ, and objection questions.
Core evidence expected: traceable records, reliable retrieval, citations, and a working connection between the
knowledge base and the voice agent.

Question 3 — Native-Language Voice Bots
Objective: Build localized prototypes for real financial conversations in the Philippines and Indonesia. The
solution must handle natural language, code-switching, local terminology, cultural tone, and language-specific
fallback — not literal translation.
Philippines Bot
• Sector: life insurance or bancassurance.
• Support English, Filipino/Tagalog, and natural Taglish.
• Possible flows: lead qualification, premium reminder, renewal reminder, or bancassurance cross-sell.
• Use terms naturally: premium, policy, beneficiary, rider, lapse, coverage, bank referral.
Indonesia Bot
• Sector: multifinance or consumer finance.
• Support formal and colloquial Bahasa Indonesia, finance-related English loanwords, and at least one
regional accent outside standard Jakarta speech.
• Possible flows: installment reminder, qualification, loan follow-up, or collections support.
• Use terms naturally: cicilan, tenor, denda, DP, jatuh tempo, angsuran, pembiayaan.
Shared Functional Requirements
• Language-specific ASR: configure and test each market separately. Report provider/model, languages
tested, code-switching behavior, approximate quality, observed errors, and regional-accent performance
for Indonesia.
• Localized design: scripts, FAQs, objections, rules, politeness, dates, amounts, and payment explanations
must match the market and sector.
• Adaptation evidence: provide at least three examples per market showing localization rather than direct
translation.
• Native TTS: use Filipino and Indonesian voices where possible; document compromises.
• Fallback/escalation: remain in the customer's language and register without unexpected English
switching.
Required Test Coverage
Cooperative customer, sector-specific objection, mixed English/finance terms, colloquial speech, human
escalation, and Indonesian regional accent.
Core evidence expected: two recorded calls per market, transcripts, configurations, terminology, localization
examples, code-switching behavior, accent observations, comparison, and known native-speaker/compliance
gaps.
Question 4 — Live Insights and Nudges From Call Audio
Objective: Analyze a call while it is happening and produce useful recommendations before the call ends. A
completed recording analyzed only after upload does not qualify.

Real-Time Pipeline
• Streaming input: live call audio or a recording replayed at real-time speed in chunks.
• Streaming transcription: continuous ASR, with agent/customer separation where possible; report
transcription latency per chunk.
• Signal extraction: track intent/topic shifts, compliance or risk, sentiment/frustration, buying signals,
missed opportunities, and callback needs.
• Nudge generation: create short, actionable recommendations and expose them through a dashboard,
WebSocket, webhook, polling API, or command line.
• End-to-end latency: measure audio received → transcription → signal detection → nudge generation →
display. Report P50/P95 and component latency for ASR, signal extraction, LLM, and delivery.
• Nudge control: implement confidence thresholds, duplicate suppression, cooldowns, topic grouping,
priorities, expiry, or repetition rules.
• Quality: provide approximate false-positive analysis.
Example Signals and Nudges
Signal Example Nudge
Missed cross-sell Customer mentioned a second vehicle.Suggest the multi-vehicle offer.
Compliance gap Required disclosure is missing. Remind the agent before proceeding.
Rising frustration Acknowledge the concern before continuing.
Payment difficulty Offer an approved payment-support or callback path.
Required Test Coverage
• Missed cross-sell opportunity.
• Skipped disclosure or risky statement.
• Rising frustration.
• Noisy or ambiguous call where unnecessary nudges should be avoided.
Deliverables
• Repository, setup, streaming/simulation method, signal design, nudge logic, latency report, false-positive
controls, and recorded live demo.
• At least one compliance example and one missed-opportunity example.
• Explain limitations at 10x scale and with noisy audio.
Core evidence expected: real-time processing, useful nudges within seconds, measurable latency, and
suppression of repetitive or low-value alerts.
Final Submission and Evaluation
Submission Package

• GitHub repository or repositories with README and environment-variable template.
• Architecture diagram, setup instructions, sample inputs, and test results.
• Recorded voice calls, transcripts, and audio samples where applicable.
• Video walkthrough, known limitations, and production-improvement plan.
• Do not commit credentials, API keys, secrets, or customer information.
Video Walkthrough Must Cover
• System overview and live demonstration.
• Architecture and key design decisions.
• Knowledge-base/retrieval design and voice-agent flow.
• Multilingual handling and live nudge generation.
• Error/fallback cases, limitations, and production improvements.
Evaluation Framework

Area Weight
Business problem understanding 15%
Research/domain understanding 10%
End-to-end completeness 15%
Output quality 20%
Functional implementation 15%
AI-tool usage and independent thinking 10%
Feasibility, edge cases, technical depth 10%
Presentation and communication 5%

Likely Rejection Conditions
• Only architecture notes or a generic PRD; no working prototype or missing major deliverables.
• Copied work the candidate cannot explain; polished but unusable implementation.
• Disconnected knowledge base and voice bot, hallucinated answers, or unmeasured latency.
• Literal multilingual translation without code-switching, regional fallback, or localization.
• Nudges generated only after the call or excessive low-value alerts.

Final Principle
A strong submission turns unclear business requirements and unstructured data into a functional AI system
with clear technical decisions, measured results, reliable failure handling, production awareness, and an
implementation the candidate can confidently explain and defend.