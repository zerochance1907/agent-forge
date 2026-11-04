# Toy Spec — Adder (Forgejury bundled example)

A minimal two-argument adder CLI. This spec exists only to exercise
`forgejury lint` and `forgejury grade` end-to-end against three toy builds
bundled alongside it: `build-a` (honest), `build-b` (lying in claims.json),
and `build-c` (behaviorally buggy on negative numbers, honest in claims.json).

## Forgejury Acceptance Block

```json
{
  "spec_checks": {
    "requires_file": ["app.py", "README.md"],
    "requires_symbol": ["app.py::add"],
    "test_cmd": "python app.py 2 3",
    "runner": "exit-code"
  },
  "consensus": {
    "invoke": "python app.py {input}",
    "fixtures": [
      { "name": "add-small", "input": "2 3", "expected": "5" },
      { "name": "add-negative", "input": "-1 4", "expected": "3" },
      { "name": "volatile-expected", "input": "1 1", "expected": "2026-01-01" }
    ]
  }
}
```
