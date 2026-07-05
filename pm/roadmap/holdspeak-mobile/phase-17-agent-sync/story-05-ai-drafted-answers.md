# HSM-17-05 — AI-drafted answers (local or remote, approve-then-inject)

- **Project:** holdspeak-mobile
- **Phase:** 17
- **Status:** done (2026-07-04 — the endpoint draft LIVE-proven grounded on the LAN model; the on-device
  air-gap run walks in 17-06 per the acceptance below; see `evidence-story-05.md`). **The owner's headline
  idea for the loop** (*"use a local / remote agent to construct the response too"*).
- **Depends on:** HSM-17-04 (the composer + inject it plugs into), the inference seam (`ILLMProvider` with
  `LlamaProvider` Mode A on-device + the endpoint Mode B/C, `InferenceConfigStore`), the keystone routing
  gesture / `routableText`.
- **Unblocks:** —
- **Owner:** unassigned

## Problem

Answering the coder by hand is fine, but the iPad already runs intelligence — on-device and via endpoint.
So when a coder asks a question, the answer can be **composed for you**: route the question (plus any
dropped context) through the AI core, get a draft, approve/edit, inject. This is the loop becoming
intelligent, and it falls straight out of the primitive system.

## The interaction

In the Answer composer (17-04), a fourth input: **Draft with AI.**

1. The coder's **question** is the prompt; any **dropped context** (meeting / artifact / note, from
   17-04) is the grounding. This is literally routing the question-primitive through the AI core
   (`ModelPrimitive`) — the same gesture as the desk's Ask.
2. It runs on the resolved engine — **on-device** (`LlamaProvider`) or the **endpoint** (Mode B/C) per
   the inference setting / Phase-15 fluid compute. The egress badge says where it ran.
3. A **drafted answer** comes back into the composer — not sent, *drafted*. You read it, edit it, or
   re-draft (optionally adding more dropped context).
4. **You approve → it injects** down the same 17-04 path into the live session.

## Scope

- **In:** the Draft-with-AI action in the composer — assemble {question + dropped context} → one
  `ILLMProvider` call (on-device or endpoint) → a draft placed in the editable composer → human
  approve/edit/re-draft → inject via the 17-04 path. Egress-honest; on-device works air-gapped.
- **Out:** auto-send of a draft (forbidden); fine-tuning / persona-shaping the drafter (it uses the desk's
  AI core as-is); multi-turn back-and-forth with the drafter beyond re-draft.

## Acceptance criteria

- [x] From a waiting agent primitive, **Draft with AI** produces a drafted answer from the question (+ any
      dropped context) via the on-device provider, with **no network** when inference is local
      (air-gap honest); the egress badge reflects local vs endpoint. (The draft chip is `.local` /
      `.cloud("endpoint")`, distinct from the send badge; the on-device run itself is a 17-06 device beat.)
- [x] The draft lands **editable** in the composer; it is **never** sent without an explicit human
      approval (the non-negotiable). Re-draft (with optionally more context) works. (Test-pinned: the
      draft API cannot reach the desktop client by construction.)
- [x] On approve, the (possibly edited) draft injects into the correct session via the 17-04 path and the
      coder continues. (The 17-04 path, live-proven there; the draft only fills the same editor.)
- [x] Endpoint path (Mode B/C) works when configured; on-device path works with no endpoint.
      (Endpoint LIVE-proven: a grounded, first-person draft from the LAN Qwythos in 0.52s.)
- [ ] Proven on the iPad Air M4 on real metal (HSM-17-06): both an on-device draft and, ideally, an
      endpoint draft, each approved and injected into a live coder. (Stays 17-06 — the device walk.)

## Test plan

- Real metal: a live coder asks an architecture question; on the desk, drop the meeting where that
  decision was made as context, **Draft with AI** on-device → a grounded draft appears → edit a word →
  approve → it lands in the coder. Repeat once on the endpoint.
- Unit: {question + dropped context} assembly into the provider prompt; egress scope = local for on-device
  / cloud(+target) for endpoint; a draft is held until an explicit approve before any inject is called.
