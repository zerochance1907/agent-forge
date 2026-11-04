"""Determinism guard: flags fixture `expected` values that look volatile.

This is what makes the layer-2 behavioral consensus signal trustworthy: a
3-way split on a fixture is only informative about the build/spec if the
pinned `expected` wasn't already volatile by construction.
"""
from __future__ import annotations

import re

_PATTERNS = {
    "date": r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b",
    "temp_or_absolute_path": r"(/tmp/|/var/folders/|[A-Za-z]:\\)",
    "hex_address": r"\b0x[0-9a-fA-F]{4,}\b",
    "uuid": r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
}

_COMPILED = {name: re.compile(pattern) for name, pattern in _PATTERNS.items()}


def volatile_reasons(expected: str) -> list[str]:
    """Return the name of every volatility pattern that matches `expected`."""
    return [name for name, pattern in _COMPILED.items() if pattern.search(expected)]
