# Programs: the Program language, shaping and the SDK (PG-LANG)

Owner, 2026-10-31, after Programs gained Requirements (#1664 design, #1665
build): "imagine an interface that lets me build and adjust those programs on
the fly, seamlessly, by allowing me to shape them. This is, by all means, an
SDK, right? Voice input gets inferred in LLM calls and specific conditions are
met, right? Incredible ease and power … With planning inference, maybe even
like a basic 'syntax' for programs, broken down, and so on? Not to mention
delivery-workbench integration (but only on major points, let's please not
over complicate by being too granular on dw level - it is known to be blowing
up in verbosity the more we do it on a granular level). … one of the main
things I'd imagine happening inside the Desk ecosystem that is going to blow
people's lids off … an absolutely powerful orchestration engine that lets you
be as hands off as possibly can, but also allow you to be so super hands-on
where we, at each time of the 'definition' phase, can add additional detail,
gates, types of verification required…, and so on. It's going to be important
to absolutely nail on this - both from a system perspective, as well as its
integration with HoldSpeak in general, its general tenets of the eco-system.
As well as its intricately delightful User Experience, absolutely beautifying
and tensifying this experience into pure execution perfection. And if this
requires us to modify the existing common component library and or engine? We
roll up this type of work in the overall plan."

The same day, extending the brief: "Make sure you perfect the design and also
immediately draft, project and model user journeys that solve multiple use
cases. Including, e.g., haiku driven nightly 'dreaming' program that uses our
idle GPU with pi, on super broken down tasks (IMO our context maxes out at 64k
tokens). And so on. Again - from dropping only a couple of paragraphs, to a
broken down, refined down sets of steps that execute, verify, prove, to some
kind of 'Architecture, Product, Stacker, and so on' interview rounds and gates
to allow me to provide down to detail level of clarity, smoothly. So UX will
be key. If it means canvas? It means that."

Sources: `PROGRAMS-DESIGN-2026-10-28.md` (the engine, its "Built" section and
PG19), `PROGRAMS-REQUIREMENTS-2026-10-31.md` (requirements, browse, adjust),
`RECIPE.md` (PG1 to PG21, PG-REQ), `docs/programs.md`,
`agent/skills/holdspeak-programs/SKILL.md`, the code on `main` at `cb6ab84e5`.
The journeys (the dreaming night, two paragraphs to Done, the interview
rounds, a call, an orchestrating agent) are in the sibling document
`PROGRAM-JOURNEYS-2026-10-31.md`, written by a parallel lane; this document is
the system and the faces those journeys run on. Canvas:
`canvases/program-language-2026-10-31.html` (the Program window with the Text
view beside the board, the shaping bar, the planning draft, the interview
round, three directions for the shaping surface with the recommended one
marked). The owner's "go with suggestions" (2026-10-27) pre-approves the
recommended directions; he judges them live on his desk.

Tenets check (Constitution, the Seven Tenets). (1) No safety machinery is
added: shaping rides the gates, the proposal rows and the control ladder that
exist; the one new guard ("a shaped change never lowers the bar") reuses the
frozen table of PG-REQ §8. (2) The point is his first real use: a Program
made from two paragraphs, in minutes. (3) One window, two views, one shaping
bar; no new window for any of it. (4) Product words follow ASD-STE100; the
Program text itself uses short, plain keywords. (5) The new pieces (a diff
row, a text pane with line lamps, a question row) go into the kit first
(§11). (6) Workbench on steroids: a text you can read beside a board you can
press. (7) The first user is a Senior Software Architect: the interview
rounds are the architecture review he would run for a report.

## 1. The job

A Program today is built by pressing: New program, a goal in a PadGadget,
steps as rows of gadgets, requirements as rows (`ProgramWindow.tsx:572`
to `:606`). That is right for one step and slow for twelve. It is also
mute: the mic on each gadget fills one field, never the plan. And the plan
comes only from him or from an orchestrating agent's `program.plan` call;
the desk itself never proposes one (the Note's "Run as a program" makes a
Program with a goal and no steps, `web/src/desk/programs/fromNote.ts:14`).

He works in three stances, and the design serves all three on one record:

1. **Hands-off.** He drops a goal (two paragraphs, a Note, a sentence on a
   call) and goes. The engine plans, sizes the steps for the engine that will
   run them, starts at his level, and at YOLO he wakes to merged PRs and a
   digest.
2. **Hands-on at definition.** While the Program is in Drafting he and the
   engine co-write it. He adds detail, gates and the kind of proof each step
   needs; the engine asks the few questions that change the plan, in named
   rounds (Architecture, Product, Stack, Verification, Delivery).
