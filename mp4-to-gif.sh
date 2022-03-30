#!/bin/bash

if [[ $# -ne 1 ]]; then
echo "usage: $0 INPUT.mp4"
exit 1
fi

name=$(basename "$1" .mp4)
# https://superuser.com/questions/556029/how-do-i-convert-a-video-to-gif-using-ffmpeg-with-reasonable-quality
ffmpeg -r 400 -i $1 -an -vf "fps=20,scale=600:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" -loop 0 $name.gif

