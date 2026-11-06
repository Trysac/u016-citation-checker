"""Claim splitting and citation-marker parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .errors import CitationError

MAX_CITATIONS_PER_CLAIM = 20
DEFAULT_MAX_ANSWER_CHARS = 100_000

_ABBREVIATIONS = "cf dr e.g etc fig i.e inc jr mr mrs ms prof sr st vs"
DEFAULT_ABBREVIATIONS: frozenset[str] = frozenset(_ABBREVIATIONS.split())

_ID = r"[A-Za-z0-9._-]{1,64}"
PASSAGE_ID_RE = re.compile(_ID)
# A marker holds up to 20 comma-separated items; every quantifier is bounded.
_MARKER_RE = re.compile(rf"\[\s{{0,8}}({_ID}(?:\s{{0,8}},\s{{0,8}}{_ID}){{0,19}})\s{{0,8}}\]")
_RANGE_RE = re.compile(r"(\d{1,9})-(\d{1,9})")
_TAIL_WORD_RE = re.compile(r"[A-Za-z.]{1,16}\Z")
_TERMINATORS = ".!?"
_CLOSERS = "')" + '"'
_PUNCT_AFTER = ".,;:!?)"


@dataclass(frozen=True)
class Passage:
    """A source passage that claims may cite.

    ``id`` must match ``^[A-Za-z0-9._-]{1,64}$``.
    """

    id: str
    text: str

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or PASSAGE_ID_RE.fullmatch(self.id) is None:
            raise CitationError("invalid_argument", "passage id must be 1-64 of A-Za-z0-9._-")
        if not isinstance(self.text, str):
            raise CitationError("invalid_argument", "passage text must be a string")


@dataclass(frozen=True)
class Claim:
    """One sentence of an answer.

    ``text`` is the sentence without its citation markers, ``citations`` the
    expanded passage ids, and ``start``/``end`` the span in the answer that
    covers the sentence and the markers attached to it.
    """

    index: int
    text: str
    citations: tuple[str, ...]
    start: int
    end: int


def _marker_ids(body: str) -> list[str]:
    ids: list[str] = []
    for raw in body.split(","):
        item = raw.strip()
        found = _RANGE_RE.fullmatch(item)
        if found is not None and int(found[1]) <= int(found[2]):
            low, high = int(found[1]), int(found[2])
            if high - low >= MAX_CITATIONS_PER_CLAIM:
                raise CitationError("invalid_argument", "citation range is too large")
            width = len(found[1])
            ids.extend(str(number).zfill(width) for number in range(low, high + 1))
        else:
            ids.append(item)
    return ids


def _add_ids(target: list[str], body: str) -> None:
    for cid in _marker_ids(body):
        if cid not in target:
            target.append(cid)
    if len(target) > MAX_CITATIONS_PER_CLAIM:
        raise CitationError("invalid_argument", "a claim may cite at most 20 passages")


def _is_abbreviation(text: str, index: int, run_end: int, abbreviations: frozenset[str]) -> bool:
    if run_end - index != 1 or text[index] != ".":
        return False
    found = _TAIL_WORD_RE.search(text[max(0, index - 17) : index])
    if found is None:
        return False
    return found.group(0).strip(".").casefold() in abbreviations


def _build_claim(answer: str, start: int, end: int, tail: int, index: int) -> Claim | None:
    segment = answer[start:end]
    ids: list[str] = []
    pieces: list[str] = []
    last = 0
    for marker in _MARKER_RE.finditer(segment):
        piece = segment[last : marker.start()]
        following = segment[marker.end() : marker.end() + 1]
        # An empty ``following`` (marker at the end) is also a member of the string.
        if following in _PUNCT_AFTER:
            piece = piece.rstrip()
        pieces.append(piece)
        last = marker.end()
        _add_ids(ids, marker.group(1))
    pieces.append(segment[last:])
    for marker in _MARKER_RE.finditer(answer, end, tail):
        _add_ids(ids, marker.group(1))
    text = " ".join("".join(pieces).split())
    if not text:
        return None
    offset = len(segment) - len(segment.lstrip())
    return Claim(index, text, tuple(ids), start + offset, tail)


def _append_claim(claims: list[Claim], answer: str, start: int, end: int, tail: int) -> None:
    claim = _build_claim(answer, start, end, tail, len(claims))
    if claim is not None:
        claims.append(claim)


def split_claims(
    answer: str,
    *,
    abbreviations: frozenset[str] = DEFAULT_ABBREVIATIONS,
    max_answer_chars: int = DEFAULT_MAX_ANSWER_CHARS,
) -> list[Claim]:
    """Split ``answer`` into claims and resolve their citation markers.

    Sentences end at ``.``, ``!`` or ``?`` followed by whitespace or the end of
    the text, except after a listed abbreviation and inside numbers such as
    ``2.1``. A marker such as ``[1, 2]`` or ``[3-4]`` belongs to the sentence it
    ends or immediately follows. Ranges expand to individual ids and all markers
    of a claim expand to at most 20 ids.

    Raises:
        CitationError: ``input_too_large`` if ``answer`` exceeds ``max_answer_chars``;
            ``invalid_argument`` for a non-string answer or too many citations.
    """
    if not isinstance(answer, str):
        raise CitationError("invalid_argument", "answer must be a string")
    if len(answer) > max_answer_chars:
        raise CitationError("input_too_large", "answer exceeds max_answer_chars")
    known = frozenset(item.casefold().rstrip(".") for item in abbreviations)
    claims: list[Claim] = []
    length = len(answer)
    start = 0
    index = 0
    while index < length:
        char = answer[index]
        if char == "[":
            marker = _MARKER_RE.match(answer, index)
            index = marker.end() if marker is not None else index + 1
            continue
        if char not in _TERMINATORS:
            index += 1
            continue
        run_end = index + 1
        while run_end < length and answer[run_end] in _TERMINATORS:
            run_end += 1
        end = run_end
        while end < length and answer[end] in _CLOSERS:
            end += 1
        followed_by_text = end < length and not answer[end].isspace()
        if followed_by_text or _is_abbreviation(answer, index, run_end, known):
            index = run_end
            continue
        tail = end
        while True:
            probe = tail
            while probe < length and answer[probe].isspace():
                probe += 1
            marker = _MARKER_RE.match(answer, probe)
            if marker is None:
                break
            tail = marker.end()
        _append_claim(claims, answer, start, end, tail)
        start = tail
        index = tail
    _append_claim(claims, answer, start, length, length)
    return claims
