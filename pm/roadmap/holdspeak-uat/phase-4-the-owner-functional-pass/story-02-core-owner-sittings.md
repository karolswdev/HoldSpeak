# HSU-4-02 — Core owner sittings (campaigns 1–5)

- **Project:** holdspeak-uat
- **Phase:** 4
- **Status:** ready
- **Depends on:** HSU-4-01
- **Owner:** owner (verdicts) + agent (debrief/triage)

## Problem

The early MVP needs direct owner evidence across its daily loops, with usability
treated as load-bearing. Authored coverage and machine probes cannot supply that
evidence.

## Scope

- Run campaigns 1–5 in order: React desktop foundation, React voice/dictation,
  React meetings/aftercare, target-qualified agents/automation, and the exact
  flagship Swift app including its independent native Desk leg.
- Finish and triage each sitting before beginning the next.
- Record every fail/partial/observe with direct surface evidence and rank fixes
  by owner pain and task blockage.
- No product fix during the active sitting; findings enter normal product work.

## Acceptance criteria

- [ ] Campaign 1 has a completed debrief and all findings triaged.
- [ ] Campaigns 2–4 have direct owner verdicts across their declared protocol-v2
      target/form-factor slots and all findings triaged.
- [ ] Campaign 5 records exact flagship target/form-factor/bundle/build/device/OS,
      has pairing-verified physical iPhone/iPad attestations, and directly tests
      Swift Desk; no React viewport, companion, or classic evidence is substituted.
- [ ] React Desk and Swift Desk are accepted independently before any parity
      conclusion joins their results.
- [ ] No core sitting has an untriaged fail, partial, or observation.

## Test plan

- Manual: the five guided sittings themselves.
- Evidence: retained sitting snapshots, verdicts, screenshots, logs, debriefs,
  and triage dispositions under `uat/_runs/` plus selected phase assets.
