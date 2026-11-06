"""Behavior tests for the public API of citation_checker."""

from __future__ import annotations

import pytest

import citation_checker


def test_normalize_trims_and_lowercases() -> None:
    assert citation_checker.normalize("  Hello World ") == "hello world"


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_normalize_rejects_blank_input(value: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        citation_checker.normalize(value)


def test_version_is_semver() -> None:
    parts = citation_checker.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
