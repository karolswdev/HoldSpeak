#!/bin/zsh
# PHILO-9 close (Codex Astra r1 on #689 finding 3): preserve.sh's exit status for
# the four combinations of (pytest exit 0/1) x (its output has a summary line
# grep keeps / has none), on the story 03 script as merged (read from
# 79fdee3c, the #686 merge) and on this one. Each variant is the script's own
# text with the pytest command replaced by `(echo <line>; exit A)`, its pipe kept.
# Wanted: the exit equals pytest's exit in every combination.
cd ${0:A:h}/../../../../../..
F=pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/preserve.sh
tmp=$(mktemp -d)
bad=0
variant() {  # <source> <A> <line> <out>
  python3 - "$1" "$2" "$3" "$4" <<'PY'
import re, sys
src, a, line, out = sys.argv[1:]
s = open(src).read()
s = re.sub(r'HOME=\$\(mktemp -d\).*?2>&1 \\\n', f'(echo "{line}"; exit {a}) 2>&1 \\\n', s, flags=re.S)
assert '.venv/bin/python -m pytest' not in s and f'exit {a}) 2>&1' in s, s
open(out, 'w').write(s)
PY
}
git show 79fdee3c:$F > $tmp/before.sh
for label in before after; do
  src=$tmp/before.sh; [[ $label == after ]] && src=$F
  for a in 0 1; do for line in "3 passed in 1.00s" "no summary"; do
    variant $src $a "$line" $tmp/v.sh
    zsh $tmp/v.sh >/dev/null 2>&1; got=$?
    verdict=ok; (( got != a )) && verdict=WRONG
    [[ $label == after && $verdict == WRONG ]] && bad=$((bad + 1))
    echo "$label pytest=$a output='$line' -> exit $got (wanted $a): $verdict"
  done; done
done
echo "after: $bad wrong"
exit $(( bad > 0 ))
