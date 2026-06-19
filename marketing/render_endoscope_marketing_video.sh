#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/marketing/output"
FONT_FILE="/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
OUT_FILE="$OUT_DIR/endoscope-marketing-5s.mp4"

mkdir -p "$OUT_DIR"

if [[ ! -f "$FONT_FILE" ]]; then
  echo "Missing Chinese font at: $FONT_FILE" >&2
  exit 1
fi

ffmpeg -y \
  -f lavfi -i "color=c=0x07111f:s=1920x1080:d=1.8:r=30" \
  -f lavfi -i "color=c=0x081623:s=1920x1080:d=1.8:r=30" \
  -f lavfi -i "color=c=0x06101b:s=1920x1080:d=1.8:r=30" \
  -filter_complex "\
[0:v]drawgrid=w=160:h=160:t=1:c=0x2ab7ff@0.08,\
drawbox=x=120:y=180:w=760:h=420:color=0x0d8dff@0.08:t=fill,\
drawbox=x=120:y=180:w=760:h=420:color=0x34d2ff@0.70:t=4,\
drawbox=x=220+90*t:y=255:w=240:h=8:color=0x54e1ff@0.95:t=fill,\
drawbox=x=300:y=290+50*sin(2*PI*t/1.8):w=8:h=220:color=0x54e1ff@0.78:t=fill,\
drawbox=x=560:y=240:w=200:h=200:color=0x15cfff@0.12:t=fill,\
drawbox=x=560:y=240:w=200:h=200:color=0x15cfff@0.70:t=3,\
drawbox=x=610:y=290:w=100:h=100:color=0xffffff@0.10:t=fill,\
drawtext=fontfile=${FONT_FILE}:text='内窥镜主控板定制':fontsize=74:fontcolor=white:x=980:y=300:alpha='min(1,(t+0.05)/0.35)',\
drawtext=fontfile=${FONT_FILE}:text='高速信号  |  稳定供电  |  精准控制':fontsize=34:fontcolor=0x93ddff:x=984:y=404:alpha='min(1,(t-0.05)/0.35)',\
drawtext=fontfile=${FONT_FILE}:text='Custom Controller Boards for Endoscopy':fontsize=30:fontcolor=0x5fb9ff:x=982:y=464:alpha='min(1,(t-0.10)/0.35)',\
format=yuv420p[s1];\
[1:v]drawgrid=w=120:h=120:t=1:c=0x22c6ff@0.06,\
drawbox=x=160:y=150:w=620:h=360:color=0x10a4ff@0.10:t=fill,\
drawbox=x=160:y=150:w=620:h=360:color=0x43d9ff@0.72:t=4,\
drawbox=x=230:y=230:w=200:h=110:color=0x6ee6ff@0.12:t=fill,\
drawbox=x=470:y=230:w=200:h=110:color=0x6ee6ff@0.12:t=fill,\
drawbox=x=230:y=370:w=440:h=70:color=0x34cfff@0.10:t=fill,\
drawbox=x=210+60*sin(2*PI*t/1.8):y=205:w=520:h=6:color=0x89eeff@0.95:t=fill,\
drawbox=x=300:y=580:w=1320:h=2:color=0x4fd4ff@0.28:t=fill,\
drawtext=fontfile=${FONT_FILE}:text='影像系统定制':fontsize=74:fontcolor=white:x=980:y=300:alpha='min(1,(t+0.05)/0.35)',\
drawtext=fontfile=${FONT_FILE}:text='ISP 调校  |  图像优化  |  低延时传输':fontsize=34:fontcolor=0x93ddff:x=984:y=404:alpha='min(1,(t-0.05)/0.35)',\
drawtext=fontfile=${FONT_FILE}:text='ISP Tuning, Image Optimization, Low-latency Pipeline':fontsize=30:fontcolor=0x5fb9ff:x=982:y=464:alpha='min(1,(t-0.10)/0.35)',\
format=yuv420p[s2];\
[2:v]drawgrid=w=180:h=180:t=1:c=0x1fb8ff@0.07,\
drawbox=x=0:y=760:w=1920:h=160:color=0x0b2d4e@0.28:t=fill,\
drawbox=x=180:y=240:w=340:h=340:color=0x17bfff@0.12:t=fill,\
drawbox=x=180:y=240:w=340:h=340:color=0x44dbff@0.70:t=5,\
drawbox=x=290:y=350:w=120:h=120:color=0xffffff@0.11:t=fill,\
drawbox=x=600:y=560:w=680:h=10:color=0x5be1ff@0.90:t=fill,\
drawbox=x=600:y=592:w=520:h=4:color=0x5be1ff@0.38:t=fill,\
drawtext=fontfile=${FONT_FILE}:text='方案设计到整机联调':fontsize=76:fontcolor=white:x=600:y=310:alpha='min(1,(t+0.05)/0.35)',\
drawtext=fontfile=${FONT_FILE}:text='内窥镜主控板与影像系统一体化开发支持':fontsize=38:fontcolor=0x95deff:x=602:y=420:alpha='min(1,(t-0.02)/0.35)',\
drawtext=fontfile=${FONT_FILE}:text='One-stop Endoscope Electronics & Imaging Development':fontsize=30:fontcolor=0x5fb9ff:x=602:y=484:alpha='min(1,(t-0.08)/0.35)',\
format=yuv420p[s3];\
[s1][s2]xfade=transition=fade:duration=0.2:offset=1.6[x1];\
[x1][s3]xfade=transition=fade:duration=0.2:offset=3.2[v]" \
  -map "[v]" \
  -c:v libx264 \
  -preset medium \
  -crf 20 \
  -pix_fmt yuv420p \
  -movflags +faststart \
  "$OUT_FILE"

echo "Rendered: $OUT_FILE"
