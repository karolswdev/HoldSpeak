# Calls

You can call HoldSpeak from your phone. You speak, and HoldSpeak does the work on your desk. It tells you what it did. It asks you before it sends something.

HoldSpeak also calls you when you press **Call me**.

## How it works

Two programs work together. One holds the line, and HoldSpeak does the work:

- **The Line** is HoldSpeak's own phone line. It runs on your Mac or on a machine on your tailnet. Read [The Line](#the-line).
- **ai-phone** can hold the line in place of the Line. It hears your words and speaks the answers. It runs on your Mac. Get it at <https://github.com/oxnw/ai-phone>.
- **HoldSpeak** does each turn of the call. It uses the tools of your desk.

The model that thinks runs on your engine. The default is your home engine over Tailscale ("Home engine over Tailscale"). Settings ▸ Engines ▸ **Phone calls** can change it.

**Settings ▸ Calls ▸ Line ▸ Adapter** selects the Line or ai-phone. ai-phone needs a Mac with Apple Silicon. It does not run on Linux. Your home engine can be on Linux.

## What a call can do

| HoldSpeak does it at once | HoldSpeak asks you first | HoldSpeak does not do it on a call |
|---|---|---|
| Read your desk, meetings, people, projects, decisions, memory and Jira | Send a prepared send | Change a setting |
| Write a note | Post a nudge on GitHub | Change an engine or an account |
| Add a task | A desk change that your control mode holds | Confirm a decision for you |
| Propose a decision | | Call another person |
| Prepare a send | | |

When HoldSpeak asks, it says what will go and where. Say "yes" to let it go. Say "no" to stop it. You can also press **Yes** or **No** in the Calls window.

After each turn, HoldSpeak tells you what it did: "Done: added a task: Nudge Tomás about the runbook."

At the end of the call, the call is a note on your desk. The note has all the words of the call. Your passphrase is not in the note. If the call was about a project, the note goes into that project.

## Who can use your line

1. Your number. Put your number in **Settings ▸ Calls ▸ Allowed numbers**. Then only that number gets to the passphrase. If the list is empty, all callers get to the passphrase.
2. Your passphrase. HoldSpeak asks for it at the start of each call. If you do not say it correctly two times, HoldSpeak ends the call. If you did not set a passphrase, HoldSpeak ends each call.

Caller ID is not proof of who calls. The passphrase is the key.

## Set up calls

Do these steps one time. **Settings ▸ Calls** shows each step and its status.

1. Install ai-phone on your Mac:

   ```bash
   git clone https://github.com/oxnw/ai-phone.git ~/dev/ai-phone
   cd ~/dev/ai-phone
   ./scripts/install.sh
   uv run ai-phone setup
   ```

   Setup downloads the speech models. This can be some GB.

2. In setup, choose these items:
   - **Receive and place calls**.
   - The brain: **OpenAI-compatible**, at `http://100.118.33.80:8080/v1`, model `qwen3.8-27b`. Then ai-phone downloads no language model.
   - The line: **A SIP address** for a free first call (no carrier).
3. Start ai-phone, and keep it running:

   ```bash
   uv run ai-phone run
   ```

4. In **Settings ▸ Calls**:
   - Set the ai-phone folder (`~/dev/ai-phone`).
   - Set a passphrase.
   - Add your number.
   - Turn on calls.

## Make a free first call

Use a SIP address on your tailnet. You do not need a carrier or an account.

1. Install a SIP phone app on your iPhone (for example, Linphone).
2. Turn on Tailscale on the iPhone.
3. Call `sip:agent@<your Mac's Tailscale name>`.

To test on the Mac only: `pjsua --local-port 5070 sip:agent@127.0.0.1`.

## Get a real phone number

A real number lets you call from the Phone app, or from CarPlay. The carrier charges money for the number and for each minute.

We recommend **Telnyx**. You need one API key, and ai-phone buys the number for you.

1. Make a Telnyx account at <https://telnyx.com>. Make an API key.
2. Put the key in `~/.ai-phone/secrets.env`:

   ```bash
   TELNYX_API_KEY=your-key
   ```

3. Add the line (this example buys a New York number):

   ```bash
   uv run ai-phone lines add telnyx --key-env TELNYX_API_KEY --country US --area 212
   ```

4. Stop ai-phone and start it again.

Do you already have a Twilio number? Use it, and nothing is bought:

```bash
uv run ai-phone lines add twilio --key-env TWILIO_ACCOUNT_SID --secret-env TWILIO_AUTH_TOKEN --existing +15555550100
```

With ai-phone, HoldSpeak does not ask for your carrier key, and it does not read it. The key stays in ai-phone's `secrets.env`. The Line keeps its secrets in your keystore (see [A Telnyx number on the Line](#a-telnyx-number-on-the-line)).

## The Line

The Line is HoldSpeak's own phone line. It does the job of ai-phone, and all of its parts have a permissive licence.

- **baresip** holds the call: SIP and the call audio. It runs as a separate program, and the Line starts it and starts it again if it stops.
- **Parakeet** hears your words. **Pocket TTS** speaks the answers. Both run on the machine of the Line, on the CPU.
- **HoldSpeak** does each turn of the call, the same as with ai-phone. Only text goes between the Line and the hub. The audio stays on the machine of the Line.

**Settings ▸ Calls ▸ Line** shows where the Line runs, its state, the line, a **Test call**, the rules it takes from Calls, and the adapter.

### Where it runs

The Line runs on this Mac or on a machine on your tailnet (for example, your home box). Select it in **Settings ▸ Calls ▸ Line ▸ Where it runs**. The state is one of: Ready, Starting, Not running, Not installed, Not set up, Offline.

