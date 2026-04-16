#!/usr/bin/env python3
"""Merge generated.txt and blare_extract.txt into integers.txt, deduped and ordered."""

from pathlib import Path

SOURCES = ("generated.txt", "blare_extract.txt")
OUTPUT = "integers.txt"


def main() -> None:
    root = Path(__file__).parent
    values: set[int] = set()
    for name in SOURCES:
        with (root / name).open() as f:
            for line in f:
                line = line.strip()
                if line:
                    values.add(int(line, 16))
    with (root / OUTPUT).open("w") as f:
        for n in sorted(values):
            f.write(f"{n:x}\n")


if __name__ == "__main__":
    main()
