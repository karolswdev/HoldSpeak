# HS-107-04 - The egress family — triage before migration

- **Project:** holdspeak
- **Phase:** 107
- **Status:** planned
- **Depends on:** none
- **Unblocks:** HS-107-05
- **Owner:** unassigned

## The thesis (the bar)

Eleven register entries, and **they are not all the same kind of
thing**. The charter counted them as eleven migratable sites; reading
them shows that is wrong, and this story exists to get the count
honest before it moves anything.

| id | site | what it actually is |
|---|---|---|
| N01 | `connector_runtime.py:144` | connector egress (mixed) |
| N02 | `plugins/gated_connector.py:229` | connector egress (dormant) |
| N05 | `intel_queue.py:485` | model call |
| N06-N09 | `intel/engine.py:221,229,300,307` | model calls |
| N10-N12 | `plugins/dictation/runtime_openai_compatible.py:126,141,190` | **transcription** |
| N13 | `cadence_telegram.py:38` | outbound message |

**N10-N12 are dictation transcription.** RFC §12 is explicit that
capture, Whisper, punctuation and rewrite stay on the low-latency path
permanently, and audio frames are never journaled. Article XI clause 5
exempts computation. Routing transcription through kernel admission
would put ceremony on the owner's hold-key path — the exact failure
Article XI clause 4 was written to prevent.

So the honest question for this family is not "how do we migrate
eleven sites" but **"which of these eleven are consequential effects,
and which are exempt computation that the census miscounted as
egress?"**

The bar: every one of the eleven ends this story either **migrated**
or **re-classified with a written reason** — and the register says
which, so nobody has to re-derive this judgement later.

## Problem

The census counted *statements that can reach the network*. That was
the right thing to count for a fence — it catches anything new. But
"can reach the network" and "is a consequential operation under
Article XI" are different properties, and treating them as identical
would either put ceremony on transcription or leave real egress
uncovered.

## Recipe

1. **Triage first, migrate second.** For each of the eleven, decide:
   consequential egress (migrate), or exempt computation (re-classify).
   The test for exempt: it is a model invocation whose *output returns
   to the caller* rather than an effect on the outside world, and it
   sits on a latency-sensitive path. Transcription is the clear case.
   Intel engine calls are the arguable ones — argue them explicitly.
2. **Model invocation and egress are distinct** — Article XI clause 1
   names them separately, deliberately. A local model call crosses no
   egress boundary. An `openai_compatible` call to a remote endpoint
   does. The register must distinguish them; today it does not.
3. **Migrate the real egress** through `actuator.egress` or a typed
   operation per site, deriving destination and data classes at
   admission so the desk's egress badge is fed from the journal
   rather than a per-surface guess.
4. **Re-classify the exempt ones in the register** with a status that
   is not "bypass" — they are not debt, they are correctly outside the
   kernel — and a one-line reason each. Update the fence test so a
   *new* transcription-shaped call still gets caught and triaged
   rather than silently inheriting the exemption.
5. **N13 (Telegram) is the clean case** — an outbound message to a
   third party. It migrates, and its receipt should name the
   destination.
6. **N01/N04-adjacent connector sites are "mixed"** — partially
   covered by `PermissionGate` today. `PermissionGate` is not a
   security boundary (it says so itself). Migrating these means the
   kernel decides and the gate stops being a second policy point —
   not two decisions for one act.

## Out of scope

- The raw-desktop primitives (§5b confinement).
- Making transcription slower to satisfy a count.
- Changing what any connector does.

## Acceptance

- All eleven resolved: each **migrated** or **re-classified with a
  written reason**, none left ambiguous.
- The final register distinguishes **model invocation** from
  **egress**, per Article XI clause 1's separate naming.
- Migrated sites: destination and data classes derived at admission;
  the egress badge fed from the journal; a refusal receipt proven for
  at least one.
- Transcription latency measured before and after — **unchanged**.
  If it moved, the story failed regardless of the count.
- The fence still catches a NEW transcription-shaped call rather than
  auto-exempting it.
- No site marked covered while its raw call still compiles reachable.
- The charter's "11 migratable" number is corrected in
  `current-phase-status.md` to whatever the triage actually found.

## Test plan

- **Unit:** triage classification per site; destination/data-class
  derivation; refusal receipts.
- **Live (evidence):** a real outbound message through the migrated
  path with its receipt; a real refusal; transcription timed on real
  metal before and after against the LAN endpoint.
- **Census:** register consistency; fence catches a new unlisted
  network call.

## Chef's notes

- The number will probably go down, not up, and that is fine. A
  register that says "7 migrated, 4 correctly exempt with reasons"
  is more useful than one claiming 11 closed doors when three of them
  were never doors.
- Resist migrating transcription to make the census look better. The
  owner will feel a slower hold-key path long before he reads a
  number.
- `PermissionGate` being "mixed" is the interesting case: it is real
  enforcement for cooperating code and no barrier at all to anything
  else. Migrating past it should not leave two policy decisions for
  one act.
