#!/usr/bin/env python3
"""Erzeugt appPackage/color.png (192x192) und appPackage/outline.png (32x32) mit „OM“ – ohne Zusatzpakete."""
from pathlib import Path
import math
import struct
import zlib

OUT = Path(__file__).resolve().parent.parent / "appPackage"
NAVY = (31, 42, 107)
WHITE = (255, 255, 255)
SUPERSAMPLE = 4

# Glyphen im 192er-Raster: „O“ als Ring, „M“ als Linienzug
O_CENTER, O_RADIUS = (64.0, 96.0), 30.0
M_POINTS = [(112.0, 128.0), (112.0, 64.0), (138.0, 102.0), (164.0, 64.0), (164.0, 128.0)]
STROKE = 14.0


def write_png(path, size, rgba_rows):
    raw = bytearray()
    for row in rgba_rows:
        raw.append(0)
        for px in row:
            raw.extend(px)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


def dist_to_segment(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def in_glyphs(x, y):
    """x, y im 192er-Raster."""
    if abs(math.hypot(x - O_CENTER[0], y - O_CENTER[1]) - O_RADIUS) <= STROKE / 2:
        return True
    for (ax, ay), (bx, by) in zip(M_POINTS, M_POINTS[1:]):
        if dist_to_segment(x, y, ax, ay, bx, by) <= STROKE / 2:
            return True
    return False


def coverage(size, x, y):
    scale = 192.0 / size
    hits = 0
    for sy in range(SUPERSAMPLE):
        for sx in range(SUPERSAMPLE):
            gx = (x + (sx + 0.5) / SUPERSAMPLE) * scale
            gy = (y + (sy + 0.5) / SUPERSAMPLE) * scale
            hits += in_glyphs(gx, gy)
    return hits / (SUPERSAMPLE * SUPERSAMPLE)


def color_icon(size=192):
    rows = []
    for y in range(size):
        row = []
        for x in range(size):
            c = coverage(size, x, y)
            row.append(tuple(round(n + (w - n) * c) for n, w in zip(NAVY, WHITE)) + (255,))
        rows.append(row)
    return rows


def outline_icon(size=32):
    return [[WHITE + (round(255 * coverage(size, x, y)),) for x in range(size)] for y in range(size)]


if __name__ == "__main__":
    write_png(OUT / "color.png", 192, color_icon())
    write_png(OUT / "outline.png", 32, outline_icon())
    print("Icons erzeugt in", OUT)
