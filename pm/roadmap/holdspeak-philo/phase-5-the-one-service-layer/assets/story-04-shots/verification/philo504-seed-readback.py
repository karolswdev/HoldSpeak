from pathlib import Path
import json,sqlite3
base=Path('pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots')
r=base/'final/20260925T001407Z-his-words-real'
uri='file:'+str((r/'db-proof.sqlite').resolve())+'?mode=ro&immutable=1'
lines=['First-open seed/onboarding readback (immutable final DB).','Transcript indices are zero-based, as in the Codex-window audit.']
rows=[json.loads(x) for x in (r/'rehearsal-transcript.jsonl').read_text().splitlines()]
for i in [43,62]: lines.append(f'row {i}: {json.dumps(rows[i],sort_keys=True)}')
with sqlite3.connect(uri,uri=True) as db:
 db.row_factory=sqlite3.Row
 for table in ['directories','notes','kbs','recipes']:
  cols=[x['name'] for x in db.execute(f'PRAGMA table_info({table})')]
  selected=[x for x in ['id','created_at','updated_at','last_modified','kind'] if x in cols]
  rs=[dict(x) for x in db.execute(f"SELECT {','.join(selected)} FROM {table} WHERE id LIKE 'hs-seed-%' ORDER BY id")]
  lines.append(table+': '+json.dumps(rs,sort_keys=True))
 for table in ['directory_memberships','knowledge_memberships','onboarding_state']:
  rs=[dict(x) for x in db.execute(f'SELECT * FROM {table}')]
  lines.append(table+': '+json.dumps(rs,sort_keys=True))
 lines.append('notes_memory_fts seed rows: '+str(db.execute("SELECT count(*) FROM notes_memory_fts WHERE source_id LIKE 'hs-seed-%'").fetchone()[0]))
lines+=['Source: FirstWords.tsx:213-216 calls both routes on first-open handoff.','Source: db/seed.py:106-230,269-313 writes manifest directories, notes, recipes, kbs and filing; thread_modes.py:171,344 ensures mode recipes and guardrail notes.','Source: db/primitives.py:384-437 maintains knowledge_memberships; schema.py:1312-1328 maintains notes_memory_fts and its FTS backing tables.','Source: services/setup_service.py:40-43 repeats additive apply_seed then writes onboarding_state.','The final snapshot proves rows exist; it is not a per-statement SQL trace or a before/after allocation between the two calls.']
text='\n'.join(lines)+'\n';(base/'verification/first-open-seed-readback.txt').write_text(text);print(text)
