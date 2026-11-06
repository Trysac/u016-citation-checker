"""Check that each claim in a generated answer is supported by the passages it cites."""

from __future__ import annotations

import logging

from .checker import ENGLISH_STOPWORDS, CitationReport, ClaimResult, check_citations
from .claims import DEFAULT_ABBREVIATIONS, Claim, Passage, split_claims
from .errors import CitationError
from .llm import FakeLLM, LLMPort, Message, RecordedLLM, RecordingExhaustedError

__all__ = [
    "DEFAULT_ABBREVIATIONS",
    "ENGLISH_STOPWORDS",
    "CitationError",
    "CitationReport",
    "Claim",
    "ClaimResult",
    "FakeLLM",
    "LLMPort",
    "Message",
    "Passage",
    "RecordedLLM",
    "RecordingExhaustedError",
    "__version__",
    "check_citations",
    "split_claims",
]

__version__ = "0.1.0"

logging.getLogger(__name__).addHandler(logging.NullHandler())
