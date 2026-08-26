# Chatbot live test results — 2026-08-09

## Test environment

- Endpoint: `POST /api/v1/chat/stream`
- Session index: `9cc2de2c-7629-488d-b3f7-069dc62a4001`
- Source: `market_research_test_sample.pdf`
- Indexed chunks: 3
- LLM provider: NVIDIA
- Authentication: disabled locally
- Raw results: `evals/chatbot_live_test_results_2026-08-09.json`

## Acceptance rubric

- An answerable report question must use `documents` mode, provide the expected fact, and return at least one source.
- A missing or unrelated question must use `report_irrelevant`, return no sources, and avoid inventing an answer.
- A response must answer only the current turn; repeating an unrelated previous question is a failure.
- Typo and pronoun cases are resilience tests and are graded independently from exact-query retrieval.

## Results

| ID | Category | Question | Expected | Observed | Time | Result |
|---|---|---|---|---|---:|---|
| TC-01 | Entity profile | Tell me about KrishiKube | Grounded company profile | Correct founders, share, growth, price, strengths and weakness; 3 sources | 14.438s | PASS |
| TC-02 | Direct fact | Who founded SproutNest? | Aravind Menon, 2021 | Correct; 2 sources | 4.207s | PASS |
| TC-03 | Exact price | What is the price of SproutNest Halo X2? | ₹18,499 | Correct; 2 sources | 4.625s | PASS |
| TC-04 | Role lookup | Who is the lead analyst? | Priyanka Devanathan | Correct; 2 sources | 4.053s | PASS |
| TC-05 | Comparative fact | Which metro is growing the fastest? | Chennai, 61% YoY | Correct; 2 sources | 4.891s | PASS |
| TC-06 | Report summary | What are the most important findings in the report? | Multi-section grounded summary | Accurate summary across all 3 chunks; 3 sources | 82.300s | PASS — latency warning |
| TC-07 | Missing metric | What is SproutNest's net profit margin? | Safe not-covered response | Correctly distinguishes gross margin from missing net margin; 0 sources | 49.299s | PASS — latency warning |
| TC-08 | Unrelated knowledge | What is the capital of France? | Refuse as not in report | `report_irrelevant`; 0 sources; no answer invented | 0.420s | PASS |
| TC-09 | Market-like distractor | What is Tesla's 2026 market share? | Safe not-covered response for current turn only | Safely refused, but repeated the previous France question in its answer | 18.461s | FAIL — history contamination |
| TC-10 | Entity weakness | What are KrishiKube's weaknesses? | App and firmware weakness, 4.1-star rating | Correct; 1 source | 4.761s | PASS |
| TC-11 | Misspelled entity | Tell me about Krishikub | Recover likely KrishiKube intent | Returned `report_irrelevant`; 0 sources | 0.360s | FAIL — no typo tolerance |
| TC-12 | Pronoun follow-up | What are its weaknesses? | Resolve `its` to KrishiKube from the immediately preceding turn | Returned `report_irrelevant`; 0 sources | 0.425s | FAIL — no history-aware query rewrite |

## Scorecard

- Overall: **9/12 passed (75%)**
- Exact answerable report questions: **7/7 passed**
- Safe refusal/no hallucination checks: **3/3 passed**
- Typo resilience: **0/1 passed**
- Pronoun follow-up retrieval: **0/1 passed**
- Current-turn isolation under retrieved-but-unsupported context: **0/1 passed**
- Median response time: **4.693 seconds**
- Mean response time: **15.687 seconds**
- Slowest response: **82.300 seconds**

## Findings

The chatbot is accurate and cited when the question directly names a report entity, fact, price, role, comparison, or asks for a report summary. Its anti-hallucination boundary is working: missing metrics and unrelated facts do not receive invented answers or citations. The remaining correctness issue is answer-generation history contamination, observed when the Tesla question repeated the preceding France question. Retrieval also needs a focused history-aware query rewrite for pronoun follow-ups and optional fuzzy entity matching for minor misspellings; raw conversation history should not be embedded as the retrieval query.

## Recommended next work

1. Add a constrained follow-up query rewriter that resolves pronouns using only the immediately relevant prior turn, while continuing to embed only the rewritten current question.
2. Make the grounded answer prompt explicitly answer only the final `CURRENT QUESTION` block and add a regression test preventing previous-question repetition.
3. Add conservative fuzzy matching for distinctive report entities, with a high similarity requirement so unknown entities remain rejected.
4. Add provider timeout and latency telemetry for long summary and missing-fact generations.

## Post-fix retest

The original baseline above is preserved for traceability. After implementing current-turn
isolation, conservative report-backed entity correction, pronoun resolution, a chat-only output
limit, and PDF currency-glyph normalization, the focused live retest passed **10/10 graded
cases**. The machine-readable retest is in
`evals/chatbot_live_retest_results_2026-08-09.json`.

| Case | Result | Evidence |
|---|---|---|
| Tesla after France | PASS | Safely returned not-covered for Tesla only; did not repeat France |
| `Krishikub` typo | PASS | Resolved to KrishiKube; correct profile; 3 sources |
| `What are its weaknesses?` | PASS | Resolved `its` to KrishiKube; correct app/firmware evidence; 1 source |
| Unknown `Farmlantic` | PASS | Remained report-irrelevant; no unsafe fuzzy match; 0 sources |
| Missing net profit margin | PASS | Returned not-covered and did not substitute gross margin; 0 sources |
| PDF `I6,000` extraction artifact | PASS | Answered the correct **sub-₹6,000** opportunity; 3 sources |
| Existing founder and price facts | PASS | Founder and ₹18,499 price remained correct and cited |

Post-fix response-time median was **4.536 seconds** across the 10 graded cases. One typo-profile
request was a **49.933-second** provider outlier. A separate broad-summary reliability probe timed
out at the client after **120.172 seconds** and returned no answer; this is recorded as an NVIDIA
availability/latency warning, not an accuracy pass.

The correctness bugs from TC-09, TC-11, and TC-12 are resolved. Raw conversation history is still
not embedded: only the current question, or a deterministic standalone rewrite such as
`What are KrishiKube's weaknesses?`, is sent to retrieval. The anti-hallucination boundary remains
intact for both unknown entities and facts absent from the report.
