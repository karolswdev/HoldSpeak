# Core documentation advisory review

Status: UNCHECKED — awaiting Muad'Dib. This is advice from `claude -p`, not Muad'Dib's check. The owner requested this work directly.

## Check — claude -p (claude-opus-5-5), invoked by Astra, 2026-10-29

Two read-only advisory passes were requested. The first found that the initial local source base was stale. The final pass reviewed the integrated draft based on `c161be0e8`. Neither advisory invocation was authorized to edit, test, call the live hub, launch workers, or message anyone.

### Disposition

- **Stale source base:** corrected by creating a fresh managed worktree at current `origin/main`, transferring and reconciling file-level three-way merges, and adding Programs, Calls, The Line, and Phone. No checkout was moved or cleaned.
- **Ask controls and retention:** current Recent/⌘N, scope picker, References, automatic conversation persistence, and separate Note/task actions are documented. Parked controls remain identified as backend/parked capabilities.
- **Setup:** current Readiness, Set up speech, and Say one sentence replace the old SPEECH READY procedure.
- **Prepared procedures:** the catalogue is described as read-only descriptors and plans. The user guide points to current People, Ask, and Project update paths for equivalent work.
- **People setting and scope:** saved setting, environment override, owner-client write access, and launched-agent reads are separate.
- **MCP Program merge spelling:** verified against `holdspeak/mcp/families/program.py` and `services/program_service.py`. The Program guide now tells MCP callers to use `auto`, normalized by the service to `level`. Product code is unchanged.
- **Overbroad People sentence:** the user guide now says agents launched by HoldSpeak do not write People. An owner-authority external MCP client can have write access under the effective setting.
- **Current roster:** the root's live-registry documentation guards verify 306 tools and the resource counts. The advisory reviewer did not import or measure those counts.

The source review and scoped checks do not establish a live microphone, model, line, call, delivery, or owner visual acceptance. The full handover and public-document coverage are recorded in `docs/internal/CORE-DOCS-REFRESH-2026-10-29.md`.

## Final advisory response, before the two wording fixes above

No material doc defects remain in the parts I sampled, apart from one MCP spelling mismatch and one misleading People sentence below. I worked read-only against `c161be0e8` (HEAD is the same commit as `origin/main`). I did not run the hub, the tests or a live flow, so none of this proves runtime behaviour.

**The six earlier findings are fixed in the docs, and the sampled ones match the source:**
- **Recent rail and ⌘N:** checked. `askFace.tsx:316–335` puts "+ New ask ⌘N" as the rail's first row, and `AskPanel.tsx:1196–1197` handles ⌘N/Ctrl+N. GETTING_STARTED:123, USER_GUIDE:20 and :634, AGENTS_AND_THREADS:25 and README:110 match.
- **Setup:** checked. `applications.ts:308` has the Setup app, and `SetupFace.tsx` has Readiness (:563), Say one sentence (:672) and Keep as note (:646); `SpeechSetup.tsx` exists. GETTING_STARTED:95–106 matches, and it says the older first-run screen is parked.
- **Ask kept as a Thread with References:** the docs are consistent (USER_GUIDE:617–618 and :668, AGENTS_AND_THREADS:8–9 and :33). I did not trace the save timing in the source.
- **Prepared procedures:** checked. The three descriptors are in `recipe_catalog.py:368`, `:461` and `:553`. USER_GUIDE:340–400 calls the catalogue read-only, gives a real feature path for each result, and separates it from Programs.
- **People access:** checked. The saved `people.mcp_access`, the env override, the default `write` and "launched agents read unless off, never write" match `config/people.py` and `mcp/families/people.py:232–287` and `:460–465`. MCP_SIDECAR:50–66 and PEOPLE_SECURITY:31–46 are accurate.
- **Programs, Calls, Phone:** checked. The gates depend on each step's settings and the Control level (programs.md:4–5, :21 and :173; USER_GUIDE:394). The review values `none|agent|person` match `program_service.py:111`. phone.md:7–11 and README:224 both say the iPhone app transport is not finished.

**Findings**

