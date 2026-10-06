# HoldSpeak User Guide

Use this guide for daily work on the Desk.
It says how to do each task and names the control that does it.
For installation and your first capture, read [Getting Started](GETTING_STARTED.md).
The [documentation index](README.md) groups all guides by task.
These documents describe `main`, which can differ from your installed release.

Models, connectors, remote clients, and outbound actions each have their own data boundary.
See [Security & Privacy](SECURITY.md).
The default Control mode is **YOLO**.
Read [Control modes](AUTHORITY.md) before you configure external effects.

## Start here

| Task | Guide |
| --- | --- |
| Install and capture a sentence | [Getting Started](GETTING_STARTED.md) |
| Describe goals and receive suggestions | [Interview](INTERVIEW.md) |
| Prepare a decision review or an agent brief | [Architecture work](ARCHITECTURE_WORK.md) |
| Choose an automation path | [Automation](AUTOMATION.md) |
| Configure model engines | [Models](MODELS.md) |
| Record or review a meeting | [Meeting mode](MEETING_MODE_GUIDE.md) |
| Configure coding dictation | [Dictation pipeline](DICTATION_PIPELINE_GUIDE.md) |
| Use Desk windows and objects | [The Desk](WEB_DESK.md) |
| Select an environment | [Places](ENVIRONMENTS.md) |
| Work in a project | [Project Rooms](PROJECT_ROOMS.md) |
| Fix a problem | [Troubleshooting](TROUBLESHOOTING.md) |

## Develop a thought

Keep a rough sentence as a Note.
Then select **Develop this thought**.
HoldSpeak keeps the original text and opens the Thought Workbench.
The Note is editable Markdown, and it saves as you type.
On a desktop, the Note and the Interview pane sit side by side.
On a phone, they are two full-width panes.

The Workbench never starts a model by itself.
Select **Ask AI** for one model turn.
When a question returns, select **Add & ask next** to add your answer and start one more turn.
Select **Add to Note** to add the answer without a new turn.
Select **Finish Thought** to finish at once.
If you edit the Note during a turn, the edit replaces that question.
A late result cannot overwrite your text.

If no model can run, Interview shows **Set up AI**.
It opens **Settings > Models**.
After you save a model, the Workbench checks readiness again and shows **Ask AI**.
Before each turn, Interview shows where the turn will run.
After the turn, it shows the receipt.
**Info** shows the preserved original.

### AI context

AI context is empty by default.
In the Thought body, select **Attach** beside **AI context**.
The picker lists pinned **Everyday context** first, then recent choices and search.
**Browse all notes** shows the full list.
The hub loads the chosen Notes and freezes their versions for the turn.
The result names what it used, for example `Used 1 context item · 5 notes`.

If a Note changes after you attach it, HoldSpeak does not swap in the new text.
It names the stale context and offers **Update context** or **Remove it**.

The picker has two groups: **On this Thought** and **For new Thoughts**.
**Use these by default** saves the current set as the default for later Thoughts.
**Remove from this Thought** detaches one item from this Thought only.
**Stop using by default** clears the default set and leaves existing Thoughts unchanged.
If a default item is stale, missing, or too large, HoldSpeak applies none of them.
The Thought is still created with no AI context, and **Default context not applied** says why.

The separate [Interview Thread mode](INTERVIEW.md) develops working context across repeatable sections.

## Voice typing

Use voice typing to insert text into the active app.

1. Start HoldSpeak with `holdspeak`.
2. Focus the target text field.
3. Hold the hotkey and speak.
4. Release the hotkey.

The default hotkey is Right Option on macOS and Right Alt on Linux.
If the system blocks global hotkeys or synthetic typing, keep HoldSpeak focused and use its hold-to-talk control.

### When voice typing does nothing

On macOS, three permissions carry three parts of voice typing.
The symptom tells you which permission is missing.

| Symptom | Missing permission | Pane |
| --- | --- | --- |
| Nothing is heard | Microphone | **System Settings > Privacy & Security > Microphone** |
| The hotkey does nothing | Input Monitoring | **System Settings > Privacy & Security > Input Monitoring** |
| Words are transcribed but never arrive | Accessibility | **System Settings > Privacy & Security > Accessibility** |

Speak shows a row for each missing permission, with the pane to open and a `Re-check` verb.
The row reads `DENIED`, `NOT ASKED`, or `UNKNOWN`.
`NOT ASKED` means the launching application never requested the permission.
`UNKNOWN` means HoldSpeak could not read the state.

The permission belongs to the application you launched from.
If you start the hub in a terminal, enable Terminal or iTerm in those panes.
macOS applies some grants only to a new process.
Quit and reopen the launching application, then select `Re-check`.

The hotkey line shows the state of the whole path.
`ACTIVE` means the key is up and every grant is held.
`BLOCKED` means a grant is missing.
`UNAVAILABLE` means the listener did not install.
When the listener fails, Speak names the reason:
`PYNPUT MISSING`, `NO GUI SESSION`, `PERMISSION REFUSED`, or `LISTENER FAILED`.

### Spoken language

Whisper transcribes about 99 languages.
Open **Settings > Voice** and use the **Language** control.
The default, Auto-detect, picks the language for each utterance.
Short utterances can be detected as a neighboring language.
If that happens, pin your language.
One setting covers dictation, live meetings, and imported recordings.

### The wake word

The wake word starts dictation with your voice and no key.
It is off by default.
Say the wake phrase (the default model listens for "hey jarvis").
HoldSpeak enters the armed window, a short countdown.
Your next sentence goes through the normal dictation pipeline.
Detection runs on your machine.
The only network use is a one-time download of the detection models.

Enable it in **Settings > Voice**, in the **Wake word** group.
The **Action** control has two values:

- **preview** (default): nothing is typed.
  A card shows the transcript and the pipeline output with a **Type it** button.
  The server types only the exact previewed text.
- **type**: HoldSpeak types at once.
  A false detection types into the focused app.

The wake word pauses while another source holds the microphone.
The setting `dictation.preview_before_type` applies the same preview card to hold-key dictation.
It is off by default.
**Threshold** and **Armed window** tune detection.

### Punctuation and symbols

Say a punctuation word and HoldSpeak inserts the symbol.

| Say | Inserts |
| --- | --- |
| `period` or `full stop` | `.` |
| `comma` | `,` |
| `question mark` | `?` |
| `exclamation mark` | `!` |
| `colon` | `:` |
| `semicolon` | `;` |
| `new line` | line break |
| `new paragraph` | blank line |

For example, "hello comma can you review this question mark" becomes `Hello, can you review this?`.

To add your own, open **Settings > Voice** and use the **Spoken symbols** dictionary.
Map a spoken phrase to a symbol or snippet.
Your entries win over the built-in words.
The attach mode sets spacing: `none`, `left`, `right`, or `both`.
With `both`, "std double colon vector" types `std::vector`.

### Clipboard token

Say `clipboard` in a phrase to insert the clipboard text at that place.
HoldSpeak removes the word and inserts the clipboard contents.

## Speak

Speak is the voice-typing window on the Desk.
It shows one loop: talk, see the result, judge it, teach it once, and watch the teaching apply.
It has four wings, **SPEAK**, **JOURNAL**, **BLOCKS**, and **LEARNED**.
The gear opens **Configure dictation**.

### The Speak wing

