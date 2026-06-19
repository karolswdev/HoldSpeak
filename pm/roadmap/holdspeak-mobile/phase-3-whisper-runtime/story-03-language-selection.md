# HSM-3-03 — Language selection (99-language parity)

- **Project:** holdspeak-mobile
- **Phase:** 3
- **Status:** backlog
- **Depends on:** HSM-3-01
- **Unblocks:** HSM-3-05
- **Owner:** unassigned

## Problem

The desktop shipped language selection in its Phase 59 — a vendored 99-language
registry with `auto` as the default, one knob driving dictation, meetings, and
import. The mobile transcriber must reach parity: a user picking German (or any of
the 99) should get a German decode, and `auto` should detect. Without this the
mobile runtime is English-biased and not at desktop parity.

## Scope

- **In:** a language-selection surface on `WhisperKitTranscriber` accepting a
  language from the desktop's 99-language registry (or `auto`); `auto` as the
  default (byte-equivalent to today's behavior when nothing is chosen); plumbing
  the selected language into WhisperKit's decode; a vendored language registry on
  the mobile side mirroring the desktop's (one source of language identity, not a
  hand-typed subset).
- **Out:** the spoken-symbol dictionary / language-specific post-processing the
  desktop also shipped in its Phase 59 (separate concern; out of Track D). UI for
  picking the language (Phase 9/iPhone, Phase 8/iPad experience). Per-meeting vs
  global language scoping policy (a Runtime Core / settings concern).

## Acceptance criteria

Checklist. Merge gate:

- [ ] The transcriber accepts a language argument from the desktop's 99-language
      registry, plus `auto`.
- [ ] `auto` is the default; with no language chosen the decode behavior is
      unchanged from HSM-3-02 (`auto` is byte-equivalent to today).
- [ ] The mobile language registry mirrors the desktop's 99 entries (a test
      asserts the count/identifiers against the desktop registry, not a hand-typed
      list).
- [ ] Selecting a specific non-`auto` language measurably changes the decode on a
      fixture in that language (e.g. a German clip decodes as German text when
      German is selected).
- [ ] Any language in the desktop registry that WhisperKit does **not** support is
      listed as a parity gap, not silently dropped.

## Test plan

- Unit: registry parity — assert mobile registry == desktop's 99-language set
  (identifiers + count); `auto` default asserted.
- Integration: decode a committed non-English fixture (German per the desktop's
  Phase-59 real-voice proof) with the matching language selected; assert the text
  is in that language. Re-run the same clip with `auto`; assert detection lands on
  the same language.
- Manual / device: n/a beyond the fixture decodes (covered in integration).

## Notes / open questions

- Canon: the desktop's 99-language registry (its Phase 59) is the parity target.
  If WhisperKit's supported set is smaller than 99, that's a real parity gap —
  record the delta and confirm the parity bar with the owner (per the phase-status
  risk) before claiming parity is met.
- Mirror the desktop's "one combined registry, `auto` byte-identical" shape; do
  not invent a mobile-specific language id scheme.
- The spoken-symbol dictionary is explicitly out of scope here.
