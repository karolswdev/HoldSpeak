# Evidence — HSM-21-03 — GitHub-repo honesty on the desk

**Status:** done (2026-07-03), on `holdspeak-mobile/hsm-21-03-github-honesty`.

## 1. The ratified design (recorded)

The repo is desktop configuration, like every credential: the iPad does **not** grow a
repo field; `DeskHostLink.propose` keeps its `{text, title}` body and the hub's
`companion_github_repo` fallback is THE path (web settings + `system/settings.py`
shipped it pre-open). What this story fixes is that **readiness tells the truth**.

## 2. The honest tile (`DeskDioramaStage.swift` + `DeskPrimitive.swift`)

- `DeskHostLink.connectorStatus()` reads the existing HS-77-03 route
  (`GET /api/desk/actuators/status` — booleans only, credentials never ride); refreshed
  on every desk sync. `nil` (unreachable / older hub) keeps the last known truth —
  an unread status is not evidence of unconfigured.
- `ConnectorPrimitive` now carries **paired** and **configured** as separate truths:
  paired-but-unconfigured renders "set up on your desktop" (subtitle, section, action)
  instead of presenting ready; `accepts` stays empty so nothing can be dropped into a
  doomed send.
- The act sheet lists **only connectors whose send can complete** — a GitHub row with no
  repo on the host was a guaranteed 400 at approve time.

## 3. The live-hub proof (control vs treatment, ONE hub, config flipped mid-run)

```
1. status (A, no repo) -> 200; {'slack_configured': True, 'webhook_configured': False, 'github_configured': False}
2. github propose (A)  -> 400; 'No GitHub repo (set companion_github_repo on the host, or pass repo)'
3. flip config -> companion_github_repo=karolswdev/HoldSpeak
4. status (B, repo set) -> 200; {'github_configured': True, …}
5. github propose (B)  -> 200; status=proposed, preview='Open a GitHub issue in karolswdev/HoldSpeak: "Phase 19 follow-up"'
```

The paired simulator desk rendered both truths against that live hub
(`hs.peer.*` written via `simctl spawn defaults`, the new
`HS_DESK_OPEN=connector-github` seed opening the pull-out):

- [`hsm-21-03-github-unconfigured.png`](./screenshots/hsm-21-03-github-unconfigured.png)
  — config A: **"set up on your desktop"**, the "Set up on your desktop" action, no
  accepts (and the 21-01 `Cloud · github` badge on top — the stories compound).
- [`hsm-21-03-github-configured.png`](./screenshots/hsm-21-03-github-configured.png)
  — config B, same hub: **"via your desktop · 127.0.0.1"**, sends enabled.

The unconfigured render also proves the fetch is live: with `connConfigured` unread the
tile would have fallen back to paired-only "ready".

## Honest boundaries

- Slack/webhook get the same honesty for free (same status route, same tile logic);
  the sim proof exercised github (the audited case).
- The on-glass tap (drop → act sheet showing only ready connectors) rides the 21-05
  walk rider.

## Suites

`swift test` **428/8-skip/0-fail** · meeting-capture sim build **BUILD SUCCEEDED** —
after the change.
