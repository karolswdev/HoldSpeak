#!/bin/zsh
# PHILO-9-05 (Codex Astra r2 condition 1): fences.sh's exit status for the four
# combinations of (fences pass/fail) x (mutations pass/fail), on the round-two
# script (67ce9256, `mrc=$?` read cut's status) and on this one. Each variant is
# the script's own text with the two commands replaced by `(exit A)` and
# `(exit B)`, their pipes kept. Wanted: exit 0 only when both pass.
cd ${0:A:h}/../../../../../..
F=pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/fences.sh
tmp=$(mktemp -d)
bad=0
variant() {  # <source text file> <A> <B> <out>
  python3 - "$1" "$2" "$3" "$4" <<'PY'
import re, sys
src, a, b, out = sys.argv[1:]
s = open(src).read()
s = re.sub(r'HOME=\$\(mktemp -d\) \.venv/bin/python -m pytest.*?2>&1 \| tail -3', f'(echo fences; exit {a}) 2>&1 | tail -3', s, flags=re.S)
s = re.sub(r'\.venv/bin/python \S*mutations\.py \| cut -c1-220', f'(echo mutations; exit {b}) | cut -c1-220', s)
assert s.count('exit ' + a) >= 1 and 'mutations.py' not in s and 'pytest' not in s, s
open(out, 'w').write(s)
PY
}
git show 67ce9256:$F > $tmp/before.sh
for label in before after; do
  src=$tmp/before.sh; [[ $label == after ]] && src=$F
  for a in 0 1; do for b in 0 1; do
    variant $src $a $b $tmp/$label-$a$b.sh
    zsh $tmp/$label-$a$b.sh >/dev/null 2>&1; got=$?
    want=$(( a != 0 || b != 0 ))
    verdict=ok; (( (got != 0) != want )) && verdict=WRONG
    [[ $label == after && $verdict == WRONG ]] && bad=$((bad + 1))
    echo "$label fences=$a mutations=$b -> exit $got (wanted $([[ $want == 1 ]] && echo nonzero || echo 0)): $verdict"
  done; done
done
echo "after: $bad wrong"
exit $(( bad > 0 ))
