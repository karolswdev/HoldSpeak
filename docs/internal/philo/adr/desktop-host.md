# ADR-PHILO-001: keep desktop hosting behind a bounded adapter

**Decision status:** PROPOSED. No desktop distribution is selected or declared supported.
**Scope:** a host for the existing production Web Desk, not another product UI.
**Research:** [primary sources](../EXTERNAL_RESEARCH.md#desktop-sources).

## Context and current reality

The browser Desk already owns rendering and application-window behavior.
`web/src/main.tsx`, `web/src/routes.tsx`, `web/src/lib/api.ts` and
`web/src/runtime/RuntimeBus.tsx` define its entry, routes, HTTP and event boundaries.
`holdspeak/desktop_presence.py` is existing native presence machinery, not proof
of an Electron or Tauri full-Desk distribution. Inspect its platform imports
before extending it. The owner requested a future desktop target and both host
prototypes. This ADR retains that request without changing the production shell.

## Problem

A host can add file selection, tray behavior and platform integration. It can
also duplicate authentication, state and commands or expose excessive native
authority. The browser and host must operate on the same records and commands.

## Options

| Option | Useful property | Cost to measure | Status |
| --- | --- | --- | --- |
| Browser only | Current product boundary and existing test harness | Native capability gaps | Existing baseline |
| Electron | Bundled Chromium offers a consistent renderer; preload can expose narrow operations | Runtime footprint, packaging, updates, IPC and navigation restrictions | Candidate |
| Tauri 2 | System WebView and native core; capability grants bound command access | WebView differences, Rust build toolchain, signing and sidecar lifecycle | Candidate |
| Native UI rewrite | Native control integration | Duplicate product state, components and workflows | Rejected for this request |

Architecture facts above come from the linked vendor sources. Resource use,
startup, rendering fidelity and maintenance cost are unmeasured until a common
fixture is run. Do not pick a winner from assumed bundle sizes.

## Proposed contract

```ts
type HostResult<T> =
  | { status: "ok"; value: T }
  | { status: "unavailable" | "denied" | "cancelled"; reason: string };
type FileRef = { id: string; name: string }; // opaque, scoped host reference
type CommandId = string; // validated against the admitted command set

interface DesktopHost {
  readonly kind: "web" | "electron" | "tauri";
  capabilities(): Promise<readonly string[]>;
  openFiles(request: { types: readonly string[]; multiple: boolean }): Promise<HostResult<readonly FileRef[]>>;
  saveFile(request: { suggestedName: string; contentRef: string }): Promise<HostResult<FileRef>>;
  revealFile(ref: FileRef): Promise<HostResult<void>>;
  registerShortcut(request: { command: CommandId; accelerator: string }): Promise<HostResult<string>>;
  unregisterShortcut(registration: string): Promise<HostResult<void>>;
  notify(request: { title: string; body: string; command?: CommandId }): Promise<HostResult<void>>;
  setTray(request: { state: "idle" | "working" | "attention" }): Promise<HostResult<void>>;
  requestAttention(): Promise<HostResult<void>>;
  platform(): Promise<{ os: string; version: string; hostVersion: string }>;
}
```

This is a proposed portable interface, not an installed browser global.
Production introduction requires a checked change brief. The Web adapter returns
named unavailable results for native-only methods, while web-supported actions
keep using current browser paths. It owns no Notes, Meetings, model assignments
or conversation store. No method accepts arbitrary shell commands or unrestricted
filesystem paths. Shortcut registration needs collision and cleanup handling.

Autostart and updating are separate host services with explicit capability
grants and packaging requirements. They are not enabled by merely constructing
this interface. Runtime process control must preserve existing kernel authority.

## Prototype comparison protocol

Both experiments load the same identified `holdspeak/static/_built` bundle through
an isolated local fixture. Record source SHA, build hash, host version, OS,
viewport, start/stop method and log paths. No owner's hub, cookies, credentials,
microphone or real data are used. A renderer boot is distinct from end-to-end
HoldSpeak correctness.

| Probe | Evidence required | Acceptance |
| --- | --- | --- |
| Renderer parity | 1440 and 393 screenshots of the same fixture | No missing controls; geometry differences named |
| Startup | Five cold launches with definition of cold | Median and range, no unsupported performance ranking |
| Resource use | RSS/process count after fixed settle time | Same fixture and instrument; all child processes counted |
| Native boundary | Allowed and denied bridge calls | No generic process/filesystem method; invalid requests refused |
| Navigation | Attempt outside origin and new-window creation | Disallowed destinations refused or deliberately handed off |
| Relaunch | Workspace fixture reopened after process restart | No new backend record ownership |
| Dialog/shortcut/tray | Scoped temporary fixture | Cancel/denied states and cleanup demonstrated |
| Distribution | Signed package/update/rollback test | Deferred until shipping scope is chartered |

The first four probes inform the host choice. The remaining probes are required
before productization. If a toolchain is unavailable, record that result rather
than infer the other host is preferable. Isolated prototype instructions and
results belong under `../desktop-prototypes/`.

## Migration, compatibility and security

Introduce the Web adapter first, behind current component contracts. Product
records remain hub-owned and existing typed HTTP and RuntimeBus boundaries
remain intact. Browser shortcuts keep browser behavior unless the user is
within an explicitly supported command context. Do not intercept platform
shortcuts globally to satisfy a documentation table.

Provider secrets remain on the hub. A host identity, pairing token and file
reference have different scopes; never reuse one as arbitrary execution
authority. Validate calls at the receiving host boundary, not only TypeScript.
Keep renderer navigation and origin policy independent of payload validation.

## Recommendation and decision criteria

Adopt the bounded-host requirement. Defer the choice between Electron and Tauri
until both experiments have comparable evidence. This is a positive decision
about the boundary and an open decision about the container.

Reject a second UI kit, renderer-side business database and generic IPC tunnel.
They add competing ownership without solving a demonstrated user job.
The next engineering decision names the native job, supported platforms,
measured results, maintenance owner and release obligations.

## Prototype evidence, 2026-09-19

The [two host probes](../desktop-prototypes/README.md) now build/load the same
production bundle on macOS ARM64 with no live hub. Electron has an inspected
error-surface capture and Node-global isolation result; Tauri has successful
build and page-load events. This closes the minimal feasibility experiment,
not the full decision matrix. No vendor is selected. Clone-local Rust was
installed for the experiment; the initial missing-toolchain limit was resolved.
