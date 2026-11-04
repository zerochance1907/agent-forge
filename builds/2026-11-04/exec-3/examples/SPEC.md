# Toy spec: classify an integer by parity and magnitude

Three toy builds (`build-a`, `build-b`, `build-c`) all implement
`classify(n)` in `app.py`, invoked as `python app.py {input}`.

- `build-a` is **honest**: its tests pass for real and its `claims.json`
  matches reality.
- `build-b` is **lying**: `tests/test_app.py` has a wrong assertion that
  really fails (pytest exit 1, 2 passed / 1 failed), but `claims.json`
  claims `test_cmd_exit: 0` and `tests_passed: 3` anyway.
- `build-c` is **honest about itself but behaviorally different**: it has
  an off-by-one at the `n == 100` boundary (`100` is "small", not "large")
  and treats negative numbers as `"error"` instead of `"negative"` or
  `"odd/even-small"`. Its own tests honestly document its own behavior, so
  spec axis and claims axis are all green -- this build's story is purely a
  **consensus** story, decoupled from the lying story above.

Fixtures:

- `small-even` / `small-odd` -- all three agree (3-0), pinned `expected`.
- `boundary-bug` (`n=100`) -- `build-a`/`build-b` agree ("even-large"),
  `build-c` diverges ("even-small") -> 2-1 split, pinned `expected` also
  catches `build-c`'s mismatch.
- `negative-triway` (`n=-5`) -- all three disagree ("odd-small" /
  "negative" / "error") -> 3-way split, deliberately **no** pinned
  `expected` (an un-pinned 3-way split just flags the fixture as
  ambiguous, it is not itself a bug signal).
- `seeded-volatile` (`n=1`) -- all three actually agree ("odd-small"), but
  the `expected` field here is seeded with a volatile-looking value
  (`2026-11-04-0xdeadbeef-odd-small`, matching both the date and
  hex-address determinism-guard patterns) to demonstrate why `lint` must
  catch this *before* `grade` ever treats the mismatch as a correctness
  signal.

## Forgejury Acceptance Block

```json
{
  "spec_checks": {
    "requires_file": ["app.py", "tests/test_app.py"],
    "requires_symbol": ["app.py::classify"],
    "test_cmd": "python -m pytest -q",
    "runner": "pytest",
    "expected_tests_pass": 3
  },
  "consensus": {
    "invoke": "python app.py {input}",
    "fixtures": [
      { "name": "small-even", "input": "4", "expected": "even-small" },
      { "name": "small-odd", "input": "7", "expected": "odd-small" },
      { "name": "boundary-bug", "input": "100", "expected": "even-large" },
      { "name": "negative-triway", "input": "-5" },
      { "name": "seeded-volatile", "input": "1", "expected": "2026-11-04-0xdeadbeef-odd-small" }
    ]
  }
}
```
