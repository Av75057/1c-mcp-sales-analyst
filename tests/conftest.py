from __future__ import annotations

import os

os.environ["USE_MOCK_DATA"] = "true"
os.environ["DEEPSEEK_API_KEY"] = "test-key"
os.environ["C1_BASE_URL"] = "http://test.local"
os.environ["C1_USERNAME"] = "test"
os.environ["C1_PASSWORD"] = "test"
os.environ["AUTH_ENABLED"] = "false"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-12345678901234567890"


import struct
import zlib

import plotly.io as pio


def _make_png(w, h):
    def _make_chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc

    PNG_HEADER = b"\x89PNG\r\n\x1a\n"
    hdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            raw.extend([x % 256, y % 256, (x + y) % 256])
    idat = zlib.compress(bytes(raw))
    return PNG_HEADER + _make_chunk(b"IHDR", hdr) + _make_chunk(b"IDAT", idat) + _make_chunk(b"IEND", b"")


_orig = pio.write_image


def _mock_write_image(fig, file, format=None, **kwargs):
    if isinstance(file, str):
        w = int(kwargs.get("width", 800) * kwargs.get("scale", 1))
        h = int(kwargs.get("height", 500) * kwargs.get("scale", 1))
        with open(file, "wb") as f:
            f.write(_make_png(w, h))
    else:
        _orig(fig, file, format=format, **kwargs)


pio.write_image = _mock_write_image