The **Talk** button is the one microphone control on this face.
Select it once to start and once to stop.
The **Open** latch keeps the microphone open.
**LEVEL** shows audio input.

You can also type in the utterance well and press **Ctrl+Enter** or **Cmd+Enter**.
With **DRY RUN** on, the run previews and types nothing.
**LANDS IN** names the target and its last latency.
The **FOCUSED APP** picker sets the target.

A finished run shows a **RESULT** with **OK** and **Wrong**.
**OK** acknowledges the result and writes nothing.
The **DICTATION** row names the transcription model and its host.
If no model is set, it reads **NOT SET** and a **Choose** verb opens **Models**.
**Details** shows the pipeline state, the latency budget, and the raw trace.
The footer has **Review**, which opens the Journal wing, and **Export**, which downloads the journal as Markdown.

### Teach a correction

Select **Wrong** to open the teach row.
The **FIELD** control picks one of three kinds.

| FIELD | What you teach | What it changes |
| --- | --- | --- |
| **TEXT** | A phrase as heard, and as you said it | The words of later dictations that contain the heard phrase |
| **INTENT** | The block this kind of utterance belongs to | The routing of later similar utterances |
| **TARGET** | The delivery target this kind of utterance belongs to | The routing of later similar utterances |

For **TEXT**, correct the wrong words in **What you said**, then select **Teach**.
**INTENT** and **TARGET** offer a fixed list.
The target list has **Claude Code**, **Codex CLI**, **Terminal shell**, **Browser**, **Editor**, and **Chat**.
The intent list shows your loaded blocks.

A receipt replaces the teach row for five seconds.

| Receipt | Meaning |
| --- | --- |
| `TAUGHT` | HoldSpeak stored the correction. |
| `NO CHANGE` | You edited nothing. |
| `REFUSED · SECRET` | The text looks like a key or a token. HoldSpeak wrote nothing. |
| `REFUSED · ONE WORD` | One word cannot route an utterance. This applies to **INTENT** and **TARGET**. |
| `REFUSED · EMPTY`, `REFUSED · KIND` | The request had no phrase, or an unknown kind. |

A text correction is exact.
It ignores case, repeated spaces, and edge punctuation.
It does not fire inside a longer word.
Longer rules apply first, and each rule sees the text the previous rules left.
A routing correction is approximate.
It matches a later utterance by token overlap above 0.5.

When a stored rule changed a run, the **RESULT** line shows **APPLIED**.
Select it to see each rule that fired.

### The Journal wing

The Journal wing streams every dictation this device ran.
**Search** filters the loaded rows.
The tokens **ALL**, **DICTATION**, **BROWSER**, and **HOTKEY** filter by source.
**Clear** deletes the whole journal.
Open a row to edit its transcript and to use **Replay**, **Copy**, and **Delete**.
**Replay** runs the stored transcript through the current pipeline.
It shows a preview, types nothing, and writes no row.
The stream loads 50 rows at a time.

### The Learned wing

The Learned wing lists every correction with its kind, key, and value.
`N APPLIED` counts the journal rows where the rule fired.
**Forget** removes one correction after one confirmation.
**Configure dictation** has a **Learning digest** for the week.

### Storage and privacy

Corrections are on by default (`dictation.pipeline.corrections_enabled`).
Corrections and journal rows live in the HoldSpeak database on this device.
The journal keeps the latest 500 entries.
HoldSpeak redacts a transcript that looks like a key or a token before it stores the row.
Both stay after a restart.

### Who owns the microphone

One machine has one microphone floor with one owner.
The hotkey, a meeting recording, the wake listener, and the browser microphone all claim it.
Open **Details** to see the `Mic` row: `CLOSED`, `SUSPENDED`, `OPEN`, `SEGMENTING`, or `HELD`.
If another source holds the floor, Speak names it, for example `FLOOR HELD MEETING`.
If you lose the floor while you speak, capture stops with `AUDIO FLOOR LOST`.

### When capture goes wrong

Speak names every capture that does not finish.
Your typed words stay in the well.

| What happened | What you see |
| --- | --- |
| Microphone access is blocked | `PERMISSION DENIED` |
| You said nothing | No speech was detected. HoldSpeak writes no row. |
| The speech engine failed | `TRANSCRIPTION FAILED` |
| Another source took the microphone | `AUDIO FLOOR LOST`. HoldSpeak discards the half sentence. |
| The session closed | `MIC INTERVAL CLOSED`. Select the microphone to continue. |
| The tab closed after you spoke | HoldSpeak still transcribes the words. Find them in **JOURNAL**. |

Typing into another app is a real effect.
If the typing adapter fails after the text may have landed, HoldSpeak parks the delivery as `OUTCOME UNKNOWN`.
A retry reads that outcome and never types a second time.

## The dictation pipeline for coding assistants

The dictation pipeline turns a spoken thought into a prompt for Claude, Codex, a terminal, or a browser.
It can add project context, keep project vocabulary, and detect that an assistant waits for your answer.

### Set up the pipeline

The pipeline is on by default.
Open the **Speak** window and select the gear to open **Configure dictation**.

1. Read the **Pipeline** group to see what is missing.
2. In the **Dictation runtime** group, select **Open Models**.
3. Assign a model to **Writing & dictation**, then select **Use these**.

The backend is `auto`, `mlx`, `llama_cpp`, or `openai_compatible`.
`auto` picks MLX on Apple Silicon and llama.cpp elsewhere.

To check the setup from the CLI:

```bash
holdspeak dictation runtime status
holdspeak dictation dry-run "ask codex to inspect the failing test"
```

For the full setup, read [Dictation Pipeline Setup](DICTATION_PIPELINE_GUIDE.md).

### OpenAI-compatible endpoints

Use `openai_compatible` when another host serves the model.
Examples are llama.cpp server, LM Studio, the Ollama OpenAI bridge, vLLM, LiteLLM, and hosted APIs.

1. Add the endpoint in **Settings > Models**.
2. Select it for **Writing & dictation** in the Concierge set.
3. Select **Use these**.

Assigning the model also sets the dictation backend.
For keyed providers, see [Models](MODELS.md).
The `HOLDSPEAK_PROFILE_<ID>_KEY` environment variable is a headless fallback.
HoldSpeak never writes the key to config or project context files.
If the endpoint fails, HoldSpeak keeps the original transcript and reports the failure in dry-run and readiness output.

The old `dictation.runtime.openai_compatible_*` fields no longer configure anything.
An upgrade converts a configured endpoint once into a model entry named `legacy-dictation`.
It does not carry over the key.
`dictation.runtime.openai_compatible_timeout_seconds` still applies.

### Project facts

Project facts are a `kb:` map in `.holdspeak/project.yaml`.
HoldSpeak stamps the exact values into dictation with no model.
Edit them in **Configure dictation**, in the **Knowledge** group.

### Project context

Project context is a `.hs/` directory at the repository root.
The files are plain text and safe to commit if your team agrees.

| File | Purpose |
| --- | --- |
| `instructions.md` | How to rewrite or inject prompts for this repository |
| `context.md` | Architecture, paths, setup notes, constraints |
| `memory.md` | Durable facts you approved |
| `workflows.md` | Test, build, review, and deploy commands |
| `issues.md` | A scratchpad for active problems |
| `terms.md` | Project vocabulary and preferred spellings |
| `targets.md` | Style notes for Codex, Claude, terminal, browser, editor, chat |
| `ignore` | Paths, topics, or data HoldSpeak must not inject |

