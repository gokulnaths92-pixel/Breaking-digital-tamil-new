#!/usr/bin/env bash
# Usage: endcard_reel.sh <reel.mp4> <output.mp4>
# Adds the small Cake N Crumble logo + handle (bottom-left) and a 3s brand end card
# ("DM for Custom Cakes") with a crossfade.
set -euo pipefail
IN="$1"; OUT="$2"
HERE=$(cd "$(dirname "$0")" && pwd); LOGO="$HERE/../assets/cake_n_crumble_logo.png"
W=$(mktemp -d)
ffmpeg -v error -y -sseof -0.1 -i "$IN" -frames:v 1 "$W/last.png"
python3 -I "$HERE/endcard.py" "$W/last.png" "$LOGO" "$W/end.png"
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
X=0.5; EC=3
OFF=$(python3 -c "print($D-$X)"); TOT=$(python3 -c "print($D-$X+$EC)"); AF=$(python3 -c "print($D-0.9)")
ffmpeg -v error -y -i "$IN" -loop 1 -t $EC -framerate 24 -i "$W/end.png" -loop 1 -i "$LOGO" -filter_complex "
[2:v]scale=120:-1,format=rgba[lg];
[0:v]fps=24,setsar=1[m0];
[m0][lg]overlay=28:H-h-74:shortest=1,
drawtext=fontfile=/usr/share/fonts/opentype/inter/Inter-Bold.otf:text='@cake_n_crumble_03':fontsize=32:fontcolor=white@0.9:borderw=2:bordercolor=black@0.55:x=30:y=h-62,format=yuv420p[m];
[1:v]fps=24,scale=1080:1920,setsar=1,format=yuv420p[e];
[m][e]xfade=transition=fade:duration=$X:offset=$OFF[v];
[0:a]afade=t=out:st=$AF:d=0.9,apad[a]" \
  -map "[v]" -map "[a]" -t $TOT -c:v libx264 -preset medium -crf 18 -c:a aac -b:a 192k -movflags +faststart "$OUT"
rm -rf "$W"; echo "done: $OUT"
