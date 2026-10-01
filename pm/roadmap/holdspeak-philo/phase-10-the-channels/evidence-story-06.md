# Evidence - PHILO-10-06

- **Story:** PHILO-10-06 - Prepare it cold, send it yourself
- **Status:** done
- **Date:** 2026-09-29
- **Branch:** `feat/philo-10-06` from main `05d01ffb` (stories 01–05 merged). No product file changed: a driver, its fixture, its fences, one parameter on the Phase 9 driver's isolation fence.
- **Label:** REHEARSED; OWNER REVIEW PENDING. Never a sitting.

## The owner's review — 2026-09-29

- **His words:** "Reviewed — with changes." Box 4 (owner-reviewed shots): **reviewed, with one change pending**.
- **The file-preview deviation:** "Folder is fine." This is an ACCEPTED CANVAS CHANGE by the owner's word (2026-09-29). The prepared file preview shows FOLDER, and the file name shows in the receipt after Send. There is no repair.
- **His change, pending:** a RESEND email provider joins SendGrid before the phase closes. That work is a separate lane and is not part of this story's diff.

## Round two — Codex Astra r1 on #700 @ `60630c31` (RATIFY-WITH-CONDITIONS), paid

`checks/story-06-built-astra-r1.md` (verbatim). There was no new real send: the folder still holds one file, and issue 699 still has one comment.

1. **Exact bytes only.** `readback_findings` (`scripts/philo10_send_job.py`) no longer accepts equality with the trailing whitespace trimmed. File and GitHub both need byte equality AND the sha256 of the frozen bytes (`digest=`). The GitHub read-back no longer records a trimmed comparison. New fence `test_an_extra_newline_on_the_far_side_is_red[file|github]`: the retained real read-back is green; with one extra trailing newline it is red; a record that claims equality with the wrong digest is red too. The fence over the retained real read-back stays green (`fence`, captured below).
2. **Shot 2 at 393.** New mode `reshoot-prepared`. It copies the retained real run's `db-proof.sqlite` (sha256 `24f1cb95…c22c0`, the same before and after), puts the two sends back to `prepared` IN THE COPY (no boundary, no proof, no history row), and boots a hub on it with a gh runner that answers nothing. The browser aborts every `POST /api/channels/send`, and Send is never pressed. For each prepared row at 1440 and 393, the mode seats the row and asserts ON SCREEN (in the viewport, inside every clipping ancestor, on top at three points): the heading (destination name), the attribution `BY CODEX-SEND-AGENT` and Send. Findings: none; sends attempted: none. Shots `2b-prepared-row-{file,github}-{1440,393}.png`; observation `observations/prepared-row-reshoot.json`; fence `test_the_prepared_row_reshoot_shows_heading_attribution_and_send_on_screen`.
3. **Named deviation (inherited, the owner decides).** The prepared file preview shows FOLDER, not the FILE the ratified canvas shows before Send. Production names the file at the dispatch boundary (`holdspeak/services/channel_service.py:469`), so a prepared row has `file_path: null`. Inherited from `05d01ffb`. It is recorded on the BACKLOG (PHILO-10-06 follow-ups). It is not repaired in this story.

The owner-review box stays open.

## What ran

