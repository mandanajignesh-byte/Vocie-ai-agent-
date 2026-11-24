#!/bin/bash
# usage: ./finish.sh <tag> [1080|4k]   — renders in 4 parallel segments, joins them and adds the voiceover.
# Default is a single 1080p file; pass 4k only when a 4K master is wanted (about 4x slower).
set -e
cd "$(dirname "$0")"
TAG=${1:-draft}; RES=${2:-1080}
if [ "$RES" = "4k" ]; then DSF=2; NAME=4K; else DSF=1; NAME=1080p; fi
SEG=../out/seg_${TAG}_$NAME; rm -rf $SEG; mkdir -p $SEG
N=$(python3 -c "import json;print(round(json.load(open('../out/timeline.json'))['duration']*30))")
Q=$(( (N / 4 / 60 + 1) * 60 ))
for i in 0 1 2 3; do
  A=$(( i * Q )); B=$(( (i + 1) * Q )); [ $B -gt $N ] && B=$N
  node render.js $A $B $SEG/s$i.mp4 $DSF > $SEG/s$i.log 2>&1 &
  echo "file 's$i.mp4'" >> $SEG/list.txt
done
wait
tail -q -n 1 $SEG/s*.log
ffmpeg -v error -y -f concat -safe 0 -i $SEG/list.txt -i ../out/vo.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -ar 48000 -movflags +faststart ../out/Chat360_Insurance_Demo_${TAG}_$NAME.mp4
ls -la ../out/Chat360_Insurance_Demo_${TAG}_$NAME.mp4
echo ALLDONE
