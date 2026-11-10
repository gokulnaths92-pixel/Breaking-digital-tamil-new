#!/usr/bin/env bash
# Usage: swap_old_meme.sh <source_video> <meme_clip> <output> [clip_start] [clip_dur]
# Replaces the Marudhamalai/Vadivelu "Old ChatGPT mode" card (8.542s-13.75s) with the given clip
# and tags the speaking cop as OLD CHATGPT.
set -euo pipefail
SRC="$1"; CLIP="$2"; OUT="$3"; CS="${4:-0}"; CD="${5:-3.4}"
A=${A:-8.542}; B=${B:-13.75}
W=$(mktemp -d)
FB=/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf
FA=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
Y=0xFFD43B

# yellow "Old ChatGPT mode" pill lifted from the original card, rounded corners
ffmpeg -v error -y -ss 10 -i "$SRC" -frames:v 1 -vf "crop=760:108:160:435,format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(gt(hypot(max(0,max(18-X,X-(W-19))),max(0,max(18-Y,Y-(H-19)))),18),0,255)'" "$W/pill.png"

# clip: drop the player controls (bottom) and frame the two cops; hide the play icon of the screen recording
ffmpeg -v error -y -ss "$CS" -t "$CD" -i "$CLIP" -i "$W/pill.png" -filter_complex "
[0:v]fps=24,delogo=x=225:y=210:w=95:h=95:enable='lt(t,0.8)',crop=542:380:0:20,split[a][b];
[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:2,eq=brightness=-0.25:saturation=0.8[bg];
[b]scale=1080:-2[fg];
[bg][fg]overlay=0:600[v1];
[v1][1:v]overlay=160:435[v2];
[v2]drawbox=x=506:y=790:w=400:h=68:color=$Y@1:t=fill,
drawtext=fontfile=$FB:text='OLD CHATGPT':fontsize=36:fontcolor=0x111111:x=506+(400-tw)/2:y=806,
drawtext=fontfile=$FA:text='◀':fontsize=50:fontcolor=$Y:x=458:y=794:shadowcolor=black@0.6:shadowx=2:shadowy=2,
drawtext=fontfile=$FB:text='\"Correct! Super! Neenga dhaan best!\"':fontsize=44:fontcolor=white:x=(w-tw)/2:y=1380:shadowcolor=black@0.6:shadowx=2:shadowy=2,
fade=t=in:st=0:d=0.15,format=yuv420p[v];
[0:a]volume=3dB,afade=t=in:d=0.05,areverse,afade=t=in:d=0.12,areverse[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset medium -crf 18 -c:a aac -ar 48000 -ac 2 -b:a 192k "$W/mid.mp4"

ffmpeg -v error -y -i "$SRC" -t $A -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -ar 48000 -ac 2 -b:a 192k "$W/head.mp4"
ffmpeg -v error -y -ss $B -i "$SRC" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -ar 48000 -ac 2 -b:a 192k "$W/tail.mp4"
ffmpeg -v error -y -i "$W/head.mp4" -i "$W/mid.mp4" -i "$W/tail.mp4" -filter_complex \
  "[0:v]setsar=1[h];[1:v]setsar=1[m];[2:v]setsar=1[t];[h][0:a][m][1:a][t][2:a]concat=n=3:v=1:a=1[v][a]" -map "[v]" -map "[a]" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart "$OUT"
rm -rf "$W"
echo "done: $OUT"
