VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **P2 — Full-width text editors remain capped by the standard-width rule.**
   `web/src/desk/surface/gadgets.css:1205` selects direct non-stepper text
   gadgets with specificity `(0,5,0)` and sets their width to the shared
   190 px value (`:1206`; 172 px below 560 px at `:1294`). The intended
   `controlWidth="full"` override at `:1221` has specificity `(0,4,0)`, so
   it loses even though it occurs later. Full rows have one grid column,
   but their direct text well retains the short cap. Settings uses this
   shape for Mic device (`web/src/pages/cores/SettingsCore.tsx:2095`),
   System audio name (`:2103`), generic strings (`:1641`) and comma-separated
   fields (`:1717`). This contradicts the shared contract at
   `web/src/desk/surface/contract.md:51` and narrows the editing area for
   names and lists. **Tenets 3 and 5:** preserve useful editing room and
   make the library's explicit layout option work. Correct the selector
   precedence in the shared library and retain the standard-width cap.

CONDITIONS:

Fix finding 1 at the shared CSS seam. Confirm that a direct StringGadget
under `controlWidth="full"` fills its available slot at both widths while
an ordinary row retains its bounded value column. One source re-check of
that correction remains available. This report does not replace the
root's focused checks and production captures.

MISSED:

1. The new primitive checks verify slot DOM and state semantics but do not
   verify the CSS outcome of `full` width
   (`web/src/desk/surface/gadgets.test.tsx:29`). The specificity collision
   can therefore pass those assertions.

TUESDAY: The source keeps direct ordinary choices, one Add symbol action, armed Forget and the existing recovery paths; useful room for longer text still needs finding 1 corrected, and live usability remains unverified by this review.

UNKNOWN:

- Source-only review against `22de063e3`, limited to the changed shared
  surface and Settings adoption. No tests, builds, browsers, installs,
  native access or owner-state walks were run. No product code was edited.
- The opt-in wrappers retain native inputs and accessible names; the diff
  does not change the 700 ms writer/revision/retry logic, calendar Save
  custody, owner-name blur flush, alias implementation, environment-held
  access, or action egress. This is a source observation, not a runtime pass.
- Actual fit, pointer ownership, focus behavior and appearance at 1440 and
  393 are the root's capture responsibility. In particular, inspect enabled
  Remote access with an address and nonzero credential count: its three
  control-slot children remain at
  `web/src/pages/cores/SettingsCore.tsx:959`, while the new slot at
  `web/src/desk/surface/gadgets.css:1203` does not restore the wrapping
  excluded for inset modules at `web/src/pages/cores/settings.css:324`.
  No measured overlap or collapsed control is claimed here.
- No owner acceptance or Muad'Dib check is claimed.
- **DRAFT — UNCHECKED — awaiting Muad'Dib. HOLD FOR SHIP.**

---

Final bounded source re-check — 2026-10-14. This result supersedes the
initial source verdict above; the initial findings remain as history.

VERDICT: RATIFY

FINDINGS:

None remaining in the requested source re-check.

- Initial finding 1 is resolved at
  `web/src/desk/surface/gadgets.css:1223`: the full text-well selector now
  has specificity `(0,5,0)`, matching the standard rule at `:1205`, and
  wins through its later position. Standard rows retain the bounded rule
  at `:1206`. The opt-in slots restore wrapping at `:1203`; the tracking
  adjustment at `:1209` remains inside the opt-in selectors.
- The new symbol buffer lives at SettingsFace scope
  (`web/src/pages/cores/SettingsCore.tsx:1294`), so Back/module navigation
  does not unmount it. Add only changes this local buffer (`:1841`), and
  patches/Forget use `writeSymbols` (`:1787`, `:1853`). Empty required
  fields stay outside the settings document; complete arrays, including
  an empty array after Forget, use the existing `update` writer (`:1790`)
  and its queue/debounce (`:1477`). No alternate save endpoint is added.
- Draft release waits for the exact symbol path to leave the debounced,
  failed and pending jobs (`:1372`) and for the authoritative array to
  match (`:1379`). An unrelated write cannot replace a different local
  buffer. Refused or older symbol writes cannot clear a newer incomplete
  buffer; Retry retains the existing exact-path rule at `:1518`.
- The final comparison trims the spoken phrase, preserves the literal
  symbol and normalizes attachment names (`:1383`), matching
  `holdspeak/config/meeting.py:330`. Completeness uses nonempty symbol
  length (`SettingsCore.tsx:1789`), so a literal-space symbol can use the
  producer's existing contract.
- TTS egress, Download, receipt and failure are direct children of the
  shared wrapping action slot (`web/src/pages/cores/settingsTts.tsx:97`),
  and the ready state still omits an empty footer. HotkeyCapture retains
  `grouped=true` by default
  (`web/src/pages/cores/settingsBespoke.tsx:47`). The frame padding
  correction is confined to inset Settings content
  (`web/src/pages/cores/settings.css:404`).

CONDITIONS:

No remaining source condition from this bounded review. Root still owns
the pending production build, focused/combined checks, real-producer
symbol cases, and 1440/393 fit and pointer captures. This source verdict
does not certify those results.

MISSED:

The producer normalizes spoken phrases and attachment names while
preserving literal symbol text (`holdspeak/config/meeting.py:330`). The
final buffer predicate/comparison now follows that distinction; the
reported live check for trimmed phrases and literal-space output remains
pending with root.

TUESDAY: Source now supports a local incomplete symbol row, recovery without overwriting newer edits, and full-width longer editors; the owner's live judgment remains outstanding.

UNKNOWN:

- This was the one final source re-check, limited to the named corrections
  and the new symbol-buffer seam. No broader audit was reopened.
- No tests, builds, browsers, installs or owner-state walks were run by
  this reviewer. No product code, staging or commits were performed.
- Runtime normalization, refused-save recovery, rendered width, target
  ownership and visual quality remain root's pending verification.
- No owner acceptance or Muad'Dib check is claimed.
- **DRAFT — UNCHECKED — awaiting Muad'Dib. HOLD FOR SHIP.**
