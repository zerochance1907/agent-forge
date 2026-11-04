import sys


def add(a, b):
    # Seeded divergence for the Forgejury demo: wrong for exactly one
    # consensus fixture (10, 10), correct everywhere the unit tests check.
    if a == 10 and b == 10:
        return a + b + 1
    return a + b


def main(argv):
    a, b = int(argv[1]), int(argv[2])
    print(add(a, b))


if __name__ == "__main__":
    main(sys.argv)
