# Phase 112 - Enough

**Status:** CHARTERED (2026-08-02). The owner's verdict after Phase
111 shipped, verbatim: *"Enough with the over-complication, enough
with me not really even understanding what HoldSpeak does and what
HoldSpeak is."* Three concrete asks, and this phase is exactly those
three plus the docs and the walk that prove them — plus one owner
rider chartered live the same day: the open mic ("we open a
microphone request once, keep sending voice, use VAD and so on — so
that we're finally in a voice-first environment"). Nothing else.

**Last updated:** 2026-08-02 (chartered; HS-112-06 The open mic
added as the owner's live rider; HS-112-01 ready).

## Why this phase exists

Eleven phases of craft made every room speak one language — and the
owner still cannot say what the OS does. That is not a rendering
problem; it is a legibility problem, and the pre-charter survey
grounded it in three structural facts:

1. **The model dial is smeared across the machine.** An endpoint or
   model can be set in ~28 named places across 5 storage tiers
   (`config.py` declares the same base_url/model/api_key triple twice
   with different defaults; three separate `profile_id` pointers use
   two different sentinels; two full CRUD APIs cover one table; three
   different UIs edit it). The single-source-of-truth candidate
   already exists — the `profiles` table as `InferenceTarget`, with
   `resolve_inference_target` as the one resolver — and the Phase-111
   Prefs room already declares an empty `models` module waiting to
   own it.
2. **The room named Speak cannot speak.** The flagship act — hold,
   talk, release, text lands where you were working — lives on a
   global hotkey with no UI, while the Speak deck's TALK key fills a
   textarea and dry-runs into the void. Six capture paths, four
   gesture contracts, and the web half can capture but not deliver
   while the companion half can deliver but not hold. No web client
   calls `/api/dictation/remote` at all.
3. **The desk cannot start fresh and cannot be reset.** There is no
   product-side seed (a fresh install is an empty floor), the desk UI
   has no delete verb (a desk is append-only), and what the owner
   sees today is his own accumulated dev residue. The seed format and
   idempotent applier already exist — quarantined in the UAT rig.

The bar for the phase: **a Senior Software Architect sits down at a
fresh desk, sets one dial, holds one key, and can explain the whole
OS in one paragraph.**

## Method

Owner's standing rules apply: hands-first, proven live on the real
hub at 1440+393, error legs are mandatory shot legs, no prose in the
UI, the egress badge not privacy novels. Every story deletes more
configuration surface than it adds. Where a story finds adjacent debt
it does not absorb it — it names it in the final summary.

## Stories

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 01 | [One dial](./story-01-one-dial.md) | "One place to configure what the endpoint and model is" | ready |
| 02 | [Speak speaks](./story-02-speak-speaks.md) | "One place to do hold to speak in the app working very, very well" | backlog |
| 03 | [The architect's desk](./story-03-architects-desk.md) | "An environment seed that starts fresh and beautiful" | backlog |
| 04 | [The plain story](./story-04-plain-story.md) | "Me not really even understanding what HoldSpeak does" — the docs | backlog |
| 05 | [The sitting walk](./story-05-walk.md) | The exit proof: fresh desk → one dial → hold → land → reset | backlog |
| 06 | [The open mic](./story-06-open-mic.md) | "Open a microphone request once, keep sending voice, use VAD" — the voice-first Desk | backlog |

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-112-01 | One dial | in-progress | [story-01-one-dial](./story-01-one-dial.md) | — |
| HS-112-02 | Speak speaks | in-progress | [story-02-speak-speaks](./story-02-speak-speaks.md) | — (captured; ships with the flip) |
| HS-112-03 | The architect's desk | in-progress | [story-03-architects-desk](./story-03-architects-desk.md) | — |
| HS-112-04 | The plain story | backlog | [story-04-plain-story](./story-04-plain-story.md) | — |
| HS-112-05 | The sitting walk | backlog | [story-05-walk](./story-05-walk.md) | — |
| HS-112-06 | The open mic | backlog | [story-06-open-mic](./story-06-open-mic.md) | — |

## Where we are

0/6 flipped; 01, 02, 03, and 06 BUILT (in-progress pending
live proofs).

HS-112-01 implemented 2026-08-02: the InferenceTarget is the only
truth. The legacy intel_cloud_*/openai_compatible_* fields are dead
everywhere except the ONE silent migration at default-path
Config.load() (legacy-intel / legacy-dictation synthetic targets,
idempotent, explicit-path loads never migrate); the three feature
pointers share one sentinel (None = hub default, rails' "" fixed);
the default host has one chokepoint; intel_queue resolves through
effective_intel_cloud instead of threading the triple through six
signatures; /api/profiles writes 405 naming /api/inference-targets;
settings PUT strips the dead fields from the wire. One face: the
Prefs Models module (DESTINATIONS table with key/readiness lamps +
armed FORGET, PROBE row, RUNS ON pickers for DICTATION/MEETINGS/
RAILS, HUB DEFAULT ENGINE, RAILS OBSERVER); RuntimeDestination and
ProfilesCore DELETED with every call site aliased into the one
dial; the grep census pinned as tests both sides. 22-test story
suite + 879 targeted + full 3454 unit + 449 web green. Named debt:
legacy key env deliberately does not carry over (per-destination
key rule); per-target probe endpoint named not absorbed. The flip
awaits the live proof: one dial set once, dictation + meeting
intel + ask all landing on the real endpoint (control-vs-treatment
on .43), error legs shot at 1440+393. Chartered 2026-08-02. Chartered 2026-08-02 from the owner's post-111 verdict; the

HS-112-03 implemented 2026-08-02: the packaged fresh-desk

HS-112-02 implemented 2026-08-02: the Speak room's TALK key delivers
for real through the one existing contract (/api/dictation/remote —
no forked idempotency), with an AIM row (FOCUSED APP / AGENT / THIS
FIELD), REHEARSE as an explicit mode never the default, opt-in
require_agent strictness (companion fallback byte-identical), a
pre-effect refusal classifier turning deterministic kernel refusals
into named terminal 422s (retry replays the cached refusal;
mid-type driver failures still honestly park pending), release-to-
landed latency on the receipt, and journal_source=dictation — which
also fixed a latent bug: companion deliveries had been journaling
as dry_run rehearsals. Contract tests byte-identical (42 tests);
new: 13 python + 12 web; suites 3464 unit + 456 web green (one
environmental node-link flake passes in isolation). Named debt in
the story report: two audio stacks, deprecated ScriptProcessorNode,
twin preview stores, companion tap-toggle, macro-dispatch bypass,
2-valued journal_source, no delivery_id on the transcribe leg. The
flip to done awaits the live proof: TALK held in a real browser,
text landing in a real focused app and a real agent pane, refusal
shot legs, 1440+393.

walk). HS-112-03 implemented 2026-08-02: the packaged fresh-desk
seed ships in the wheel (holdspeak/seeds/fresh-desk.yaml — six
hs-desk-* drawers: ADRs, Meetings, Rules, Decisions, Reference,
Inbox; two authored starter notes: the ADR template and the
Working rules), applied by a repository-level idempotent seeder
(holdspeak/db/seed.py), reachable as `holdspeak seed`, POST
/api/desk/seed, an EmptyDesk "Seed the desk" chip, and the Prefs
Desk module. Reset-to-seed is the desk's first destructive act,
done honestly: tombstone-only sweep (sync include_deleted ships the
deletions — a paired device can never resurrect the clutter; pinned
by test), re-seed, then the six ghost layout keys swept only after
the wire says ok; the ConfirmVerb arming (RESET TO SEED → danger
RESET DESK?, 3s auto-disarm) with fact labels naming what RESETS
and what KEEPS (meetings, journal, settings, runs-on targets), and
a TOMBSTONED N · SEEDED M receipt. The desk.reset-to-seed verb
never destroys from a menu tap — it opens the Prefs face. UAT
quarantine + fresh-desk empty assertions hold (no auto-seed at
boot). 112 targeted python + 10-test story suite + 453 web green;
full-suite failures triaged pre-existing/environmental in the
report. The flip awaits the live walk: first boot, drawer open,
ADR template read, reset confirm + after, 1440+393. Chartered
2026-08-02. Chartered 2026-08-02 from the owner's post-111 verdict; the

Chartered 2026-08-02 from the owner's post-111 verdict; the
same day the owner chartered the open-mic rider live (HS-112-06 —
the voice-first Desk: one mic grant, continuous stream, VAD; PTT
byte-identical). The pre-charter survey (three parallel audits: the
config map, the hold-to-speak map, the desk-seed map) is folded into
the story theses; each story names its file:line ground. 01/02/03
are independent; 06 rides on 02; 04 needs the surfaces settled; 05
closes. Phase 111's sitting remains pending in parallel — this phase
does not touch its exhibit.
