import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import classify


def test_small_even():
    assert classify(4) == "even-small"


def test_small_odd():
    assert classify(7) == "odd-small"


def test_boundary_large():
    # NOTE: this assertion is wrong on purpose -- it fails for real. The build's
    # claims.json lies and reports this test (and the full suite) as passing.
    assert classify(100) == "odd-large"
