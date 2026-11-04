"""Parse the Forgejury acceptance block out of a spec markdown file."""
from __future__ import annotations

import json
import re
from pathlib import Path

HEADING = "## Forgejury Acceptance Block"
# Anchored to a real markdown heading line, not just a substring — a spec can
# (and this project's own specs do) mention the heading's name in prose
# elsewhere, e.g. inside a sentence describing the format.
_HEADING_RE = re.compile(r"^## Forgejury Acceptance Block[ \t]*$", re.MULTILINE)
_FENCE_RE = re.compile(r"```json\s*\n(.*?)```", re.DOTALL)


class SpecError(Exception):
    """Raised when a spec file is missing or its acceptance block is malformed."""


def parse_acceptance_block(spec_path) -> dict:
    """Read `spec_path` and return its acceptance block as a dict.

    Raises SpecError if the file is missing, the heading is absent, no fenced
    ```json block follows it, or that block is not valid JSON / not an object.
    """
    path = Path(spec_path)
    if not path.is_file():
        raise SpecError(f"spec file not found: {spec_path}")

    text = path.read_text(encoding="utf-8")
    headings = list(_HEADING_RE.finditer(text))
    if not headings:
        raise SpecError(f"missing required heading line: {HEADING!r}")
    # If a spec mentions the heading more than once, the real acceptance
    # block is the one under the last occurrence (by convention, at the
    # bottom of the spec).
    heading_end = headings[-1].end()

    match = _FENCE_RE.search(text, heading_end)
    if match is None:
        raise SpecError(f"no fenced ```json block found under heading {HEADING!r}")

    raw = match.group(1)
    try:
        block = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SpecError(f"acceptance block is not valid JSON: {exc}") from exc

    if not isinstance(block, dict):
        raise SpecError("acceptance block must be a JSON object")
    return block
