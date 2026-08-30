# HS-150-06 - The composer (mic, @-refs, send/stop, / verbs)

- **Project:** holdspeak
- **Phase:** 150
- **Status:** done
- **Depends on:** HS-150-05
- **Unblocks:** HS-150-08
- **Owner:** unassigned

## Problem

The foot of the thread is where the manager actually works: speak or
type, point at the desk with `@`, send, stop. Art. IV (voice arms,
never fires), Art. VII (no modals), the mic-on-every-input law
(settled-design D6).

## Scope

### In (D6)

- Composer component in the pullout foot: textarea + `MicButton`
  (click-to-toggle; text lands in the field, never auto-sends),
  Enter sends / Shift+Enter newline / Esc stops, Send↔Stop while
  streaming.
- `@` → `InletAutocomplete` extended from zones to primitives
  (meeting, note, artifact, decision, person by title); selection adds
  a ref chip above the field; chips are the attachments; chips are
  removable; the chip set is sent as `refs[]`.
- `/` → the verb palette filtered to thread verbs (registry, not a
  second command system).
- Edit-and-resend on a user row reuses the composer inline (no modal)
  and calls `/branch`.

### Out

File upload / PDF extraction (no upload route exists — deferred to a
DC-02 rider); annotations (DC-03); TTS (DC-04).

## Acceptance criteria

- [ ] Real-Chromium probe: type → Enter sends; Shift+Enter inserts a
      newline; Esc during streaming aborts; focus returns to the field
      after done (double-rAF precedent).
- [ ] Mic toggles on/off, transcript lands in the field, nothing is
      sent until Enter.
- [ ] `@Ewa` lists the person; selecting adds a chip; the turn's refs
      are frozen and shown in the assistant row's provenance.
- [ ] `/keep`, `/fork`, `/stop` run the registry verbs.
- [ ] 393px: the composer never overflows horizontally; chips wrap.

## Test plan

- **Unit:** vitest `Composer.test.tsx` (keys, chips, verb filter) +
  `InletAutocomplete.test.tsx` extension.
- **Integration:** the glass probe from 05 extended with a composer leg.
- **Manual / device:** owner shot review at close.

## Notes / open questions

Voice-arms law: the mic must never call Send; a future call-mode
(DC-04) is an explicit per-thread toggle.
