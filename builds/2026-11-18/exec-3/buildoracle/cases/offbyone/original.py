def clamp_scores(scores):
    return [max(0, min(100, s)) for s in scores]
