# Calls

You can call HoldSpeak from your phone. You speak, and HoldSpeak does the work on your desk. It tells you what it did. It asks you before it sends something.

HoldSpeak also calls you when you press **Call me**.

## How it works

Two programs work together on your Mac:

- **ai-phone** holds the line. It hears your words and speaks the answers. It runs on your Mac. Get it at <https://github.com/oxnw/ai-phone>.
- **HoldSpeak** does each turn of the call. It uses the tools of your desk.

The model that thinks runs on your engine. The default is your home engine over Tailscale ("Home engine over Tailscale"). Settings ▸ Engines ▸ **Phone calls** can change it.

ai-phone needs a Mac with Apple Silicon. It does not run on Linux. Your home engine can be on Linux.

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

HoldSpeak does not ask for your carrier key, and it does not read it. The key stays in ai-phone's `secrets.env`.

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

The MCP tools are `calls.status`, `calls.list`, `calls.hangup` and `calls.place`. Only you can use `calls.place`. HoldSpeak refuses it from an agent. Each change of a call is a `call_state` frame.

## Licence

ai-phone has the AGPL-3.0 licence. HoldSpeak does not include ai-phone. HoldSpeak runs your own copy of ai-phone as a different program.
