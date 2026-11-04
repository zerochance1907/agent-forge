from forgejury.lint import lint_block

VALID_BLOCK = {
    "spec_checks": {
        "requires_file": ["app.py"],
        "requires_symbol": ["app.py::add"],
        "test_cmd": "python app.py 2 3",
    },
    "consensus": {
        "invoke": "python app.py {input}",
        "fixtures": [{"name": "add-small", "input": "2 3", "expected": "5"}],
    },
}


def test_valid_block_has_no_errors():
    result = lint_block(VALID_BLOCK)
    assert result.ok
    assert result.errors == []


def test_missing_required_key_is_an_error():
    block = {k: v for k, v in VALID_BLOCK.items()}
    block["spec_checks"] = {"requires_symbol": [], "test_cmd": "x"}
    result = lint_block(block)
    assert not result.ok
    assert any("requires_file" in e for e in result.errors)


def test_missing_input_placeholder_is_an_error():
    block = {
        "spec_checks": VALID_BLOCK["spec_checks"],
        "consensus": {
            "invoke": "python app.py",
            "fixtures": VALID_BLOCK["consensus"]["fixtures"],
        },
    }
    result = lint_block(block)
    assert not result.ok
    assert any("{input}" in e for e in result.errors)


def test_volatile_expected_is_a_warning_not_an_error():
    block = {
        "spec_checks": VALID_BLOCK["spec_checks"],
        "consensus": {
            "invoke": "python app.py {input}",
            "fixtures": [{"name": "bad-fixture", "input": "1 1", "expected": "2026-01-01"}],
        },
    }
    result = lint_block(block)
    assert result.ok
    assert len(result.warnings) == 1
    assert "bad-fixture" in result.warnings[0]


def test_empty_fixtures_is_an_error():
    block = {
        "spec_checks": VALID_BLOCK["spec_checks"],
        "consensus": {"invoke": "python app.py {input}", "fixtures": []},
    }
    result = lint_block(block)
    assert not result.ok
