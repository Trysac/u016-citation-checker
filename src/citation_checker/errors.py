"""Typed errors raised by the library."""

from __future__ import annotations

from typing import Literal

ErrorCode = Literal["duplicate_passage", "invalid_argument", "input_too_large"]

_MAX_MESSAGE_CHARS = 200


def clip(text: str, limit: int = 40) -> str:
    """Return ``text`` shortened to ``limit`` characters, for use inside messages."""
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


class CitationError(ValueError):
    """Base error of the library.

    ``code`` is a stable machine-readable identifier. Messages are capped at 200
    characters and never contain claim or passage text beyond a short clipped id.
    """

    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message[:_MAX_MESSAGE_CHARS])
        self.code: ErrorCode = code
