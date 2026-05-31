# Evidence — HS-25-03 — Threat Model + Encryption-at-Rest Stance

- **Shipped:** 2026-05-31
- **Commit:** (pending — same commit as this evidence file)
- **Owner:** Claude (agent)

## What shipped

`docs/SECURITY.md` — HoldSpeak's threat model: data classes, storage/at-rest
posture, trust boundaries, every egress point, secrets handling, and the
recorded encryption-at-rest decision. Linked from the root README and added to
the roadmap source canon.

## Files touched

- `docs/SECURITY.md` — **new**. §1 data classes, §2 storage + encryption-at-rest
  decision, §3 trust boundaries, §4 egress table, §5 secrets, §6 threat-model
  summary, §7 reporting.
- `README.md` — "Where to go next" links to `docs/SECURITY.md`.
- `pm/roadmap/holdspeak/README.md` — source-canon list includes `docs/SECURITY.md`.

## Verification artifacts

This is a docs/decision story — "Tests ran" discharges as n/a. The substantive
verification is that the claims match code; cross-checked:

```
$ grep -n DEFAULT_DB_PATH holdspeak/db.py
26: DEFAULT_DB_PATH = ~/.local/share/holdspeak/holdspeak.db          # §1, §2

$ grep -n CONFIG_FILE holdspeak/config.py
12: ~/.config/holdspeak/config.json                                  # §1, §5

$ grep -n "embedding BLOB" holdspeak/db.py
148: speakers.embedding BLOB (float32)                               # §1 voiceprint

# Egress sites enumerated in §4:
intel.py:538/632  OpenAI client + chat.completions.create           # cloud intel
intel_queue.py:345  urlopen(failure webhook)                        # queue stats only
connector packs  subprocess (gh/jira)                               # entity IDs, opt-in
device_audio.py:519  verify_psk                                     # device link

# Confirmed NO network calls in activity_history.py (read-only snapshots).
```

Egress claims also reflect the *hardened* behavior from HS-25-01 (no silent
local→cloud) and HS-25-02 (off-loopback token gate), not the pre-phase state.

## Acceptance criteria — re-checked

- [x] `docs/SECURITY.md` enumerates data classes, storage, trust boundaries, egress.
- [x] Encryption-at-rest decision recorded with rationale + residual risk + revisit trigger.
- [x] Root `README.md` links to it.
- [x] Roadmap source-canon list includes it.
- [x] Claims cross-checked against code.

## Deviations from plan

None. Decision taken on the recorded default (document the stance, recommend
full-disk encryption, defer app-level encryption) per the user's "proceed on the
default" steer.

## Follow-ups

- If HoldSpeak ever goes multi-user/server or holds third-party data, open a new
  story for app-level DB encryption (SQLCipher) per the §2 revisit trigger.
