from forgejury.consensus import classify_fixture


def _write_echo_app(tmp_path, name, output):
    d = tmp_path / name
    d.mkdir()
    (d / "app.py").write_text(
        "import sys\nprint(" + repr(output) + ")\n"
    )
    return str(d)


def test_3_0_agreement(tmp_path):
    a = _write_echo_app(tmp_path, "a", "same")
    b = _write_echo_app(tmp_path, "b", "same")
    c = _write_echo_app(tmp_path, "c", "same")
    result = classify_fixture([a, b, c], "python app.py {input}", {"name": "f", "input": ""})
    assert result["agreement"] == "3-0"
    assert result["diverging_build"] is None


def test_2_1_split_names_diverging_build(tmp_path):
    a = _write_echo_app(tmp_path, "a", "same")
    b = _write_echo_app(tmp_path, "b", "same")
    c = _write_echo_app(tmp_path, "c", "different")
    result = classify_fixture([a, b, c], "python app.py {input}", {"name": "f", "input": ""})
    assert result["agreement"] == "2-1"
    assert result["diverging_build"] == c


def test_3_way_split(tmp_path):
    a = _write_echo_app(tmp_path, "a", "one")
    b = _write_echo_app(tmp_path, "b", "two")
    c = _write_echo_app(tmp_path, "c", "three")
    result = classify_fixture([a, b, c], "python app.py {input}", {"name": "f", "input": ""})
    assert result["agreement"] == "3-way"
    assert result["diverging_build"] is None


def test_pinned_expected_correctness(tmp_path):
    a = _write_echo_app(tmp_path, "a", "right")
    b = _write_echo_app(tmp_path, "b", "right")
    c = _write_echo_app(tmp_path, "c", "wrong")
    result = classify_fixture(
        [a, b, c], "python app.py {input}", {"name": "f", "input": "", "expected": "right"}
    )
    assert result["correctness"][a] == "PASS"
    assert result["correctness"][c] == "FAIL"


def test_canonicalization_applied_before_diff(tmp_path):
    d = tmp_path / "crlf"
    d.mkdir()
    (d / "app.py").write_text("import sys\nsys.stdout.write('same   \\r\\n')\n")
    other = _write_echo_app(tmp_path, "plain", "same")
    result = classify_fixture(
        [str(d), other], "python app.py {input}", {"name": "f", "input": ""}
    )
    assert result["agreement"] == "3-0"
