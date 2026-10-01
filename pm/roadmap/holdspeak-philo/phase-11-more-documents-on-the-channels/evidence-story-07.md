# Evidence - PHILO-11-07

- **Story:** PHILO-11-07 - The closing use
- **Status:** done
- **Date:** 2026-10-01
- **Branch:** `feat/philo-11-07` from main `349e25c4` (stories 01–06 merged). No product file changed: a driver (`scripts/philo11_send_job.py`), its fixture (`story-07-fixture.json`), its fences (`tests/unit/test_philo11_send_job.py`), and one parameter on the Phase 9 driver's isolation fence (`scripts/philo9_room_job.py:152`, the same change as the open Phase 10 PR #700).
- **Label:** REHEARSED; OWNER REVIEW PENDING. Never a sitting.

## What ran

- **The owner's targets** (charter D3; the Phase 10 Q6 ruling carries): the folder `/Users/karol/Documents/HoldSpeak` and the public scratch issue `karolswdev/HoldSpeak#699`. Fixture text only (every document says "PHILO-11-07 test"). Email (no Resend details yet) and Slack (no webhook) are named limits; Jira and Confluence too (no accounts).
- **The fixture** `story-07-fixture.json` is copied into each run with its sha256 before the hub is seeded. Every document is minted through its real producer (the `tests/unit/_philo11_documents.py` pattern) into the hub's own DB under a scratch HOME, before the hub boots. The People sidecar uses a file key in that HOME (no Keychain).
- The driver reuses Phase 9 story 06 and Phase 7: the cold root, the Codex turn, the zero-read fence, the receipt read and the redaction at capture. The face uses the Phase 11 glass rig `tests/e2e/_doc_send_glass.Boards` (the on-screen law and the nine-point pointer pass at both widths).

### Leg A: the rehearsal (isolated hub, scratch folder; nothing leaves)

