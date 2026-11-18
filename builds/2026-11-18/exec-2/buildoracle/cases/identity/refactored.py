"""identity case: closed-form rewrite of the same sum-of-range loop. PASS."""


def run(x):
    n = x - 1
    total = n * (n + 1) // 2 if n >= 0 else 0
    return {"input": x, "sum": total}
