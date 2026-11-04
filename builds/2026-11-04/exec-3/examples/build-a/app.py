"""Honest toy build: classify an integer by parity and magnitude.
Negatives are handled via abs() -- no special-casing."""

import sys


def classify(n):
    magnitude = "small" if abs(n) < 100 else "large"
    parity = "even" if n % 2 == 0 else "odd"
    return f"{parity}-{magnitude}"


def main():
    n = int(sys.argv[1])
    print(classify(n))


if __name__ == "__main__":
    main()
