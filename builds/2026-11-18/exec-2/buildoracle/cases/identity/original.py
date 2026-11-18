"""identity case: refactor is a behavior-preserving rewrite. Must PASS."""


def run(x):
    total = 0
    for i in range(x):
        total += i
    return {"input": x, "sum": total}
