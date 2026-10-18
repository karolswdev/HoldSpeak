# Engines: betterment design

Status: draft for the owner. Inputs: `MODEL.md` (the code map, 2026-10-17).
The face was read in code, not walked live; slice E0 in `RECIPE.md` takes
the shots before any face slice ships.

## 1. The job

Owner, 2026-10-17: "I thought we wanted to have simple integration with
various engines, e.g. OpenRouter, Claude Code CLI (like -p), Codex CLI, and
so on. How come those engines aren't assignable too? The local llama.cpp
and the OpenAI LAN endpoints are a good start, but so are other things."

He opens Engines to say *this kind of work runs on that thing I already
have*. What he already has: a model on his LAN, an OpenRouter account, a
Claude Code subscription and a Codex subscription. He closes it when each of
those is in his list, each one shows that it works, and each kind of work
(meeting summaries, answers, drafts, automations) points at the engine he
chose.

## 2. What it is today

From the code (`MODEL.md` §4); live shots come in E0.

| Step of the job | What happens today |
|---|---|
| Find the place | Four names: "Engines" in Settings, "Runs on" on the window, `/models` in the address, "Concierge" in the code. |
| Add Claude Code or Codex | Not possible. They show as INSTALLED and SIGNED IN only on the first-run Agents card, never in the engine list. |
| Add OpenRouter | About 6 presses and a drag. He must know the URL `https://openrouter.ai/api/v1`. Check takes the alphabetically first of several hundred models. There is no model picker. Six OpenRouter presets ship in the catalog, but the face never shows them. |
| Add a second OpenRouter model | It seems to replace the first, because one engine is made per host. |
| Add Anthropic | Shows NOT SUPPORTED YET, with no next step. |
| Point one job at one engine | The face assigns whole groups only, by dragging a wire. Single jobs ("summaries on OpenRouter, everything else on the LAN") need MCP. |

## 3. Why it fails

1. **The concept is too narrow.** In the code, an engine is "a model file or
   an OpenAI-style server". To him, an engine is *anything that takes a
   prompt and gives back text*. A CLI he is already signed in to is the
   cheapest engine he has, and the product cannot see it.
2. **"Add an engine" means "type a server address".** A service is reduced
   to a URL he must already know. A program has no way in at all.
3. **The product hides what it already knows.** It knows his CLIs are
   installed and signed in, and it ships OpenRouter presets, but it shows
   neither.
4. **Choosing the model is skipped.** Taking `models[0]` gives him a model he
   did not pick.
5. **The assignment face is a diagram, not a list.** A wire you drag reads as
   a demo. "Which engine does my meeting summary use?" should be a row that
   he reads and changes in one press.

## 4. The design

### The concept

**An engine is anything that takes a prompt and gives back text.** He sees
five kinds, named by where they are, not by protocol:

| Kind (as he sees it) | Examples | Where the prompt goes |
|---|---|---|
| **An agent on this Mac** (new) | Claude Code, Codex, pi, Gemini CLI | the agent's vendor (ANTHROPIC, OPENAI, …), or his LAN for pi on his model |
| **A service** | OpenRouter, OpenAI, Anthropic, Gemini | the service host |
| **A server on my network** | LAN llama.cpp, vLLM, Ollama, LM Studio | his network |
| **A model on this Mac** | a downloaded GGUF/MLX file | nowhere (this Mac) |
| **Another HoldSpeak** | a mesh node | that node |

### The words

- One name everywhere: **Engines**. The window title, the Settings row, the
  palette and the docs all say Engines. "Runs on" and "Concierge" stop being
  words the user sees.
- The assignment list is called **What runs where**.
- Rows use plain job names: Meeting summaries, Live meeting notes, Answers
  (Ask), Thread, Thoughts, Drafts and updates, Automations, Background
  memory, Dictation clean-up, Speech to text. The default row is
  **Everything else**.

### The layout (desktop, one window, no modal)

```
┌ Engines ───────────────────────────────────────────────────────────┐
│ YOUR ENGINES                                                       │
│  ◉ LAN Qwen 3.8 27B        server on my network   READY   192.168… │
│  ◉ Claude Code · sonnet    agent on this Mac      READY   ANTHROPIC│
│  ◉ OpenRouter · gpt-5.x    service                READY   OPENROUTER│
│                                                  [ Add an engine ] │
│                                                                    │
│ FOUND ON THIS MAC                                                  │
│  Codex · signed in                                         [ Add ] │
│                                                                    │
│ WHAT RUNS WHERE                                                    │
│  Everything else         LAN Qwen 3.8 27B          ▾   [ Try it ]  │
│  Meeting summaries       OpenRouter · gpt-5.x      ▾   [ Try it ]  │
│  Answers (Ask)           Claude Code · sonnet      ▾   [ Try it ]  │
│  Automations             Everything else           ▾               │
│  ▸ 6 more                                                          │
└────────────────────────────────────────────────────────────────────┘
```

