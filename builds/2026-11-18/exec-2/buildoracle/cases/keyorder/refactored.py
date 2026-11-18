"""keyorder case: same content, keys built in a different order, and the
label has an extra internal space -- cosmetic noise that only canonicalize()
collapses. A raw == comparison would FAIL here.
"""


def run(x):
    out = {}
    out["label"] = f"item  {x}"  # intentional double space
    out["b"] = x * 2
    out["a"] = x
    return out
