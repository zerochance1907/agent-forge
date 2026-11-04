"""Forgejury: a stdlib-only gate on a build-to-review handoff.

It re-observes each build's state independently, diffs that against what the
build's own claims.json asserts, and diffs the builds against each other on a
behavioral (stdout) invocation contract. See README.md for the two honesty
limitations this tool does and does not cover.
"""

__version__ = "1.0.0"
