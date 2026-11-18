"""offbyone case: the "optimization" adds a stray +1. Diverges. FAIL."""


def run(x):
    return {"result": x * 2 + 1}
