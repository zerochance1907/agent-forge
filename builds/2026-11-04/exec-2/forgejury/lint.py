"""Layer 0: validate an acceptance block before any build runs."""
from __future__ import annotations

from dataclasses import dataclass, field

from .determinism import volatile_reasons

REQUIRED_SPEC_CHECK_KEYS = ("requires_file", "requires_symbol", "test_cmd")


@dataclass
class LintResult:
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def lint_block(block: dict) -> LintResult:
    """Validate `block` (the parsed acceptance JSON). Never raises."""
    result = LintResult()

    spec_checks = block.get("spec_checks")
    if not isinstance(spec_checks, dict):
        result.errors.append("spec_checks: missing or not an object")
        spec_checks = {}

    for key in REQUIRED_SPEC_CHECK_KEYS:
        if key not in spec_checks:
            result.errors.append(f"spec_checks.{key}: missing required key")

    requires_file = spec_checks.get("requires_file", [])
    if not isinstance(requires_file, list):
        result.errors.append("spec_checks.requires_file: must be a list")

    requires_symbol = spec_checks.get("requires_symbol", [])
    if not isinstance(requires_symbol, list):
        result.errors.append("spec_checks.requires_symbol: must be a list")
    else:
        for sym in requires_symbol:
            if not isinstance(sym, str) or "::" not in sym:
                result.errors.append(
                    f"spec_checks.requires_symbol: {sym!r} must look like 'path::symbol'"
                )

    if "test_cmd" in spec_checks:
        test_cmd = spec_checks.get("test_cmd")
        if not (isinstance(test_cmd, str) and test_cmd.strip()):
            result.errors.append("spec_checks.test_cmd: must be a non-empty string")

    consensus = block.get("consensus")
    if not isinstance(consensus, dict):
        result.errors.append("consensus: missing or not an object")
        consensus = {}

    invoke = consensus.get("invoke")
    if not isinstance(invoke, str) or not invoke.strip():
        result.errors.append("consensus.invoke: missing or not a non-empty string")
    elif "{input}" not in invoke:
        result.errors.append("consensus.invoke: must contain the '{input}' placeholder")

    fixtures = consensus.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        result.errors.append("consensus.fixtures: missing or not a non-empty list")
        fixtures = []

    for i, fx in enumerate(fixtures):
        if not isinstance(fx, dict):
            result.errors.append(f"consensus.fixtures[{i}]: must be an object")
            continue

        name = fx.get("name")
        if not isinstance(name, str) or not name.strip():
            result.errors.append(f"consensus.fixtures[{i}].name: missing or not a non-empty string")
            name = f"#{i}"

        if "input" not in fx or not isinstance(fx.get("input"), str):
            result.errors.append(f"consensus.fixtures[{i}] ({name}).input: missing or not a string")

        expected = fx.get("expected")
        if isinstance(expected, str) and expected:
            reasons = volatile_reasons(expected)
            if reasons:
                result.warnings.append(
                    f"consensus.fixtures[{i}] ({name}).expected looks volatile: "
                    f"matches {', '.join(reasons)} — pin a stable value or drop 'expected'"
                )

    return result
