import time


def stamped_id(prefix):
    return f"{prefix}-{int(time.time())}"
