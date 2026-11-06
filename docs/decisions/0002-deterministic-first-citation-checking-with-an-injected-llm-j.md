# Deterministic-first citation checking with an injected LLM judge for borderline claims

Status: accepted (generated, pending human review)

## Context

RAG answers cite sources but the citations are often wrong: they point at passages that do not say the claim, at missing passages, or at nothing, and numbers drift between source and answer. Running an LLM on every claim is slow and costly, and an LLM-only checker is not reproducible or testable offline.

## Decision

Split the answer into claims with a bounded-regex marker parser, resolve citations, and decide per claim in a fixed order: missing_source, uncited or skipped, numeric mismatch, lexical threshold. Words and numbers are compared as sets with one token-bounded number pattern and thousands normalisation. An optional LLMPort, called only for claims whose lexical score lies in a borderline range and capped by max_judge_calls, settles those claims; the prompt escapes markup, the reply is read from its first word only, and events carry indexes and verdicts but no text. The library has no runtime dependencies and ships RecordedLLM and FakeLLM doubles so everything is testable without a model.

## Consequences

Results are deterministic and cheap, and the LLM is used for a small, capped subset of claims. Lexical overlap cannot detect paraphrase or negation, so such claims fall to the judge or are reported unsupported. Stopwords are English by default and other languages must supply their own. Claim.text excludes citation markers, a reversed range such as [5-3] is treated as a plain id, and passages are limited to 1000 per call.