A call minute costs about 0.13 of one core on an Apple Silicon Mac, and about 0.4 of one core on the home box (measured).

### Install the Line on your Mac

The Line runs in its own Python 3.13. The speech engine (onnxruntime) has no package for Python 3.14 yet, so it cannot go into the hub's Python. Do these steps one time:

```bash
brew install baresip
uv python install 3.13
uv venv ~/.holdspeak/line/venv --python 3.13
uv pip install --python ~/.holdspeak/line/venv -e "<your HoldSpeak checkout>[line]"
~/.holdspeak/line/venv/bin/holdspeak line models
```

`holdspeak line models` downloads the two speech models from Hugging Face (about 0.6 GB and 0.2 GB). Then start the Line, and keep it running:

```bash
~/.holdspeak/line/venv/bin/holdspeak line
```

The hub does not start the Line for you. When the Line is not running, **Settings ▸ Calls ▸ Line** shows these commands, each with **Copy**.

The `holdspeak line` commands:

| Command | What it does |
|---|---|
| `holdspeak line` | Run the Line on this machine (`--node`, `--hub`, `--bind`, `--sip-port`) |
| `holdspeak line check` | Show what is installed and what is missing |
| `holdspeak line build` | Build the Line's audio module for this machine's baresip again |
| `holdspeak line models` | Download the two speech models, and show their licences |

On another machine, the Line runs as `holdspeak line --node <name> --hub <your hub's address>`. The setup of another machine is not done yet.

### The free SIP address

You do not need a carrier or an account. The Line listens on one address only, never on all addresses. To take calls from your iPhone, start the Line on your Mac's Tailscale address:

```bash
~/.holdspeak/line/venv/bin/holdspeak line --bind <your Mac's Tailscale IP>
```

**Settings ▸ Calls ▸ Line ▸ Address to dial** shows the address, with **Copy**. Dial it from a SIP app on your iPhone (for example, Linphone), with Tailscale on. Tailscale decides who can reach the address; your numbers and your passphrase decide who gets to your desk.

### A Telnyx number on the Line

Select **A Telnyx number** in **Settings ▸ Calls ▸ Line ▸ The line**. Type the SIP user and the domain of your Telnyx credential connection, the SIP password and the Telnyx API key.

The SIP password and the API key go into your keystore (the macOS Keychain). HoldSpeak does not write them to its settings file, and it never shows them again. The row says where each one is:

- **Stored in your keystore**.
- **From the environment: move it to the keystore**. The hub found it in its own environment. Type it in Settings to keep it in the keystore.
- **Missing**. Type it in Settings.

A key in your shell profile (for example, `~/.zshrc`) is not in the hub's environment. Type it in Settings.

The Telnyx line is not tested with a real account yet.

### Test call

**Test call** calls your first number (or your SIP address). The Line says one sentence and ends the call. The row shows **Ringing**, then **Answered**, **No answer**, **Busy**, **Rejected** or **Line not running**. With no number in **Your numbers**, the row says **No number**.

### The rules the Line takes from Calls

- **Daily limit**: at most 20 placed calls a day (`calls.daily_limit`; 0 is no limit). Calls to you do not count.
- **First words out**: each call the Line places starts with "This is HoldSpeak, an AI assistant, calling for <your name>."
- **Never dialled**: 911, 112, 999, 000 and the other emergency numbers.

### The adapter

**Settings ▸ Calls ▸ Line ▸ Adapter** selects the program that holds the line: **The Line**, or **ai-phone** (optional, AGPL, a separate program). With no choice, HoldSpeak uses the Line when it finds baresip, else ai-phone when it finds it.

## Time to answer

The first answer of a call can take 5 to 9 seconds, because the engine reads the desk's tools one time. The answers after it are faster. While HoldSpeak works, ai-phone says "One moment." and HoldSpeak says "Still working on it." The line does not go quiet.

## For tools and agents

| Route | What it does |
|---|---|
| `GET /api/calls/status` | The line, the engine, the setup steps and the active call |
| `GET /api/calls` | The last 20 calls |
| `GET /api/calls/{id}` | One call, with all its words |
| `POST /api/calls/place` | Call a number (`{"to": "+1…"}`); with no number, call you |
| `POST /api/calls/{id}/hangup` | End a call |
| `POST /api/calls/{id}/decide` | Answer the held question (`{"decision": "approve"}` or `"deny"`) |
| `GET /api/calls/line/status` | The Line: where it runs, its state, the address, and where each secret is (never a value) |
| `POST /api/calls/line/test` | Test call: the Line calls you, says one sentence and ends the call |

The MCP tools are `calls.status`, `calls.list`, `calls.hangup` and `calls.place`. Only you can use `calls.place`. HoldSpeak refuses it from an agent. Each change of a call is a `call_state` frame.

## Licence

ai-phone has the AGPL-3.0 licence. HoldSpeak does not include ai-phone. HoldSpeak runs your own copy of ai-phone as a different program.

The Line has no GPL or AGPL code:

| Part | Licence |
|---|---|
| baresip 4.12 and libre 4.12 | BSD-3-Clause |
| aupipe (the Line's audio module, in HoldSpeak) | BSD-3-Clause |
| onnx-asr, onnxruntime, pocket-tts | MIT |
| Parakeet TDT 0.6B v2 weights (NVIDIA) | CC-BY-4.0 |
| Pocket TTS weights (Kyutai) | CC-BY-4.0 |

The attributions are in [NOTICE](../NOTICE).
