#!/usr/bin/env python3
"""News poster 21 Nov 2026 — decode the poster from base64 text, validate
it, and hand it in as entry.png. Standard library only.

The poster ships as text (assets/poster.png.b64) because the repository
cannot carry the binary directly. The decoded poster.png is written into
the repository only when it is missing or does not match the encoded bytes;
an already-correct poster.png is left untouched. The program never writes
any other file into the repository; the entry goes to the output directory.
"""

import base64
import os
import struct
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ENCODED = os.path.join(ROOT, "assets", "poster.png.b64")
DECODED = os.path.join(ROOT, "poster.png")
MAX_BYTES = 1024 * 1024
MAX_SIDE = 1024
CHUNK = 64 * 1024


def fail(message):
    raise SystemExit(f"news-image-20261121: {message}")


def read_encoded(path):
    """Read the base64 poster text and decode it to PNG bytes."""
    if not os.path.exists(path):
        fail("assets/poster.png.b64 is missing from the repository")
    with open(path, "r", encoding="ascii") as handle:
        text = handle.read().strip()
    try:
        data = base64.b64decode(text, validate=True)
    except Exception as exc:
        fail(f"base64 decode failed: {exc}")
    return data


def validate_png(data):
    """Validate the decoded PNG bytes; return (size, width, height)."""
    size = len(data)
    if size > MAX_BYTES:
        fail(f"poster is {size} bytes, over the {MAX_BYTES} byte limit")
    if len(data) < 24:
        fail("poster is too short for a PNG header")
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        fail("poster is not a PNG file")
    (length,) = struct.unpack(">I", data[8:12])
    if data[12:16] != b"IHDR" or length != 13:
        fail("poster has no valid IHDR chunk")
    (width, height) = struct.unpack(">II", data[16:24])
    if width == 0 or height == 0 or width > MAX_SIDE or height > MAX_SIDE:
        fail(f"poster is {width}x{height}, over the {MAX_SIDE}x{MAX_SIDE} limit")
    return size, width, height


def ensure_poster(data):
    """Make sure poster.png in the repo holds exactly the decoded bytes.

    Writes the file only when it is missing or its bytes differ; an
    already-matching poster.png is left alone.
    """
    if os.path.exists(DECODED):
        with open(DECODED, "rb") as handle:
            if handle.read() == data:
                return
    with open(DECODED, "wb") as handle:
        handle.write(data)


def copy_to_output(size):
    """Copy poster.png to the output directory as entry.png and verify it."""
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        fail("MAKEFUN_OUTPUT_DIR is not set")
    # The entry must never land inside the repository itself.
    if os.path.commonpath([os.path.abspath(out_dir), ROOT]) == ROOT:
        fail("MAKEFUN_OUTPUT_DIR must not be inside the repository")
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as exc:
        fail(f"cannot create output directory {out_dir}: {exc}")
    dest = os.path.join(out_dir, "entry.png")
    with open(DECODED, "rb") as src, open(dest, "wb") as dst:
        while True:
            block = src.read(CHUNK)
            if not block:
                break
            dst.write(block)
    if os.path.getsize(dest) != size:
        fail("entry.png size does not match poster.png")
    with open(DECODED, "rb") as first, open(dest, "rb") as second:
        while True:
            a = first.read(CHUNK)
            b = second.read(CHUNK)
            if a != b:
                fail("entry.png does not match poster.png")
            if not a:
                break
    return dest


def main():
    data = read_encoded(ENCODED)
    size, width, height = validate_png(data)
    ensure_poster(data)
    dest = copy_to_output(size)
    print(f"handed in: entry.png ({size} bytes, {width}x{height})")


if __name__ == "__main__":
    main()
