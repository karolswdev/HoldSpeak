# pi is the third harness: the real-metal walk

Walked 2026-10-08, 15:36 to 16:00 MDT, on branch `feat/pi-harness` (worktree `wt-pi-harness`, base `09ac79a5e`).

## The rig

- One HOME (`mktemp -d -t hs-pi-rig`), removed at the end. Inside it: `CODEX_HOME`, `CLAUDE_CONFIG_DIR`, `TMUX_TMPDIR`, `HOLDSPEAK_PEOPLE_KEYSTORE_FILE`, `GH_CONFIG_DIR`, the hub's config and database, and pi (`npm install --prefix $H/prefix @earendil-works/pi-coding-agent@1.1.0`, 121 packages, 8 s). `GIT_CONFIG_NOSYSTEM=1`. The HOME's `.gitconfig` resets the credential helpers and allows only `!gh auth git-credential`. `GH_TOKEN` from `gh auth token`.
- The hub: `python -m holdspeak.main web --no-open` on port 8797. Its log names the database inside the rig HOME.
- The model: `qwen3.8-27b` at `http://192.168.1.43:8080`, key `local`, set on the first-run face ("Use a server on my network", Check: `READY · qwen3.8-27b · TOOLS`, "Use this for summaries": `USING · QWEN3.8-27B · SUMMARIES · DEFAULT SET`). pi's engine is the route of `agent.code`, which inherits that default.
- The repository: `karolswdev/holdspeak-dayone-rehearsal-1558`, picked on the Door (shot 01), registered at Create (shot 02), cloned by the hand (`project.repository.clone`, its receipt in `hub-launch-record.json`).
- Headless Chromium (Playwright) at 1440 x 900 and 393 x 852. Owner gestures by script, each on the face, except where the walk says otherwise.

## The five proofs

| Proof | What the hub and pi recorded | Evidence |
|---|---|---|
| (a) pi started in its worktree and received the brief | Launch `launch_acb5cacbab4b4103`: `state: launched` → `registered`, `profile_id: pi-default`, `gate: gated`, `control_mode: yolo`, `instruction_state: sent`, `brief_sent_at: 21:46:46Z` (2 s after the launch). The rider registered `pi:01a11d7b-…` from the worktree `…/hs-project_item-pitem_d25d3fc0…` with the Story claim `claimed_by: rider:pi` and `tmux_pane: %0`. The transcript's first user message is the brief. Lane: `BRIEF 15:46`, `SENT · 15:46`. | `evidence/hub-launch-record.json`, `evidence/hub-agent-session-pi.json`, `evidence/pi-session-transcript.jsonl`, `08-lane-asks-1440.png` |
| (b) it called a HoldSpeak tool | `mcp__holdspeak__project_list` at 15:46, answered by the hub with the rig's Project (`proj-e5abdabc568b`, "pi rig: the third harness"), with the launch credential (`agent:launch:launch_acb5…`, palette CONDUCTOR). Lane rail: `CALL mcp__holdspeak__project_list`. | `evidence/pi-session-transcript.jsonl`, `evidence/hub-agent-credentials.txt`, `08-lane-asks-1440.png` |
| (c) one shell call held, the deny reached the model, the command did not run | `cat /etc/hosts` held at 15:47:00 (`path_outside_worktree`, `OUTSIDE THE WORKTREE · /etc/hosts`). Denied from the Needs row at 393 at 15:50:00. pi's tool result: `denied from the desk: OUTSIDE THE WORKTREE · /etc/hosts. The owner denied this call. Do not try it again in a different form.` (`isError: true`, no output). The model wrote `hosts: not read` and did not retry. A second hold (`git -c user.name=… commit`, `NOT READ · git_global_option`, CUT) was denied from the Needs window at 1440 at 15:51:17. | `05-needs-held-1440.png`, `05-needs-held-393.png`, `06-needs-denied-393.png`, `07-needs-held-commit-1440.png`, `evidence/hub-gate-proposals.txt`, `evidence/hub-kernel-operations.txt`, `evidence/pi-session-transcript.jsonl` |
| (d) its turn end reached the lane | The turn ended at about 15:51:40 with a question. The lane: `PI ASKS · 1 MIN` with the agent's words, station `ASKS now`, `HELD 2 HELD · 2 DENIED`, `COMMIT 1` (`45e2b1a`), `FILES CHANGED · 1 NOTES.md`. | `08-lane-asks-1440.png`, `08-lane-asks-393.png`, `08-lane-asks-full-393.png` |
| (e) Stop from the desk killed pi and its hook | The owner's Answer on the lane at 15:55 asked for `head -1 /etc/shells`: held at 15:55:49, its hook alive (`pid 52373/52374`, group `47870` with `pi`). Stop pressed twice on the lane: 15:56:22.6 and 15:56:23.3. At 15:56:32: no process in group 47870, no `pi`, no `gate hook --agent pi`, no tmux server. The launch credential was revoked at 15:56:23.5. Lane: `STOPPED · 15:56 · BY YOU`. | `evidence/e-stop-process-group.txt`, `11-lane-held-before-stop-1440.png`, `12-lane-stopped-1440.png`, `evidence/hub-agent-credentials.txt` |