Edit these files in your editor.
Rules:

- `.hs/` files are the canonical format.
- Flat files such as `.hs_context` are read-only compatibility inputs.
- If both exist, `.hs/<name>.md` wins.
- HoldSpeak never writes project context during dictation.
- HoldSpeak skips binary files, very large files, and files that look like secrets.
- Do not put secrets in `.hs/`.

### Automation hooks for Claude and Codex

The operating system does not expose a terminal's working directory.
Hooks let Claude Code and Codex report their own `cwd`, session id, and tool state.
Open **Configure dictation** and read the **Automation hooks** group to see hook status.
For the full flow, read [Claude/Codex automation hook install](AGENT_HOOK_INSTALL.md).

```bash
holdspeak agent-hook templates --agent claude
holdspeak agent-hook templates --agent codex --capture-messages
```

Assistant-message capture is opt-in.
When it is on, HoldSpeak keeps at most 4 KB of the latest assistant message from a Stop hook.
It marks likely questions as `awaiting_response`.
The next submitted prompt clears the text.

## Meeting mode

Use meeting mode for a searchable record of a conversation.

```bash
holdspeak meeting --setup
holdspeak meeting --list-devices
holdspeak
```

`--setup` checks system audio.
`--list-devices` lists audio devices.
Open **Meetings** to start and stop a meeting.
During a meeting, HoldSpeak shows the live transcript with speaker labels, bookmarks, topics, action items, and summaries.

After a meeting, its row in the Meetings stream shows one state.

| State | Meaning | Verb |
| --- | --- | --- |
| **SAVED** | Intelligence ran and results are stored. | **Open** |
| **OFF** | A transcript exists and no summary ran. | **Run summary** |
| **RAN** | Auto-run finished. The row shows duration and model host. | **Open** |
| **RUNNING** | Intelligence is running. | |
| **NEEDS YOU** | Open items need you. | **Open** |
| **NO TRANSCRIPT** | No transcript exists yet. | |
| **FAILED** | Intelligence failed. The row names the reason. | **Retry** |
| **REC** | The meeting is recording. | |

**Run summary** writes the summary, topics, and action items.
It also runs the routed plugins whose model assignments can be frozen. Their results can produce proposals.
For meeting details, read [Meeting mode](MEETING_MODE_GUIDE.md) and [Meeting intelligence](MEETING_INTELLIGENCE.md).

### The auto-run setting

Open **Settings > Meetings**.
The **Intelligence** row has three positions and a model host chip.

| Position | Behavior |
| --- | --- |
| **OFF** | Nothing runs by itself. Use **Run summary**. |
| **AFTER ROOM MEETINGS** | Intelligence runs after each meeting linked to a Room. |
| **AFTER EVERY MEETING** (default) | Intelligence runs after every meeting with a transcript. |

If no model is assigned, the chip reads **NO MODEL** and auto-run jobs queue with a named failure.

### Where the model runs

Meeting intelligence runs locally or on an OpenAI-compatible endpoint.
Transcripts, artifacts, and queues stay on this device.
No external system receives a write unless a connector or export does it.
Meeting text can go to the primary or fallback hosts in its capability assignments.
Add the endpoint in **Settings > Models**.
Select it for **Meetings** and apply **Use these**.
The `intel_cloud_*` fields only migrate old settings.
`holdspeak doctor` checks the endpoint and names the model each pipeline uses.

### Named owners

Intelligence puts names it hears into the `owner` field of each action item.
**Me** (the speaker) and **Remote** (the counterpart) are reserved.
An unclear owner is `null`.
To map an owner string to a person, add it under **Owner aliases** in the relationship's **Context** lens.
Add each name variant as its own alias.

## Proposals and review

Intelligence extracts decisions and action items.
Nothing fires by itself.
Each item arrives as a proposal, and **Confirm** commits it.

### Proposals in the Room and on the arrival

Proposals appear in the Room's **NEEDS YOU** section and on the arrival.
Each row shows `Decide:` for a decision or `Confirm:` for an action item.
It also shows the meeting and segment time, the speaker when known, and the model host.

| Verb | What it does |
| --- | --- |
| **Confirm** | Writes the decision record and the commitment. |
| **Edit** | Opens the text, owner, and due date. **Save & confirm** commits your version. The original stays as provenance. |
| **Dismiss** | Declines the proposal with a receipt. HoldSpeak creates no record. |

On the arrival, a proposal row has **Confirm** and **Open**.

### Review a meeting's outcomes

Open a meeting and select the **Review** wing.
The head shows how many proposals wait, the linked Project, and the extraction time.
**COVERAGE** shows how much of the transcript the read covered.
Proposals sit in two ledgers, **DECISIONS** and **COMMITMENTS**.
Each row has three separate chips:

- The kind, `PROPOSAL`.
- What the transcript shows: `SUPPORTED` (a quote of its span), `LINKED` (the span exists but the wording differs), or `UNSUPPORTED` (no source).
- Your judgment, `UNREVIEWED` until you act.

A missing owner or due date shows as `OWNER · UNKNOWN` or `DUE · UNKNOWN`.
HoldSpeak never guesses them.
**MORE** on a row holds **Edit**, **Dismiss**, and **Open evidence**.
**Accept reviewed** in the footer confirms every `SUPPORTED` or `LINKED` row with no unknown.
The receipt names what it left and why.
A retry or a repeated **Confirm** never creates a second record while the transcript is unchanged.
If the transcript changes, a new read proposes again.
A **PRIOR REVISION** disclosure lists the earlier rows.

### Suggested sources

When a transcript names a repository or issue key that matches a connected provider, the Room's **SOURCES** section shows a suggested source.
**Add** creates a Watch source.
**Dismiss** hides it for this Room.

## The steward's hand

The steward drafts a weekly project update and can propose a reviewer nudge.
Both are opt-in, receipted, and visible before they act.

### The drafted update

When the steward runs, it collects every change since the last published update.
If you assigned a model to the project update capability, the model rewrites the inventory as prose.
Each factual sentence carries its claim reference as a chip.
Sentences the model added beyond the inventory read **UNVERIFIED**.
The footer names the model and its host.
Without a model, or if the model fails, the update uses the plain deterministic body.

The update has four verbs.
**Save** keeps your edit.
**Regenerate** rebuilds the draft.
**Copy** copies the Markdown.
**Publish** publishes it through the project revision law.

### What a claim state means

Each claim has three independent tokens.

**What the sentence asserts:** `OBSERVATION`, `INFERENCE`, `PROPOSAL`, `DECISION`, `EXECUTION RESULT`, or `OUTCOME MEASURE`.

**What the evidence shows:**

| Token | Meaning |
| --- | --- |
| `SUPPORTED` | A field mapping read the value from the named source version, or a person attested it. |
| `LINKED` | The sentence cites a real source and nothing more. |
| `LINKED · MIGRATED` | An older record. Nobody reviewed its citation. |
| `LINKED · EDITED` | You edited the sentence, so its support was withdrawn. |
| `UNSUPPORTED` | No source. |
| `DISPUTED` | Someone disagrees. |

**Who judged it:** `UNREVIEWED`, `ACCEPTED`, `REJECTED`, or `SUPERSEDED`.
Only you move this token.
A name, date, or number that the source does not carry shows as its own token, for example `NAME · Priya`.

