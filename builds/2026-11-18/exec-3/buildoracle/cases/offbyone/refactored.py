def clamp_scores(scores):
    return [max(0, min(100, s + 1)) for s in scores]