- **The owner's word (2026-09-29):** file under `~/Documents/HoldSpeak`; GitHub `karolswdev/HoldSpeak`, an issue Muad'Dib chose (#699, public: only the fixture text posted); Jira, Confluence, email: "I don't have those yet. And that's fine."
- **Driver** `scripts/philo10_send_job.py` (reuses `scripts/philo9_room_job.py` and, through it, Phase 7's cold root, Codex turn, zero-read fence, pairing, receipt read and redaction). **Fixture** `story-06-fixture.json`, copied into the run with its sha256 before the hub was seeded.
- **Session 1 `agent_prepare`** (Codex `gpt-6-astra`, cold: scratch root, HOME and CODEX_HOME with `auth.json` alone, `--ignore-user-config --ignore-rules --disable apps --disable plugins`, the isolated hub the only MCP server, AGENT leg with a Settings-issued PROJECT credential). Its tools: `channel.destinations`, `project.list`, `connection.recheck` (refused `owner_principal_required`), `channel.check_destination` ×2, `project.list_updates`, `channel.prepare` ×2 (succeeded, `prepared_by` agent `codex-send-agent`), `channel.send` ×2 (**refused `owner_principal_required`, each with its receipt**). Zero non-MCP actions.
- **The press:** the driver, AS THE OWNER, pressed Send on each prepared row in the Room's face at 1440 (`POST /api/channels/send`), by the owner's word, for exactly these two targets. Codex never sent. Before each press: the exactly-once guard; for GitHub, `gh api user` under the scratch HOME answered `karolswdev`.
- **Session 2 `agent_check`** (fresh, distinct id, no resume): `project.list`, `project.list_updates`, `channel.sends`; its answer names both proofs; it wrote nothing.

## The two real sends and their independent read-backs

| Target | Proof (the hub's receipt, owner, succeeded) | Read back apart from the hub |
|---|---|---|
| File | `/Users/karol/Documents/HoldSpeak/2026-09-29-harbor-cutover-r1-d4f01b83.md`, sha256 `2158714a37e483dc14dfec2eceb95403c48efd0c2e97c3f752bc132f0c2830fd`, 287 bytes (operation `op_fb8f8bc5f6254b938a44e5b16e5a99ee`) | the file's bytes equal the frozen bytes; `shasum -a 256` gives the same digest |
| GitHub | `https://github.com/karolswdev/HoldSpeak/issues/699#issuecomment-5896512251` (operation `op_a438f300770a4e62a74432a09ede8c37`) | `gh api repos/karolswdev/HoldSpeak/issues/comments/5896512251`: author `karolswdev`, `html_url` = the proof, body sha256 `2158714a…30fd` = the frozen bytes exactly; the issue holds 1 comment |

**Exactly once:** `assets/story-06-real-sends.json` (the ledger, written before each click) names both; a second `--real` run is refused before anything boots (captured below, exit 4). The guard also reads the folder (the fixture's bytes) and the issue (the fixture's marker).

**Custody:** the hub ran on a scratch HOME. One file came from the real HOME: a 0600 copy of `~/.config/gh/hosts.yml`, deleted at the end (`assets/story-06-shots/final/20260929T184651Z-send-job-real/gh-login-file.json`: `exists_after: false`). No owner DB, no Keychain. Fences: account leaks 0, gh credentials 0, session isolation 0, fixture before run 0, zero-read 0/0.

## Named limits (exit 5 MET WITH QUALIFICATION for these three)

- **Jira, Confluence, email:** no real send. The owner has no account yet (2026-09-29). Their contracts are proven by the fences of story 02 (Jira, Confluence) and story 03 (email). The face at both widths shows Jira and Confluence NEVER CHECKED (no account) and no Jira, Confluence or email destination saved (shot 7). The pinned `acli --json` shapes, Confluence's `--from-json` fields and SendGrid's pinned 403 text stay unverified until his first real send.

## The face (1440 and 393) — `assets/story-06-shots/final/20260929T184651Z-send-job-real/shots/`

1. `1-prepared-list`: the update list, ◆ PREPARED ×2.
2. `2-prepared-well`: both rows PREPARED BY CODEX-SEND-AGENT, the first open with Send, Discard and its preview (at 393 the first row's head is above the seat; the facts read both rows).
3. `3-sent-list`: ✓ DELIVERY ×2.
4. `4-sent-results`: SAVED with the path, POSTED karolswdev/HoldSpeak #699, both BY CODEX-SEND-AGENT.
5. `5-sent-history`: DELIVERY 2 — the SAVED and POSTED rows with their proofs.
6. `6-destinations`: the Destinations group (the folder and issue 699).
7. `7-connections-named-limits`: Jira and Confluence NEVER CHECKED; two destinations only.

A rehearsal (recording runner, scratch folder; not retained) ran first: all green but the face check's wording for the named limits (it expected "Not set up"; the face says NEVER CHECKED on a hub that never saw an account). The check was corrected to the face's own words before the real run.

## Proof

### Captured run — 2026-09-29T18:46:51Z

- **Command:** `uv run python scripts/philo10_send_job.py run --real --codex-timeout 900`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b3ba01c26beac960f17474e1c3625bf179af3265

```text
RUN_DIR /Users/karol/dev/tools/wt-philo-10-06/pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-06-shots/final/20260929T184651Z-send-job-real
MODE REAL
PROOF REHEARSED; OWNER REVIEW PENDING
READBACK file {"bytes_equal_frozen": true, "exists": true, "in_folder": true, "mode": "0o644", "path": "/Users/karol/Documents/HoldSpeak/2026-09-29-harbor-cutover-r1-d4f01b83.md", "sha256": "2158714a37e483dc14dfec2eceb95403c48efd0c2e97c3f752bc132f0c2830fd", "size": 287}
READBACK github {"api": "GET repos/karolswdev/HoldSpeak/issues/comments/5896512251", "body_equals_frozen": true, "body_equals_frozen_trailing_whitespace_aside": true, "body_sha256": "2158714a37e483dc14dfec2eceb95403c48efd0c2e97c3f752bc132f0c2830fd", "created_at": "2026-09-29T18:47:56Z", "html_url": "https://github.com/karolswdev/HoldSpeak/issues/699#issuecomment-5896512251", "login": "karolswdev", "url_equals_proof": true}
OUTCOME COMPLETED
```

### Captured run — 2026-09-29T18:49:43Z

- **Command:** `sh -c H=$(mktemp -d); trap "rm -rf $H" EXIT; HOME=$H uv run pytest -q tests/unit/test_philo10_send_job.py tests/unit/test_philo9_room_job.py tests/unit/test_evidence_scratch_guard.py --basetemp $H/bt -p no:cacheprovider 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b3ba01c26beac960f17474e1c3625bf179af3265

```text

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
68 passed, 3 warnings in 2.16s
```

### Captured run — 2026-09-29T18:49:46Z

- **Command:** `uv run python scripts/philo10_send_job.py fence pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-06-shots/final/20260929T184651Z-send-job-real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b3ba01c26beac960f17474e1c3625bf179af3265

```text
fixture_before_run=[]
session_isolation=[]
account_leaks=[]
gh_credentials=[]
agent receipts=[]
agent prepared=[]
owner press file=[]
read-back file=[]
owner press github=[]
read-back github=[]
agent_prepare zero_read=0
agent_check zero_read=0
FENCES GREEN
```

### Captured run — 2026-09-29T18:49:46Z

- **Command:** `sh -c uv run python scripts/philo10_send_job.py run --real --out "$(mktemp -d)"; echo "exit=$?"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b3ba01c26beac960f17474e1c3625bf179af3265

```text
REFUSED file: the ledger records a real send at 2026-09-29T18:47:52.977794+00:00
REFUSED github: the ledger records a real send at 2026-09-29T18:47:54.934478+00:00
REFUSED file: /Users/karol/Documents/HoldSpeak/2026-09-29-harbor-cutover-r1-d4f01b83.md already holds the fixture's bytes
PHILO10_SEND_JOB_REFUSED a real send to a target that already has one; nothing booted
exit=4
```

### Captured run — 2026-09-29T19:02:12Z

- **Command:** `uv run python scripts/philo10_send_job.py reshoot-prepared pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-06-shots/final/20260929T184651Z-send-job-real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c0c798ec88ab21c0aeba49ed39248baed36d281c

```text
{
 "findings": [],
 "shots": [
  "shots/2b-prepared-row-file-1440.png",
  "shots/2b-prepared-row-github-1440.png",
  "shots/2b-prepared-row-file-393.png",
  "shots/2b-prepared-row-github-393.png"
 ]
}
```

### Captured run — 2026-09-29T19:03:02Z

- **Command:** `sh /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/c59536e9-4c14-410c-8d54-e0c2beed10bc/scratchpad/mut.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c0c798ec88ab21c0aeba49ed39248baed36d281c

```text
FAILED tests/unit/test_philo10_send_job.py::test_an_extra_newline_on_the_far_side_is_red[github]
1 failed, 1 passed, 21 deselected in 0.32s
restored:  1 file changed, 126 insertions(+), 14 deletions(-)
```

### Captured run — 2026-09-29T19:03:09Z

- **Command:** `uv run python scripts/philo10_send_job.py fence pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-06-shots/final/20260929T184651Z-send-job-real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c0c798ec88ab21c0aeba49ed39248baed36d281c

```text
fixture_before_run=[]
session_isolation=[]
account_leaks=[]
gh_credentials=[]
agent receipts=[]
agent prepared=[]
owner press file=[]
read-back file=[]
owner press github=[]
read-back github=[]
agent_prepare zero_read=0
agent_check zero_read=0
FENCES GREEN
```

### Captured run — 2026-09-29T19:03:10Z

- **Command:** `sh -c H=$(mktemp -d); trap "rm -rf $H" EXIT; HOME=$H uv run pytest -q tests/unit/test_philo10_send_job.py tests/unit/test_philo9_room_job.py tests/unit/test_evidence_scratch_guard.py --basetemp $H/bt -p no:cacheprovider 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c0c798ec88ab21c0aeba49ed39248baed36d281c

```text
71 passed, 3 warnings in 2.23s
```
