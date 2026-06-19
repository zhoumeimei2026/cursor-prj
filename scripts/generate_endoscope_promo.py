#!/usr/bin/env python3
"""Generate a 5-second endoscope systems marketing video.

The script uses only Python's standard library plus ffmpeg. It renders
animated SVG frames and muxes them with a subtle synthesized audio bed.
"""

from __future__ import annotations

import argparse
import math
import subprocess
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape


WIDTH = 1920
HEIGHT = 1080
FPS = 30
DURATION = 5.0
FONT_FAMILY = "'WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'Noto Sans', sans-serif"


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def ease_out_cubic(value: float) -> float:
    value = clamp(value)
    return 1.0 - (1.0 - value) ** 3


def smoothstep(value: float) -> float:
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def scene_opacity(t: float, start: float, end: float, fade: float = 0.35) -> float:
    if t < start or t > end:
        return 0.0
    return min(smoothstep((t - start) / fade), smoothstep((end - t) / fade))


def text(
    content: str,
    x: float,
    y: float,
    size: int,
    fill: str = "#FFFFFF",
    weight: int = 400,
    opacity: float = 1.0,
    anchor: str = "start",
    extra: str = "",
) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" opacity="{clamp(opacity):.3f}" '
        f'text-anchor="{anchor}" {extra}>{escape(content)}</text>'
    )


def rect(
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str,
    opacity: float = 1.0,
    stroke: str | None = None,
    stroke_width: float = 1.0,
    rx: float = 0.0,
) -> str:
    stroke_attrs = ""
    if stroke:
        stroke_attrs = f' stroke="{stroke}" stroke-width="{stroke_width}"'
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
        f'rx="{rx:.1f}" fill="{fill}" opacity="{clamp(opacity):.3f}"{stroke_attrs}/>'
    )


def line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    stroke: str,
    width: float = 2.0,
    opacity: float = 1.0,
    extra: str = "",
) -> str:
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{stroke}" stroke-width="{width:.1f}" '
        f'opacity="{clamp(opacity):.3f}" {extra}/>'
    )


def circle(
    cx: float,
    cy: float,
    r: float,
    fill: str = "none",
    stroke: str | None = None,
    stroke_width: float = 2.0,
    opacity: float = 1.0,
    extra: str = "",
) -> str:
    stroke_attrs = ""
    if stroke:
        stroke_attrs = f' stroke="{stroke}" stroke-width="{stroke_width:.1f}"'
    return (
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" '
        f'opacity="{clamp(opacity):.3f}"{stroke_attrs} {extra}/>'
    )


def polyline(points: list[tuple[float, float]], stroke: str, width: float, opacity: float) -> str:
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return (
        f'<polyline points="{pts}" fill="none" stroke="{stroke}" '
        f'stroke-width="{width:.1f}" opacity="{clamp(opacity):.3f}" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
    )


def render_background(t: float) -> list[str]:
    parts: list[str] = [
        '<rect width="1920" height="1080" fill="url(#bg)"/>',
        f'<circle cx="{1540 + 45 * math.sin(t * 1.4):.1f}" cy="210" r="360" '
        'fill="url(#cyanGlow)" opacity="0.55"/>',
        f'<circle cx="{360 + 36 * math.sin(t * 1.0):.1f}" cy="840" r="420" '
        'fill="url(#violetGlow)" opacity="0.42"/>',
    ]

    grid_offset = (t * 42.0) % 120.0
    parts.append('<g opacity="0.15">')
    for x in range(-120, WIDTH + 121, 120):
        parts.append(line(x + grid_offset, 0, x + grid_offset, HEIGHT, "#6DEBFF", 1.0, 0.55))
    for y in range(-120, HEIGHT + 121, 120):
        parts.append(line(0, y + grid_offset * 0.55, WIDTH, y + grid_offset * 0.55, "#6DEBFF", 1.0, 0.32))
    parts.append("</g>")

    parts.append('<g opacity="0.72">')
    for i in range(40):
        x = (137 * i + 55 * math.sin(t * 0.7 + i)) % WIDTH
        y = (83 * i + 35 * math.cos(t * 0.9 + i * 0.6)) % HEIGHT
        pulse = 0.35 + 0.45 * (0.5 + 0.5 * math.sin(t * 3.0 + i))
        parts.append(circle(x, y, 2.2 + (i % 4) * 0.35, "#7DF7FF", opacity=pulse))
    parts.append("</g>")
    return parts