### The health rows

The Room's **HEALTH** section appears when at least one source has entities.
It shows `CHECKED <age>`.
Each row is one signal, with a green, amber, or red lead chip.

| Row | Shows |
| --- | --- |
| **REVIEW WAIT** | Median and count of open PRs that wait for review. Days count from PR creation, because GitHub does not give the request time. |
| **ISSUE AGING** | Jira issues older than the threshold (default 14 days). |
| **CI** | Flaky branches and PRs that pass CI but are not merged. |
| **RELEASE** | The combined state, `READY` or the worst signal. |

An absent row means HoldSpeak has no data for it.

### The reviewer nudge

A reviewer nudge is a proposed GitHub comment on a PR whose review wait exceeds the threshold.
It is the first external write the steward can make.

1. Open the steward policy on the project.
2. Check **Reviewer nudge**.
   The row shows the `GITHUB.COM` egress badge.
   It is unchecked by default.
3. When the steward proposes a nudge, a **NEEDS YOU** row appears with a **Nudge** verb.
4. Select **Nudge**.
   The card shows the reviewer, the PR, and the comment text.
   You can edit the text.
5. Select **Send** to post the comment from your own `gh` identity.
   Select **Dismiss** to close the card with no write.

After you send, the card becomes a receipt, for example `SENT, Ania Kowalska, #612, 18:02, GITHUB.COM`.
HoldSpeak cannot retract a posted comment.
After a send or a dismiss, the steward waits 7 days before it proposes the same nudge again.

## Prepared work: preparation, review, and the weekly update

Three prepared procedures ship: **meeting preparation**, **decision and commitment review**, and the **weekly project update**.
Each is a versioned descriptor in the product tree, bound to the service that already does the work.
You do not author them.

A descriptor declares its inputs, sources, produced record, executing service, effects, and triggers.
Compiling one against a project binds those declarations to that project.

A descriptor declares a limit only where one is real.
Where the executing service enforces a cap, the descriptor points at that service's own value and reads it rather than repeating the number.
Where no cap exists, it declares none.
The same rule covers inputs: none of the three offers a setting no step can act on.

A blocker comes back as a typed gap with a coverage state: `available`, `stale`, `failed`, `forbidden`, or `unavailable`.
A plan with a gap is not ready.
A source you did not connect reports `unavailable`.
It never reports an all-clear it did not observe.

### Running one

All three run manually, through the surface each already had.
Run preparation from the Room, the review from the follow-through board, and the update from the steward.
Compiling a plan is a read.
It writes nothing and runs nothing.

**None of the three fires on a schedule yet.**
A schedule needs an owner path that really recurs: a connector watch swept by the Heartbeat, whose due evaluation mints an effect the steward drains.
No effect kind names one of these three yet.
Each descriptor reports its scheduled trigger as an unavailable prerequisite.

### Finding them

Over MCP, `practice_recipe.list` reads the catalog, `practice_recipe.get` reads one descriptor, and `practice_recipe.compile` compiles a plan.
Do not confuse these with `recipe.list` and `recipe.run`, which are for Agents you author.

Over HTTP:

- `GET /api/automations/practice-recipes`
- `GET /api/automations/practice-recipes/{recipe_id}`
- `GET /api/automations/practice-recipes/{recipe_id}/plan`

## Reach

Reach lets a second machine on your tailnet call the hub remotely.
It can run the Heartbeat sweep and the steward's drafter while you are away.
The hub uses Streamable HTTP.
A scoped credential limits the caller, and every remote call leaves a receipt.
There is no relay and no cloud proxy.

### Turn remote access on

1. Stop the hub. Start it with `HOLDSPEAK_WEB_HOST=0.0.0.0 holdspeak web --no-open`.
   This binds all IPv4 interfaces, including loopback.
2. Open **Settings > System** and switch remote access on.
3. Connect the runner to the hub's tailnet IP and actual listening port.

Remote access is off by default. Its switch controls MCP admission.
The stored `bind_host` value does not change the listener.

### Issue a credential

With remote access on, a `CREDENTIALS` section appears.

1. Select **Issue credential**.
2. Enter a **Name**.
3. Pick a **Palette**: `PROJECT` (default), `SWEEP`, `DESK`, or `ALL`.
4. Pick a **TTL**: `12 H` (default), `24 H`, `7 D`, or `30 D`.
5. Select **Issue**.
6. Copy the token.
   The page shows it once.
   The hub stores only a hash.

The palette limits which tool families the credential can call.
`PROJECT` allows project tools only.
`ALL` allows every non-owner tool.
**Revoke** on a row ends the credential at once.
Credentials are in memory, so a hub restart clears them.

### What a remote caller can do

A remote credential acts as an `AGENT`, never as `OWNER`.
`POST /api/mcp` refuses the owner's web token on a non-loopback request.
No other route applies that refusal.
A call outside the palette returns a capability error.
HoldSpeak never reads `X-Forwarded-For` to find the principal.
Every remote tool call writes a receipt with `origin: remote` and the credential name.
Receipt rows show a `REMOTE` badge with the caller's address.

### The overnight runner

A headless machine runs a client script that connects with a scoped credential.
It calls `heartbeat.run_now` for one sweep, then `project.run_steward` for each active Room.
The receipts arrive on your desk.
The hub does not prevent sleep.
Keep the hub machine awake, for example with `caffeinate -s`.
See [Reach Runner](REACH_RUNNER.md) for the install steps.

### Rhythm's Runs on row

In **Settings > Rhythm**, the `Runs on` row picks `THIS DEVICE` or a configured remote host.
For a remote host, the caption reads `WHILE THIS MAC IS AWAKE`.

## The Arrival

The arrival is the Desk home screen.
Its headline shows how many items need you, for example `17 need you across 3 projects`.
It reads `Nothing needs you` when none do.
It reads `Coverage incomplete` when a source was not observed.
A line under it names your next scheduled recording or calendar event.

**NEEDS YOU** shows five items at first, ranked so the first row is where to start.
A strip of tokens (`RANKED · OVERDUE · DUE TODAY · NOT RUN · NO DUE DATE · WAITING`) states the order.
Each token filters one class.
**Show all** reveals the rest, and `Show fewer` collapses them.
Each row has a source emblem, the item, its reason, the Project, and one verb.
One item from several sources shows as one row.
`N SOURCES` lists the sources, each with **Open**.

### When a source was not observed

`Nothing needs you` appears only when every expected source answered.
Otherwise a **COVERAGE** section appears above **NEEDS YOU**.
Each row names the source, the reason, when HoldSpeak last observed it, and a repair verb.

| Token | Meaning | Verb |
| --- | --- | --- |
| `READ FAILED` | The read failed on this pass. | **Retry** |
| `CANT CHECK` | A watch reported an error, often a credential. | **Reconnect** |
| `STALE` | The last good read is too old. | **Retry** |
| `PAUSED` | The watch is paused. | **Open source** |
| `NEVER CHECKED` | The watch never finished a check. | **Open source** |
| `NOT OBSERVED` | The source was expected and not read. | **Retry** |
| `FORBIDDEN` | The source refused the read. | **Open source** |

Items from a failing source stay in **NEEDS YOU**, marked `STILL TRUE · OBSERVED <time>`.
The hub keeps this memory only while it runs.

