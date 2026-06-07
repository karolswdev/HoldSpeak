# Phase 48 — The Visible Learning Loop ("What HoldSpeak learned")

**Status:** CLOSED (5/5). Opened 2026-06-07 on user direction, after Phase 47
closed (PR #28). The user liked the "what I learned this week" idea from the
strategic review and asked to make it a real phase, framed as an open-source
differentiator: *"I do like the 'what I learned this week' ... let's make this
Open Source thing happen."*

**Last updated:** 2026-06-07 (**Phase CLOSED (5/5).** HS-48-05 — closeout —
**done**: true before/after captured (old raw Memory/Journal vs the new digest +
inline chips + one-tap ritual, the before built from `5a3c047` then restored), a
green `scripts/dogfood_learning_loop.py` (dictate -> correct -> digest shows
`similar_nudged=2`), `final-summary.md` written, full suite 2401/18, 0 `_built/`
tracked, PR to `main` opened and merged on green CI. See
[`final-summary.md`](./final-summary.md).)

## The thesis — why this phase

**HoldSpeak's strongest, most ownable idea is a local speech-to-work loop that gets
better as you use it: it hears rough speech, routes and rewrites it in context,
remembers the attempt, learns from your corrections, and can replay to prove it
improved. That loop already exists in code. It is just invisible.** Grounded in the
live tree:

- **The learning is real but buried.** Phase 45 ships the dictation **journal**
  (`dictation_journal`: said → typed → routed → latency, with a `corrected` flag),
  the **moment-of-truth** correction (`POST /api/dictation/journal/{id}/correct`),
  and **replay**. Phase 40 ships **correction memory** (`dictation_corrections`:
  kind/gist/value) with a Jaccard matcher (`CorrectionStore.best_match_in`) that
  nudges routing when `corrections_enabled` is on. But a user sees only two raw
  lists (a Memory tab and a Journal tab). Nothing says "here is what HoldSpeak
  learned from you."
- **There is no aggregation over time.** The only stats today are in-session depth
  telemetry (`build_depth_readiness`), reset on restart. There is **no** weekly /
  over-window rollup, and corrections do **not** track how many utterances they
  cover. So "what I learned this week" is genuinely new work, not a re-skin.
- **Correcting is effortful.** The teach path is a multi-field form in the dry-run
  moment and the Memory tab. "That was wrong" should be one tap, or the loop that
  feeds the digest starves.
- **This is the open-source pitch.** "It gets better at your voice, on your
  machine, and shows you the proof" is a differentiator worth demoing. Making the
  loop visible is what turns a pile of subsystems into a story.

## Goal

Make the learning loop **visible** (a "What HoldSpeak learned" digest with honest,
windowed counts), **trustworthy** (inline "learned from N similar" signals at the
moment of value, never inflated), and a **normal ritual** (one-tap right/wrong on a
result), held to the Phase-43+ Signal UX bar — without changing what the pipeline
does.

## Scope

- **In:** a windowed **learning-digest** aggregation + a "What HoldSpeak learned"
  view (HS-48-01); **inline trust signals** that show the real coverage of a
  correction (HS-48-02); a **frictionless right/wrong correction ritual** reusing
  the existing correct path (HS-48-03); a **docs** story telling the loop end to end
  as the OSS differentiator (HS-48-04); a **closeout** (before/after, dogfood,
  final-summary, PR) (HS-48-05).
- **Out:** changing pipeline behavior (routing, rewrite, substitution stay; the
  digest is read-only over existing data); a new ML matcher (reuse the Jaccard
  `CorrectionStore`); the public release contract + schema-migration policy (a
  separate pre-release gate, deferred); a voice-command grammar (a different bet);
  meeting-side work.

## Exit criteria (evidence required)

- A read-only digest endpoint + a "What HoldSpeak learned" view show honest,
  windowed counts (corrections made, dictations corrected, by-kind/target/block,
  and a real "N similar" from the existing matcher). (HS-48-01)
- The result + journal surfaces carry a truthful "learned from N similar" signal,
  and the post-correction confirmation states real coverage. (HS-48-02)
- A one-tap right/wrong affordance makes correcting a normal ritual, reusing the
  existing correct endpoint; focus-safe. (HS-48-03)
- The docs tell the loop end to end and the README/index frames it as the
  local-first differentiator; guards green. (HS-48-04)
- Before/after captured; dogfood green; `final-summary.md`; phase CLOSED; PR to
  `main` merged on green. (HS-48-05)

## Invariants

- **Behavior-preserving.** The digest is read-only aggregation; correcting reuses
  the existing write path; `corrections_enabled` posture and secret-filtering are
  respected. Pipeline tests stay green.
- **Honest over hype.** Every count is real and computed from the same matcher that
  actually nudges routing; surfaces stay quiet at N=0; no implied silent retraining.
  The learning is Jaccard token overlap, local, and off-by-default until enabled.
- **Local-first & focus-safe.** Everything stays local; any result/presence
  affordance is dismissible and never steals keyboard focus (the zero-`.focus()`
  guard in the dictation bundle holds).
- **UX bar.** Signal language via `ui-ux-pro-max`; the digest reads as a reward, not
  a table; no bare lists.
- **Page density.** Do not pile more onto `dictation.astro` / `dictation-app.js`
  without factoring into section partials / behavior modules (the standing density
  warning; Phase 47 already grew these files).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-48-01 | The learning digest ("What HoldSpeak learned") | done | [story-01-learning-digest.md](./story-01-learning-digest.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-48-02 | Inline trust signals ("learned from N similar") | done | [story-02-inline-trust-signals.md](./story-02-inline-trust-signals.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-48-03 | Frictionless correction ritual (right/wrong, in flow) | done | [story-03-correction-ritual.md](./story-03-correction-ritual.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-48-04 | Docs: the learning loop, end to end | done | [story-04-docs.md](./story-04-docs.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-48-05 | Closeout — before/after + dogfood + PR | done | [story-05-closeout.md](./story-05-closeout.md) | [evidence-story-05.md](./evidence-story-05.md) |

## Where we are

**HS-48-01 (digest), HS-48-02 (inline signals), and HS-48-03 (the ritual) are
done — the whole visible loop now works.** The aggregation lives in
`holdspeak/dictation_learning.py`: `reach_for_gist` is the one definition of
"N similar" and `best_correction_signal` reuses `best_match_in`, so the digest,
the chips, and the toast all count identically. The digest hero is at the top of
the Memory tab; the "learned from N similar" chip rides the dry-run result,
journal entries, and the Memory list; and correcting is one tap (`correctionRitual`
/ `wireFixit`, reusing `POST /journal/{id}/correct`, focus-safe). Everything is
quiet at N=0 and honest about `corrections_enabled` + secret-filtering; the
spoken `say` → Whisper → digest e2e still proves it through real voice. The docs
(guide §12 + README + index) tell the loop end to end and frame it as the
local-first differentiator, with an honest limits note. **The phase is CLOSED:**
before/after captured, `scripts/dogfood_learning_loop.py` green, full suite
2401/18, `final-summary.md` written, PR to `main` merged on green CI. Sequence:
01 ✓ → 02 ✓ → 03 ✓ → 04 ✓ → 05 ✓. See [`final-summary.md`](./final-summary.md).

## Active risks

- **Inflated counts.** Mitigation: one matcher (the existing Jaccard
  `CorrectionStore`), surfaces quiet at N=0, honesty-over-hype invariant.
- **Page-file bloat.** Mitigation: the page-density invariant; factor into
  partials/modules; this phase is also a good moment to start that discipline.
- **Scope creep into release engineering.** Mitigation: the release contract +
  schema policy are explicitly deferred; this phase is the visible-learning feature.
- **Naggy correction UI.** Mitigation: calm, dismissible, focus-safe; honesty over
  celebration (no confetti banners).

## Decisions made (this phase, from user)

- **Build the "what I learned this week" view.** The user picked this from the
  strategic review (`.guru_meditation.md`) as the next phase and tied it to the
  open-source push.

## Decisions deferred

- **Digest home.** A dedicated "Learned" section vs. a reframed Memory hero —
  settle in HS-48-01, favoring the lightest thing that reads as a reward.
- **Presence-surface right/wrong.** Whether the one-tap ritual also lands on the
  desktop-presence HUD — candidate, not required; settle in HS-48-03.
- **Release contract + schema-migration policy.** A separate pre-release gate (the
  strategic review flags it); not this phase.
