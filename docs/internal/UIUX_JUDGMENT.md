# The UI/UX Judgment (HS-100-02)

Every surface and desk component of the shipping product judged against
[GROUNDING.md](GROUNDING.md)'s jobs — not "is it styled" but "which job
does it serve, and does it serve it well." Verdicts: **keep** (serves a
job, composition sound), **re-shape** (right to exist, wrong shape for
its job), **merge** (its job is another surface's job), **kill**
(serves no ranked job). Evidence: three live end-to-end flow traces on
the staged spike build (assets/hs-100-02-traces/ under the phase dir,
traces.json + numbered screenshots), the owner-verdict record, and the
phase-93→99 walk history. The judgment is completeness-checked by
`scripts/judgment_census.py` against the SURFACES registry and the
desk component inventory.

## 1. The three flow traces (measured, not imagined)

### Flow A — "I just had a meeting" → "the actions are filed" (Job 2)

3 clicks from arrival to the full meeting detail: room menu → Meetings
→ the meeting row. The detail window carries **seven section concepts**
(Transcript / Artifacts / Aftercare / Routing / Proposals + the list's
Actions / Speakers / Projects / Queues / Filters facets) before the
user has done anything. The traced instance had intelligence disabled:
the row says "Disabled" and exactly one affordance points at a fix.
To actually reach "filed": enable intelligence (Settings), re-run
intel, read aftercare, approve the proposal, and have an executor
configured (Settings again) — **nine distinct concepts** (meeting,
transcript, artifact, intelligence, aftercare, routing, proposal,
executor, integration) stand between the felt need and the felt value.
The capability chain is real and proven (dogfood 2026-07-04); the
presentation is an API map, not a job.

### Flow B — speak → text lands → teach a correction (Job 1)

5 clicks, one window, fully real (fake-mic wav → the hub's real
Whisper → the real pipeline → Right/Wrong → the correction ritual open
in place). This is the best flow in the product: the verdict pair and
in-place teaching are exactly Article VII's quiet-chrome ideal. Two
convictions anyway: (1) the Dictation window opens on **Readiness** —
a diagnostics pane shouting "Dictation pipeline is disabled" and
"Project KB file is missing" — instead of on the job; the headline
mode presents as a 9-tab settings machine (Readiness/Try it/Blocks/
Memory/Knowledge/Journal/Runtime/Hooks/Nudges) in which *speaking* is
tab two. (2) On the plain-HTTP LAN origin — exactly how the owner
explores staged builds — `navigator.mediaDevices` is undefined and
**every MicButton silently renders null**: the voice product loses
its voice with no explanation (MicButton.tsx:56). Article VI violation
by omission.

### Flow C — tap a kept object → rope → ask → answer (Job 4)

4 clicks from arrival to a printed response: tap opens the pull-out,
lasso ropes a selection, Ask AI opens with the roped grounding already
picked, Ask prints. **This is the desk metaphor earning its keep** —
zero navigation concepts, the space itself is the query builder. The
imported meeting materialized as a desk object (a cassette) with no
ceremony: filing is automatic, as Article II demands. Convictions:
the refusal reads "⚠ Intel model not found:
/Users/karol/…/Qwen3.5-9B-Instruct-Q6_K.gguf" — the canon-banned word
"intel" in user-facing copy (POSITIONING vocabulary table) plus a
leaked absolute filesystem path where the fix ("pick a model in
Settings") should be.

## 2. The surfaces, judged

Every row of the SURFACES registry (SurfaceWindows.tsx) plus its
aliases. "Posture" is GROUNDING §4's lens.

| Surface (key) | Job / posture | Verdict | Why |
|---|---|---|---|
| Dictation `dictate` | Job 1 / working+reviewing+configuring collapsed | **re-shape** | The headline job wears 9 config tabs; opens on diagnostics. Working posture (speak, verdict, teach — trace B's 5-click loop) must lead; Journal is reviewing; Blocks/Memory/Knowledge/Runtime/Hooks/Nudges are configuring and belong folded behind one quiet door. |
| Meetings `review-meetings` | Job 2 / reviewing | **re-shape** | Trace A: the detail is an API map (7+ section concepts). The job is "what came out, what do I approve" — aftercare and proposals are the headline, transcript is the receipt, routing/queues are plumbing. |
| Live meeting `record-live` | Job 2 / working | **keep** | One job, one posture, walk-proven; the record orb entry is right. |
| Settings `configure-settings` | cross / configuring | **keep** (absorb) | The spike's grouped-settings shape carries. Absorbs the aliases below and RuntimeDocs. |
| — alias `configure-integrations` | cross / configuring | **merge** | Already a scoped Settings open; keep the scoping, kill the separate shelf identity. |
| — alias `configure-integration` | cross / configuring | **merge** | Same. |
| Runs on `configure-runs-on` | trust cross-cut / configuring | **keep** | The boundary surface; egress badges live here; Articles III/V. |
| Cadence `configure-cadence` | long tail / reviewing | **keep** | Quiet, off by default, honest — correctly proportioned today. |
| Setup `configure-setup` | arrival | **re-shape** | Owner verdict 2026-07-17: "way too full with noise… absolutely confusing." Arrival must show the two modes and one trust badge, not a checklist wall. |
| Workbench `build-workflow` | Tier-3 plumbing | **re-shape (demote)** | No ranked job hires a node canvas daily; it is a builder's tool. Keep it, remove it from daily prominence. |
| Studio `configure-tools` | none ranked | **kill (merge remains)** | A "focused workspace" tier is the pre-Article-I front door surviving in the registry — the Desk IS the workspace. Whatever it uniquely hosts moves to Settings or the shelf. |
| Personas and coders `inspect-personas-and-coders` | Job 3 / working+reviewing | **re-shape + rename** | The job (see the blocked coder, answer it) is Tier-1-adjacent and the surface buries it under a roster. "Personas" is canon-banned vocabulary — the canon word is **agents**. |
| Runtime guide `read-runtime-docs` | arrival / configuring | **merge** | A doc pretending to be an application; belongs inside Settings/Setup as help. |
| Components `design-components` | none (dev gallery) | **keep (internal)** | The design system's mirror — keep for builders, hide from the user-facing shelf. |
| Activity `inspect-activity` | Tier 2 / reviewing | **keep** | This-device context that feeds dictation grounding; right size. |
| Commands `configure-commands` | Tier 2 / configuring | **keep** | Voice macros; right size, off by default. |

## 3. The desk components, judged

| Component | Job / posture | Verdict | Why |
|---|---|---|---|
| DeskWindow | shell | **keep** | The 97 grammar + 98/99 chrome + spike material are floors (Article VIII); traffic lights and head menu carry. |
| DeskChrome | shell | **keep** | The menu bar + clock landed the "OS" read; the room menu inside it is one of FOUR launchers (see §5.4). |
| DeskMenu | shell | **keep** | One menu vocabulary — exactly the consistency Article VIII names. |
| SurfaceWindows | shell (host) | **keep** | The registry host is sound; §2 re-scopes its rows. |
| Dock (in DeskWindow) | shell | **keep** | One shelf, running marks, magnification — proven grammar. |
| DeskStartActions | Jobs 1+2 arrival | **keep** | Two daily starts = the two modes; the truest thing in the chrome. |
| DeskCreateMenu | Job 4 | **keep** | Create-in-world, no modals (Article VII). |
| DeskToolShelf | shell | **re-shape** | A junk drawer: tools + context actions + resources + desk items + search in one popover. Its search is good; its four-section stack is the old sitemap wearing a popover. |
| DeskToolInspector | Job 4 / reviewing | **keep** | Facts-not-forms object inspection. |
| DeskListView | Job 4 / arranging | **keep** | The desk's honest dense mode. |
| EmptyDesk | arrival | **re-shape** | First contact must present the two modes, not desk mechanics. |
| FirstWords | arrival | **re-shape** | Same posture; still on pre-98 idiom (`signal-eyebrow`) — convert or fold into arrival. |
| Pullout | Job 4 / reviewing | **keep (re-shape edges)** | The object reader is central; the spike normalized its chrome; persona/coder tails never live-passed (§5.7). |
| SessionPullout | Job 3 / working | **re-shape** | The steering seam's front end deserves the Job-3 headline treatment, not a side sheet stacked with facts. |
| PersonaChat | Job 3 / working | **re-shape + rename** | Vocabulary + never live-walked; the chat belongs inside the agent surface. |
| AskPanel | Job 4 / working | **keep (fix copy)** | Trace C's hero. Fix: "intel" vocabulary, path leak, and the refusal must point at its fix. |
| GroundingSection | Job 4 | **keep** | Receipts for what rode the ask — Article IV made visible. |
| MicButton | Job 1 everywhere | **keep (fix the silent null)** | Voice-mic-on-every-input is standing owner doctrine; silently vanishing on insecure origins is an Article VI violation — render disabled WITH the reason. |
| RecordOrb | Job 2 / working | **keep** | The one-glance record state. |
| InlineEditor | Job 4 / working | **keep** | Edit-in-world, no modals. |
| TrustWindow | cross / configuring | **keep** | The spike's grouped facts shape is right. |
| RunsOnPicker | cross / configuring | **keep** | Boundary picking at the point of use. |
| RailsPicker | delivery / configuring | **keep** | Same pattern for rails. |
| AttentionDrawer | Jobs 2+3 / reviewing | **re-shape** | The approve-queue is load-bearing (proposals live here) but reads as a stack of cards from four eras; one card grammar. |
| MissionControlConveyor | Tier-3 / reviewing | **re-shape (demote)** | Delivery theater; fold what matters into the delivery board. |
| DeliveryBoard | Job 3 / reviewing | **keep** | Rails-as-receipts worked (Phase 88). |
| DeliveryListSection | Job 3 / reviewing | **keep** | The board's list half. |
| DeliveryDossierWindow | Job 3 / reviewing | **keep** | The story dossier earns its window. |
| DeliveryTerminalWindow | Job 3 / working | **keep** | The factory's pane; steering flows through it live (Phase 89/90). |

## 4. The desk metaphor, judged honestly

**Where it earns its keep (evidence for):** Trace C is the proof — tap
/ rope / ask with zero navigation concepts, grounding assembled by
gesture; the imported meeting self-filed as a desk object; zones and
piles group without ceremony. The physics floors (93/95/97) made the
world feel held. Job 4's arranging posture is genuinely better here
than any page could be — this is the product's difference, and the
owner's Constitution ratifies it (Articles I, II).

**Where it is scenography (evidence against):** Jobs 1–3 — the value
jobs — happen inside windows whose interiors ignore the desk
entirely: 9-tab API maps that could be served at any URL. The desk
launches them and then decorates behind them; the owner's verdict
("a front door that keeps throwing you out of it", "zero 'I'm sitting
in an operating system' feeling") is the felt version of that split.
The metaphor is not wrong; it is **unfinished at the window boundary**
— the world got physics, the windows got chrome, and the interiors
never joined either.

**Ruling for the thesis:** keep the desk as the operating surface
(ratified canon, and Job 4 proves it); the application layer's work
is to make window interiors *of* the desk — shaped by posture
(working / reviewing / arranging / configuring), grounded in desk
objects, with configuration folded behind quiet doors instead of
leading.

## 5. The mangled paths, named end-to-end

1. **Meeting → filed actions** (trace A): nine concepts, two Settings
   detours, and the headline value (aftercare + proposals) is the
   sixth section of a tab strip. The whole chain must present as ONE
   reviewing posture: "here is what your meeting produced; approve or
   bin."
2. **Dictation opens on diagnostics** (trace B): the flagship job
   greets its user with two warnings and a facts table; speaking is
   tab two of nine.
3. **The mic silently vanishes** on non-secure origins (trace B,
   MicButton.tsx:56) — on the very LAN posture used to show the
   product. Must render with its reason.
4. **Four launchers for the same surfaces**: room menu, dock, tool
   shelf, start actions (+ deep links). Four idioms to learn where an
   OS has one-and-a-half. The thesis must pick the dock + one menu and
   demote the rest.
5. **Vocabulary in the glass**: "Personas" (banned; canon: agents),
   "Intel model not found" (banned; canon: intelligence), and a leaked
   filesystem path in a refusal. One sweep, guard-locked (the Swift
   prose guard pattern exists; the web needs the same).
6. **Arrival noise**: Setup/EmptyDesk/FirstWords stack checklists at
   the exact moment the product must show its two modes (owner verdict
   2026-07-17).
7. **Job 3's front door never live-passed**: PersonaChat and the coder
   session pull-out have no live walk on record — the most-built seam
   (steering) has the least-proven glass.

## 6. The materials spike, judged as input

**Carries into the thesis:** the real vibrancy material + glass edge;
traffic lights with idle/front states; the menu bar + clock; dock
magnification + running marks; one menu vocabulary (DeskMenuList);
bare-control inheritance so no raw HTML control can render unstyled;
grouped settings (SurfaceGroup/SurfaceSettingRow/SurfaceToggle);
sprite-bearing empty states. These answered the owner's "material"
verdicts and survive his last screenshots.

**Does not carry:** the method. Six rounds of component-by-component
patching moved the material forward and left every interior's
information architecture untouched — §5's paths were all still there
after round six. The thesis designs interiors from jobs first, then
applies the proven material; never the reverse again.

## 7. What the thesis must decide (handoff to HS-100-03)

- The application roster: which of §2's re-shaped surfaces become the
  few real applications (working title: Speak, Meetings, Agents,
  Settings) and what each opens ON.
- The posture rule: how one window presents working vs reviewing vs
  configuring without tab walls.
- The launcher ruling (§5.4) and the arrival ruling (§5.6).
- The desk-window boundary: how interiors become "of the desk"
  (grounding chips, desk-object references, sprites as state).
- The guard set that locks §5's paths shut (vocabulary guard, mic
  honesty, concept-count budget per flow).
