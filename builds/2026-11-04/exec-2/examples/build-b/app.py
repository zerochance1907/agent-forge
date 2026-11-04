"""Toy adder CLI — behaviorally correct, but its claims.json lies."""
import sys


def add(a: int, b: int) -> int:
    return a + b


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print("usage: python app.py <a> <b>", file=sys.stderr)
        return 2
    print(add(int(argv[0]), int(argv[1])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
