# Browser and platform path

Research date: 2026-10-23. Baseline: `787c55c80` (PR1428). This note is
research, not a shipped capability or owner aesthetic acceptance.

## Decision

Keep ReactDOM and the Desk compositor. The browser is the rendering/input
surface, not an operating-system window manager. Use a typed adapter around
DOM input, layout, overlays and timing. React asks it for capabilities, with a
plain DOM/CSS fallback and an honest state for unavailable permissions.

This supports Workbench-like drag, resize, focus, selection, menus and
scrolling. ReactDOM can receive a user-granted `DataTransfer` file drop and
permissioned `getDisplayMedia()` output. It does not turn a browser into an
AppKit window: system-wide file-manager commands, native widgets and OS
window/source control remain outside ReactDOM. Use the existing Python/AppKit
boundary when needed.
Do not add Tauri, Electron or another UI runtime.

## Capability findings

| Area | Practical baseline | Progressive path and boundary |
| --- | --- | --- |
| Drag and resize | Pointer Events, `touch-action`, `setPointerCapture`, `lostpointercapture`; update the model in one `requestAnimationFrame`. Pointer capture keeps later events targeted at the active handle, including when the pointer leaves its box ([Pointer Events](https://www.w3.org/TR/pointerevents/latest/)). | Feature-detect pointer capture. Keep a mouse/touch event fallback for old embedded WebViews. Do not use HTML drag-and-drop for Desk window physics. Preserve Firefox coverage: pointer cancel, capture loss, Escape, touch scrolling and keyboard resize all need tests. |
| Focus and selection | Native focusable elements, `:focus-visible`, roving focus only where a real composite widget needs it, and normal text selection. A pointer grab may raise and activate an inactive window. Preserve an existing caret/range when drag starts in an editor; do not focus a new editor or replace its selection as a drag side effect. | A drag ghost may be painted, but the source remains the accessible selection owner. A virtual list must retain a selected item and restore focus by stable id, not by DOM index. |
| Container layout, subgrid and intrinsic sizing | Use named `@container` queries with `min-width: 0`, `minmax(0, 1fr)` and explicit overflow. `container-type` changes intrinsic sizing ([CSS Containment](https://www.w3.org/TR/css-contain-3/)). Subgrid shares parent tracks and can make sizing multi-pass ([CSS Grid Level 2](https://drafts.csswg.org/css-grid/)). WebKit documents Safari container queries/subgrid; Firefox documents name-only queries ([Safari 16](https://webkit.org/blog/13152/webkit-features-in-safari-16-0/), [Firefox 149](https://developer.mozilla.org/en-US/docs/Mozilla/Firefox/Releases/149)). | Gate newer query/subgrid syntax with `@supports` and retain simple grid/flex first. Test long titles, replaced content, nested containers and 393px. |
| Scrollbars and containment | `scrollbar-gutter: stable` reserves space for classic, not overlay, scrollbars; side, width and appearance remain UA/OS choices ([CSS Overflow](https://www.w3.org/TR/css-overflow/)). | Use stable gutters only where movement hurts controls. `::-webkit-scrollbar` at `web/src/styles/global.css:660-684` is CSS paint, not a native widget. Use `content-visibility` with an honest `contain-intrinsic-size` only for cold lists; never on focused, selected or actively dragged content. |
| Non-modal menus | The HTML Popover API supplies a browser-managed top layer and light dismiss, but it does not supply menu ARIA or menu keyboard behavior ([HTML popover](https://html.spec.whatwg.org/multipage/popover.html#the-popover-attribute)). Firefox's BCD record identifies the base `popover` attribute separately from newer `hint` support ([Firefox 149](https://developer.mozilla.org/en-US/docs/Mozilla/Firefox/Releases/149)). | Use it as a placement/lifecycle substrate for the existing DeskMenu: retain its ARIA, roving keys and focus return. Do not turn it into a Disclosure or assume automatic menu semantics. Top-layer elements escape the shell z ladder and can cover the dock or an active window; test placement, Escape, focus return and close-on-navigation. |
| Anchor positioning | CSS anchor positioning can tether a menu to a trigger and try alternate positions when it would overflow ([Chrome anchor positioning](https://developer.chrome.com/docs/css-ui/anchor-positioning-api/)). | Detect `CSS.supports("anchor-name: --desk-anchor")`. If false, use measured absolute positioning or the in-flow menu. Anchor positioning is not permission to skip collision tests, clipped ancestors, zoom, RTL or 393px geometry. |
| Motion | Use WAAPI or compositor-friendly transform/opacity; reduced motion means no movement. Same-document View Transitions are optional and have a direct fallback ([Chrome SPA View Transitions](https://developer.chrome.com/docs/web-platform/view-transitions/same-document), [WebKit Safari 18](https://webkit.org/blog/15865/webkit-features-in-safari-18-0/)). | Feature-detect `startViewTransition`; keep focus/selection outside its snapshot. Skip it while dragging, typing, composing or when reduced motion is on. |
| Capture, clipboard, drop and IME | Keep native inputs and composition events; keyboard events alone do not describe IME state ([UI Events](https://www.w3.org/TR/uievents/)). Use user-initiated copy/paste and `DataTransfer` drops. | Clipboard access is permission/focus-sensitive ([Clipboard API](https://www.w3.org/TR/clipboard-apis/)); `getDisplayMedia()` is user-selected and permissioned ([Screen Capture](https://www.w3.org/TR/screen-capture/)). On denial, show a named state and retain the last screenshot/selection. OS window commands need Python/AppKit. |

### Current BCD matrix

Raw MDN browser-compat-data records accessed 2026-10-23. Versions are first
supported versions; “future” means do not make it a baseline without checking
the target release. BCD records: [popover](https://raw.githubusercontent.com/mdn/browser-compat-data/main/html/global_attributes.json), [anchor](https://raw.githubusercontent.com/mdn/browser-compat-data/main/css/properties/position-anchor.json), [same-document View Transitions](https://raw.githubusercontent.com/mdn/browser-compat-data/main/api/Document.json), [content visibility](https://raw.githubusercontent.com/mdn/browser-compat-data/main/css/properties/content-visibility.json), [LoAF](https://raw.githubusercontent.com/mdn/browser-compat-data/main/api/PerformanceLongAnimationFrameTiming.json).

| Feature | Chromium | Firefox | Safari/WebKit | Decision |
| --- | --- | --- | --- | --- |
| `popover` attribute | 114 | 125 | 17 | Baseline, still probe. |
| `position-anchor` | 151 full; 125–150 partial | 151 full; 147–150 partial | 27 full; 26 partial | Future enhancement; fallback. |
| `document.startViewTransition` | 111 | 144 | 18 | Progressive enhancement. |
| `content-visibility` | 85 | 125 | 18; `auto` partial until 26 | Profile and protect focus/search. |
| Long Animation Frames | 123 | Not supported | Not supported | Chromium-only diagnostic; use rAF traces elsewhere. |

The partial `position-anchor` entries include differences in the initial
keyword (`implicit`/`auto`/`none` versus `normal`); they do not mean explicit
named anchors are uniformly unusable before the listed full-support version.
Probe the needed properties and behavior separately.

### Observed installed-engine probes

Root ran `scripts/probe_ui_capabilities.py` under the test lock with isolated
HOME on macOS 26.2 arm64, 2026-10-23. These are parser/API-exposure checks on
`about:blank`, not layout, application, performance or accessibility passes.

| Engine | Version | Common probes | Named anchors | Long Animation Frames |
| --- | --- | --- | --- | --- |
| Chromium | 143.0.7499.4 | Present | Present | Present |
| Firefox | 144.0.2 | Present | Absent | Absent |
| Playwright WebKit | 26.0 | Present | Present | Absent |

Common probes: base popover, `startViewTransition`, content visibility,
subgrid, inline-size containers, pointer capture and Event Timing. Presence
of an API does not establish every subfeature or correct rendering. Installed
Safari, the owner's Firefox application, and native WKWebView are not the
same thing as these isolated automation engines.

Reproduce on this Mac after the development environment and browser binaries
are installed. This invocation actually isolates HOME, retains the real browser
cache, uses the existing lock and removes its scratch home afterward:

```sh
python3 - <<'PYPROBE'
import os
from pathlib import Path
import subprocess
import tempfile
real_home = Path.home()
with tempfile.TemporaryDirectory(prefix="holdspeak-ui-probe-") as scratch:
    env = dict(os.environ, HOME=scratch,
               PLAYWRIGHT_BROWSERS_PATH=str(real_home / "Library/Caches/ms-playwright"),
               UV_CACHE_DIR=str(real_home / "Library/Caches/uv"),
               UV_NO_SYNC="1", HOLDSPEAK_SKIP_WEB_BUILD="1")
    subprocess.run(["uv", "run", "python", "scripts/test_lock.py", "--",
                    "python", "scripts/probe_ui_capabilities.py"], env=env, check=True)
PYPROBE
```

Optional missing APIs report false independently; they must not erase the
rest of an engine's report. A missing engine or a genuine probe failure is
still an error with nonzero exit. The probe makes no hub request, permission
prompt or owner-data change. This is not an application test.

### Typed adapter boundary

The future adapter should expose capabilities as data, for example:

```ts
type BrowserCapabilities = {
  pointerCapture: boolean;
  popover: boolean;
  anchorPositioning: boolean;
  viewTransitions: boolean;
  contentVisibility: boolean;
  eventTiming: boolean;
  longAnimationFrames: boolean;
  displayCapture: boolean;
};

type DeskPlatform = {
  capabilities: BrowserCapabilities;
  beginPointerGesture(handle: Element, event: PointerEvent): void;
  openMenu(trigger: Element, menu: HTMLElement): void;
  captureScreen(): Promise<"captured" | "denied" | "unsupported">;
};
```

Names are illustrative. Centralize detection; return typed outcomes; do not
silently change consent or data ownership. Probe features, not browser brands.

## Performance: local proof, not telemetry

Measure locally with DevTools recordings, React Profiler and rAF traces.
Profiler `onRender` gives render durations and a `commitTime` timestamp; the
browser trace covers commit, layout and paint ([React Profiler](https://react.dev/reference/react/Profiler)). No analytics or network beacon: this is local-first.

Event Timing measures input to next rendered update, but excludes
`pointermove`/`touchmove`; INP covers completed drag/menu actions, not every
drag frame ([Event Timing](https://www.w3.org/TR/event-timing/)). Record rAF
timestamps for drag. Gate Long Animation Frames with
`PerformanceObserver.supportedEntryTypes`; use rAF/DevTools in Firefox/WebKit
([Chrome LoAF](https://developer.chrome.com/docs/web-platform/long-animation-frames)).

Proposed budgets, not measurements of this baseline:

* A drag frame has at most one state write and one rAF; target under 16.7ms
  at 60Hz and no avoidable forced layout.
* A completed click, key or menu interaction targets under 200ms to visible
  feedback; this is not a current INP claim.
* Profile a large collection before virtualizing it; small lists stay normal
  DOM and do not pay virtualization complexity.

When profiling justifies virtualization, require stable item ids, an active
row kept mounted, selection in state rather than DOM presence,
`aria-setsize`/`aria-posinset` only when truthful, and a restoration test for
focus after prepend, filter, resize and scroll. If those safeguards cost more
than the list saves, use paged rendering or `content-visibility` on measured
groups instead.

## Delivery matrix

| Ship class | Scope |
| --- | --- |
| Baseline now | Pointer capture with fallback; native focus/selection/IME; container-query layout with CSS fallback; stable scroll ownership; WAAPI/rAF drag loop; reduced-motion branch; local performance trace recipe. |
| Progressive next | Popover menus; anchor positioning; same-document View Transitions; measured cold-list containment; clipboard/screen-capture adapters with denial states. Each gets Firefox, WebKit and Chromium probes. |
| Native integration boundary | System-wide shortcuts, OS-managed window movement, Finder/file-manager transfer and native capture use the existing native boundary when required. This does not defer application command routing, internal drag/drop, browser file drop or explorer behavior; those are core desktop-framework work. See the application model. |

## Unknowns and risks

* App geometry and focus were not measured; budgets are not pass/fail results.
* Check exact Firefox/WebKit support for anchor, View Transition Level 2 and
  LoAF subfeatures before use; probes and fallback are mandatory.
* Top-layer painting can conflict with the shell z ladder. Require 1440/393
  shots plus focus/Escape checks before Popover.
* Tuesday: this can feel OS-like inside a browser, but true OS window
  ownership still needs the native boundary.

## Sources

Primary specifications and vendor documentation, accessed 2026-10-23:

1. [W3C Pointer Events](https://www.w3.org/TR/pointerevents/latest/)
2. [W3C CSS Containment Level 3](https://www.w3.org/TR/css-contain-3/) and [CSS Grid Level 2](https://drafts.csswg.org/css-grid/)
3. [W3C CSS Overflow Level 3](https://www.w3.org/TR/css-overflow/)
4. [WHATWG HTML: Popover and drag-and-drop](https://html.spec.whatwg.org/multipage/popover.html)
5. [Chrome CSS anchor positioning](https://developer.chrome.com/docs/css-ui/anchor-positioning-api/)
6. [Chrome same-document View Transitions](https://developer.chrome.com/docs/web-platform/view-transitions/same-document)
7. [WebKit Safari 16 container queries/subgrid](https://webkit.org/blog/13152/webkit-features-in-safari-16-0/), [Safari 18 View Transitions](https://webkit.org/blog/15865/webkit-features-in-safari-18-0/) and [Mozilla Firefox 149 release notes](https://developer.mozilla.org/en-US/docs/Mozilla/Firefox/Releases/149)
8. [W3C Event Timing](https://www.w3.org/TR/event-timing/)
9. [Chrome Long Animation Frames](https://developer.chrome.com/docs/web-platform/long-animation-frames)
10. [React Profiler](https://react.dev/reference/react/Profiler)
11. [W3C UI Events and composition](https://www.w3.org/TR/uievents/)
12. [W3C Clipboard API](https://www.w3.org/TR/clipboard-apis/) and [W3C Screen Capture](https://www.w3.org/TR/screen-capture/)
