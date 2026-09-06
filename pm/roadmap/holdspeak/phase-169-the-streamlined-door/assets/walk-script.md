# HS-169-05 Walk Script

**Runner:** `tests/e2e/live169_walk.py`
**Env:** `HS169_WALK=1` + `HS169_WALK_DB=isolated|real` (default isolated)
**Auth guard:** `gh auth status` exit 0 AND `acli jira auth status` exit 0
**Build:** web bundle rebuilt fresh via `glass_infra._ensure_build`
**Widths:** every step shot at 1440 AND 393

---

## The 5-click Door and the Room's first paint

### Connected leg (isolated fixtures OR real desk)

| # | What the owner sees | The click | Asserted (both widths) | Shot name |
|---|---------------------|-----------|------------------------|-----------|
| 01 | Settings > Connections | (staging) | `connections-github` Connected; `connections-jira` Connected | `01-settings-connections` |
| 02 | New Project first open | (staging) | `door-root` visible; `door-outcome-input` placeholder "What are you delivering?"; both rows UNPICKED; Create disabled; receipt "NO SOURCES" | `02-door-empty` |
| 03 | Type the outcome | (typing, not a click) | `door-outcome-input` filled with "Ship the Q4 platform on schedule with zero incidents"; receipt still "NO SOURCES" | `03-outcome-typed` |
| 04 | GitHub trigger opens picker | click 1: `door-trigger-github` | `door-picker-github` visible; picker items loaded | `04-gh-picker` |
| 05 | Repo card karolswdev/HoldSpeak | click 2: `door-pick-karolswdev/HoldSpeak` | picker closes; state CHECKING then LIVE; `door-counts-github` visible with count text | `05-gh-live` |
| 06 | Jira trigger opens picker | click 3: `door-trigger-jira` | `door-picker-jira` visible; Jira projects loaded | `06-jira-picker` |
| 07 | Jira project card KAN | click 4: `door-pick-KAN` | picker closes; state CHECKING then LIVE; receipt shows SOURCES + WATCHES | `07-jira-live` |
| 08 | Create Project | click 5: `door-create` | Project created; Room opens via `openSurface("open-project-memory", ...)` | `08-create` |
| 09 | Room first paint | (automatic) | `room-body` visible; `room-headline` text matches count or "Nothing needs you"; SOURCES label with count > 0; source-scope tokens not blank; POST /room/read called once; shot within 500ms of window appearing, then again after settle | `09-room-first-paint` |
| 10 | HISTORY wing | click: History tab | `room-history` visible; history entries rendered | `10-history` |
| 11 | Back to Room | click: Room tab | `room-body` visible; headline + sources still rendered | `11-room-return` |

**Click count:** 5 (steps 04, 05, 06, 07, 08)
**Stopwatch:** seconds from step 02 (door open) to step 09 (room first paint)

168 comparison: 17 steps from Settings > Connections to Activated (Part B steps 08-25). 169 comparison: 5 clicks, 11 steps total, no wizard, no test, no review.

---

## LEG: REAL (owner's desk; `HS169_WALK_DB=real`)

Same steps 01-11 against the REAL DB (`~/.local/share/holdspeak/holdspeak.db`) with the owner's real `gh` and `acli`. The real leg uses his KAN project.

**Skip guard:** `HS169_WALK=1` + `gh auth status` exit 0 + `acli jira auth status` exit 0

**Finally:**
1. Disable unattended BEFORE archive (`PUT /api/projects/{id}/steward/policy` with `unattended_enabled: false`)
2. Archive project (`DELETE /api/projects/{id}`) -- never delete
3. READ watch rows (`GET /api/projects/{id}/room`): `connector_watches` state, baseline_state, last_error; assert no blank entries in any list clause
4. Print watch rows before exit

**Shots:**
- Isolated leg: `assets/story-05-walk/isolated-{connected-desktop|connected-phone}/`
- Real leg: `assets/story-05-walk/real-{connected-desktop|connected-phone}/`

---

## Stopwatch targets

| Metric | Phase 168 | Phase 169 target |
|--------|-----------|-----------------|
| Connected > Room with counts | 19 steps, ~28-60s | 5 clicks, 11 steps |
| Clicks to a live Room | 17+ (wizard per Watch, Test, Review, Activate) | 5 |
| Wizards visited | 3 (GH + known-scope GH + Jira) | 0 |
| Test clicks | 3 (one per Watch) | 0 (count IS the test) |
| Review/Activate | 2 steps | 0 (Create = done) |
