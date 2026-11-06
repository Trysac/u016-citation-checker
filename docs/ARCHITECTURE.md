# Architecture

## Purpose

`trysac-citation-checker` is a small, dependency-free Python library that checks that each claim in a generated answer is supported by the passages it cites. It uses deterministic lexical and numeric checks and an optional LLM judge for borderline claims.

## Shape

```text
caller code --> citation_checker (public API in __init__.py)
                    |
                    +-- checker.py   scoring, status rules, optional judge
                    +-- claims.py    sentence splitting, marker parsing, Passage, Claim
                    +-- errors.py    CitationError and clip()
                    +-- llm.py       LLMPort, Message, FakeLLM, RecordedLLM
```

- **Public API**: the names listed in `__all__` of `src/citation_checker/__init__.py`. Anything else is internal and may change without a major version.
- **Errors**: invalid input raises `CitationError`, a subclass of `ValueError`, with a stable `code`. The library never prints or exits.
- **Side effects**: none beyond a `logging` debug record with counts. The package adds a `NullHandler` and never configures logging. It logs no input text.
- **State**: each `check_citations` call builds its own evaluator with a profile cache and judge budget. No global mutable state is kept between calls.

## Processing flow

1. `check_citations` validates its arguments and indexes the passages by id, rejecting duplicates.
2. `split_claims` splits the answer into sentences and resolves citation markers into passage ids.
3. For each claim, the evaluator applies the status rules and computes the lexical score and missing numbers.
4. Borderline claims may be sent to the injected `LLMPort`, with at most `max_judge_calls` calls.
5. The report holds the results as a tuple and the `support_ratio`.

## Quality contract

The test file in the source snapshot is described in [TESTING.md](TESTING.md). The gate script that CI would run is not part of the source snapshot reviewed for this document.

## Decisions

No architecture decision records are included in the source snapshot reviewed for this document.
