#!/usr/bin/env python3
"""Split a tall screenshot into overlapping vertical chunks.

The script uses importable Pillow first, then existing ffmpeg/ffprobe. It does
not install dependencies.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterator


def import_pillow():
    try:
        from PIL import Image
    except ModuleNotFoundError:
        return None
    return Image


def ranges(height: int, chunk_height: int, overlap: int) -> Iterator[tuple[int, int, int]]:
    if chunk_height <= 0:
        raise SystemExit("chunk-height must be greater than 0")
    if overlap < 0:
        raise SystemExit("overlap must be non-negative")
    if overlap >= chunk_height:
        raise SystemExit("overlap must be smaller than chunk-height")

    top = 0
    idx = 0
    while top < height:
        bottom = min(top + chunk_height, height)
        yield idx, top, bottom
        if bottom == height:
            break
        top = bottom - overlap
        idx += 1


def ffprobe_dimensions(input_path: Path) -> tuple[int, int, str]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,codec_name",
            "-of",
            "json",
            str(input_path),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    data = json.loads(result.stdout)
    stream = data["streams"][0]
    return int(stream["width"]), int(stream["height"]), str(stream.get("codec_name", "image"))


def split_with_pillow(input_path: Path, out_dir: Path, chunk_height: int, overlap: int) -> tuple[int, int, str, int]:
    Image = import_pillow()
    if Image is None:
        raise RuntimeError("Pillow is not importable")

    with Image.open(input_path) as img:
        width, height = img.size
        image_format = img.format or "image"
        count = 0
        for idx, top, bottom in ranges(height, chunk_height, overlap):
            out_path = out_dir / f"chunk_{idx:03d}_{top}_{bottom}.png"
            img.crop((0, top, width, bottom)).save(out_path)
            print(f"saved {out_path} ({bottom - top}px)")
            count += 1
    return width, height, image_format, count


def split_with_ffmpeg(input_path: Path, out_dir: Path, chunk_height: int, overlap: int) -> tuple[int, int, str, int]:
    width, height, image_format = ffprobe_dimensions(input_path)
    count = 0
    for idx, top, bottom in ranges(height, chunk_height, overlap):
        out_path = out_dir / f"chunk_{idx:03d}_{top}_{bottom}.png"
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(input_path),
                "-vf",
                f"crop={width}:{bottom - top}:0:{top}",
                str(out_path),
            ],
            check=True,
        )
        print(f"saved {out_path} ({bottom - top}px)")
        count += 1
    return width, height, image_format, count


def choose_tool(requested: str) -> str:
    has_pillow = import_pillow() is not None
    has_ffmpeg = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None

    if requested == "pillow":
        if not has_pillow:
            raise SystemExit("Pillow is not importable. Try: uvx --with pillow python scripts/split_long_screenshot.py ...")
        return "pillow"

    if requested == "ffmpeg":
        if not has_ffmpeg:
            raise SystemExit("ffmpeg and ffprobe are required for --tool ffmpeg")
        return "ffmpeg"

    if has_pillow:
        return "pillow"
    if has_ffmpeg:
        return "ffmpeg"

    raise SystemExit(
        "No local image splitter found. Use an existing ffmpeg/ffprobe, or run once with:\n"
        "  uvx --with pillow python scripts/split_long_screenshot.py <input-image>"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_image", type=Path)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--chunk-height", type=int, default=2500)
    parser.add_argument("--overlap", type=int, default=500)
    parser.add_argument("--tool", choices=("auto", "pillow", "ffmpeg"), default="auto")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = args.input_image.expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"input image not found: {input_path}")

    out_dir = args.out_dir
    if out_dir is None:
        out_dir = Path(tempfile.mkdtemp(prefix="feishu_ocr.", dir="/tmp"))
    else:
        out_dir = out_dir.expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

    tool = choose_tool(args.tool)
    if tool == "pillow":
        width, height, image_format, count = split_with_pillow(input_path, out_dir, args.chunk_height, args.overlap)
    else:
        width, height, image_format, count = split_with_ffmpeg(input_path, out_dir, args.chunk_height, args.overlap)

    print(f"tool={tool}")
    print(f"input={input_path}")
    print(f"width={width} height={height} format={image_format}")
    print(f"out_dir={out_dir}")
    print(f"chunks={count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
