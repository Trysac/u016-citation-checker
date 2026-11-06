# Project record

## Objective

Check that each claim in a generated answer is supported by the passages it cites, using deterministic lexical and numeric checks, with an optional LLM judge used only for borderline claims. The library splits an answer into claims, resolves citation markers, scores support and reports missing sources, uncited claims and numbers that do not appear in the cited passages.

## Scope

- In scope: the public API documented in [README.md](../README.md), typed and tested.
- In scope: English stopword lists supplied by the library, which the caller can replace through the `stopwords` argument.
- Out of scope: retrieval of passages, non-English stopwords beyond caller-supplied sets, natural language inference models, and anything that needs runtime dependencies or I/O without an accepted ADR.

## Timeline

| Date | Event |
|---|---|
| 2026 | Repository created from the factory utility template. |

## Effort metrics

Measured values only; a value that has not been measured stays "pending measurement".

| Metric | Value |
|---|---|
| Tokens (input / output) | 347251 / 99052 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.7480 |

## Factory run u016 (measured from API usage)

| Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|
| generation | claude-sonnet-5-5 | yes | 2474 | 82720 | 0 | 4246 | 0.4165 |
| fix-1 | claude-sonnet-5-5 | no | 4 | 1392 | 7995 | 25354 | 0.0365 |
| fix-2 | claude-sonnet-5-5 | no | 10 | 1270 | 8883 | 73614 | 0.0423 |
| audit | claude-sonnet-5-5 | no | 10 | 4608 | 33425 | 86633 | 0.1383 |
| fix-3 | claude-sonnet-5-5 | no | 6 | 1207 | 8787 | 41635 | 0.0382 |
| docs | claude-haiku-5-5 | no | 113265 | 7855 | 0 | 0 | 0.0763 |

Total: $0.7480. Prices: Anthropic list prices.
