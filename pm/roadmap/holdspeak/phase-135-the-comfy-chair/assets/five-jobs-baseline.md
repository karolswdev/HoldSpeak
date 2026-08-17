Good. All 21 screenshots are captured. Here is the complete report.

---

## FIVE JOBS BASELINE AUDIT -- HoldSpeak @ main b4c6aced, 2026-08-16

**Environment:** Isolated HOME, seeded + populated state (walk harness's `_seed_and_serve` + `_populate`), Playwright headless Chromium at 1440x900 (2x DPR).

**Output directory:** `/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/f380fecb-4e2f-4c34-9ce4-e1babbe72b2a/scratchpad/five-jobs/`

---

### (1) HEADLINE TABLE

| Job | Actions (measured) | Shortest possible | Seconds | Voice? | Verdict |
|---|---|---|---|---|---|
| 1. Record a meeting | 1 | 1 | 4.3s | no (trigger is pointer) | Best-served job. One click on the Record Orb. |
| 2. Capture a 1:1 note | 7 | 5 | 7.3s | partial (mic on body, not title) | Achievable but 5-step minimum; auto-save would cut to 4. |
| 3. Capture a TODO | 6 | 5 | 9.7s | partial | No canonical TODO home; falls back to a Note. |
| 4. Ask a question | 4 (via Speak) | 3 (via Ask AI Cmd+I) | 11.1s | yes (Speak face) | Two doors to the same job; Ask AI is better but hidden. |
| 5. Check on agents | 2 | 2 | 5.8s | no | Clean path; blocked-first + Answer button works. |

---

### (2) PER-JOB PATH NARRATIVES

**JOB 1 -- Record a meeting**
- Path: click Record Orb (center dock, orange circle sprite, 40px).
- The orb is visible at all times on the desk floor (bottom-center of the dock).
- One click starts the meeting AND auto-opens the Live meeting surface window.
- The window immediately shows "Recording", intelligence streaming live (3 segments, 3 action items), transcript with timestamps, and a "Stop meeting" button.
- The recording state shows in the dock's orb as an elapsed timer ("0:04").
- Dead ends: none. The path is 1-click from landing.
- Voice possible: No -- the start trigger is a pointer click on the orb. There is no "start meeting" voice command visible.
- Screenshot: `job1-recording-started.png`

**JOB 2 -- Capture a 1:1 note**
- Path measured: Cmd+N (1) -> triple-click title to select (2) -> type "1:1 with Ana" (3) -> click body area (4) -> type body content (5) -> click Save (6) -> Tab (7, redundant).
- Shortest possible: Cmd+N (1) -> type title (2, if auto-selected) -> Tab to body (3) -> type body (4) -> click Save (5) = 5 actions.
- The note opens as an "Edit New note" pullout window with: title input (pre-filled "New note"), rich-text toolbar (B, I, H1-H3, List, numbered list, code, Link, Quote), body area with "Write" placeholder, Tags field, mic button, Cancel/Save buttons.
- The note immediately appears on the desk floor as an icon with a green "NEW" badge.
- The note IS persisted via `POST /api/notes` and confirmed present on the desk floor in screenshots.
- Dead ends: none encountered. The Cmd+N shortcut is fast. Alternative: right-click desk -> New -> New Note (3 clicks) or Cmd+K -> "New Note" -> click (3 actions).
- Voice possible: Partial -- the mic button is on the body area (visible in screenshot), so voice can dictate content. But the title field and the Save button require pointer/keyboard actions.
- Screenshot: `job2-note-saved.png` (note "1:1 with Ana" on desk floor with green dot)

**JOB 3 -- Capture a TODO**
- Path measured: Cmd+K (1) -> type "Cadence" (2) -> click Cadence result (3) -> [dead end: no Add button] -> Escape (4) -> Cmd+N (5) -> type "TODO: Review Q3 budget" (6) = 6 actions.
- Shortest possible (knowing the answer): Cmd+N (1) -> type title (2) -> Tab (3) -> type body (4) -> Save (5) = 5 actions (same as Job 2, since the only path is a Note).
- Dead ends:
  - **The Cadence surface has no "Add commitment" or "Create TODO" verb.** It shows "Off - normal", "No open loops", "No nudges yet" and only a "Run now" button. Follow-Through commitments are derived from meetings only (created by intelligence extracting action items from meeting transcripts), not manually entered.
  - **Ambiguity: where does a TODO live?** Three plausible homes exist: (a) Follow-Through/Cadence commitments -- but these only come from meetings, (b) a Note titled as a TODO, (c) a Workbench item. There is no "New TODO" verb in the entire verb registry. The search shelf (screenshot `job3-search-shelf.png`) shows no TODO-related verb.
- Voice possible: Partial -- same as Job 2 (mic on body, not on title/save).
- Screenshot: `job3-todo-done.png` (note pullout with "TODO: Review Q3 budget" title)

**JOB 4 -- Ask a question**
- Path measured (through Speak): click Speak dock button (1) -> click utterance textarea (2) -> type question (3) -> click Deliver button (4) = 4 actions. Wall time 11.1s.
- Shortest possible (through Ask AI): Cmd+I (1) -> type question (2) -> Enter or click ASK button (3) = 3 actions. The Ask AI panel opens as a docked in-world panel with a text input, a "ASK" TransportKey button, Lens selector, and grounding context. Enter submits.
- IMPORTANT FINDING: The measurement went through the Speak surface, which is the WRONG door for this job. The Speak surface is a dictation cockpit (instrument strip with TALK/OPEN, LEVEL meter, STATE register, PIPELINE status, TARGET, MIC state, BUDGET). Its "Deliver" verb is for dictation delivery to a focused app (TARGET: CLAUDE CODE). Ask AI (Cmd+I) is the dedicated question interface with grounding, lenses, and receipts.
- Dead ends:
  - Speak's footer showed "PIPELINE OFF" and "LOCAL" -- the question could not execute because no LLM endpoint is configured in the seeded profiles (base_url is empty for local profiles). This is a first-run setup cost.
  - The "Deliver" button turned orange but no result appeared -- no error receipt was shown to the user. Silent failure.
  - Two doors to the same class of job: Speak (dictation-first) and Ask AI (question-first). A user seeking "ask a question" has to know which one. The search shelf does show "Ask AI PROGRAM Cmd+I" which is discoverable, but neither the dock nor the verb names make the distinction clear.
- Voice possible: Yes -- the Speak surface IS the voice path. The mic can be opened (TALK button), speech transcribed, and delivered. Ask AI also has a MicButton. Both paths support voice input.
- Screenshot: `job4-answer-result.png` (shows Speak surface with question typed; HoldSpeak menu accidentally dropped)

**JOB 5 -- Check on agents**
- Path: click Agents dock button (1) -> click Answer button on blocked session (2) = 2 actions.
- The Agents surface immediately shows "CREW 0 - SESSIONS 1 - BLOCKED 1" with the session listed at "/Users/karol/dev/tools/HoldSpeak" marked "BLOCKED" (orange badge). The "Answer" button is directly visible without scrolling.
- Clicking "Answer" opens the session's pullout window showing: node (this Mac), status ("x pane gone"), and at the bottom "CLASSIFY" / "Keep as note" options.
- The Agents surface has two wings: ROSTER (default) and DELIVERY.
- Dead ends: none. The blocked-first sort order (confirmed in `CompanionCore.tsx:68`) means the actionable session is always at top.
- Voice possible: No -- no voice path for navigating to Agents or steering a session.
- Screenshot: `job5-agents-open.png` (blocked session visible with Answer button)

---

### (3) RANKED FRICTION FINDINGS (Top 10)

**F1 (P0). No canonical TODO home.**
There is no "New TODO" or "Add commitment" verb anywhere in the product. The Follow-Through/Cadence surface is read-only (commitments come from meetings). A user must repurpose a Note, a Workbench item, or rely on meeting intelligence. Three plausible homes, zero purpose-built paths. This is the worst ambiguity in the five jobs.
Screenshot: `job3-cadence-open.png` (Cadence with no add verb), `job3-search-shelf.png` (no TODO in shelf)

**F2 (P1). Ask a question has two doors: Speak vs. Ask AI.**
"Speak" (dock button, Cmd+1) is a dictation cockpit. "Ask AI" (Cmd+I, only in the search shelf and Cmd+K) is the dedicated question surface. The dock shows Speak but not Ask AI. A user wanting to ask a question will click Speak first (it is the more prominent verb), encounter a complex instrument strip (PIPELINE, TARGET, MIC, BUDGET, STATE), and likely fail. Ask AI is hidden behind Cmd+K or Cmd+I.
Screenshot: `job4-speak-open.png` (Speak's cockpit complexity), `job3-search-shelf.png` (Ask AI listed under PROGRAMS)

**F3 (P1). Speak's Deliver fails silently when no LLM endpoint is configured.**
Clicking Deliver with empty seeded profiles produces no error message, no receipt, no feedback. The footer stays "PIPELINE OFF" / "LOCAL". The user has no indication that anything went wrong or what to configure. The same applies to Ask AI.
Screenshot: `job4-answer-result.png`

**F4 (P1). Note requires explicit Save click -- no auto-save.**
Creating a note via Cmd+N opens an edit pullout with Cancel/Save. The user must click Save to persist. There is no auto-save, no dirty indicator, and closing the pullout (Cancel) discards content. Every note creation costs at least 5 actions instead of 3 (create, title, body = done).
Screenshot: `job2-note-created.png` (Save button visible)

**F5 (P2). Meeting recording has no voice trigger.**
"Record a meeting" is the best-served job (1 click), but the trigger is exclusively a pointer click on the Record Orb. There is no "start recording" voice command, no wake word trigger, and no keyboard shortcut. For a voice-first product, the primary verb should be voice-triggerable.
Screenshot: `job1-landing.png` (orb visible, no voice label)

**F6 (P2). Speak surface is a cockpit, not a conversation.**
The Speak face shows 12+ state indicators (TALK, OPEN, LEVEL, STATE, PIPELINE, TARGET, MIC, LANDED, BUDGET, AIM, REHEARSE) before the user can type a single word. The instrument strip is useful for debugging the voice pipeline but hostile for "I want to ask something." It reads as flight instruments, not a conversational surface.
Screenshot: `job4-speak-open.png`

**F7 (P2). Stale windows from previous jobs leak into subsequent tasks.**
After Job 1 stops recording, the Live meeting window remains open. In Job 2, the new note opens alongside the Live meeting window (visible in `job2-note-created.png`). By Job 3, the Cadence window opens alongside the Live meeting window (visible in `job3-cadence-open.png`). By Job 4, the Speak window opens alongside the persisted Live meeting window. Every new job adds windows but does not close the previous ones. A user performing multiple jobs accumulates visual noise.
Screenshot: `job3-cadence-open.png` (Live meeting + Cadence side by side)

**F8 (P2). The "1" badge on Intelligence dock button has no explanation.**
The Intelligence dock button shows a "1" badge in every screenshot. There is no tooltip or flyover explaining what the "1" means (overdue commitment? brief ready?). The badge draws attention but offers no path to resolve it.
Screenshot: `desk-floor-baseline.png` (Intelligence badge visible)

**F9 (P3). Cmd+Enter in Speak opens the HoldSpeak application menu.**
When the measurement script pressed Cmd+Enter (attempting to submit), it accidentally opened the HoldSpeak application menu (visible in `job4-answer-result.png`). The menu shows "List view, Arrange desk, Refresh from hub" then the dock shortcuts. Cmd+Enter is a common "submit" convention but is not wired in the Speak surface -- it falls through to the system menu accelerator. (The correct submit is clicking Deliver.)
Screenshot: `job4-answer-result.png` (accidental menu drop)

**F10 (P3). The search shelf (Cmd+K) is the only discovery mechanism.**
The shelf reveals everything (verbs, programs, drawers, settings), but it requires knowing that Cmd+K exists. There is a "Search Cmd+K" label in the menubar, which is correct, but the shelf is the ONLY way to discover Ask AI, Cadence, Context, Activity, Processes, Integrations, Commands, Runs on, and all the Settings subsections. The dock shows only 5 programs (Intelligence, Speak, Meetings, Agents, Settings) plus Desk memory, Delivery, Panes, and the Record Orb. Everything else is behind the shelf.
Screenshot: `job3-search-shelf.png` (full shelf inventory)

---

### (4) EDITORIAL

**The worst-served job today is Job 3: Capture a TODO.** The product has no concept of a standalone obligation. Follow-Through commitments exist but are exclusively derived from meeting intelligence -- there is no manual entry point. The Cadence surface shows "No open loops" with no affordance to add one. The user must fall back to a Note, repurposing a freeform text primitive as a task tracker. This is not merely an extra-click problem; it is a conceptual gap. A user with something to track who has not just come out of a meeting has no path that names their intent. The "five daily jobs" design should treat quick-capture obligations as a first-class verb, not a Note-shaped workaround. Every other job has a purpose-built surface and verb (Record Orb for meetings, Cmd+N for notes, Ask AI for questions, Agents for coder sessions); TODO has none.