def render_hardware_visual(t: float) -> list[str]:
    parts: list[str] = []
    lens_x = 420 + 16 * math.sin(t * 1.1)
    lens_y = 575 + 10 * math.cos(t * 1.3)
    ring_dash = 260 - (t * 88) % 260

    parts.append('<g filter="url(#softGlow)">')
    parts.append(circle(lens_x, lens_y, 204, "rgba(24,54,86,0.65)", "#34DFFF", 4, 0.80))
    parts.append(circle(lens_x, lens_y, 148, "rgba(9,18,32,0.78)", "#9BF7FF", 2.2, 0.72))
    parts.append(circle(lens_x, lens_y, 72, "url(#lens)", "#FFFFFF", 2.0, 0.92))
    parts.append(
        circle(
            lens_x,
            lens_y,
            186,
            "none",
            "#6DEBFF",
            5.0,
            0.72,
            f'stroke-dasharray="52 208" stroke-dashoffset="{ring_dash:.1f}"',
        )
    )
    parts.append(circle(lens_x + 32, lens_y - 42, 22, "#FFFFFF", opacity=0.34))
    parts.append(line(lens_x - 270, lens_y, lens_x - 620, lens_y - 82, "#32E6FF", 14, 0.30, 'stroke-linecap="round"'))
    parts.append(line(lens_x - 292, lens_y + 30, lens_x - 650, lens_y + 104, "#32E6FF", 10, 0.20, 'stroke-linecap="round"'))
    parts.append("</g>")

    board_x = 1110 + 10 * math.sin(t * 1.6)
    board_y = 210 + 8 * math.cos(t * 1.2)
    parts.append('<g filter="url(#softGlow)">')
    parts.append(rect(board_x, board_y, 620, 360, "#102B45", 0.88, "#4BE7FF", 2.2, 34))
    parts.append(rect(board_x + 244, board_y + 112, 132, 112, "#081522", 0.95, "#7DF7FF", 2, 18))
    parts.append(text("ISP", board_x + 310, board_y + 181, 34, "#EAFBFF", 700, 0.95, "middle"))
    for idx, (cx, cy) in enumerate(
        [
            (board_x + 96, board_y + 82),
            (board_x + 500, board_y + 82),
            (board_x + 102, board_y + 278),
            (board_x + 505, board_y + 278),
        ]
    ):
        parts.append(rect(cx - 46, cy - 30, 92, 60, "#173F61", 0.96, "#39DFF5", 1.5, 11))
        parts.append(text(["MCU", "MIPI", "FPGA", "USB3"][idx], cx, cy + 10, 22, "#C9FAFF", 700, 0.88, "middle"))

    trace_segments = [
        (board_x + 142, board_y + 82, board_x + 244, board_y + 140),
        (board_x + 500, board_y + 82, board_x + 376, board_y + 140),
        (board_x + 148, board_y + 278, board_x + 244, board_y + 198),
        (board_x + 505, board_y + 278, board_x + 376, board_y + 198),
        (board_x + 310, board_y + 224, board_x + 310, board_y + 330),
    ]
    for idx, segment in enumerate(trace_segments):
        dash = 80 - ((t * 120 + idx * 22) % 80)
        parts.append(
            line(
                *segment,
                "#5BF2FF",
                4.0,
                0.68,
                f'stroke-linecap="round" stroke-dasharray="28 52" stroke-dashoffset="{dash:.1f}"',
            )
        )
    parts.append("</g>")

    monitor_x = 1070
    monitor_y = 660
    parts.append('<g filter="url(#softGlow)">')
    parts.append(rect(monitor_x, monitor_y, 650, 250, "#0A1728", 0.88, "#4BE7FF", 2.2, 28))
    parts.append(rect(monitor_x + 34, monitor_y + 36, 582, 146, "#07101D", 0.94, "#1C637C", 1.2, 18))
    wave: list[tuple[float, float]] = []
    for i in range(88):
        x = monitor_x + 56 + i * 6.4
        y = monitor_y + 110 + math.sin(i * 0.28 + t * 5.2) * 34 + math.sin(i * 0.77 + t * 2.0) * 12
        wave.append((x, y))
    parts.append(polyline(wave, "#55F2FF", 4.0, 0.90))
    parts.append(text("4K 低延迟影像链路", monitor_x + 58, monitor_y + 224, 30, "#EAFBFF", 700, 0.95))
    parts.append("</g>")
    return parts


