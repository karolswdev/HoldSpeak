# Presence source counsel

DRAFT — UNCHECKED, awaiting Muad'Dib. Independent worker counsel, not a formal
Muad'Dib check. 2026-10-16. One source pass; no product changes, tests, browser,
build or provider calls. This verdict concerns the completed Presence diff.

VERDICT: RATIFY

FINDINGS:

1. No concrete regression found in the reviewed diff. The activity subscription,
   label fallback, error precedence and connection-driven lamp-on expression
   remain unchanged (`web/src/pages/PresencePage.tsx:16`, `:18`, `:20`, `:31`).
   `useRuntimeFrame` still subscribes through the existing provider and returns
   its unsubscribe function (`web/src/runtime/RuntimeBus.tsx:128`). No runtime
   writer, transport or lifecycle code changed. This preserves Tenets 1 and 3.
2. Return uses one native library Button and the current query without parsing
   or rebuilding it (`web/src/pages/PresencePage.tsx:26`). The Button defaults
   to `type="button"` and forwards the single click handler
   (`web/src/components/signal/Button.tsx:32`, `:41`). BrowserRouter and the
   runtime provider remain mounted above App (`web/src/main.tsx:19`); returning
   needs no authentication bootstrap. Existing bootstrap captures and removes
   the arrival token before mounting (`web/src/main.tsx:12`,
   `web/src/lib/auth.ts:43`). Source shows no query or authentication regression.
3. The material repair stays local: Presence maps semantic ink/state tokens to
   existing Workbench tokens, uses existing floor and bevels, and introduces no
   new component or token (`web/src/styles/react-app.css:226`, `:257`, `:268`).
   SurfaceSection owns the caption/action strip
   (`web/src/desk/surface/Surface.tsx:130`); LampGadget's existing block variant
   enables wrapping (`web/src/desk/surface/gadgets.css:756`). The polite status
   region now surrounds only activity (`web/src/pages/PresencePage.tsx:30`).
   Source is consistent with Tenets 5 and 6 and the settled composition.

CONDITIONS:

None from source counsel. This does not certify final viewport geometry,
pointer ownership or live runtime output; those remain root's actual proof.

MISSED:

1. Inherited state limitation, not introduced here: an activity label remains
   visible when transport disconnects because the frame hook retains its last
   data (`web/src/runtime/RuntimeBus.tsx:130`) and the producer label takes
   precedence over the connection fallback (`web/src/pages/PresencePage.tsx:18`).
   The off lamp uses muted text (`web/src/desk/surface/gadgets.css:775`). Do not
   mistake a retained label for a new connection claim or silently change the
   prescribed mapping in this composition pass.
2. The component tests inspect all four declared connection states, error
   precedence, complete label text and exact duplicate/encoded query return
   (`web/src/pages/__tests__/PresencePage.test.tsx:50`, `:64`, `:74`, `:84`).
   Their hooks are mocked (`:7`), so they do not establish real frame delivery,
   reconnect sequencing, rendered wrapping or 44 px pointer ownership. Shared
   phone Button rules provide the intended target (`web/src/styles/global.css:184`);
   only root's actual walk can establish its ownership on this face.

TUESDAY:

Source supports reading one complete activity label and returning to Desk in
one native action; actual glass and runtime truth remain separately observed.

UNKNOWN:

No tests or runtime were run for this counsel, and no screenshots were read.
Root's accepted canvas and actual observations are reported context, not my
independent evidence. Live announcements, browser wrapping, nine target points
and post-return Desk behavior are outside this source-only verdict. Phone Home
and all other product lanes were excluded.
