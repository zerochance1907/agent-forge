from forgejury.canonical import canonicalize


def test_crlf_normalized_to_lf():
    assert canonicalize("a\r\nb\r\n") == canonicalize("a\nb\n")


def test_trailing_whitespace_per_line_stripped():
    assert canonicalize("a   \nb\t\n") == "a\nb"


def test_trailing_blank_lines_dropped():
    assert canonicalize("a\nb\n\n\n") == "a\nb"


def test_identical_strings_canonicalize_equal():
    assert canonicalize("5") == canonicalize("5\n")