1. **The MCP schema refuses `gate_merge=level`, the value programs.md teaches** (plausible; it matters to MCP callers).
   - programs.md:21 and :173 name the merge values `level|owner|none`. The service accepts those and maps `auto` to `level` (`program_service.py:110` and `:1176–1179`).
   - But the MCP step schema allows only `["owner","auto","none",null]` (`holdspeak/mcp/families/program.py:60`), and `mcp/tools.py:679` checks every call against its schema.
   - So an MCP client that sends `"gate_merge": "level"` gets `Invalid arguments` back. The web/API path and the templates (`program_templates.py`, all `"level"`) work.
   - Fix one of two ways: add `"level"` to the enum in `program.py:60` (a source change, outside a docs PR), or add a line in programs.md saying MCP spells it `auto` until that change lands.

2. **USER_GUIDE:612–614 says "Agents do not write People records", which is too broad.**
   - With the default `write` mode, an outside MCP client can call the People write tools (`people.py:377`, `_require_access(write=True)`).
   - Only agents that HoldSpeak launches are kept to reads (`people.py:232–234`, `:249–250`).
   - The same paragraph tells readers to pick `read` or `off` to remove write access, so the two sentences contradict each other.
   - Fix: say "Agents that HoldSpeak launches do not write People records." The heading "The dev keystore" also doesn't match what the paragraph covers; that one is minor.

**What I did not check**
- The README and MCP_SIDECAR:394 figure of "306 tools across 52 families". There is no generated count in the tree to compare against, and I did not import the registry.
- The rest of AGENTS_AND_THREADS, calls.md past the setup and gate sections, and the architecture overviews.


## Initial advisory response, historical stale-base draft

Advisory only; I edited nothing. I ran no tests or builds, made no MCP calls, and launched no agents.

## Findings, most important first

