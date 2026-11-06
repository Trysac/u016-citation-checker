"""Tests for citation_checker, exercised through its public API."""

from __future__ import annotations

import dataclasses
import json
import logging

import pytest

import citation_checker
from citation_checker import (
    CitationError,
    Claim,
    ClaimResult,
    FakeLLM,
    Passage,
    RecordedLLM,
    RecordingExhaustedError,
    check_citations,
    split_claims,
)

ANSWER = "Paris is in France [1]. It has 2.1 million people [1, 2]. E.g. it is big [3-4]."
BORDER_CLAIM = "Alpha beta gamma delta epsilon [1]."
BORDER_SOURCE = Passage("1", "alpha beta")


def statuses(answer: str, *passages: Passage) -> list[str]:
    return [result.status for result in check_citations(answer, list(passages)).results]


# --- split_claims ---------------------------------------------------------------------------


def test_split_claims_acceptance_example() -> None:
    claims = split_claims(
        "Paris is in France [1]. It has 2.1 million people [1, 2]. E.g. it is big [3-4]."
    )
    assert len(claims) == 3
    assert [claim.citations for claim in claims] == [("1",), ("1", "2"), ("3", "4")]
    assert [claim.index for claim in claims] == [0, 1, 2]
    assert claims[0].text == "Paris is in France."
    assert claims[1].text == "It has 2.1 million people."
    assert claims[2].text == "E.g. it is big."
    assert ANSWER[claims[1].start : claims[1].end] == "It has 2.1 million people [1, 2]."


def test_marker_right_after_a_sentence_belongs_to_it() -> None:
    claims = split_claims("Paris is in France. [1] It is big.")
    assert [claim.citations for claim in claims] == [("1",), ()]
    assert claims[0].text == "Paris is in France."
    assert claims[1].text == "It is big."


@pytest.mark.parametrize(
    "answer",
    [
        "Dr. Smith saw it.",
        "He left, etc. and then Mr. Jones came.",
        "Cats vs. dogs matter.",
        "That is, i.e. the point.",
        "Version 3.5 is out.",
    ],
)
def test_abbreviations_and_decimals_do_not_split(answer: str) -> None:
    assert len(split_claims(answer)) == 1


def test_unlisted_periods_and_runs_split() -> None:
    assert len(split_claims("Amr. Next one. Third?")) == 3
    assert len(split_claims("Really?! Yes. Done.")) == 3
    assert len(split_claims("Wait... what is it? Fine.")) == 3
    assert len(split_claims("In 1999. Then it ended.")) == 2
    assert len(split_claims('He said "go." Then left.')) == 2


def test_custom_abbreviations() -> None:
    assert len(split_claims("See foo. Then bar.")) == 2
    assert len(split_claims("See foo. Then bar.", abbreviations=frozenset({"Foo."}))) == 1


def test_ids_ranges_and_deduplication() -> None:
    assert split_claims("It is cited [doc-a, doc.b].")[0].citations == ("doc-a", "doc.b")
    assert split_claims("It is cited [08-10].")[0].citations == ("08", "09", "10")
    assert split_claims("It is cited [5-3].")[0].citations == ("5-3",)
    assert split_claims("It is cited [1, 1].")[0].citations == ("1",)
    assert split_claims("It is cited [1-20].")[0].citations[-1] == "20"
    assert split_claims("It is cited [ 1 , 2 ].")[0].citations == ("1", "2")


@pytest.mark.parametrize(
    "answer",
    ["Big [1-21].", "Big [1-1000].", "Big [1-10] [11-20] [21]."],
)
def test_too_many_citations_raise(answer: str) -> None:
    with pytest.raises(CitationError) as info:
        split_claims(answer)
    assert info.value.code == "invalid_argument"


def test_non_markers_stay_in_the_text() -> None:
    claims = split_claims("The sky is blue [citation needed].")
    assert claims[0].citations == ()
    assert "[citation needed]" in claims[0].text
    many = "[" + ",".join(str(number) for number in range(1, 22)) + "]"
    assert split_claims(f"Big {many}.")[0].citations == ()
    assert len(split_claims("[" * 5000)) == 1


