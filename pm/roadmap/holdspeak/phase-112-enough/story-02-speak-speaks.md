# HS-112-02 - Speak speaks

- **Project:** holdspeak
- **Phase:** 112
- **Status:** in-progress
- **Depends on:** —
- **Unblocks:** HS-112-04, HS-112-05
- **Owner:** unassigned

## The thesis (the bar)

The owner: "One place to do hold to speak in the app working very,
very well." The room named Speak cannot speak: its TALK key fills a
textarea and runs `/api/dictation/dry-run` — it never delivers
anything anywhere. The flagship act lives on a global hotkey with no
UI. The bar: **hold TALK in the Speak room, talk, release — and the
text LANDS where you aimed it (the focused desktop app or the
awaiting agent), through the same pipeline, journal, kernel warrant,
and receipts as the global hotkey.** The room and the verb become the
same thing, and it feels excellent: honest level meter, visible
state, latency on the receipt, every failure in-flow.

## Ground (from the pre-charter survey)

- The Speak deck's only pipeline call is
  `POST /api/dictation/dry-run`
  (`web/src/pages/cores/DictationCore.tsx:334`); its TALK key
  (`:443`) is the generic speak-to-fill MicButton wearing a bigger
  face.
- The delivery route exists and is proven — `/api/dictation/remote`
  (`holdspeak/web/routes/dictation/pipeline.py:305`) with
  `target_mode: agent|focused`, `delivery_id` idempotency, and the
  full kernel path (`_deliver_remote_dictation`,
  `holdspeak/runtime/dictation_capture.py:447`) — but **no web
  client calls it**; only the Swift companion does.
- Browser capture (`web/src/lib/speakToFill.ts`) deliberately skips
  journaling, macros, and delivery
  (`dictation_capture.py:282-294`). The web half captures but cannot
  deliver; the companion half delivers but cannot hold.
- Four gesture contracts for one verb (hotkey hold-release,
  MicButton pointer down/up, wake armed window, companion
  tap-toggle mislabeled "Hold to speak").
- Preview-vs-type is decided in three unrelated places with three
  defaults (`dictation_capture.py:117`, `wake_glue.py:203`, the
  remote route's `raw`/`target_mode` flags).

## Method

1. **Wire the room to the real act.** The TALK key's release posts
   to the delivery contract (`/api/dictation/remote` or a cleaned
   successor): full pipeline, journal, receipts, idempotent
   delivery. Dry-run remains as an explicit REHEARSE mode, never the
   default.
2. **An aim selector, not prose.** One gadget row names the target:
   FOCUSED APP / AGENT / THIS FIELD — with the same honest refusal
   the kernel already speaks (`desktop_focus_unresolved`, no
   awaiting agent) rendered in the footer receipt bar.
3. **One gesture contract.** Hold means hold everywhere the web
   renders it; the deck's preview semantics follow one written rule
   shared with the hotkey path (preview opt-in, type default), and
   the receipt shows release-to-landed latency.
4. **Scope honesty.** The two audio stacks, the twin preview token
   stores, and the companion's tap-toggle are named debt for the
   final summary unless trivially absorbed — this story's job is the
   flagship room performing the flagship act, very well.

## Test plan

- Live on real metal (standing rule): hold TALK in the browser,
  speak, release — the text lands in a real focused desktop app
  through the kernel warrant path, receipt captured; second leg
  lands a reply in a real awaiting agent pane.
- The refusal legs live: no focus resolved, no awaiting agent, STT
  failure — each in-flow (receipt bar / deck state), no toast, no
  overlap; mandatory shot legs.
- Idempotency: a retried delivery with the same `delivery_id` lands
  once (pinned by test).
- The journal shows the room's dictations beside the hotkey's, same
  schema; dry-run entries only from explicit REHEARSE.
- Screenshot walk at 1440+393: idle, held (inverted TALK + live
  meter), landed receipt, each refusal.
