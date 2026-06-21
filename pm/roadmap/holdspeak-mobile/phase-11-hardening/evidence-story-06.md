# Evidence — HSM-11-06 (On-device generation robustness — structured-output salvage)

**Date:** 2026-06-21 · **Status:** done

The on-device artifact-generation parse path is now robust to real 4B-model drift. This is a
**host story** — pure, model-free, fully tested without a device — that directly de-risks the
pending HSM-8-06 device gate by turning formatting drift that used to cost an artifact
(`noJSON`/decode failure) into a recovered parse.

## What shipped (`StructuredOutput`, Providers)

- **Balanced extraction** — `firstBalancedJSON` scans for the FIRST complete, brace-balanced
  `{…}`/`[…]` respecting strings + escapes, replacing the old first-`{`-to-**last**-`}` grab.
  Trailing prose, a second object, or a `}`/`[` *inside a string value* no longer break it.
- **Truncation salvage** — if the model is cut off, an open string is closed and the open
  brackets are appended, so a truncated-but-mostly-there object still decodes (the title +
  early fields survive). Handles cut-after-value, cut-mid-string, and cut-in-a-nested-field.
- **Conservative repair** — smart quotes → straight, value-position `True`/`False`/`None` →
  `true`/`false`/`null` (regex-anchored to value position so a body's prose is untouched),
  and **string-aware** trailing-comma removal (a comma inside body text is never touched).
- **Array unwrap** — a model that returns `[{…}]` when one object was asked for decodes the
  inner object instead of failing.
- The repair-retry loop remains the backstop for anything salvage can't recover; its re-prompt
  is sharpened ("one valid JSON object … no prose, no fences, no trailing commas").

## Tests (ran)

`swift test` → **197 passed / 6 skipped / 0 failed** (+15 `StructuredOutputRobustnessTests`):
trailing-prose-with-stray-brace, brace-in-string, two-objects→first, nested balance, trailing
comma, Python literals, **repair-leaves-string-content-alone** (a body containing `True` and
`[1,2,]`), smart quotes, truncated-no-closer, truncated-mid-string, truncated-nested, array
unwrap, pure-prose→nil, clean-unchanged, fenced-with-tag. The existing `InferenceTests`
(extract / decode / repair-retry succeed + exhaust) stay green — **no regressions**.

## Acceptance

- **Balanced extraction** ignores trailing prose / a second object / a brace in a string. ✅
- **Truncation salvage** closes + decodes a cut-off object (incl. mid-string). ✅
- **Conservative repair** fixes trailing commas / Python literals / smart quotes without
  corrupting string contents (proven by the leave-string-alone test). ✅
- **Array unwrap** decodes `[{…}]` to the inner object. ✅
- **No regressions** — prose-with-no-JSON still returns `nil` (retry loop still fires +
  exhausts); clean/fenced JSON still extracts exactly. ✅

## Note

This reduces `noJSON` losses but does **not** replace the HSM-8-06 device gate — that still
proves the four artifact types generate on the physical iPad (the fresh-provider fix +
this salvage together). See the phase-8 "Pending device verification" section.
