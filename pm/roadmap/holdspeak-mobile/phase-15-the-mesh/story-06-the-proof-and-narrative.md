# HSM-15-06 — The Proof: air-gapped value + the launch narrative

- **Project:** holdspeak-mobile
- **Phase:** 15
- **Status:** backlog
- **Depends on:** HSM-15-01 (dictation), HSM-15-02 (mesh Workbench), HSM-15-03 (mesh queue),
  HSM-15-05 (the approval/egress contract). This is the phase's capstone evidence.
- **Owner:** the owner drives the session; the agent produces the assets.

## Vision (owner)

> "Deliver enough LinkedIn-worthy material to start promoting this — what I did as a senior
> software architect to increase my efficiency using the tools that I paid for, using the memory I
> paid for, running on the iPad, how privacy is key, and how it's local inference on a machine
> that's completely air-gapped and I still extract so much value out of it."

The most credible thing a senior architect can post is **proof**, not claims. This story captures a
real, owner-driven session where HoldSpeak's mesh produces real daily value with **local inference
on owned, air-gapped hardware** — and packages it into post-ready material.

## The deliverable (two parts)

### 1. The air-gapped value session (the evidence)

A scripted-but-real session, run on the owner's mesh with **the network egress disabled** (the Mac
and/or iPad provably air-gapped — Wi-Fi off / firewall blocked, shown), demonstrating end-to-end
value with nothing leaving:

- **Capture or dictate** — e.g., a real working meeting captured on the iPad, *or* a dictation-driven
  work loop (iPad mic → the Mac) — your choice of the more compelling story.
- **Intelligence, local** — the model runs on hardware the owner owns (on-device Llama and/or the
  Mac's local server); the produced artifacts (decisions / actions / risks / a digest) are real.
- **A Workbench program** — a user-built workflow runs over the session, showing the *programmable*
  intelligence, with the queue narrating exactly what ran where.
- **The trust beat** — the egress badge stays `local` throughout; an action that *would* emit
  degrades to a draft (HSM-15-05). The point lands: **invaluable, yet nothing left the machine.**

Captured as: committed screenshots (the air-gap shown — radios off), a short screen/ःdevice capture
or photo set, and the real artifacts produced. Stored under `./screenshots/` + a
`proof/` evidence folder.

### 2. The launch narrative (post-ready)

A written narrative the owner can adapt for LinkedIn — the senior-architect angle:

- The thesis: *a personal intelligence mesh* — tools + memory you pay for, working for you across
  the devices you own.
- The hook: real efficiency gains (concrete: meetings → artifacts in seconds; dictation into any app;
  programmable intelligence) with **local, air-gapped inference** — no SaaS, no data exhaust.
- The proof: the session above, shown not told.
- Voice: aligned to `docs/internal/POSITIONING.md` (honest, named comparisons, no hype, no privacy
  novels). Drafted in the repo for the owner to make his own — **posting is the owner's button.**

## Acceptance criteria

- [ ] **Air-gap shown** — the session is captured with the machine provably offline (radios off /
      egress blocked, visible in the evidence).
- [ ] **Real value, local** — real artifacts produced by local inference on owned hardware; a
      Workbench program runs; the queue narrates where each step ran.
- [ ] **Trust beat** — the egress badge stays `local`; an emitting action degrades to a draft, proven.
- [ ] **Evidence committed** — screenshots + the produced artifacts under `./screenshots/` + `proof/`.
- [ ] **Narrative drafted** — a post-ready write-up in the repo, POSITIONING-aligned; posting left to
      the owner.

## Build plan

1. Script the session beats (capture/dictate → local intelligence → a Workbench run → the trust beat).
2. Run it with the owner on the air-gapped mesh; capture evidence (air-gap visible).
3. Assemble the evidence folder + the screenshot gallery.
4. Draft the launch narrative (POSITIONING voice); hand to the owner.

## Test plan

- This story's "test" is the captured evidence itself: the air-gap is shown, the artifacts are real,
  the egress badge is `local` throughout. No synthetic/staged data — a real session.

## Notes

- **Posting is the owner's button** (carried from the Phase-65 launch lesson — the announcement kit is
  drafted by the agent, posted by the owner).
- The air-gapped framing is the whole differentiator: not "private-ish cloud," but **provably nothing
  leaves**, and still invaluable. That is the senior-architect-credible story.
- Honest data only: if a beat needs the runner (HSM-15-04) or a mesh connector (HSM-15-02), those land
  first — the proof must show shipped behavior, not a mock.
