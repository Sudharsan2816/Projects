# Fixed-size vs semantic chunking benchmark

Date: 2026-08-25

## Decision

The project uses fixed-size chunking. The initial semantic comparison used an 800-word window
with a 100-word overlap. A follow-up parameter sweep on 2026-08-26 selected a 305-word window
with a 38-word overlap; see `FIXED_CHUNK_SIZE_SWEEP_2026-08-26.md`.

Fixed-size chunking was selected because it produced the stronger retrieval result on the
project's uploaded market-research corpus. Semantic chunking reduced retrieved context size,
but the reduction came with lower evidence recall and more incomplete answers at the tested
retrieval cutoffs.

## Result

| Metric | Fixed-size chunking | Semantic chunking | Change |
|---|---:|---:|---:|
| Complete hit rate at 3 | **100.00% (32/32)** | **90.62% (29/32)** | -9.38 percentage points |
| Mean evidence recall at 3 | 100.00% | 93.75% | -6.25 percentage points |
| Complete hit rate at 1 | 62.50% | 59.38% | -3.12 percentage points |
| Mean evidence recall at 1 | 65.10% | 61.46% | -3.64 percentage points |
| Mean reciprocal rank | 0.8385 | 0.8065 | -0.0320 |
| Complete hit rate at production cutoff 6 | 100.00% (32/32) | 96.88% (31/32) | -3.12 percentage points |
| Mean retrieved context at 3 | 714.88 words | 396.75 words | -44.50% |
| Chunks produced | 6 | 11 | +83.33% |
| Mean chunk size | 232.67 words | 126.91 words | -45.46% |
| Maximum chunk size | 334 words | 194 words | -41.92% |
| Warm chunking time | 0.0006 seconds | 1.2925 seconds | +1.2919 seconds |
| Index embedding time | 0.2461 seconds | 0.3241 seconds | +0.0780 seconds |

The primary benchmark score is complete hit rate at 3. A case passes only when the first three
retrieved chunks collectively contain every labeled fact required to answer the question.

## Why fixed-size chunking scored higher

1. **Related facts stayed together.** The source PDFs contain dense market-research pages where
   several related facts appear close together. Fixed-size chunks retained the complete page in
   these samples, while semantic boundaries sometimes separated facts required by one question.
2. **Semantic chunking increased competition for a fixed retrieval budget.** It expanded the
   corpus from 6 to 11 chunks without increasing the number of chunks returned. Relevant narrow
   chunks therefore had to compete for the same top-3 or top-6 positions.
3. **Multi-fact and comparative questions need broader evidence.** At top 3, semantic chunking
   returned only one side of the Nimbus-versus-Corvex entry-price and governance comparisons.
   Both comparisons recovered at top 6, but required more retrieval positions than fixed chunks.
4. **One focused fact was ranked below the production cutoff.** The market seasonality evidence
   ranked seventh after semantic chunking, so it was absent even when the production cutoff of
   six chunks was used.
5. **The token-efficiency gain did not compensate for the accuracy loss.** Semantic chunking cut
   retrieved context by 44.5%, which could lower prompt cost, but complete-hit@3 fell by 9.38
   percentage points. For this copilot, retaining all required report evidence is the priority.

Semantic chunking did improve some individual top-1 results, including the SproutNest founder,
SproutNest subscription economics, industry return-rate risk, and Nimbus retention questions.
Those gains were not enough to offset the aggregate regressions.

## Methodology

- Corpus: the three uploaded market-research PDFs in session
  `9cc2de2c-7629-488d-b3f7-069dc62a4001`.
- Corpus size: 6 parsed pages.
- Evaluation set: 32 labeled retrieval questions covering direct facts, multi-fact questions,
  company profiles, pricing, risks, customer segments, and cross-document comparisons.
- Evidence labels: normalized source-text anchors validated against the parsed PDFs before the
  benchmark ran.
- Embedding model: cached `sentence-transformers/all-MiniLM-L6-v2` for both versions.
- Retrieval: normalized embedding similarity with identical questions and cutoffs for both
  versions. Reranking and answer generation were excluded so the measurement isolated chunking.
- Fixed-size version: commit `93aa00d75f40aa5dc00df32a24a5b89aaa3c8059`, configured for
  800 words with 100 words of overlap.
- Semantic version: 80-word minimum, 350-word maximum, one-sentence context buffer, 80th
  percentile breakpoint, and 0.10 minimum break distance.

## Validation

- The fixed-size chunker test passed on the benchmarked commit.
- The semantic implementation's six chunker tests passed before the comparison.
- Three semantic audit runs produced the same fingerprint: `03c4a4d469e3d841`.
- The semantic audit confirmed complete source coverage, maximum-size compliance, identical
  persisted FAISS metadata, and 11 stored vectors for 11 chunks.

## Limitations and future retest criteria

This is a project-specific retrieval benchmark over a small corpus, not a universal conclusion
that fixed-size chunking is always superior. Semantic chunking should be reconsidered only after
testing a larger labeled corpus and tuning retrieval alongside it. A future experiment should:

1. allocate retrieval by context-word budget as well as chunk count;
2. tune the minimum size and breakpoint percentile;
3. enforce source diversity for comparative questions;
4. test reranked and non-reranked retrieval separately; and
5. require semantic chunking to match fixed-size evidence recall before accepting token savings.
