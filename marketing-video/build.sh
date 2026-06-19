#!/usr/bin/env bash
#
# Build a 5-second 1080p marketing video for a team that does custom
# development of endoscope main control boards & imaging systems.
#
# Pipeline:
#   1. Three branded still images (assets/) -> animated 1080p clips
#      (Ken Burns zoom/pan + Chinese text overlays + per-clip fades)
#   2. Clips joined with crossfade (xfade) transitions
#   3. A subtle ambient audio bed mixed underneath
#
# Requires: ffmpeg (with libx264, drawtext/freetype) and a CJK font.
#
set -euo pipefail

# --- Paths ------------------------------------------------------------------
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETS="$HERE/assets"
BUILD="$HERE/build"
OUT="$HERE/endoscope_marketing_5s.mp4"
mkdir -p "$BUILD"

# --- Look & feel ------------------------------------------------------------
FPS=30
W=1920
H=1080
FONT="${FONT:-/usr/share/fonts/truetype/wqy/wqy-microhei.ttc}"   # CJK-capable
ACCENT="0x35C3FF"   # tech blue accent

# Per-scene durations (seconds). With two 0.4s crossfades the final
# length is 2.1 + 1.9 + 1.8 - 0.4 - 0.4 = 5.0s.
D1=2.1
D2=1.9
D3=1.8
XF=0.4

frames() { awk -v d="$1" -v f="$FPS" 'BEGIN{printf "%d", d*f}'; }
F1=$(frames "$D1"); F2=$(frames "$D2"); F3=$(frames "$D3")

# Common drawtext styling (shadow for legibility on any background).
TXT_COMMON="fontfile=$FONT:fontcolor=white:shadowcolor=black@0.6:shadowx=2:shadowy=2"

echo ">> Scene 1: main control board (zoom-in)"
ffmpeg -y -loop 1 -i "$ASSETS/scene1_board.png" -filter_complex "
  [0:v]scale=$W:$H:force_original_aspect_ratio=increase,crop=$W:$H,scale=3840:2160,
  zoompan=z='min(1.0+0.10*on/$F1,1.10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$F1:s=${W}x${H}:fps=$FPS,
  drawtext=$TXT_COMMON:text='内窥镜主控板':fontsize=92:x=(w-text_w)/2:y=h*0.68:alpha='if(lt(t,0.4),t/0.4,1)',
  drawtext=$TXT_COMMON:text='高性能 · 定制开发':fontsize=46:fontcolor=$ACCENT:x=(w-text_w)/2:y=h*0.68+120:alpha='if(lt(t,0.7),max(0\,(t-0.3)/0.4),1)',
  fade=t=in:st=0:d=0.4,fade=t=out:st=$(awk -v d=$D1 'BEGIN{print d-0.4}'):d=0.4,
  setsar=1,format=yuv420p
" -r "$FPS" -frames:v "$F1" -an "$BUILD/clip1.mp4"

echo ">> Scene 2: imaging system (zoom-out)"
ffmpeg -y -loop 1 -i "$ASSETS/scene2_imaging.png" -filter_complex "
  [0:v]scale=$W:$H:force_original_aspect_ratio=increase,crop=$W:$H,scale=3840:2160,
  zoompan=z='max(1.10-0.10*on/$F2,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$F2:s=${W}x${H}:fps=$FPS,
  drawtext=$TXT_COMMON:text='高清影像系统':fontsize=92:x=(w-text_w)/2:y=h*0.68:alpha='if(lt(t,0.4),t/0.4,1)',
  drawtext=$TXT_COMMON:text='整机方案 · 全链路交付':fontsize=46:fontcolor=$ACCENT:x=(w-text_w)/2:y=h*0.68+120:alpha='if(lt(t,0.7),max(0\,(t-0.3)/0.4),1)',
  fade=t=in:st=0:d=0.3,fade=t=out:st=$(awk -v d=$D2 'BEGIN{print d-0.4}'):d=0.4,
  setsar=1,format=yuv420p
" -r "$FPS" -frames:v "$F2" -an "$BUILD/clip2.mp4"

echo ">> Scene 3: brand close (slow zoom-in)"
ffmpeg -y -loop 1 -i "$ASSETS/scene3_brand.png" -filter_complex "
  [0:v]scale=$W:$H:force_original_aspect_ratio=increase,crop=$W:$H,scale=3840:2160,
  zoompan=z='min(1.0+0.06*on/$F3,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$F3:s=${W}x${H}:fps=$FPS,
  drawbox=x=(w-360)/2:y=h*0.40+150:w=360:h=5:color=$ACCENT@0.9:t=fill:enable='gte(t,0.5)',
  drawtext=$TXT_COMMON:text='主控板 · 影像系统 · 定制开发':fontsize=78:x=(w-text_w)/2:y=h*0.40:alpha='if(lt(t,0.5),t/0.5,1)',
  drawtext=$TXT_COMMON:text='专业研发团队 · 助您快速落地':fontsize=44:fontcolor=$ACCENT:x=(w-text_w)/2:y=h*0.40+180:alpha='if(lt(t,0.9),max(0\,(t-0.5)/0.4),1)',
  fade=t=in:st=0:d=0.3,fade=t=out:st=$(awk -v d=$D3 'BEGIN{print d-0.5}'):d=0.5,
  setsar=1,format=yuv420p
" -r "$FPS" -frames:v "$F3" -an "$BUILD/clip3.mp4"

# --- Crossfade the three clips into one 5s video ----------------------------
echo ">> Joining clips with crossfades"
OFF1=$(awk -v d=$D1 -v x=$XF 'BEGIN{print d-x}')                     # 1.7
OFF2=$(awk -v d1=$D1 -v d2=$D2 -v x=$XF 'BEGIN{print d1+d2-2*x}')    # 3.2
ffmpeg -y -i "$BUILD/clip1.mp4" -i "$BUILD/clip2.mp4" -i "$BUILD/clip3.mp4" -filter_complex "
  [0:v][1:v]xfade=transition=fade:duration=$XF:offset=$OFF1[v01];
  [v01][2:v]xfade=transition=fade:duration=$XF:offset=$OFF2,format=yuv420p[v]
" -map "[v]" -r "$FPS" -c:v libx264 -pix_fmt yuv420p -crf 18 -preset slow "$BUILD/video_noaudio.mp4"

# --- Subtle ambient audio bed (soft perfect-fifth pad, faded) ---------------
echo ">> Generating ambient audio bed"
ffmpeg -y \
  -f lavfi -t 5 -i "sine=frequency=196:sample_rate=48000" \
  -f lavfi -t 5 -i "sine=frequency=293.66:sample_rate=48000" \
  -filter_complex "
    [0:a]volume=0.10[a0];
    [1:a]volume=0.07[a1];
    [a0][a1]amix=inputs=2:normalize=0,
    tremolo=f=4:d=0.3,lowpass=f=1200,
    afade=t=in:st=0:d=0.6,afade=t=out:st=4.2:d=0.8[a]
  " -map "[a]" -c:a aac -b:a 160k "$BUILD/bed.m4a"

# --- Mux video + audio ------------------------------------------------------
echo ">> Muxing final video"
ffmpeg -y -i "$BUILD/video_noaudio.mp4" -i "$BUILD/bed.m4a" \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 160k -shortest -movflags +faststart "$OUT"

echo ">> Done: $OUT"
ffprobe -v error -show_entries format=duration,size:stream=codec_type,width,height -of default=noprint_wrappers=1 "$OUT"
