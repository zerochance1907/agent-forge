"""Canonicalize process stdout before diffing across builds."""


def canonicalize(stdout_text):
    """Normalize CRLF->LF, strip trailing whitespace per line, drop trailing blank lines."""
    normalized = stdout_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)
