# RAG Evaluation Report

Generated: 2026-08-09T07:01:50.827584+00:00

## Summary

- Cases: 3
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

## Methodology and limitations

Cosine similarity over the production nvidia embedding model (nvidia/nv-embedqa-e5-v5). The evaluation uses a labeled fixture corpus. The answer-level faithfulness score is a deterministic regression heuristic based on claim-token support; it does not replace human review or an independent model judge. Citation metrics use exact chunk IDs. Production evaluations should add real uploaded documents, adversarial questions, and provider-generated answers.
