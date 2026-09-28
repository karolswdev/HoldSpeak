# PHILO-10-02 - The GitHub and Atlassian channels (and the nudge)

- **Project:** holdspeak-philo
- **Phase:** 10
- **Status:** backlog
- **Depends on:** PHILO-10-01; the owner's answers to Q2, Q3 and Q6
- **Unblocks:** PHILO-10-05, PHILO-10-06
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Codex Astra checks
- **Closure finding:** `docs/internal/philo/phase-10/grounding/README.md` F3, F4, F5, F8, F9
- **Canvas:** none

## Problem

`gh` and `acli` are on this machine (`gh` 2.86.0, `acli` 1.3.36-stable; `docs/internal/philo/phase-10/grounding/cli-probe.out.txt`), and the Room uses them only to read, except the nudge. The nudge records a timeout as "failed" and offers Send again (`holdspeak/kernel/subprocess_exec.py:282-289`; `holdspeak/services/project_steward_service.py:2049-2066`; `holdspeak/services/steward_contract.py:649-660`, F4), and its `gh` op has no parent (`subprocess_exec.py:249-260`, F5). `acli` cannot make or change a Confluence page (F8).

## Scope

- **In:** the GitHub channel (a comment on an issue or a pull request, the body in argv; a secret gist only if Q2 (b)); the Jira channel (`acli jira workitem comment create --key … --body … --json`, never `--jql` or `--filter`); the Confluence channel as Q3 rules (`acli confluence blog create …`); switch → status → create under the existing acli lock (`holdspeak/services/jira_provider.py:175`, `:570`; `holdspeak/services/confluence_provider.py:544-580`); each command a `subprocess.exec` child of the send (the parent link added to the subprocess op); the destination names its connection from `watch_provider_connections` and shows its Phase 9 B1 state; the nudge sends through the GitHub channel's path, parents its child and records an unknown result as unknown. Each channel's native proof pinned by one real send to a Q6 target (the `--json` answer shapes are unknown today).
- **Out:** Confluence page create or update; Slack; the other outbound paths (BACKLOG).

## Acceptance criteria

- [ ] Each channel's send is one `channel.send` with its CLI children parented; red on main for the nudge's child (F5).
- [ ] A nudge whose `gh` call times out is UNKNOWN in its record and its receipt and is not offered for Send again (red on main, F4).
- [ ] The argv of each channel starts with its manifest prefix and carries the previewed body; a plan that would add `--jql` or `--filter` cannot be built.
- [ ] An Atlassian send runs inside the acli lock; a second send waits for it (a fence with two concurrent sends).
- [ ] One real send per channel to a Q6 target, its proof read back from the far side; or the limit named.

## Effort (not a promise)

PROVISIONAL: 2–3 engineering days.

## Test plan

- **Integration:** fences through the real hub with a recording runner minted through each real `plan`; the nudge's red fences on main.
- **Real sends:** as Q6 rules, redacted at capture.

## Notes

- 2026-09-28 — drafted by the Fedaykin docs lane for Muad'Dib; unratified. Nothing was sent in the grounding (no account on an isolated HOME).
