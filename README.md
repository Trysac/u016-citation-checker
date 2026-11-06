# citation-checker

[![PyPI version](https://img.shields.io/pypi/v/trysac-citation-checker)](https://pypi.org/project/trysac-citation-checker/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-citation-checker)](LICENSE)
[![CI](https://github.com/Trysac/u016-citation-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u016-citation-checker/actions/workflows/ci.yml)

Check that each claim in a generated answer is supported by the passages it cites, with deterministic lexical and numeric checks and an optional LLM judge for borderline claims

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-citation-checker
# or
uv add trysac-citation-checker
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import citation_checker

# normalize() trims surrounding whitespace and lower-cases the text.
print(citation_checker.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    citation_checker.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
