# Dictation commit boundary

- **Contract:** HS-107-01
- **Law:** Constitution Article V; Article XI.1–6
- **Migration rule:** `docs/internal/PLAN_KERNEL_OPERATION_BROKER.md` §7 rung 5 and §12

## Terms

- **Computation:** capture, transcription, punctuation, intent selection, rewrite, preview rendering, and target-profile detection. It has no external effect and owes no kernel admission or receipt (Article XI.5; RFC §12). Audio frames never enter an operation payload, journal, or receipt.
- **Effect:** the first synthetic input delivered to a desktop input target or process target. Only this boundary is consequential.
- **Commit:** the single kernel admission immediately before that effect. Admission does not add a prompt, hold, or second decision to an owner's direct gesture.
- **Direct gesture:** authority basis `direct_gesture`, the existing dictation-commit basis in `holdspeak/operation_policy.py:227-244`, selected at `:238`. No caller may mint it; admission derives it from an authenticated owner principal and the path-specific gesture.
- **Preview posture:** `configured_preview` at `holdspeak/operation_policy.py:227-244` (selected at `:238`) means “wait for a gesture.” It is not authority to type.

## Receipt shape

Every attempted effect ends in one terminal receipt, including refusal, failure, and indeterminate outcome. The operation record and receipt together contain only:

- operation id, type and version;
- authenticated principal and derived authority basis;
- immutable target ref and placement;
- SHA-256 of the canonical admitted payload, UTF-8 text byte count, and `submit` boolean;
- a non-content head bounded to 120 characters;
- policy version, timestamps, outcome, and bounded result ref/correlation refs.

The receipt and operation journal contain no full dictated or macro text, no recoverable text prefix, and no audio/audio-frame/token-stream content. Domain stores may retain text under their own contracts; the kernel stores the hash and bounded metadata only.

## Path matrix

| Path / debt sites | Effect | Commit point | Authority basis | Receipt additions | Exempt computation |
|---|---|---|---|---|---|
| Ordinary hold-key typing / D01 | `desktop.type_text@1`: insert final text into the focused input; `submit=false`. | After final text and target profile are resolved, immediately before the one desktop insertion. Key release is the owner's approving gesture; admission must be invisible and non-blocking. | `direct_gesture` — `holdspeak/operation_policy.py:227-244`, specifically `:238`. | Target is a focus-generation-bound desktop input ref; text hash, byte count, `submit=false`; terminal outcome. | Audio capture and frames, Whisper, punctuation, routing, rewrite, target detection, presentation, and callbacks. |
| Preview-before-commit / D02 | `desktop.type_text@1`: insert the stored one-shot preview; `submit=false`. Arming or displaying the preview is not an effect. | **Only when the owner invokes Type and the one-shot token is consumed**, immediately before insertion. Initial hold/release commits nothing because configured policy deliberately withheld the effect. Discard commits nothing. | The Type control is a fresh `direct_gesture` — `holdspeak/operation_policy.py:227-244`, `:238`. `configured_preview` at the same line explains the wait state only; it cannot authorize insertion. | Preview token/ref (not preview text), focused-input target ref, text hash, byte count, `submit=false`; terminal outcome. | Everything through preview creation, storage, broadcast/rendering, discard, and token lookup/validation. |
| `type_text` voice command / D03 | `desktop.type_text@1`: insert the configured macro payload into the resolved desktop target; `submit=false`. The recognized keyword itself is not typed. | After deterministic whole-utterance macro selection and target resolution, immediately before insertion. | `direct_gesture` — `holdspeak/operation_policy.py:227-244`, `:238`. It is valid only for an authenticated owner actively holding/releasing the dictation control; stored macro configuration alone is not authority. | Macro id/ref and action kind, target ref, payload-text hash and byte count, `submit=false`; never the keyword or configured payload text. | Capture, transcription, punctuation, exact-keyword matching, macro lookup, preview label, and target detection. Non-typing macro kinds are outside this contract and require their own operation type and authority semantics. |
| Remote dictation / D04, D05 | For `target=focused`, `desktop.type_text@1` with `submit=false`. For `target=agent`, `process.input@1` with `submit=true` when a process target exists; the legacy no-session fallback is `desktop.type_text@1`, `submit=false`. | The companion's explicit Send is approval. Commit after destination resolution, immediately before the selected desktop or process effect. The already-processed text is not re-admitted during computation. | `direct_gesture` — `holdspeak/operation_policy.py:227-244`, `:238`; it is derived from the authenticated owner's Send action, not from loopback/device proximity. | Requested target plus resolved immutable target; operation-specific text hash/byte count/submit flag; delivery method; terminal outcome. If `target=agent` cannot resolve a process and the resolved fallback target is not the owner's current focus generation, refuse by name. | Companion capture/upload, transcription, punctuation, pipeline processing, recent-session lookup, target selection, and response presentation. Audio frames never reach this delivery path. |
| Dictation-to-agent / T03 (and D01/D04 desktop fallback only when no process target exists) | **`process.input@1`**, not `desktop.type_text`: send final text and Enter to one immutable tmux-backed process target (`submit=true`). | After pane identity is resolved to process ref + expected generation, immediately before terminal input. The hold/release or companion Send is the approving gesture; no second confirmation is permitted. | `direct_gesture` — `holdspeak/operation_policy.py:227-244`, `:238`. The existing coder-steering alternatives are `control_posture` / `scoped_grant` at `holdspeak/operation_policy.py:246-286`, specifically `:270-275`; they are not substituted for the owner's immediate dictation gesture. | Process ref, expected generation, command ref/id, text payload hash, UTF-8 byte count, `submit=true`, node/placement, and terminal outcome; never pane text or full dictated text. | Capture, transcription, punctuation, routing/rewrite, awaiting-session lookup, pane discovery, and presentation. |

## Findings and migration constraints

1. **T03 is `process.input@1`.** Its destination is a controlled process/pane and its Enter is part of terminal input; desktop focus and desktop target profiles are irrelevant.
2. **Preview ambiguity is resolved at Type.** Seeing or storing text is presentation/computation. The consequential boundary cannot precede the owner's one-shot Type gesture because the effect may still be discarded.
3. **No path in this matrix requires a new authority-basis name.** All covered effects are immediate consequences of an authenticated owner's direct gesture. Configuration, posture, and proximity are not replacements for that gesture.
4. **The remote `target=agent` focus fallback is target-ambiguous today.** HS-107-02 must bind and record the actually resolved process or focus generation. It must refuse by name rather than claim an agent delivery against an unresolved/changed target.
5. **A voice macro reached without an active owner hold/release has no honest basis in the current descriptors.** `direct_gesture` applies only when that gesture is authenticated. Stored macro configuration is not a scoped grant and must not be relabeled as one (`scoped_grant` is defined by matching at `holdspeak/operation_policy.py:160-189` and selected at `:270-275` / `:300-304`).
6. The existing `process.input@1` vocabulary is the compatibility target: immutable `process:` ref, expected generation, command id/ref, `submit`, SHA-256 payload, byte-count head, and terminal command receipt. Dictation must adapt to it; the kernel spine must not adapt to dictation.
7. **The current native terminal authority encoder cannot yet carry `direct_gesture`.** `holdspeak/delivery/commands.py:84-88` maps only `scoped_grant`, `control_posture`, and grant-required outcomes; its fallback at `:176-184` becomes `refused_by_policy`. HS-107-02 must add the existing `direct_gesture` decision to that process-input adapter and its decode table. This is driver adaptation, not a new authority basis and not a kernel-spine change.
