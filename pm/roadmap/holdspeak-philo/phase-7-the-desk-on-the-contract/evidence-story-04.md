# Evidence - PHILO-7-04

- **Story:** PHILO-7-04 - File it and find it without the repo
- **Status:** done
- **Date:** 2026-09-25
- **Branch:** `feat/philo-7-04-cold-context` (main merged in).
- **History of this file:** while the story was in progress, the gate refused `evidence-story-04.md` ("Orphan evidence"), so it was kept as `lane-report-story-04.md`; the earlier `dw evidence capture` runs below were captured into `evidence-story-04.md` and moved there unchanged. It became this evidence file at the flip.
- **Label:** REHEARSED; OWNER-REVIEWED ("Reviewed — it's right", 2026-09-26, on the rerun; the first run bounced: "the decision is thin"). Never a sitting.
- **Record:** `docs/internal/philo/phase-7/file-and-find/rehearsal.md` (the full launch record, each turn, the receipts, the shots, the reds).

## The claim (R6, with R3's qualification intact)

This story claims exactly: "a cold-context Claude session (an empty scratch dir, a scratch HOME with only the auth file, no user or project instructions, `--strict-mcp-config` with the one holdspeak server, no preamble), ZERO repository reads in the retained log, discovery from the catalogue alone".

## The closing run (R6: "Claude closes it"; rerun after the owner's review)

The owner reviewed the first run's shots: "the decision is thin — a decision put on my review list should carry its context, not just a title." That run is under `attempts/20260926T014230Z-file-and-find/` ("owner review: the decision is thin"). The repair: the owner's words carry the reason; the catalogue names a decision's parts (the discovery fence's new job "the reason for a decision", red on main); the readback checks the context durably; the shots are split per leg.

`assets/story-04-shots/final/20260926T015522Z-file-and-find/`: COMPLETED in 94.8 s, exit 0 (the capture of 2026-09-26T01:55:22Z below).

- **Auth:** the macOS login keychain (`Claude Code-credentials`), reduced to the access token (the refresh token dropped). It is the scratch HOME's only file and is deleted after the run.
- **OWNER leg** (the built sidecar): file 9.2 s, find 4.9 s, decide 8.0 s, brief 8.0 s. One `zone.file` and one `decision.create`, each `succeeded`, actor the owner.
  - The decision reads back through `decision.read`: context "Our own runners are full every night. The shared runner pool has spare capacity after 8 PM.", decision "Move the nightly build to the shared runners.", status `proposed`.
  - The brief row: `decision:decision_32cacbceb68d`.
- **AGENT leg** (`/api/mcp`, the DESK bearer):
  - Without the grant: `zone.file` refused with `desk_delegation_required` (actor `claude-desk-agent`); the note was not filed; zero `awaiting_decision`.
  - With the grant: filed, receipt `succeeded`, `desk-delegation:deskdeleg_87740697…:sha256:…`, `delegator_kind=owner`.
- **Zero reads:** 0 findings in all six sessions.
- **Shots:** `shots/owner-zone/`, `shots/owner-decision/` and `shots/brief/` (the OWNER leg, before the agent files); `shots/agent-zone/` (after). All at 1440 and 393.
- **Engine:** `none` (the jobs call no model).

## Account redaction

The repository is public. The first closing run's retained session records held the account e-mail (nine files), the organisation id and the synced skill names. The driver now redacts them at the end of every run (`redact_run`), and its retained files were redacted in place (`attempts/20260926T014230Z-file-and-find/redaction.json`); the rerun was redacted at capture. The leak fence was RED on nine files before (`docs/internal/philo/phase-7/file-and-find/red-account-scan.txt`) and is green after. By the owner's ruling, the branch was rebuilt from main with the clean tree only: its file content holds no e-mail; the commit author header carries the repository's git identity, as every commit on main does. The Phase 5 and Phase 6 retained runs hold no e-mail address and no token-shaped string (a byte-level scan of every file; report only, not edited).

## Reds

- `docs/internal/philo/phase-7/file-and-find/red-claude-read/`: a real `claude -p` in the same cold setup told to read `<repo>/CLAUDE.md`: 1 finding (Bash `head -n 1 <repo>/CLAUDE.md`).
- `docs/internal/philo/phase-7/file-and-find/red-zero-read-phase5.txt`: the Phase 5 Codex logs, 25 + 3 = 28 findings.
- The mutation reds are listed in the record.

## The check on built, paid

