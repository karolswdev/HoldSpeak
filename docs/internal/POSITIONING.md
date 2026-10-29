# HoldSpeak positioning canon

The owner's direct documentation brief of 2026-10-29 names HoldSpeak an **agentic-first, web-based AI operating system**.
That brief supersedes the older dictation-first lead for the README and core documentation.
Voice typing and meetings remain first-class flows within the broader product.
This refresh does not amend the Constitution or add a new implemented capability.

The [Constitution](CONSTITUTION.md) and its Seven Tenets remain supreme.
The first user's jobs are those of a Senior Software Architect with reports.
User documentation follows [DOCS_STYLE.md](DOCS_STYLE.md) and states the current implementation and its limits.

## The one-liner

> **An agentic-first, web-based AI operating system for your work.**

Expanded form:

> Bring notes, meetings, projects, people, and coding agents onto one Desk.
> Ask it to find context, prepare work, and act through tools.
> Hand a task to a coding agent, or configure an Automation to do the job again.

### Decision 1: the lead angle is the agentic Desk

The Desk is the operating surface.
Saved context, conversations, tool use, delegation, and recurring work form the product story.
Do not reduce it to a voice utility or imply that a chat answer alone completes a task.

The former “one copilot, two modes” lead is historical.
A guide can focus on dictation or meetings without treating those two inputs as the product boundary.

### Decision 2: the first audience leads projects and people

Lead with a concrete job: develop an idea, review a meeting, prepare a decision, delegate implementation, or follow through.
Developer references can assume repository and shell knowledge.
User procedures still need clear starts, prerequisites, actions, and results.

### Decision 3: comparisons require current evidence

A named comparison is optional, and it requires dated, checked evidence for both products.
Credit the other tool's strengths and state HoldSpeak's limitations beside its claims.
Do not retain a stale competitor table to satisfy an older presentation rule.

## The pillars

1. **One operating surface.** Objects, drawers, windows, menus, and the dock connect work through a shared Desk framework.
2. **Context that carries into work.** Notes, Meetings, Projects, decisions, and Memory can supply grounded answers and execution inputs.
3. **Tools and delegation.** Suitable engines can use permitted Desk tools. Coding handoffs start separate repository sessions with a brief and worktree.
4. **Recurring work with retained results.** Automations define sources, trigger, executor, review choice, and output. Results expose what the run did.
5. **Local ownership and explicit execution choices.** The hub stores work locally. Model engines, connectors, CLIs, and outgoing destinations have distinct boundaries.
6. **Inspectable outcomes.** Sources, writes, prepared actions, run states, and Receipts distinguish intent from execution.

These pillars are narrative categories, not claims that every combination is supported.
Each guide checks its path against the current service, control, and recorded result.

## The web surface (the Desk OS)

The Desk is the main browser surface of a local hub.
Tools open in the common window framework rather than creating separate feature worlds.
The active React Desk, its current application registry, and its service-backed windows define the implementation.
The parked spatial Floor and earlier visual treatments are historical.

The surface presents current work through Today and Needs you, domain objects, Projects, agent sessions, and Programs.
Programs coordinates multi-step work and its gates. Calls and Phone provide configured voice and attention paths.
Ask can read context and use tools when its assigned engine supports that path.
**About** starts retrieval and does not grant or define a general access boundary.
A specific service scope can enforce narrower reads and writes.

The current browser opens Ask where the older separate Thread window was used.
Saved Thread records and their APIs remain distinct from the browser host that presents a request.
Use [WEB_DESK.md](../WEB_DESK.md) and the active source for procedures.

## The competitive frame

HoldSpeak spans a browser workspace, retained context, model tools, coding-agent coordination, and recurring work.
Describe those concrete connections before using a broad category label as evidence.
The product is pre-alpha, depends on configured engines and host integrations, and does not support Windows today.
A local process can use a cloud provider. Local storage does not make every operation local.

## Canonical feature names

One name per surface, used identically in every user-facing doc. The
left column is the name; do not alternate with the synonyms.

