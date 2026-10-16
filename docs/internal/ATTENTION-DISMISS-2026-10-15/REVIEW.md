# Source counsel — attention dismissal

2026-10-15. Bounded source review; no product edits or test/UI runs.
This is worker counsel, not Muad'Dib's formal review.

VERDICT: RATIFY within the reviewed source scope. No security, data-loss,
or severe functional regression found.

FINDINGS: No blocking finding. Dictation journal rows are excluded only
from popup selection (`web/src/components/AmbientLayer.tsx:358`). Dismiss
writes the visible ID, pins that row through pending/failure, retries the
same ID, and advances the cutoff only after success
(`web/src/components/AmbientLayer.tsx:355`, `:366`, `:381`). The writer's
boolean is based on its own request outcome (`web/src/desk/projections.ts:134`).
The ref guard and library loading state prevent duplicate presses
(`web/src/components/AmbientLayer.tsx:367`, `:475`);
the doorless projection branch remains safe (`:440`). Storage refusal
retains the cutoff in module memory for remounts
(`web/src/components/ambientAttentionCutoff.ts:5`, `:15`).

CONDITIONS: None from source counsel. Root owns the quick check and
1440/393 UI verification.

MISSED: Nonblocking sampler limitation: ambient still requests only the
four newest attention rows (`web/src/desk/projections.ts:120`), before
Qlippy excludes dictation. Four newer dictation rows can therefore hide
an eligible fifth row from the popup. It remains in Attention. This
change does not establish exhaustive popup delivery; root will record
the limitation for a later use-driven decision. Tenet 3 applies if the
sampler proves to hide a useful interruption.

TUESDAY: The source now lets one successful Dismiss quiet historical
attention while leaving its reader/history intact.

UNKNOWN: Runtime behavior, screenshots, and test outcomes were not
verified in this counsel. With sessionStorage denied, module memory can
survive remounts but cannot survive a full page reload. Delivery outside
the existing four-row ambient sample is not guaranteed.
