# HSEGHS001HS104-142-03 - One Model Chooser

- **Project:** holdspeak
- **Phase:** 142
- **Status:** done
- **Depends on:** HSEGHS001HS104-142-02
- **Unblocks:** (optional)
- **Owner:** HoldSpeak orchestration

## Problem

Models currently renders detected local artifacts as oversized, dead inventory
cards and renders suggested downloads/hosted choices in a separate chooser.
Owners cannot select an already-present GGUF and can easily miss the catalog.

## Scope

- **In:** one compact selectable model chooser; server-owned activation of an
  existing detected GGUF; exact unsupported MLX truth; a pinned tiny Qwen local
  option; a broader current OpenRouter catalog; HTTP/MCP parity; 1440/393 glass.
- **Out:** MLX Thought execution, automatic recommendation claims, utility-route
  execution distinct from Thoughts, silent downloads, or model-authored setup.

## Acceptance criteria

- [x] Detected, downloadable, and hosted models participate in one radiogroup
  and one stable action seat; unselected rows remain compact.
- [x] A projected detected GGUF can be selected and activated through one
  owner-only idempotent application command without exposing its locator.
- [x] MLX remains selectable for explanation but exposes no false Use action.
- [x] The signed catalog includes a pinned ~1B local Qwen and at least five
  current OpenRouter choices with outcome-first copy and exact model Details.
- [x] Backend/API/MCP, focused web tests, and isolated 1440/393 glass pass.

## Test plan

- **Unit:** detected-ref resolution/privacy, existing-file hash/adoption/replay,
  route conflict/runtime refusal, catalog signatures, chooser state/copy.
- **Integration:** reciprocal HTTP/MCP command envelopes and setup refresh.
- **Manual / device:** real existing GGUF activation plus compact chooser at
  1440/393 with one action seat, keyboard selection, and no overflow.

## Notes / open questions

The ~1B preset is a fast local option suitable for intent/lightweight work, not
a claim that a separate utility-routing subsystem ships in this story.