- **Your engines**: one row for each engine: name and model, kind, state,
  and where the prompt goes (the egress chip). Pressing a row unfolds it in
  place: change model, Check again, Remove.
- **Found on this Mac**: installed, signed-in CLIs and running local servers
  that are not in the list yet. One press on **Add** adds one. The section
  is absent when nothing is found (no counters of zero).
- **Add an engine** unfolds in place into five tiles, one for each kind.
  Choosing a tile asks only what that kind needs:
  - *An agent on this Mac*: the CLIs this Mac has, then pick the model or
    keep the CLI's default. Missing ones show how to install them, in one
    line.
  - *A service*: named tiles (OpenRouter, OpenAI, Anthropic, Gemini). Paste
    the key, then a **model picker** with search, with the catalog presets
    on top. No URL to know.
  - *A server on my network*: Find on LAN, or type an address. Then the same
    model picker.
  - *A model on this Mac*: the existing download fold.
- **What runs where**: one row for each job, with a picker of his engines.
  "Everything else" is the default; a row that inherits says "Everything
  else". Groups collapse; **▸ 6 more** expands to every job. **Try it** runs
  the job's sample on the chosen engine and shows the answer under the row.
- **Automations** (see `../workbench/DESIGN.md`): the *with* line of every
  automation uses the same picker of the same list.

Phone (393): the same three sections stacked. A picker opens as a sheet in
the window, not as a modal.

### What each press does

| Verb | Result |
|---|---|
| Add (found) | The engine is in Your engines with its state checked. |
| Add an engine → tile | Unfolds that kind's two or three fields. |
| Check | Lists the service's or server's models in the picker. It never picks one for him. |
| Use (in the picker) | Saves that model as an engine. A second model on the same host is a second engine. |
| Picker in What runs where | Assigns that job at once, with Undo in the foot. |
| Try it | Runs the sample and shows the text and time, or the error in words. |
| Remove | Removes the engine. Jobs that used it say "Everything else", in words. |

### What is removed or parked

- The drag-a-wire switchboard is parked behind the existing RAW/debug
  affordance; What runs where replaces it.
- "NOT SUPPORTED YET" states with no next step are removed. A kind we cannot
  run is not shown.

### The desk's tools

An agent on this Mac, and any engine whose Check reports tool support, gets
HoldSpeak's own tools when it runs work: it may read the desk and write on
it, and it never sends or changes settings. See `../mcp/DESIGN.md`. The
engine row says which engines can use tools.

### Rules the engine kinds keep

- **The prompt goes where the chip says.** An agent on this Mac is never
  labelled THIS DEVICE: its prompt goes to its vendor.
- **HoldSpeak never reads or copies a CLI's sign-in.** It runs the CLI as
  the owner, with tools off or read-only, in an empty temp folder.
- Speech to text stays on this Mac, and Dictation clean-up cannot use an
  agent (its latency limit). Their pickers list only engines that can do
  the job.
- Background memory does not default to an agent CLI, because each call is
  a new process and counts against his subscription.

## 5. Decisions for the owner

1. **Replace the drag switchboard with the What runs where list?**
   Recommended: yes. Park the switchboard behind RAW.
2. **Anthropic API as a service:** use Anthropic's OpenAI-compatible
   endpoint first, and add a native adapter only if it fails. Recommended:
   yes. Claude Code covers Claude for him from slice E1 onwards in any case.
3. **Cost limits are his, and are set on the engine.** No hard-coded cap.
   (The $0.10 in the first draft was copied from `agent_summarizer.py:158`,
   a cap for summarizing one short coding session. It was wrong here.)
   - Each engine row has **Spend limit per run**, with *No limit* or an
     amount. An automation can set its own limit, which overrides the
     engine's.
   - Where the CLI can enforce a limit (Claude Code `--max-budget-usd`), we
     pass it. Where it cannot, we say so on the row ("Codex cannot limit
     spend") and do not invent our own guard (Tenet 1).
   - Every result shows what it cost when the CLI reports it (Claude Code's
     JSON output). The Engines row shows the total for today and this week.
   - Recommended default: **No limit**, with the cost shown on each result.
     The MCP map (`../mcp/MODEL.md`) will confirm whether limits apply to
     subscription logins.


## 6. How we know it worked

On an empty Engines window, he:

- adds Claude Code in **2 presses** (it is under Found);
- adds OpenRouter with the model he chose in **at most 5 presses and one
  paste**, without typing a URL;
- points Meeting summaries at OpenRouter and Answers at Claude Code in
  **2 presses each**;
- presses Try it on Answers and reads a real answer from Claude Code.

All of this happens in one window, with no doc open and no question to us.
