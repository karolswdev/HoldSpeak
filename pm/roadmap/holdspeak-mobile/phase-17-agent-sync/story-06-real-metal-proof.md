# HSM-17-06 — The real-metal proof (cabled iPad + a live coder on the Mac)

- **Project:** holdspeak-mobile
- **Phase:** 17
- **Status:** todo — the phase gate.
- **Depends on:** HSM-17-02..05 (the full loop). The build/deploy/verify loop
  (`apple/scripts/meeting-capture-device.sh` + the [[reference_xcode_beta_swift_syntax_break]] workaround).
- **Unblocks:** HSM-17-07 (docs follow the proven loop).
- **Owner:** unassigned

## Problem

Per [[feedback_verify_on_device_not_seeded]] and [[feedback_prefer_real_metal_proof]], agent sync is only
"done" when the whole loop runs **on the cabled iPad against a live Claude/Codex session on the Mac** —
not seeded states, not a no-LLM plumbing pass. This is the owner-witnessed proof.

## The proof (owner-witnessed)

1. **Inject ourselves:** install the hooks (HSM-17-02) into a real Claude Code session on the Mac; start
   it on a real repo.
2. **Surface:** drive the coder to a genuine question (a clarification / tool-permission prompt). Confirm
   it appears on the cabled iPad as an agent primitive with the glaring *"needs you"* treatment and the
   full question.
3. **Answer, four ways** (across one or more questions):
   - spoken (WhisperKit) → injected, coder continues;
   - typed → injected;
   - dropped context (a meeting/artifact/note onto the question) included in the answer;
   - **AI-drafted on-device** → approved → injected. (Endpoint draft too if convenient.)
4. **Loop integrity:** each injected answer lands in the live session and the primitive returns to
   `working`; ending the session removes it from the desk.
5. **Egress + air-gap honesty:** the egress badge is correct for each path; the on-device draft runs with
   no network.
6. Repeat the surface+answer step once with **Codex** to prove both agents.

Capture screenshots / a short recording of the loop for the closeout and the docs (HSM-17-07).

## Acceptance criteria

- [ ] On the cabled iPad Air M4 against a live Claude Code session on the Mac: a real question surfaces,
      is answered by **each** of the four modes (at least once each across the session), injected, and the
      coder continues — owner-witnessed.
- [ ] The on-device AI-draft runs with **no network** (air-gap honest); egress badges are correct.
- [ ] Codex proven for at least the surface + one answer.
- [ ] No stale ghosts: ended sessions leave the desk.
- [ ] Artifacts (screenshots / recording) captured under the phase `screenshots/`.

## Test plan

- The proof IS the test (real metal). Pre-flight on Simulator with seeded states (HSM-17-03) to catch UI
  regressions before the cabled run. If a Linux/`.43` coder is in scope, run that leg live per
  [[feedback_linux_proofs_on_43]] rather than code-only.
