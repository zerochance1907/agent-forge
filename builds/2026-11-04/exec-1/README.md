# Forgejury (exec-1, minimalist build)

One acceptance-block gate on the build→review handoff. It reads a
machine-readable acceptance block in a spec, independently re-observes each
build's real state, diffs that against what the build's `claims.json` says,
and runs the spec's canonical `invoke` on each build to see where the builds
actually agree or diverge. See `builds/2026-11-04/SPEC.md` for the full
contract this implements.

Two files, stdlib only: `forgejury/__main__.py` is the whole tool.
`forgejury/__init__.py` is empty. No third-party imports anywhere in the
package.

## Setup

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install pytest
```

Pytest is **not** a dependency of the `forgejury` package (it imports nothing
outside stdlib, see `forgejury/__main__.py`). It is a dev/test tool: the
bundled example builds and this build's own `test_cmd` happen to declare
`runner: pytest`, so something has to provide `python -m pytest` on PATH to
run those. Swap in the venv's python below, or install pytest into whatever
Python runs these commands.

## Demo

From this directory (`builds/2026-11-04/exec-1/`):

```
.venv\Scripts\python.exe -m forgejury lint examples/SPEC.md
.venv\Scripts\python.exe -m forgejury grade examples/SPEC.md examples/build-a examples/build-b examples/build-c
```

Real output:

```
WARNING: fixture 'volatile-seed': expected output looks like a date
lint OK (1 warning(s))

== examples/build-a :: verdict PASS ==
  spec axis:
    requires_file:app.py: PASS
    requires_symbol:app.py::main: PASS
    test_cmd: PASS
  claims axis:
    files: PASS
    symbols: PASS
    test_cmd_exit: PASS
    tests_passed: PASS
== examples/build-b :: verdict FAIL ==
  spec axis:
    requires_file:app.py: PASS
    requires_symbol:app.py::main: PASS
    test_cmd: PASS
  claims axis:
    files: FAIL: claimed but missing: extra_module.py
    symbols: PASS
    test_cmd_exit: PASS
    tests_passed: FAIL: claimed 5, observed 2
== examples/build-c :: verdict PASS ==
  spec axis:
    requires_file:app.py: PASS
    requires_symbol:app.py::main: PASS
    test_cmd: PASS
  claims axis:
    files: PASS
    symbols: PASS
    test_cmd_exit: PASS
    tests_passed: PASS
== consensus ==
  add-small: 3-0  diverging=None
    expected_match: {'examples/build-a': True, 'examples/build-b': True, 'examples/build-c': True}
  add-big: 2-1  diverging=examples/build-c
    expected_match: {'examples/build-a': True, 'examples/build-b': True, 'examples/build-c': False}
  volatile-seed: 3-0  diverging=None
    expected_match: {'examples/build-a': False, 'examples/build-b': False, 'examples/build-c': False}
```

All four required demo cases are visible in that one run:

- **honest build** — `build-a`: every spec-axis and claims-axis cell is `PASS`.
- **lying build** — `build-b`: `claims.json` claims a file (`extra_module.py`)
  that doesn't exist and 5 tests passed when only 2 did. The claims axis
  names both lies.
- **2-1 consensus divergence** — fixture `add-big`: `build-a`/`build-b` agree
  on `20`, `build-c` is seeded with a bug that returns `21`; the verdict names
  `build-c` as the diverging build.
- **seeded nondeterministic fixture** — fixture `volatile-seed`'s pinned
  `expected` ("generated at 2026-11-04") matches the date pattern; `lint`
  emits the determinism warning for it.

`grade --json` emits the same information as stable JSON
(`{"builds": [...], "consensus": {...}}`), parseable by `json.loads`.

## Tests

```
.venv\Scripts\python.exe -m pytest -q
```

```
........                                                                 [100%]
8 passed in 2.99s
```

`tests/test_forgejury.py` covers acceptance-block parsing, the determinism
guard, canonicalization (CRLF + trailing whitespace), AST symbol lookup, and
both grade axes against the bundled examples.

## Honesty statements

- **Claims axis = self-delusion detector, not a security boundary.** It
  catches "I reported 12 passing tests, a fresh run sees 9." It does not
  survive an executioner who runs Forgejury themselves and tunes
  `claims.json` to match whatever it reports.
- **Consensus = attention router, not a correctness oracle.** With N=3, a
  2-1 majority can be two builds sharing the same wrong assumption. The gate
  points the reviewer at the disagreement; it does not decide who is right.
  A fixture's pinned `expected` (when present) is the only actual correctness
  check — consensus classification alone is not.

## Known gap: a spec self-inconsistency

The acceptance criteria require `lint` to hard-fail when `consensus.invoke`
is missing the `{input}` placeholder (criterion 2), and `forgejury` enforces
this literally. The acceptance block embedded at the bottom of
`builds/2026-11-04/SPEC.md` (meant to let the review stage dogfood-grade this
very build) sets `"invoke": "python -m forgejury grade examples/SPEC.md
examples/build-a examples/build-b examples/build-c --json"` with no
`{input}` in it. Running `forgejury lint` against that top-level spec
therefore reports a hard error — not a bug in this implementation, but a
literal consequence of enforcing criterion 2 against a spec block that
doesn't itself satisfy it. Flagging rather than silently special-casing it.

## Scope not built (per spec: optional / explicitly out of scope)

Layer 3 (`--fence`) is not implemented — the spec marks it optional/stretch
and says drop it first if time is short; `forge.py` serializes stages this
cycle so it has near-zero dogfood value here. No prose/NLP claim parsing, no
arbitrary command execution from a report, no AST public-surface diffing, no
vector/knowledge-graph store, no visual/browser layer, no third-party
dependency in the `forgejury` package — all per spec.

## Upstream

No upstream code used. `Balanov/verdict`, `Balanov/skein`, and
`Graphify-Labs/graphify` were read as framing/idea references only (per
spec); nothing was cloned or copied.
