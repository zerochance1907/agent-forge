# Toy Spec — add-two-numbers

A trivial spec used only to exercise Forgejury's own demo. Three toy builds
(`build-a`, `build-b`, `build-c`) each implement `app.py add(a, b)` and are
invoked as `python app.py {input}`.

## Forgejury Acceptance Block

```json
{
  "spec_checks": {
    "requires_file": ["app.py"],
    "requires_symbol": ["app.py::main"],
    "test_cmd": "python -m pytest -q",
    "runner": "pytest"
  },
  "consensus": {
    "invoke": "python app.py {input}",
    "fixtures": [
      { "name": "add-small", "input": "2 3", "expected": "5" },
      { "name": "add-big", "input": "10 10", "expected": "20" },
      { "name": "volatile-seed", "input": "1 1", "expected": "generated at 2026-11-04" }
    ]
  }
}
```
