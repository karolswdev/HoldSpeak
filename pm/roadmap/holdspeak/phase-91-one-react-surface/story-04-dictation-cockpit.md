# HS-91-04 — The Dictation cockpit in React

- **Project:** holdspeak
- **Phase:** 91
- **Status:** done
- **Depends on:** HS-91-01, HS-91-02
- **Unblocks:** HS-91-09
- **Owner:** unassigned

## Problem

Dictation is composed from Astro sections plus many imperative modules that
mutate shared DOM and hold distributed state. It is a core daily surface and
must feel as immediate and spatially coherent as DeskOS without losing its
mature runtime, memory, knowledge, dry-run, journal, and microphone behavior.

## Scope

- In: React `/dictation`; readiness, blocks, runtime, dry-run, memory,
  knowledge, journal, hooks, project-root and activity-nudge sections; mic and
  speak-to-fill behavior; typed route-local state/hooks; shared runtime frames.
- Out: dictation pipeline/backend changes; new voice features; native hotkey
  implementation.

## Acceptance criteria

- [x] Every Dictation ledger verb and failure state passes against existing
      APIs, including dry-run, correction ritual, project knowledge, journal,
      runtime save/rebuild, agent summary and discovery nudges.
- [x] One React state graph owns section selection and shared runtime data; no
      module mutates DOM by id/class or injects product HTML strings.
- [x] DeskOS-aligned hierarchy makes readiness, active work and advanced depth
      legible without flattening the expert controls.
- [x] Mic permissions, active/listening states, focus restoration and reduced
      motion are exercised in tests.
- [x] Existing dictation integration suites remain green and cohort Astro/JS
      bootstraps are deleted.

## Test plan

- Unit: hooks/reducers for each Dictation section and runtime frames.
- Integration: existing dictation pytest suites plus Playwright dry-run,
  correction, project-root and journal flows.
- Manual / device: real hold-to-talk and dry-run walk on macOS; compare the
  actual Swift Dictation surface separately.

## Notes / open questions

Break implementation into internal component modules, but ship as one route
cohort so users never encounter half React/half imperative state on Dictation.