The other sections are **THOUGHTS** (unfinished Thoughts, with **Continue**), **BRIEF** (waiting items with **Ack** and **Defer**, or **Generate**), and **MEETINGS** (the last three).
An empty section is absent.
The capture bar at the foot has **Talk**, **Develop a thought**, and **Record meeting**.

## The clock

The clock is the calendar on the Desk.
Your calendar is one or more ICS sources, either file paths or HTTPS URLs.
HoldSpeak reads the next 14 days from every enabled source.
The hub refreshes each source at boot and every 15 minutes.
A source that fails keeps its last good events and leaves a named receipt.

### Connect a calendar

1. Open **Settings > Meetings**.
   You can also select **Connect calendar** on the arrival.
2. In the **CALENDAR** section, select **Add** on the **Connect calendar** row.
3. Enter an ICS URL or a local file path.
4. Select **Save**.

Each source gets a row with **Edit**, **Disable** (or **Enable**), and **Remove**.
An HTTPS source shows an egress chip with the host.
A file source shows no chip because nothing leaves the machine.
If two feeds hold the same event, it shows twice with its source label.

### Import from a screenshot

Use a screenshot when your calendar has no ICS feed.

1. Take a screenshot of the week view.
   PNG, JPEG, and WebP work.
   You can merge up to three screenshots of one week.
2. In **Settings > Meetings**, select **Snapshot** on the **Connect calendar** row.
   You can also drop the image on the Desk.
3. The hub sends the image to the vision model assigned to `calendar.snapshot_extract`.
   If none is assigned, the import is refused with a receipt.
4. Review the events in the window.
   Set the **Week anchor** (the Monday, `YYYY-MM-DD`).
   HoldSpeak never guesses the anchor.
5. Select **CONFIRM** to write the events.
   Close the window to cancel.

HoldSpeak writes a local `.ics` file under `~/.local/share/holdspeak/calendar-snapshots/`.
It registers the file as a source labeled **O365 SNAPSHOT**.
The normal bounded ICS parser reads it.
A new screenshot of the same week replaces that source's events.

### Armed recordings

An armed recording is linked to a calendar event.
The title, start, and duration come from the event.
The recording starts 60 seconds before the event.
If the event is already running, it starts at once.
Duration is at most 480 minutes.
The arrival shows an **ARMED** line with a countdown and a **Cancel** verb.

When the recording runs, it uses the same capture path as a manual recording.
The finished meeting shows **FROM <SOURCE>** with the event title.
Calendar changes follow an idle armed recording:

- A longer event or a new title updates the recording.
- A moved event rebinds the recording to the nearest occurrence of the series.
- A removed event cancels the recording.

A recording that already started is never changed.
You can arm an imported snapshot event the same way.

### Auto-record

Open **Settings > Meetings**.
The **Auto-record** row has three states.

| State | What it does |
| --- | --- |
| `OFF` (default) | Creates no event recordings. |
| `ARM ROOM MEETINGS ONLY` | Arms events that match a Room. |
| `ARM ALL CALENDAR MEETINGS` | Arms every event with a meeting URL. |

An armed recording starts five minutes before the event.
The setting is your standing consent to record.
**Cancel** stops one recording for good.
A later refresh never re-arms it.

### The week and the brief

When a calendar is connected, the arrival shows a WEEK strip with one dot per meeting for each day.
The Room's **SOURCES** section shows a meeting watch row with the count and the next meeting.
The brief gains a `THIS WEEK` section with meetings, armed recordings, commitments due, and new decisions.
In **Settings > Rhythm**, the brief row regenerates daily.

## Connect your tools

Open **Settings > Connections**.
Each tool has a card with a readiness state and one verb.

| Tool | States | Recovery |
| --- | --- | --- |
| **GitHub** | `Connected`, `Sign in`, `gh missing`, `Unreachable`, `Off` | `gh auth login` |
| **Jira** | `Connected`, `Sign in`, `acli missing`, `Not set up` | `acli jira auth login --site <site> --email <email> --token` |
| **Calendar** | `Connected`, `Not set up` | Opens **Settings > Meetings** |
| **Models** | `Assigned`, `Unassigned` | Opens **Settings > Models** |

`gh` and `acli` hold the credentials on this machine.
HoldSpeak stores no token and uses no relay.
**Recheck** runs the CLI's own probe from this device.
The tile footer shows the check time and the host contacted.
Each Jira connection is one (site, email) pair.
Confluence uses the same `acli` identity.

The API is `GET /api/connections` and `POST /api/connections/{provider}/recheck`.
The MCP tools are `connection.list` and `connection.recheck`.

## New Project

Select **Desk > New Project**.
Type what you deliver in the outcome line.
This text becomes the project name (first 80 characters) and its outcome.
A microphone button accepts voice.

Each connected tool (GitHub, Jira) has a row in **SOURCES**.

1. Select the scope trigger and pick a repository or project.
   The picker has search and **Show more**.
2. Set the default Watch toggles.
   GitHub has `OPEN PRS` and `CI`, both on.
   Jira has `OVERDUE` and `DUE 7 DAYS` on, and `BLOCKED` off.
3. Read the live count.
   The row reads `CHECKING`, then the count, or `CAN'T CHECK` with the reason.
4. Select `Adjust` for more settings.
   GitHub has `BASE BRANCH`, `LABELS`, and `DRAFTS`.
   Jira has `ISSUE TYPES` and `JQL`.
5. Select `Create Project`.

A tool that is not connected shows `Connect`, which opens **Settings > Connections**.
You can create a project with no sources.
Create builds the project and its Watches, then opens the Room.

## Project Room

A project opens as a Room with two wings, **ROOM** and **HISTORY**.
The **ROOM** wing answers four questions in order.
What needs me now?
What am I watching?
What changed since I last looked?
What did we decide, and what do I owe?
An ask well sits at the foot.
For the full model, read [Project Rooms](PROJECT_ROOMS.md).

- **The head** shows `3 need you` or `Nothing needs you`.
  Chips show `ON TRACK` or `AT RISK`, the target date, the check time, and the **Draft update** button.
  `AT RISK` means overdue Jira entities, failing CI on the base branch, or a review that waits more than 3 days.
- **NEEDS YOU** lists items with a reason and age, and `Open` or `Decide`.
  It draws on review requests, base-branch CI, overdue Jira entities, and pending proposals.
- **SOURCES** has one row per Watch with counts, the check time, the egress host, and `Pause` or `Resume`.
  A failing Watch offers `Remove`.
  A `SUGGESTED` row offers `Add`.
  The `Steward` button opens the steward settings.
- **SINCE YOU LOOKED** groups changes by source since your last read.
  Opening the Room moves the read marker.
- **DECISIONS & COMMITMENTS** comes from linked meetings.
  The section is hidden when empty.
- **UNFINISHED** holds asks you started and did not finish.
  HoldSpeak saves an ask before it sends it, so it survives a closed tab, a restart, or a trip to set up a model.
  `Resume` never runs the question twice.
  `Discard` is under `MORE`.
- **The ask well** takes `Ask this project…` with a microphone.
  The model chip shows `MODEL · <host>` or `MODEL · NOT SET`.
  Answers carry citations.
- **HISTORY** is a dated stream.
  Filter by `ALL`, `GITHUB`, `JIRA`, or `ROOM`, or search by text.

## Settings

