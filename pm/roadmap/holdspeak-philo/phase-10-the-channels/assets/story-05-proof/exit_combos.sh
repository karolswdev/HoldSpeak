#!/bin/zsh
# PHILO-10-05 (the Phase 9 lesson, Codex Astra r2 on #688; Codex Astra r1 on #698
# finding 2): every wrapper propagates each status, and a failed build stops the
# walk. Each variant is the script's own text with its commands replaced by
# stubs `(exit N)` (their pipes kept); the rig and copier stubs also leave a
# marker, so a variant proves whether they RAN.
#   fences.sh:    A = the pytest fences, B = mutations.py      -> exit 0 only when both 0
#   rig_phase.sh: BUILD x RIG x RETAIN, on both branches (ROOT unset: this tree;
#                 ROOT set: an export) -> a failed build exits nonzero and neither
#                 the rig nor the copier runs; else exit 0 only when all are 0
cd ${0:A:h}
REPO=${0:A:h}/../../../../../..
REPO=${REPO:A}
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT INT TERM
bad=0
variant() {  # <script> <out> <A> <B> [<BUILD>]
  python3 - "$@" "$tmp/ran" "$REPO" <<'PY'
import re, sys
src, out, a, b, build, ran, repo = (sys.argv[1:] + [None])[:5] + sys.argv[-2:] if len(sys.argv) == 8 else sys.argv[1:5] + ["0"] + sys.argv[-2:]
s = open(src).read()
if src.endswith("fences.sh"):
    s, n1 = re.subn(r'HOME=\$H \.venv/bin/python -m pytest.*?2>&1 \| tail -3', f'(echo fences; exit {a}) 2>&1 | tail -3', s, flags=re.S)
    s, n2 = re.subn(r'\.venv/bin/python \S*mutations\.py \| cut -c1-220', f'(echo mutations; exit {b}) | cut -c1-220', s)
    n0 = 2
else:
    s, n0 = re.subn(r'\(cd (\$ROOT/)?web && npm run build 2>&1', f'(cd . && (echo build; exit {build}) 2>&1', s)
    s, n1 = re.subn(r'HOME=\$H PLAYWRIGHT.*?\| cut -c1-240', f'(echo rig >> {ran}; exit {a}) | cut -c1-240', s, flags=re.S)
    s, n2 = re.subn(r'\.venv/bin/python \$HERE/retain\.py [^\n]*', f'(echo retain >> {ran}; exit {b})', s)
    s, n3 = re.subn(r'^cd \$\{0:A:h\}/[^\n]*', f'cd {repo}', s, flags=re.M)
    assert n3 == 1
assert n0 == 2 and n1 == 1 and n2 == 1 and "-m pytest" not in s and "/rig_run.py" not in s and "/retain.py" not in s, (src, n0, n1, n2)
open(out, "w").write(s)
PY
}
for a in 0 1; do for b in 0 1; do
  variant $PWD/fences.sh $tmp/v.sh $a $b
  zsh $tmp/v.sh >/dev/null 2>&1; got=$?
  want=$(( a != 0 || b != 0 ))
  verdict=ok; (( (got != 0) != want )) && { verdict=WRONG; bad=$((bad + 1)); }
  echo "fences.sh A=$a B=$b -> exit $got (wanted $([[ $want == 1 ]] && echo nonzero || echo 0)): $verdict"
done; done
mkdir -p $tmp/export/scripts $tmp/export/web
for branch in tree export; do
  for build in 0 7; do for a in 0 1; do for b in 0 1; do
    rm -f $tmp/ran
    variant $PWD/rig_phase.sh $tmp/v.sh $a $b $build
    if [[ $branch == export ]]; then ROOT=$tmp/export zsh $tmp/v.sh x 1 >/dev/null 2>&1; else zsh $tmp/v.sh x 1 >/dev/null 2>&1; fi
    got=$?
    ran=$(cat $tmp/ran 2>/dev/null | tr '\n' ' ')
    if (( build != 0 )); then
      verdict=ok; { (( got == 0 )) || [[ -n $ran ]]; } && { verdict=WRONG; bad=$((bad + 1)); }
      echo "rig_phase.sh [$branch] BUILD=$build RIG=$a RETAIN=$b -> exit $got, ran: ${ran:-nothing} (wanted nonzero, nothing ran): $verdict"
    else
      want=$(( a != 0 || b != 0 ))
      verdict=ok; (( (got != 0) != want )) && { verdict=WRONG; bad=$((bad + 1)); }
      echo "rig_phase.sh [$branch] BUILD=0 RIG=$a RETAIN=$b -> exit $got, ran: $ran(wanted $([[ $want == 1 ]] && echo nonzero || echo 0)): $verdict"
    fi
  done; done; done
done
# Before (813e6684, Codex's probe): the same failed build walked and retained, exit 0.
(cd $REPO && git show 813e6684:pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-proof/rig_phase.sh) > $tmp/before.sh
rm -f $tmp/ran; variant $tmp/before.sh $tmp/v.sh 0 0 7 && zsh $tmp/v.sh x 1 >/dev/null 2>&1
echo "before (813e6684) [tree] BUILD=7 -> exit $?, ran: $(cat $tmp/ran 2>/dev/null | tr '\n' ' ')(the defect: shown, not counted)"
echo "$bad wrong"
exit $(( bad > 0 ))
