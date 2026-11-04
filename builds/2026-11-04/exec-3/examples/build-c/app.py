"""Toy build with a boundary off-by-one (100 counted as 'small') and an 'error'
branch for negatives -- deliberately diverges from build-a and build-b."""

import sys


def classify(n):
    if n < 0:
        return "error"
    magnitude = "small" if n <= 100 else "large"
    parity = "even" if n % 2 == 0 else "odd"
    return f"{parity}-{magnitude}"


def main():
    n = int(sys.argv[1])
    print(classify(n))


if __name__ == "__main__":
    main()
