import json,re,sys,glob
root='docs/internal/philo/graph/'
ids=set()
for f in ['static-muaddib','static-astra','live-muaddib','live-astra']:
    g=json.load(open(root+f+'.json')); ids|={x['id'] for x in g.get('findings',[])}
r=json.load(open(root+'council-resolutions.json'))
covered=set(); [covered.update(x.get('findings',[])) for x in r['resolutions']]
missing=sorted(ids-covered)
c=open(root+'COUNCIL.md').read()
first_h2=re.search(r'^## (.+)$',c,re.M).group(1)
p3=len(glob.glob('pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/story-*.md'))
print(f"sealed finding ids: {len(ids)}; covered by resolutions: {len(ids-set(missing))}; missing: {missing}")
print(f"COUNCIL.md first section: {first_h2!r}")
print(f"resolutions with disposition_final: {sum(1 for x in r['resolutions'] if x.get('disposition_final'))}/{len(r['resolutions'])}; open dissents: {r.get('open_dissents')}")
print(f"phase 3 stories: {p3} (cap 10)")
ok = not missing and first_h2.startswith('1. The decision page') and p3<=10 and all(x.get('disposition_final') for x in r['resolutions'])
print("COUNCIL CHECK:", "OK" if ok else "FAIL"); sys.exit(0 if ok else 1)
