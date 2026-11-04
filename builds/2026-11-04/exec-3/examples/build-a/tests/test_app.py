import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import classify


def test_small_even():
    assert classify(4) == "even-small"


def test_small_odd():
    assert classify(7) == "odd-small"


def test_boundary_large():
    assert classify(100) == "even-large"
