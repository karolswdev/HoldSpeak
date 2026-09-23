# Evidence — PHILO-2-03: The static pass, Astra

This seals source inspection only. The worktree is
`/Users/karol/dev/tools/wt-philo-2-03`; branch
`audit/philo-2-03-static-astra`; inspected source commit
`c42963bcd154b7d199de501370f1643e14a3921d`.

Artifacts: `docs/internal/philo/graph/static-astra.json` and the adjacent
§9 report `static-astra.md`. The supplied untracked static-pass lane brief
is a declared dirty input; it is hashed in the graph and left unmodified and
unstaged. No other brain’s pass artifact, branch or worktree was read.

## Unit fence — actual collection and run output

The lane owner ran the focused schema fence with a fresh temporary HOME for
each invocation. No product service, browser, engine, native input or e2e
process was started. The full product suite and 1440/393 screenshots do not
apply: the specific static-lane brief forbids those runtime walks.

Command: `HOME=$(mktemp -d) uv run pytest -q --collect-only tests/unit/test_philo_graph_schema.py`

```text
tests/unit/test_philo_graph_schema.py::test_schema_is_a_valid_draft_2020_12_schema
tests/unit/test_philo_graph_schema.py::test_worked_example_passes_schema_and_integrity
tests/unit/test_philo_graph_schema.py::test_worked_example_joins_phase1_records_and_api_pairs
tests/unit/test_philo_graph_schema.py::test_observations_are_stored_one_per_brain_pass_viewport
tests/unit/test_philo_graph_schema.py::test_unresolved_link_endpoint_is_refused
tests/unit/test_philo_graph_schema.py::test_observation_without_provenance_is_refused
tests/unit/test_philo_graph_schema.py::test_finding_without_a_bin_is_refused
tests/unit/test_philo_graph_schema.py::test_case_without_an_expected_predicate_is_refused
tests/unit/test_philo_graph_schema.py::test_duplicate_ids_are_refused
tests/unit/test_philo_graph_schema.py::test_phase1_record_id_must_exist_in_that_inventory
tests/unit/test_philo_graph_schema.py::test_phase1_api_reference_must_exist_as_that_method_and_path
tests/unit/test_philo_graph_schema.py::test_phase1_api_reference_must_match_the_declared_method
tests/unit/test_philo_graph_schema.py::test_phase1_inventory_must_be_a_file_in_the_tree
tests/unit/test_philo_graph_schema.py::test_claim_review_record_reference_must_exist
tests/unit/test_philo_graph_schema.py::test_source_path_must_exist_in_the_tree
tests/unit/test_philo_graph_schema.py::test_evidence_path_must_exist_in_the_tree
tests/unit/test_philo_graph_schema.py::test_cli_exits_zero_on_the_example_and_one_on_a_broken_graph

17 tests collected in 0.05s
```

Command: `HOME=$(mktemp -d) uv run pytest -q tests/unit/test_philo_graph_schema.py`

```text
.................                                                        [100%]
17 passed in 0.92s
```

## Verification boundary

The schema validator proves structure, endpoint IDs and Phase 1 references.
A separate source-contract audit checks exact atlas copies, atlas-state and
edge coverage, trigger-specific typed paths, current API operation coverage,
input hashes, evidence line bounds, exact claim fields, exposure labels and
the complete first-value failure vocabulary. Those checks do not prove that
any user action completed; source findings were reviewed separately.

The graph keeps runtime observations and council resolutions empty. J7’s
same-summary/two-move outcome, J8 native delivery, provider results, clock
transitions and owner usefulness remain unverified. The atlas also records
the missing next-day clock mechanism. All cases are preserved verbatim.

## Seal and debt homes

Eight product findings belong to the council and Phase 3. One J9/J11
recipe/predicate tooling finding belongs to shared live-pass preparation.
Unresolved Phase 1 field reviews stay visible for council/story 07; an
inventory omission without a contradictory sentence is not called doc drift.
No product or curated/generated metadata was changed.

Muad’Dib’s check is deferred under the lane sealing law until all four pass
outputs are sealed. The story records this amendment explicitly; this seal
claims neither cross-brain ratification nor live/owner success.

## Captured validation

The captures below run the delivered-file validator and final source-contract
checks against the quiet lane tree. All workers held before sealing.

## Reproduce the additional source-contract check

The captured command uses a temporary lane helper. Its complete source is
retained here so verification does not depend on that ignored file. Save this
block as a Python file and run it with `uv run python` from the repository root.
It uses only source files and read-only Git commands.

