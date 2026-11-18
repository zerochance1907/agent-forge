import time


def timestamped_id(seed):
    return f"{seed}-{int(time.time())}"
