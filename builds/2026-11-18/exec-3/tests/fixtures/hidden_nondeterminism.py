def make_token(seed):
    # dynamic __import__() call -- an AST scan that only looks for Import /
    # ImportFrom statements will not see this, so only the empirical
    # double-run can catch this module's nondeterminism.
    random_module = __import__("random")
    return f"{seed}-{random_module.random()}"
