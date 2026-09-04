# HS-168-05 Walk Script

**Runner:** `tests/e2e/live168_walk.py`
**Env:** `HS168_WALK=1` + `HS168_WALK_DB=isolated|real` (default isolated)
**Auth guard:** `gh auth status` exit 0 AND `acli jira auth status` exit 0
**Build:** web bundle rebuilt fresh via `glass_infra._ensure_build`
**Widths:** every step shot at 1440 AND 393

---

## LEG 1: ISOLATED (cold then connected)

### Part A: Cold (GH_CONFIG_DIR empty, no Jira, isolated DB, real HOME)

| # | Step | The face | Wire | Asserted (both widths) |
|---|------|----------|------|------------------------|
| 01 | Settings > Connections | Settings window, Connections module | `openSurfaceWindow("configure-settings", "integrations")` | `connections-github` card visible; state chip reads "Sign in" |
| 02 | Connections: Jira state | Same window, Jira card | (loaded with the module) | `connections-jira` card visible; state reads "Not set up" |
| 03 | New Project > Outcome | Interview opens; answer outcome textarea | `POST /api/project-setups`; answer outcome | `setup-root` visible; textarea filled |
| 04 | Notice answered | Signal question answered | answer signals | Suggestions appear (`setup-suggestion-cards`) |
| 05 | Sources: TOOLS row | Suggestion cards + TOOLS row | `GET /api/connections` | `setup-tools-row` visible; `setup-tool-github` reads "Sign in" or "Connect"; `setup-tool-jira` reads "Not set up" or "Connect"; ZERO gh/jira suggestion cards |
| 06 | Press Connect GitHub | Connect card opens Connections window | `openSurfaceWindow("configure-settings", "integrations")` | `connections-github` card visible in a second window |
| 07 | Close Connections | Close Settings window; return to setup | (window leaves `windowsById`) | `setup-tools-row` re-appears; session answers survive (`GET /api/project-setups/{id}` has outcome + signals) |

### Part B: Connected (re-boot with real HOME + isolated DB, prime Jira)

| # | Step | The face | Wire | Asserted (both widths) |
|---|------|----------|------|------------------------|
| 08 | Settings > Connections | Settings window, Connections module | `openSurfaceWindow("configure-settings", "integrations")` | `connections-github` reads "Connected"; Jira connection reads "Connected" |
| 09 | New Project > Outcome | Interview opens; answer outcome | `POST /api/project-setups`; answer outcome | `setup-root` visible |
| 10 | Notice answered | Signal question answered | answer signals | Suggestions appear |
| 11 | Sources: TOOLS + cards | Suggestion cards + TOOLS row | `GET /api/connections` | `setup-tool-github` reads "Connected"; gh suggestion cards present; jira suggestion cards present |
| 12 | GitHub wizard | Click first GH card | (card click) | `provider-wizard-flow` visible; `wizard-heading-name` shows Watch name; `provider-test-btn` disabled (no scope yet) |
| 13 | GitHub scope | Pick `karolswdev/HoldSpeak` from discovery | (card click) | `provider-test-btn` enabled |
| 14 | GitHub test | Click "Test this Watch" | `POST .../proposals/{id}/test` | `provider-test-display[data-test-state="passed"]`; SUBJECT + MATCHES visible |
| 15 | Use this Watch | Click `provider-wizard-done` | (done verb) | Returns to suggestion cards |
| 16 | Second GH: known scope | Click second GH card | (card click) | `known-scope-card` visible; text contains "chosen for" |
| 17 | Use this repo | Click `known-scope-use` | (use verb) | Scope set; `provider-test-btn` enabled |
| 18 | Second GH test | Click "Test this Watch" | `POST .../proposals/{id}/test` | `provider-test-display[data-test-state="passed"]` |
| 19 | Use second Watch | Click `provider-wizard-done` | (done verb) | Returns to suggestion cards |
| 20 | Jira wizard | Click Jira card | (card click) | `jira-wizard-flow` visible; account step skipped (1 connection); `jira-scope-step` visible |
| 21 | Jira scope: pick KAN | Click KAN project card | (card click) | `jira-test-btn` enabled |
| 22 | Jira test | Click "Test this Watch" | `POST .../proposals/{id}/test` | Test step reached |
| 23 | Use Jira Watch | Click `jira-wizard-done` | (done verb) | Returns to suggestion cards |
| 24 | Review | Click "Review" | (advance to review) | `setup-review` visible; `review-watches` lists selected watches; `review-activate-btn` visible |
| 25 | Activate | Click "Activate" | `POST .../finalize` | `setup-done` visible; `GET /api/projects/{id}` returns state=active; both watches baseline established |

---

## LEG 2: REAL (owner's desk; `HS168_WALK_DB=real`)

Same as Part B steps 08-25 against the REAL DB (`~/.local/share/holdspeak/holdspeak.db`).

**Skip guard:** `HS168_WALK=1` + `gh auth status` exit 0 + `acli jira auth status` exit 0

**Finally:**
1. Disable unattended BEFORE archive (`PUT /api/projects/{id}/steward/policy` with `unattended_enabled: false`)
2. Archive project (`DELETE /api/projects/{id}`) -- never delete
3. KAN untouched (no transitions in this walk)
4. DB project count read back before/after

---

## Stopwatch targets

| Metric | Before (audit-today.md) | After target |
|--------|------------------------|--------------|
| Cold > first GitHub on the face | dead end (6 clicks, no GH) | Connect GitHub visible in TOOLS row (step 05) |
| New Project > tested GitHub Watch | 9 clicks, 10.5s | comparable or fewer |
| New Project > tested Jira Watch | 15 clicks, 28.2s (Test gated on Preview) | fewer clicks (scope-only, Test enabled by pick) |
| Second GH Watch (scope carried?) | n/a (scope per proposal) | known-scope card, 2-3 clicks to tested |
| Terminal visits per tool | (embedded in wizard) | 0 from Sources; max 1 from Connections face |
| Sentences on screen | 2 in GH wizard | 0 (zero-sentence law) |
