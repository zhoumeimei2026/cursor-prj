#!/usr/bin/env python3
"""Generate a 5-second marketing video for endoscope control board & imaging systems."""

import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent
ARTIFACTS = Path("/opt/cursor/artifacts/marketing-video")
ASSETS = Path("/opt/cursor/artifacts/assets")
FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"

W, H = 1920, 1080
FPS = 30
DURATION = 5
FONT_MAIN = 72
FONT_SUB = 42
FONT_TAG = 36


def load_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size)


def create_text_overlay(
    main_text: str,
    sub_text: str,
    tag_text: str = "",
    accent: tuple[int, int, int] = (0, 180, 220),
) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Accent line
    line_y = H // 2 - 60
    draw.rectangle([(W // 2 - 120, line_y), (W // 2 + 120, line_y + 4)], fill=(*accent, 255))

    font_main = load_font(FONT_MAIN)
    font_sub = load_font(FONT_SUB)
    font_tag = load_font(FONT_TAG)

    # Main title
    bbox = draw.textbbox((0, 0), main_text, font=font_main)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    y = H // 2 - 20
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        draw.text((x + dx, y + dy), main_text, font=font_main, fill=(0, 0, 0, 180))
    draw.text((x, y), main_text, font=font_main, fill=(255, 255, 255, 255))

    # Subtitle
    bbox = draw.textbbox((0, 0), sub_text, font=font_sub)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    y = H // 2 + 80
    draw.text((x, y), sub_text, font=font_sub, fill=(*accent, 255))

    if tag_text:
        bbox = draw.textbbox((0, 0), tag_text, font=font_tag)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        y = H - 120
        draw.text((x, y), tag_text, font=font_tag, fill=(200, 210, 220, 220))

    return img


def prepare_background(src: Path, dst: Path) -> None:
    bg = Image.open(src).convert("RGB")
    bg = bg.resize((W, H), Image.LANCZOS)
    overlay = Image.new("RGBA", (W, H), (8, 18, 40, 160))
    bg = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    bg = bg.filter(ImageFilter.GaussianBlur(radius=0.5))
    bg.save(dst, quality=95)


def build_video(bg_path: Path, overlays: list[tuple[Path, float, float]], output: Path) -> None:
    """Build video with timed text overlays and Ken Burns zoom."""
    filter_parts = []
    inputs = ["-loop", "1", "-i", str(bg_path)]

    for i, (overlay_path, start, end) in enumerate(overlays):
        inputs.extend(["-loop", "1", "-i", str(overlay_path)])

    # Background: slow zoom in
    filter_parts.append(
        f"[0:v]scale=2200:1238,crop=1920:1080:"
        f"x='(2200-1920)/2*(1-t/{DURATION})':y='(1238-1080)/2*(1-t/{DURATION})',"
        f"fade=t=in:st=0:d=0.5,fade=t=out:st={DURATION - 0.5}:d=0.5[bg]"
    )

    prev = "[bg]"
    for i, (_, start, end) in enumerate(overlays):
        idx = i + 1
        fade_in = 0.4
        fade_out = 0.4
        filter_parts.append(
            f"[{idx}:v]format=rgba,fade=t=in:st={start}:d={fade_in}:alpha=1,"
            f"fade=t=out:st={end - fade_out}:d={fade_out}:alpha=1[ov{i}]"
        )
        filter_parts.append(f"{prev}[ov{i}]overlay=0:0:enable='between(t,{start},{end})'[v{i}]")
        prev = f"[v{i}]"

    filter_parts.append(f"{prev}format=yuv420p[vout]")
    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-t", str(DURATION),
        "-r", str(FPS),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(output),
    ]
    subprocess.run(cmd, check=True)


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    bg_src = ASSETS / "endoscope-bg.png"
    if not bg_src.exists():
        bg_src = ROOT / "endoscope-bg.png"

    bg_path = ARTIFACTS / "background.jpg"
    prepare_background(bg_src, bg_path)

    scenes = [
        ("内窥镜主控板 · 影像系统", "专业定制开发", "承接 OEM / ODM 项目"),
        ("硬件设计 · 影像算法 · 系统集成", "一站式解决方案", ""),
        ("精工制造 · 可靠交付", "从方案到量产", "医疗级品质保障"),
    ]

    overlay_paths = []
    for i, (main, sub, tag) in enumerate(scenes):
        overlay = create_text_overlay(main, sub, tag)
        path = ARTIFACTS / f"overlay_{i}.png"
        overlay.save(path)
        overlay_paths.append(path)

    # Scene timing within 5 seconds
    timed = [
        (overlay_paths[0], 0.0, 2.0),
        (overlay_paths[1], 1.6, 3.6),
        (overlay_paths[2], 3.2, 5.0),
    ]

    output = ARTIFACTS / "endoscope-marketing-5s.mp4"
    build_video(bg_path, timed, output)
    print(f"Video saved to: {output}")


if __name__ == "__main__":
    main()