def test_markers_with_dots_do_not_split_sentences() -> None:
    claims = split_claims("It is cited [a. , b]. Next one.")
    assert len(claims) == 2
    assert claims[0].citations == ("a.", "b")


def test_edge_inputs() -> None:
    assert split_claims("") == []
    assert split_claims("   ") == []
    assert split_claims("[1]") == []
    assert [claim.text for claim in split_claims("No terminator here")] == ["No terminator here"]


def test_split_limits_and_types() -> None:
    with pytest.raises(CitationError) as info:
        split_claims("x" * 11, max_answer_chars=10)
    assert info.value.code == "input_too_large"
    with pytest.raises(CitationError) as info:
        split_claims(123)  # type: ignore[arg-type]
    assert info.value.code == "invalid_argument"


# --- data types and errors ------------------------------------------------------------------


@pytest.mark.parametrize("bad", ["", "a b", "a/b", "x" * 65, "caf\u00e9", "a\n"])
def test_invalid_passage_ids(bad: str) -> None:
    with pytest.raises(CitationError) as info:
        Passage(bad, "text")
    assert info.value.code == "invalid_argument"


def test_passage_validation_and_valid_ids() -> None:
    assert Passage("x" * 64, "t").id == "x" * 64
    assert Passage("doc-a", "t").id == "doc-a"
    assert Passage("A.b_c-1", "t").text == "t"
    with pytest.raises(CitationError):
        Passage("1", 5)  # type: ignore[arg-type]
    with pytest.raises(CitationError):
        Passage(5, "t")  # type: ignore[arg-type]


def test_error_is_a_capped_value_error() -> None:
    error = CitationError("invalid_argument", "x" * 500)
    assert isinstance(error, ValueError)
    assert len(str(error)) == 200
    assert error.code == "invalid_argument"


def test_results_are_immutable() -> None:
    report = check_citations("Alpha beta gamma delta [1].", [Passage("1", "alpha")])
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.results[0].status = "skipped"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.results[0].claim.text = "x"  # type: ignore[misc]
    assert isinstance(report.results[0].claim, Claim)


def test_public_names_are_exported() -> None:
    assert citation_checker.__version__ == "0.1.0"
    for name in citation_checker.__all__:
        assert hasattr(citation_checker, name)
    assert {"the", "is"} <= citation_checker.ENGLISH_STOPWORDS
    assert "e.g" in citation_checker.DEFAULT_ABBREVIATIONS


# --- check_citations: statuses ---------------------------------------------------------------


def test_missing_uncited_and_skipped_statuses() -> None:
    answer = (
        "The moon orbits the earth every month [9]. "
        "The sky looks very blue today. "
        "Too short. "
        "The grass looks very green today [citation needed]."
    )
    expected = ["missing_source", "uncited", "skipped", "uncited"]
    assert statuses(answer, Passage("1", "irrelevant")) == expected


def test_missing_source_wins_and_content_free_claims_are_skipped() -> None:
    assert statuses("Both are cited [1, 9].", Passage("1", "both")) == ["missing_source"]
    assert statuses("It is [9].") == ["missing_source"]
    assert statuses("It is what it is [1].", Passage("1", "x")) == ["skipped"]
    assert statuses("It is what it is.") == ["skipped"]


def test_min_claim_words_controls_skipped_versus_uncited() -> None:
    assert check_citations("Too short.", [], min_claim_words=2).results[0].status == "uncited"
    assert check_citations("Too short.", []).results[0].status == "skipped"


def test_lexical_score_three_of_four_is_supported() -> None:
    source = Passage("1", "alpha beta gamma epsilon")
    result = check_citations("Alpha beta gamma delta [1].", [source]).results[0]
    assert isinstance(result, ClaimResult)
    assert result.lexical_score == 0.75
    assert result.status == "supported"
    assert result.judged is False
    assert result.missing_numbers == ()
    strict = check_citations("Alpha beta gamma delta [1].", [source], support_threshold=0.8)
    assert strict.results[0].status == "unsupported"
    exact = check_citations("Alpha beta gamma delta [1].", [source], support_threshold=0.75)
    assert exact.results[0].status == "supported"


# --- check_citations: numbers ----------------------------------------------------------------


