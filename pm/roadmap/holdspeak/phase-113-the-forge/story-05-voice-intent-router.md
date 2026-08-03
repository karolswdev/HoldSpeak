# HS-113-05 - Voice Intent Router

- **Project:** holdspeak
- **Phase:** 113
- **Status:** backlog
- **Depends on:** HS-113-02, HS-113-04
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

Voice on the Desk must understand what window it's talking to.
Speaking into a git drawer should understand "commit with message:
fixed the routing bug." Speaking into the editor should understand
"make this more concise." Speaking with nothing focused should
understand "open the holdspeak project." A Voice Intent Router sits
between raw transcription and action, classifies intent against the
focused surface's declared grammar, and proposes the action for
user confirmation. Voice arms, never fires (Article IV).

**Articles served:** IV (voice is first-class, mic authority is
singular, voice arms not fires), V (consent is the spine —
propose-approve-execute), VII (in-world, no modals), XI (consequential
actions admitted through the kernel).

## Ground (from the pre-charter survey)

- `web/src/desk/components/MicButton.tsx` — current voice: hold-to-
  talk, raw transcription appended to a text field. No intelligence
  between speech and action.
- `web/src/desk/components/AskPanel.tsx` — the Ask panel runs LLM
  calls with grounding and egress receipts. Its infrastructure (the
  `/api/ask` route, egress badges, model selection) can power the
  LLM-tier of intent classification.
- `web/src/desk/ask.ts` — Ask request/response data layer. Supports
  context and structured results.
- `web/src/desk/components/InlineEditor.tsx` — after HS-113-02,
  this will be CodeMirror 6 with `dispatch` for range replacements.
  After HS-113-04, it will have the VoiceProposalStrip for AI
  operations. The Voice Intent Router connects these two: spoken
  intent → proposal strip → editor action.
- `web/src/desk/floorMenu.ts` — the verb registry. Voice intents
  that map to verbs fire through this registry, not a parallel
  system.

## Method

1. **VoiceGrammar contract** (`web/src/desk/voice/grammar.ts`):
   - `VoiceGrammar` interface: surfaceKind, intents array,
     dictationFallback boolean.
   - `VoiceIntentDef` interface: id, local patterns (RegExp[]),
     requiresLLM flag, verbId (from verb registry), extract function,
     ghost function.
   - Every surface that wants voice beyond dictation registers a
     grammar. Surfaces without a grammar get plain dictation
     (existing MicButton behavior).

2. **Voice Intent Router** (`web/src/desk/voice/intentRouter.ts`):
   - Stateless classifier: takes (transcript, surfaceId, surfaceKind,
     selectionState, voiceGrammar) → VoiceProposal.
   - **Tier 1 — local pattern match:** checks transcript against
     the grammar's RegExp patterns. No LLM, no egress, no badge.
     Covers formatting ("bold that"), navigation ("show changes"),
     simple verbs ("stage everything").
   - **Tier 2 — LLM-assisted classification:** for natural-language
     intents that require understanding ("make this more concise").
     Routes through the hub's LLM via `/api/ask` with the egress
     badge visible. The classification call is SEPARATE from the
     action call.
   - Confidence threshold: below 0.5, fall through to dictation.

3. **VoiceProposalStrip** (`web/src/desk/voice/ProposalStrip.tsx`):
   - Inline confirm/cancel surface in the focused window's
     receipt bar area.
   - Shows: what was heard, what will happen, confirm/cancel buttons.
   - Keyboard: Enter confirms, Escape cancels.
   - Egress badge when the classification used an LLM.
   - Loading state: the `LedMeter` scanning bar with "CLASSIFYING"
     label (same instrument language as the Ask panel).
   - Multi-turn scoped to pending proposal: a new utterance while
     a proposal is pending refines it, doesn't start fresh.

4. **Surface grammars** (`web/src/desk/voice/grammars/`):
   - `editor.ts` — intents: dictate, bold, italic, heading, list,
     rewrite, expand, summarize, continue, readback.
     Dictation fallback: true.
   - `desk.ts` — intents: open-item, create-item, attention-summary,
     desk-search.
     Dictation fallback: false.
   - `repo.ts` — intents: show-changes, stage-files, commit,
     switch-branch, pr-status.
     Dictation fallback: false.
   - `roadmap.ts` — intents: whats-next, mark-done, show-health,
     capture-evidence.
     Dictation fallback: false.

5. **Integration with MicButton:**
   - MicButton gains an optional `grammar` prop. When present,
     transcripts route through the Voice Intent Router instead of
     raw append.
   - The mic session pipeline is unchanged (one grant, one floor).
   - The router consumes transcripts from the same pipeline.

6. **Visual feedback while listening:**
   - The focused window's border gains a 2px animated highlight
     synced to capture level (the `onLevel` tap from mic session).
   - The dock mic lamp states are unchanged: closed/suspended/open/
     segmenting/held.
   - New lamp state: `speaking` (steady blue) when TTS is active.

## Test plan

- Unit: `VoiceIntentRouter` classifies "bold that" as format intent
  (local, no LLM) when editor grammar is active.
- Unit: `VoiceIntentRouter` classifies "make this more concise" as
  rewrite intent (LLM tier) when editor grammar is active.
- Unit: `VoiceIntentRouter` falls through to dictation when
  confidence is below threshold.
- Unit: `VoiceIntentRouter` returns dictation when surface has no
  grammar registered.
- Unit: `VoiceProposalStrip` renders proposal, fires on Enter,
  cancels on Escape.
- Unit: `VoiceProposalStrip` shows egress badge only when the
  classification used an LLM.
- Unit: multi-turn refinement: "switch to feature branch" → proposal
  for feature-login → "no, the other one" → proposal updates to
  feature-auth.
- Integration: open the editor, speak "bold that" with text
  selected → text is bolded (no confirmation needed, reversible).
- Integration: open the editor, speak "make this more concise"
  with text selected → proposal strip appears → confirm → text
  is rewritten.
- Integration: no window focused, speak "open holdspeak project" →
  proposal strip in dock → confirm → project opens.
- Screenshot walk: 1440px — proposal strip visible in editor window,
  egress badge shown, confirm/cancel buttons. Must feel like a Desk
  OS feature, not a chatbot interface.
- Error leg: no inference target configured → LLM-tier intents
  are ghosted with "No model configured."
