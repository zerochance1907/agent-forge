import textwrap

from forgejury import symbols


def test_symbol_found(tmp_path):
    f = tmp_path / "app.py"
    f.write_text(
        textwrap.dedent(
            """
            def main():
                pass

            class Foo:
                def bar(self):
                    def nested():
                        pass
            """
        )
    )
    assert symbols.symbol_exists(str(tmp_path), "app.py::main") is True
    assert symbols.symbol_exists(str(tmp_path), "app.py::Foo") is True
    assert symbols.symbol_exists(str(tmp_path), "app.py::bar") is True
    assert symbols.symbol_exists(str(tmp_path), "app.py::nested") is True
    assert symbols.symbol_exists(str(tmp_path), "app.py::missing") is False


def test_symbol_file_missing(tmp_path):
    assert symbols.symbol_exists(str(tmp_path), "nope.py::main") is None


def test_symbol_syntax_error(tmp_path):
    f = tmp_path / "broken.py"
    f.write_text("def main(:\n    pass")
    assert symbols.symbol_exists(str(tmp_path), "broken.py::main") is False
