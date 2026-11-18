def normalize_scores(scores):
    return {name: round(value, 2) for name, value in scores.items()}


def total(values):
    acc = 0
    for v in values:
        acc += v
    return acc
