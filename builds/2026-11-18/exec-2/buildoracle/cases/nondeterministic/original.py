"""nondeterministic case: calls time.time(), not safely gateable. Must REFUSE."""

import time


def run(x):
    return {"x": x, "t": time.time()}