3. **Shaping on the fly.** While it runs he says or types one sentence ("put
   the People routes on Codex and make step 6 wait for the loop watch") and
   sees the change as a diff on the board; Apply, or at YOLO it applies and is
   listed under Decided for you with Overturn.

**The Program text is a readable, line-oriented view of a Program that
round-trips with its tables. He reads and edits it beside the board; a
sentence (spoken or typed) becomes a proposed change to that text through one
inference call; the change lands as diff rows he applies with one press. The
same text is the SDK's format for agents and scripts.**

## 2. What it is not

- **Not a file he hand-edits as the primary surface.** The board, the
  Requirements board and the shaping bar stay the primary faces. The text is
  a second view of the same record, for reading the whole plan at once, for
  precise edits, and for agents. It is not stored as a file and is never the
  truth; the tables are (§3.6). This keeps the 2026-10-28 rule "Not a workflow
  DSL … one record … edited three ways" (`PROGRAMS-DESIGN-2026-10-28.md:37`):
  the text adds a fourth way to edit the same one record, not a second
  record.
- **No YAML, no JSON for people, no graph language.** Dependencies stay
  "after 2, 3". There are no variables, no loops, no conditions, no
  includes. A line says one thing.
- **Not a second orchestrator.** The engine (`program_runner.py`) runs
  steps exactly as now. The language service writes through the service
  verbs that exist (`plan`, `update`, `require`, `edit_requirement`,
  `change_step`, `amend`; `program_service.py:1576`, `:1501`, `:2193`,
  `:2304`, `:2643`, `:2801`), under the same lock, with the same
  checkpoints and frames. A text apply is a batch of those calls, not a new
  write path.
- **Not a chat.** The shaping bar takes one sentence and gives one diff. It
  keeps no conversation; the Program text is the memory.
- **No Delivery Workbench per step.** dw sees a Program at two points: when
  it is linked to a story, and at Done (§8). Never a step, a checkpoint, a
  brief, a finding.
- **Not a new trust level.** A sentence from him is his; a change an agent
  writes as text goes up the ladder exactly as `step_change` does today
  (`PROGRAMS-REQUIREMENTS-2026-10-31.md` §6). No model output is ever
  applied as if he had typed it, except at YOLO and then never when it lowers
  the bar (§4.6).

## 3. The Program text

### 3.1 The shape at a glance

```
# program text 1
program The hub stops stalling
  goal
  > Make the hub answer every route under 100 ms while a meeting records.
  > Nothing on the event loop takes a lock.
  in HoldSpeak · main · project HoldSpeak
  control normal
  check scripts/quick_check.sh
  agent Claude Code, then Codex
  reviewer Codex at delta
  for Alice

every step
  R2 review: The change does only what its brief says.
  R3 check: `uv run pytest -q tests/unit/test_hub_loop_budget.py` is green.

at the end
  R1 word: I used the desk for a morning with no stall.

step 1 Indexes                                   # Merged #1585 · 41 min
  owns holdspeak/db/schema.py
  agent Claude Code · effort low

step 4 People routes                             # Working · Codex · 12 min
  owns holdspeak/web/routes/people.py
  after 1, 2
  agent Codex
  brief
  > Move every People handler's database work into run_in_threadpool.
  + Also the avatar route.                         # sent 14:05
  R5 shot: The People window at 393 has no clipped text.

step 6 The fan-out                               # Planned
  after 4, 5
  review agent at standard · merge owner
  brief
  > One frame per change, not one per row.
```

### 3.2 The grammar

Lexical rules:

- One statement per line. Two spaces of indent put a line under the last
  `program`, `step`, `every step`, `at the end` or `round` header. A line
  under a requirement (four spaces) adds to that requirement.
- `#` to the end of a line is a **lamp**: the printer writes the state there
  ("Merged #1585 · 41 min", "Met · log", "sent 14:05"); the parser ignores
  every lamp. A lamp is never stored and never changes anything. This is how
  the text shows the run without making the run editable.
- `>` starts a line of his words (a goal or a brief), kept byte for byte
  after the `> `. Markdown inside is kept as it is.
- `+` under a started step is an amendment line (PG-REQ §8, `amend`).
- `·` joins several short statements on one line (`agent Codex · effort
  high`); the printer joins only the step's agent line and its gate line.
- Keywords are lower case English words. A value that is a name (an agent,
  an engine, a person, a project, a template) is matched the way the faces
  match it (case and spaces do not count; `codex` = `Codex`).
- The first line `# program text 1` names the format version (§7.4). It is a
  lamp; a text without it is read as the current version.

The statements (EBNF; `TEXT` is the rest of the line; `NL` the line end):

```
text        = [version] program-block { req-block | round-block | step-block } ;
version     = "# program text " INT NL ;
program-block = "program " TEXT NL { "  " program-line NL } ;
program-line  = "goal" NL { "  > " TEXT NL }
              | "in " REPO [ " · " BRANCH ] [ " · project " NAME ]
              | "control " ( "secure" | "normal" | "yolo" )
              | "check " ( COMMAND | "none" )
              | "agent " AGENTS                     (* the default Runs on list *)
              | "reviewer " AGENT [ " at " DEPTH ]
              | "planner " ENGINE                   (* the engine of the library that plans and shapes, §4.3, §5.5 *)
              | "budget " TOKENS                    (* the context budget, §5.4 *)
              | "when idle" | "may call" | "may hand off"
              | "allow " AGENT { ", " AGENT }       (* allowed agents *)
              | "spend up to $" NUMBER
              | "for " PERSON
              | "from " REF                         (* origin: note:…, meeting:…, decision:… *)
              | "template " TEMPLATE
              | "delivery dw " DW-REF               (* §8, opt-in *)
              | "night " TIME "–" TIME [ " · at most " INT " steps" ]   (* §5.5 *)
              | "within " PATHS ;                   (* the files the Program may own at all, §5.5 *)
req-block   = ( "every step" | "at the end" ) NL { req } ;
req         = "  " RID " " KIND [ " optional" ] ": " TEXT NL { "    " req-line NL } ;
RID         = "R" INT | "R+" ;                     (* R+ = a new requirement *)
KIND        = "check" | "review" | "shot" | "word" | "measure" ;
req-line    = "run " COMMAND | "expect " PATTERN | "shot " CASE " at " ( "393" | "1440" )
            | "walk " TEXT                          (* a line of a Your word walk, §6.3 *)
            | "bound " METRIC OP NUMBER UNIT ;      (* measure only, §6.3 *)
round-block = "round " ROUND " · " ROUND-STATE NL { "  ? " TEXT NL [ "  = " TEXT NL ] } ;
step-block  = "step " ( INT | "+" ) " " TEXT NL { "  " step-line NL } ;
step-line   = "owns " PATHS | "after " INT { ", " INT }
            | "agent " AGENTS | "effort " ( "low" | "medium" | "high" )
            | "race " ( "2" | "3" ) | "when idle" | "may call"
            | "check off" | "review " ( "none" | "agent" | PERSON ) [ " at " DEPTH ]
            | "merge " ( "level" | "owner" | "none" )
            | "budget " TOKENS | "for " PERSON | "from " REF
            | "merged #" INT [ " · " DATE ]         (* PG17 history steps *)
            | "brief" NL { "  > " TEXT NL }
            | "+ " TEXT                              (* an amendment *)
            | req ;
AGENTS      = AGENT { ", then " AGENT } ;          (* PG19's ordered list *)
AGENT       = "Claude Code" | "Codex" | "pi" [ " on " ENGINE ] | "the desk's agent" ;
TOKENS      = INT ( "k" | "" ) ;                   (* 64k = 65536 *)
```

Defaults are not printed. A step with the Program's agent prints no `agent`
line; a step with the template's gates prints no `review` or `merge` line; a
requirement whose `run`, `shot` or `expect` is what the kind rule guesses from
its sentence prints no sub-line (`program_requirements.guess`,
`holdspeak/services/program_requirements.py:60`). The printer writes the
shortest text; the parser fills every default by the same rules the service
already uses (`triage_effort`, `program_service.py:256`; the template's step
shape, `program_service.py:1608`). That is what makes the round trip exact
and the text short.

### 3.3 The round-trip rule

The text covers the **definition**: every field that `program.create`,
`update`, `plan`, `require`, `step_update` and `amend` can write, and nothing
else. The run (state, launch, worktree, branch, PR, check log, verdicts,
findings, handoffs, evidence, judgements) is never in a statement; it is in
lamps.

The rule, tested over every recorded fixture and a generator of random
Programs (T1):

1. `parse(print(p))` gives back every definition field of `p`, equal.
2. `print(parse(t))` is `t` in canonical form (defaults dropped, `·` joins,
   lamps rewritten from the record).
3. `diff(print(p), t)` is empty if and only if `t` changes no definition
   field.

A field the text cannot say is a design bug, not a loss: the lane adds the
statement. The only data that is not a statement is runtime data, named
above.

### 3.4 Identity, order and new things

- A step's identity is the number in its header **at the base the edit
  started from** (§3.6). Its new order is its place in the text. Moving a
  block of a Planned step is a move (`change_step(before=…)`); the numbers
  then follow the order, as decision 6 of PG-REQ ruled.
- `step +` is a new step. Where it sits is where it is inserted
  (`plan(before=…)`, `waits` on).
- A requirement's identity is its `R n`; `R n` is never reused
  (PG-REQ §3). `R+` is a new one; the apply gives it the next number.
- Removing the block of a Planned step removes the step (the `replace` path
  already deletes Planned steps, `program_service.py:1696`). Removing the
  block of a started step is refused: "Step 4 started. It stays; park the
  program or skip the step in Your turn."
- Removing a requirement line is refused for every requirement: "R4 stays.
  Waive it with a line." (PG-REQ decision 7: only his Waive lowers the bar.)
  `R4 waived: <his line>` is the text's own waive (his only).
- Removing a `+` amendment that was sent is refused: "It was sent at 14:05."

### 3.5 Frozen fields

The text obeys the frozen table that exists (`step_fields`,
`program_service.py:451`, the four reasons at `:440`–`:443`). A changed line
that touches a frozen field is a **refused change** with the same words the
board's hover title uses:

```
step 4 · brief   The agent has read it. Add a line with + instead.
step 4 · agent   The worktree and the agent are set. Hand off instead.
step 2 · owns    It is merged.
step 3 · check off   The bar does not come down while it runs.
```

The parser never guesses around a frozen field: it reports the line, the
field and the reason, and the rest of the diff stays as it was proposed.

### 3.6 The text is a view; the database stays the truth

- `program.text` (get) prints the text from the tables at this moment, with
  the lamps, and returns `revision` (`programs.revision`, bumped by every
  `_touch`, `program_service.py:3205`).
- `program.text_apply` takes `{base, text, preview}`: `base` is the text he
  started from (the client keeps it), `text` is his. The service computes the
  changes as `diff(parse(base), parse(text))`, then checks each change
  against the record **now**:
  - a change to a field whose value now differs from its value in `base` is a
    **conflict** ("Step 4's agent changed since you read it: now Codex");
  - a change to a frozen field is refused (§3.5);
  - everything else is allowed.
- The engine's own moves bump the revision all the time (a step goes from
  Working to Checking). They do not conflict, because they touch no
  definition field: an edit started an hour ago still applies.
- `preview: true` writes nothing and returns the change rows (§3.8).
  `preview: false` is atomic: every change is applied in one transaction
  under `_LOCK`, with one checkpoint "Changed by the text: 3 changes" plus the
  checkpoints each verb writes, one `program_changed` frame and one
  `desk_changed("program", id, "text")`. If any change is refused or in
  conflict, nothing is written and the answer is the change rows. The
  preview also returns `allowed_text`: the proposed text with each refused
  hunk put back as it was in `base`, so "Apply the rest" is one more apply of
  that text, not a second code path.

### 3.7 Five examples

