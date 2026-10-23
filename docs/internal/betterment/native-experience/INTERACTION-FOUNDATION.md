# Interaction foundation for native-feeling HoldSpeak

**Status:** Research complete; implementation recommendations proposed  
**Research date:** 2026-10-23  
**Owner boundary:** fixed React/TypeScript/DOM stack; no replacement UI stack

## Outcome

Keep the current homegrown interaction framework. Make its behavior contracts
explicit and fix only diagnosed gaps. React Aria Components is a credible,
style-free source for one narrow gap, not a reason to replace `signal`,
`DeskMenu`, `WorkbenchSelect`, or the compositor. No package addition or React
upgrade is proposed here.

The worktree locks React and React DOM `19.2.7`, with Zustand 5 and React Query
5. It already has a runtime bus, composed desk store, shared signal Button,
native-select-backed picker, APG-like WorkMenu, roving rows, Ask gadgets,
non-modal focus return, and typed Settings, Ask, and People recovery flows.
This is a useful foundation, not a blank canvas.

Baseline anchors: `web/package.json:41-62`; RuntimeBus `:27-135`; signal Button
`:25-54`; WorkbenchSelect `:22-216`; DeskMenu `:1-145,523-677`; DeskWindow
`:1104-1121,1182-1362`; Settings `:1481-1672`; Ask `:457-558,779-1001`;
People `:206-430`.

## Evidence table

