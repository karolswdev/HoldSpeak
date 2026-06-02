# HoldSpeak IA spec (HS-30-01)

**Date:** 2026-06-01. The redesigned information architecture + the shared global
patterns every route must follow. This is the **contract** the shell (HS-30-04)
and the page stories (HS-30-06/07/08) build to. It fixes the problems named in
`ux-audit.md`. Visual language ("Signal") is HS-30-02; this doc is structure only.

**Scope guard:** no new product features and **no new page routes** — the five
existing routes stay. The one relocation (Settings out of History) is realized as
a **global drawer reachable from the shell**, not a new route (see §2).

## 1. Navigation model

Replace the flat 5-link strip with a grouped model that signals what each surface
is *for*. The shell exposes three clusters:

```
┌ HoldSpeak ──────────────────────────────────────────────── [status] [⌘] [⚙] ┐
│  ● Runtime    History · Activity     Dictation · Companion                    │
│    (live)     (review)               (configure)                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

- **Brand mark** (left) → Runtime.
- **Primary destinations**, grouped by job-to-be-done (labels unchanged, grouping
  is visual/semantic):
  - **Live** — `Runtime` (`/`). The default surface; the only real-time one.
  - **Review** — `History` (`/history`), `Activity` (`/activity`).
  - **Configure** — `Dictation` (`/dictation`), `Companion` (`/companion`).
- **Active-route state** must be **dual-encoded** (not colour-only, per skill `ux`
  *Color Only*): a filled/“pressed” treatment **and** weight change **and**
  `aria-current="page"` — not just an accent underline.
- **Global status cluster** (right): one persistent **connection/runtime** chip
  (idle / live / reconnecting) **and** the **local-only** privacy chip. This is
  the single home for connection state — it stops being a stat-grid cell and stops
  being an error toast (problem #5).
- **Command entry** `⌘` (right): a placeholder affordance for a command palette /
  quick-switcher. **Decision deferred to HS-30-04** (implement vs cut); the IA
  only reserves the slot.
- **Settings** `⚙` (right): opens the global Settings drawer (§2).
- **Responsive:** below a breakpoint the primary destinations collapse into a
  single menu/overflow control — a deliberate strategy, not flex-wrap.

## 2. Settings — lifted out of History (problem #7/#8)

The **History → Settings** tab (`history.astro` 632–851: Appearance & UI, Core
settings, Cloud intel) moves to a **global Settings drawer/panel** opened from the
shell `⚙`. It is available from every route, not just History.

- Realized as a slide-over drawer or a dedicated full-height panel within the
  existing shell — **not** a new top-level route (keeps route count at five).
- Three sections preserved as-is in content: **Appearance & UI**, **Core
  settings**, **Cloud intel**. (Theme picker stays here even though Signal ships
  dark-only — it just won't offer a light option yet.)
- History keeps **five** tabs (Meetings, Action items, Speakers, Projects, Intel
  queue); Settings is gone from it.

## 3. Shared global patterns (every route obeys these)

These make the five routes read as one product and kill the per-page divergence
(problems #5, #12).

### 3a. Page header
Every route opens with one consistent header block:
`eyebrow (route group) → h1 (route name) → one-line purpose → primary action(s)
right-aligned`. Exactly one `h1` per route; panel titles are `h2`, sub-panels
`h3` — **sequential, never skipped** (skill `ux` *Heading Hierarchy*).

### 3b. Panel / card grammar
One panel primitive (the restyled `Panel.astro`) with a header row (title +
optional inline controls) and a body. Two densities only: **comfortable** and
**dense** (already in the component API). No bespoke per-page box treatments.

### 3c. Side rail
Where a route has a secondary column (Runtime, Activity, History-detail), it uses
one **rail** pattern: a single scroll column of panels with consistent spacing and
a clear "primary column vs rail" weight difference (depth + width, not just a
border). The rail is visually subordinate to the primary column.

### 3d. Status, empty, loading, error — one system
- **Status** lives in the shell cluster (§1) + inline pills on items.
- **Empty state**: the restyled `EmptyState.astro` (icon + line + optional CTA),
  used everywhere a list/stream can be empty.
- **Loading**: inline skeleton/placeholder within the panel, never a layout jump.
- **Error**: an **inline** `InlineMessage` *inside the relevant panel*, plus the
  shell connection chip for connection loss. **Toasts are reserved for transient
  confirmations only** and must not overlap content (kills problem #5). Convey
  errors with icon + text, never colour alone (skill `ux` *Color Only*).

### 3e. Sticky-nav offset
The sticky shell header must reserve its height so no route's first row hides
under it (skill `ux` *Sticky Navigation*).

## 4. Per-route layout intention

Structure/region intent only — not visual styling.

### 4a. Runtime (`/`) — "Real-Time Monitor" (skill-recommended for dev tools)
- **Header**: Runtime + the live meeting title + primary action (**Start / Stop
  meeting**) + meeting-state chip (idle / live / stopping).
- **Primary column (dominant)**: the **live transcript stream** — the reason the
  page exists. Gets the most width + the clearest surface. Footer dock: Bookmark ·
  Copy all · Export.
- **Rail (subordinate)**: the intel column, but **grouped into a few labelled
  sections** instead of 8 equal boxes — *Live intelligence* (intel + topics +
  summary), *Action items*, *Devices*, *Operations* (deferred plugin jobs + intent
  routing, collapsed by default). The rail is clearly secondary to the transcript.
- Pre-meeting **briefing** stays as an idle-state panel in the primary column.
- Modals (bookmark, metadata) unchanged in function.

### 4b. Dictation (`/dictation`) — progressive disclosure (problem #11)
- **Header**: Dictation + the project-root selector promoted into the header (it
  gates everything).
- Re-group the 7 tabs into **two tiers**:
  - **Setup** (first-run / occasional): Readiness, Blocks, Project KB, Project
    Context, Agent Hooks.
  - **Runtime & test** (frequent): Runtime config, Dry-run.
- The **dry-run** input→trace→result is a first-class, legible surface (its timing
  trace must be readable — it's the signature feature).

### 4c. History (`/history`) — archive + review (five tabs now)
- **Header**: History + the archive metrics (meetings / actions / queued intel).
- Tabs: **Meetings** (search + cards + detail modal), **Action items**, **Speakers**,
  **Projects**, **Intel queue**. (Settings removed → §2.)
- **Action items** is the canonical "my work" home (problem #9): the dashboard
  rail and project detail *link into* this tab rather than re-implementing it.
- **Intel queue** is the canonical ops home (problem #10): the dashboard's
  deferred-jobs panel is a compact read-only summary that deep-links here for the
  full controls.
- Meeting-detail modal + structured artifact renders retained, restyled.

### 4d. Activity (`/activity`) — capture + rules (keep 2-column)
- **Header**: Activity + the capture status (Running / Paused) as the primary
  control, promoted out of the left panel into the header.
- **Left rail**: Controls, Sources, Excluded domains.
- **Main**: Project rules, Connectors, Meeting candidates, Recent activity.
- The candidate **preview vs saved** distinction must be dual-encoded (label/chip
  + treatment), not dashed-vs-solid border alone (problem from per-route notes).

### 4e. Companion (`/companion`) — read-only monitor (template route)
- Keep the shape (summary grid → selected target → waiting sessions → blockers);
  it's the cleanest IA. Apply the shared patterns; it becomes the reference
  implementation of the card/status grammar for the other routes.

## 5. Open question handed to HS-30-04

- **Command palette** (`⌘`): the IA reserves the slot but does not require it.
  HS-30-04 decides implement-vs-cut from effort; default if undecided = ship the
  slot empty/omit and record the decision. Given the deep surfaces (History tabs,
  Dictation tabs, Settings drawer), a quick-switcher is *recommended* but not
  blocking.

## 6. Traceability (audit problem → fix)

| Audit # | Problem | Fixed by |
|---|---|---|
| 1–3, 12 | Blue/white/pixel/hairline, no depth, heading drift | HS-30-02/03 (Signal) + §3a–3c |
| 4 | Flat ungrouped nav, colour-only active | §1 |
| 5 | Fragmented status, overlapping error toasts | §1 status cluster + §3d |
| 6 | No command/search | §1 `⌘` (HS-30-04 decision) |
| 7, 8 | Settings buried in History; History overloaded | §2 |
| 9 | Action items fragmented | §4c (canonical home) + §4a (link-in) |
| 10 | Duplicated ops surfaces | §4c (Intel queue canonical) + §4a (read-only summary) |
| 11 | Dictation 7 flat tabs | §4b (two tiers) |
