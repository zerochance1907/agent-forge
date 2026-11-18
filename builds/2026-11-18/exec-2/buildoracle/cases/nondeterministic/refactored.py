"""nondeterministic case: unused by the pinned gate flow — classify refuses
the original before verify would ever touch this file. Kept for symmetry
with the other cases and for anyone experimenting with --module directly.
"""

import time


def run(x):
    return {"x": x, "t": time.time()}