def render_scene_text(t: float) -> list[str]:
    parts: list[str] = []

    op1 = scene_opacity(t, 0.0, 2.10, 0.42)
    if op1:
        slide = -92 * (1.0 - ease_out_cubic(t / 0.62))
        parts.append(f'<g opacity="{op1:.3f}" transform="translate({slide:.1f},0)">')
        parts.append(rect(132, 142, 410, 50, "#112C45", 0.78, "#3BDAF0", 1.2, 25))
        parts.append(text("ENDOSCOPE CUSTOM R&D", 160, 176, 26, "#8DF7FF", 700, 0.95))
        parts.append(text("内窥镜主控板", 130, 286, 82, "url(#titleGradient)", 800, 1.0))
        parts.append(text("影像系统定制", 130, 388, 82, "#FFFFFF", 800, 0.98))
        parts.append(text("硬件控制 · ISP调校 · 高清采集 · 低延迟传输", 134, 462, 34, "#CFEFFF", 500, 0.92))
        parts.append("</g>")

    op2 = scene_opacity(t, 1.55, 3.65, 0.34)
    if op2:
        parts.append(f'<g opacity="{op2:.3f}">')
        parts.append(text("从原理图到稳定成像", 134, 210, 58, "#FFFFFF", 800, 0.96))
        parts.append(text("面向内窥镜整机厂与医疗影像设备团队", 136, 264, 30, "#AEEBFF", 500, 0.86))
        cards = [
            ("主控板开发", "ARM / FPGA / 接口控制"),
            ("影像链路", "CMOS / ISP / 4K采集"),
            ("系统集成", "SDK / 算法 / 量产测试"),
        ]
        for idx, (title, body) in enumerate(cards):
            local = smoothstep((t - 1.72 - idx * 0.18) / 0.38)
            x = 138 + idx * 284
            y = 348 + 34 * (1.0 - local)
            parts.append(rect(x, y, 252, 166, "#0D243A", 0.66 * local, "#46E3F6", 1.4, 24))
            parts.append(text(title, x + 126, y + 64, 31, "#FFFFFF", 800, local, "middle"))
            parts.append(text(body, x + 126, y + 113, 22, "#AEEBFF", 500, local * 0.88, "middle"))
        parts.append("</g>")

    op3 = scene_opacity(t, 3.28, 5.0, 0.38)
    if op3:
        scale = 0.96 + 0.04 * smoothstep((t - 3.28) / 0.55)
        parts.append(f'<g opacity="{op3:.3f}" transform="translate(960,0) scale({scale:.3f}) translate(-960,0)">')
        parts.append(rect(238, 240, 1460, 360, "#07182A", 0.66, "#40E3F5", 1.6, 42))
        parts.append(text("让下一代内窥镜平台更快落地", 960, 360, 70, "#FFFFFF", 800, 0.98, "middle"))
        parts.append(text("方案咨询 · 样机验证 · 量产支持", 960, 444, 40, "#8DF7FF", 700, 0.94, "middle"))
        parts.append(text("主控板 + 影像系统一站式定制开发", 960, 520, 32, "#D8F8FF", 500, 0.90, "middle"))
        parts.append("</g>")

    parts.append(text("ODM / OEM  |  Endoscope Imaging Engineering", 960, 1008, 24, "#86DDEB", 600, 0.72, "middle"))
    return parts


