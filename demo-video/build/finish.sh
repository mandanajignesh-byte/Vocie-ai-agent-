#!/bin/bash
# full render in 4 parallel segments, then join + mux voiceover + make the 1080p version
set -e
cd "$(dirname "$0")"
TAG=${1:-v2}; SEG=../out/seg_$TAG; rm -rf $SEG; mkdir -p $SEG
N=$(python3 -c "import json;print(round(json.load(open('../out/timeline.json'))['duration']*30))")
Q=$(( (N / 4 / 60 + 1) * 60 ))
for i in 0 1 2 3; do
  A=$(( i * Q )); B=$(( (i + 1) * Q )); [ $B -gt $N ] && B=$N
  node render.js $A $B $SEG/s$i.mp4 2 > $SEG/s$i.log 2>&1 &
  echo "file 's$i.mp4'" >> $SEG/list.txt
done
wait
tail -q -n 1 $SEG/s*.log
ffmpeg -v error -y -f concat -safe 0 -i $SEG/list.txt -i ../out/vo.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -ar 48000 -movflags +faststart ../out/Chat360_Insurance_Demo_${TAG}_4K.mp4
ffmpeg -v error -y -i ../out/Chat360_Insurance_Demo_${TAG}_4K.mp4 -vf "scale=1920:1080:flags=lanczos+accurate_rnd" -c:v libx264 -preset slow -crf 16 -profile:v high -level 4.2 -pix_fmt yuv420p -g 60 -bf 2 -maxrate 16M -bufsize 32M -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv -c:a copy -movflags +faststart ../out/Chat360_Insurance_Demo_${TAG}_1080p.mp4
ls -la ../out/*${TAG}*.mp4
echo ALLDONE