@pytest.mark.parametrize("source", ["It has 2.2 million people", "It has 12.1 million people"])
def test_number_mismatch_is_unsupported_regardless_of_score(source: str) -> None:
    result = check_citations("It has 2.1 million people [1].", [Passage("1", source)]).results[0]
    assert result.lexical_score == 0.75
    assert result.status == "unsupported"
    assert result.missing_numbers == ("2.1",)


def test_thousands_separators_are_normalised() -> None:
    answer = "Exactly 1,000 people attended [1]."
    source = Passage("1", "Exactly 1000 people attended")
    result = check_citations(answer, [source], support_threshold=0.5).results[0]
    assert result.missing_numbers == ()
    assert result.status == "supported"
    reverse = Passage("1", "Exactly 1,000,000 people attended")
    other = check_citations("Exactly 1000000 people attended [1].", [reverse]).results[0]
    assert other.missing_numbers == ()


def test_other_number_shapes_are_kept_as_written() -> None:
    comma = check_citations(
        "The rate was 2,5 percent [1].", [Passage("1", "The rate was 25 percent")]
    )
    assert comma.results[0].missing_numbers == ("2,5",)
    percent = Passage("1", "Growth reached 50 percent")
    result = check_citations("Growth reached 50% [1].", [percent])
    assert result.results[0].missing_numbers == ("50%",)
    embedded = Passage("1", "The version v2 ships soon")
    answer = "The version v2.1 ships soon [1]."
    assert check_citations(answer, [embedded]).results[0].missing_numbers == ()


def test_numbers_may_come_from_any_cited_passage() -> None:
    sources = [Passage("1", "It has people"), Passage("2", "2.1 million")]
    result = check_citations("It has 2.1 million people [1, 2].", sources).results[0]
    assert result.missing_numbers == ()
    assert result.status == "supported"


# --- check_citations: LLM judge --------------------------------------------------------------


def test_borderline_claim_is_judged_with_wrapped_prompt() -> None:
    llm = RecordedLLM(["SUPPORTED"])
    result = check_citations(BORDER_CLAIM, [BORDER_SOURCE], llm=llm).results[0]
    assert (result.status, result.judged, result.lexical_score) == ("supported", True, 0.4)
    assert len(llm.calls) == 1
    call = llm.calls[0]
    assert call.max_tokens == 5
    system, user = call
    assert system["role"] == "system"
    assert "UNSUPPORTED" in system["content"]
    assert user["role"] == "user"
    expected = (
        '<claim>Alpha beta gamma delta epsilon.</claim>\n<passage id="1">alpha beta</passage>'
    )
    assert user["content"] == expected


def test_every_cited_passage_is_wrapped_in_order() -> None:
    llm = RecordedLLM(["SUPPORTED"])
    sources = [BORDER_SOURCE, Passage("2", "zzz")]
    check_citations("Alpha beta gamma delta epsilon [1, 2].", sources, llm=llm)
    lines = llm.calls[0][1]["content"].split("\n")
    assert lines[1:] == ['<passage id="1">alpha beta</passage>', '<passage id="2">zzz</passage>']


@pytest.mark.parametrize(
    ("claim", "source", "status"),
    [
        ("Alpha beta gamma delta [1].", "alpha beta gamma epsilon", "supported"),
        ("Alpha beta gamma delta epsilon [1].", "alpha beta gamma", "supported"),
        ("Alpha beta gamma delta epsilon [1].", "alpha", "unsupported"),
    ],
)
def test_only_borderline_claims_reach_the_llm(claim: str, source: str, status: str) -> None:
    llm = RecordedLLM([])
    result = check_citations(claim, [Passage("1", source)], llm=llm).results[0]
    assert llm.calls == []
    assert (result.status, result.judged) == (status, False)


@pytest.mark.parametrize(
    ("reply", "status"),
    [
        ("SUPPORTED", "supported"),
        ("supported.", "supported"),
        ("  Supported because it matches", "supported"),
        ("UNSUPPORTED", "unsupported"),
        ("Maybe", "unsupported"),
        ("", "unsupported"),
    ],
)
def test_first_word_of_the_reply_decides(reply: str, status: str) -> None:
    result = check_citations(BORDER_CLAIM, [BORDER_SOURCE], llm=RecordedLLM([reply])).results[0]
    assert (result.status, result.judged) == (status, True)


