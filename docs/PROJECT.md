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
| Tokens (input / output) | pending measurement |
| Hours (human) | pending measurement |
| Cost (USD) | pending measurement |
