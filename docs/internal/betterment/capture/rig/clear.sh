#!/bin/sh
# clear.sh <port>: close every hub window, and drop browser workspace caches
P=$1; B=http://127.0.0.1:$P; H="Authorization: Bearer graph-walk-token"
for id in $(curl -s -H "$H" $B/api/desk/windows | python3 -c "import json,sys,urllib.parse; [print(urllib.parse.quote(w['id'],safe='')) for w in json.load(sys.stdin).get('windows',[])]"); do curl -s -o /dev/null -X POST -H "$H" -H 'content-type: application/json' -d '{}' $B/api/desk/windows/$id/close; done
rm -rf "$(dirname $0)"/profile-$P-*
