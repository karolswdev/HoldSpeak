# HSM-23 — the storage rider (two checks for the staged couch session)

Ride-alongs for the session that runs
[`HSM-18-06-WALK.md`](../phase-18-ipad-dictation-contracts/HSM-18-06-WALK.md),
[`HSM-19-07-WALK.md`](../phase-19-ipad-meeting-contracts/HSM-19-07-WALK.md) and
[`HSM-21-WALK-RIDER.md`](../phase-21-honest-everywhere/HSM-21-WALK-RIDER.md) — same hub,
same pairing, ~2 extra minutes. Both checks were already proven live from the connected
simulator (see [`evidence-story-03.md`](./evidence-story-03.md)); the rider verifies the
same truths on glass.

**R1 — the iPad states its own health (23-03).** Open Settings → READINESS. EXPECT:
**This iPad** shows the Store chip green (**ok · schema v2**), mic and models stated
plainly, the app version under the header. Below it, the paired desktop card carries the
hub's overall chip (**Ready** or **Needs attention**, matching what `holdspeak doctor`
says on the Mac at that moment) and the doctor's own sections row by row, warn rows
amber.

**R2 (optional, the refusal on glass) — a newer store is named, never eaten.** Only if
the session has a minute to spare: with a future-version `meetings.sqlite` seeded into
the app container (the evidence file's sqlite3 one-liner), relaunch. EXPECT: the home
banner reads **Store written by a newer HoldSpeak (v7 > v2), left unread**, and the
Settings Store chip reads **newer than this app · v7 > v2** in amber. Delete the seeded
file afterwards; the store recreates on the next launch.

## The trace

```
R1 readiness panel:   PASS/FAIL — <store chip / hub overall seen, vs doctor on the Mac>
R2 refusal (optional): PASS/FAIL/SKIPPED — <banner + chip wording seen>
```

PASS on R1 closes HSM-23-05 and the phase (R2 is a bonus, already machine-proven).
