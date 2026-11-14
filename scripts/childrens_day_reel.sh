#!/usr/bin/env bash
# Usage: childrens_day_reel.sh <daddy_reel.mp4 (audio source)> <tower_brownie.mp4> <output.mp4>
# Tower brownie footage (transition intro cut, smooth slow-mo to fit the song) + Children's Day
# header, "Tag your parents" caption, Cake N Crumble logo and @cake_n_crumble_03 watermark.
set -euo pipefail
AUD="$1"; TOWER="$2"; OUT="$3"
HERE=$(cd "$(dirname "$0")" && pwd)
LOGO="$HERE/../assets/cake_n_crumble_logo.png"
W=$(mktemp -d)
START=3.667   # first frame after the split-screen transition
python3 -I "$HERE/childrens_day_overlay.py" "$W/ov.png"
ADUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$AUD")
TDUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$TOWER")
F=$(python3 -c "print(round($ADUR/($TDUR-$START),4))")
ffmpeg -v error -y -ss $START -i "$TOWER" -i "$AUD" -loop 1 -i "$W/ov.png" -loop 1 -i "$LOGO" -filter_complex "
[0:v]setpts=$F*(PTS-STARTPTS),minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,scale=720:1280,setsar=1[bg];
[2:v]format=rgba,fade=t=in:st=0:d=0.4:alpha=1[ov];
[bg][ov]overlay=0:0:shortest=1[v1];
[3:v]scale=80:-1,format=rgba[logo];
[v1][logo]overlay=W-w-20:H-h-50:shortest=1,
drawtext=fontfile=/usr/share/fonts/opentype/inter/Inter-Bold.otf:text='@cake_n_crumble_03':fontsize=22:fontcolor=white@0.9:borderw=2:bordercolor=black@0.55:x=w-tw-18:y=h-44,format=yuv420p[v]" \
  -map "[v]" -map 1:a -t "$ADUR" -c:v libx264 -preset medium -crf 18 -c:a aac -b:a 192k -movflags +faststart "$OUT"
rm -rf "$W"
echo "done: $OUT"
