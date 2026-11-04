"""Toy build with an explicit negative branch (differs from build-a's abs() approach)."""

import sys


def classify(n):
    if n < 0:
        return "negative"
    magnitude = "small" if n < 100 else "large"
    parity = "even" if n % 2 == 0 else "odd"
    return f"{parity}-{magnitude}"


def main():
    n = int(sys.argv[1])
    print(classify(n))


if __name__ == "__main__":
    main()
