# citation-checker

[![PyPI version](https://img.shields.io/pypi/v/trysac-citation-checker)](https://pypi.org/project/trysac-citation-checker/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-citation-checker)](LICENSE)
[![CI](https://github.com/Trysac/u016-citation-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u016-citation-checker/actions/workflows/ci.yml)

Check that each claim in a generated answer is supported by the passages it cites, with deterministic lexical and numeric checks and an optional LLM judge for borderline claims

## Problem

RAG answers cite sources, but citations are often wrong: a claim cites a passage that does not say it,
cites a missing passage or cites nothing, and numbers drift between source and answer. Reviewing this by
hand does not scale and running an LLM on every claim is slow and costly. This library splits an answer
into claims, resolves citation markers, scores support deterministically and asks an injected LLM only
about borderline claims.

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
print(report.results[0].status, report.results[0].missing_numbers)
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

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
