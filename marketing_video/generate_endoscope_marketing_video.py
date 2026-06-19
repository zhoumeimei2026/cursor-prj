#!/usr/bin/env python3
"""Generate a 5-second marketing video for endoscopy control board services."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
DEFAULT_OUTPUT = OUTPUT_DIR / "endoscope_marketing_5s.mp4"
DEFAULT_POSTER = OUTPUT_DIR / "endoscope_marketing_5s_poster.png"
FONT_FILE = Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc")

WIDTH = 1280
HEIGHT = 720
FPS = 30
DURATION = 5


def alpha_expr(start: float, end: float, fade_in: float = 0.32, fade_out: float = 0.32) -> str:
    """Return an ffmpeg expression for smooth fade in and fade out."""
    fade_in_end = start + fade_in
    fade_out_start = end - fade_out
    return (
        f"if(lt(t,{start:.2f}),0,"
        f"if(lt(t,{fade_in_end:.2f}),(t-{start:.2f})/{fade_in:.2f},"
        f"if(lt(t,{fade_out_start:.2f}),1,"
        f"if(lt(t,{end:.2f}),({end:.2f}-t)/{fade_out:.2f},0))))"
    )


def slide_y(base_y: int, start: float, settle: float = 0.45, offset: int = 28) -> str:
    """Move text slightly upward while it fades in."""
    settle_end = start + settle
    return (
        f"{base_y}+if(lt(t,{start:.2f}),{offset},"
        f"if(lt(t,{settle_end:.2f}),({settle_end:.2f}-t)*{offset / settle:.3f},0))"
    )


def drawtext(
    *,
    textfile: Path,
    fontsize: int,
    fontcolor: str,
    x: str,
    y: str,
    alpha: str,
    shadowcolor: str = "0x04121c@0.95",
    shadowx: int = 0,
    shadowy: int = 6,
    borderw: int = 0,
    bordercolor: str = "0x001018@0.75",
) -> str:
    """Build one drawtext filter expression."""
    return "drawtext=" + ":".join(
        [
            f"fontfile={FONT_FILE}",
            f"textfile={textfile}",
            f"fontsize={fontsize}",
            f"fontcolor={fontcolor}",
            "text_shaping=1",
            "expansion=none",
            "fix_bounds=1",
            f"shadowcolor={shadowcolor}",
            f"shadowx={shadowx}",
            f"shadowy={shadowy}",
            f"borderw={borderw}",
            f"bordercolor={bordercolor}",
            f"x='{x}'",
            f"y='{y}'",
            f"alpha='{alpha}'",
        ]
    )


def write_text(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def render_video(output_path: Path, poster_path: Path) -> None:
    if not FONT_FILE.exists():
        raise FileNotFoundError(f"Chinese-capable font not found: {FONT_FILE}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="endoscope-video-") as temp_dir_name:
        temp_dir = Path(temp_dir_name)

        label = write_text(temp_dir / "label.txt", "ENDOSCOPY OEM / ODM")
        tagline = write_text(temp_dir / "tagline.txt", "CONTROL BOARD + IMAGING SYSTEM")

        scene1_main = write_text(temp_dir / "scene1_main.txt", "内窥镜主控板")
        scene1_sub = write_text(temp_dir / "scene1_sub.txt", "定制开发")
        scene1_note = write_text(temp_dir / "scene1_note.txt", "硬件设计  ·  接口适配  ·  稳定集成")

        scene2_main = write_text(temp_dir / "scene2_main.txt", "影像系统方案")
        scene2_sub = write_text(temp_dir / "scene2_sub.txt", "低延时  |  高画质  |  易联调")
        scene2_note = write_text(temp_dir / "scene2_note.txt", "支持图像链路优化与整机协同")

        scene3_main = write_text(temp_dir / "scene3_main.txt", "从主控到成像")
        scene3_sub = write_text(temp_dir / "scene3_sub.txt", "一站式联合开发")
        scene3_note = write_text(temp_dir / "scene3_note.txt", "欢迎对接定制项目")

        scene1 = (0.00, 1.75)
        scene2 = (1.55, 3.45)
        scene3 = (3.20, 5.00)

        filters = [
            "format=yuv420p",
            "eq=contrast=1.10:brightness=-0.03:saturation=1.15",
            "drawgrid=width=80:height=80:thickness=1:color=0x7cecff@0.05",
            "drawbox=x='-360+t*210':y=0:w=280:h=ih:color=0x25ddff@0.08:t=fill",
            "drawbox=x='iw-340-t*70':y=92:w=220:h=2:color=0x8af6ff@0.65:t=fill",
            "drawbox=x='iw-340':y=92:w=2:h=220:color=0x8af6ff@0.18:t=fill",
            "drawbox=x=96:y=588:w=260:h=2:color=0x8af6ff@0.42:t=fill",
            "drawbox=x=96:y=588:w=2:h=56:color=0x8af6ff@0.18:t=fill",
            "drawbox=x='mod(t*320,iw)':y=0:w=3:h=ih:color=0xffffff@0.035:t=fill",
            "drawbox=x=0:y='mod(t*170,ih)':w=iw:h=2:color=0x59ecff@0.05:t=fill",
            "noise=alls=2.5:allf=t+u",
            "vignette=PI/5",
            drawtext(
                textfile=label,
                fontsize=24,
                fontcolor="0xa9f8ff",
                x="110",
                y="108",
                alpha="0.75",
                shadowy=4,
            ),
            drawtext(
                textfile=tagline,
                fontsize=22,
                fontcolor="0xffffff",
                x="110",
                y="h-84",
                alpha="0.45",
                shadowy=4,
            ),
            drawtext(
                textfile=scene1_main,
                fontsize=76,
                fontcolor="0xffffff",
                x="(w-text_w)/2",
                y=slide_y(210, scene1[0]),
                alpha=alpha_expr(*scene1),
                borderw=1,
            ),
            drawtext(
                textfile=scene1_sub,
                fontsize=52,
                fontcolor="0x78f3ff",
                x="(w-text_w)/2",
                y=slide_y(318, scene1[0] + 0.08),
                alpha=alpha_expr(*scene1),
            ),
            drawtext(
                textfile=scene1_note,
                fontsize=30,
                fontcolor="0xd8fbff",
                x="(w-text_w)/2",
                y=slide_y(414, scene1[0] + 0.16),
                alpha=alpha_expr(*scene1),
                shadowy=3,
            ),
            drawtext(
                textfile=scene2_main,
                fontsize=74,
                fontcolor="0xffffff",
                x="(w-text_w)/2",
                y=slide_y(210, scene2[0]),
                alpha=alpha_expr(*scene2),
                borderw=1,
            ),
            drawtext(
                textfile=scene2_sub,
                fontsize=48,
                fontcolor="0x78f3ff",
                x="(w-text_w)/2",
                y=slide_y(318, scene2[0] + 0.08),
                alpha=alpha_expr(*scene2),
            ),
            drawtext(
                textfile=scene2_note,
                fontsize=30,
                fontcolor="0xd8fbff",
                x="(w-text_w)/2",
                y=slide_y(414, scene2[0] + 0.16),
                alpha=alpha_expr(*scene2),
                shadowy=3,
            ),
            drawtext(
                textfile=scene3_main,
                fontsize=74,
                fontcolor="0xffffff",
                x="(w-text_w)/2",
                y=slide_y(210, scene3[0]),
                alpha=alpha_expr(*scene3),
                borderw=1,
            ),
            drawtext(
                textfile=scene3_sub,
                fontsize=50,
                fontcolor="0x78f3ff",
                x="(w-text_w)/2",
                y=slide_y(318, scene3[0] + 0.08),
                alpha=alpha_expr(*scene3),
            ),
            drawtext(
                textfile=scene3_note,
                fontsize=30,
                fontcolor="0xffffff",
                x="(w-text_w)/2",
                y=slide_y(414, scene3[0] + 0.16),
                alpha=alpha_expr(*scene3),
                shadowy=3,
            ),
        ]

        filter_complex = ",".join(filters)

        render_command = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            (
                f"gradients=s={WIDTH}x{HEIGHT}:r={FPS}:d={DURATION}:speed=0.006:"
                "type=spiral:c0=0x04111b:c1=0x0b1e33:c2=0x093458:c3=0x00d0ff:n=4"
            ),
            "-filter_complex",
            filter_complex,
            "-t",
            str(DURATION),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-movflags",
            "+faststart",
            "-pix_fmt",
            "yuv420p",
            str(output_path),
        ]

        subprocess.run(render_command, check=True)

        poster_command = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            "4.10",
            "-i",
            str(output_path),
            "-frames:v",
            "1",
            str(poster_path),
        ]
        subprocess.run(poster_command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Video output path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--poster",
        type=Path,
        default=DEFAULT_POSTER,
        help=f"Poster output path (default: {DEFAULT_POSTER})",
    )
    args = parser.parse_args()

    render_video(args.output.resolve(), args.poster.resolve())
    print(f"Video written to: {args.output.resolve()}")
    print(f"Poster written to: {args.poster.resolve()}")


if __name__ == "__main__":
    main()