- **One cold Codex session** `agent_prepare` (`gpt-6-astra`; scratch root, HOME and CODEX_HOME with `auth.json` alone; `--ignore-user-config --ignore-rules --disable apps --disable plugins`; the isolated hub is its only MCP server; AGENT leg with a Settings-issued **DESK** credential, because PROJECT has no brief or decision-record tools). It got the fixture's words: "Get my brief from today and the decision record about moving the queue in two steps ready to go to the HoldSpeak folder. Then send both of them."
- **Its tools** (retained run `assets/story-07-shots/final/20261001T115906Z-rehearse`): `channel.destinations`, `decision_record.search`, `monday_brief.get`, `decision_record.get`, `channel.check_destination`, `channel.preview` ×2, `channel.prepare` ×2 (both succeeded, `prepared_by` agent `codex-send-agent`, each digest equal to the owner's own preview), `channel.send` (**refused `owner_principal_required` with its receipt**). Zero non-MCP actions. Fences: fixture before run 0, session isolation 0, zero-read 0, account leaks 0.
- **The face** (shots below): the Chair's brief well and Intelligence → DECISIONS show `◆ PREPARED BY CODEX-SEND-AGENT` at 1440 and 393. The driver, AS THE OWNER, clicked Send on each prepared row at 1440 (`POST /api/channels/send` from the face). Both settled `✓ SAVED <path> BY CODEX-SEND-AGENT` at both widths, with `SENDS 1`. Read back from the hub: each row is `sent`; each receipt is `channel.send` succeeded by the owner; each file's sha256 equals the frozen `payload_digest` and the hub's proof; there is no transcript sentinel and no internal id in either file. The brief's Slack text is 566 / 39,000 characters.
- **An earlier capture was blocked, and it stays on record** (`assets/story-07-shots/final/20261001T115709Z-rehearse`, exit 3). That session ran `ls -la` once in its own empty scratch root. This is not a repository read, but the zero-read fence counts every non-MCP action, so the run is BLOCKED. The second session above is a fresh cold session (new root, homes and session id). Nothing was changed between the two runs.

### Leg B: the real sends (`assets/story-07-shots/final/20261001T120102Z-real`)

On an isolated hub (scratch HOME; one file from the real HOME: a 0600 copy of `~/.config/gh/hosts.yml`, deleted at the end, `exists_after: false`), the driver AS THE OWNER read each preview and pressed the inline Send with the digest it read (`POST /api/channels/send`, the SEND well's own route; not a click). The ledger `assets/story-07-real-sends.json` got each entry BEFORE its press.

| Kind | Target | Far-side proof | Read back apart from the hub |
|---|---|---|---|
| monday_brief | file | `/Users/karol/Documents/HoldSpeak/2026-10-01-brief-2026-10-01-brief-2026-10-01-21901155.md` | sha256 `296d0de6…51ad` (576 B) = the frozen digest |
| monday_brief | GitHub | https://github.com/karolswdev/HoldSpeak/issues/699#issuecomment-5930904969 | `gh api`: author `karolswdev`, body sha256 `296d0de6…51ad` |
| decision_record | file | `…/2026-10-01-move-the-queue-in-two-steps-philo-11-07-test-decision-00bbda64.md` | sha256 `46b46fe1…4b73` (239 B) |
| decision_record | GitHub | https://github.com/karolswdev/HoldSpeak/issues/699#issuecomment-5930906027 | body sha256 `46b46fe1…4b73` |
| meeting_summary | file | `…/2026-10-01-lantern-migration-review-philo-11-07-test-summary-2026-10-01-bfd28f67.md` | sha256 `bc55db0d…64dd` (253 B) |
| meeting_summary | GitHub | https://github.com/karolswdev/HoldSpeak/issues/699#issuecomment-5930906937 | body sha256 `bc55db0d…64dd` |
| project_update | file | `…/2026-10-01-lantern-migration-rev-1-aea5b26f.md` | sha256 `f2ac574f…06e2e` |
| desk_decision | file | `…/2026-10-01-keep-the-old-queue-read-only-for-one-week-decision-4d95ccf4.md` | sha256 `b38e4122…81a4a` |
| meeting_decision | file | `…/2026-10-01-move-the-queue-in-two-steps-philo-11-07-test-decision-f8f1825f.md` | sha256 `9f68ebb2…bc9bc` |
| meeting_digest | file | `…/2026-10-01-lantern-migration-review-philo-11-07-test-digest-2026-10-01-9159ef9d.md` | sha256 `f93bb2f9…6e0` |
| meeting_followup | file | `…/2026-10-01-lantern-migration-review-philo-11-07-test-followup-2026-10-01-34af5653.md` | sha256 `6ff79858…65d1` |

- All three families went on both channels he has, and all eight Phase 11 kinds went to the folder once each. Each row: the send is `sent`; the receipt is `channel.send` succeeded by the owner; the frozen digest equals the digest of the preview he read; the far side's sha256 equals the frozen digest (exact bytes); the far side carries the fixture's own document of that kind. **The #711 law, checked on the read-back:** no transcript sentinel, no internal ref (`prop-`, `record-`, `meeting:`, `#segment`, `brief-`, `chs_`, …), no hex id of 8+ characters, and no source id in any text that went out. The file NAMES carry the first 8 hex of the send id by the Phase 10 §5 naming law; a name is not sent text.
- **Independent reads** (captured below): `shasum -a 256` over the folder gives the same eight digests; `gh api` on each comment gives the same three digests and author `karolswdev`. The issue now holds four comments (Phase 10's one plus these three). My first comment-hash command failed (`head -c -1` is not valid on macOS: empty-input digests `e3b0…`). That capture stays in the record, and the corrected capture follows it.
- **The Slack length of each real brief sent** (Astra r1 finding 9): 566 / 39,000 characters of Slack text (`markdown_to_slack`, the channel's own converter) for the brief to the folder and to the issue. Well under the limit; the Tuesday claim holds for this brief.
- **Exactly once:** a second `real` run is refused before anything boots (exit 4, captured): by the ledger (11 pairs) and, independently, by the folder (the eight files carry their kinds).

## Named limits

- **Email:** no real send. The owner has not given the Resend details yet. The contract is proven by Phase 10 stories 03 and 07 and the Phase 11 fences.
- **Slack:** no real post. The owner has given no webhook. The contract is proven by story 02's recording-edge fences and story 06's atlas cases. The brief's Slack length is recorded above.
- **Jira, Confluence:** no account. The contract is proven by Phase 10 story 02's fences.
- **`artifact`**, the ninth registry kind (`holdspeak/services/document_sources.py`), is not a Phase 11 kind and is outside this story.

## The face — `assets/story-07-shots/final/20261001T115906Z-rehearse/shots/` (each looked at)

1. `1-brief-prepared-{1440,393}`: the Chair's brief well, `◆ PREPARED BY CODEX-SEND-AGENT BRIEF OCT 1`, the FOLDER, Send and Discard, and the brief's preview with its person section below.
2. `2-record-prepared-{1440,393}`: Intelligence → DECISIONS, the record's well, `◆ PREPARED BY CODEX-SEND-AGENT D-…`, and the record's preview.
3. `3-brief-saved-{1440,393}`: `✓ SAVED <path> BY CODEX-SEND-AGENT`; the destination row `✓ SAVED 06:00`; `SENDS 1`.
4. `4-record-saved-{1440,393}`: the same for the record.

Seen, inherited, for the owner's review (not repaired here): after the brief's prepared send settles, the Chair's BRIEF head keeps a lone `THIS DEVICE` chip where `◆ PREPARED ×1` was (shot 4 at 1440, left pane). Each prepared FOLDER preview shows the folder, not the file name (the Phase 10 deviation the owner accepted, "Folder is fine").

## Proof

### Captured run — 2026-10-01T11:57:09Z

- **Command:** `sh -c H=$(mktemp -d); trap "rm -rf $H" EXIT; HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run python scripts/philo11_send_job.py rehearse --out pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-07-shots/final --codex-auth /Users/karol/.codex/auth.json --codex-timeout 900`
- **Cwd:** .
- **Exit code:** 3
- **Index-tree:** 62be92e5d517c83052da18a3f6f52d239b219866

```text
RUN_DIR /Users/karol/dev/tools/wt-philo-11-07/pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-07-shots/final/20261001T115709Z-rehearse
MODE REHEARSAL (isolated hub, scratch folder: nothing leaves the machine)
AGENT_TOOLS ['decision_record.search', 'monday_brief.get', 'channel.destinations', 'channel.preview', 'channel.preview', 'channel.check_destination', 'channel.prepare', 'channel.prepare', 'channel.send', 'channel.send']
SAVED monday_brief {"exists": true, "in_folder": true, "mode": "0o644", "path": "/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo11-07-rh-glg5x3fg/outbox/2026-10-01-brief-2026-10-01-brief-2026-10-01-2cb7f0e7.md", "sha256": "60d08b4e1fe8844595e4733cb6e61ef8cfd6f6797f434e43aa27abd42231c0a2", "size": 576, "slack": {"limit": 39000, "slack_text_characters": 566, "slack_text_sha256": "5b89e1f7575dded48e9b1d325ed7130b63450859c18134f837d7027ab0146d62", "within_limit": true}}
SAVED decision_record {"exists": true, "in_folder": true, "mode": "0o644", "path": "/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo11-07-rh-glg5x3fg/outbox/2026-10-01-move-the-queue-in-two-steps-philo-11-07-test-decision-09458726.md", "sha256": "46b46fe148a2febb86cc5e0587e80951b3bcae53848813256bdd258f25ed4b73", "size": 239}
OUTCOME BLOCKED
BLOCKED agent_prepare: zero-read fence: 1 non-MCP action(s)
BLOCKED fence zero_read: 1
```

### Captured run — 2026-10-01T11:59:06Z

- **Command:** `sh -c H=$(mktemp -d); trap "rm -rf $H" EXIT; HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run python scripts/philo11_send_job.py rehearse --out pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-07-shots/final --codex-auth /Users/karol/.codex/auth.json --codex-timeout 900`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 62be92e5d517c83052da18a3f6f52d239b219866

```text
RUN_DIR /Users/karol/dev/tools/wt-philo-11-07/pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-07-shots/final/20261001T115906Z-rehearse
MODE REHEARSAL (isolated hub, scratch folder: nothing leaves the machine)
AGENT_TOOLS ['channel.destinations', 'decision_record.search', 'monday_brief.get', 'decision_record.get', 'channel.check_destination', 'channel.preview', 'channel.preview', 'channel.prepare', 'channel.prepare', 'channel.send']
SAVED monday_brief {"exists": true, "in_folder": true, "mode": "0o644", "path": "/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo11-07-rh-r0tvc2sd/outbox/2026-10-01-brief-2026-10-01-brief-2026-10-01-f2686bef.md", "sha256": "119e6ca6c18fd2844a2d345b21dc7ccf97b3d9a5eadb96e77ee4bd9fd6190c06", "size": 576, "slack": {"limit": 39000, "slack_text_characters": 566, "slack_text_sha256": "191364136735c5550c0a65dbc3bcd8fce8fac9361ef8645f146e45ba025c0b04", "within_limit": true}}
SAVED decision_record {"exists": true, "in_folder": true, "mode": "0o644", "path": "/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo11-07-rh-r0tvc2sd/outbox/2026-10-01-move-the-queue-in-two-steps-philo-11-07-test-decision-045d562d.md", "sha256": "46b46fe148a2febb86cc5e0587e80951b3bcae53848813256bdd258f25ed4b73", "size": 239}
OUTCOME COMPLETED
```

### Captured run — 2026-10-01T12:01:02Z

- **Command:** `sh -c HOLDSPEAK_EVIDENCE_WRITE=1 uv run python scripts/philo11_send_job.py real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 62be92e5d517c83052da18a3f6f52d239b219866

```text
RUN_DIR /Users/karol/dev/tools/wt-philo-11-07/pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-07-shots/final/20261001T120102Z-real
MODE REAL
SENT monday_brief -> file sent /Users/karol/Documents/HoldSpeak/2026-10-01-brief-2026-10-01-brief-2026-10-01-21901155.md sha256=296d0de698bd85c9028e97d875f05b8b3b78db856c00f40a86e9af27b5c951ad far_side_ok=True
SENT monday_brief -> github sent https://github.com/karolswdev/HoldSpeak/issues/699#issuecomment-5930904969 sha256=296d0de698bd85c9028e97d875f05b8b3b78db856c00f40a86e9af27b5c951ad far_side_ok=True
SENT decision_record -> file sent /Users/karol/Documents/HoldSpeak/2026-10-01-move-the-queue-in-two-steps-philo-11-07-test-decision-00bbda64.md sha256=46b46fe148a2febb86cc5e0587e80951b3bcae53848813256bdd258f25ed4b73 far_side_ok=True
SENT decision_record -> github sent https://github.com/karolswdev/HoldSpeak/issues/699#issuecomment-5930906027 sha256=46b46fe148a2febb86cc5e0587e80951b3bcae53848813256bdd258f25ed4b73 far_side_ok=True
SENT meeting_summary -> file sent /Users/karol/Documents/HoldSpeak/2026-10-01-lantern-migration-review-philo-11-07-test-summary-2026-10-01-bfd28f67.md sha256=bc55db0d49908c177446566f1c73f458177dbc172f5f01777dbc6db0ad7164dd far_side_ok=True
SENT meeting_summary -> github sent https://github.com/karolswdev/HoldSpeak/issues/699#issuecomment-5930906937 sha256=bc55db0d49908c177446566f1c73f458177dbc172f5f01777dbc6db0ad7164dd far_side_ok=True
SENT project_update -> file sent /Users/karol/Documents/HoldSpeak/2026-10-01-lantern-migration-rev-1-aea5b26f.md sha256=f2ac574f5f2164bc6e320f251a2af96fe8a0de80d1d1fa4255951c7720c06e2e far_side_ok=True
SENT desk_decision -> file sent /Users/karol/Documents/HoldSpeak/2026-10-01-keep-the-old-queue-read-only-for-one-week-decision-4d95ccf4.md sha256=b38e412281de09017ab47ba1684f74209fa71eb5794c408053eb4198f6a81a4a far_side_ok=True
SENT meeting_decision -> file sent /Users/karol/Documents/HoldSpeak/2026-10-01-move-the-queue-in-two-steps-philo-11-07-test-decision-f8f1825f.md sha256=9f68ebb22a76d165095af5913db88e153a6fdbf203ef355f03eae63fe4cbc9bc far_side_ok=True
SENT meeting_digest -> file sent /Users/karol/Documents/HoldSpeak/2026-10-01-lantern-migration-review-philo-11-07-test-digest-2026-10-01-9159ef9d.md sha256=f93bb2f9fda3929697c0871c18948320e6430525b6025a739db466716c8ea6e0 far_side_ok=True
SENT meeting_followup -> file sent /Users/karol/Documents/HoldSpeak/2026-10-01-lantern-migration-review-philo-11-07-test-followup-2026-10-01-34af5653.md sha256=6ff79858ba2b4f6c1f42e31c6c2c66846724314ffb798d4e4de43835c8f965d1 far_side_ok=True
SLACK brief -> file: 566 / 39000 characters
SLACK brief -> github: 566 / 39000 characters
OUTCOME COMPLETED
```

### Captured run — 2026-10-01T12:01:23Z

- **Command:** `sh -c cd /Users/karol/Documents/HoldSpeak && shasum -a 256 2026-10-01-*.md; gh api repos/karolswdev/HoldSpeak/issues/699/comments --jq ".[] | [.html_url, .user.login, (.body|length|tostring)] | join(\" \")"; for id in 5930904969 5930906027 5930906937; do gh api repos/karolswdev/HoldSpeak/issues/comments/$id --jq .body | head -c -1 | shasum -a 256; done`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 62be92e5d517c83052da18a3f6f52d239b219866

```text
296d0de698bd85c9028e97d875f05b8b3b78db856c00f40a86e9af27b5c951ad  2026-10-01-brief-2026-10-01-brief-2026-10-01-21901155.md
b38e412281de09017ab47ba1684f74209fa71eb5794c408053eb4198f6a81a4a  2026-10-01-keep-the-old-queue-read-only-for-one-week-decision-4d95ccf4.md
f2ac574f5f2164bc6e320f251a2af96fe8a0de80d1d1fa4255951c7720c06e2e  2026-10-01-lantern-migration-rev-1-aea5b26f.md
f93bb2f9fda3929697c0871c18948320e6430525b6025a739db466716c8ea6e0  2026-10-01-lantern-migration-review-philo-11-07-test-digest-2026-10-01-9159ef9d.md
6ff79858ba2b4f6c1f42e31c6c2c66846724314ffb798d4e4de43835c8f965d1  2026-10-01-lantern-migration-review-philo-11-07-test-followup-2026-10-01-34af5653.md
bc55db0d49908c177446566f1c73f458177dbc172f5f01777dbc6db0ad7164dd  2026-10-01-lantern-migration-review-philo-11-07-test-summary-2026-10-01-bfd28f67.md
46b46fe148a2febb86cc5e0587e80951b3bcae53848813256bdd258f25ed4b73  2026-10-01-move-the-queue-in-two-steps-philo-11-07-test-decision-00bbda64.md
9f68ebb22a76d165095af5913db88e153a6fdbf203ef355f03eae63fe4cbc9bc  2026-10-01-move-the-queue-in-two-steps-philo-11-07-test-decision-f8f1825f.md
https://github.com/karolswdev/HoldSpeak/issues/699#issuecomment-5896512251 karolswdev 285
https://github.com/karolswdev/HoldSpeak/issues/699#issuecomment-5930904969 karolswdev 573
https://github.com/karolswdev/HoldSpeak/issues/699#issuecomment-5930906027 karolswdev 239
https://github.com/karolswdev/HoldSpeak/issues/699#issuecomment-5930906937 karolswdev 253
head: illegal byte count -- -1
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  -
head: illegal byte count -- -1
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  -
head: illegal byte count -- -1
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  -
```

### Captured run — 2026-10-01T12:01:25Z

- **Command:** `sh -c uv run python scripts/philo11_send_job.py real --out "$(mktemp -d)"; echo "exit=$?"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 62be92e5d517c83052da18a3f6f52d239b219866

```text
REFUSED monday_brief -> file: the ledger records a real press at 2026-10-01T12:01:06.212814+00:00
REFUSED monday_brief -> github: the ledger records a real press at 2026-10-01T12:01:07.047372+00:00
REFUSED decision_record -> file: the ledger records a real press at 2026-10-01T12:01:09.210453+00:00
REFUSED decision_record -> github: the ledger records a real press at 2026-10-01T12:01:10.079626+00:00
REFUSED meeting_summary -> file: the ledger records a real press at 2026-10-01T12:01:12.461336+00:00
REFUSED meeting_summary -> github: the ledger records a real press at 2026-10-01T12:01:13.342725+00:00
REFUSED project_update -> file: the ledger records a real press at 2026-10-01T12:01:15.436563+00:00
REFUSED desk_decision -> file: the ledger records a real press at 2026-10-01T12:01:15.458670+00:00
REFUSED meeting_decision -> file: the ledger records a real press at 2026-10-01T12:01:15.468246+00:00
REFUSED meeting_digest -> file: the ledger records a real press at 2026-10-01T12:01:15.477843+00:00
REFUSED meeting_followup -> file: the ledger records a real press at 2026-10-01T12:01:15.487562+00:00
REFUSED monday_brief -> file: /Users/karol/Documents/HoldSpeak/2026-10-01-brief-2026-10-01-brief-2026-10-01-21901155.md already carries it
REFUSED desk_decision -> file: /Users/karol/Documents/HoldSpeak/2026-10-01-keep-the-old-queue-read-only-for-one-week-decision-4d95ccf4.md already carries it
REFUSED project_update -> file: /Users/karol/Documents/HoldSpeak/2026-10-01-lantern-migration-rev-1-aea5b26f.md already carries it
REFUSED meeting_digest -> file: /Users/karol/Documents/HoldSpeak/2026-10-01-lantern-migration-review-philo-11-07-test-digest-2026-10-01-9159ef9d.md already carries it
REFUSED meeting_followup -> file: /Users/karol/Documents/HoldSpeak/2026-10-01-lantern-migration-review-philo-11-07-test-followup-2026-10-01-34af5653.md already carries it
REFUSED meeting_summary -> file: /Users/karol/Documents/HoldSpeak/2026-10-01-lantern-migration-review-philo-11-07-test-summary-2026-10-01-bfd28f67.md already carries it
REFUSED decision_record -> file: /Users/karol/Documents/HoldSpeak/2026-10-01-move-the-queue-in-two-steps-philo-11-07-test-decision-00bbda64.md already carries it
REFUSED meeting_decision -> file: /Users/karol/Documents/HoldSpeak/2026-10-01-move-the-queue-in-two-steps-philo-11-07-test-decision-f8f1825f.md already carries it
PHILO11_SEND_JOB_REFUSED a real send that already happened; nothing booted
exit=4
```

### Captured run — 2026-10-01T12:01:26Z

- **Command:** `sh -c H=$(mktemp -d); trap "rm -rf $H" EXIT; HOME=$H uv run pytest -q tests/unit/test_philo11_send_job.py tests/unit/test_philo9_room_job.py tests/unit/test_evidence_scratch_guard.py --basetemp $H/bt -p no:cacheprovider 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 62be92e5d517c83052da18a3f6f52d239b219866

```text
57 passed, 3 warnings in 2.45s
```

### Captured run — 2026-10-01T12:01:40Z

- **Command:** `sh -c for id in 5930904969 5930906027 5930906937; do gh api repos/karolswdev/HoldSpeak/issues/comments/$id | python3 -c "import sys,json,hashlib;c=json.load(sys.stdin);b=c[\"body\"].encode();print(c[\"html_url\"],c[\"user\"][\"login\"],hashlib.sha256(b).hexdigest(),len(b))"; done`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 62be92e5d517c83052da18a3f6f52d239b219866

```text
https://github.com/karolswdev/HoldSpeak/issues/699#issuecomment-5930904969 karolswdev 296d0de698bd85c9028e97d875f05b8b3b78db856c00f40a86e9af27b5c951ad 576
https://github.com/karolswdev/HoldSpeak/issues/699#issuecomment-5930906027 karolswdev 46b46fe148a2febb86cc5e0587e80951b3bcae53848813256bdd258f25ed4b73 239
https://github.com/karolswdev/HoldSpeak/issues/699#issuecomment-5930906937 karolswdev bc55db0d49908c177446566f1c73f458177dbc172f5f01777dbc6db0ad7164dd 253
```