| Canonical name | Not |
|---|---|
| Desk | "the dashboard", "the runtime page" |
| Meetings (the mode + its nav label) | "History", "the history tab" |
| Go (the application menu) | "Studio", "the advanced tier" |
| voice typing | "basic dictation", "simple mode" |
| the dictation pipeline | "intelligent typing", "DIR" (user-facing), "smart dictation" |
| target profiles | "destinations", "apps" |
| the dictation journal | "the history tab", "the log" |
| the correction memory | "the memory", "corrections store" |
| the learning digest | "What HoldSpeak learned" is its on-screen title; "the digest" after first use |
| replay | "re-run", "retry" |
| voice commands | "macros", "voice macros" |
| activity pre-briefing | "nudges" (the cards are "nudge cards") |
| meeting intelligence | "meeting AI", "intel" (user-facing) |
| meeting plugins | "analyzers", "extractors" |
| actuators | "actions" (an actuator *proposes* an action) |
| meeting aftercare | "follow-up panel", "next moves" |
| meeting import | "upload", standing alone |
| the archive | "/history" is the route; the surface is "the archive" |
| desktop presence | "the HUD" after first use is fine |
| Qlippy, the mascot | "the assistant", "the agent" |
| the spoken-symbol dictionary | "custom symbols", "symbol macros", "vocabulary" |
| the spoken language setting | "language mode", "locale" |
| the wake word | "hotword", "voice activation" |
| the armed window | "listening window", "wake session" |
| Send to Slack | "Slack integration", "Slack connector" (user-facing), "Slack export" |
| AIPI-Lite | "the companion device" after first use |
| agents (tailored personas you author) | "bots", "assistants" |
| coders (live coding sessions awaiting you) | "agents" for this concept, "companions" (the word is retired: an agent is a persona you author; a coder is a live Claude or Codex session) |
| the iPad app | "the companion", "the companion app" |
| Interview (repeatable Thread mode) | "the onboarding wizard" for the entire capability; distinguish the Thought Workbench Interview pane |
| Note (editable work on the desk) | "Thought" for the same record |
| Wallpaper (Settings background picker) | "Places", "Change places", "Environments" for this setting |
| Accounts (Settings connections) | "Connections" for this setting |
| Settle in (temporary quiet Desk view) | "saved focus layout" |
| Threads (multi-turn desk conversations) | "chat", "chat app", "PersonaChat" |
| Automations (the watch/reaction surface) | "event triggers", "webhooks", "watches" (except the Project-scoped Watches of Project Rooms) |
| Watches (Project-scoped) | "event triggers", "monitors", "subscriptions" |
| Resourceful (overnight bounded maintenance) | "maintenance mode", "idle work", "overnight tasks" |
| Engines (Settings model choices) | "Runs on", "the Concierge", "model setup wizard" |
| the arrival (the desk's home screen) | "the Chair Door", "the board", "the dashboard" |
| Speak (the voice-typing window) | "DictationCore", "the cockpit", "the voice panel" |
| Meetings (the meetings window) | "HistoryCore", "the history page" |
| needs you (the cross-project headline) | "pending items", "action required", "to-do" |
| the Heartbeat (the unattended sweep) | "the pulse", "the poller", "background sync" |
| the sweep (one Heartbeat evaluation pass) | "the tick", "the poll", "the check" |
| Rhythm (the Settings module for the Heartbeat) | "cadence settings", "heartbeat config" |
| the shade (the system pull-down) | "the tray", "the notification panel", "the dropdown" |
| Run summary (the verb on an OFF meeting) | "process", "analyze", "run AI", "Run intelligence" |
| a proposal (an extracted decision or action item awaiting Confirm) | "suggestion", "recommendation", "finding" |
| Confirm (the verb that commits a proposal) | "accept", "approve", "apply" |
| the loop (capture to confirmed decision) | "the pipeline", "the workflow", "the auto-intel flow" |
| a suggested source (a repo or issue key mentioned in a transcript) | "a recommendation", "a detected source", "an inferred source" |
| the 1:1 card (the People Prep lens before a meeting) | "the person card", "the prep card", "the contact card" |
| People in the Room (the PEOPLE section in a project Room) | "room contacts", "project members", "room people section" |
| the steward's hand (the steward's bounded external actions) | "steward actions", "the hand", "steward effects" |
| a reviewer nudge (a proposed comment on a waiting PR) | "a ping", "a reminder", "a review request", "a poke" |
| the health rows (the Room's HEALTH signal section) | "the health dashboard", "the health panel", "the status board" |
| the drafted update (the model-rewritten weekly update) | "the AI update", "the generated update", "the smart update" |
| Reach (remote access over Streamable HTTP) | "remote mode", "the remote transport", "the listener" |
| a scoped credential (palette + TTL, shown once) | "an API key", "an access token", "a remote token" |
| the REMOTE badge (the fourth egress state) | "the remote chip", "the network badge", "the external badge" |
| the overnight runner (the .43 client script) | "the cron job", "the scheduled runner", "the background agent" |
| the Confluence connector (blog posts + pages by ID) | "the wiki connector", "the Confluence integration", "the Confluence plugin" |
| the clock (the calendar on the desk) | "the calendar view", "the schedule", "the planner" |
| the WEEK strip (the arrival's day-token row) | "the week bar", "the calendar bar", "the day pills" |
| an event-born recording (auto-created from a calendar event) | "a calendar recording", "an auto-recording", "a scheduled capture" |
| the meeting watch (the Room's meeting Watch source) | "the meeting tracker", "the meeting monitor", "the meeting feed" |
| the weekly brief (the full-week summary in Rhythm) | "the week report", "the weekly digest", "the week-in-review" |
| the Speak wings (Speak, Journal, Blocks, Learned) | "tabs", "panels", "sections" |
| a text correction (a heard phrase paired with the said phrase) | "a spelling fix", "a vocabulary entry", "a find and replace" |
| a routing correction (an intent or target correction) | "a route fix", "a redirect", "a reroute" |
| the Learned wing (the correction memory on the face) | "the Memory tab", "the corrections table" |
| APPLIED (the chip where a stored rule fired on a run) | "corrected", "learned", "fixed", "nudged" |

## Voice rules (the editing standard for every user-facing doc)

The controlled-English policy is [DOCS_STYLE.md](DOCS_STYLE.md), using
ASD-STE100 Issue 9 as its language reference. The rules below continue to
govern product voice and names. [DOCS_TERMINOLOGY.md](DOCS_TERMINOLOGY.md)
records the domain terms used with that policy.

- **The humanizer standard applies** (the vendored skill): no AI-vocab
  (delve, seamless, leverage, robust, comprehensive, supercharge…), no
  rule-of-three padding, no negative-parallelism tics ("it's not just X,
  it's Y"), plain copulas over "serves as / boasts", active voice.
- **No em or en dashes in prose.** Use periods, commas, colons, or
  parentheses. Code blocks and quoted UI strings are exempt.
- **The honesty bar:** every claim is backed by a shipped capability a
  guide or test can point to; superlatives without proof points do not
  ship; limits are stated next to the strengths they qualify; comparisons
  credit the other tool.
- **Disclose egress at the act.** The owner's 2026-10-25 direction removes host, address, and scope chips from ordinary working rows, toolbars, and status bars. Disclosure belongs in Send previews, Destinations, Engines, Accounts, Setup, and the Door. Reference docs explain actual execution boundaries without promising a badge on every working surface. The current UX canon owns this rule.
- **Ledes sell the why.** Every guide opens with one or two sentences on
  why the feature exists and what the reader gets, before any mechanics.
- **Developer register.** Direct, technical, unafraid of a config snippet;
  never corporate, never breathless.

## Maintenance

Recheck any named comparison at release-readiness review.
Keep the product lead aligned with the owner's current brief and the implemented flows. The canonical-name table grows one row per new
user-facing surface, in the phase that ships it.
