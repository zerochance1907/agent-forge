def days_until(current_day, target_day):
    return target_day - current_day


def clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value
