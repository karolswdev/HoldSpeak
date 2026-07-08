# Phase 87 — The Steering Desk (B2) — Final Summary

- **Phase opened:** 2026-07-08 (scaffolded from the owner's post-86
  steering bar; the RFC's B2 row expanded into a six-story charter)
- **Phase closed:** 2026-07-08, the same day
- **Stories shipped:** 6/6

## Goal — was it met?

> The desk becomes the primary steering surface for live agent
> sessions — attach, steer, classify, ground — every verb admitted
> only under the Telegram layer's consent spine or stronger: watching
> free, steering armed, pane identity verified per keystroke,
> everything audited, the dw gate keeping final say. Owner bar: "so
> robust, it will literally destroy our brains."

**Yes.** The desk now watches a real agent session, arms it under a
consent grant, types into it through one audited chokepoint, carries
desk objects in as grounded context, and triages what a session
surfaces onto the desk and the rails — proven live, end to end, in a
single eight-beat walk against a real tmux pane and the real `.43`
model.

## Exit criteria — final state

- [x] A live session watched from the pull-out, honest staleness,
      zero grants issued (HS-87-01) — `test_coder_steering`, live peek
      integration.
- [x] Unarmed steer refused; armed steer lands; recycled-pane steer
      refused AND disarms; expiry and disarm visible (HS-87-02/03) —
      the grant lifecycle property tests + the live crown cases.
- [x] A steer carries a real desk object as hydrated, provenance-headed
      context; the agent's next output demonstrably uses it (HS-87-04)
      — control-vs-treatment on `.43`: "I don't have access…" vs
      "Friday the 13th at 3:47pm, code-named BLUEBIRD".
- [x] Classify: a session's ask becomes a desk note; a story flip
      proposed from the pull-out rides the Phase-82 leg (HS-87-05).
- [x] The audit answers who/when/what/where for every steer of the
      walk; suite + guards green; docs shipped (HS-87-06).

## What shipped

- **`holdspeak/coder_steering.py`** — the whole consent spine in one
  file: `peek_pane` (hash-gated read), the in-memory grant store
  (`arm` / `disarm` / `require_grant` / `sweep`, monotonic clock,
  fail-closed on restart), and `deliver` — the ONE chokepoint that
  checks the grant, re-verifies the pinned `%N`, sends to the verified
  pane, and audits.
- **`holdspeak/grounding.py`** — the Phase-83 ask hydration factored
  verbatim and now shared by ask and steer; `compose_steer` fences
  desk objects with provenance headers, capped at 8 KB.
- **`db/steering.py` + schema v12** — the `steering_audit` table:
  hash + head, refs, outcome, per attempt.
- **`web/routes/system/coder_steering_routes.py`** — peek / arm /
  disarm / grants / steer / audit / keep-note, carved out for the
  single-concern budget.
- **The desk** — `SessionPullout` (live pane, hold-to-arm chip →
  countdown, voice-first composer, grounding picker, classify
  section), armed rings and manual pins on the conveyor, `scope:"coder"`
  frames on the one bus.
- **Docs** — USER_GUIDE "Steer a session from the desk", the
  SECURITY.md consent-model trust boundary, the ARCHITECTURE.md
  steering-chokepoint paragraph.

## What the trenches taught

- **tmux 3.6 answers a dead target with rc 0 and an empty expansion**
  when the server is otherwise alive. The live arming rig caught it;
  an unprovable pane is now typed `pane_gone`, and the recycled-pane
  crown case proves refuse-and-revoke.
- **The awaiting-transition watcher had to live hub-side.** The
  ingest-side detection runs in the hook's own process and cannot
  reach the bus; the hub stats the registry file's mtime and diffs.
- **`deliver` sends to the verified `%N`, not the target string** —
  the check-to-keystroke TOCTOU window is closed by construction.

## The handoff to B3 / B4

This phase is the consent spine those later verbs inherit:

- **B3 — the factory ("New Project" from the desk).** A new-project
  act is another consequential local operation; it reuses this
  phase's shape — an explicit desk act, a documented wire contract, a
  hub-side chokepoint, an audit row, the dw gate keeping final say.
  The propose→approve→execute leg (Phase 82, reused here for
  flip-from-here) is the machinery; the factory adds one gated argv
  shape (`dw project new` or equivalent), never a new write path.
- **B4 — the DeskOS belt (HSM track).** Every steering shape this
  phase shipped — the peek envelope, the grant, the steer, the audit
  row, the classify verbs — is a documented wire contract on public
  `/api/coders/*` routes, so the iPad and iPhone render them natively
  instead of scraping a page. The phone already answers a waiting
  coder by voice (HSM Phase 13); the session pull-out, the armed
  steer, and the grounding picker are its next chapter, and B4 does
  not need a redesign to get them.

## Not done here (by design)

- No new egress: steering never leaves the machine.
- No autonomous steering: a human is behind every keystroke.
- Multi-pane sessions, steering other mesh nodes, and a persistent
  arming ledger are deferred (fail-closed restart is the feature, not
  a gap).
