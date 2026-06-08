# Design — the Voice Commands board (HS-52-05)

The design spec for the centerpiece surface, produced with `ui-ux-pro-max` (design-system
pass: Dark/OLED, Inter, high contrast, SVG icons, visible focus, reduced-motion). It is
the source of truth for HS-52-05 and informs the macro model in HS-52-02 (design the
surface, derive the schema). Build target: an Astro page at `web/src/pages/commands.astro`
plus a behavior module, Signal styling, cards rendered at runtime go in `<style is:global>`.

## 0. Principle

**What you see is what fires.** This is a consent surface: the user accepts the risk by
configuring a command here, so the real action must be impossible to misread. Every card
and every editor reads back the exact action in plain language. Off by default; the master
switch and the safety posture are always visible.

## 1. Design tokens (Signal + the design-system pass)

- **Surfaces (dark/OLED):** background `#0E0F13` (near-black), card surface `#15171D`,
  raised/hover `#1B1E26`, border `#272B36`, divider `#1F232C`.
- **Text:** primary `#F4F6FB` (>= 4.5:1), secondary `#A4ABBA` (>= 3:1 for labels), muted
  `#6C7385`.
- **Brand / primary accent (Signal):** orange `#FF6B35` — the master-on state, the primary
  CTA ("Add command"), focus ring tint, primary buttons. Use it for ONE primary action per
  view; do not also color per-kind badges with it.
- **Per-kind hues (badge + card accent edge), one each so kinds are distinct at a glance:**
  - Open URL: sky `#38BDF8`
  - Launch app: violet `#A78BFA`
  - Type text: green `#34D399`
  - Shell: amber `#F59E0B` (the "runs code" signal; the command text itself uses the danger
    red `#EF4444` accents). Shell is the only kind that carries a warning treatment.
- **Semantic:** test-success green `#22C55E`, danger red `#EF4444`, focus ring `#FF6B35` at
  2px with a 2px offset (always visible, keyboard-first).
- **Type:** Inter. Scale 12 / 13 / 14 / 16 / 20 / 28. Keyword chips and previews of
  commands use a mono stack (`ui-monospace, SFMono-Regular, Menlo`) so a command reads as
  code. Weights: 700 headings, 600 labels/keywords, 400 body.
- **Spacing:** 4/8 system. Card padding 16. Grid gap 16. Section rhythm 16 / 24 / 32.
- **Radius:** cards 14, chips/badges 8, buttons 10. **Elevation:** card `0 1px 0 #FFFFFF08
  inset, 0 8px 24px #00000066`; raise on hover by 2px translate (transform only,
  reduced-motion disables it). **Motion:** 150-220ms ease-out; exits ~70%; respect
  `prefers-reduced-motion`.
- **Icons:** Lucide SVG, 1.75 stroke, 20px in cards / 16px in chips. No emoji in the build
  (the ASCII below uses glyphs only as placeholders).

## 2. Route + page skeleton

A dedicated route `/commands` (not a settings section). A discoverable entry from the
dashboard and settings links here.

```
/commands
┌─ header ───────────────────────────────────────────────────────────────┐
│  Voice Commands                                   Voice commands  ●━ On  │
│  Say a keyword while dictating and HoldSpeak runs the action instead of  │
│  typing it. You set every command, so you decide what runs.  [Learn more]│
└──────────────────────────────────────────────────────────────────────────┘
   (grid of command cards)                                  [ + Add command ]
```

- Header: H1 "Voice Commands" (28/700), one-line lede (14/secondary), and the **master
  switch** top-right with the label "Voice commands" + state. Off by default; when off, the
  grid is dimmed to ~0.55 and a thin banner reads "Voice commands are off. Turn them on to
  use them." (cards still editable while off).
- Primary CTA "Add command" (orange) is both a header-right action and the trailing
  add-card in the grid.

## 3. State A — populated board (card grid)

Responsive grid: `repeat(auto-fill, minmax(280px, 1fr))`, gap 16. Resizes 1 -> 2 -> 3+
columns. Each command is a card; a dashed "add" card trails the grid.

