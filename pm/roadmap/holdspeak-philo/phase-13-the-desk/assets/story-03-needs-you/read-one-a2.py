import json, pathlib, sys
root=pathlib.Path('.tmp/graph-walk/philo-13-03')/sys.argv[1]
p=next(root.glob('*/observation.json'))
d=json.loads(p.read_text())
prov=d['provenance']
assert d.get('complete'), 'Still running: do not read as final'
print(json.dumps({'path':str(p),'verdict':d['verdict'],'notes':d['notes'],
'steps':[{k:s[k] for k in ('kind','action','selector','name','done','status','holds','shot','response','adapter','summary') if k in s} for s in d['setup']],
'error':d.get('setup_error'),'trigger':d.get('trigger'),
'after':{k:d.get('after',{}).get(k) for k in ('text','rect','visible')} if d.get('after') else None,
'hit_test':{k:((d.get('after') or {}).get('hit_test') or {}).get(k) for k in ('in_viewport','all_owned')},
'outcome':d.get('terminal_outcome'),'touch':prov.get('touch_mode'), 'tmux':prov.get('tmux_isolation'),
'images':[str(x.resolve()) for x in p.parent.glob('*.png')]},indent=2))
