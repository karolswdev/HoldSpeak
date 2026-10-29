# HoldSpeak User Guide

HoldSpeak is an agentic-first, web-based AI operating system for work. The
Desk stores Notes, Meetings, Projects, People, and results. Ask and Threads
can read those records and use permitted tools. Coding-agent handoffs and
automations use their own prerequisites, scope, host, and receipts.

HoldSpeak is pre-alpha. A model answer or successful tool call does not establish that the result is correct.
A saved configuration does not establish that a later job will run. Inspect the source records, result, and receipt.

## Start here

1. Start the local hub and open its printed URL.
2. Open **Settings > Engines** and check the engine for the task.
3. Keep one Note by typing or using **Speak**.
4. Select **Ask about this** on the Note, or open **Ask** for a whole-Desk question.
5. Inspect **References** and any **Wrote** or **Prepared** result.

Ask and Thread share one window. **Go > Ask AI** opens the window labelled
**Ask**. To start a new conversation, select the first row in **Recent** or
press **⌘N**. The first question is kept as a Thread. Follow-up questions
continue it. A separate Thread window is parked in the current Desk
navigation.

Use [Getting Started](GETTING_STARTED.md) for installation and [The
Desk](WEB_DESK.md) for navigation.

| Task | Start here |
| --- | --- |
| Install and keep a sentence | [Getting Started](GETTING_STARTED.md) |
| Describe goals and receive suggestions | [Interview](INTERVIEW.md) |
| Prepare a decision review or agent brief | [Architecture work](ARCHITECTURE_WORK.md) |
| Choose an automation path | [Automation](AUTOMATION.md) |
| Choose model engines | [Models](MODELS.md) |
| Record or review a Meeting | [Meeting mode](MEETING_MODE_GUIDE.md) |
| Configure coding dictation | [Dictation pipeline](DICTATION_PIPELINE_GUIDE.md) |
| Use Desk windows and objects | [The Desk](WEB_DESK.md) |
| Select an atmosphere | [Places](ENVIRONMENTS.md) |
| Work in a Project | [Project Rooms](PROJECT_ROOMS.md) |
| Run a multi-step goal | [Programs](#programs) |
| Make or receive a phone-number call | [Calls](calls.md) |
| Understand the paired-phone path | [Phone](phone.md) |
| Fix a problem | [Troubleshooting](TROUBLESHOOTING.md) |

## Develop a thought

The product calls the editable record a **Note**. **Thought** is an older
domain term for the same refinement path. Open a Note and select **Develop
this thought** to open the Workbench. The Workbench displays the Note and
preserves the original text while you refine it.

The Note and Workbench can show these paths:

- **Ask AI** starts refinement for the Note when the local model is ready.
- **Add to note** adds your answer or a draft to the working Note.
- **Finish Thought** completes the refinement and keeps the working Note.
- **Resume refining** reopens a completed refinement.
- **Original kept** shows the captured source text. **Get Info** shows record details.

Read the answer before you add it. A reply is not a Note until you use the
save control. A Note stays editable after refinement.

### AI context

Attach context when the question needs more than the Note. The context can
include selected Notes, Meetings, Projects, decisions, or an **Everyday
context** prompt. Check the attached references before you send.

The Ask scope control (accessible label **About**) is a retrieval starting
point. It is not a blanket access boundary. An engine with permitted tools can
read other allowed Desk records when the request needs them. Project service
operations use the Project's narrower source scope.

Do not put credentials in a Note, Thread, or prompt. Select the named Settings
connection instead.

## Voice typing

Voice typing sends speech to the focused application.

1. Put the cursor in a text field.
2. Hold Right Option on macOS or Right Alt on Linux.
3. Speak.
4. Release the key.

These are the default keys. The **Control mode**, preview setting, and speech
engine decide whether text is delivered directly or shown for review. The
dictation journal records the transcript, delivery route, and result. It does
not prove that the target application accepted the text.

### When voice typing does nothing

Check the three macOS permissions in **System Settings > Privacy & Security**:

| Permission | Covers |
| --- | --- |
| Microphone | Audio capture |
| Input Monitoring | Global hotkey detection |
| Accessibility | Insertion into the focused application |

Grant permissions to the application that launches the hub. Restart that
launcher. Select **Re-check** in Speak. Linux needs an active GUI session and
can require clipboard paste when Wayland blocks direct insertion.

### Spoken language

Choose the speech language in **Settings** when the speech control offers it.
Use the language that matches the recording. A language mismatch can produce a
transcript even when its words are wrong.

### The wake word

The local wake-word extra is optional. Install it and configure the wake word
before you use it. A wake word can start capture. It does not grant permission
to insert text into another application.

### Punctuation and symbols

Speak punctuation words that the selected speech engine supports. Check the
preview before delivery when the sentence contains code, paths, or symbols.
Use the editor for exact source code. Dictation is an input path, not a code
parser.

### Clipboard token

When direct insertion is unavailable, use the clipboard route shown by Speak.
HoldSpeak can place the result on the clipboard for you to paste. A clipboard
result is not delivery into the target application. Check the target after you
paste.

## Speak

Speak is the voice-typing window. It shows capture state, speech readiness,
permission state, preview behavior, and the journal link.

### The Speak wing

The current Speak face is the **Talk** plate. Select **Talk** to start or stop
capture. The **Utterance** well also accepts typed text. **Types into** names
the target and **Try it here** runs a preview without typing into another app.
**Details** shows the diagnostic rows when builder tools are enabled.

Read the status before you speak. **ACTIVE** means the key listener is ready.
**BLOCKED** means a required permission is missing. **UNAVAILABLE** means the
listener did not start.

After a result, select **OK** or **Wrong**. **APPLIED** opens the corrections
that fired. **Wrong** opens **FIELD** with **TEXT**, **INTENT**, or **TARGET**.
Enter the correction and select **Teach**. A **TEXT** correction changes
words. **INTENT** and **TARGET** change routing.

### Teach a correction

1. Open a dictation journal row.
2. Select the correction control.
3. Enter the phrase and the desired text or route.
4. Save the correction.
5. Replay the earlier utterance when you want to check it.

A stored correction and a correction that fired are different results. Read the
next journal row to check whether it applied.

### The Journal wing

The Journal lists dictation runs on this device. **Search** and the source
filters narrow the rows. **Clear** removes the journal. A row can show what
HoldSpeak heard, what it delivered, the route, latency, and corrections.
**Replay** uses the stored transcript and returns **REPLAY · PREVIEW**. It does
not send text to another app. **Copy** copies the transcript or replay result.
**Delete** removes a row.

### The Learned wing

Learned lists stored corrections and their applied counts. Remove a correction
when it produces unwanted changes. A count is evidence of a recorded match,
not a quality score.

### Storage and privacy

Dictation storage and model routes have separate boundaries. A local speech
engine keeps input on its host. A configured endpoint or CLI can transfer its
prompt to that provider. Read the route and receipt for each run.

### Who owns the microphone

Only one active capture path should own the microphone. A meeting recorder,
browser capture, and voice typing can have different owners. Stop the other
capture when Speak reports that the device is busy.

### When capture goes wrong

| Symptom | Action |
| --- | --- |
| No key state | Check Input Monitoring or the GUI session. |
| No audio | Check Microphone permission and the selected device. |
| Words appear but do not arrive | Check Accessibility, preview mode, or clipboard paste. |
| Transcript quality is poor | Check language, speech engine, and background noise. |
| A correction did not apply | Read the journal row and compare the exact phrase. |

## The dictation pipeline for coding assistants

The pipeline can deliver a short spoken request to a coding assistant. It can
use project facts or an optional project context rewrite before delivery.

### Set up the pipeline

1. Open **Settings > Engines** and choose the speech and rewrite engines.
2. Set project facts in the project configuration when the template needs exact values.
3. Set optional project context files when a rewrite needs them.
4. Speak into the focused coding tool.
5. Check the journal and the target application.

Project facts are exact values from the configured `kb:` map. Project context
is separate optional material. Neither setting proves that a target coding
tool accepted the delivered text.

### OpenAI-compatible endpoints

An OpenAI-compatible endpoint is an inference route. Configure its URL, model,
and credentials in the supported Settings control. Check what data the
endpoint receives. Compatibility does not mean that the endpoint is local or
that it can use Desk tools.

### Project facts

Project facts supply exact template values. Keep them short and review them
when the repository or branch changes. A fact is not a source document and is
not a permission grant.

### Project context

Project context files can guide an optional rewrite. The rewrite engine and
its host can receive the context. Read the receipt before you treat the
rewritten text as delivered.

### Automation hooks for Claude and Codex

Hooks report an existing Claude Code or Codex session to HoldSpeak. They do
not turn a CLI inference engine into a coding-agent session. A coding-agent
handoff needs its own repository, branch, worktree, agent CLI, and authority.
Use [Coder integration](CODER_INTEGRATION.md) for launch and steering.

## Meeting mode

Meeting mode records or imports a Meeting, then runs configured intelligence.
Audio capture, transcription, model intelligence, and follow-up are separate
steps.

1. Open **Meetings**.
2. Select **Record** for a new capture, or **Import** for a supported file.
3. Select the meeting and check its transcript.
4. Choose an assigned intelligence job.
5. Read the result, source references, and job receipt.

The Meetings window accepts a file drop and opens its import form. The active
Desk does not provide a general file drop. See [Meeting mode](MEETING_MODE_GUIDE.md)
for audio and provider details.

Read the state before you choose an action. **REC**, **IMPORTING**, and
**TRANSCRIBING** mean capture work is active. **QUEUED** and **RUNNING** mean
intelligence work is pending or active. **RAN** means the run completed.
**OFF** means no summary ran. **FAILED** and **IMPORT FAILED** name a failure.
**NO TRANSCRIPT** means speech setup or capture is still missing. **Run
summary**, **Retry**, and **Open** appear only when their state supports them.

### The auto-run setting

Auto-run is a recording preference. It can start configured work after a
recording when its prerequisites are ready. Read the selected engine, job,
source scope, and receipt. A setting does not prove that a run completed.

### Where the model runs

The engine assignment names the model route and host. A local model, network
endpoint, cloud API, and CLI can have different data boundaries. Check the
receipt and egress indicator before you share a transcript.

### Named owners

Review named owners in the Meeting result. An extracted owner string is not a
People relationship. Use an explicit People alias when you want a known
relationship link. Meeting participants are not automatically linked.

## Proposals and review

HoldSpeak can prepare proposals from a Meeting or Project. A proposal is a
candidate result. It needs review before confirmation or an external effect.

### Proposals in the Room, Needs you and Today

The arrival and Project Room can show pending proposals. Select **Review N** or
the proposal row. Read its source, target, and requested action. Confirm only
when the proposal matches your intent.

### Review a meeting's outcomes

Read the transcript and the evidence links first. Check decisions, risks,
requirements, commitments, and action owners. A saved outcome is not proof of
organizational acceptance. Follow the authority process for the work.

### Suggested sources

Project Rooms can show suggested sources. A suggested source is not watched.
Select **Add** only after checking the provider, account, and source scope.
Select **Dismiss** when it does not belong to the Project.

## The steward's hand

The Steward evaluates observed Project work under a Project policy. Its scope
is narrower than whole-Desk Ask.

### The drafted update

1. Open a Project Room.
2. Select **Write update**.
3. Check the model chip and source references.
4. Correct unsupported facts.
5. Save or prepare the update only after review.

**Write update** prepares text. It does not send the update. A project-update
run has the Project service scope, source watches, policy, and run receipt.

### What a claim state means

A claim can be supported by a live source, changed since the last check, or
missing evidence. Read the source and time before you act. A model phrase such
as “confirmed” is not an authority decision.

### The health rows

Health rows summarize the Project's current observed state. Read the source
rows, last check, and failure reason. A blank or stale row does not prove that
the provider has no work.

### The reviewer nudge

The reviewer nudge identifies work that needs your review. It does not approve,
send, or schedule the work. Use the linked source and proposal controls.

## Prepared work: preparation, review, and the weekly update

Three prepared procedures ship: meeting preparation, decision and commitment review, and the weekly project update.
They are versioned descriptors in `holdspeak/services/recipe_catalog.py` that bind existing services.
A descriptor declares a limit only where one is real.
It reads a cap from the executing service rather than duplicating an unenforced number.

**None of the three fires on a schedule yet.**
This limitation applies to those prepared-procedure descriptors.
Ordinary Automations and scheduled recordings have their own supported triggers.
Read [Automation](AUTOMATION.md) for those paths.

A prepared result names its output, target, route, and next owner action.
It does not establish completed external work.

### Running one

The prepared-procedure catalogue is read-only.
Its APIs describe a procedure and compile a plan. They do not execute that plan.
Use the current feature that owns the result:

| Result | Current path |
| --- | --- |
| Meeting or 1:1 preparation | Open the person's preparation view in People and inspect the available brief. |
| Decision review | Open Ask, select decision evidence through the scope menu, and request a review. This is ordinary Ask. |
| Weekly Project update | Open the Project Room and select **Write update**. |

Inspect the sources and result before keeping or using the output.
Review any **Wrote** changes and **Prepared** actions.
Select **Send** only when the destination and exact content are correct.

### Finding them

Use **Today**, **Needs you**, Project Room **HISTORY**, Memory, or the source
record's receipt. Search can find a kept Note, Artifact, Thread, or Meeting.
A prepared item can remain pending until you send it or discard it through its
own control.

## Programs

A **Program** is a goal cut into steps. An agent can do each step, while the
owner keeps the decisions that affect scope, authority, and delivery.

1. Open **Programs** from **Go** or Search.
2. Select **New program** or choose **Templates**.
3. Define the goal and steps, then review the plan.
4. Select **Start** when the steps, **Runs on** host, and control level are
   correct.
5. Read each checkpoint and answer the **Your turn** item when the Program
   asks.

The Program window can **Park** a run, **Resume** it, add a step, and show
handoff notes and decisions. **Race** is available only where the service
allows parallel work. **Secure**, **Normal**, and **YOLO** are control
presets for the Program. Its step gates and Control level govern routine decisions and merge.
Core questions, held owner operations, and security or data-loss findings still return to you.
Read [Programs](programs.md) for the exact ladder and merge-gate choices.

Programs are different from the prepared-procedure catalogue above. The
catalogue contains read-only procedure descriptors; it is not an executable
Program list or a schedule.

## Reach

Reach exposes remote MCP access through a scoped credential. It is not the
same as opening the Desk in a browser.

### Turn remote access on

Open the Reach settings and read the bind address, transport, and expiry. Turn
it on only when a remote client needs it. Check the scope before you pair a
client.

### Issue a credential

Create a credential with the smallest required scope and expiry. Copy it only
to the intended client. HoldSpeak does not recover a secret that you lose.

### What a remote caller can do

`POST /api/mcp` refuses the owner's web token on a non-loopback request.
Remote MCP uses the scoped agent credential path.
Other HTTP routes have their own guards; the MCP refusal is not a universal network fence.


The credential and MCP policy decide which tools and records the caller can
use. A remote caller does not gain all Desk authority. Read the tool result and
receipt. People access has its own restriction.

### The overnight runner

An overnight run needs a configured trigger, engine or agent, source scope,
authority, and a running execution host. Read its receipt after the run. A
credential or saved recipe alone does not prove that it ran.

<a id="rhythms-where-it-runs-row"></a>
<a id="rhythm-s-where-it-runs-row"></a>
### Notices' Where it runs row

The **Where it runs** row names the host for a Heartbeat path. Check it against
the selected engine and destination. A saved host is not evidence of a
completed run.

<a id="the-arrival"></a>
## Today

The arrival shows current work, **Needs you**, unfinished Notes, a brief, and
recent Meetings. Select an item to open its owning surface. A badge tells you
that a source has state to inspect. It does not explain the state by itself.

### When a source was not observed

Read the source status and last check. “Not observed” can mean that the source
was not in scope, the provider was unavailable, or the run did not complete.
Do not treat it as proof that nothing changed.

## The clock

The clock contains calendar and recording controls. It does not replace the
Meeting record or a calendar provider.

### Connect a calendar

Use the Calendar settings flow and grant only the requested provider access.
Check the selected account and calendar. A linked calendar event can support a
People association only after your explicit link.

### Import from a screenshot

The current active Desk does not mount a general screenshot import. Use a
supported Calendar or Meetings import control when the current build offers
one. Do not treat a screenshot on the clipboard as an imported event.

### Armed recordings

An armed recording stores a schedule or event link for a future capture. Check
the time zone, source event, device, and recorder state. Armed does not mean
recorded.

### Auto-record

Auto-record can use a configured calendar mode. Check whether it is **Off** or
configured for calendar meetings. Read the recording receipt and Meeting
record after the event.

### The week and the brief

The weekly view gathers current records and configured pages. It can show
source references and missing inputs. A brief is preparation. It is not a
decision, a People score, or a sent message.

## Connect your tools

Open **Settings > Connections** to configure GitHub, Jira, Confluence, a
calendar, or another supported provider. Check the account and source scope.
The provider's credentials remain under its configured boundary.

Connectors read only the data their service supports. A successful connection
does not add every provider record to a Project. Use [Project Rooms](PROJECT_ROOMS.md)
to select sources and Watches.

## New Project

1. Select **Desk > New Project**.
2. Enter an outcome in **Project name**.
3. Paste repository, Jira, or Confluence links in **Paste source links**.
4. Select **Check sources**.
5. Review the source rows and select **Create Project**.

The Door can create a blank Project. It shows **NO SOURCES · BLANK PROJECT**
when no source is selected. A source check is not a Watch. The Project Room
creates Watches only for the selected source and templates.

## Project Room

The Project Room has **ROOM** and **HISTORY** wings. Read **NEEDS YOU**,
**PLAN**, **SOURCES**, **SINCE YOU LOOKED**, and **DECISIONS & COMMITMENTS**.
Use **Add source**, **Pause**, **Resume**, **Remove**, and suggested-source
**Add** or **Dismiss** according to the source scope.

The Ask field is **Ask this project**. Choose an answer or brief result and
check the model chip. **Write update** prepares a Project update. A Project
Room run is narrower than whole-Desk Ask. See [Project Rooms](PROJECT_ROOMS.md).

## Settings

Use Settings to choose **Engines**, **Accounts**, **Wallpaper**, **Meetings**,
**Notices**, **Calls**, **Agents**, and other configured options. Search for a
setting by its current label. Read the state after you save it.

The browser keeps local atmosphere preferences. The hub owns Desk window state
and records. Do not describe a browser cache as the shared Desk store.

<a id="rhythm"></a>
## Notices and the Heartbeat

**Notices** hosts the Heartbeat controls. A Heartbeat sweep needs a trigger,
source scope, executor, authority, and running host. Check **Where it runs**,
its policy, and its receipt. Cadence and Heartbeat are different paths.

Do a manual trial before you enable a recurring path. A saved schedule does not
prove that the next sweep will run.

## Engines

Engines lists model runtimes, endpoints, and supported CLI routes. Assign an
engine to each capability that you use. Check its host and egress.

An installed CLI can answer a Desk request through its provider. That does not
make it a coding agent. A coding-agent handoff launches a separate session in
a repository worktree. A persona supplies instructions. It does not execute
by itself.

Select **Test** to send a real request. Read the result and receipt. A cloud
check can incur cost.

## People

People is a protected surface for relationship context. It does not rank
people, infer relationship health, or link meeting participants automatically.

Select **Add person** to create the local store on first use. Choose **Direct
report**, **Peer**, or **Extended relationship**. Use the **Context** lens for
Notes, linked Projects, links, calendar series, and **Names in meeting notes**.

People can show **Leader private** and **Shared** note visibility. A locked or
missing store reports its state. It does not silently become an empty roster.

### Link the 1:1 series

1. Open a relationship and select **Context**.
2. Select **Link calendar event**.
3. Choose the series and check the label.

Select **Unlink** to remove it. A title match can show **SUGGESTED**. A
suggestion is not a link. One series can belong to one relationship.

### The Prep brief

The 1:1 preparation view can read open commitments, agenda backlog, grounding
notes, linked Meetings, decisions, and unlinked Meetings in the chosen window.
It stores no generated brief. It does not make an employment decision.

### The 1:1 card

Read the relationship's Notes, open commitments, linked Projects, and source
links. Use **Mark satisfied** only with completion evidence. Counts in History
describe follow-through records. They are not performance scores.

### Map an owner string to a person

1. Open **Context**.
2. In **Names in meeting notes**, enter the owner string.
3. Select **Add**.

Comparison ignores case. Remove an alias when it is wrong. HoldSpeak rejects
empty, reserved, or duplicate aliases. It does not guess a person from a voice
or meeting participant.

### People in the Room

A Project can link an existing relationship or show a People reference. The
Room does not copy confidential People notes into Project sources. Open People
to read protected context.

### The chief-of-staff brief

The brief can combine permitted Project work and People shared intent. Check
the source and access policy. People content remains in its protected store.

### The dev keystore

People MCP access is controlled by `HOLDSPEAK_MCP_PEOPLE_ACCESS`. Use `read` or
`off` when the client does not need default write access. Agents launched by HoldSpeak do not write People records. Only shared intent crosses MCP.

<a id="threads"></a>
## Ask

Ask and Thread share one active window.
When the first answer lands, the exchange is saved as a Thread.
Follow-up questions continue it in place.
The hub retains turns, references, message parts, and tool results under the applicable execution path.

<a id="start-a-thread"></a>
### Start a question

1. Open **Ask AI** from **Go** (the window label is **Ask**).
2. Select sources through the scope control (accessible label **About**) when
   needed.
3. Enter your question.
4. Select the send control.
5. Ask a follow-up after the answer returns.

Use **Recent** to reopen a retained conversation. Select its first row or press
**⌘N** to start another conversation.
The current Ask window does not offer the older Thread mode tabs.

<a id="the-composer"></a>
### The answer

Enter text in the follow-up box or use its microphone.
Use the scope control (accessible label **About**) to choose starting
context, rather than the parked Thread composer's at-sign attachment
interface.
Speech input and speech output are separate capabilities.
Check the engine and any named refusal before repeating a failed request.

### Branch, keep, and search

The active answer controls include **Make it a task**, **Save as note**, **Copy**, and **Send…** where applicable.
Ask opened from a Note can offer **Add to note**.
These create or change a record in addition to the saved conversation.
Search and **Recent** can return to retained work.
The current window does not expose **Fork from here** or a **Keep**/**Bin** exchange decision.
Thread branch and keep operations remain available through the API.

### People boundary

Ask and its tools follow the applicable People read policy.
Use the protected People surface for confidential relationship editing.
Interview's People section is a separate service handoff.
A saved Thread or persona cannot grant itself People write or owner authority.

<a id="the-thread-has-hands"></a>
### Ask has hands

A compatible engine can read permitted records, write Desk work, and prepare a send.
The answer shows **References**. The retained trace can also expose
source references, writes, and prepared actions fields.
A prepared send waits for your **Send** press.
A held tool call offers **Allow once** or **Deny**.
A persona supplies instructions and does not grant a tool permission.

<a id="thread-modes-slash-commands-and-the-call"></a>
### Modes

The retained Thread API supports modes such as Draft, Plan, Project, and Interview.
Their prompts and tool palettes shape that service's turns.
The active Ask window does not expose a mode picker.
Read [Agents and Threads](AGENTS_AND_THREADS.md) and [Interview](INTERVIEW.md) for the service contracts.

### Saved prompts, guardrails, annotations

The Thread services retain prompt, guardrail, and annotation capabilities.
The older controls live in the parked Thread interface.
The current Ask uses its question, source selection, and permitted tools.
Instructions and annotations do not grant execution authority.

### Slash commands

Slash-command controls belong to the parked Thread composer.
The current Ask does not present its `/mode`, `/todo`, `/keep`, `/fork`, or `/compact` menu.
Use active answer controls for tasks and saved Notes.
Programmatic clients can use the corresponding Thread API operations when authorized.

### The Call

The repository retains Thread call-mode services and the parked Thread interface.
The current Ask does not provide a **The Call** control.
Use its microphone for a spoken question.
That input path does not establish a two-way spoken call.

## Schedule a recording

Use Meetings **Coming up** or the schedule control when Calendar is configured.
Choose the event, time zone, and recording mode. An armed schedule is not a
recording. Read the resulting Meeting and receipt after the event.

## Project memory

Open **Memory** for **What I owe**, **What changed this week**, **Ask your
desk**, and **RAW** recall. Open a Project scope to read its standing pages.
Standing pages are read-only at the time of display and show only sentences
whose cited inputs remain live.

Meaning search is separate. Turn it on in Settings before it can index. People
content does not enter normal Project or Desk memory.

## Companions

A paired companion uses the hub's services from another device. Pairing does
not grant all authority. Check its credential, scope, and receipt. A companion
can see the same records only where the hub permits it.

For phone-number calls and the paired-phone service, read [Calls](calls.md)
and [Phone](phone.md). A configured Calls line can work without a delivered
Phone app. The pairing service is a future client path until an app is
delivered and enrolled; do not treat a pairing QR or token as proof that a
phone client is connected.

## Using the Desk

Open **Today**, **Needs you**, **Memory**, Projects, or People from **Go**.
Select an object to open its window. Use **Object** for object-specific verbs.
Use **Window** to close, arrange, zoom, raise, cycle, or send back.

The hub owns state for hub-backed Desk windows. The browser has a local
first-paint cache. Some transient views, including Ask, are view-specific. A
second browser can change the same hub-backed window and cause a stale revision
response. Read the receipt before you retry a window action.

## Mission Control on the Desk

Mission Control collects sessions, deliveries, and receipts that need review.
Open a row to inspect the owning surface. It does not replace the agent
session, Project Room, or external provider.

### Pull request receipts

Read the repository, branch, revision, checks, and destination in a pull
request receipt. A green check is not a code review. Open the agent or
repository result before you merge.

### Follow a pull request through

1. Open the Project or agent row.
2. Read the source pull request and current check state.
3. Open the coding-agent session when it needs input.
4. Review the delivered work and receipt.
5. Use the repository's normal review and merge process.

## Steer a session from the Desk

The Desk can show a coding-agent session and its terminal output. A session
needs a configured agent CLI, repository, worktree, and authority.

### Send keys, any pane, any machine

Use the supported session control to send text or a key. Check the target pane,
host, and session before you send. A steering action is not a code review and
does not confirm that the agent followed it.

## The gate

The Gate shows a held operation that needs a decision. Read the operation,
scope, target, and expiry. Select **Allow once** or **Deny** for that request.
Gate armed is a policy state. Gate installed but idle is not a held request.

## Session receipts

A receipt identifies the operation, route, host, source scope, authority basis,
attempt, outcome, and time. Use it to tell a prepared action from a sent
action, and a started agent from a finished agent.

## Ground a run on the rails

Attach the source records that matter. Ask, Thread, Project update, and agent
briefs can have different source scopes. Read the references in the result.
Grounding shows what the model received. It does not guarantee that the model
used each source correctly.

## Privacy

HoldSpeak runs its hub on your machine by default. Data can still leave the
machine through a configured endpoint, cloud API, CLI provider, connector,
remote client, or outbound destination. Check the engine, host, egress, and
receipt for the operation.

People uses a separate encrypted local store and has separate MCP policy.
Project sources use provider credentials and selected scope. A local browser
cache is not the shared record store. Read [Security & Privacy](SECURITY.md)
and [People security](PEOPLE_SECURITY.md) for the full contracts.

## Troubleshooting

| Problem | Action |
| --- | --- |
| The Desk does not load | Check the hub URL and read the setup state. Select **Retry** when it is offered. |
| Voice typing does nothing | Check microphone, Input Monitoring, Accessibility, the hotkey, and the GUI session. |
| Ask has no answer | Check the engine, assignment, source permission, and held tool request. |
| Ask looked at the wrong scope | Check **About** and Project scope separately. About is only the retrieval start. |
| A Thread lost its draft | Check the same browser tab. An unsent draft is not a saved Thread turn. |
| People is empty or unavailable | Read the People state. A locked store is not an empty roster. Select **Try again** when offered. |
| A Project Room has no source work | Check provider account, source scope, Watch state, and last check. |
| A model result is not useful | Check its source references, assumptions, engine host, and prompt. |
| A prepared send did not leave | Review the target, then select **Send**. |
| A recurring job did not run | Check trigger, scheduler, host, policy, engine, and receipt. |
| A coding agent did not start | Check repository, branch, worktree, agent CLI, and authority. |

## See also

- [Getting Started](GETTING_STARTED.md): installation and first value.
- [The Desk](WEB_DESK.md): navigation and active controls.
- [Use cases](USE_CASES.md): jobs, results, and failure boundaries.
- [Interview](INTERVIEW.md): context and suggestion flow.
- [Project Rooms](PROJECT_ROOMS.md): sources and Project-scoped runs.
- [People integration](PEOPLE_INTEGRATION.md): relationship boundaries.
- [Glossary](GLOSSARY.md): product terms.
