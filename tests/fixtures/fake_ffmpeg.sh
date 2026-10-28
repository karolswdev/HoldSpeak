#!/bin/sh
# A fake ffmpeg for tests/unit/test_recordings.py: no codec runs.
#   encode (-progress pipe:1): print four progress blocks, copy the -i input
#     to the last argument;
#   poster (no -progress): write a few bytes to the last argument.
# FAKE_FFMPEG_FAIL=1 makes it fail like a broken input.
input=""
progress=0
prev=""
last=""
for arg in "$@"; do
  [ "$prev" = "-i" ] && input="$arg"
  [ "$arg" = "-progress" ] && progress=1
  prev="$arg"
  last="$arg"
done
if [ "${FAKE_FFMPEG_FAIL:-0}" = "1" ]; then
  echo "in.webm: Invalid data found when processing input" >&2
  exit 1
fi
if [ "$progress" = "1" ]; then
  for us in 1000000 2500000 4000000 5000000; do
    echo "frame=1"
    echo "out_time_us=$us"
    echo "progress=continue"
  done
  echo "progress=end"
  cp "$input" "$last"
else
  printf 'JPEG' > "$last"
fi
exit 0
