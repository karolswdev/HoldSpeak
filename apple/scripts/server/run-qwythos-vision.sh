#!/bin/bash
# Qwythos-9B + vision (mmproj) on .43:8080 — general chat + image understanding (for sketch→Mermaid).
M=/home/karol/dev/llama.cpp/models
exec /home/karol/dev/llama.cpp/build/bin/llama-server \
  -m "$M/Qwythos-9B-Claude-Mythos-5-1M-Q6_K.gguf" \
  --mmproj "$M/mmproj-Qwythos-9B-Claude-Mythos-5-1M-f16.gguf" \
  --host 0.0.0.0 --port 8080 -c 16384 -ngl 99 -fa on \
  --cache-type-k q4_0 --cache-type-v q4_0 -np 1 --jinja --reasoning off \
  --temp 0.7 --top-p 0.95 --top-k 20
