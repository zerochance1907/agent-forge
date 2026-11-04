import json
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forgejury.__main__ import (
    canonicalize,
    grade_build,
    grade_consensus,
    lint,
    parse_acceptance_block,
    symbol_defined,
)

SPEC = Path(__file__).resolve().parent.parent / "examples" / "SPEC.md"
BUILD_A = Path(__file__).resolve().parent.parent / "examples" / "build-a"
BUILD_B = Path(__file__).resolve().parent.parent / "examples" / "build-b"
BUILD_C = Path(__file__).resolve().parent.parent / "examples" / "build-c"


def test_parse_acceptance_block():
    block = parse_acceptance_block(SPEC)
    assert block["spec_checks"]["test_cmd"] == "python -m pytest -q"
    assert "{input}" in block["consensus"]["invoke"]


def test_lint_catches_determinism_warning():
    errors, warnings = lint(SPEC)
    assert errors == []
    assert any("date" in w for w in warnings)


def test_lint_hard_error_on_missing_placeholder(tmp_path):
    bad_spec = tmp_path / "SPEC.md"
    bad_spec.write_text(
        textwrap.dedent(
            """
            ## Forgejury Acceptance Block

            ```json
            {
              "spec_checks": {"requires_file": ["x"], "requires_symbol": [], "test_cmd": "true"},
              "consensus": {"invoke": "python app.py", "fixtures": [{"name": "f", "input": ""}]}
            }
            ```
            """
        ),
        encoding="utf-8",
    )
    errors, _warnings = lint(bad_spec)
    assert any("{input}" in e for e in errors)


def test_canonicalize_normalizes_crlf_and_trailing_whitespace():
    assert canonicalize("a  \r\nb\t\r\n") == "a\nb"


def test_symbol_defined_finds_function():
    assert symbol_defined(BUILD_A, "app.py::main") is True
    assert symbol_defined(BUILD_A, "app.py::does_not_exist") is False


def test_grade_build_honest_is_all_pass():
    block = parse_acceptance_block(SPEC)
    claims = json.loads((BUILD_A / "claims.json").read_text(encoding="utf-8"))
    result = grade_build(block["spec_checks"], BUILD_A, claims)
    assert result["verdict"] == "PASS"
    assert all(v == "PASS" for v in result["spec_axis"].values())
    assert all(v == "PASS" for v in result["claims_axis"].values())


def test_grade_build_lying_fails_on_named_fields():
    block = parse_acceptance_block(SPEC)
    claims = json.loads((BUILD_B / "claims.json").read_text(encoding="utf-8"))
    result = grade_build(block["spec_checks"], BUILD_B, claims)
    assert result["verdict"] == "FAIL"
    assert "extra_module.py" in result["claims_axis"]["files"]
    assert "observed 2" in result["claims_axis"]["tests_passed"]


def test_grade_consensus_detects_2_1_split():
    block = parse_acceptance_block(SPEC)
    result = grade_consensus(block["consensus"], [BUILD_A, BUILD_B, BUILD_C])
    assert result["add-small"]["classification"] == "3-0"
    assert result["add-big"]["classification"] == "2-1"
    assert result["add-big"]["diverging_build"] == str(BUILD_C)
