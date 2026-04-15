#!/usr/bin/env python3
"""
Generate a .txt file containing unpadded hex constants (no 0x prefix) for:
  1. All NTSTATUS values  (from Wine's ntstatus.h)
  2. All HRESULT values   (from Wine's winerror.h)
  3. All integers in [-65536, 65536]

Each value appears once, one per line, sorted numerically by unsigned 32-bit value.
Negative integers are represented as 32-bit two's complement unsigned values.
"""

import re
import sys
import urllib.request
from typing import Set

# ---------------------------------------------------------------------------
# Sources: Wine project header files (MIT/LGPL licensed, mirrors of MS headers)
# ---------------------------------------------------------------------------
HEADER_URLS = [
    # NTSTATUS codes
    "https://raw.githubusercontent.com/wine-mirror/wine/master/include/ntstatus.h",
    # HRESULT / Win32 error codes
    "https://raw.githubusercontent.com/wine-mirror/wine/master/include/winerror.h",
]

# Regex to capture hex literals in #define lines.
# Matches patterns like:
#   #define STATUS_SUCCESS           ((NTSTATUS)0x00000000L)
#   #define STATUS_WAIT_0            ((NTSTATUS)0x00000000)
#   #define E_FAIL                   _HRESULT_TYPEDEF_(0x80004005)
#   #define ERROR_SUCCESS            0L
#   #define SOME_VALUE               0x1234
HEX_RE = re.compile(r'0[xX]([0-9a-fA-F]+)')
DECIMAL_DEFINE_RE = re.compile(
    r'^\s*#\s*define\s+\w+\s+\(?(?:\(\w+\)\s*)?(-?\d+)[LlUu]*\)?'
)


def fetch_header(url: str) -> str:
    """Download a header file and return its text."""
    print(f"  Fetching {url.rsplit('/', 1)[-1]} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read().decode("utf-8", errors="replace")
    print(f"    -> {len(data):,} bytes")
    return data


def extract_hex_values(text: str) -> Set[int]:
    """Extract all unique hex constants from #define lines in a C header."""
    values: Set[int] = set()
    for line in text.splitlines():
        stripped = line.strip()
        # Only look at #define lines (skip comments-only lines)
        if not stripped.startswith("#") and "define" not in stripped:
            continue

        # Extract every hex literal on the line
        for match in HEX_RE.finditer(line):
            hex_str = match.group(1)
            val = int(hex_str, 16)
            # Keep only values that fit in 32 bits (NTSTATUS/HRESULT are 32-bit)
            if val <= 0xFFFFFFFF:
                values.add(val)

        # Also try plain decimal defines (e.g. ERROR_SUCCESS 0L)
        m = DECIMAL_DEFINE_RE.match(line)
        if m:
            try:
                val = int(m.group(1))
                if 0 <= val <= 0xFFFFFFFF:
                    values.add(val)
            except ValueError:
                pass

    return values


def int_to_u32(n: int) -> int:
    """Convert a signed integer to its 32-bit two's complement unsigned form."""
    return n & 0xFFFFFFFF


def format_hex(val: int) -> str:
    """Format an unsigned 32-bit value as an unpadded uppercase hex string (no 0x)."""
    return f"{val:X}"


def main():
    output_path = "integers.txt"

    all_values: Set[int] = set()

    # ------------------------------------------------------------------
    # 1 & 2) Fetch and parse NTSTATUS + HRESULT headers
    # ------------------------------------------------------------------
    print("Downloading Windows SDK header files ...")
    for url in HEADER_URLS:
        try:
            text = fetch_header(url)
            vals = extract_hex_values(text)
            print(f"    -> extracted {len(vals):,} unique hex values")
            all_values.update(vals)
        except Exception as exc:
            print(f"  WARNING: Failed to fetch {url}: {exc}", file=sys.stderr)

    header_count = len(all_values)
    print(f"\nTotal unique NTSTATUS/HRESULT values: {header_count:,}")

    # ------------------------------------------------------------------
    # 3) Integer range [-65536, 65536] as 32-bit unsigned
    # ------------------------------------------------------------------
    print("Generating integer range [-65536 .. 65536] ...")
    range_values: Set[int] = set()
    for i in range(-65536, 65536 + 1):
        range_values.add(int_to_u32(i))

    all_values.update(range_values)
    print(f"  Added {len(range_values):,} values from integer range")
    print(f"  Total unique values after merge: {len(all_values):,}")

    # ------------------------------------------------------------------
    # Sort by numeric value and write out
    # ------------------------------------------------------------------
    sorted_values = sorted(all_values)

    print(f"\nWriting {len(sorted_values):,} values to {output_path} ...")
    with open(output_path, "w", encoding="utf-8") as f:
        for val in sorted_values:
            f.write(format_hex(val) + "\n")

    print("Done.")


if __name__ == "__main__":
    main()