Settings is the one configuration window.
Its headline names the most important open issue, such as `No default model`, or `All set`.
Each row is a module with **Open**.

| Row | Controls |
| --- | --- |
| **MODELS** | The Concierge. See below. |
| **CONNECTIONS** | GitHub, Jira, Calendar, and Models readiness |
| **VOICE** | Hotkey, language, typing, spoken symbols, wake word |
| **MEETINGS** | Intelligence, calendar sources, auto-record |
| **WALLPAPER** | The selected place |
| **RHYTHM** | The Heartbeat |
| **SOUNDS & PRESENCE** | Sounds and desktop presence |
| **SYSTEM** | Hub, remote access, mesh |

The **POSTURE** row cycles the Control mode: `YOLO`, `Normal`, or `Secure`.

## Rhythm

Open **Settings > Rhythm**.
Rhythm controls the Heartbeat.
The Heartbeat is the unattended sweep that evaluates project Watches and refreshes **NEEDS YOU**.

- **Sweep** sets the interval: `EVERY 5 MIN`, `EVERY 15 MIN` (default), `EVERY 30 MIN`, or `EVERY 60 MIN`.
  **Run now** runs one sweep at once, also during quiet hours.
  During quiet hours a `HELD · QUIET UNTIL hh:mm` chip shows.
- **Monday brief** regenerates once a day after quiet hours end.
  The `DAILY hh:mm` token is not a setting.
  **Generate** regenerates it now.
- **Notify** has two cycle controls.
  **Mode** is `OFF`, `ON THE EDGE` (default), or `EVERY SWEEP`.
  **Content** is `COUNT ONLY` (default) or `ROOM NAMES`.

`ON THE EDGE` fires when a new item joins the set that needs you.
The same items again stay silent.
A known item that becomes due today or overdue fires again as `1 escalated`.
Quiet hours hold notifications.
The first sweep after quiet hours delivers once.
A restart notifies nothing again.

Each Room has a mute toggle.
A muted Room is out of the notification count and the dock badge.
It stays in the shade's **PROJECTS** section, dimmed.
The shade's **PROJECTS** section lists each Room with needs-you items and an **Open** verb.
In the command deck (Cmd+K), type a project name to open its Room.

## Models: the Concierge

Open **Settings > Models**.
The Concierge shows what engines exist, what each capability uses, and whether all are ready.
The full reference is [Models](MODELS.md).

**FOUND** lists every detected engine with its kind (**LAN**, **THIS MAC**, or **CLOUD**), latency, host, and state (`READY` or `UNREACHABLE`).
A catalog preset not on disk shows **Download** with its size.
`Add an engine...` opens a field for a base URL, with **Check**.
A cloud row has a **Check** verb with the cost chip `1 TOKEN · $`.
It is the only action that sends a paid token.

**THE SET** proposes one engine for each capability group.
The groups are Thoughts & notes, Chat, Writing & dictation, Speech recognition, Meetings, Agents & tools, and Background.
Each row shows a state: **READY**, **CHECKING**, **WAITING**, **KEY NOT SET**, or **OFF**.
Speech recognition uses a local Whisper engine only.
Writing & dictation picks the smallest reachable low-latency engine.
Other groups pick the strongest reachable LAN engine.
A cloud engine appears only when you pick it.
**Use these** writes the whole set.
It stays disabled until every group is **READY** or **OFF**.
**Adjust** opens the full per-capability table.

A **NEEDS YOU** section appears when an assigned engine is not usable.

| State | Verb |
| --- | --- |
| **MODEL FILE MISSING** | **Download** |
| **ENDPOINT UNREACHABLE** | **Check** |
| **TOOL INCOMPATIBLE** | **Choose** |
| **CREDENTIAL EXPIRED** | **Connections** |

**Test** on the **PROBE** row sends one short real request through the assigned route.
It reports the model, the time, and the host.
If the route leaves this machine, the first **Test** refuses and names the boundary.
Select **Test** again to run it.

When you open **Models** from a Thought, an Interview step, or Speak, it opens over that work.
After **Use these**, the face you came from checks readiness again.

## People

People is an encrypted, local-only surface for managers who run recurring 1:1s.
HoldSpeak encrypts every record with a key in your OS credential store (macOS Keychain or Linux Secret Service).
See [People security](PEOPLE_SECURITY.md) for the boundary.

1. Open People from the Desk or the Go menu.
2. Select **Set up People** on the first visit.
3. Select **New relationship**.
   Enter a name, pick a kind (Direct report, Peer, or Extended), and select **Add**.

### Link the 1:1 series

1. Open a relationship and select the **Context** lens.
2. Select **Link calendar event** in the Calendar series section.
3. Pick an event.
   Events with the person's name sort first, marked **SUGGESTED**.

One link covers every past and future occurrence of the series.
A series links to one person at a time.
Select **Unlink**, then **Unlink?**, to remove a link.

### The Prep brief

The Prep lens is computed when you read it and is never stored.
It shows open assignments, overdue commitments, the last meeting, the agenda, what you wait on from the person, and shared Projects.

The `people.one_on_one.brief` MCP tool returns only `shared_intent` material.
It never returns leader-private items.
The People MCP capability defaults to write for the local owner.
Set `HOLDSPEAK_MCP_PEOPLE_ACCESS=read` or `=off` in the hub's environment before the hub starts to reduce it.

### The 1:1 card

Before a 1:1, the person's card shows what waits on them from your project Watches.
**PRS WAITING** lists PRs where they are a requested reviewer.
The Prep lens counts their open Jira assignments.
**LAST MEETING** shows the open items.
A name never leaves the encrypted store.
Only opaque references cross into the Watch projection.

### Map an owner string to a person

A meeting gives each action item an owner string.
Open the relationship, select the **Context** lens, and add the string under **Owner aliases**.
One person holds one alias.
The reserved strings `me`, `remote`, and `you` cannot be mapped.

### People in the Room

A Room's **PEOPLE** section lists every person the Project names.
The caption is `PEOPLE 2 OF 3` when someone is not linked yet.
A row shows the person's open commitments with **Open source**, and observable facts such as `2 PRS WAITING`.
HoldSpeak never scores, ranks, or infers.
An owner that could mean two people reads `OWNER · AMBIGUOUS` with **Resolve**.
An unknown owner reads `OWNER · NOT LINKED` with **Link**.
HoldSpeak never attributes an ambiguous owner by itself.
A locked or missing ledger shows `LOCKED`, `NOT SET UP`, or `UNAVAILABLE` on the section.

### The chief-of-staff brief

The Monday brief gains a People section when you map relationships with open signals.
Each row shows **They owe N**, **You owe N**, **N agenda**, and **Next: title**.
Expand a row for **Add to 1:1 agenda** and **Open person**.
HoldSpeak computes this section when you read the brief and stores nothing about people in it.
If the sidecar is down, the brief shows **PEOPLE · UNAVAILABLE**.

### The dev keystore

Set `HOLDSPEAK_PEOPLE_KEYSTORE_FILE` to a file path to replace the OS credential store.
Use it for development and tests only.
`holdspeak doctor` reports the keystore mode and warns when the dev keystore is active.

## Threads

A Thread is a saved conversation on the hub.
It holds your messages, model replies, source references, and tool results.

### Start a Thread

1. Select **Desk > New Thread**.
2. Select a mode if the task needs one.
3. Enter your request and select **Send**.

