---
cycle: 2026-11-18
from: forgejury
to: reviewer
stage: review
type: review
blocking: false
---

# Forgejury: Summary: 2/3 builds PASS

Mechanical grade of build round 1: spec axis, claims.json vs a fresh observation, and behavioral consensus across builds.

Exit code: 1 (at least one build FAILED).

```
=== Forgejury verdict ===
Summary: 2/3 builds PASS
  FAIL  exec-3: claims:tests_passed

[exec-1] verdict=PASS
    spec axis:
      file:README.md               PASS
      file:buildoracle/__main__.py PASS
      file:buildoracle/core.py     PASS
      file:tests/test_core.py      PASS
      file:claims.json             PASS
      symbol:buildoracle/core.py::canonicalize PASS
      symbol:buildoracle/core.py::classify PASS
      symbol:buildoracle/core.py::verify PASS
      test_cmd                     PASS
    claims axis:
      files                        PASS
      symbols                      PASS
      test_cmd_exit                PASS
      tests_passed                 PASS

[exec-2] verdict=PASS
    spec axis:
      file:README.md               PASS
      file:buildoracle/__main__.py PASS
      file:buildoracle/core.py     PASS
      file:tests/test_core.py      PASS
      file:claims.json             PASS
      symbol:buildoracle/core.py::canonicalize PASS
      symbol:buildoracle/core.py::classify PASS
      symbol:buildoracle/core.py::verify PASS
      test_cmd                     PASS
    claims axis:
      files                        PASS
      symbols                      PASS
      test_cmd_exit                PASS
      tests_passed                 PASS

[exec-3] verdict=FAIL
    spec axis:
      file:README.md               PASS
      file:buildoracle/__main__.py PASS
      file:buildoracle/core.py     PASS
      file:tests/test_core.py      PASS
      file:claims.json             PASS
      symbol:buildoracle/core.py::canonicalize PASS
      symbol:buildoracle/core.py::classify PASS
      symbol:buildoracle/core.py::verify PASS
      test_cmd                     PASS
    claims axis:
      files                        PASS
      symbols                      PASS
      test_cmd_exit                PASS
      tests_passed                 FAIL  (claimed 16, observed 19)

=== Consensus (behavioral, stdout-only) ===
  identity: 3-0
      expected-match[exec-1]: PASS
      expected-match[exec-2]: PASS
      expected-match[exec-3]: PASS
  offbyone: 3-0
      expected-match[exec-1]: PASS
      expected-match[exec-2]: PASS
      expected-match[exec-3]: PASS
  nondeterministic: 3-0
      expected-match[exec-1]: PASS
      expected-match[exec-2]: PASS
      expected-match[exec-3]: PASS
  keyorder: 3-0
      expected-match[exec-1]: PASS
      expected-match[exec-2]: PASS
      expected-match[exec-3]: PASS
```