The Astra-role check (`checks/story-04-built-astra-role-r1.md`): RATIFY-WITH-CONDITIONS.
- **C1:** a holdspeak resource whose body is a repository document (`holdspeak://desk/constitution`, `holdspeak/mcp/resources.py:475`) is now a zero-read finding (`REPO_DOC_RESOURCES`, both the Claude and the Codex fence). A structural fence keeps the set equal to the resources that read `_REPO_ROOT`. RED before: `docs/internal/philo/phase-7/file-and-find/red-constitution-resource.txt` (0 findings at 123675c7, 1 after). The six sessions still have 0.
- **C2:** `desk.update` now reads "Change a decision: … the new text replaces the old". Every `--check` is green; the discovery fence is green.
- **C3:** the stale records are corrected. The transcripts carry the redaction marker. The first run's path is under `attempts/`. The `-receipt`/`-row` files are named full-shot copies.
- **C4:** acceptance boxes 1, 3 and 4 are reworded to R6's Claude claim.
- **C5 (ruled by the coordinator):** the commit author header is the repository's git identity; the file content holds no e-mail.
- **Recorded in the rehearsal record:** the ToolSearch qualification (tools were chosen mostly by name; the reason's placement is confounded with the changed words), and "find it" proving "find it again", not "find it cold".

## Not done, and uncertain

- One acceptance box is not ticked: "Muad'Dib's check recorded". The check in the tree is the Astra-role check.
- The retained session transcripts carry the redaction marker `<owner-account-email>` where Claude's own `session_context` attachment named the account.
- The initial context carries a count of the account's synced skills (their names are redacted).
- The Codex attempt (before R6) stays under `attempts/`. It is superseded; no rerun is owed.
- Backlog (the check's MISSED, on main already): the DESK palette equals ALL; the decision window shows an empty CONSEQUENCES heading; the brief reports the people sections as unavailable on a fresh hub.

### Captured run — 2026-09-25T21:56:23Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.qTzfxzkPik HOLDSPEAK_EVIDENCE_WRITE=1 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright .venv/bin/python scripts/philo7_file_and_find.py run --out pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-04-shots/attempts --codex-auth /Users/karol/.codex/auth.json`
- **Cwd:** .
- **Exit code:** 3
- **Index-tree:** fd172788324ab0ba5e2d81e96df00c4c2791b6d2

```text
RUN_DIR /Users/karol/dev/tools/wt-philo-7-04/pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-04-shots/attempts/20260925T215624Z-file-and-find
PROOF REHEARSED; OWNER REVIEW PENDING
OUTCOME BLOCKED
BLOCKED OWNER: owner_file: codex_usage_limit: You’ve hit your usage limit. Visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at Sep 26th, 2026 8:50 PM.
BLOCKED AGENT: ungranted: codex_usage_limit: You’ve hit your usage limit. Visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at Sep 26th, 2026 8:50 PM.
BLOCKED AGENT: granted: codex_usage_limit: You’ve hit your usage limit. Visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at Sep 26th, 2026 8:50 PM.
```

### Captured run — 2026-09-25T22:00:15Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.vsTIRgKuw0 uv run pytest -q -p no:cacheprovider tests/unit/test_philo7_file_and_find.py tests/unit/test_philo5_his_words.py tests/unit/test_philo5_rig_import_boundary.py tests/unit/test_docs_navigation.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fd172788324ab0ba5e2d81e96df00c4c2791b6d2

```text
........................................................................ [ 80%]
..................                                                       [100%]
90 passed in 2.20s
```

### Captured run — 2026-09-26T01:42:30Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.7ugUoZtX77 HOLDSPEAK_EVIDENCE_WRITE=1 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright .venv/bin/python scripts/philo7_file_and_find.py run --out pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-04-shots/final --client claude`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b784330d520dbdc6d05b67cebd1b6f87399d59c5

```text
RUN_DIR /Users/karol/dev/tools/wt-philo-7-04/pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-04-shots/final/20260926T014230Z-file-and-find
PROOF REHEARSED; OWNER REVIEW PENDING
OUTCOME COMPLETED
```

### Captured run — 2026-09-26T01:46:48Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.5r2KaFPWYV uv run pytest -q -p no:cacheprovider tests/unit/test_philo7_file_and_find.py tests/unit/test_philo5_his_words.py tests/unit/test_philo5_rig_import_boundary.py tests/unit/test_docs_navigation.py tests/unit/test_doc_drift_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b784330d520dbdc6d05b67cebd1b6f87399d59c5

```text
........................................................................ [ 48%]
........................................................................ [ 96%]
......                                                                   [100%]
150 passed in 3.63s
```

### Captured run — 2026-09-26T01:51:38Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.MNo0uJC7LK uv run pytest -q -p no:cacheprovider tests/unit/test_philo7_file_and_find.py tests/unit/test_philo5_his_words.py tests/unit/test_philo5_rig_import_boundary.py tests/unit/test_docs_navigation.py tests/unit/test_doc_drift_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 57f642a76ef413df4fec8972a7ba88d266ea8095

```text
........................................................................ [ 46%]
........................................................................ [ 92%]
............                                                             [100%]
156 passed in 3.85s
```

### Captured run — 2026-09-26T01:55:22Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.78DjnJKSW7 HOLDSPEAK_EVIDENCE_WRITE=1 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright .venv/bin/python scripts/philo7_file_and_find.py run --out pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-04-shots/final --client claude`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3c9e99e096097374e9ca37bf2d4dcb72eb3a1272

```text
RUN_DIR /Users/karol/dev/tools/wt-philo-7-04/pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-04-shots/final/20260926T015522Z-file-and-find
PROOF REHEARSED; OWNER REVIEW PENDING
OUTCOME COMPLETED
```

### Captured run — 2026-09-26T01:59:06Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.xEvFK00Y09 uv run pytest -q -p no:cacheprovider -n 8 tests/unit/test_philo7_file_and_find.py tests/unit/test_philo7_discovery.py tests/unit/test_philo7_article_xi.py tests/unit/test_philo5_his_words.py tests/unit/test_philo5_rig_import_boundary.py tests/unit/test_philo5_one_decision.py tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_api_surface.py tests/unit/test_docs_navigation.py tests/unit/test_doc_drift_guard.py tests/unit/test_philo_graph_reference.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3c9e99e096097374e9ca37bf2d4dcb72eb3a1272

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 23%]
........................................................................ [ 46%]
........................................................................ [ 70%]
........................................................................ [ 93%]
...................                                                      [100%]
307 passed in 16.43s
```

### Captured run — 2026-09-26T06:35:22Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.iJAwqu6IvO uv run pytest -q -p no:cacheprovider -n 8 tests/unit/test_philo7_file_and_find.py tests/unit/test_philo7_discovery.py tests/unit/test_philo7_article_xi.py tests/unit/test_philo5_his_words.py tests/unit/test_philo5_rig_import_boundary.py tests/unit/test_philo5_one_decision.py tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_api_surface.py tests/unit/test_docs_navigation.py tests/unit/test_doc_drift_guard.py tests/unit/test_philo_graph_reference.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ae591b8bed6b7025ff5d552bff831ef7082290da

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 23%]
........................................................................ [ 46%]
........................................................................ [ 69%]
........................................................................ [ 92%]
......................                                                   [100%]
310 passed in 16.40s
```

### Captured run — 2026-09-26T06:36:07Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.HUjNBTbZFa .venv/bin/python scripts/philo7_file_and_find.py fence pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-04-shots/final/20260926T015522Z-file-and-find`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ae591b8bed6b7025ff5d552bff831ef7082290da

```text
owner_file zero_read=0 unlisted=[] init=[]
owner_find zero_read=0 unlisted=[] init=[]
owner_decide zero_read=0 unlisted=[] init=[]
owner_brief zero_read=0 unlisted=[] init=[]
agent_ungranted zero_read=0 unlisted=[] init=[]
agent_granted zero_read=0 unlisted=[] init=[]
decision_reason=[] agent_receipts=[] account_leaks=0
FENCES GREEN
```

### Captured run — 2026-09-26T06:36:15Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.sqLl0UL3Zt uv run pytest -q -p no:cacheprovider -n 8 tests/unit/test_philo7_file_and_find.py tests/unit/test_philo7_discovery.py tests/unit/test_philo7_article_xi.py tests/unit/test_philo5_his_words.py tests/unit/test_philo5_rig_import_boundary.py tests/unit/test_philo5_one_decision.py tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_api_surface.py tests/unit/test_docs_navigation.py tests/unit/test_doc_drift_guard.py tests/unit/test_philo_graph_reference.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ae591b8bed6b7025ff5d552bff831ef7082290da

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 23%]
........................................................................ [ 46%]
........................................................................ [ 69%]
........................................................................ [ 92%]
......................                                                   [100%]
310 passed in 16.69s
```
