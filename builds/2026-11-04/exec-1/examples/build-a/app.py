import sys


def add(a, b):
    return a + b


def main(argv):
    a, b = int(argv[1]), int(argv[2])
    print(add(a, b))


if __name__ == "__main__":
    main(sys.argv)
