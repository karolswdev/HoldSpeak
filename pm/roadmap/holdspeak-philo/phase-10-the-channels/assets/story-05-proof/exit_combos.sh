#!/bin/zsh
# PHILO-10-05 (the Phase 9 lesson, Codex Astra r2 on #688): every wrapper
# propagates each status. Each variant is the script's own text with its two
# commands replaced by `(exit A)` / `(exit B)`, their pipes kept, run for the
# four combinations. Wanted: exit 0 only when both are 0.
#   fences.sh:    A = the pytest fences, B = mutations.py
#   rig_phase.sh: A = rig_run.py, B = retain.py (the build and the copy of the export stubbed out)
cd ${0:A:h}
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT INT TERM
bad=0
variant() {  # <script> <A> <B> <out>
  python3 - "$@" <<'PY'
import re, sys
src, a, b, out = sys.argv[1:]
s = open(src).read()
if src.endswith("fences.sh"):
    s, n1 = re.subn(r'HOME=\$H \.venv/bin/python -m pytest.*?2>&1 \| tail -3', f'(echo fences; exit {a}) 2>&1 | tail -3', s, flags=re.S)
    s, n2 = re.subn(r'\.venv/bin/python \S*mutations\.py \| cut -c1-220', f'(echo mutations; exit {b}) | cut -c1-220', s)
else:
    s, n0 = re.subn(r'\(cd web && npm run build 2>&1 \| tail -1\)', 'true', s)
    s, n1 = re.subn(r'HOME=\$H PLAYWRIGHT.*?\| cut -c1-240', f'(echo rig; exit {a}) | cut -c1-240', s, flags=re.S)
    s, n2 = re.subn(r'\.venv/bin/python \$HERE/retain\.py [^\n]*', f'(echo retain; exit {b})', s)
assert n1 == 1 and n2 == 1 and "-m pytest" not in s and "/rig_run.py" not in s and "/retain.py" not in s, (src, n1, n2)
open(out, "w").write(s)
PY
}
for script in fences.sh rig_phase.sh; do
  for a in 0 1; do for b in 0 1; do
    variant $PWD/$script $a $b $tmp/v.sh
    zsh $tmp/v.sh x 1 >/dev/null 2>&1; got=$?
    want=$(( a != 0 || b != 0 ))
    verdict=ok; (( (got != 0) != want )) && { verdict=WRONG; bad=$((bad + 1)); }
    echo "$script A=$a B=$b -> exit $got (wanted $([[ $want == 1 ]] && echo nonzero || echo 0)): $verdict"
  done; done
done
echo "$bad wrong"
exit $(( bad > 0 ))
