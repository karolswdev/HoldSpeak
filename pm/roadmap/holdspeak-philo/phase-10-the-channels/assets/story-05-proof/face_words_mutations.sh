#!/bin/zsh
# PHILO-10-05 (Muad'Dib's ruling on #698): the face-word fence turns red on
# (m1) a word dropped from the FAILED table, (m2) a new ChannelRefused code in a
# service with no word, (m3) a new Outcome code passed through a new variable;
# Codex Astra r1 on #698 finding 1, its three escapes: (m4) a formatted f-string
# code, (m5) a .format() code, (m6) a formatted code through the existing
# `reason` flow of the Atlassian dispatch.
# Each file is restored byte for byte. Exit 1 if a mutation stays green or the
# baseline is red.
cd ${0:A:h}/../../../../../..
H=$(mktemp -d); T=$(mktemp -d); trap 'cp $T/channels.ts web/src/features/channels/channels.ts; cp $T/channel_service.py holdspeak/services/channel_service.py; cp $T/channel_cli.py holdspeak/services/channel_cli.py; rm -rf "$H" "$T"' EXIT INT TERM
cp web/src/features/channels/channels.ts holdspeak/services/channel_service.py holdspeak/services/channel_cli.py $T/
fence() { HOME=$H .venv/bin/python -m pytest -q -p no:cacheprovider --basetemp=$H/pt tests/unit/test_philo10_face_words.py 2>&1 | tail -1; return ${pipestatus[1]}; }
fence; base=$?; echo "baseline exit $base"
missed=0
sed -i '' '/  github_target_not_found: "ISSUE NOT FOUND",/d' web/src/features/channels/channels.ts
fence; (( $? == 0 )) && { echo "m1 MISSED"; missed=$((missed+1)); } || echo "m1 RED (a FAILED word dropped)"
cp $T/channels.ts web/src/features/channels/channels.ts
printf '\ndef _m2():\n    raise ChannelRefused("brand_new_refusal", "x")\n' >> holdspeak/services/channel_service.py
fence; (( $? == 0 )) && { echo "m2 MISSED"; missed=$((missed+1)); } || echo "m2 RED (a new refusal code with no word)"
cp $T/channel_service.py holdspeak/services/channel_service.py
printf '\ndef _m3(code):\n    return Outcome("failed", code)\n' >> holdspeak/services/channel_service.py
fence; (( $? == 0 )) && { echo "m3 MISSED"; missed=$((missed+1)); } || echo "m3 RED (a code through a new variable site)"
cp $T/channel_service.py holdspeak/services/channel_service.py
printf '\ndef _m4(kind):\n    raise ChannelRefused(f"destination_{kind}_gone", "x")\n' >> holdspeak/services/channel_service.py
fence; (( $? == 0 )) && { echo "m4 MISSED"; missed=$((missed+1)); } || echo "m4 RED (an f-string code outside the allow-list)"
cp $T/channel_service.py holdspeak/services/channel_service.py
printf '\ndef _m5(kind):\n    return Outcome("failed", "{}_refused".format(kind))\n' >> holdspeak/services/channel_service.py
fence; (( $? == 0 )) && { echo "m5 MISSED"; missed=$((missed+1)); } || echo "m5 RED (a .format() code)"
cp $T/channel_service.py holdspeak/services/channel_service.py
python3 - <<'PYM'
from pathlib import Path
p = Path("holdspeak/services/channel_cli.py"); s = p.read_text()
a = 'else "atlassian_switch_failed")'
assert s.count(a) == 1
p.write_text(s.replace(a, 'else f"atlassian_switch_failed_{code}")'))
PYM
fence; (( $? == 0 )) && { echo "m6 MISSED"; missed=$((missed+1)); } || echo "m6 RED (a formatted code through the reason flow)"
cp $T/channel_cli.py holdspeak/services/channel_cli.py
echo "6 mutations: $((6-missed)) red, $missed missed"
exit $(( base != 0 || missed > 0 ))
