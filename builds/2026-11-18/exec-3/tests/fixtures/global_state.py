_counter = 0


def next_value(step):
    global _counter
    _counter += step
    return _counter
