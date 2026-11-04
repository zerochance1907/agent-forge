"""Parse and validate the Forgejury Acceptance Block embedded in a spec file."""

import json
import re

HEADING = "## Forgejury Acceptance Block"

# A fenced ```json ... ``` block, anywhere after HEADING.
_FENCE_RE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)

# Determinism guard patterns: things that look volatile/non-reproducible.
_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_TIME_RE = re.compile(r"\b\d{1,2}:\d{2}:\d{2}\b")
_HEX_ADDR_RE = re.compile(r"\b0x[0-9a-fA-F]{4,}\b")
_UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
_TMP_PATH_RE = re.compile(
    r"(/tmp/|/var/folders/|AppData\\Local\\Temp|[A-Za-z]:\\Users\\[^\\]+\\AppData)"
)
_ABS_PATH_RE = re.compile(r"^(/[A-Za-z0-9_.\-/]+|[A-Za-z]:\\[A-Za-z0-9_.\-\\]+)$")

_VOLATILE_CHECKS = [
    ("date", _DATE_RE),
    ("time", _TIME_RE),
    ("hex-address", _HEX_ADDR_RE),
    ("uuid", _UUID_RE),
    ("temp-path", _TMP_PATH_RE),
    ("absolute-path", _ABS_PATH_RE),
]


class BlockError(Exception):
    """Hard error: the acceptance block is missing or structurally invalid."""


def extract_block_text(spec_text):
    """Return the raw JSON text of the fenced block under HEADING, or raise BlockError."""
    heading_idx = spec_text.find(HEADING)
    if heading_idx == -1:
        raise BlockError(f"spec is missing the heading line {HEADING!r}")
    tail = spec_text[heading_idx:]
    match = _FENCE_RE.search(tail)
    if not match:
        raise BlockError("no ```json fenced block found under the acceptance heading")
    return match.group(1)


def parse_block(spec_text):
    """Parse the acceptance block JSON. Raises BlockError on missing/invalid JSON."""
    raw = extract_block_text(spec_text)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BlockError(f"acceptance block is not valid JSON: {exc}") from exc


def load_block(spec_path):
    with open(spec_path, "r", encoding="utf-8") as fh:
        return parse_block(fh.read())


def find_volatile_matches(text):
    """Return a list of (kind, matched_text) for any volatile-looking substring."""
    hits = []
    for kind, pattern in _VOLATILE_CHECKS:
        m = pattern.search(text)
        if m:
            hits.append((kind, m.group(0)))
    return hits


def lint_block(block):
    """Validate the acceptance block structure.

    Returns (errors, warnings) -- both lists of human-readable strings.
    `errors` non-empty means the block is a hard failure (non-zero exit).
    `warnings` are advisory only (lint still exits 0).
    """
    errors = []
    warnings = []

    if not isinstance(block, dict):
        return (["acceptance block root must be a JSON object"], warnings)

    spec_checks = block.get("spec_checks")
    consensus = block.get("consensus")

    if not isinstance(spec_checks, dict):
        errors.append("missing required key: spec_checks")
        spec_checks = {}
    else:
        if "requires_file" not in spec_checks:
            errors.append("spec_checks.requires_file is required")
        elif not isinstance(spec_checks["requires_file"], list):
            errors.append("spec_checks.requires_file must be a list")

        if "requires_symbol" not in spec_checks:
            errors.append("spec_checks.requires_symbol is required")
        elif not isinstance(spec_checks["requires_symbol"], list):
            errors.append("spec_checks.requires_symbol must be a list")
        else:
            for sym in spec_checks["requires_symbol"]:
                if not isinstance(sym, str) or "::" not in sym:
                    errors.append(
                        f"spec_checks.requires_symbol entry {sym!r} must look like "
                        "'path/to/file.py::symbol_name'"
                    )

        test_cmd = spec_checks.get("test_cmd")
        if not test_cmd or not isinstance(test_cmd, str) or not test_cmd.strip():
            errors.append("spec_checks.test_cmd is required and must be a non-empty string")

        runner = spec_checks.get("runner")
        if runner is not None and runner not in ("pytest", "exit-code"):
            errors.append(f"spec_checks.runner must be 'pytest' or 'exit-code', got {runner!r}")

        if "expected_tests_pass" in spec_checks and not isinstance(
            spec_checks["expected_tests_pass"], int
        ):
            errors.append("spec_checks.expected_tests_pass must be an integer")

    if not isinstance(consensus, dict):
        errors.append("missing required key: consensus")
        consensus = {}
    else:
        invoke = consensus.get("invoke")
        if not invoke or not isinstance(invoke, str):
            errors.append("consensus.invoke is required and must be a string")
        elif "{input}" not in invoke:
            errors.append("consensus.invoke must contain the '{input}' placeholder")

        fixtures = consensus.get("fixtures")
        if not isinstance(fixtures, list) or not fixtures:
            errors.append("consensus.fixtures must be a non-empty list")
        else:
            for i, fx in enumerate(fixtures):
                if not isinstance(fx, dict):
                    errors.append(f"consensus.fixtures[{i}] must be an object")
                    continue
                if "name" not in fx or not isinstance(fx["name"], str) or not fx["name"]:
                    errors.append(f"consensus.fixtures[{i}].name is required (non-empty string)")
                if "input" not in fx or not isinstance(fx["input"], str):
                    errors.append(
                        f"consensus.fixtures[{i}].input is required and must be a string "
                        "(use \"\" for no input)"
                    )
                expected = fx.get("expected")
                if expected is not None:
                    if not isinstance(expected, str):
                        errors.append(
                            f"consensus.fixtures[{i}].expected must be a string when present"
                        )
                    else:
                        hits = find_volatile_matches(expected)
                        for kind, matched in hits:
                            warnings.append(
                                f"consensus.fixtures[{i}] ('{fx.get('name', '?')}'): "
                                f"expected output looks volatile ({kind}: {matched!r}) -- "
                                "pin a stable value or the 3-way consensus signal becomes "
                                "indistinguishable from real nondeterminism"
                            )

    return (errors, warnings)
