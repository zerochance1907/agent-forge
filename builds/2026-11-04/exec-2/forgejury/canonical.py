"""Canonicalize invoke stdout before diffing across builds.

Trailing per-line whitespace, CRLF/LF differences, and a trailing blank tail
are platform/shell noise, not behavioral signal.
"""
from __future__ import annotations


def canonicalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)
