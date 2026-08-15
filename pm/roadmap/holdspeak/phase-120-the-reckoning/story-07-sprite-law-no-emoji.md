# HS-120-07 — Sprite law, no emoji

- **Project:** holdspeak
- **Phase:** 120
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-120-11 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

The Signal Workbench material language uses pixel-art sprites and
monochrome SVG glyphs. Platform emoji are banned — they render
differently across OS/browser, break the flat mono aesthetic, and
sometimes show color where the desk is intentionally monochrome.
Multiple surfaces violate this:

1. **SessionPullout** (`SessionPullout.tsx:695`): Window icon renders
   raw `🙋`/`🤖` emoji.
2. **EmptyDesk** (`EmptyDesk.tsx:24`): App identity mark is raw `◍`
   (Unicode dotted circle) at 44px instead of the `SYSTEM.menuMark`
   sprite used in the chrome.
3. **WorkbenchesHomeCore**: Agentless cards render `⚙` at 14px/0.6
   opacity (covered by story 01, but the sprite vocabulary applies
   here too).
4. **SurfaceWings** (`wings.tsx:119`): Configuration door renders raw
   `⚙` emoji where other chrome uses SVG glyphs.
5. **SurfaceState** (`Surface.tsx:156-190`): Loading `◌`, error `⚠`,
   empty `○` — raw Unicode characters where `⚠` can render as color
   emoji on some platforms.

When this ships, every listed surface uses system sprites, monochrome
SVG glyphs, or the approved desk glyph vocabulary. Zero platform emoji
in desk chrome.

## Acceptance criteria

- [ ] SessionPullout icon: system sprite or AgentAvatar, not emoji.
- [ ] EmptyDesk identity mark: `SYSTEM.menuMark` sprite.
- [ ] SurfaceWings door: SVG glyph or monochrome text glyph, not `⚙`.
- [ ] SurfaceState: monochrome text glyphs forced to text presentation
      (append U+FE0E) or replaced with approved desk vocabulary.
- [ ] Grep: no raw emoji in desk chrome components (audit confirms).

## Test plan

- Visual: open a session pullout, verify sprite icon.
- Visual: load an empty desk, verify system sprite mark.
- Visual: open a surface with wings + door, verify monochrome glyph.
- Visual: trigger loading, error, empty states, verify no color emoji.

## Files in scope

- `web/src/desk/components/SessionPullout.tsx`
- `web/src/desk/components/EmptyDesk.tsx`
- `web/src/desk/surface/wings.tsx`
- `web/src/desk/surface/Surface.tsx`
