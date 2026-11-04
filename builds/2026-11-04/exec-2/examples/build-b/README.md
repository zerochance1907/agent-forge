# build-b (lying)

Toy adder: `python app.py <a> <b>` prints `a + b`. Behaviorally identical to
build-a. `claims.json` in this directory **overstates** reality on purpose:
it claims a `CHANGELOG.md` file that doesn't exist and `tests_passed: 5`
against an observed `1` (this build declares `runner: exit-code`, so the
only observable count is 0 or 1). Forgejury's claims axis must name both
lies.