**1. The branch is far behind main, and the docs were checked against old code (high; affects every "active UI" claim).**
- The worktree branches from `33fdbce59` (#1456). `origin/main` is now 153 commits ahead, at `c161be0e8` (#1611).
- Main has also edited 27 of the same public docs since then. That includes README, GETTING_STARTED, USER_GUIDE, WEB_DESK, AGENTS_AND_THREADS, MCP_SIDECAR, SECURITY, MODELS, AUTOMATION and INTERVIEW, so merging will conflict.
- `web/src/desk/components/AskPanel.tsx` changed by 638 insertions and 302 deletions on main (#1515 "the Recent rail", #1538, #1565, #1583).
- Main added Programs (#1602, #1604), Phone (#1605), the Line (#1606–#1610) and `docs/calls.md`. None of these are in the rewrite. Programs is main's orchestration engine for agents, so this is a real gap for an "agentic-first OS" story. Today it is a missing feature, not a false claim.
- **Fix:** rebase onto `origin/main` and keep main's doc edits when resolving. Re-check every quoted control label against main's source. Then either add short sections on Programs and Calls/Phone/Line, or say plainly what the docs leave out.

**2. "New ask" is false on main (false claim after rebase).**
- The docs that say it: `README.md:107`, `docs/AGENTS_AND_THREADS.md:25`, `docs/USER_GUIDE.md:593`, `docs/WEB_DESK.md:91`.
- The label exists in the worktree's AskPanel (1 match) but not in main's (0 matches). On main, a new ask is the first row of the Recent rail, or ⌘N (`AskPanel.tsx` on main, around lines 1196–1200, which calls `startNew`).
- **Fix:** "Start a new conversation from the first row of the Recent rail, or press ⌘N." Check the rail's wording while you are there; #1515 changed how Recent is shown.

**3. The "Prepared work: Running one" steps cannot be followed (unusable instructions; framing is close to false).**
- `docs/USER_GUIDE.md:336-358` lists steps to "run" the three prepared procedures. Step 2 is "Ask for the draft or update," which names no control.
- In the code, the procedure catalogue only describes and plans. The routes `GET /automations/practice-recipes`, `.../{id}` and `.../{id}/plan` are all reads (`holdspeak/web/routes/automations.py:126-160`; the plan route's docstring says "writes nothing and runs nothing").
- The MCP family `holdspeak/mcp/families/practice_recipe.py` is described as "Three read-only tools," kept out of the Thread tool set (`CHAT_PALETTE`).
- No active Desk window calls these routes; the only `web/src` hits for `practice` are in tests or parked files.
- **Fix:** say the descriptors are a read-only catalogue that compiles a plan. Point each procedure to the control that actually runs it:
  - weekly update: Project Room **Write update** (`project.draft_update`)
  - meeting preparation: the People 1:1 brief (`people.one_on_one_brief`)
  - decision review: confirm its real entry point before naming it
  
  Keep steps 3–6 (check sources, Wrote, Prepared, Send).

**4. GETTING_STARTED names a status that no longer appears (false claim, small).**
- `docs/GETTING_STARTED.md:100-101` says to wait for **SPEECH READY**.
- That string only exists in `web/src/desk/firstrun/_parked/FirstRun.parked.tsx`.
- The active `SetupFace.tsx:449-463` decides readiness from the speech row's `works` state and shows "Ready, {ownerName}." only once the owner's name is also set.
- **Fix:** "Wait until the Speech row shows that it works." Check this against main's first-run screen after the rebase.

**5. The MCP sidecar doc leaves out how People access is really set (missing information, not false).**
- `docs/MCP_SIDECAR.md:50-58` presents the environment variable `HOLDSPEAK_MCP_PEOPLE_ACCESS` as the only way to restrict access.
- `holdspeak/config/people.py:1-11` and `onboarding_operations.py:81-86` show three more facts:
  - a saved setting exists (`people.mcp_access`, set by the owner-only `people_access.set`)
  - the environment variable overrides that saved setting
  - an agent that HoldSpeak launched always gets `read` unless access is `off`
- The line "applies to all MCP clients" is therefore slightly wrong for launched agents.
- **Fix:** list the saved setting first, then the environment-variable override and the launched-agent rule.

## Claims I checked and found correct
- **README:** 14 built-in meeting plugins (`plugins/builtin/__init__.py:125-140`); YOLO is the default (`db/schema.py:527`); Python 3.10 or later.
- **Install extras:** the `meeting`, `dictation-mlx`, `wakeword`, `tts` and `linux` extras exist, and so do the `doctor`, `restore` and `web` commands. Running bare `holdspeak` starts the web hub.
- **Thread limits:** 10 model passes (`thread_service.py:118`); 30 s per tool call (`thread_service.py:121`); 16 references and 12,000 transcript characters (`grounding.py:26-27`); Automation memory of 100 entries, 20 recalled, 2,048 bytes (`workbench_memory.py`).
- **People redaction:** the redaction step on cloud routes exists (`thread_service.py:2358-2381`), and agent CLI engines count as cloud routes (`cli_engine.py:278-289`).
- **Coding agents:** the brief cap is 32,768 bytes (`agent_brief.py:38`); `working_at_once` defaults to 6; every `/api/coders/*` route in the table exists.
- **Sending:** only the owner can send (`channel_operations.py:251-260`).
- **People over MCP:** only shared-intent material is returned (`mcp/families/people.py:56,329`).
- **Desk windows:** `NOT_ON_HUB` is in `desk_window_service.py:89`, and the ⌘I shortcut exists.
- **UI labels:** every quoted label I grepped (Develop this thought, Find the tasks, Hand to agent, Start when one is free, Looked at, Review by, Put it in, Write update, Keep as note, Continue later, Allow once, Re-check) exists in active, non-parked code at the worktree base.

## What I could not check
- I only grepped static source. Nothing here proves how anything behaves at runtime, including whether a label is actually on screen in a given state.
- I checked against the worktree's base commit. After the rebase in finding 1, all UI-label checks need to be redone against main.
- I sampled only: README, GETTING_STARTED, AGENTS_AND_THREADS, CODER_INTEGRATION, MCP_SIDECAR, the Prepared-work section of USER_GUIDE, and parts of WEB_DESK and DESK_ARCHITECTURE.
- I did not review WHAT_IS_HOLDSPEAK, INTERVIEW, ARCHITECTURE_WORK, AUTOMATION, MODELS, SECURITY (beyond grep hits), PEOPLE_SECURITY, SYSTEM_ARCHITECTURE or DOMAIN_MODEL in depth.
- I did not trace whether **Ask about this** on a person can send People-derived text through AskService to a cloud engine. The redaction I confirmed is ThreadService's. That path deserves its own check before the docs promise that People text is redacted for Ask as well.


## README visual revision advisory, 2026-10-29

The owner asked for a more alluring, modern, simple, screenshot-rich README. A further read-only `claude -p --model claude-opus-5-5` advisory reviewed this separate editorial revision. This is advice invoked by Astra, not Muad'Dib's check.

Disposition: corrected the two template names against the Programs guide, put the fixture disclosure beside the first Program image, removed repeated feature descriptions, simplified the phone/Calls explanation, and stated the meeting plugin engine prerequisite. Kept the numeric tool claim because live documentation guards enforce the registry count. The first Ask flow uses the hero screenshot; an additional nearly empty Note image would repeat the visual story. Root inspected all seven source images, including the JPG and Program captures the advisor did not open.

### Advisory response before corrections

The raw response uses paths relative to the repository root.

```text
**Verdict: Pass, with five small fixes.** The README has a clear goal and enough screenshots. All its links, anchors and image paths resolve. `agents.png`, `ask-mobile.png` and `project.png` are byte-for-byte copies of the files in `docs/internal/betterment/native-experience/atlas-2026-10-27/`. The alt text on those three images matches what they show.

**Findings**

1. **`README.md:106`: two Program template names do not match the guide.** `docs/programs.md:51-52` names them **Overnight on the home box** and **From the desk**. Suggested wording: "Templates include **Fast cycle**, **Build and review**, **Race**, **Overnight on the home box**, and **From the desk**."

2. **`README.md:168`: the note that the Program images come from test fixtures is too far from the first one.** That image is at line 97, 70 lines above the note. A reader sees "a pull request ready for a merge decision" as live product. Add to the caption at line 99: "*… (Check and pull request states come from a test fixture.)*" Keep line 168 as the general note.

3. **`README.md:19-26` repeats what comes next.** Line 23 ("find evidence, write a Note, make a task, or prepare an update") comes back almost word for word at lines 51-52. Lines 24-26 say the same as the table rows at lines 39-41. Suggestion: cut lines 23-26 to one line, such as "**Agentic-first:** Ask, coding agents, Programs and Automations act with tools on the context your Desk already holds." Let the table carry the rest.

4. **`README.md:148-166` puts three different topics under "Take the Desk with you".** Mobile, voice typing, and Calls/Line/Phone share one section. Lines 163-164 ("The Line supplies a SIP adapter; ai-phone is an optional alternative. Phone adds reach-you rules. Its iPhone-app transport is still incomplete.") is internal jargon in a showcase README. Suggestion: keep the two phone screenshots and voice typing here. Move Calls to one line: "With Calls set up, you can phone your Desk to ask, add a task or write a Note. [Calls](docs/calls.md)". Leave the Phone transport status to `docs/phone.md:8`, which already says it.

5. **`README.md:68`: "14 built-in plugins" is correct but leaves out a condition.** The count matches `_BUILTIN_PLUGIN_DEFS` in `holdspeak/plugins/builtin/__init__.py`. But `docs/MEETING_INTELLIGENCE.md:36-42` gives no count and says each plugin needs an engine assignment, or it records a skip. Suggestion: "HoldSpeak includes 14 built-in plugins; each one runs on the engine you assign to it."

**Smaller points**

- **`README.md:196`:** "306 tools across 52 families" matches `docs/MCP_SIDECAR.md:394`. It will drift as tools are added. Either drop the numbers ("a full catalogue of Desk tools; each caller sees only its allowed tools") or accept that both files must be updated together.
- **`README.md:111-112`:** the overnight sentence is hard to read. Suggestion: "If an agent reaches its usage limit, a fallback agent continues on the same step, branch and worktree. **Overnight on the home box** runs pi on your idle home engine."
- **`README.md:44`:** "From a thought to a useful result" is the first and most agentic flow, but it is the only main flow with no image. If the atlas has a Note or "Develop this thought" capture, put it here.
- **`README.md:120`:** the caption quotes "What needs me?", but the window in the image shows **Needs you**. Use the label on screen.

**Unknowns**

- I did not open the two JPGs or the two Program PNGs. The hero alt text (line 9) and the Program alt text (lines 97 and 152) are not checked against their images.
- I did not check these claims against source: "Speech recognition runs locally with Whisper" (line 172), Calls' spoken confirmation (line 162), and Gemini CLI as an engine. `docs/MODELS.md:47` does list Gemini CLI.
```
