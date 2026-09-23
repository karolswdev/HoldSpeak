# Check — Muad'Dib, 2026-09-23, on Astra's PHILO-3-02 design (`summary-design.md`) and draft canvas

Astra's first attempt to obtain this check ran `claude -p` inside an isolated HOME, which has no Claude credentials ("Not logged in"); that invocation is not a verdict. This check was written by Muad'Dib in his own session (Claude Code 2.1.280) after reading `summary-design.md`, `summary-lane-record.md`, `summary-baseline-capture.md`, the install-d2 report, the fixture manifest and the eight draft boards' findings. No product run.

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
1. **The four product seams are the smallest that buy A2 and I ratify them.** (a) The endpoint model client joins the ordinary install: D2 is reproduced (base install → `from holdspeak.intel import OpenAI` is None; the `meeting` extra supplies it). Tenet 1 and 3. (b) The deferred queue announces running/settled through `notify_desk_changed`, riding the existing trailing debounce; no polling, no new bus protocol — the exact seam both static passes named (`meeting_service.py:289` emits on import only; the drainer never). (c) The Arrival row carries the persisted detail by reading `/api/meetings/:id` for the visible top three on each desk refresh, stale responses dropped by identity and generation. (d) The Arrival keeps its section, ordering, row, Run and Open; the summary lands beneath its row; the receipt renders in every state; planned disclosure before, the actual route after (Article III).
2. **Seam (c) is bounded correctly but must stay bounded.** Three reads per desk refresh, driven only by `desk_changed`/the existing refresh triggers, never a timer. Tenet 1.
3. **The draft canvas is not ratifiable as it stands, and Astra says so.** Its own four findings hold: a title truncated to `Ar...` by retry tokens; 393 boards with verbs behind the dock; the old faint token `#767e8d` (current `#8b93a3`); invented prose in the failure wells; an invented Arrival Retry verb and `2/3` attempt limits that no design has settled. Tenets 3, 5, 6, 7; UX-CANON (design on the library, no prose, the type-scale ruling, 44 px hit at 393). The OWNER ratifies the corrected canvas before seam (d) is built — the standing law.
4. **The proof seams are right.** ONE synthetic architect meeting (retained source, planted decisions/owners/actions, generated speech — labelled as such, never an observed transcript); the real import worker produces duration and transcript; the actual `case.j4/j5/j6/j7` recipes repaired (import completion wait, engine setup window closed before observing, ONE Run, a retained failure reply at the provider boundary, the rig's restart step with before/after identity); technical completion and usefulness reported separately with each planted item mapped to the output including omissions; the owner's sitting never claimed from the fixture. Tenets 2, 3, 7.
5. **Environment facts, accepted:** Node 25's broken `libllhttp` → lane commands use the nvm Node 22 path; the WAV is gitignored by the broad fixture rule → `git add -f` by explicit path is lawful here (a fixture, not evidence); the parked DW capture is honest.

CONDITIONS:
- Seams (a) and (b) may build NOW (no face change): the install correction is the first commit (through the gate, no story flip), then the queue seam with a real-producer fence that fails pre-fix (an admitted job's running → settled transitions reach `notify_desk_changed`).
- Seam (c)+(d): correct the canvas per finding 3 (readable title; attempt/cause facts in the existing below-row well; no new Arrival verb or attempt limit; current tokens; ASD-STE100 state facts, no prose; 393 boards with the real shell/scroll and the dock not covering a verb), then hand Muad'Dib the corrected boards' paths — he publishes them for the owner's ratification; build (d) only after the owner ratifies.
- The failure reply is a retained artifact in the tree (not `.tmp`), named in the atlas case's boundary step.
- The install correction is verified by the same documented base-install reproduction after the fix (its executable assertion exits 0), retained beside the failing one.

MISSED: The install seam decides whether J6 is broken on the owner's own desk today; ship it first and say in the PR whether his documented install path was affected.

TUESDAY: Yes, if (d) lands as designed: he runs the summary where he starts, sees it land, and finds it after a restart.

UNKNOWN: Real LAN completion, restart equality and usefulness — the lane's proof seams; the built face — Muad'Dib's counsel on built.
