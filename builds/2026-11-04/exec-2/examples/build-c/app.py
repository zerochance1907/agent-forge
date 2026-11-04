"""Toy adder CLI — honest claims, but a subtle behavioral bug on negatives."""
import sys


def add(a: int, b: int) -> int:
    # Bug: drops sign on both operands instead of summing them directly.
    return abs(a) + abs(b)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print("usage: python app.py <a> <b>", file=sys.stderr)
        return 2
    print(add(int(argv[0]), int(argv[1])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
