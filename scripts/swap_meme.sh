#!/usr/bin/env bash
# Usage: swap_meme.sh <source_video> <enthiran_clip> <output> [clip_start] [clip_dur]
# Replaces the Thiruvilaiyadal meme (26.0s-30.2s) with the given clip, styled like the original card.
set -euo pipefail
SRC="$1"; CLIP="$2"; OUT="$3"; CS="${4:-0}"; CD="${5:-}"
A=${A:-26.0}; B=${B:-30.2}
W=$(mktemp -d)
FB=/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf
FM=/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf
[ -f "$FM" ] || FM=/usr/share/fonts/opentype/inter/Inter-Bold.otf
DUR_ARGS=(); [ -n "$CD" ] && DUR_ARGS=(-t "$CD")

# header pill ("New ChatGPT mode") lifted from the original card
ffmpeg -v error -y -ss 27 -i "$SRC" -frames:v 1 -vf "crop=794:110:143:268,format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(gt(hypot(max(0,max(18-X,X-(W-19))),max(0,max(18-Y,Y-(H-19)))),18),0,255)'" "$W/pill.png"

cat > "$W/cap.txt" <<'EOF'
"Manushanga seiyuradhaiyum seiyum,
avangalala mudiyaadhadhaiyum seiyum!"
EOF

ffmpeg -v error -y -ss "$CS" "${DUR_ARGS[@]}" -i "$CLIP" -i "$W/pill.png" -filter_complex "
[0:v]fps=24,crop=iw-8:ih-8,split[a][b];
[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:2,eq=brightness=-0.25:saturation=0.8[bg];
[b]scale=1080:-2[fg];
[bg][fg]overlay=0:(528+(784-h)/2)[v1];
[v1][1:v]overlay=143:268[v2];
[v2]drawtext=fontfile=$FM:text='ENDHIRAN (2010) · Rajinikanth':fontsize=26:fontcolor=white:box=1:boxcolor=black@0.75:boxborderw=12:x=52:y=1205,
drawtext=fontfile=$FB:textfile=$W/cap.txt:fontsize=44:fontcolor=white:line_spacing=14:text_align=center:x=(w-tw)/2:y=1285:shadowcolor=black@0.6:shadowx=2:shadowy=2,
drawbox=x=16:y=596:w=448:h=64:color=0xC6F35E@1:t=fill,drawtext=fontfile=$FB:text='CHITTI = NEW CHATGPT':fontsize=32:fontcolor=0x111111:x=34:y=611,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='▼':fontsize=46:fontcolor=0xC6F35E:x=48:y=652:shadowcolor=black@0.6:shadowx=2:shadowy=2,drawbox=x=2:y=712:w=150:h=444:color=0xC6F35E@1:t=5,
fade=t=in:st=0:d=0.15,format=yuv420p[v];[0:a]volume=3dB,afade=t=in:d=0.05,areverse,afade=t=in:d=0.12,areverse[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset medium -crf 18 -c:a aac -ar 48000 -ac 2 -b:a 192k "$W/mid.mp4"

# head and tail of the original, re-encoded so the concat is frame-accurate
ffmpeg -v error -y -i "$SRC" -t $A -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -ar 48000 -ac 2 -b:a 192k "$W/head.mp4"
ffmpeg -v error -y -ss $B -i "$SRC" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -ar 48000 -ac 2 -b:a 192k "$W/tail.mp4"

ffmpeg -v error -y -i "$W/head.mp4" -i "$W/mid.mp4" -i "$W/tail.mp4" -filter_complex \
  "[0:v]setsar=1[h];[1:v]setsar=1[m];[2:v]setsar=1[t];[h][0:a][m][1:a][t][2:a]concat=n=3:v=1:a=1[v][a]" -map "[v]" -map "[a]" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart "$OUT"
rm -rf "$W"
echo "done: $OUT"
