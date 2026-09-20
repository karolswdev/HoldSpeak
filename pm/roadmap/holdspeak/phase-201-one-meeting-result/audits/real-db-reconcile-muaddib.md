# Real-DB reconcile probe — Muad'Dib, 2026-09-19 19:06

Lane A counsel condition 4 (checks/lane-a-built-muaddib.md): the two new
`intel_jobs` columns reconciled against a COPY of the owner's real DB
(`~/.local/share/holdspeak/holdspeak.db`, 3.4 MB, 249 tables), opened
with the branch's `Database` under an isolated HOME. The copy was deleted
after the probe; the real file was never opened.

```
Schema shape changed; backed up to <copy>.20260919-190638.bak before applying backfills
intel_jobs columns added: ['planned_route_json', 'run_receipt_json']
intel_jobs columns removed: []
row-count changes: none
tables before/after: 249 249
integrity: ok
```

Additive only; no row moved. Cited by story 07's evidence.
