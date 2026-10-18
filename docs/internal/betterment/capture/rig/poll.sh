#!/bin/sh
# poll.sh <port> <seconds> : print the latency of GET / every 0.5 s
end=$(( $(date +%s) + $2 ))
while [ $(date +%s) -lt $end ]; do
  printf "%s " "$(date +%H:%M:%S)"; curl -s -m 60 -o /dev/null -w "%{http_code} %{time_total}\n" "http://127.0.0.1:$1/?token=graph-walk-token"; sleep 0.5
done
