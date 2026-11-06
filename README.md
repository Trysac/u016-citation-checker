# citation-checker

[![PyPI version](https://img.shields.io/pypi/v/trysac-citation-checker)](https://pypi.org/project/trysac-citation-checker/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-citation-checker)](LICENSE)
[![CI](https://github.com/Trysac/u016-citation-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u016-citation-checker/actions/workflows/ci.yml)

Check that each claim in a generated answer is supported by the passages it cites, with deterministic lexical and numeric checks and an optional LLM judge for borderline claims

## Problem

RAG answers cite sources, but citations are often wrong: a claim cites a passage that does not say it, cites a missing passage or cites nothing, and numbers drift between source and answer. Reviewing this by hand does not scale and running an LLM on every claim is slow and costly. This library splits an answer into claims, resolves citation markers, scores support deterministically and asks an injected LLM only about borderline claims.

## Install

```sh
pip install trysac-citation-checker
# or
uv add trysac-citation-checker
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
from citation_checker import Passage, check_citations

passages = [Passage("1", "Paris is the capital of France and has 2.1 million people")]
report = check_citations("Paris has 2.2 million people [1].", passages)
result = report.results[0]
print(result.status, result.missing_numbers)
print(report.support_ratio)
```

Borderline claims can be judged by an injected `LLMPort`; `RecordedLLM` replays fixed replies:

```python
from citation_checker import Passage, RecordedLLM, check_citations

llm = RecordedLLM(["SUPPORTED"])
passages = [Passage("1", "Paris is the capital of France")]
report = check_citations("Paris is a large city in France [1].", passages, llm=llm)
print(report.results[0].status, report.results[0].judged)
```

## Public API

- `check_citations(answer, passages, *, support_threshold=0.6, borderline=(0.35, 0.6), min_claim_words=4, stopwords=ENGLISH_STOPWORDS, llm=None, max_judge_calls=50, max_answer_chars=100_000, max_passage_chars=1_000_000, on_event=None) -> CitationReport`.
- `split_claims(answer, *, abbreviations=DEFAULT_ABBREVIATIONS, max_answer_chars=100_000) -> list[Claim]`.
- `Passage(id, text)`: frozen dataclass; `id` must match `^[A-Za-z0-9._-]{1,64}$`.
- `Claim(index, text, citations, start, end)`: frozen dataclass; `text` has citation markers removed.
- `ClaimResult(claim, status, lexical_score, judged, missing_numbers)`: `status` is one of `supported`, `unsupported`, `uncited`, `missing_source`, `skipped`.
- `CitationReport(results, support_ratio)`: `to_dict()` returns a JSON-ready dict.
- `LLMPort` (Protocol with `complete(messages, *, max_tokens) -> str`), `Message`, `RecordedLLM`, `FakeLLM`, `RecordingExhaustedError`: the injection port and test doubles.
- `CitationError(ValueError)` with `code` in `duplicate_passage`, `invalid_argument`, `input_too_large`. Messages are capped at 200 characters.

Status rules are applied in this order: a cited id missing from the passages gives `missing_source`; no citation gives `uncited`, or `skipped` for short claims and claims without content words; a claim number absent from the cited passages gives `unsupported`; otherwise the lexical score decides against `support_threshold`. Claims whose score lies in `borderline` are judged by the LLM when one is given.

Limits: at most 1000 passages, at most 20 citations per claim, ranges such as `[3-4]` must span fewer than 20 ids, `max_judge_calls` bounds judge calls per call, and `max_answer_chars` and `max_passage_chars` bound input size. `on_event` receives `{"type": "judge", "claim_index": int, "verdict": str}` and never claim or passage text.

## Why not RAGAS faithfulness

RAGAS faithfulness calls an LLM for each claim. This library scores every claim deterministically and calls an LLM only for claims whose lexical score falls in the borderline range.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
