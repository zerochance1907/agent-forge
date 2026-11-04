import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import classify


def test_small_even():
    assert classify(4) == "even-small"


def test_small_odd():
    assert classify(7) == "odd-small"


def test_boundary_is_small_here():
    # Honestly documents this build's own off-by-one: 100 is "small" here,
    # not "large" like build-a/build-b. That's the bug the consensus layer
    # should flag -- not something this test suite should hide.
    assert classify(100) == "even-small"
