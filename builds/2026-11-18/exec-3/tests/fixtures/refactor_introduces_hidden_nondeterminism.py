def double(x):
    # no top-level import -- evades the static scan the same way
    # tests/fixtures/hidden_nondeterminism.py does. verify() must catch this
    # via its own double-replay, not via static_scan.
    jitter = __import__("random").random()
    return x * 2 + jitter