```python
import ast,collections,hashlib,json,pathlib,re,subprocess
p=pathlib.Path('docs/internal/philo/graph/static-astra.json');g=json.loads(p.read_text());a=json.load(open('docs/internal/philo/graph/atlas.json'));ns={n['id']:n for n in g['nodes']};assert g['cases']==a['cases'];assert not g['observations'] and not g['resolutions']
assert len(ns)==len(g['nodes']);assert {s['id'] for s in a['states']}<=ns.keys()
by_input={i['path']:i['sha256'] for i in g['inputs']}
for path,digest in by_input.items():assert hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()==digest,path
sources=[s for n in g['nodes'] for s in n['sources']]+[s for k in ['links','claim_reviews','findings'] for n in g[k] for s in n['evidence']]
for s in sources:
 assert 1<=s['line']<=len(pathlib.Path(s['path']).read_text().splitlines()),s
 assert s['path'] in by_input,s
revisions={s['revision']for s in sources}
for r in revisions:subprocess.run(['git','cat-file','-e',r+'^{commit}'],check=True)
records=collections.defaultdict(list)
for shard in ['runtime','voice','desk','integrations']:
 path='docs/internal/philo/data/'+shard+'.json'
 for xs in json.load(open(path)).values():
  if isinstance(xs,list):
   for x in xs:
    if isinstance(x,dict) and 'id'in x:records[path,x['id']].append(x)
for r in g['claim_reviews']:
 c=r['claim_ref'];assert r['limits'].startswith('pass: static'),r['id']
 if 'record_id'in c:assert any(c['field'] in x for x in records[c['inventory_path'],c['record_id']]),r['id']
assert all(re.search(r'\[exposure=(active|conditional|internal|parked|historical)\]',n['label']) for n in g['nodes'] if n['kind']=='edge')
edges={e for c in a['cases'] for e in c['edge_ids']};adj=collections.defaultdict(list)
for l in g['links']:assert l['from'] in ns and l['to'] in ns;adj[l['from']].append(l['to'])
for e in edges:
 assert any(ns[i]['kind']=='interface' and any(ns[c]['kind']=='connection' and any(ns[x]['kind']=='action' for x in adj[c]) for c in adj[i]) for i in adj[e]),e
# Cross-check current API roster, rather than accepting a saved count.
o=json.load(open('docs/generated/openapi.json'));pairs={(method.upper(),path)for path,obj in o['paths'].items()for method in obj if method.lower()in {'get','post','put','patch','delete','options','head','trace'}}
refs={(r.get('method'),r.get('path')) for n in g['nodes'] if n['kind']=='edge' for r in n['phase1_refs'] if r.get('inventory_path')=='docs/generated/openapi.json'};assert pairs<=refs,pairs-refs
py=ast.parse(pathlib.Path('holdspeak/db/onboarding.py').read_text());server=next(ast.literal_eval(n.value)for n in py.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name)and t.id=='FIRST_VALUE_FAILURES'for t in n.targets))
ts=pathlib.Path('web/src/lib/dictationRecovery.ts').read_text();client=set(re.findall(r'\|\s*"([a-z_]+)"',ts.split('export type DictationFailure =',1)[1].split('export interface',1)[0]));assert server==client,(server-client,client-server)
report=pathlib.Path('docs/internal/philo/graph/static-astra.md').read_text()
for path,line in re.findall(r'((?:web|holdspeak|scripts|pm|docs)/[A-Za-z0-9_./-]+):(\d+)',report):assert pathlib.Path(path).is_file() and int(line)<=len(pathlib.Path(path).read_text().splitlines()),(path,line)
assert not subprocess.check_output(['git','diff','--name-only','--','holdspeak','web','scripts','tests','docs/generated','docs/internal/philo/data'],text=True)
print(f'OK: {len(a["cases"])} verbatim cases; {len(a["states"])} atlas state IDs; {len(edges)} trigger-scoped atlas chains; {len(pairs)} OpenAPI operations.')
print(f'OK: {len(g["inputs"])} input hashes; {len(sources)} source references with valid line bounds; {len(g["claim_reviews"])} exact-field reviews; {len(server)} matching first-value failures.')
print('OK: empty runtime observations/resolutions; declared trigger exposure; source commits resolve; report anchors exist; no product/generated/curated source modifications.')
print('LIMIT: these checks do not establish semantic correctness of every source claim or any executed/owner outcome; source findings were reviewed separately.')
print('Graph SHA256: '+hashlib.sha256(p.read_bytes()).hexdigest())
```

### Captured run — 2026-09-23T00:30:56Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.8Q4I3BFBHA uv run python .tmp/philo-astra/verify_seal.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e332786740a5e10ab853fc0f509270ff2fea5932

```text
OK: 69 verbatim cases; 111 atlas state IDs; 38 trigger-scoped atlas chains; 665 OpenAPI operations.
OK: 543 input hashes; 6409 source references with valid line bounds; 74 exact-field reviews; 14 matching first-value failures.
OK: empty runtime observations/resolutions; declared trigger exposure; source commits resolve; report anchors exist; no product/generated/curated source modifications.
LIMIT: these checks do not establish semantic correctness of every source claim or any executed/owner outcome; source findings were reviewed separately.
Graph SHA256: 866e7a3d957eca18f6a99d9c91d56866d027342ee61f58bbd02893e054633d0e
```

