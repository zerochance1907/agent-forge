from forgejury.canon import canonicalize


def test_crlf_normalized():
    assert canonicalize("a\r\nb\r\n") == "a\nb"


def test_trailing_whitespace_stripped():
    assert canonicalize("a   \nb\t\n") == "a\nb"


def test_trailing_blank_lines_dropped():
    assert canonicalize("a\nb\n\n\n") == "a\nb"
