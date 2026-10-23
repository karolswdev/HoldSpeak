# What nearly OS-native means for HoldSpeak

Research and proposed design criteria, 2026-10-23; baseline PR1428. This is
not a new visual theme, a browser capability claim, or a replacement for the
Constitution and UX-CANON. The owner's Workbench meets Pop!_OS direction stays.

## Experience thesis

A desktop experience earns trust when the same action has the same result,
attention stays with the user's work, and objects remain where the user put
them. Polished painting matters, but cannot compensate for lost selection,
unstable focus, an inaccessible action, or an opaque wait. HoldSpeak should
provide that behavior through complete production patterns in the existing
React/DOM framework.

Use desktop HIGs as evidence about interaction and information hierarchy.
Do not import a platform's visual theme or its modal conventions. Apple's
[keyboard guidance](https://developer.apple.com/design/human-interface-guidelines/keyboards)
asks apps to respect established shortcuts and provide keyboard access.
Its [layout guidance](https://developer.apple.com/design/human-interface-guidelines/layout)
connects importance, placement and alignment. GNOME's
[adaptive guidance](https://developer.gnome.org/hig/guidelines/adaptive.html)
treats different window sizes as normal desktop use, not just a phone mode.
Those principles fit the existing Desk model.

## A visible system with a quiet interior

The frame names the window, exposes feedback and window actions, and conveys
front/inactive state. The content starts with the task or outcome. A reading
surface, preferences editor, collection and conversation need distinct
compositions within one material system. Do not turn every window into a
stack of bordered cards, or repeat a frame title as a content heading.

Continue the current type tokens and 12px readable floor, 32px ordinary
desktop controls and 44px narrow hit ownership. Improve hierarchy through
alignment, restrained weight, group spacing and readable measure before
adding more colors, labels or decorative plates. Keep sentence-case control
labels and reserve compact mono metadata for its existing roles. GNOME's
[typography guidance](https://developer.gnome.org/hig/guidelines/typography.html)
supports a small intentional type vocabulary and discourages pervasive caps.
It does not authorize replacing HoldSpeak's established font or token choices.

Selection, keyboard focus, front-window activation, hover, pressed, disabled
and busy are different states. Give each an identifiable treatment; an
inactive selected row should retain its selection without impersonating the
active input target. Apple's
[focus and selection guidance](https://developer.apple.com/design/human-interface-guidelines/focus-and-selection/)
is a useful reference for that distinction. Screen-reader state and visible
state must describe the same object.

## Input must feel like the user's machine

Use real inputs, textarea elements and the existing CodeMirror editor. Keep
selection ranges, platform editing commands, undo, composition and clipboard
behavior. A field does not become less native because its border is custom;
it becomes less native when an incoming render replaces the caret or the
app interprets an IME completion key as Send.

Voice remains a first-class input through the existing microphone authority.
A shared insertion adapter should specify target identity, selection at
capture, late-result behavior and undo semantics for simple fields and rich
editors. Do not assume every voice result should replace the whole value or
append at the end. Preserve the current retained-audio recovery path; a
re-render or an abandoned form must not route a late result into a different
field. Any change to the existing insertion policy needs explicit behavior
proof, not a global text-replacement patch.

The current command registry remains authoritative. Menus, shortcuts and
visible verbs should describe the same operation and availability. Browser
and OS reserved shortcuts remain constraints; an in-page Desk cannot promise
to receive every Command/Control chord. Editor and IME handling takes
precedence over global Desk shortcuts. Escape dismisses the innermost
transient context first and returns focus to a valid trigger; ordinary Desk
windows are non-modal and must not acquire modal focus traps.

## Spatial continuity is a framework responsibility

A window head must reserve its fixed controls, give its title a clear yielding
rule, fold navigation when needed, and retain an intentional drag region.
These are one head contract, not a negotiation among feature stylesheets.
Use the current mounted compositor authority; do not add a second front or
window registry. User placement and explicit input outrank incidental runtime
updates that would otherwise raise a window or steal attention.

Each ordinary window owns one primary content scroller. A source preview,
editor or terminal may have a bounded internal scroller when its task calls
for one. Streaming follows the end only while the reader was following it;
reading older content or selecting text stops automatic following. Collection
selection uses stable object identity and survives sorting, filtering,
refresh, narrow list/detail navigation and restoration.

The framework owns reflow by the window container, including awkward widths
between the desktop and phone snapshots. Test long labels, missing metadata,
slow data and populated content. User zoom, larger text, reduced motion,
high contrast and mixed input devices are part of this design space. A
1440px screenshot alone says little about a 560px floating window on it.

## Every transition has a believable outcome

Typing and selection stay immediate. A local state change shows feedback
without waiting for a network request. Longer operations identify what is
working and provide real recovery. Show cancellation only when the operation
supports it. A captured request and a newer draft remain separate: retrying
one must preserve the other. An external revision must not silently replace
unsaved work.

Receipts describe actual outcomes. A failed write keeps the draft; a refusal
names the reason; an indeterminate remote outcome does not invite a blind
retry. Existing authority, egress and operation contracts stay in the backend.
Shared presentation/controller patterns must not duplicate those policies or
optimistically report an irreversible delivery as complete.

## The reference must be the product's paved road

The Components window should render the same production pattern components
used by Settings, Ask and People, with fixture-backed adapters for their
states. It should be possible to reproduce a rejected save, a newer draft
during retry, a long source, an empty collection and a lost connection there.
It must not become a second implementation that looks correct while real
windows retain different layout and behavior.

Judge the experience with paired task evidence: inspect the actual window
at useful widths, complete its job with pointer and keyboard, retain the
relevant selection/draft/scroll state, inspect a local timing trace, and
capture its state with the existing feedback engine. Automated correctness
and source adoption are separate from the owner's visual acceptance. A
working reference and a merged PR are intermediate evidence, not proof that
the application is delightful.
