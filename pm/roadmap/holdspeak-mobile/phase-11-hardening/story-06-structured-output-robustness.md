# HSM-11-06 — On-device generation robustness (structured-output salvage)

- **Project:** holdspeak-mobile
- **Phase:** 11
- **Status:** done
- **Depends on:** HSM-5-04 (StructuredOutput), HSM-6-01 (artifact engine)
- **Unblocks:** fewer `noJSON` losses on the pending HSM-8-06 device gate
- **Owner:** unassigned

## Problem

The on-device generation path turns a 4B model's free text into a contract value via
`StructuredOutput.extractJSON` → decode. Real-metal testing surfaced how fragile the
*parse* is: the model drifts (code fences, prose around the JSON, a stray brace in the
body text, truncation when it runs long, Python-style `True`/`None`, trailing commas), and
each drift becomes a `noJSON`/decode failure — a silently dropped artifact. The
fresh-provider fix removed the context-starvation cause of those failures, but the *parse*
itself is still brittle: `extractJSON` grabs first-`{`-to-**last**-`}`, which over-grabs
when prose (or a second object) follows, and it gives up entirely on truncation.

This story makes the salvage path robust and host-tested, so a well-fed model's
occasional formatting drift no longer costs an artifact — and the pending device gate sees
fewer losses.

## Scope

- **In:** harden `StructuredOutput` (Providers, host-side, on-device-agnostic) —
  (1) **balanced extraction**: scan for the FIRST complete, brace-balanced `{…}`/`[…]`
  respecting strings + escapes, so trailing prose, a second object, or a `}` inside a
  string value no longer breaks it;
  (2) **truncation salvage**: if the structure opens but the model was cut off, close the
  open string + the open brackets so a truncated-but-mostly-there object still decodes
  (the title/early fields survive);
  (3) **conservative repair**: smart quotes → straight, value-position `True`/`False`/
  `None` → `true`/`false`/`null`, and string-aware trailing-comma removal — none of which
  touch string *contents* by structure;
  (4) **array unwrap**: if the model wraps the object in a one-element array, decode the
  inner object rather than failing.
- **Out:** changing the prompts/engine (HSM-6) or the model. A full JSON5/JSON-repair
  grammar (the four targeted repairs above cover the observed 4B drift; more is
  speculative). Any device-specific code — this is pure, host-tested, on-device-agnostic.
  Grammar-constrained decoding (an engine-specific optimization, separate track).

## Acceptance criteria

- [ ] **Balanced extraction** returns the first complete structure and ignores trailing
      prose / a second object / a brace inside a string value — host-tested against each.
- [ ] **Truncation salvage**: a cut-off object (missing closer, or cut mid-string) is
      closed and decodes with the fields it did emit — host-tested.
- [ ] **Conservative repair**: trailing commas, value-position Python literals, and smart
      quotes are repaired without corrupting string contents — host-tested, including a
      string that legitimately contains `True`/a comma so repair leaves it alone.
- [ ] **Array unwrap**: `[{…}]` decodes to the inner object — host-tested.
- [ ] **No regressions**: text with no JSON still returns `nil` (the repair-retry loop
      still fires + exhausts), and clean/fenced/prose-wrapped JSON still extracts exactly
      — the existing `InferenceTests` stay green.

## Test plan

- Unit (host, model-free): a table of realistic messy 4B outputs → expected extracted/
  decoded result (clean, fenced w/ + w/o language tag, prose-wrapped, trailing prose with
  a stray brace, brace-in-string, two objects, `[{…}]`, trailing comma, Python literals,
  smart quotes, truncated-no-closer, truncated-mid-string, pure prose → nil). Plus the
  existing `InferenceTests` (extract + decode + repair-retry succeed/exhaust) stay green.

## Notes / open questions

- The four repairs are deliberately the *observed* 4B drifts, not an open-ended JSON5
  parser — bias toward conservative, never corrupting a valid body. The repair-retry loop
  remains the backstop for anything the salvage can't recover.
- This de-risks the HSM-8-06 device gate (fewer `noJSON` losses) but does not replace it —
  the gate still proves the four types generate on the iPad.