You can also select **Continue in thread** on a supported Desk object.
The object becomes a source reference.

### The composer

Type, or use the microphone.
Type `@` to attach Meetings, Notes, Artifacts, and decisions.
**Enter** sends.
**Shift+Enter** adds a line.
**Send** becomes **Stop** during generation.
A failed send keeps your text.
An unsent draft does not survive a reload.

Replies stream in.
The turn's boundary and Receipt show where it ran.
Routine tool calls stay collapsed under **Actions**.
Approval requests, questions, failures, and denials stay visible.

### Branch, keep, and search

Editing a past message or regenerating a reply creates a branch.
Branch controls show the siblings.
Keep a reply as a Note or an Artifact with its provenance.
Desk search includes saved Threads.
A recall in the Desk memory window returns the current decision first, with its rationale and source.
It lists superseded or disputed versions after it.
**Carry into brief** queues the current record for the Project's next preparation.
See [Relationship-aware memory](RELATIONSHIP_AWARE_MEMORY.md).

### People boundary

People source parts carry a sensitive classification.
The context assembler redacts them before a cloud model turn.
In Interview's **People** section, use **Open People** for relationship work.

### The Thread has hands

A model can request the tools its mode exposes.
The Thread tool gate checks the tool class, the Control mode, and any recorded tool policy.
The called service also applies its own rules.

| Control mode | Tool admission without a per-tool policy |
| --- | --- |
| **Secure** | Evidence reads proceed. Candidate builders and effect proposals wait for you. |
| **Normal** | Evidence reads and candidate builders proceed. Effect proposals wait. |
| **YOLO** | Classified, offered tools proceed. Service authority checks still apply. |

A held call offers **Allow once**, **Allow always** (a policy for this tool in this Thread), and **Deny**.
A recorded policy wins at the Thread gate.
It does not bypass destination, credential, or permission checks.
See [Control modes](AUTHORITY.md).

### Modes

A mode selects a system instruction and a tool set.
Select a mode above the composer.
A change applies to the next turn.
Select the active mode again to remove it.

| Mode | Purpose |
| --- | --- |
| **Desk** | Read Desk evidence and prepare candidates. |
| **Chase** | Use broader Desk and People operations for follow-through. |
| **Draft** | Write without tools. |
| **Plan** | Read Thoughts, decisions, and Desk context. |
| **Project** | Use the project mode and its MCP path. |
| **Interview** | Revisit sections and develop suggestions. |

### Saved prompts, guardrails, annotations

- A saved prompt is a Note tagged `prompt`.
  `/prompt <name>` inserts it.
- A guardrail is a Note tagged `guardrail` with settings in its front matter.
  It can show violations or warnings.
  It does not deny requests by itself.
- Select text in a reply to add a comment.
  Saved comments join your next message.

### Slash commands

Type `/` at the start of a line.

| Command | Action |
| --- | --- |
| `/mode <name>` | Select a mode |
| `/prompt <name>` | Insert a saved prompt |
| `/tools` | List the mode's tools |
| `/guardrail <name>` | Toggle a guardrail |
| `/todo <text>` | Create an action item with a link to the Thread |
| `/compact` | Summarize earlier turns into a cut marker |
| `/keep` | Keep the last reply as a Note |
| `/fork` | Branch the conversation |
| `/stop` | Stop generation |
| `/new` | Create a Thread |

### The Call

Call mode combines spoken replies with microphone input.
A new Thread starts with Call off.
The control shows listening, thinking, or speaking.
Select it again to stop.
Browser speech synthesis is the default voice.
The optional `tts` extra adds server voices through kokoro-onnx.
It includes GPL-3.0 components.

## Schedule a recording

A scheduled recording uses the hub's microphone and the same capture path as a manual recording.
No browser needs to be open.

Create one in any of three ways:

1. Select **Schedule** in the arrival's capture bar.
   Name it, choose **Once** or **Recurring**, and set a duration (default 60 minutes).
2. Call `POST /api/scheduled-recordings` with `title`, `cron_expr`, `duration_minutes`, and `enabled`.
3. Use the `scheduled_recording.*` MCP tools.

A one-shot schedule fires once and disables itself.
A recurring schedule moves to its next time after each outcome.

At the scheduled time, the hub starts an arming countdown.
Cancel it with `POST /api/scheduled-recordings/{id}/cancel`.
Otherwise capture starts and stops at the set duration.
If another source holds the microphone, the schedule refuses with a receipt.
If the hub was down, it leaves a missed receipt after restart.

## Project memory

Open **Desk memory** to search connected evidence across the Desk or within a Project.
Intelligence turns each decision from a meeting into a durable record.
A decision moves through `proposed`, `accepted`, `superseded`, and `deprecated`.
A decision that replaces another names the one it supersedes.

To rebuild the local search indexes, run:

```bash
holdspeak memory rebuild-index
```

The search index is not a backup.
Back up the database separately.

## Companions

A companion on another device drives the hub through the same local HTTP API as your browser.
It uses your LAN or Tailscale, with the hub's bearer token and no hosted relay.

**The iPad app** is a client for both modes.
You can dictate into your desk through the full dictation pipeline.
You can read a meeting back with its artifacts, sources, and aftercare, and browse the archive by speaker, tag, or text.
In Secure and Normal, proposals need your approval.
In YOLO, an eligible action to a configured destination runs with its receipt.
See [iPad](IPAD.md).

**AIPI-Lite** is an optional portable device for meeting controls, status, and spoken replies to a waiting Claude or Codex session.
See the [AIPI-Lite Developer Workflow](AIPI_LITE_DEV_WORKFLOW.md).

## Using the Desk

Every object on the Desk is a working icon.
See [The Desk](WEB_DESK.md) for the full grammar.

- **Badges show live facts only.**
  A member count sits bottom-right on a drawer or Knowledge.
  A green tick means edited in the last two days.
  An amber dot means it needs you.
- **Select and open.**
  One click selects.
  A double-click opens.
  On touch, a tap opens.
  Right-click shows the object menu.
- **Drawers are directories.**
  A double-click opens a drawer as a window with an Icons view and a List view.
  It remembers its view, sort, size, and position.
  **Take out** returns a member to the Desk.
- **Drop to compose.**
  Drag an object over another.
  A tag names what release does.
  A drop never runs a model.
  Dropping a Note on an Agent opens its card with the Note as run material.
  You select **Ask**.
- **Info.**
  Right-click and choose **Info** to see identity, where it is filed, where it came from, and, for Agents, **Runs on**.
- **The menu bar** has Desk, Object, Go, and Window.
  A verb that cannot run stays visible with its reason.
  Go reaches every application, the same list as the Cmd+K search.

The written rules are in [`web/ICON-DISCIPLINE.md`](../web/ICON-DISCIPLINE.md) and [`docs/internal/DESK_GRAMMAR.md`](internal/DESK_GRAMMAR.md).

## Mission Control on the Desk

