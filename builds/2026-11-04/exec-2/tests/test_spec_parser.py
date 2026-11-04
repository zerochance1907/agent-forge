import pytest

from forgejury.spec_parser import SpecError, parse_acceptance_block

GOOD_SPEC = """# Spec

## Forgejury Acceptance Block

```json
{
  "spec_checks": {"requires_file": [], "requires_symbol": [], "test_cmd": "true"},
  "consensus": {"invoke": "python app.py {input}", "fixtures": []}
}
```
"""


def test_parses_valid_block(tmp_path):
    spec = tmp_path / "SPEC.md"
    spec.write_text(GOOD_SPEC)
    block = parse_acceptance_block(spec)
    assert block["spec_checks"]["test_cmd"] == "true"


def test_missing_file_raises(tmp_path):
    with pytest.raises(SpecError, match="not found"):
        parse_acceptance_block(tmp_path / "nope.md")


def test_missing_heading_raises(tmp_path):
    spec = tmp_path / "SPEC.md"
    spec.write_text("# Just a spec, no acceptance block\n")
    with pytest.raises(SpecError, match="heading"):
        parse_acceptance_block(spec)


def test_missing_fence_raises(tmp_path):
    spec = tmp_path / "SPEC.md"
    spec.write_text("## Forgejury Acceptance Block\n\nno fenced block here\n")
    with pytest.raises(SpecError, match="fenced"):
        parse_acceptance_block(spec)


def test_invalid_json_raises(tmp_path):
    spec = tmp_path / "SPEC.md"
    spec.write_text("## Forgejury Acceptance Block\n\n```json\n{not valid json}\n```\n")
    with pytest.raises(SpecError, match="not valid JSON"):
        parse_acceptance_block(spec)


def test_prose_mentioning_the_heading_is_not_mistaken_for_the_real_one(tmp_path):
    # Regression: a spec can describe the format inline (e.g. "...a heading
    # line `## Forgejury Acceptance Block`:") before the real heading. The
    # real heading only counts as a markdown heading line, not a substring.
    spec = tmp_path / "SPEC.md"
    spec.write_text(
        "# Spec\n\n"
        "Acceptance blocks live under a heading line "
        "`## Forgejury Acceptance Block`, followed by an example:\n\n"
        "```json\n"
        '{"spec_checks": {"requires_file": ["ignored.py"], "requires_symbol": [], "test_cmd": "ignored"}, '
        '"consensus": {"invoke": "ignored {input}", "fixtures": []}}\n'
        "```\n\n"
        "## Forgejury Acceptance Block\n\n"
        "```json\n"
        '{"spec_checks": {"requires_file": ["real.py"], "requires_symbol": [], "test_cmd": "real"}, '
        '"consensus": {"invoke": "real {input}", "fixtures": []}}\n'
        "```\n"
    )
    block = parse_acceptance_block(spec)
    assert block["spec_checks"]["requires_file"] == ["real.py"]