### Captured run — 2026-09-23T00:30:57Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.j5EOe0QYdo uv run python scripts/philo_graph_validate.py docs/internal/philo/graph/static-astra.json`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e332786740a5e10ab853fc0f509270ff2fea5932

```text
OK docs/internal/philo/graph/static-astra.json
```

## Supplied dirty input — reproduction copy

The supplied lane brief is not staged. A fresh checkout can validate the graph
without it; to repeat the stricter input-hash check, first recreate
`docs/internal/philo/briefs/static-pass-lane-brief.md` from this exact block.
This preserves the inspected input without adopting it as a new canon file.

```markdown
# The static pass — lane brief (PHILO-2-02 Muad'Dib · PHILO-2-03 Astra)

Both brains receive this text verbatim. The contract is `docs/internal/philo/briefs/graph-audit-brief.md` §§0–2, 6, 8, 9; this page only fixes the deliverable paths, the bounds and the sealing law. Read the brief first, then `docs/internal/philo/graph/atlas.json` (69 cases, 37 edges, 111 states: the ids you must reuse), `docs/internal/philo/graph/graph.schema.json` (+ `examples/graph.example.json`), `docs/internal/philo/data/README.md` and the four shards (Phase 1 record ids), `docs/generated/openapi.json`, `capabilities.yaml`, `components.yaml`, `domain-model.yaml`, `integrations.yaml`, `trust-boundaries.yaml`.

## Deliverables (this lane's files only)

1. `docs/internal/philo/graph/static-<brain>.json` — validates with `uv run python scripts/philo_graph_validate.py <file>` (schema + referential integrity + Phase 1 references). `observations` is empty (no hub in a static pass). `cases` references the atlas ids it traced (copy the case objects verbatim; do not invent cases). `claim_reviews` carry `pass: static` reasoning in `limits`.
2. `docs/internal/philo/graph/static-<brain>.md` — the §9 report shape (PASS: static; SOURCE revision + dirty; CONTRACT versions; JOBS: for each of J1–J11 the expected result and the STATIC verdict: wired | broken | unverifiable-statically, with evidence; GRAPH; COVERAGE; FINDINGS ranked by owner cost with bin; ORPHANS; UNKNOWN).

## Bounds

- **Deep trace, mandatory:** every edge the atlas names (37) and every control on the faces the eleven jobs touch (the arrival/Chair, the SETUP row and Concierge engine door, the Meetings review row and the summary face, the Desk memory shade and window, the BRIEF section, the Thought/note editor, the first-value gate): edge → interface → connection → action, each link with `path:line` evidence and a `relation`; a chain that breaks (a handler that resolves nothing; an execution owner that never performs the promised operation; a state the face has no branch for) is a `finding` with bin `product-defect`.
- **Enumeration, mandatory, breadth not depth:** every production entry point platform-wide with its exposure (active | conditional | internal | parked | historical): `web/src/desk/verbRegistry.ts`, `web/src/desk/applications.ts`, every library `Button` `onClick`/submit/change site, keyboard maps and the hotkey, `holdspeak/runtime/*` timers, WebSocket frame kinds, the MCP tool list (`holdspeak/mcp/`), the CLI (`holdspeak/main.py`), connector inputs, engine responses. One node per edge; links only where you traced them.
- **Claim reviews:** every Phase 1 capability whose `entry_points` or `surfaces` touch the deep-traced edges: verified | contradicted | unresolved | not_applicable, with the record id, the field, the revision and evidence.
- **Orphans:** derived from typed links and declared exposure (an internal capability needs no button; a parked surface is not an active edge; a local presentation action needs no table).
- **Doc drift:** a Phase 1 or canon sentence the trace contradicts → `finding` bin `doc-drift` (ledger only; correction is story 07).
- Source inspection, executed behaviour and owner observation stay distinct; never claim the second or third from the first.

## Sealing

Work in your own worktree (`../wt-philo-2-02` Muad'Dib, `../wt-philo-2-03` Astra), branch `audit/philo-2-0N-static-<brain>`. Commit only through the gate (`dw contract new --story PHILO-2-0N`), or hold for SHIP if you are a worker. **Do not read the other brain's `static-*.json`/`.md`, its branch, or its worktree until all four pass outputs are sealed.** Shared preparation (schema, atlas, rig) is not a finding.

## Laws

No hub, no product process, no e2e in a static pass. Unit fences in an isolated HOME only (`HOME=$(mktemp -d)`). Never the owner's data dir, keychain or microphone. Never a git verb that moves or cleans a tree; stage by explicit path. Report with the validator's output for your JSON and the §9 report; never inflate; "unverifiable statically" is a good answer.
```