def render_frame(t: float) -> str:
    parts: list[str] = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">',
        "<defs>",
        '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '<stop offset="0%" stop-color="#05101E"/>',
        '<stop offset="46%" stop-color="#071A2D"/>',
        '<stop offset="100%" stop-color="#020611"/>',
        "</linearGradient>",
        '<linearGradient id="titleGradient" x1="0" y1="0" x2="1" y2="0">',
        '<stop offset="0%" stop-color="#FFFFFF"/>',
        '<stop offset="52%" stop-color="#83F7FF"/>',
        '<stop offset="100%" stop-color="#43A8FF"/>',
        "</linearGradient>",
        '<radialGradient id="cyanGlow"><stop offset="0%" stop-color="#34E8FF" stop-opacity="0.75"/>'
        '<stop offset="100%" stop-color="#34E8FF" stop-opacity="0"/></radialGradient>',
        '<radialGradient id="violetGlow"><stop offset="0%" stop-color="#5772FF" stop-opacity="0.48"/>'
        '<stop offset="100%" stop-color="#5772FF" stop-opacity="0"/></radialGradient>',
        '<radialGradient id="lens"><stop offset="0%" stop-color="#CFFFFF"/>'
        '<stop offset="35%" stop-color="#40E5FF"/><stop offset="100%" stop-color="#071526"/></radialGradient>',
        '<filter id="softGlow" x="-40%" y="-40%" width="180%" height="180%">',
        '<feGaussianBlur stdDeviation="3.2" result="blur"/>',
        '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>',
        "</filter>",
        f'<style>text {{ font-family: {FONT_FAMILY}; letter-spacing: 0.5px; }}</style>',
        "</defs>",
    ]
    parts.extend(render_background(t))
    parts.extend(render_hardware_visual(t))
    parts.extend(render_scene_text(t))
    parts.append("</svg>")
    return "\n".join(parts)


def build_video(output: Path, fps: int, duration: float) -> None:
    frame_count = int(round(duration * fps))
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="endoscope_promo_frames_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        for frame in range(frame_count):
            t = frame / fps
            (temp_dir / f"frame_{frame:04d}.svg").write_text(render_frame(t), encoding="utf-8")

        audio_expr = (
            "aevalsrc="
            "0.035*sin(2*PI*92*t)+0.018*sin(2*PI*184*t)+"
            "0.010*sin(2*PI*(360+18*sin(2*PI*0.5*t))*t)"
            f":duration={duration:.3f}:sample_rate=48000"
        )
        command = [
            "ffmpeg",
            "-y",
            "-framerate",
            str(fps),
            "-i",
            str(temp_dir / "frame_%04d.svg"),
            "-f",
            "lavfi",
            "-i",
            audio_expr,
            "-vf",
            f"scale={WIDTH}:{HEIGHT},format=yuv420p",
            "-af",
            f"afade=t=in:st=0:d=0.35,afade=t=out:st={max(duration - 0.45, 0):.2f}:d=0.45,volume=0.85",
            "-c:v",
            "libx264",
            "-profile:v",
            "high",
            "-level",
            "4.1",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(fps),
            "-t",
            f"{duration:.3f}",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            "-shortest",
            str(output),
        ]
        subprocess.run(command, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the endoscope marketing video.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("media/endoscope_promo_5s.mp4"),
        help="Output MP4 path.",
    )
    parser.add_argument("--fps", type=int, default=FPS, help="Frames per second.")
    parser.add_argument("--duration", type=float, default=DURATION, help="Video duration in seconds.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_video(args.output, args.fps, args.duration)
    print(f"Generated {args.output} ({args.duration:.1f}s at {args.fps} fps)")


if __name__ == "__main__":
    main()