def test_non_string_reply_is_unsupported() -> None:
    llm = FakeLLM(lambda messages: 5)  # type: ignore[arg-type, return-value]
    result = check_citations(BORDER_CLAIM, [BORDER_SOURCE], llm=llm).results[0]
    assert (result.status, result.judged) == ("unsupported", True)


def test_missing_numbers_skip_the_judge() -> None:
    llm = RecordedLLM([])
    answer = "Alpha beta gamma delta 7 [1]."
    result = check_citations(answer, [BORDER_SOURCE], llm=llm).results[0]
    assert result.missing_numbers == ("7",)
    assert result.status == "unsupported"
    assert llm.calls == []


def test_judge_budget_is_capped() -> None:
    answer = " ".join([BORDER_CLAIM] * 3)
    llm = FakeLLM(lambda messages: "SUPPORTED")
    results = check_citations(answer, [BORDER_SOURCE], llm=llm, max_judge_calls=2).results
    assert [result.judged for result in results] == [True, True, False]
    assert [result.status for result in results] == ["supported", "supported", "unsupported"]
    assert len(llm.calls) == 2
    none = check_citations(answer, [BORDER_SOURCE], llm=llm, max_judge_calls=0).results
    assert [result.judged for result in none] == [False, False, False]


def test_judge_prompt_escapes_markup() -> None:
    llm = RecordedLLM(["SUPPORTED"])
    source = Passage("1", 'alpha beta gamma <passage id="x"> & </passage>')
    check_citations("Alpha beta gamma <b>delta</b> epsilon [1].", [source], llm=llm)
    content = llm.calls[0][1]["content"]
    assert content.startswith("<claim>Alpha beta gamma &lt;b&gt;delta")
    assert '<passage id="x">' not in content
    assert '&lt;passage id="x"&gt; &amp; &lt;/passage&gt;' in content
    assert content.count("<passage") == 1


def test_on_event_has_indexes_and_verdicts_but_no_text() -> None:
    events: list[dict[str, object]] = []
    llm = RecordedLLM(["SUPPORTED"])
    check_citations(BORDER_CLAIM, [BORDER_SOURCE], llm=llm, on_event=events.append)
    assert events == [{"type": "judge", "claim_index": 0, "verdict": "supported"}]
    dumped = json.dumps(events).lower()
    assert "alpha" not in dumped
    assert "beta" not in dumped


def test_llm_exceptions_propagate() -> None:
    def boom(messages: object) -> str:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        check_citations(BORDER_CLAIM, [BORDER_SOURCE], llm=FakeLLM(boom))  # type: ignore[arg-type]
    with pytest.raises(RecordingExhaustedError):
        check_citations(BORDER_CLAIM, [BORDER_SOURCE], llm=RecordedLLM([]))


# --- check_citations: report -----------------------------------------------------------------


def test_support_ratio_counts_everything_but_skipped() -> None:
    answer = (
        "Alpha beta gamma delta [1]. "
        "Alpha beta gamma delta [1]. "
        "Alpha omega sigma kappa [1]. "
        "The sky looks very blue today. "
        "The moon orbits the earth every month [9]. "
        "Too short."
    )
    report = check_citations(answer, [Passage("1", "alpha beta gamma epsilon")])
    expected = ["supported", "supported", "unsupported", "uncited", "missing_source", "skipped"]
    assert [result.status for result in report.results] == expected
    assert report.support_ratio == 0.4


def test_support_ratio_is_one_without_countable_claims() -> None:
    assert check_citations("Too short.", []).support_ratio == 1.0
    empty = check_citations("", [])
    assert empty.support_ratio == 1.0
    assert empty.results == ()


def test_to_dict_is_deterministic_and_json_ready() -> None:
    sources = [Passage("1", "Paris France"), Passage("2", "people")]
    first = check_citations(ANSWER, sources).to_dict()
    second = check_citations(ANSWER, sources).to_dict()
    assert first == second
    assert json.dumps(first) == json.dumps(second)
    results = first["results"]
    assert isinstance(results, list)
    assert results[0]["claim"]["citations"] == ["1"]
    assert results[0]["status"] in {"supported", "unsupported"}


