# HS-59-03 — Docs: languages + the dictionary

- **Project:** holdspeak
- **Phase:** 59
- **Status:** done
- **Depends on:** HS-59-01, HS-59-02
- **Unblocks:** HS-59-04
- **Owner:** unassigned

## Problem
Both features die in the dark without docs: the language knob's honest
auto-detect note and the dictionary's attach semantics need plain words.

## Scope
- **In:** the typing guide learns both (the knob's location + what "auto"
  means + the short-utterance honesty note + that meetings and import use
  the same knob; the dictionary with attach semantics and two or three
  real examples). README's Dictate cell + where-next touched only if it
  earns it. Canon-clean (the voice guard is a live test).
- **Out:** localization of HoldSpeak's own UI.

## Acceptance criteria
- [x] Product-tense; voice guard green (zero dashes in the new prose,
      canonical names). Home decision recorded: both features documented
      in the User Guide beside the punctuation table they extend (the
      canon's extend-don't-fragment rule), with a Getting Started pointer.
- [x] The auto-detect honesty note stated plainly ("a few words in one
      language can be detected as a neighboring one").
- [x] Doc slice green (81). See `evidence-story-03.md`.

## Test plan
- Doc-guard slice + full suite.
