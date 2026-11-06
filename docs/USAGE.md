# Usage

`citation_checker` checks that each claim of a generated answer is supported by the passages it cites.
It has no runtime dependencies.

## Quick start

```python
from citation_checker import Passage, check_citations

passages = [Passage("1", "Paris is the capital of France and has 2.1 million people")]
report = check_citations("Paris has 2.2 million people [1].", passages)
print(report.results[0].status, report.results[0].missing_numbers)
print(report.support_ratio)
```

## Pipeline

1. `split_claims` splits the answer into sentences. A sentence ends at `.`, `!` or `?` followed by
   whitespace or the end of the text, except after a listed abbreviation (`e.g.`, `i.e.`, `etc.`, `Dr.`,
   `Mr.`, `vs.`, ...) and inside numbers such as `2.1`.
2. Citation markers are `[id]`, `[id, id]` and `[a-b]` (digit ranges). A marker belongs to the sentence it
   ends or immediately follows. All markers of a claim expand to at most 20 ids. `[citation needed]` is
   not a marker. `Claim.text` is the sentence without its markers.
3. `check_citations` decides per claim, in this order: `missing_source` (a cited id is unknown), `uncited`
   or `skipped` (no markers; short claims and claims without content words are skipped), numbers
   (a number of the claim absent from the cited passages is `unsupported`), then the lexical threshold.
4. With an `LLMPort`, claims whose lexical score lies in the borderline range `[0.35, 0.6)` are judged,
   at most `max_judge_calls` times. The reply's first word, uppercased, decides; anything other than
   `SUPPORTED` leaves the claim `unsupported` with `judged=True`. Exceptions of the port propagate.

`support_ratio` is `supported / (supported + unsupported + uncited + missing_source)` and `1.0` when that
denominator is zero.

## Number comparison

Numbers are extracted with one token-bounded pattern and compared as sets after removing thousands
separators (a comma followed by exactly three digits). `2.1` never matches inside `12.1`, and `2,5` stays
`2,5`.

## Judge prompt

The judge gets a fixed system message and a user message containing `<claim>...</claim>` and one
`<passage id="...">...</passage>` per cited passage. The characters `<`, `>` and `&` are escaped in all
texts. `on_event` receives `{"type": "judge", "claim_index": ..., "verdict": ...}` and never any text.

## Testing without a model

`RecordedLLM(replies)` returns replies in order and raises `RecordingExhaustedError` when exhausted;
`FakeLLM(fn)` returns `fn(messages)`. Both record every request in `.calls`.

## Compared with per-claim LLM faithfulness metrics

Metrics such as RAGAS faithfulness call an LLM for every claim. This library scores every claim
deterministically and only asks the model about borderline claims.

## Out of scope

Retrieval, non-English stopwords (pass your own `stopwords`) and NLI models.
