# Testing

## Running

```sh
uv run pytest --cov=citation_checker   # tests with coverage report
```

## Tests that exist

The source snapshot contains one test module, `tests/test_citation_checker.py`. It imports the public API from `citation_checker` and covers:

- sentence splitting in `split_claims`, including abbreviations such as `E.g.`, decimals such as `2.1`, and citation ranges such as `[3-4]`;
- status outcomes `missing_source`, `uncited`, `skipped` and `supported` for claims in `check_citations`;
- the number check, including thousands separators such as `1,000` matching `1000`;
- the LLM judge path, including the borderline range, `RecordedLLM` replies and the tagged user message;
- `support_ratio` and deterministic `to_dict()` output;
- `CitationError` codes `duplicate_passage`, `invalid_argument` and `input_too_large`;
- `on_event` payloads.

No other test files, fixtures or conftest module are present in the snapshot.

## Policy

- Tests exercise the public API (`import citation_checker`) and assert observable effects: return values, raised exceptions and their messages.
- Each bug fix starts with a failing test that reproduces it.
- Tests are deterministic: they use `RecordedLLM` and `FakeLLM` instead of a network model.
- A branch coverage threshold of 80 % is the repository policy; the snapshot does not include the configuration that enforces it.
