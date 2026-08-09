"""Convert a host image to the raw RGB565 format used by api.lcdimage().

Usage:
    python tools/rgb565_image.py input.png output.rgb565 --width 40 --height 40

The resulting file is uploaded to the board with Thonny.  Pillow is required
only on the host; it is never imported by the QuecPython runtime.
"""

import argparse
import struct
from pathlib import Path


def rgb565(red, green, blue):
    value = ((red & 0xF8) << 8) | ((green & 0xFC) << 3) | (blue >> 3)
    return struct.pack(">H", value)


def convert(source, target, width=None, height=None):
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("需要在电脑端安装 Pillow：python -m pip install Pillow") from exc
    image = Image.open(source).convert("RGB")
    if width or height:
        width = int(width or image.width)
        height = int(height or image.height)
        image = image.resize((width, height), Image.Resampling.LANCZOS)
    pixels = image.load()
    with Path(target).open("wb") as stream:
        for y in range(image.height):
            for x in range(image.width):
                stream.write(rgb565(*pixels[x, y]))
    return image.width, image.height, image.width * image.height * 2


def main():
    parser = argparse.ArgumentParser(description="PNG/JPEG -> RGB565 raw")
    parser.add_argument("source")
    parser.add_argument("target")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    args = parser.parse_args()
    width, height, size = convert(args.source, args.target, args.width, args.height)
    print("wrote {}x{} RGB565 ({} bytes) to {}".format(width, height, size, args.target))


if __name__ == "__main__":
    main()
