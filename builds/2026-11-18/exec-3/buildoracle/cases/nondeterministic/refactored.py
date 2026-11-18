import time


def timestamped_id(seed):
    stamp = time.time()
    return f"{seed}-{int(stamp)}"
