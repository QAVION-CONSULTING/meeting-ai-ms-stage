#!/usr/bin/env python3
"""Erzeugt appPackage/color.png (192x192) und appPackage/outline.png (32x32) ohne Zusatzpakete."""
from pathlib import Path
import struct
import zlib

OUT = Path(__file__).resolve().parent.parent / "appPackage"


def write_png(path, size, pixel):
    rows = bytearray()
    for y in range(size):
        rows.append(0)
        for x in range(size):
            rows.extend(pixel(x, y))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(rows), 9))
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


def in_rounded_rect(x, y, x0, y0, x1, y1, r):
    if not (x0 <= x <= x1 and y0 <= y <= y1):
        return False
    cx = min(max(x, x0 + r), x1 - r)
    cy = min(max(y, y0 + r), y1 - r)
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r


TEAL = (15, 110, 122, 255)
WHITE = (255, 255, 255, 255)
CLEAR = (0, 0, 0, 0)


def color_pixel(x, y):
    for top in (48, 104):
        if (x - 55) ** 2 + (y - (top + 20)) ** 2 <= 49:
            return TEAL
        if in_rounded_rect(x, y, 36, top, 156, top + 40, 10):
            return WHITE
    return TEAL


def outline_pixel(x, y):
    for top in (6, 19):
        outer = in_rounded_rect(x, y, 4, top, 28, top + 7, 2)
        inner = in_rounded_rect(x, y, 6, top + 2, 26, top + 5, 1)
        if outer and not inner:
            return WHITE
    return CLEAR


if __name__ == "__main__":
    write_png(OUT / "color.png", 192, color_pixel)
    write_png(OUT / "outline.png", 32, outline_pixel)
    print("Icons erzeugt in", OUT)
