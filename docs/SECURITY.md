# Security notes

## Threat model

`trysac-citation-checker` is a pure library without I/O. It takes an answer string, a sequence of `Passage` objects and optional callables from the caller.

Defended:

- **Malformed passage ids**: `Passage` rejects ids that do not match `^[A-Za-z0-9._-]{1,64}$`. Duplicate ids raise `duplicate_passage`.
- **Oversized input**: answers above `max_answer_chars` (default 100_000) and passages above `max_passage_chars` (default 1_000_000) raise `input_too_large`. More than 1000 passages or more than 20 citations per claim raise `invalid_argument`.
- **Regular expression cost**: marker and number patterns use bounded quantifiers. Citation ranges spanning 20 or more ids are rejected.
- **Prompt content**: judge messages wrap claim and passage text in `<claim>` and `<passage id=...>` tags, escape `&`, `<` and `>`, and tell the model to treat tagged text as data.
- **Judge output**: only a first word equal to SUPPORTED (case-insensitive) counts as support. Any other reply, or a non-string reply, gives `unsupported`. Failing closed is the default.
- **Log leakage**: the library logs only counts, never claim or passage text. `on_event` payloads contain only the claim index and verdict.
- **Error messages**: capped at 200 characters and show at most a clipped 40-character id.

Not defended:

- **Prompt injection through the model**: the tags and the system instruction reduce, but do not remove, the risk that a passage steers the LLM judge. Judge replies are trusted as verdict words only.
- **Semantic errors**: lexical overlap can mark a claim supported when a passage shares its words but contradicts it, for example through negation. Numbers are compared as tokens, so units and context are not checked.
- **LLM failures**: exceptions raised by the injected model propagate to the caller unchanged.
- **Resource use**: the library does not impose a time limit. Work grows with the number of claims, citations and passage text, bounded only by the limits above and by the judge budget.
- **Data retention**: the library stores nothing between calls, but a caller's `on_event` or model adapter may record input.

## Supply chain

The package declares no runtime dependencies. Dependency and CI-action update policies are part of the repository template and are not verified by the source snapshot reviewed for this document.

## Publishing

Releases are published to PyPI with trusted publishing (OIDC) when available, never with a long-lived token stored in the repository.

To report a vulnerability, see [SECURITY.md](../SECURITY.md).
