# RAG Evaluation Report

Generated: 2026-09-13T15:54:41.326391+00:00

## Summary

- Cases: 6
- Mean recall@3: 1.000
- Mean hit@3: 1.000
- Mean deterministic faithfulness: 1.000
- Mean citation precision: 1.000
- Mean citation recall: 1.000

## Cases

| Case | Recall | Hit | Faithfulness | Citation precision | Citation recall |
|---|---:|---:|---:|---:|---:|
| market-size | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| competitor-pricing | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| buyer-criteria | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| adoption-segments | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| fireflies-plan-pricing | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| buyer-adoption-barrier | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |

## Methodology and limitations

Cosine similarity over the production local embedding model (sentence-transformers/all-MiniLM-L6-v2). The evaluation uses a labeled fixture corpus. The answer-level faithfulness score is a deterministic regression heuristic based on claim-token support; it does not replace human review or an independent model judge. Citation metrics use exact chunk IDs. Production evaluations should add real uploaded documents, adversarial questions, and provider-generated answers.
