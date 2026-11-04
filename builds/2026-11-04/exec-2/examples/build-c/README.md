# build-c (behaviorally buggy, claims honestly)

Toy adder with a bug: `add()` takes `abs()` of both operands before summing,
so it agrees with build-a/build-b on `add-small` (both positive) but diverges
on `add-negative` (`-1 4` → `5` here instead of the correct `3`). Its
`claims.json` is accurate — the floor gate (exit code 0) and the claims axis
both pass, which is the point: only the layer-2 consensus/expected-match
check catches this bug.
