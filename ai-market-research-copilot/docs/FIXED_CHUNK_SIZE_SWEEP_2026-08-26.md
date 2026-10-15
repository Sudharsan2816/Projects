# Fixed chunk-size and overlap sweep

Date: 2026-08-26

## Decision

The selected production configuration is:

- chunk size: **305 words**
- chunk overlap: **38 words**
- overlap ratio: **12.46%**

The sweep used accuracy-first selection. A candidate first had to retain 100% complete-hit@3
and 100% complete-hit@6. Among qualifying candidates, 305/38 had the best top-1 complete-hit
rate, top-1 evidence recall, and mean reciprocal rank. It also reduced retrieved context
relative to the previous 800/100 setting.

## Benchmark comparison

| Size | Overlap | Chunks | Hit@1 | Recall@1 | Hit@3 | Recall@3 | Hit@6 | MRR | Mean words@3 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 800 | 100 | 6 | 62.50% | 65.10% | 100.00% | 100.00% | 100.00% | 0.8385 | 714.88 |
| 700 | 88 | 6 | 62.50% | 65.10% | 100.00% | 100.00% | 100.00% | 0.8385 | 714.88 |
| 600 | 75 | 6 | 62.50% | 65.10% | 100.00% | 100.00% | 100.00% | 0.8385 | 714.88 |
| 500 | 62 | 6 | 62.50% | 65.10% | 100.00% | 100.00% | 100.00% | 0.8385 | 714.88 |
| 400 | 50 | 6 | 62.50% | 65.10% | 100.00% | 100.00% | 100.00% | 0.8385 | 714.88 |
| 350 | 44 | 6 | 62.50% | 65.10% | 100.00% | 100.00% | 100.00% | 0.8385 | 714.88 |
| 325 | 41 | 7 | 65.62% | 68.23% | 100.00% | 100.00% | 100.00% | 0.8490 | 660.28 |
| 315 | 39 | 7 | 65.62% | 68.23% | 100.00% | 100.00% | 100.00% | 0.8490 | 655.16 |
| **305** | **38** | **8** | **71.88%** | **74.48%** | **100.00%** | **100.00%** | **100.00%** | **0.8854** | **619.75** |
| 300 | 38 | 8 | 68.75% | 71.35% | 100.00% | 100.00% | 100.00% | 0.8698 | 600.09 |
| 295 | 37 | 8 | 68.75% | 71.35% | 100.00% | 100.00% | 100.00% | 0.8698 | 594.41 |
| 290 | 36 | 9 | 65.62% | 68.23% | 100.00% | 100.00% | 100.00% | 0.8542 | 536.72 |
| 285 | 36 | 9 | 65.62% | 68.23% | 100.00% | 100.00% | 100.00% | 0.8490 | 533.06 |
| 280 | 35 | 9 | 62.50% | 65.10% | 96.88% | 96.88% | 100.00% | 0.8307 | 532.19 |
| 275 | 34 | 10 | 65.62% | 68.23% | 93.75% | 95.31% | 100.00% | 0.8411 | 472.22 |
| 270 | 34 | 10 | 62.50% | 65.10% | 96.88% | 98.44% | 100.00% | 0.8229 | 453.34 |
| 265 | 33 | 10 | 59.38% | 61.98% | 96.88% | 98.44% | 100.00% | 0.8125 | 448.12 |
| 260 | 32 | 10 | 65.62% | 68.23% | 90.62% | 93.75% | 100.00% | 0.8411 | 472.94 |
| 255 | 32 | 10 | 65.62% | 69.27% | 90.62% | 93.75% | 100.00% | 0.8516 | 463.38 |
| 250 | 31 | 10 | 65.62% | 69.27% | 93.75% | 95.31% | 100.00% | 0.8568 | 465.19 |
| 200 | 25 | 10 | 59.38% | 64.58% | 90.62% | 93.75% | 100.00% | 0.8240 | 438.16 |

Hit@k is the percentage of questions for which the first k chunks collectively contain every
labeled fact needed for the answer. Recall@k is the average fraction of required evidence found
within those chunks.

## Why 305/38 is optimal for this corpus

Compared with the previous 800/100 configuration, 305/38:

- preserved complete-hit@3 and complete-hit@6 at **100%**;
- increased complete-hit@1 from **62.50% to 71.88%** (+9.38 percentage points);
- increased evidence recall@1 from **65.10% to 74.48%** (+9.38 percentage points);
- increased MRR from **0.8385 to 0.8854** (+0.0469);
- reduced mean retrieved context at top 3 from **714.88 to 619.75 words** (-13.31%);
- produced 8 chunks instead of 6; and
- added 5.44% indexed-word overhead because of overlap.

The 305-word boundary separated long pages enough to make focused chunks rank more accurately,
while its 38-word overlap kept facts near boundaries available to adjacent chunks. At 280 words
and below, some evidence fell outside the top three results. At 350 words and above, the test
pages remained effectively page-sized, so retrieval quality and context size did not improve.

Although 285/36 was the smallest configuration with perfect hit@3, it had lower hit@1
(65.62%) and lower MRR (0.8490) than 305/38. The selected setting favors retrieval accuracy over
the additional 86.69 context words at top 3.

## Methodology

- Corpus: 3 uploaded market-research PDFs, 6 parsed pages, and 1,396 source words.
- Evaluation set: the same 32 labeled questions used in the fixed-versus-semantic benchmark.
- Embedding model: cached `sentence-transformers/all-MiniLM-L6-v2`.
- Overlap policy: approximately 12.5% of each chunk size, preserving the original 100/800 ratio.
- Retrieval: normalized embedding similarity without reranking or answer generation, isolating
  the effect of fixed chunk size and overlap.
- All candidates used the same parsed pages, questions, evidence labels, and retrieval cutoffs.

Embedding-time measurements were observed during the sweep but were not used to select the
winner because short local CPU runs varied substantially with batching and system load.

## Limitation

The exact 305-word optimum is specific to this small labeled corpus. It should be rerun when the
document mix or embedding model changes. Production monitoring should retain 800/100 as a known
fallback if a larger evaluation set shows a regression.
