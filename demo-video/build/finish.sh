#!/bin/bash
# waits for running jobs, renders remaining segments, then joins + muxes + makes the 1080p version
set -e
cd "$(dirname "$0")"
SEG=../out/seg
while pgrep -f "render.js (0|1860) " >/dev/null; do sleep 3; done
node render.js 3720 5550 $SEG/s3.mp4 2 > $SEG/s3.log 2>&1 &
node render.js 6300 8005 $SEG/s5.mp4 2 > $SEG/s5.log 2>&1 &
while pgrep -f avatar_sr.py >/dev/null; do sleep 3; done
echo "avatar frames: $(ls ../sr/frames | wc -l)"
node render.js 5550 6300 $SEG/s4.mp4 2 > $SEG/s4.log 2>&1
wait
for i in 1 2 3 4 5; do tail -n 1 $SEG/s$i.log; echo "file 's$i.mp4'" ; done | grep -v "^file" ; printf "file 's1.mp4'\nfile 's2.mp4'\nfile 's3.mp4'\nfile 's4.mp4'\nfile 's5.mp4'\n" > $SEG/list.txt
ffmpeg -v error -y -f concat -safe 0 -i $SEG/list.txt -i ../out/vo.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -ar 48000 -movflags +faststart ../out/Chat360_Insurance_Demo_4K.mp4
ffmpeg -v error -y -i ../out/Chat360_Insurance_Demo_4K.mp4 -vf "scale=1920:1080:flags=lanczos+accurate_rnd" -c:v libx264 -preset slow -crf 16 -profile:v high -level 4.2 -pix_fmt yuv420p -g 60 -bf 2 -maxrate 16M -bufsize 32M -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv -c:a copy -movflags +faststart ../out/Chat360_Insurance_Demo_1080p.mp4
ls -la ../out/*.mp4
echo ALLDONE