If you plan work with [Delivery Workbench](https://github.com/karolswdev/delivery-workbench), the Desk shows your repositories as a conveyor.
Each project has a belt, each phase is a segment, and live Coder sessions pin to their story.
HoldSpeak keeps registered repositories in `~/.holdspeak/delivery_sources.json`.
A project map in `~/.holdspeak/delivery_workbench.json` imports once on first run.

The belt reads receipts.
Roadmap state comes from each repository's `dw` command, and PRs and CI results come from your own `gh`.
The ticker comes from the repository's rail log.
If a repository cannot answer, its lane says so.
The belt never writes.
The one action is the story-flip proposal, which uses the normal propose, approve, and execute flow.

### Pull request receipts

A registered repository shows its pull requests as rows in the list view.
Each row has the number, title, state, CI conclusion, author, and observation time.
Open PRs with failing CI sort first.
**Refresh** runs one batched `gh` call for each source.
It is the only network use.
To poll, set `pr_refresh_seconds` on the source's registry entry.
A failed refresh keeps the last good rows and marks them stale.

Each row says how it matched your work.
**exact** means the head commit or branch belongs to a registered worktree.
**name match** means a branch name resembles a story id.
Everything else is unattributed.

### Follow a pull request through

- **Diff** reads the local checkout.
- **Send agent** starts a Coder session in the matched worktree with your instruction and the PR diff.
- **Draft review** runs your model and keeps the answer as an Artifact.
- **Post comment**: edit the text, then select **Propose**.
  The row shows the full text with a GitHub badge.
  **Approve** posts exactly that text.
  **Deny** leaves GitHub unchanged.

**Merge**, **Close**, and **Force push** are not offered.
A result appears as a Receipt below the row.

## Steer a session from the Desk

Watching is free.
Every steer resolves authority and is audited.
Local steering does not leave your machine.

Select a session pin on the belt, or **Watch live** on a Coder card.
The session pull-out shows the terminal pane live and read-only.
It marks itself stale when the session goes quiet.

The pull-out names the exact pane and the Control mode.

- In **Secure**, select **Arm pane** for a five-minute grant on that pane.
- In **Normal**, the same action grants fifteen minutes.
  The chip becomes a countdown, and one click disarms it.
- In **YOLO**, an eligible registered session reads **YOLO · DIRECT** and needs no arm step.
  HoldSpeak still re-checks the pane identity before every key.
  A missing or replaced pane refuses.

A posture change or a hub restart clears pane grants.

After the grant, the composer appears.
Hold the microphone or type.
The paper-plane toggle sets whether HoldSpeak presses return after the text.
You can attach a meeting or an artifact with the grounding picker.
HoldSpeak caps it, shows the exact text before it sends, and refuses a context that is too large.

From the pull-out you can also keep the session's question as a Note, pin an off-rails session to a story, and flip a correlated story through the proposal flow.
Every reply and refusal goes to the steering audit.
Read it at `GET /api/coders/steering/audit`.

### Send keys, any pane, any machine

You can send real keys, such as `C-c`, `Escape`, the arrows, and `Enter`.
Keys use the same path and audit as text.
HoldSpeak refuses a name that is not a terminal key (`POST /api/coders/{key}/keys`).

`GET /api/coders/steering/panes` lists every tmux pane, including shells you opened by hand.
Secure and Normal ask you to arm the exact pane id (`pane:%N`).
HoldSpeak re-verifies the pane before delivery.

With nodes configured in `HOLDSPEAK_STEER_NODES`, the Desk relays steering to another machine.
The far node decides authority and records the audit.
A node that does not answer refuses at once.
The **Panes** list at the bottom of the Desk shows every pane and attaches to one.
A header chip names the machine you steer.
The Panes list can spawn a session by name.
Rename and Kill live in a separate session-control window.
Kill needs an arm and a confirmation.

## The gate

The gate lets a Claude Code session stop before a risky tool call and ask the Desk.
The agent's PreToolUse hook posts a proposal and waits.
The call runs only after you approve.

The gate fails closed.
If the hub is down or errors while the gate is armed, HoldSpeak denies the matched call and names the reason.
The gate is off by default, and the hook does nothing while it is off.

To arm it:

1. Run `holdspeak gate install`.
   Add the printed hook block to `~/.claude/settings.json` yourself.
   HoldSpeak never edits another application's configuration.
2. Run `holdspeak gate arm`.
3. Run `holdspeak gate allow --repo <path>` to name the repository whose calls are held.
   This release holds Bash only.

`holdspeak gate status` and `holdspeak doctor` show the state.
See [Gate](GATE.md).

A held call appears in the shade's **Needs you** group.
The card names the session, the tool, a redacted argument preview, and the wait time.
**Approve** lets the call run.
**Deny** takes a one-line reason that goes to the agent.
An undecided hold expires as a deny.
A hub restart invalidates every held proposal.
Read the audit at `GET /api/gate/audit`.

## Session receipts

A steered session's pull-out shows one receipt line.
Each number has a stated source.

- Elapsed time, steers, and holds come from hub records.
- Token figures appear only when the adapter reports them.
  A gated Claude Code session reports its transcript totals when it ends.
  A bare tmux pane reports none.
- Cost appears only with reported tokens and a price row for the model in `~/.holdspeak/pricing.json`.
  It reads `≈ $X.XX (price table, date)`.
  With no price row, HoldSpeak shows no cost.

## Ground a run on the rails

In the grounding picker, a rails group lists the belt's live projects, with the roadmap, phase, and stories.
Pick one, and its content joins your ask or steer, labeled with its source.
The hub reads the exact file the `dw` command names.
It refuses a reference it cannot resolve.

The optional ambient observer keeps a journal of rails activity.
It is off by default.
Turn it on in your configuration and name a model.
It reads your pipeline events and writes a Note for each batch.
It never changes the rails.
Read the journal at `GET /api/missioncontrol/rails/journal`.

## Privacy

HoldSpeak is local-first.
These stay on the machine by default:

- Audio capture and Whisper transcription.
- Meeting history.
- Dictation block configuration.
- `.hs/` project context.
- The Coder session registry.
- Captured assistant-message text, if you enable it.

Data leaves the machine only when you configure it:

- Cloud meeting intelligence.
- An OpenAI-compatible runtime outside localhost.
- Connector integrations.
- Manual exports and uploads.

Set model keys in the credential controls, or use environment variables for a headless hub.
See [Security & Privacy](SECURITY.md).

## Troubleshooting

Run diagnostics first:

```bash
holdspeak doctor
```

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| The hotkey does nothing | An OS permission or hook restriction | Check the permissions above. Use the hold-to-talk control. |
| Text does not type | Synthetic typing is blocked | Paste from the clipboard. |
| System audio is missing | No BlackHole or Pulse monitor | Run `holdspeak meeting --setup`. |
| The dictation model is unavailable | Missing backend or model | Open **Configure dictation** and read **Pipeline**. |
| Project context is not found | Wrong working directory | Set **Project root** in **Configure dictation**. |
| Claude or Codex context is missing | Hooks are not installed | Open **Configure dictation** and read **Automation hooks**. |

For more, read [Troubleshooting](TROUBLESHOOTING.md).

## See also

- [README](../README.md): install, platform notes, configuration.
- [Getting Started](GETTING_STARTED.md): first capture.
- [Interview](INTERVIEW.md): saved context and suggestions.
- [Automation](AUTOMATION.md): triggers, tools, and limits.
- [Dictation Pipeline Setup](DICTATION_PIPELINE_GUIDE.md): the pipeline, project context, and hooks.
- [Meeting Mode Guide](MEETING_MODE_GUIDE.md): meeting setup and troubleshooting.
- [Firefox Extension Guide](FIREFOX_EXTENSION_GUIDE.md): the companion extension.
