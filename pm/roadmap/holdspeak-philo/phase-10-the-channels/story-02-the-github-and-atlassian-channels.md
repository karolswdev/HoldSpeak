# PHILO-10-02 - The GitHub and Atlassian channels (and the nudge)

- **Project:** holdspeak-philo
- **Phase:** 10
- **Status:** backlog
- **Depends on:** PHILO-10-01; the owner's answers to Q2, Q3 and Q6
- **Unblocks:** PHILO-10-05, PHILO-10-06
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Codex Astra checks
- **Closure finding:** `docs/internal/philo/phase-10/grounding/README.md` F3, F4, F5, F8, F9, F15; Codex Astra r1 findings 3–5
- **Design:** `design/send-lifecycle.md` sections 3–6 (binding)
- **Canvas:** none

## Problem

`gh` and `acli` are on this machine (`gh` 2.86.0, `acli` 1.3.36-stable; `docs/internal/philo/phase-10/grounding/cli-probe.out.txt`), and the Room uses them only to read, except the nudge. The nudge records a timeout as "failed" and offers Send again (`holdspeak/kernel/subprocess_exec.py:282-289`; `holdspeak/services/project_steward_service.py:2049-2066`; `holdspeak/services/steward_contract.py:649-660`, F4), and its `gh` op has no parent (`subprocess_exec.py:249-260`, F5). `acli` cannot make or change a Confluence page (F8).

## Scope

- **In:** the body through a private 0600 payload file for every command, argv without the body (design section 3); the GitHub channel (a comment on an issue or a pull request, `--body-file <path>`; the gist parked); the Jira channel (`acli jira workitem comment create --key <one canonical key> --body-file <path> --json`; `--key` accepts a list, so a second key is refused `jira_key_not_single`; never `--jql`, `--filter` or `--edit-last`; stdin is not accepted, probed); the Confluence channel as Q3 rules (`acli confluence blog create --from-json <0600 file with the title and the body> --json`, no title in argv; if the real-account leg shows `--from-json` cannot carry the title, the named limit of design section 3 or Confluence to the BACKLOG); the GitHub identity: the destination freezes `{host, login}`, the send reads `gh api user --hostname <host>` before the boundary and refuses `github_identity_changed` / `github_not_logged_in` by name (design section 5); the outcome mapping with the pinned known-non-delivery lists (design section 4); the size limits pinned by real sends; switch → status → create under the existing acli lock (`holdspeak/services/jira_provider.py:175`, `:570`; `holdspeak/services/confluence_provider.py:544-580`); each command a `subprocess.exec` child of the send, under the authenticated owner principal, the parent and the broker threaded through the seam (design section 6); the destination names its connection from `watch_provider_connections` and shows its Phase 9 B1 state; the nudge sends through the GitHub channel's path, parents its child and records an unknown result as unknown. **Moved from story 01 (round two, Codex Astra r1 finding 5):** the CLI seam itself — each CLI channel's `WriteConnectorManifest` + `plan` + `interpret` in the registry, and the owner principal, the parent and the broker threaded through `build_gated_connector` → `run_subprocess_operation` (design section 6) — built with its first user; the reuse of story 01's `private_payload_file` and `redact` (excerpts and secrets). **The steward prepares a send** (Q5): a steward effect kind that calls `channel.prepare` as its run's child, under the steward's identity; it never sends. Each channel's native proof pinned by one real send to a Q6 target (the `--json` answer shapes are unknown today).
- **Out:** Confluence page create or update; Slack; the other outbound paths (BACKLOG).

## Acceptance criteria

- [ ] Each channel's send is one `channel.send` with its CLI children parented; red on main for the nudge's child (F5).
- [ ] A nudge whose `gh` call times out is UNKNOWN in its record and its receipt and is not offered for Send again (red on main, F4).
- [ ] The argv of each channel starts with its manifest prefix and carries no body; the payload file's bytes equal the preview's digest; a plan that would add `--jql`, `--filter`, `--edit-last` or a second key cannot be built.
- [ ] An Atlassian send runs inside the acli lock; a second send waits for it (a fence with two concurrent sends).
- [ ] A GitHub destination saved as login A, with `gh` now logged in as B, is refused `github_identity_changed` before any dispatch (a fence through the real provider with synthetic auth answers; the Phase 9 connection row rewritten from A to B does not change the verdict).
- [ ] The Confluence title is inside the frozen payload digest and absent from argv and the subprocess receipt (a sentinel fence), or the named limit is recorded.
- [ ] An unpinned nonzero exit, exit 0 without a valid URL or id, and a timeout are UNKNOWN; only a pinned error is FAILED.
- [ ] (Moved from story 01.) No body in argv or a subprocess receipt (a sentinel fence); each CLI child runs under the authenticated owner principal with the send as its parent, through the broker.
- [ ] (Moved from story 01; Q5.) The steward prepares a send as its run's child under its own identity; its attempt to send is refused `owner_principal_required` with a receipt.
- [ ] The real-account leg (separate from the rehearsals; the owner authorizes each target, Q6): one real send per channel, its proof read back from the far side; or the limit named. `gh` and `acli` keep their logins in the macOS keychain (F15): the leg runs on his own session.

## Effort (not a promise)

PROVISIONAL: 2–3 engineering days.

## Test plan

- **Integration:** fences through the real hub with a recording runner minted through each real `plan`; the nudge's red fences on main.
- **Real sends:** as Q6 rules, redacted at capture.

## Notes

- 2026-09-28 — the CLI seam, its outcome clauses and the steward's prepare moved here from story 01 (round two of story 01, Codex Astra r1 finding 5).
- 2026-09-28 — round three: Codex Astra r2 conditions 2 and 3 added.
- 2026-09-28 — round two: amended on Codex Astra r1 DO-NOT-RATIFY (`checks/charter-astra-r1.md`); bound by `design/send-lifecycle.md`.
- 2026-09-28 — drafted by the Fedaykin docs lane for Muad'Dib; unratified. Nothing was sent in the grounding (no account on an isolated HOME).
