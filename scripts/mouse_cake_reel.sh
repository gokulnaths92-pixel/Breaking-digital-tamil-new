#!/usr/bin/env bash
# Usage: mouse_cake_reel.sh <mouse_reel.mp4> <cake_video.mp4> <output.mp4>
# Keeps the hamster meme, caption and audio of the mouse reel; replaces the brownie-tub
# footage underneath with a montage of the Jack Daniel's cake video.
set -euo pipefail
MOUSE="$1"; CAKE="$2"; OUT="$3"
W=$(mktemp -d)
FS=/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf
printf 'Ithu vaangi kudu ilana\nsutruven' > "$W/cap.txt"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$MOUSE")
ffmpeg -v error -y -i "$CAKE" -i "$MOUSE" -filter_complex "
[0:v]fps=30,scale=720:1280,setsar=1,split=4[c1][c2][c3][c4];
[c1]trim=0:2,setpts=PTS-STARTPTS[s1];
[c2]trim=2:4,setpts=PTS-STARTPTS[s2];
[c3]trim=8.5:11.5,setpts=PTS-STARTPTS[s3];
[c4]trim=19:23,setpts=PTS-STARTPTS[s4];
[s1][s2][s3][s4]concat=n=4:v=1:a=0,trim=0:$DUR,setpts=PTS-STARTPTS[bg];
[1:v]fps=30,crop=485:351:117:24[ham];
[bg][ham]overlay=117:24:shortest=1[v1];
[v1]drawtext=fontfile=$FS:textfile=$W/cap.txt:fontsize=44:fontcolor=black:borderw=3:bordercolor=white:line_spacing=6:text_align=center:x=(w-tw)/2:y=398,format=yuv420p[v]" \
  -map "[v]" -map 1:a -t "$DUR" -c:v libx264 -preset medium -crf 18 -c:a aac -b:a 192k -movflags +faststart "$OUT"
rm -rf "$W"
echo "done: $OUT"
