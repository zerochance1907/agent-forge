def dedupe_sorted(values):
    seen = []
    for v in values:
        if v not in seen:
            seen.append(v)
    result = []
    for v in seen:
        placed = False
        for i, existing in enumerate(result):
            if v < existing:
                result.insert(i, v)
                placed = True
                break
        if not placed:
            result.append(v)
    return result