```
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ «terminal»          [Launch]·│  │ «ship it»            [Shell]·│  ← kind badge, color-edged
│                              │  │                  ⚠ runs code  │
│ opens Terminal.app           │  │ runs:  git push origin HEAD   │  ← live preview (mono)
│                              │  │                              │
│ matches: terminal            │  │ matches: ship it             │  ← normalized match hint
│ ───────────────────────────  │  │ ───────────────────────────  │
│ [ ▷ Test ]        [edit][del]│  │ [ ▷ Test ]        [edit][del]│
└──────────────────────────────┘  └──────────────────────────────┘
┌──────────────────────────────┐  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
│ «standup»            [Type] ·│  │            +                  │
│                              │     Add a command
│ types: "## Standup\n- Yest…" │  │  map a keyword to an action   │
│ matches: standup             │  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
│ ───────────────────────────  │
│ [ ▷ Test ]        [edit][del]│
└──────────────────────────────┘
```

### Command card spec
- **Left color edge** (3px) in the kind hue, so kind is legible without reading the badge.
- **Keyword chip** top-left: mono, 600, in a subtle pill (`#FFFFFF0D` bg), quotes optional;
  this is the spoken trigger.
- **Kind badge** top-right: Lucide icon + label (Open URL / Launch app / Shell / Type text)
  in the kind hue at low-alpha bg. Shell additionally shows an amber `⚠ runs code` tag.
- **Live preview** (the heart): one line, mono, reading the exact effect — `opens
  Terminal.app`, `runs: git push origin HEAD`, `opens https://github.com/...`, `types:
  "..."` (snippet truncated with title tooltip). For shell, `runs:` + the command in a
  faint red-tinted mono block.
- **Match hint:** `matches: <normalized keyword>` in muted 12, so the user knows what is
  actually compared (case-folded, trimmed).