**Fast cycle** (the form HoldSpeak's own lanes take; three briefs pasted):

```
# program text 1
program Hub loop budget
  in HoldSpeak · main · project HoldSpeak
  template fast cycle
  control yolo

every step
  R1 review: The change does only what its brief says.

step 1 Pipeline events index
  owns holdspeak/db/pipeline_events.py
  brief
  > Add the (kind, at) index; the Needs you scan reads 1.39M rows today.

step 2 Retention thread
  owns holdspeak/db/pipeline_events_retention.py
  brief
  > Prune READ receipts older than HOLDSPEAK_EVENT_RETENTION_DAYS in a daemon thread.

step 3 Loop watch
  owns holdspeak/web/loop_watch.py
  after 1
  brief
  > Log each handler that holds the event loop over 100 ms when HOLDSPEAK_LOOP_WATCH=1.
  R4 check: `uv run pytest -q tests/unit/test_hub_loop_budget.py` is green.
```

**Overnight** (the template's own defaults, so few lines):

```
program Words wave, part 3
  in HoldSpeak · main
  template overnight
  agent pi on qwen3.8-27b, then Claude Code
  budget 64k
  when idle · may call

step 1 Settings words
  owns web/src/desk/settings/
  brief
  > Every Settings label in ASD-STE100. Keep the ids.
```

**Race**:

```
program Faster sweep
  in HoldSpeak · main
  template race

step 1 Sweep in one browser
  race 2
  agent Claude Code, then Codex
  brief
  > Run every case of tests/e2e/test_desk_sweep.py in one browser context.
  R2 measure: The sweep takes under 6 minutes.
    run uv run pytest -q tests/e2e/test_desk_sweep.py --durations=0
    bound total < 6 min
```

**From the desk** (one step per open action; `from` names each origin):

```
program Atlas wave 6
  in HoldSpeak · main · project HoldSpeak
  template from the desk

step 1 Cite the Calls window in the atlas
  from action:act-91c2
step 2 Cite the Line settings in the atlas
  from action:act-91c3
```

**A running Program he changes** (the base, then his text; the diff is in
§3.8):

```
step 5 Projects routes                            # Findings · round 2
  owns holdspeak/web/routes/projects.py
  agent Claude Code
  R6 review: No new route skips the residual set.  # Unmet · round 2

step 6 The fan-out                                # Planned
  after 4, 5
```

becomes

```
step 5 Projects routes
  owns holdspeak/web/routes/projects.py
  agent Claude Code, then Codex
  R6 review: No new route skips the residual set.
  + The fold route needs its residual-set entry.

step + The loop watch
  after 4
  agent pi on qwen3.8-27b · effort low
  brief
  > Log handlers over 100 ms.

step 6 The fan-out
  after 4, 5, 7
  merge owner
```

### 3.8 The diff form

A diff is a list of **change rows**, each one statement, in reading order.
Each row has an `op` (`add`, `change`, `remove`, `move`, `amend`), the
`where` (`program`, `step 5`, `R6`), the `before` and the `after` lines, a
`say` sentence (for a call, §10), a `verdict` (`allowed`, `refused`,
`conflict`, `lowers`) and, when not allowed, its `reason`. The example above:

```
~ step 5 · agent      Claude Code  →  Claude Code, then Codex          allowed
+ step 5 · amend      + The fold route needs its residual-set entry.     allowed
+ step 7 The loop watch · after 4 · pi on qwen3.8-27b · low                allowed
↕ step 7              before step 6 (step 6 is now step 8)                allowed
~ step 8 · after      4, 5  →  4, 5, 7                                    allowed
~ step 8 · merge      level  →  owner                                     allowed
```

A unified line diff of the text is also returned (`patch`), for agents and
for the Text view's gutter; the rows are what the faces draw.

### 3.9 Refusals

Every refusal is by name (Constitution V.3), with a code an agent can read:

| Code | Words | When |
|---|---|---|
| `text_unknown_word` | "Line 7: 'budjet' is not a word of the program text." | a keyword the version does not know |
| `text_bad_value` | "Line 9: effort is low, medium or high." | a value out of its set (the service's own words) |
| `step_frozen` | "Step 4 · brief: The agent has read it. Add a line with + instead." | §3.5 |
| `text_conflict` | "Step 4's agent changed since you read it: now Codex." | §3.6 |
| `step_stays` | "Step 4 started. It stays." | a started step's block removed |
| `requirement_stays` | "R4 stays. Waive it with a line." | a requirement line removed |
| `text_version` | "This text is version 2; this hub reads version 1." | §7.4 |
| `requirement_unprovable` | "A shot needs a window and a width." | as PG-REQ |

## 4. Shaping: a sentence becomes a diff

### 4.1 The loop

1. He says or types one sentence in the **shaping bar** (§9.2) of a Program
   window: "put the People routes on Codex and make step 6 wait for a loop
   watch step".
2. The hub tries the **quick forms** first (§4.4): a closed set of sentence
   shapes read by rule, with no model, in under 50 ms. Most short edits end
   here.
3. Else one inference call (§4.3) with the current text, the sentence and the
   grounding returns **block edits** (§4.5).
4. The hub splices the blocks into the current text, then runs the same
   `text_apply` preview as a typed edit (§3.6). Shaping has no write path of
   its own.
5. The diff rows land on the board under the shaping bar. He presses
   **Apply** (or **Not this**). At YOLO the allowed rows that do not lower the
   bar apply at once and are one line under Decided for you with **Overturn**
   (§4.6).

### 4.2 Where the mic sits

- The shaping bar is a `StringGadget` with its mic (`gadgets.tsx:266`, `mic =
  true` at `:272`): the voice law, one mic authority (the bar's). Hold to talk
  or press the mic; the words fill the bar; Return (or the end of a held
  press) sends.
- The Program window registers a voice grammar `program`
  (`web/src/desk/voice/grammars/program.ts`, beside `desk.ts`, `editor.ts`,
  `workbench.ts`) whose one intent is `shape` with `requiresLLM: true`; the
  desk's wake or push-to-talk, with a Program window in front, puts the
  utterance into that window's shaping bar. The existing proposal strip
  (`web/src/desk/voice/ProposalStrip.tsx`) is not used: the diff rows are the
  proposal, and Apply is the confirm (Constitution IV.2, "voice arms; it does
  not fire").
- On a call and on the Line, a sentence about a Program is `program.shape`
  held for his spoken yes (§10).

### 4.3 The engine and the prompt contract

- **Capability:** `agent.plan` ("Plan a bounded agent task without
  authorizing effects", structured output, `inference_capabilities.py:1104`).
  It has no caller in the tree today (`inference_memory_policy.py:105`: "No
  caller in this tree yet"); the language service is its first. It resolves
  through the desk's assignment and its inheritance (`_resolve_for_capability`,
  `project_update_service.py:1583`), called the way Find the tasks calls its
  engine (`note_outcomes_service.py:108`: an `InvocationRequest` with a
  `ServiceContract`, the runner's receipt, no direct engine). A Program's
  `planner` line overrides the assignment for that Program only (the dreaming
  Program's cheap planner, §5.5).
- **Contract** `program.shape@1`, structured output (JSON schema in the
  request's `response_format`):

  ```
  in:  {sentence, text, frozen: [{where, field, reason}], vocabulary, grounding}
  out: {say: "one line in his words: what changes",
        blocks: [{where: "program" | "every step" | "at the end" | "step 5" | "step +" | "round Product",
                  action: "replace" | "insert_before:step 6" | "remove",
                  text: "<the whole new block, in the Program text>"}],
        question: null | "one question when the sentence cannot be read"}
  ```

- **The system prompt** carries: the grammar of §3.2 (about 60 lines), the
  rules ("change only what the sentence asks; never touch a frozen field;
  never remove a requirement; never lower a gate; keep his words in `>`
  lines; write a new step with `step +`"), the frozen list of this Program,
  and the **vocabulary**: the agents and engines this desk has (the Runs on
  list's own source), the templates, the requirement kinds, the shot cases
  of `applications.ts`, the people the Program names.
- **Grounding** (bounded, so the call fits a small engine; §5.4): the Program
  text (the whole of it; a 20-step Program is about 3k tokens); the repo map
  cut to the files the touched steps own and their neighbours (`git
  ls-files` under those folders, 200 paths at most); the Program's Note (the
  origin note, first 2k tokens); the Project's open actions (titles, 30 at
  most); the last 10 checkpoints. No transcript, no other Program.
- **Temperature** 0.2, **max tokens** 1500, **deadline** 30 s.
- A `question` answer (the sentence is ambiguous: "which step 6?") is drawn
  as one question row under the bar (the round question species, §9.4) and
  his answer is sent with the sentence as a second call. Never two
  questions.

### 4.4 The quick forms (no model)

A small closed grammar, read by rule before any model call, like the
requirement kind rule. Each form maps to text edits:

| He says | It does |
|---|---|
| "step 4 on Codex" / "put step 4 on pi" | `agent` line of step 4 |
| "move step 6 before step 5" / "step 6 first" | a move |
| "step 6 after 4" / "step 6 waits for 7" | `after` |
| "add a step <title> after 3" | `step +` with `after 3` |
| "require `<command>` on every step" / "on step 4" | `R+ check:` in the scope |
| "<Window> window at 393 has no clipped text on step 4" | `R+ shot:` |
| "make it YOLO" / "control normal" | `control` |
| "step 5 merges on my press" | `merge owner` |

The forms run in the hub (`holdspeak/programs/quick.py`), in under 50 ms,
offline, and are the whole of shaping when no engine is set.

### 4.5 The guard: a shaped change never lowers the bar

After the splice, every change row is classed. A row **lowers the bar** when
it: turns `check off`; moves `review` from `agent` or a person to `none`, or
from `standard` to `glance`; moves `merge` from `owner` to `level` or `none`;
marks a requirement `optional`; waives one; changes a requirement's kind to a
weaker proof (check, measure or shot to review; anything to nothing); removes
a `within` path limit; raises a spend limit; moves `control` up the ladder
(secure → normal → yolo).

- A row that lowers the bar is drawn with the ember lamp and the words
  "Lowers the bar". It is never applied by YOLO's auto-apply, at any level.
  It needs his own press on Apply, in the window. On a call it is read back
  and needs his yes, as a start does.
- A row the model wrote that touches a frozen field is refused (§3.5) and
  shown as refused; the model is never asked again for it.
- A row that is a core question (files outside the repository, a new egress
  such as `for` a person with `may call`, money) is drawn with its core
  reason and waits for his press at every level.
- The model never waives: a `R4 waived:` line from shaping is refused
  ("Only you waive"), even when his sentence says "waive R4". He presses
  Waive on the row, which asks for his line (PG-REQ §6).

### 4.6 YOLO applies and ledgers

At YOLO, after the preview, the allowed rows that do not lower the bar and
are not core apply at once. The ledger gets one decision row: "Shaped: put
step 4 on Codex; step 7 The loop watch added before step 6" with rule "YOLO
applies a shaped change", `overturnable` while every changed step is still
Planned or Ready, and `undo_json` = the inverse text (the `base` blocks).
**Overturn** applies the inverse through `text_apply`; if a step has started
since, the Overturn is withheld and its hover title says "Step 7 started".
At Secure and Normal nothing applies without Apply. A setting per Program
("Apply what I say", `programs.shape_applies`, default off below YOLO) is a
decision for the owner (§15.4).

### 4.7 Latency targets (not measured yet; §17)

| Path | Target p50 | Target p95 |
|---|---|---|
| `program.text` get (20 steps) | 40 ms | 100 ms |
| typed-text preview (parse, diff, check) | 60 ms | 150 ms |
| a quick form | 20 ms | 50 ms |
| shaping on the home qwen through the hub (8k in, 400 out) | 3 s | 8 s |
| shaping on a hosted Haiku-class engine | 1.5 s | 4 s |
| planning a Program of 10 steps (§5) | 15 s | 40 s |

While a shaping call runs, the bar shows the sentence with a breathing lamp
and "Reading the program"; the window stays usable; a second sentence
replaces the first (the first call is cancelled).

### 4.8 With no engine, or offline

- The Text view, typed edits, the preview and Apply work with no engine: the
  parser is pure.
- The quick forms work.
- A sentence that no quick form reads, with no engine set: the bar keeps the
  sentence and says "No engine is set for planning" with the library Buttons
  **Open Engines** and **Open text**. Nothing is guessed.
- An engine that fails or answers something the parser cannot read: "The
  engine's answer could not be read. The program is unchanged." (the Find
  the tasks words, `note_outcomes_service.py`), with **Try again**.

## 5. Planning inference: a goal becomes a draft

### 5.1 What it does

`program.draft` takes a Program in Drafting (with its goal, its template, its
repository) and proposes its whole text: steps with titles, briefs, owns,
after, agents, efforts, gates and requirements. The draft lands as diff rows
against the current text (all `+` rows for an empty Program), exactly like a
shaped change; Apply writes it through `text_apply`, which in Drafting calls
`plan(replace=True)` (`program_service.py:1576`), `require` and `update`. It
never starts the Program.

### 5.2 Grounding

- the goal (his paragraphs) and the origin Note when `from note:…`;
- the template's shape: its step gates, its reviewer, its level, its default
  requirements (`program_templates.TEMPLATES`, `holdspeak/program_templates.py:41`);
  the planner may not change what the template set, only add;
- the repo map: top folders with file counts, the files named in the goal,
  the repository's CLAUDE.md or AGENTS.md headings (the handoff brief already
  reads them, PG19);
- the last 10 merged PR titles of the repository (through the GitHub
  connection when it is set, else `git log --merges -10 --format=%s`), so
  the plan follows how the repository cuts its work;
- the Project's open actions (titles), and for a linked dw story its
  acceptance lines (§8.3);
- the answers of the interview rounds so far (§6.2);
- the context budget of the engine that will build (§5.4).

### 5.3 Where it starts

- **New program** with a goal: the toolbar shows **Plan it** (primary) while
  the Program has no steps.
- **Run as a program** on a Note: the new Program opens and its draft is
  planned at once (the rows rise in as they come); today the verb makes a
  Program with no steps (`fromNote.ts:14`).
- **Over MCP**: `program.draft` from an orchestrating agent writes a
  proposal row ("The orchestrator proposes a plan: 8 steps, 11
  requirements") at Secure and Normal, and applies at YOLO, as `step_change`
  does.
- **On a call**: "make a program from my note about the loop budget" is
  `program.create` + `program.draft`, held for his yes (§10).

### 5.4 Step sizing for small-context engines (the 64k rule)

The home engine runs pi with a context window of its own: pi reads it from
the deployment revision (`context_window=int(revision.context_ceiling or 0)
or DEFAULT_CONTEXT_WINDOW`, `holdspeak/delivery/pi_launch.py:128`; the
default is 32,768, `:58`). A step that does not fit in that window fails
slowly: the agent reads half the files, forgets the brief, and the check
round burns the night.

**Fields** (additive): `programs.context_budget` (INTEGER tokens, NULL: the
budget of the first agent's engine) and `program_steps.context_budget`
(NULL: the Program's). The text says `budget 64k`. A budget is only read for
an agent whose engine has a window (pi on an engine); Claude Code and Codex
have no budget unless the text names one.

**The estimate** (by rule, no model; `holdspeak/programs/sizing.py`):

```
estimate(step) = brief tokens (the composed brief, program_brief.compose)
               + Σ owns files' bytes / 4  (a folder counts its files, at most 400)
               + the harness's fixed cost (pi's system prompt and tool list, measured once per harness, §17)
fits(step)     = estimate(step) ≤ 0.5 × budget
```

Half the window is left for the agent's own reads, edits and the check's log
tail. The 0.5 is a constant with a name (`WORKING_SHARE`), not a setting.

**At planning**, when the building agent has a budget, the planner is told:
one concern per step, at most three owned files, a brief under 400 words,
`effort low` or `medium` only, and the repo map pre-cut to the step's owned
folders. The draft's rows show each step's estimate as a lamp ("# 18k of
32k").

**One denominator** (reconciled with the journeys, #1667): every size word
names the working share, `WORKING_SHARE × budget`, never the whole budget.
With `budget 64k` a step's lamp reads "# 18k of 32k" and a step that does
not fit reads "Too big for qwen · 41k of 32k". The same number is the fit
rule's bound, so a lamp at or under its denominator always fits.

**At dispatch**, the runner refuses to hand a step that does not fit
(`program_runner._dispatch`, before the hand): the step is held with the
word **Too big for qwen · 41k of 32k**, and the rule
`program_rules.decide(level, "step_too_big", facts)` decides:

| Secure | Normal | YOLO |
|---|---|---|
| Your turn: **Split** / **Run anyway** | Your turn: Split / Run anyway | the planner splits it (one `agent.plan` call with the step and its owns), the split is applied, one line under Decided for you (Overturn while the parts are Planned) |

A split is a shaped change on the one step: the step is replaced by two to
four `step +` blocks that together own what it owned, each with its own
brief, and the step after it waits for the last part. The split keeps the
step's requirements on every part when they are every-step copies, and on
the last part when they are its own. **Run anyway** hands it as it is and
writes the estimate into the checkpoint.

The text grammar gains `budget` on the Program and the step for this; the
estimate is only ever a lamp.

### 5.5 The dreaming shape (nightly, on the idle home engine)

The owner's example: a nightly Program that uses the idle GPU with pi on
very small tasks, planned by a cheap planner. It is not a new engine; it is
a template, **Dreaming**, plus two Program lines (`night`, `within`) and one
source of steps.

```
# program text 1
program Dreaming · HoldSpeak
  in HoldSpeak · main · project HoldSpeak
  template dreaming
  control yolo
  agent pi on qwen3.8-27b
  planner qwen3.8-27b
  reviewer Claude Code at glance
  budget 64k
  when idle
  night 23:30–07:00 · at most 8 steps
  within web/src/desk/, docs/, tests/unit/

every step
  R1 review: The change does only what its brief says.
  R2 check: `uv run python scripts/ux_canon_scan.py` is green.
```

**What it does.**

1. An Automation (PG14, "Run a program") starts it at 23:30 when the night
   line says so. Each night is one Program run with its own steps; the
   Program record is reused (its Done reopens as Running at 23:30), so the
   Note keeps one history.
2. **The backlog** is read by rule, never invented: the Door tasks filed to
   the Project with the word "dream" or made by a Later finding; the open
   Project actions marked small; the UX canon ratchet's residues (the scanner
   names each raw `<button>` by file, `tests/ux_canon_ceiling.json`); the
   failing tests in the last main run's report, when the watcher writes one.
   Each item becomes one tiny step of one file (§5.4), planned by the
   Program's `planner` (one `agent.plan` call per item, through the same
   contract as shaping).
3. Steps run one at a time, only while the engine is idle (`prefer_idle`,
   `program_runner.engine_idle`): his dictation or Ask always takes the slot
   (as built).
4. Each step has the check and the two every-step requirements; the
   reviewer reads at `glance` depth.
5. At 07:00, or after `at most` steps, or after two red steps in a row, the
   night stops: Ready steps go back to the backlog, a Working step finishes
   its turn and parks with "the night ended".
6. **The morning digest** is a section of the handover note, "Since last
   night", on top: merged (PR numbers), parked (with the reason), held (too
   big, no idle time), and what waits on him. Today's Since morning line says
   "Dreaming: 5 merged, 1 waits on you".

**What it may do without him** (the YOLO rows of the 2026-10-28 §6 table and
PG-REQ §6, unchanged): start, re-brief, run the check and the reviewer, open
the PR, merge on green and PASS, fix a SHOULD in the open round, skip a NOTE,
type a routine answer, allow a gate call by its rules, run round 3, try one
smaller brief and then park, add a step from the backlog (the "adding a step
the plan lacked" row; YOLO adds and says so), split a step that is too big
(§5.4).

**What it may not do** (the core questions, at every level, plus two lines of
this shape): touch a file outside `within` (the core question "files outside
what its steps own" with `within` as the bound); spend money (a hosted
planner with no `spend up to` is the money core question before the first
call; the LAN planner costs nothing); egress beyond its own PRs; change
Settings; delete a test; a migration; lower a requirement; run past `night`
or past `at most`. A Your word requirement holds its step's merge to the
morning (PG-REQ decision 1).

Note: merges at night on HoldSpeak's own main redeploy his desk (the fast
cycle). The default `at most 8 steps` and the stop after two red steps keep a
bad night small; whether dreaming may merge to HoldSpeak's own main at all is
a decision for him (§15.6).

## 6. The definition phase as a stance

### 6.1 Drafting is a document he and the engine co-write

In Drafting, the Program window has three ways in, all to the same text:
the board's gadgets (as built), the Text view, and the shaping bar. The
planning draft, the interview rounds and his own edits all arrive as diff
rows; nothing changes under him without a row.

### 6.2 Interview rounds

From a couple of pasted paragraphs, the engine asks the few questions that
change the plan, in named rounds. The default rounds, his names:
**Architecture**, **Product**, **Stack**, **Verification**, **Delivery**. A
Program may drop or add rounds in its text (`round Security · open`).

**The engine contract** (`holdspeak/programs/rounds.py`):

- A round is `{name, state, questions: [{id, text, answer, answered_by, at,
  became: [change ids]}]}` in `programs.rounds_json` (one additive column;
  no table). States: `open`, `asking`, `done`, `skipped`.
- **One question at a time.** `program.round_next(round)` makes one
  `agent.plan` call (contract `program.round@1`): in, the Program text, the
  round's name and its charter line (below), the answers so far; out,
  `{question, why, options?: [up to 3 short answers], done: bool}`. `done:
  true` means the engine has no question left that would change the plan in
  this round.
- **He answers by voice or text** in the question row's StringGadget (mic),
  or presses one of the offered answers, or **Skip question**.
- **Each answer becomes text.** The answer goes to one shaping call (§4) with
  the sentence "In the <round> round, to '<question>', the owner said
  '<answer>'": the diff rows it proposes (a requirement, a gate, a step's
  detail, a new step) land under the question; he presses Apply, as with any
  shaped change. The question records the change ids it became.
- **A round gate is a press**: **Done with Architecture**. It is withheld
  while a question waits; Skip round is always there. Start is not blocked
  by an open round (rounds help, they do not gate), unless the Program says
  `rounds before start` (§15.5).
- **Re-enterable while running.** A done round can be opened again from its
  row ("Ask more"); a question asked while steps run proposes changes that
  obey the frozen table, like any shaped change.

The round charters (one line each, given to the engine; the names are his):

| Round | The engine asks about | Typical result |
|---|---|---|
| Architecture | the boundaries, the data, what must not change, where the risk is | `within`, step `owns`, a Review requirement ("No route takes a lock on the loop") |
| Product | who it is for, what he will see, what "done" looks like to that person | `for`, Your word and Shot requirements |
| Stack | the libraries, the versions, the commands, what the repository already has | `check`, step `agent`, `budget` |
| Verification | how each claim is proven: which tests, which windows, which numbers | Check, Shot, Measure requirements, `review … at standard` |
| Delivery | the order, the merge rule, the level, the dw story, the night | `after`, `merge`, `control`, `delivery dw`, `night` |

In the text, rounds are blocks with their state and their questions; the
answers are kept (they are the reason for a requirement), and each answer
line's lamp names what it became:

```
round Architecture · done
  ? Does the cache live in the hub or in the client?
  = In the hub; the client stays as it is.          # → R11, step 3 owns
  ? Can the event log lose rows on a crash?
  = No.                                             # → R12 measure
round Product · asking
  ? Who sees the stall first?
round Stack · open
```

`?` lines are the engine's (never editable: a changed `?` line is refused,
"The engine asked it"); `=` lines are his and editable while the round is
not done.

### 6.3 Verification kinds: the four, plus Measure

The four kinds of PG-REQ stay (check, review, shot, word). The rounds show
two needs the four do not meet:

- **Measure** (new kind, `measure`): "The People routes answer under 100
  ms". A command that prints a number, and a bound. Judged at CHECK with the
  check kinds, through the requirement log form
  (`program_verifier.verify_requirement_log`) plus one rule: the last line
  that matches `METRIC … NUMBER UNIT` gives the value, and the value meets
  the bound. Evidence: "p95 84 ms (bound < 100 ms)". Lines: `run`, `bound p95
  < 100 ms`. The kind is never guessed; he or the Verification round picks
  it. (A Check with `expect` cannot compare numbers; a regex can only match
  them.)
- **A walk** is not a new kind: it is Your word with `walk` lines, the steps
  he will do ("Open Programs at 393", "Press Plan it", "See 6 steps"). His
  Your turn row shows the lines; Met and Unmet stay the only verbs. A walk
  can name the shot it follows, so the evidence of a Shot sits beside it.

### 6.4 Definition while running

Everything of PG-REQ §8 holds: add requirements to a running step, amend a
started brief, insert and move Planned steps, change what the state leaves
open. The text and the shaping bar are two more ways to do exactly those
things; the frozen table is the same table.

### 6.5 The ladder: from two paragraphs to Done

The stations, and where he can enter or leave at each. The journeys
document (`PROGRAM-JOURNEYS-2026-10-31.md`) walks each with times.

| Station | What exists | He enters here by | He may leave it to | The board says |
|---|---|---|---|---|
| **1 · Dropped** | a goal (two paragraphs, a Note, a sentence) | New program, Run as a program, a call, an Automation | Plan it (2), or write steps himself (4) | Drafting · no steps |
| **2 · Drafted** | a planning draft as diff rows | Plan it, `program.draft` | Apply (3 or 4), Not this (1) | Drafting · draft of 8 steps |
| **3 · Interviewed** | rounds open, one question at a time | Apply the draft; or Ask me first | Done with each round, or Skip round (4) | Drafting · Architecture: 2 of ~4 |
| **4 · Refined** | steps with briefs, owns, gates, requirements, sized | Apply; his own edits | Start (5) | Drafting · 8 steps · 14 requirements |
| **5 · Running** | steps hand, work, check | Start; the night line; a call's yes | Park, shape (stays in 5), Your turn | Running |
| **6 · Verified** | each step's check, review and requirements judged | the engine, per step | Send back, Waive (stays in 6) | n of m met |
| **7 · Proven** | the PRs merged; the end check; evidence; the dw story | the engine; his Your word | Close (8) | Done? · end check |
| **8 · Done** | the note's Done line, the Result, the dw record | the engine at Normal and YOLO; his Close at Secure | Reopen (a dreaming night; 5) | Done · 9 of 9 met |

Hands-off goes 1 → 2 → 4 → 5 → 8 with no press at YOLO (Plan it applies at
YOLO and the template's level starts it when an Automation made it).
Hands-on goes 1 → 2 → 3 → 4 → 5, with presses where he wants them. He can
step in at any station and the next station still works.

## 7. The SDK

### 7.1 The layers

| Layer | What | Where |
|---|---|---|
| **The text** | the format of §3, its spec and its test corpus | `docs/program-text.md` (user doc, ASD-STE100); `tests/fixtures/program_text/*.program` (each fixture parses, prints back, diffs empty) |
| **The language module** | pure Python: `parse`, `print_text`, `diff`, `classify` (the guard), `quick` (the quick forms), `sizing` | `holdspeak/programs/` (new package: `text.py`, `diff.py`, `quick.py`, `sizing.py`, `rounds.py`) |
| **The service** | `ProgramTextService`: `text`, `text_apply`, `shape`, `draft`, `round_next`, `round_answer`, `round_done` on top of `ProgramService` | `holdspeak/services/program_text_service.py` |
| **MCP** | `program.text`, `program.text_apply`, `program.shape`, `program.draft`, `program.round` | `holdspeak/mcp/families/program.py` |
| **REST** | §12 | `holdspeak/web/routes/programs.py` |
| **Python client** | `holdspeak.programs.client.Programs(hub, token)`: the REST calls; and the language module itself, offline | importable from the installed package |
| **CLI** | `holdspeak program text <id>`, `holdspeak program apply <id> <file> [--preview]`, `holdspeak program shape <id> "<sentence>"`, `holdspeak program draft <id>` | `holdspeak/commands/program.py` (beside `commands/gate.py`) |
| **TS client** | `web/src/desk/programs/text.ts`: `getText`, `previewText`, `applyText`, `shape`, `draft`, the round calls; a tokenizer for the Text view's colours only | the desk |
| **The skill** | "Read the text first. Write changes as text. Never edit a frozen field. Never write `waived`." | `agent/skills/holdspeak-programs/SKILL.md` |

One parser. The desk never parses the text for meaning; it sends the text to
the hub's preview (debounced 300 ms) and draws the rows that come back. The
TS tokenizer only colours keywords, `>` lines, `#` lamps and `R n` ids.

### 7.2 What an orchestrating agent can do with it

An agent (Claude Code at his keyboard, Codex as Astra, pi, a step's own
agent for its own step) reads a Program in one call as about 3k tokens of
text instead of a large JSON (`program.get` carries every checkpoint and
every requirement's wire). It writes a change as text and gets the change
rows back; at Secure and Normal its change is one proposal row ("The
orchestrator changes the program: 3 changes" · **Apply** · **Skip**, the
existing `step_change` proposal kind with the whole diff in `undo_json`), at
YOLO it applies with a Decided for you line. It can `program.draft` a
Program it made and `program.round` to ask the owner's questions on his
desk instead of in chat. It cannot waive, decide, or change a frozen field;
it gets the same refusals he does.

### 7.3 The stability promise

- The text format, version 1, is additive: a new keyword never changes what
  an old text means. A hub reads every version 1 text it ever printed.
- The MCP tool names and argument names of §12 do not change; new arguments
  are optional.
- Refusal codes (§3.9) do not change meaning.
- The diff row shape (`op`, `where`, `before`, `after`, `say`, `verdict`,
  `reason`) is stable.

### 7.4 Versioning

The printer writes `# program text 1`. A future breaking change (a keyword
that means something else) is version 2; the hub then reads 1 and 2 and
prints 2, and `program.text` takes `version: 1` for an old client. Within
version 1, an unknown keyword is a refusal by name, never dropped.

## 8. Delivery Workbench at major points only

The owner: "only on major points … it is known to be blowing up in verbosity
the more we do it on a granular level". So:

### 8.1 The mapping

- **One Program = one dw story** (or, with `delivery dw <project>/<phase>
  milestone`, one phase). Never a story per step.
- **Opt-in per Program**: the `delivery dw <project>/<phase>[/<story>]` line.
  No line, no dw. The line is refused in a repository with no rails
  (`.githooks/dw` missing): "This repository has no Delivery Workbench."
- **HoldSpeak's own repository** keeps it off: its `pm/roadmap/` is history by
  the owner's ruling (CLAUDE.md, the fast cycle). The integration is for his
  other repositories that run the rails.

### 8.2 The two points

1. **Link** (at create or by editing the line): the hub reads `dw context`
   for the story (read only, the mission-control bridge's own runner and
   timeout, `holdspeak/missioncontrol_bridge.py`), keeps the story ref in the
   Program's facts, and offers the story's acceptance lines as proposed
   requirements at planning (§8.3). No write.
2. **Done** (after the end check, before `program_done`): one write, as one
   PR, never in his working tree. The engine makes a scratch worktree at the
   base head (the end check's `hs-program-<id>-end`, PG-REQ §6), runs `dw
   story create` when the story does not exist, `dw story evidence
   --from-file <evidence.md>` and `dw story status <…> done` there, commits
   on `program/<slug>/delivery`, and opens one PR "Delivery: <title> done",
   merged by the Program's merge rule. For a milestone, `dw phase close` with
   the summary.

### 8.3 What the evidence is

The evidence file is the Program's Done, nothing more:

```
## Program: The hub stops stalling — Done 2026-11-02
- PRs: #1585, #1587, #1591, #1593, #1597, #1598 (merged; merge commits listed)
- Requirements: 18 of 18 met (1 waived: R8 "measured by hand: 0.4 ms")
  - R1 word · I used the desk for a morning with no stall · the owner, 09:12
  - R12 measure · The event log loses no row on a crash · 0 lost of 10,000
  - …
- Decided for you: 7 (merges 5, Later 2); overturned 0
- Handover note: program-<id>
```

A story's acceptance lines, when linked, came in as requirements at
planning; their Met lines are the evidence of those lines.

### 8.4 What dw never sees

Steps, step titles beyond the PR titles, briefs, amendments, checkpoints,
findings, review text, handoff briefs, transcripts, worktree paths, the
interview's questions and answers, a parked or failed Program (a Park writes
nothing; the story stays as it was).

## 9. The faces

Kit only (UX-CANON §B), no modal, no prose, every verb the library `Button`,
no counter of zero. One window (`pullout:program:<id>`), two views, one
truth. The Programs list is unchanged beyond what #1665 shipped.

### 9.1 The Text view beside the board

- The toolbar gains a two-token `FilterTokens` at its right, **Board ·
  Text**, and at 1440 a third, **Both** (the default when the window is
  wider than 1100 px): the board on the left, the text on the right, in one
  scroll each.
- The **text pane** is a new kit species, `TextPane` (§11): a mono editor
  with a gutter. Each line has a **line lamp** in the gutter: the state dot
  of the step or requirement the line belongs to (the same tones as the
  board), so the text is never a dead file. Keywords in ink, `>` lines in
  body sans (his words read as words), `#` lamps in faint, `R n` ids as the
  kind Token's tint.
- Select a step row on the board and the text scrolls to its block, and the
  other way round (one selection).
- Typing in the text: after a 300 ms pause the hub's preview comes back and
  the changed lines get a gutter mark (`~`, `+`, `−`); the diff rows appear
  in the **change well** under the toolbar (the same well as shaping, §9.2)
  with **Apply** and **Revert**. A refused line has a fail lamp and its
  reason as the hover title and as the row's words.
- At 393 the views are tokens (Board · Text), one at a time; the text pane
  is 14 px mono, wrapped, with the gutter lamps.

### 9.2 The shaping bar and the change well

- **The shaping bar**: one row under the toolbar, 36 px: a `StringGadget`
  "Change the program" with its mic, and the library `Button` **Shape**
  (Return sends). In Drafting with no steps it reads "Describe the work" and
  the verb is **Plan it**.
- **The change well** (only when there are rows): an inset under the bar.
  Its head is the `say` line ("Put step 4 on Codex; add The loop watch before
  step 6") and the engine's name and time in muted words ("qwen3.8-27b · 2.8
  s"). Then one **diff row** per change (§11, the new species): the op glyph
  (`+`, `~`, `−`, `↕`), the where (`step 7`, `R+`), before → after in mono
  where it is a value, the verdict as a `DotWord` (Allowed, Lowers the bar,
  Refused, Changed since you read it). The well's verbs: **Apply** (primary;
  "Apply 5" when one row is refused: it applies `allowed_text`), **Not
  this**, and on a lowers-the-bar row its own **Apply this** (his press per
  row).
- When the well is applied, the rows **land**: each `+` row's step slides
  into its place on the board (the compositor's motion, 180 ms, none under
  reduced motion) and the well closes.

### 9.3 The planning draft face

- In Drafting with a goal and no steps: the goal `PadGadget` (as built), the
  shaping bar reading "Describe the work", and **Plan it**.
- While planning: the board shows ghost rows rising in as the draft streams
  (the rows are diff rows of op `+`), the status bar says "Planning ·
  qwen3.8-27b". Each ghost row has its estimate lamp when a budget applies
  ("18k of 64k").
- The draft done: the change well holds "8 steps · 11 requirements · 3
  rounds to ask" with **Apply**, **Ask me first** (opens the first round,
  §9.4) and **Not this**.

### 9.4 The interview round face (recommended direction R-A)

Three directions are on the canvas; the recommendation:

- **R-A · One question on the board (recommended).** The rounds are a strip
  of tokens over the board: **Architecture · Product · Stack · Verification
  · Delivery**, each with its state dot (open hollow, asking breathing, done
  ok, skipped struck through). Under the strip, **one question row**: the
  question in 15/600 ink, the `why` in muted words under it, up to three
  offered answers as plated Buttons, a `StringGadget` with its mic for his
  own answer, **Skip question**. When he answers, the question row folds to
  one line ("? Cache in the hub · = In the hub") and its diff rows appear
  under it in the change well; Apply; the next question rises in. The round's
  verb at the strip's right: **Done with Architecture** (withheld while a
  question waits). Nothing else moves.
- **R-B · The interview as a column.** A third column beside board and text
  with every question of the round as a list. Faster to scan, but a list of
  questions reads as a form, and the owner asked for one at a time, never a
  form.
- **R-C · Questions in the text.** The questions appear as `?` lines in the
  Text view and he types `=` lines. True to the text, but it asks him to be in
  the Text view to be interviewed, and the voice path is weak.

**Why R-A.** One question at a time on the board is the smoothest path: his
eye stays on the plan, the question changes the plan in front of him, and the
mic is where the answer goes. R-C stays true anyway, because the round blocks
print in the text (§6.2) for anyone who prefers the text.

### 9.5 The definition-phase affordances

- On a selected step's fold (PG-REQ's FilterTokens strip), a **Sizing**
  token appears when a budget applies: the estimate, the share, **Split**.
- The Add requirement row gains **Measure** in its kind CycleGadget and the
  bound field (a `StringGadget` "p95 < 100 ms").
- A Your word requirement with walk lines shows the lines in its well under
  the row.

### 9.6 At 393

Board · Text tokens; the shaping bar full width with its 44 px mic and
Shape; the change well as rows two lines high (`+ step 7 The loop watch` /
`after 4 · pi · low · Allowed`), plated verbs 44 × 44; the round strip
scrolls sideways; the question row stacks (question, offered answers in a
column, the field).

### 9.7 Delight (four moments, UX-CANON D)

1. **The diff lands.** Applied rows travel into the board and the changed
   cells breathe once (the 2.4 s ring, once).
2. **A step is born from a sentence.** A `step +` row draws its six station
   dots one after the other, left to right, as it lands (60 ms each).
3. **A round closes.** Its token turns ok, and the count of what it became
   ("4 changes") stays on the token for the session.
4. **Done.** The status bar's Done word ("Done · 18 of 18 met") and, for a
   dreaming night, the morning digest's first line in the Note with its
   merged PR numbers in PR green.

## 10. The ecosystem

- **Project.** A Program's text names its project (`in … · project`); the
  Room's Programs fold (as built) gains **Open text**. The steward's update
  paragraph is unchanged.
- **Person.** `for Alice` and `review Alice` in the text are the existing
  person fields; the person's room line is unchanged.
- **Note.** "Run as a program" plans at once (§5.3); the handover note gains
  "Since last night" for a dreaming Program and the round answers under
  "Why" (one line per answer that became a requirement).
- **The Door and Needs you.** Size and round asks are Your turn rows
  (`step_too_big`: Split / Run anyway; `round_question` is not a Needs you
  row: a question waits in the window, never on his desk, unless the Program
  says `rounds before start`).
- **Control.** The ladder decides shaping's auto-apply (§4.6) and the
  splits (§5.4); nothing new.
- **The Phone and the Line.** PG15's "start the overnight program" stays.
  New, in the call palette (`holdspeak/mcp/palettes.py:206`):
  `program.shape` held for his spoken yes (`CALL_HELD_PROGRAM`), and
  `program.text` read as speech. On a call the diff is read back from the
  rows' `say` sentences: "I put step 4 on Codex, and I add a step, The loop
  watch, before step 6. One change lowers the bar: step 5 merges without your
  press. Say yes to apply the first two." A lowers-the-bar row is read
  separately and needs its own yes.
- **What can be spoken of a Program's text.** Its state (`spoken_state`, as
  built, `program_service.py:3514`), one step block ("Step 4, People routes,
  on Codex, after 1 and 2, working for 12 minutes, one requirement not yet
  judged"), the requirements by state ("2 unmet: R4, R6"), the next round
  question ("The Product round asks: who sees the stall first?"; his spoken
  answer is a `round_answer`, held for his yes when it changes the plan).
  Never the briefs read aloud whole; "read me the brief of step 4" reads the
  first 40 words.
- **Calls (the voice agent on the home server).** Same palette, same holds.
- **Automations.** "Run a program" (PG14) gains the Dreaming template and the
  night line.

## 11. What the component library and the engine need

These ship inside this program of work, each into the kit first, documented
in `web/src/desk/surface/contract.md`, then used (UX-CANON §B, Tenet 5).

**Kit (web):**

| Piece | What | Why it is new |
|---|---|---|
| `DiffRow` (species) | one change row: op glyph · where · before → after (mono values) · verdict `DotWord` · per-row verbs; 32 px; two lines at 393 | no diff species exists: the Terminals workspace shows diffs as a plain `<pre>` (`web/src/desk/terminals/WorkspaceView.tsx:454`) and `SurfaceCode` is a `<pre>` (`web/src/desk/surface/Surface.tsx:471`) |
| `ChangeWell` (pattern) | the inset that holds a `say` head, `DiffRow`s and the Apply / Not this verbs; the landing motion | the shaping bar, the text, the draft and the rounds share it |
| `TextPane` (species) | a mono editor with a gutter of line lamps, keyword colouring from a token list, line marks `~ + −`, a scroll-to-line API, the mic as a gadget; the kit's second text well after `PadGadget` | `PadGadget` is "the kit's ONLY textarea face" (`gadgets.tsx:367`): it has no gutter, no per-line state |
| `QuestionRow` (pattern) | the round question: question, why, up to three plated answers, a `StringGadget` with mic, Skip | a question that changes a plan has no species (Ask's composer is a conversation) |
| `RoundStrip` | `FilterTokens` with a state dot per token and a trailing verb | a FilterTokens variant, not a new species |

**Engine (hub):** the `holdspeak/programs/` package (§7.1);
`ProgramTextService`; the contracts `program.shape@1`, `program.round@1`,
`program.draft@1` on `agent.plan`; the `measure` kind in
`program_requirements.KINDS` and its verifier rule; `step_too_big` and the
round kinds in `program_rules.KINDS`; the dispatcher's size check; the
Dreaming template and its backlog reader; the night stop in the runner; the
dw Done writer.

## 12. The contract for the lanes

### Tables (minimal, additive; SCHEMA_VERSION 89)

```
ALTER TABLE programs ADD COLUMN context_budget INTEGER;        -- NULL: the first agent's engine window
ALTER TABLE programs ADD COLUMN planner_engine TEXT;           -- NULL: the desk's agent.plan assignment
ALTER TABLE programs ADD COLUMN rounds_json TEXT NOT NULL DEFAULT '[]';
ALTER TABLE programs ADD COLUMN night_json TEXT;               -- {from, to, at_most}
ALTER TABLE programs ADD COLUMN within_json TEXT NOT NULL DEFAULT '[]';
ALTER TABLE programs ADD COLUMN delivery_ref TEXT;             -- "dw:<project>/<phase>[/<story>]"
ALTER TABLE programs ADD COLUMN shape_applies INTEGER NOT NULL DEFAULT 0;
ALTER TABLE program_steps ADD COLUMN context_budget INTEGER;
```

No new table. The Measure kind is a value of `program_requirements.kind`
with `spec_json` `{command, metric, op, bound, unit}`; walk lines are
`spec_json.walk` on a word requirement. The schema snapshot is regenerated.

### REST (`holdspeak/web/routes/programs.py`, every handler through `run_in_threadpool`)

```
GET  /api/programs/{id}/text                    {text, revision, version}
POST /api/programs/{id}/text                    {base, text, preview}   → {changes, patch, allowed_text, applied?, program?}
POST /api/programs/{id}/shape                   {sentence, base?, preview: true}  → {say, changes, question?, engine, seconds}
POST /api/programs/{id}/draft                   {preview: true}  → {say, changes, rounds, engine, seconds}
POST /api/programs/{id}/rounds/{name}/next      → {question?, done}
POST /api/programs/{id}/rounds/{name}/answer    {question_id, answer | option | skip}  → {changes}
POST /api/programs/{id}/rounds/{name}/decide    {choice: done | skip | reopen}
POST /api/programs/{id}/steps/{sid}/split       {preview}  → {changes}
```

Each new route gets its residual-set entry, an aware clock (`local_now`), the
api-surface regen.

### MCP (`program` family; palette CONDUCTOR; the call palette as §10)

| Tool | Does | Who |
|---|---|---|
| `program.text` | the text, its revision and version; `name` as `program.get` | anyone |
| `program.text_apply` | `{program_id, base, text, preview}` | owner at once; an orchestrating agent by the level (`step_change`) |
| `program.shape` | `{program_id, sentence, preview}`; applying is his press or the level (§4.6) | owner; an orchestrating agent (preview only, then `text_apply`) |
| `program.draft` | plan the whole Program (Drafting only) | owner; the agent that made it |
| `program.round` | `{program_id, round, action: next | answer | done | skip | reopen, answer?}` | owner; an orchestrating agent may `next` and pass his chat answer only as a proposal |

`tool_authority.py`: `program.text` READ, `program.text_apply`, `program.shape`,
`program.draft`, `program.round` WORK; `decide` and `overturn` stay
AUTHORITY.

### The wire

On a Program (`_wire`): `text_revision` (= `revision`), `rounds: [{name,
state, asked, answered, became}]`, `context_budget`, `planner: {engine,
label} | null`, `night: {from, to, at_most} | null`, `delivery: {kind:
"dw", ref, linked: bool} | null`. On a step: `estimate: {tokens, budget,
fits} | null`. Your turn kinds: `step_too_big` (split, run_anyway), and for
`rounds before start` only, `round_question`.

### Frame

`program_changed` gains `text: true` when the definition changed (the Text
view refreshes its base only then; lamps refresh on every frame);
`desk_changed("program", id, verb)` gains `text`, `shape`, `draft`, `round`,
`split`.

### Fixtures (recorded from the rig, `scripts/record_program_fixtures.py`)

`program.text.json` (each of the five examples of §3.7 as a Program and its
text), `program.text.preview.json` (allowed, refused, conflict, lowers rows),
`program.shape.json` (a fake planner's block answer, spliced), `program.draft.json`,
`program.rounds.json` (a round asking, one done, one skipped),
`program.sizing.json` (a too-big step and its split). The fake planner is a
recorded `agent.plan` answer replayed through the runner's test seam, never
a typed double (the test diet).

## 13. The slices

One branch per lane group, in build order; each slice is a PR in the fast
cycle. A short path: `hs/` is `holdspeak/`, `desk/` is `web/src/desk/`.

| Slice | Lane | What | Done when (tier) |
|---|---|---|---|
| **LANG1** | HUB | `hs/programs/text.py` (parse, print), `diff.py`, `ProgramTextService.text` and `text_apply` (preview and apply through the existing verbs), the refusals, `GET`/`POST /api/programs/{id}/text`, `program.text` + `program.text_apply` | the round-trip rule holds over every fixture and 500 generated Programs; each frozen field refuses with its reason; a conflict is named; an apply writes one checkpoint and one frame (T1 `tests/unit/test_program_text.py`, `tests/integration/test_desk_programs.py`) |
| **LANG2** | FACES | the Text view (Board · Text · Both), a first `TextPane` in the kit (gutter lamps, keyword colours), the change well with `DiffRow`, Apply / Revert | from `program.text.json` and `program.text.preview.json`: an edit shows its rows, Apply lands them, a refused row shows its reason (T2 `programs.app.test.tsx`); the sweep's `program` case at 1440 and 393 stays green (T3) |
| | | **LANG1 + LANG2 are the first slice on his desk, within a day.** | |
| LANG3 | HUB | the quick forms (`quick.py`), `program.shape` with the `agent.plan` contract, the splice, the guard (`classify`), YOLO auto-apply and Overturn | each quick form maps to its rows; a recorded planner answer becomes rows; a lowers-the-bar row never auto-applies at YOLO; Overturn applies the inverse (T1) |
| LANG4 | FACES | the shaping bar (typed), the say head, the lowers-the-bar row's own Apply, the landing motion | a typed sentence presses through to the rendered rows and the applied board (T2) |
| LANG5 | FACES + HUB | voice: the `program` voice grammar, the bar's mic as the window's one mic authority; the call palette's `program.shape` held for his yes and the spoken diff | a recorded utterance fills the bar and shapes (T2); the Calls rig applies a shape after a spoken yes and refuses a lowers-the-bar row without its own yes (T1) |
| LANG6 | HUB | `program.draft` (grounding, the template's shape), Run as a program plans at once | a recorded draft becomes rows; Apply in Drafting plans, requires and updates (T1) |
| LANG7 | FACES | the planning draft face (ghost rows, Plan it, Ask me first) | from `program.draft.json` (T2) |
| LANG8 | HUB | sizing: `budget`, the estimate, the dispatcher's refusal, `step_too_big` by level, the split | a 41k step on a 32k engine is held; YOLO splits it; Secure asks (T1 `test_program_sizing.py`) |
| LANG9 | HUB | rounds: `rounds.py`, `program.round`, the round routes, answers become shaped changes, the round gate | a round asks, takes an answer, proposes rows, closes on Done (T1) |
| LANG10 | FACES | the round strip and the question row (direction R-A), the Sizing token | from `program.rounds.json` and `program.sizing.json`; an answer presses through to its rows (T2) |
| LANG11 | HUB | the Measure kind and its verifier rule; walk lines on Your word | a measure log under the bound is Met with its value; over is a red round (T1 `test_program_verifier.py`) |
| LANG12 | HUB | Dreaming: the template, `night`, `within`, the backlog reader, the night stop, the morning digest in the note | the rig runs a night of three tiny steps from a recorded backlog, stops at `at most`, writes "Since last night" (T1 rig) |
| LANG13 | HUB | Delivery Workbench: the link (read `dw context`), the Done writer as one PR | in a scratch repository with the rails, Done makes one PR whose roadmap diff is one story's evidence and status (T1, a temp git repo) |
| LANG14 | HUB | the SDK: `holdspeak.programs.client`, `holdspeak program …` CLI | the CLI's `text`, `apply --preview`, `shape` against a rig hub (T1) |
| LANG15 | DOCS | `docs/program-text.md` (the format, ASD-STE100), `docs/programs.md` (Text, Shape, Plan it, rounds, sizing, Dreaming, dw), the skill, `RECIPE.md` "PG-LANG", TRACKER, UX-CANON "Shipped", `contract.md` for the kit pieces, the generated docs | `scripts/gen_docs.sh` clean |

Sequence: LANG1 → LANG2 (the first slice on his desk); then LANG3/LANG4
(typed shaping), LANG5 (voice), then LANG6–LANG10 (planning, sizing,
rounds) in parallel by file ownership, then LANG11–LANG14; LANG15 rides
each slice's docs and closes the set.

## 13b. Slices from the journeys (PG-JOURNEYS build)

`PROGRAM-JOURNEYS-2026-10-31.md` walks eight use cases on this system; its
"What the journeys demand" table marks each need Exists, In PG-LANG (with the
LANG slice) or New. The New ones are these slices, in build order after
LANG15, each a PR in the fast cycle. The interview face of the journeys
(direction A) is this design's R-A, so it is LANG10; only the goal split is
left in that group.

| Slice | Lane | What | Done when (tier) |
|---|---|---|---|
| | | **The interview face** | |
| JRN1 | HUB + FACES | the draft proposes several Programs when the goal is several goals: one row per proposed Program in the change well ("Split into 3 programs") with Apply / Not this; never split by rule | a recorded draft of a three-goal paste returns three Program rows; Apply makes three Programs in Drafting, each with its own goal lines; Not this keeps one (T1, T2 `programs.app.test.tsx`) |
| | | **Dreaming** (the template, `night`, `within`, the backlog reader, the night stop and "Since last night" are LANG12) | |
| JRN2 | HUB + FACES | **Add to tonight** on a Door task, a Later finding and a note line: marks the item for the dreaming backlog (the mark the backlog reader reads, so no magic word is typed); `program.backlog_add`, `POST /api/programs/{id}/backlog`; a call's "add this to tonight" through the same tool | a press on each of the three rows puts the item in the next night's backlog read; the Door row shows "Tonight"; the call rig adds one by voice (T1, T2) |
| JRN3 | HUB | the red-main hold: no step of a Program with `night` is handed while the base branch's last CI run is red; "Since last night" says how long the night waited | the rig with a recorded red run holds a Ready step, hands it after a green run, and the digest names the wait (T1) |
| JRN4 | HUB | the night's end reaches him: one phone message with the first line of "Since last night", through Reach (the "Program is done" row's rules; quiet hours as built) | the night stop in the rig writes one reach with that line and no second one for the same night (T1) |
| | | **Answers by voice and by phone** | |
| JRN5 | HUB + FACES | the default, no ruling needed: on a call, a spoken answer to a held Your turn item becomes a **prepared answer** (the choice and his words as its line) on that item; the call decides nothing; Needs you shows "prepared on a call" with the item's verbs and **Not this** | the Calls rig turns "step 7: go on, with a new column" into a prepared row; the item stays open until a press; the press types his words to the agent at its next turn end (T1, T2) |
| JRN6 | HUB + PHONE | the item's own verbs on a phone message (Go on · Park, Met · Unmet, Merge · Not yet); a press on his paired phone calls `program.decide` as his press; never a waive (it needs a typed line) | a recorded phone press decides the item once; a second press hears "answered already"; the paired-device check refuses an unpaired token (T1) |
| JRN7 | HUB | with the ruling of §15.10 only: `program.decide` in the call palette, held for his spoken yes with the verbatim read-back, the same hold as `program.start` | the Calls rig decides a core question after "yes" and does nothing after "no" or silence; with the ruling off, the tool is not in the palette (T1) |
| | | **Audit programs** | |
| JRN8 | HUB | the **Audit** template: steps with no builder, each agent in a scratch copy (the reviewer's AG12 copy), `merge none`, a report of findings MUST / SHOULD / NOTE with evidence (a shot, a file and line); a commit on an audit step is a core question | a rig audit step returns a parsed report from a recorded agent answer; a commit on it raises the core question (T1) |
| JRN9 | HUB + FACES | each finding filed as a Door task with its evidence through `door.add_item`, one task for one finding across windows; the Findings board on the Program window; the audit stations BRIEF · WORK · REVIEW · FILE | from a recorded report, 14 findings become 14 tasks grouped by window, a repeated finding is one task; the board draws each state (T1, T2) |
| JRN10 | HUB | a proposed fix program from the MUST findings, a proposal row; started only by his press | the proposal makes a Program in Drafting with one step per MUST (T1) |
| | | **Lessons** | |
| JRN11 | HUB + FACES | the lesson rule (the same red cause on two steps, or the same finding on three), by rule, no model; the Lesson Your turn row **Keep for this program** · **Keep for HoldSpeak** · **Skip**; the `lesson` decide kinds; never kept by rule | two recorded reds with one cause raise one Lesson; Keep for this program adds an every-step requirement; a skipped cause is not proposed again in the Program (T1, T2) |
| JRN12 | HUB | **Keep for the repository**: a tiny step in the same Program that edits `.holdspeak/program.json` (the check line or a `requirements` item), checked, reviewed and merged as any step | the step's diff is one JSON change; the next Program reads it after the merge (T1, a temp git repo) |
| | | **From the desk, for a person** | |
| JRN13 | HUB + FACES | **Run as a program** on a project action row: a From the desk Program of that one action, `for` its person, planned at once | a press on a recorded action row makes one Program of one step with `from action:` and `for` (T1, T2) |
| JRN14 | HUB | a person review gate: the step's Review requirements become Your word at MERGE; GitHub "changes requested" comments go to the builder as findings for a round | a recorded "changes requested" review starts round 2 with its comments; the template requirement waits for his Met (T1) |

Sequence: JRN13 and JRN14 can go with LANG6; JRN1 after LANG7; JRN2 to JRN4
after LANG12; JRN5 and JRN6 after LANG5; JRN7 only after the ruling; JRN8 to
JRN12 after LANG15. User templates ("Keep for a template") are parked, not a
slice: the repository file is the place.

## 14. What he presses

1. He opens "The hub stops stalling" and presses **Text**. The plan is one
   page; each line's lamp says where the work is.
2. He types `merge owner` under step 6. The row "~ step 6 · merge level →
   owner · Allowed" appears. **Apply**.
3. He holds the bar's mic: "put the People routes on Codex and add a loop
   watch step before the fan-out". Three seconds. Three rows. **Apply**. A
   new step 7 lands with its six dots drawn one by one.
4. He makes a new Program from two paragraphs in a Note: **Run as a
   program**. The draft rises in: 8 steps, 11 requirements. **Ask me first**.
   The Architecture round asks one question; he answers by voice; two rows;
   **Apply**; the next question. **Done with Architecture**. **Skip round**
   for Product. **Start**.
5. In the morning, the Note of "Dreaming · HoldSpeak" says: "Since last
   night: 5 merged (#1702–#1706), 1 parked (too big for qwen, split
   proposed), 1 waits on you". He presses **Split**.

## 15. Decisions for the owner (defaults chosen; say if another is wanted)

1. **The text is a view; the tables stay the truth.** No `.program` file is
   stored by the hub; the CLI reads and writes files only on his machine for
   his scripts. Default: as written. The other choice: a repository may keep
   `.holdspeak/programs/<name>.program` as templates.
2. **A shaped change applies on his press below YOLO; at YOLO it applies at
   once, except a row that lowers the bar or is a core question.** Default:
   as written.
3. **One engine, `agent.plan`, plans, shapes and asks the rounds; a Program's
   `planner` line overrides it.** Default: the desk's assignment. The other
   choice: shaping on the Ask engine (`ask.answer`).
4. **"Apply what I say" below YOLO is off** (`shape_applies`). Default: off.
5. **Rounds help; they do not gate Start.** Default: Start is never held by
   an open round; `rounds before start` in the text makes them a gate for
   that Program.
6. **Dreaming may merge to HoldSpeak's own main at night** (each merge
   redeploys his desk). Default: yes at `at most 8 steps` and stop after two
   red steps; the other choice: `merge owner` for HoldSpeak's own repository,
   so he presses each in the morning.
7. **Measure is a fifth kind.** Default: add it (LANG11). A walk stays a
   Your word with walk lines.
8. **Sizing leaves half the window for the agent's work** (`WORKING_SHARE =
   0.5`). Default: 0.5.
9. **dw at two points only (link, Done) and one PR at Done.** Default: as
   written; off for HoldSpeak's own repository.
10. **A spoken yes on his own line decides a held item** (`program.decide` on
   a call, JRN7). Today a call may not confirm a decision for him
   (`docs/calls.md:44`). Default: **no**; the call prepares the answer and his
   press decides it, on the desk or on his paired phone (JRN5, JRN6). The
   other choice: the spoken yes, after the passphrase, with the verbatim
   read-back, for core questions and Your word.

## 16. How we know it worked

**The scripted walk** (a rig hub with the recorded planner, then on his desk
with the real one):

1. A running Program of six steps at Normal: step 1 Merged, steps 2–4
   Working, steps 5–6 Planned.
2. He says: **"Put step 3 on Codex after its limit."** The preview has one
   row, `~ step 3 · agent Claude Code → Claude Code, then Codex · Allowed`
   (step 3 started, so only the agents after the first may change, as
   `change_step` allows). Apply. `program.get` shows step 3's `runs_on` with
   two entries; one checkpoint; the first agent unchanged.
3. He says: **"Add a step that checks the People window at 393 before the
   fan-out, on pi."** The preview has `+ step 7 …`, `↕ step 7 before step
   6`, `~ step 8 · after … 7`, and `+ R9 shot: The People window at 393 has
   no clipped text` on the new step. Apply. The new step is Planned at
   position 6, the fan-out is step 7 and waits for it, R9 is on it with kind
   shot and case people at 393.
4. He says: **"And step 2 does not need the review."** The preview has one
   row, `~ step 2 · review agent → none · Lowers the bar · Refused: The bar
   does not come down while it runs` (step 2 is Working). Nothing applies.
   The bar says why.
5. The same three sentences at YOLO: sentences 1 and 2 apply at once and are
   two lines under Decided for you with Overturn; sentence 3 is refused the
   same way.
6. Every apply left one checkpoint and one frame; Overturn of sentence 2,
   while step 7 is Planned, puts the text back exactly (`diff(print(p),
   base)` is empty).

**Also:** the round-trip property over the fixtures; a 41k step held on a
32k engine and split at YOLO; a dreaming night in the rig that stops at its
cap with the digest; on his desk, a Program made from two paragraphs of his
reaches Running with requirements from two rounds in under ten minutes of
his time.

## 17. What this design could not establish

- **Latency.** No shaping or planning call has run; the targets of §4.7 are
  targets. `agent.plan` has never been invoked in this tree
  (`inference_memory_policy.py:105`), so its route on his desk (which engine
  the inheritance resolves to) is not verified.
- **Whether qwen3.8-27b writes valid block edits.** The contract is
  structured output and the parser is strict; the rate of unreadable answers
  is not measured. The quick forms are the fallback for short edits.
- **The harness's fixed context cost** for pi (its system prompt and the 
  HoldSpeak MCP tools it sees) is not measured; the sizing estimate needs
  one number per harness, measured once in LANG8.
- **The context window of the home engine.** pi reads it from the
  deployment's `context_ceiling` or uses 32,768 (`pi_launch.py:58`, `:128`);
  the owner says 64k; which one his desk's revision carries is not read.
- **The dreaming backlog sources.** Door tasks with "dream", small actions
  and the canon scanner's residues are named here; whether the scanner can
  emit one item per raw `<button>` with its file and line without a change is
  not checked. A main-run failure report does not exist today.
- **dw in a scratch worktree.** The rails' commit gate (`.githooks`) may
  refuse a commit made by the engine without a contract; the parked hooks in
  HoldSpeak do not tell how another repository's rails behave. LANG13 proves
  it in a temp repository first.
- **A TextPane in the kit.** Whether the desk can host an editor with a gutter
  and keep the 60 fps budget on a 400-line text without a library (CodeMirror
  is not in the tree) is not measured; LANG2 starts with a textarea and an
  overlaid gutter.
- **The journeys.** The times and the end-to-end walks of each use case are
  in `PROGRAM-JOURNEYS-2026-10-31.md`, written by another lane; this design
  did not read it. That document was reconciled with this one afterwards; its
  New needs are §13b.
