# HSM-25-03 — The live proof + docs

- **Status:** backlog
- **Depends on:** HSM-25-01, HSM-25-02
- **Unblocks:** none (closes the phase)

## Problem

The phase's claim — flip one toggle and the desk runs on the phone — has
to be walked on real metal (the standing rule: seeded sim demos aren't
proof), then taught at the entry points.

## Scope

- In: the live walk, on the real hub with the real device (or the
  simulator against the live hub for the wire beats + the device for the
  felt beats, per the HSM proof pattern):
  1. Toggle ON in Settings — the device appears in `holdspeak doctor`'s
     "Mesh edges" line and the hub's models door, live, under its mesh
     name.
  2. A meshNode profile naming the device (authored once, hub-side) runs
     a desk ask on the Mac/web — the badge names the device; the device's
     serving counter increments; the run's answer came from the DEVICE's
     model.
  3. Toggle OFF (and separately: kill the app) — pickers/doctor read
     offline within the window; a forced run refuses fast (< 5s), naming
     the device.
  Screenshots (device Settings serving state; hub badge; offline picker)
  + outputs committed to `screenshots/`.
- In: docs at the entry points — `apple/README.md` (the serving toggle),
  the mobile ARCHITECTURE note, desktop `docs/MODELS.md` ("your phone can
  serve too" sentence in the mesh-edge section); voice/drift guards
  green.
- In: phase close — exit criteria re-run, `final-summary.md`, mobile
  roadmap README pointer + "Last updated".
- Out: background serving, multi-device simultaneous-serve walk (works by
  construction; a rider only on owner ask).

## Test plan

- The walk IS the proof (outside the sandbox; hub restarted on merged
  code with `HOLDSPEAK_WEB_PORT=8765` pinned).
- Full `swift test` + desktop guards green at close.

## Done when

The walk's three beats pass with artifacts committed, the docs teach the
toggle honestly, and the phase closes with the cadence complete.
