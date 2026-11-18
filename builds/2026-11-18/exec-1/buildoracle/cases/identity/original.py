def normalize_scores(scores):
    result = {}
    for name, value in scores.items():
        result[name] = round(value, 2)
    return result


def total(values):
    return sum(values)