- **Footer:** a **Test** button (ghost, left) and **edit** / **delete** icon buttons
  (right, 44px hit area, aria-labels). Delete asks an inline confirm ("Delete 'terminal'?
  [Cancel] [Delete]") — destructive in red, separated from other actions.

### Test affordance + feedback
- Test fires the macro through the real dispatch path. On press: button shows a 150ms
  spinner, then a transient inline result chip on the card: success = green check + "ran"
  (auto-dismiss 3s, `aria-live="polite"`); failure = red + the error (persists until
  dismissed, with a retry). Test never needs the mic; it is the trust-builder.

## 4. State B — empty state

Inviting, gets the first command in seconds. Centered panel, not a blank grid.

```
            ◇  (Signal mark, dim)
      No voice commands yet
  Map a keyword you speak to an action HoldSpeak runs.
  You set every command, so you decide what runs.

  Start with one:
   [ "terminal"  → open Terminal ]   [ "docs" → open a URL ]
   [ "standup"   → type a snippet ]  [ + Build my own     ]

  Voice commands run real actions on your machine. They are
  off until you turn them on.
```

- The starter chips are one-tap: they open the editor pre-filled with that example (kind +
  payload), so the user only confirms. "Build my own" opens a blank editor.
- Honest footnote about real actions + off-by-default, in muted text, no alarm styling.

## 5. State C — the adaptive editor (add / edit)

A focused panel/sheet over a scrim (40-60% black). Two fixed fields (keyword, kind) plus a
**morphing payload region** that swaps by kind. Live preview updates as you type.

```
┌─ New command ─────────────────────────────────────────────┐
│  When I say   [ terminal                              ]    │
│               matches: terminal   ⚠ already used by "open" │  ← conflict warning (if any)
│                                                           │
│  Do this      ▸ [Open URL] [Launch app] [Shell] [Type text]│  ← segmented; selected = kind hue
│                                                           │
│  ── payload region morphs by kind ──────────────────────  │
│  (Launch app)   App   [ Terminal                    ▾ ]   │
│  (Open URL)     URL   [ https://…                      ]   │
│  (Type text)    Text  [ multiline textarea            ]   │
│  (Shell)        Command                                   │
│                 ┌───────────────────────────────────────┐ │
│                 │ git push origin HEAD                  │ │  ← mono, red-tinted frame
│                 └───────────────────────────────────────┘ │
│                 ⚠ Runs this on your machine when you say  │
│                   the keyword. No confirmation.           │
│                                                           │
│  Preview:  runs: git push origin HEAD                     │  ← always-on "what fires" line
│  [ ▷ Test ]                           [ Cancel ] [ Save ] │
└────────────────────────────────────────────────────────────┘
```

### Adaptive editor spec
- **Keyword field:** under it, live `matches: <normalized>` and a **conflict warning** if
  another macro already claims that normalized keyword (amber, names the other command;
  non-blocking but loud).
- **Kind selector:** a segmented control; the selected segment takes the kind hue. Changing
  kind swaps the payload region (crossfade, reduced-motion = instant) and preserves the
  keyword.
- **Payload region per kind:**
  - Open URL: a URL input with `type=url`, inline validation on blur, a small favicon/host
    echo.
  - Launch app: an app field (free text + a suggest list of common apps); shows resolved
    target.
  - Type text: a mono textarea (the snippet), with a char count; preview shows the snippet.
  - Shell: a mono command box framed in faint red, with the honest one-line note "Runs this
    on your machine when you say the keyword. No confirmation." No nag, no block.
- **Preview line:** always visible above the buttons, the same plain-language string the
  card will show. This is the consent contract.
- **Test** in the editor fires the current (unsaved) action so the user verifies before
  saving. **Save** is the primary (orange); disabled until keyword + payload are valid.
- Escape / Cancel / scrim-click dismiss; confirm if there are unsaved edits.

## 6. The shell danger treatment (cross-cutting)

Shell is the only kind that runs arbitrary code, so it is honestly marked everywhere, but
never nags (the user owns the risk):
- Card: amber `⚠ runs code` tag by the badge; the command in a faint-red mono block.
- Editor: the red-framed command box + the one-line "runs on your machine, no confirmation"
  note.
- Color is never the only signal: the `⚠` glyph + the words "runs code" carry it for
  color-blind and screen-reader users (the tag has an `aria-label`).
- No modal gate, no per-fire prompt. Consent happened at config time, by design.

## 7. Master switch

- Top-right, labeled ("Voice commands" + On/Off), orange when on, neutral when off; the
  whole feature is off by default. A native checkbox under the hood (keyboard + screen
  reader), styled as a Signal toggle. When off, the grid dims and a thin banner explains;
  cards remain editable so a user can set up while off, then flip on.

## 8. Microcopy

- Lede: "Say a keyword while dictating and HoldSpeak runs the action instead of typing it.
  You set every command, so you decide what runs."
- Empty: "No voice commands yet" / "Map a keyword you speak to an action HoldSpeak runs."
- Shell note: "Runs this on your machine when you say the keyword. No confirmation."
- Off banner: "Voice commands are off. Turn them on to use them."
- Conflict: "already used by '<other keyword>'".
- Delete confirm: "Delete '<keyword>'?"

## 9. Accessibility + interaction (desktop-first, keyboard-first)

- Every action reachable by keyboard; visible 2px orange focus ring with offset; logical
  tab order (card -> Test -> edit -> delete).
- Icon-only buttons (edit/delete) carry `aria-label`; the kind badge and `⚠ runs code` tag
  have text, not color alone.
- Test result uses `aria-live="polite"`; errors `role="alert"`.
- Hit areas >= 40px; hover and focus states distinct; cursor-pointer on clickables.
- `prefers-reduced-motion`: no translate/scale, crossfades become instant, Test spinner
  becomes a static "running".
- Responsive: grid reflows 1/2/3+ columns; editor panel is centered and width-capped; works
  in a resized desktop window down to ~480px.

## 10. Implications for the macro model (HS-52-02)

Designing the surface first pins the schema. A `VoiceMacro` needs exactly:
- `keyword: str` (stored as typed; the matcher normalizes case-fold + trim).
- `action.kind: "open_url" | "launch_app" | "shell" | "type_text"`.
- `action.payload`: the kind's single field (url / app / command / text).
- a derived, never-stored **preview string** the card and editor render ("opens
  Terminal.app", "runs: ...") — compute it from kind+payload in one place so the UI and any
  audit log read identically.
No more fields than the editor shows. Keep it that tight.
