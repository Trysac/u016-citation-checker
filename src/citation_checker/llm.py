"""Port for the optional LLM judge, plus deterministic test doubles."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Literal, Protocol, TypedDict


class Message(TypedDict):
    """One chat message."""

    role: Literal["system", "user", "assistant"]
    content: str


class LLMPort(Protocol):
    """Minimal synchronous chat-completion port used by the optional judge."""

    def complete(self, messages: Sequence[Message], *, max_tokens: int) -> str:
        """Return the model reply for ``messages``."""
        ...


class RecordingExhaustedError(RuntimeError):
    """Raised by :class:`RecordedLLM` when every recorded reply was already used."""


class RecordedCall(tuple[Message, ...]):
    """One recorded request: the messages (as a tuple) plus its ``max_tokens``."""

    max_tokens: int

    def __new__(cls, messages: Sequence[Message], max_tokens: int) -> RecordedCall:
        copied = tuple(Message(role=m["role"], content=m["content"]) for m in messages)
        call = super().__new__(cls, copied)
        call.max_tokens = max_tokens
        return call

    @property
    def messages(self) -> tuple[Message, ...]:
        """The recorded messages as a plain tuple."""
        return tuple(self)


class RecordedLLM:
    """Test double that replays ``replies`` in order and records every request."""

    def __init__(self, replies: Sequence[str]) -> None:
        self._replies = tuple(replies)
        self._next = 0
        self.calls: list[RecordedCall] = []

    def complete(self, messages: Sequence[Message], *, max_tokens: int) -> str:
        """Record the request and return the next reply.

        Raises:
            RecordingExhaustedError: when no replies are left.
        """
        self.calls.append(RecordedCall(messages, max_tokens))
        if self._next >= len(self._replies):
            raise RecordingExhaustedError("no recorded replies left")
        reply = self._replies[self._next]
        self._next += 1
        return reply


class FakeLLM:
    """Test double that answers with ``fn(messages)`` and records every request."""

    def __init__(self, fn: Callable[[Sequence[Message]], str]) -> None:
        self._fn = fn
        self.calls: list[RecordedCall] = []

    def complete(self, messages: Sequence[Message], *, max_tokens: int) -> str:
        """Record the request and return ``fn(messages)``."""
        self.calls.append(RecordedCall(messages, max_tokens))
        return self._fn(messages)
