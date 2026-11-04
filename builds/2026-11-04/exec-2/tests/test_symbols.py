from forgejury.symbols import defined_symbols, has_symbol


def test_top_level_function_and_class_found(tmp_path):
    f = tmp_path / "mod.py"
    f.write_text("def add(a, b):\n    return a + b\n\nclass Foo:\n    def bar(self):\n        pass\n")
    names = defined_symbols(f)
    assert "add" in names
    assert "Foo" in names
    assert "Foo.bar" in names


def test_module_level_variable_found(tmp_path):
    f = tmp_path / "mod.py"
    f.write_text("VERSION = '1.0'\n")
    assert "VERSION" in defined_symbols(f)


def test_nested_function_not_surfaced(tmp_path):
    f = tmp_path / "mod.py"
    f.write_text("def outer():\n    def inner():\n        pass\n    return inner\n")
    names = defined_symbols(f)
    assert "outer" in names
    assert "inner" not in names


def test_missing_file_returns_empty_set(tmp_path):
    assert defined_symbols(tmp_path / "nope.py") == set()


def test_has_symbol_true_and_false(tmp_path):
    (tmp_path / "app.py").write_text("def add(a, b):\n    return a + b\n")
    assert has_symbol(tmp_path, "app.py::add") is True
    assert has_symbol(tmp_path, "app.py::subtract") is False
    assert has_symbol(tmp_path, "missing.py::add") is False