Also: Get Info for pi (`pi · AGENT · VERSION 1.1.0 · HOOKS IN · SIGN-IN SIGNED IN`, `09-get-info-pi-1440.png`, `09-get-info-pi-393.png`); the Conductor drawer with the pi member and the live pi agent, both with the π sprite (`10-conductor-drawer-1440.png`); the launch folder's modes (`evidence/pi-launch-folder-modes.txt`: folder 0700, `models.json`, `mcp.json`, `holdspeak.json` 0600) and its files (`evidence/pi-launch-*.json`; no key, no token).

## Timings

| What | Time |
|---|---|
| pi install into the rig | 8 s |
| Hub start to healthy | 2 s |
| LAN Check to READY | within the 6 s wait |
| Door: Create Project with the repository | 5 s |
| `POST /api/agent/hand` (clone + worktree + spawn) | 15:46:42 → 15:46:44, 2 s |
| Launch → brief typed (`brief_sent_at`) | 2 s |
| Brief → first gated call (`pwd && git status …`, passed by YOLO) | 15:46:59, 13 s |
| First hold (`cat /etc/hosts`) | 15:47:00 |
| Deny → the model's next call (`write NOTES.md`) | 15:50:00 → 15:50:02 |
| Second deny → plain commit (passed by YOLO) | 15:51:17 → 15:51:22 |
| Turn end (ASKS) | about 15:51:40 |
| Stop (second press) → group gone | 15:56:23.3 → by 15:56:32 (the check time; not measured closer) |

## Corrected after Astra round 1

- The walk's approved `Write` (`oNeSc8bU…`, operation `op_0fd0e2720…`) stayed `claimed`: completion matched the literal `Write`. Fixed in r1 (`test_an_approved_pi_write_reaches_its_terminal_receipt`).
- The walk ran in YOLO only. Secure MCP holds, outside reads and Stop after a dead leader are fenced in `tests/unit/test_pi_harness_r1.py`, not walked on metal.

## What the walk did not do through the face

- The hand itself: a Room ITEMS row (a project item) has no Hand to agent verb, so the walk sent `POST /api/agent/hand {kind: project_item, profile: pi-default}`, the body the confirm line sends. The confirm line's three-way turn to PI is proven in `web/src/desk/hand/__tests__/hand.test.tsx`, not on the live hub.
- The GitHub "Use it" on the first-run Connections card: the walk called `POST /api/onboarding/connections/use` (the card's route) after gh rewrote the token-less `hosts.yml` to `{}`.
- The item: `POST /api/projects/{id}/items`.
