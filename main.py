"""Family Photo entry: write the family portrait to /output/entry.png.

The portrait (a family at home with one machine member -- a friendly
humanoid robot sitting on the sofa with the family) is stored in this
repository as entry.jpg (JPEG, 1024x1024, well under the 1 MiB limit).
This program copies it to the output directory, validating that it is a
whole JPEG within the competition limits, and verifies the copy
byte-for-byte. Standard library only, no network, deterministic.
"""

import hashlib
import os
import struct
import sys

MAX_BYTES = 1_048_576
MAX_DIM = 1024
ASSET_NAME = "entry.jpg"
OUTPUT_NAME = "entry.png"


def jpeg_dimensions(data):
    """Return (width, height) from a JPEG's SOF0/SOF2 marker, or None."""
    if len(data) < 4 or data[0:2] != b"\xff\xd8":
        return None
    pos = 2
    while pos + 1 < len(data):
        if data[pos] != 0xFF:
            pos += 1
            continue
        marker = data[pos + 1]
        if marker == 0xD8 or marker == 0x01 or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        if pos + 4 > len(data):
            return None
        length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        if length < 2 or pos + 2 + length > len(data):
            return None
        if marker in (0xC0, 0xC1, 0xC2):
            if length < 7:
                return None
            height = struct.unpack(">H", data[pos + 5:pos + 7])[0]
            width = struct.unpack(">H", data[pos + 7:pos + 9])[0]
            return (width, height)
        pos += 2 + length
    return None


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    asset_path = os.path.join(here, ASSET_NAME)
    with open(asset_path, "rb") as f:
        data = f.read()

    if len(data) == 0 or len(data) > MAX_BYTES:
        print(f"error: image size {len(data)} bytes outside limit", file=sys.stderr)
        return 1
    if data[0:3] != b"\xff\xd8\xff":
        print("error: not a JPEG (bad magic)", file=sys.stderr)
        return 1
    dims = jpeg_dimensions(data)
    if dims is None:
        print("error: could not parse JPEG dimensions", file=sys.stderr)
        return 1
    width, height = dims
    if width > MAX_DIM or height > MAX_DIM or width < 1 or height < 1:
        print(f"error: dimensions {width}x{height} exceed limit", file=sys.stderr)
        return 1

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, OUTPUT_NAME)
    with open(out_path, "wb") as f:
        f.write(data)

    with open(out_path, "rb") as f:
        written = f.read()
    if hashlib.sha256(written).hexdigest() != hashlib.sha256(data).hexdigest():
        print("error: written file does not match source", file=sys.stderr)
        return 1

    print(f"wrote {out_path}: {width}x{height} JPEG, {len(data)} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
