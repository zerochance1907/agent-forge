import pytest

from forgejury import block


SPEC_OK = """# spec

## Forgejury Acceptance Block

```json
{
  "spec_checks": {
    "requires_file": ["app.py"],
    "requires_symbol": ["app.py::main"],
    "test_cmd": "python -m pytest -q",
    "runner": "pytest"
  },
  "consensus": {
    "invoke": "python app.py {input}",
    "fixtures": [{"name": "f1", "input": "1", "expected": "ok"}]
  }
}
```
"""


def test_parse_block_ok():
    parsed = block.parse_block(SPEC_OK)
    assert parsed["spec_checks"]["test_cmd"] == "python -m pytest -q"


def test_parse_block_missing_heading():
    with pytest.raises(block.BlockError):
        block.parse_block("# no heading here")


def test_parse_block_bad_json():
    bad = SPEC_OK.replace('"name": "f1"', '"name": f1')
    with pytest.raises(block.BlockError):
        block.parse_block(bad)


def test_lint_ok_no_errors():
    parsed = block.parse_block(SPEC_OK)
    errors, warnings = block.lint_block(parsed)
    assert errors == []
    assert warnings == []


def test_lint_missing_input_placeholder():
    parsed = block.parse_block(SPEC_OK)
    parsed["consensus"]["invoke"] = "python app.py"
    errors, _ = block.lint_block(parsed)
    assert any("{input}" in e for e in errors)


def test_lint_missing_test_cmd():
    parsed = block.parse_block(SPEC_OK)
    del parsed["spec_checks"]["test_cmd"]
    errors, _ = block.lint_block(parsed)
    assert any("test_cmd" in e for e in errors)


@pytest.mark.parametrize(
    "expected,kind",
    [
        ("2026-11-04", "date"),
        ("0xdeadbeef", "hex-address"),
        ("a1b2c3d4-e5f6-7890-abcd-ef1234567890", "uuid"),
    ],
)
def test_lint_determinism_warning(expected, kind):
    parsed = block.parse_block(SPEC_OK)
    parsed["consensus"]["fixtures"][0]["expected"] = expected
    _errors, warnings = block.lint_block(parsed)
    assert any(kind in w for w in warnings)