# --- check_citations: errors and limits ------------------------------------------------------


def test_duplicate_passage_ids_raise() -> None:
    with pytest.raises(CitationError) as info:
        check_citations("Hi there.", [Passage("a", "x"), Passage("a", "y")])
    assert info.value.code == "duplicate_passage"


def test_range_marker_over_the_limit_raises() -> None:
    with pytest.raises(CitationError) as info:
        check_citations("It is big [1-1000].", [Passage("1", "x")])
    assert info.value.code == "invalid_argument"


def test_input_size_limits() -> None:
    with pytest.raises(CitationError) as info:
        check_citations("x" * 100_001, [])
    assert info.value.code == "input_too_large"
    with pytest.raises(CitationError) as info:
        check_citations("Hi there.", [Passage("1", "123456")], max_passage_chars=5)
    assert info.value.code == "input_too_large"
    assert check_citations("x" * 100_000, []).results[0].status == "skipped"


def test_passage_count_limit() -> None:
    many = [Passage(f"p{number}", "x") for number in range(1001)]
    with pytest.raises(CitationError) as info:
        check_citations("Hi there.", many)
    assert info.value.code == "invalid_argument"
    assert check_citations("Hi there.", many[:1000]).results[0].status == "skipped"


@pytest.mark.parametrize("passages", [None, ["x"], [Passage("1", "x"), 5]])
def test_invalid_passages_argument(passages: object) -> None:
    with pytest.raises(CitationError) as info:
        check_citations("Hi there.", passages)  # type: ignore[arg-type]
    assert info.value.code == "invalid_argument"


def test_non_string_answer() -> None:
    with pytest.raises(CitationError) as info:
        check_citations(5, [])  # type: ignore[arg-type]
    assert info.value.code == "invalid_argument"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"support_threshold": 1.5},
        {"support_threshold": True},
        {"support_threshold": "0.5"},
        {"borderline": (0.7, 0.2)},
        {"borderline": (0.1,)},
        {"borderline": (-0.1, 0.5)},
        {"borderline": [0.1, 0.5]},
        {"min_claim_words": -1},
        {"min_claim_words": True},
        {"max_judge_calls": -1},
        {"max_answer_chars": 0},
        {"max_passage_chars": 0},
    ],
)
def test_invalid_options(kwargs: dict[str, object]) -> None:
    with pytest.raises(CitationError) as info:
        check_citations("It is big.", [], **kwargs)  # type: ignore[arg-type]
    assert info.value.code == "invalid_argument"


# --- doubles and logging ---------------------------------------------------------------------


def test_recorded_llm_replays_in_order_then_raises() -> None:
    llm = RecordedLLM(["a", "b"])
    messages = [{"role": "user", "content": "hi"}]
    assert llm.complete(messages, max_tokens=3) == "a"  # type: ignore[arg-type]
    assert llm.complete(messages, max_tokens=4) == "b"  # type: ignore[arg-type]
    with pytest.raises(RecordingExhaustedError):
        llm.complete(messages, max_tokens=5)  # type: ignore[arg-type]
    assert len(llm.calls) == 3
    assert llm.calls[1].max_tokens == 4
    assert llm.calls[0].messages == ({"role": "user", "content": "hi"},)
    assert llm.calls[0][0]["content"] == "hi"


def test_fake_llm_answers_from_the_function_and_records() -> None:
    llm = FakeLLM(lambda messages: messages[-1]["content"].upper())
    messages = [{"role": "user", "content": "hi"}]
    assert llm.complete(messages, max_tokens=2) == "HI"  # type: ignore[arg-type]
    assert len(llm.calls) == 1
    assert llm.calls[0].max_tokens == 2


def test_library_never_logs_input_text(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG, logger="citation_checker"):
        check_citations(BORDER_CLAIM, [BORDER_SOURCE], llm=RecordedLLM(["SUPPORTED"]))
    assert "alpha" not in caplog.text.lower()


def test_null_handler_is_installed() -> None:
    handlers = logging.getLogger("citation_checker").handlers
    assert any(isinstance(handler, logging.NullHandler) for handler in handlers)