| Source and date | Capability | Decision implication | Caveat |
|---|---|---|---|
| [React versions](https://react.dev/versions); [React 19.3, 2026-09-09](https://react.dev/blog/2026/09/09/react-19-3) | 19.3 is latest; ViewTransition and Fragment Refs are stable. | Keep 19.2.7 as baseline; record 19.3 as future, not an upgrade chase. | Current docs do not make 19.3 a requirement. |
| [React 19.2, 2025-10-01](https://react.dev/blog/2025/10/01/react-19-2); [useEffectEvent](https://react.dev/reference/react/useEffectEvent) | 19.2 introduced Activity and Effect Events, which read latest committed values inside Effects. | Use Effect Events only for real Effect-fired events; keep user events and dependencies ordinary. | Identity is not stable; it must not hide dependencies or escape the component. |
| [Activity reference](https://react.dev/reference/react/Activity) | Hidden Activity sets `display:none` and destroys Effects/subscriptions, then recreates them. | Do not wrap every minimized DeskWindow. Prove frame, focus, bus, and mic lifecycle first. | Preserved React state is not preserved side-effect ownership. |
| [useSyncExternalStore](https://react.dev/reference/react/useSyncExternalStore) | `subscribe`/`getSnapshot` needs cached immutable snapshots; store mutation can make a transition blocking. | Use for a new browser/bus adapter only; do not migrate Zustand or RuntimeBus wholesale. | Built-in state remains simpler where it fits. |
| [useTransition](https://react.dev/reference/react/useTransition) | Background work can be interrupted; transitions cannot control text inputs and need another transition after `await`. | Defer heavy derived list/detail work only. Keep typing, IME, mic, receipts, and writes urgent. | It does not solve request ordering or optimistic safety. |
| [React Compiler 1.0, 2025-10-07](https://react.dev/blog/2025/10/07/react-compiler-1); [Vite setup](https://react.dev/learn/react-compiler/installation) | Stable build-time automatic memoization; this app has plugin-react 4.7.0 and no compiler. | Profile first; if useful, trial a small scope with exact versions and behavior checks. | Performance tool, not interaction model or visual-quality cure. |
| [APG keyboard interface](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/), current | Composites normally have one Tab stop; arrows move within; focus stays visible and predictable. | Keep roving rows and test pointer re-anchoring and async row changes. | ARIA widgets need author-supplied keyboard behavior; native HTML is safer when it fits. |
| [APG menu](https://www.w3.org/WAI/ARIA/apg/patterns/menubar/), current | Menus open onto an item, use arrows, let Tab leave/close, and return focus on Escape. | WorkMenu is a strong local implementation; audit edge cases before a behavior seam. | Menu roles are for actions, not arbitrary window content. |
| [APG combobox](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/), current; [W3C UI Events, 2026-02-21](https://www.w3.org/TR/uievents/) | Text editing keys and composition/IME must remain intact. | Keep native select and `isComposing` guards; global shortcuts must yield to editors. | A popup must preserve focus, selection, and Escape behavior. |
| [React Aria overview](https://react-aria.adobe.com/); [customization](https://react-aria.adobe.com/customization); [quality](https://react-aria.adobe.com/quality) | 50+ style-free components provide semantics, keyboard/pointer behavior, focus, i18n, and screen-reader testing; render props preserve local styling. | Candidate for one diagnosed recurring menu/listbox/focus defect, not wholesale adoption. | It must compose with Workbench windows and the one-Button contract. |
| [React Aria Components metadata](https://raw.githubusercontent.com/adobe/react-spectrum/main/packages/react-aria-components/package.json) | Upstream metadata lists version 1.22.1, Apache-2.0, and React 19 peer ranges. | A later spike must pin the package and audit all transitive licenses. | Direct-package metadata does not approve a dependency graph. |
| [SpeechRecognition, MDN](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition) | Not Baseline; some browsers use a server service, so offline and egress vary. | Keep MicButton, stream session, proposal, and one audio-floor owner; show honest unsupported states. | Do not make browser recognition the native boundary. |

## Foundation contracts

**Ownership and timing.** Every interaction has one owner for state, focus,
side effects, and recovery. Keep text, selection, focus, drag, mic status, and
accepted input urgent; defer only derived rendering. A save, send, command, or
voice action needs a typed request snapshot, in-flight identity, and
authoritative result or refusal. Never treat an optimistic answer or
irreversible effect as success. Settings already separates base, pending and
failed changes, revision writes, focus return, and retry. Ask has immutable
snapshots, abort identity, stopped/failed states, and retry. People keeps master
selection while reads race and rejects stale detail responses. Spread these
patterns.

**Focus and windows.** Preserve native DOM focus where possible. Inside a
composite, keep one Tab stop and arrow movement. DeskWindow is a non-modal
region: focus enters on open, Escape closes, and focus returns to the opener;
windows coexist and must not receive a modal trap. Do not add `role=dialog` or
`aria-modal` because a surface is portaled; see [WAI-ARIA 1.2](https://www.w3.org/TR/wai-aria-1.2/).
Menus restore the invoking Button.
Activity is unsafe as a generic minimize primitive: DeskWindow registers
layout/effect lifecycle, subscriptions, focus identity, and mic authority.

**Menus, selection, and IME.** Keep WorkMenu’s one vocabulary, roving focus,
Home/End, Escape return, submenu direction, and typeahead. Keep the visible
native `<select>` as WorkbenchSelect’s semantic and browser-owned fallback; the
custom listbox is an enhancement, not a second truth. Future comboboxes must
preserve text editing and composition. `event.isComposing` wins over
Enter/Escape commands; global shortcuts yield to editable elements.

**Voice.** MicButton remains the only microphone authority. A result is text or
a typed proposal until confirmed, never a direct irreversible command. Claim,
renew, and release the audio floor. Do not silently fall back to a
`SpeechRecognition` service.

## Small decision matrix

| Approach | Decision | Use when | Main risk |
|---|---|---|---|
| Existing `signal`/DeskMenu/DOM patterns | **Default** | The local contract already covers the diagnosed behavior. | Local edge cases need focused APG checks. |
| React Aria Components | **Scoped candidate** | A repeated menu/listbox/focus defect remains after local diagnosis. | Dependency and lifecycle composition; audit exact pin and transitive licenses. |
| React Compiler | **Performance experiment** | Profiling shows render churn that memoization can address. | Build/config and behavior drift; unrelated to focus semantics. |
| React 19.3 Activity/ViewTransition | **Future, case by case** | A proof shows lifecycle and browser support are safe for one surface. | Activity destroys Effects while hidden; 19.3 is not the locked baseline. |
| Wholesale UI library replacement | **Reject** | Never for this brief. | Breaks the Button contract, Workbench language, and native boundary. |

## Delivery shape and open proof

Name the failing interaction and its state/focus owner. Fix the smallest
existing seam and check keyboard, pointer, touch, IME, interruption, retry, and
unsupported-browser behavior. A React Aria spike must wrap one diagnosed
component and keep HoldSpeak’s Button, window, and visual contracts. Compiler
and 19.3 experiments remain optional and measured against a real interaction.
Future visual proof covers 1440/393 widths and Chromium/WebKit/Firefox; this
lane intentionally did not build, test, or create shots.

## Findings

- React 19.3 is current, but the repository is locked to React 19.2.7; do not
  turn this research into an upgrade chase.
- Native feeling comes mainly from honest state ownership, focus return,
  interruption, recovery, and browser semantics—not from adding a UI library.
- WorkMenu, WorkbenchSelect, roving rows, and the non-modal window rule already
  cover much of APG; diagnose a real gap before replacing a local pattern.
- `useEffectEvent`, `useSyncExternalStore`, transitions, Activity, and Compiler
  each have narrow contracts. None is a blanket fix for UI quality, and
  Activity is unsafe around unproved window or mic lifecycles.
- Voice must stay behind the one MicButton/audio floor and explicit proposal
  confirmation because browser SpeechRecognition support and egress are not
  dependable.

**Tuesday:** the owner should be able to capture, ask, review a person, and
change settings without fighting focus, waiting, or recovery; this foundation
supports that path while leaving live browser proof as the next observation.

**Unknowns:** no live browser shots, assistive-technology run, package install,
or transitive-license audit was performed, by design of this read-only lane.
