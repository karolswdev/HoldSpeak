# Phase 112 - Enough

**Status:** 6/6 SHIPPED AND WALKED (chartered, built, and proven on a fresh HOME in ONE DAY, 2026-08-02); THE CLOSED CLAIM AWAITS THE OWNER SITTING. The owner's verdict after Phase
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
| HS-112-01 | One dial | done | [story-01-one-dial](./story-01-one-dial.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-112-02 | Speak speaks | done | [story-02-speak-speaks](./story-02-speak-speaks.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-112-03 | The architect's desk | done | [story-03-architects-desk](./story-03-architects-desk.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-112-04 | The plain story | done | [story-04-plain-story](./story-04-plain-story.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-112-05 | The sitting walk | done | [story-05-walk](./story-05-walk.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-112-06 | The open mic | done | [story-06-open-mic](./story-06-open-mic.md) | [evidence-story-06](./evidence-story-06.md) |

## Where we are

6/6. Chartered morning, built by afternoon, walked by evening —
2026-08-02, one day. The exit proof ran on a genuinely fresh HOME
(first_run true, zero directories): the seed chip minted the
architect's desk (six drawers, the ADR template, the Working
rules), the Models dial was set once to the real LAN .43 and PROBEd,
TALK was held in a real browser with real speech and LANDED with a
1335 MS receipt, the OPEN MIC latch landed an ambient utterance
with no key touched (chrome lamp MIC OPEN -> CLOSED), aim AGENT
with none awaiting refused by name and replayed idempotently, and
RESET TO SEED's armed ritual tombstoned the clutter and brought the
seed back — 21 shots at 1440+393 in assets/hs-112-05/, the wire
proofs in evidence-story-05.md, the sitting brief in
[final-summary.md](./final-summary.md). Held for the owner: the
sitting, the FOCUSED APP default-aim ruling, and the Phase-111
printed-Ask-turn room shot (.43 is back; the wire leg is proven).
