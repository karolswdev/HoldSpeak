# HSM-21 — the honesty rider (three checks for the staged couch session)

Ride-alongs for the session that runs
[`HSM-18-06-WALK.md`](../phase-18-ipad-dictation-contracts/HSM-18-06-WALK.md) and
[`HSM-19-07-WALK.md`](../phase-19-ipad-meeting-contracts/HSM-19-07-WALK.md) — same hub,
same pairing, ~5 extra minutes. Every check below was already proven live from the
simulator (see the per-story evidence); the rider verifies the same truths on glass.

**H1 — the badge tells the object's truth (21-01).** On the desk, open a connector's
pull-out (Slack or GitHub). EXPECT: the header badge reads **Cloud · <name>** (amber).
CONTROL: open a note's pull-out — **On device** (green). Then, in the Companion shell,
preview a dictation. EXPECT: the receipt chip reads **Local + <your Mac>** in amber,
never green.

**H2 — readiness is real (21-03).** With no `companion_github_repo` on the hub
(Settings → Connections), open the GitHub tile. EXPECT: "set up on your desktop", and
an action-item act sheet does NOT offer GitHub. Set the repo on the web settings page,
re-sync the desk. EXPECT: the tile flips to "via your desktop · <host>" and the act
sheet offers GitHub again.

**H3 — the posture chip moves with the hub (21-04).** With actuators off, the shell
header reads **Local only**; flip Allow actuators in the web settings and relaunch the
shell. EXPECT: **Writes need approval** — and the web header chip says the same words.

## The trace

```
H1 badge truth + control: PASS/FAIL — <connector seen / note control>
H2 readiness flip:        PASS/FAIL — <before/after states>
H3 posture flip:          PASS/FAIL — <postures seen, both surfaces>
```

PASS×3 closes HSM-21-05 and the phase.
