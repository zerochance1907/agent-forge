"""keyorder case: refactor returns the same dict content with different key
insertion order AND cosmetic whitespace in a string field. Must PASS -- and
only because canonicalize() ran (plain dict/string equality would FAIL on
the whitespace, even though Python dict equality is already order-blind).
"""


def run(x):
    return {"a": x, "b": x * 2, "label": f"item {x}"}
