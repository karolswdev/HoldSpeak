# Calls

Calls lets a configured phone line reach the HoldSpeak Desk. You can call the
Desk, speak a request, and receive a short spoken result. The Desk can also
place a call to the configured owner number from **Call me**.

This guide is source-backed. No provider, hardware, or real call was used while
refreshing it. A phone-number call needs an enabled Calls adapter, its
credentials, a reachable engine, and a configured number or SIP address.

## How it works

The phone half and the Desk have separate jobs:

- **The Line** is HoldSpeak's adapter. It can run on this Mac or on an enrolled
  Line node. It uses SIP audio locally and sends text turns to the hub.
- **ai-phone** is an optional external adapter. It is a separate program that
  can hold the line and provide speech.
- **HoldSpeak** owns the call turn, the Desk tools, the held decisions, and the
  call record.

Use **Settings > Calls > Line > Adapter** to select **The Line** or
**ai-phone**. Selection follows these rules:

1. `HOLDSPEAK_LINE=off` overrides the setting. It selects a detected ai-phone adapter, or none.
2. Otherwise, an explicit **The Line** or **ai-phone** choice wins.
3. With no explicit choice, a non-empty `HOLDSPEAK_AI_PHONE` command selects ai-phone.
4. Otherwise, a found baresip binary or a `calls.line.where` value starting with `node:` selects The Line.
5. The remaining fallback is a detected ai-phone adapter, or none.

A `node:` setting does not prove enrollment, reachability, or readiness.
The selected process and adapter must still start successfully.

The call turn uses the configured Calls engine. The source does not require a
particular provider, host, endpoint, or model name. Read **Settings > Calls**
and **Settings > This Mac > Engines** before you run a call.

## What a call can do

| HoldSpeak can do | HoldSpeak asks first | HoldSpeak does not do from a call |
| --- | --- | --- |
| Read permitted Desk records | Send a prepared action | Change a setting |
| Write a Note or add a task | Post a send or other held egress | Change an engine or account |
| Propose a decision or add Project work | A control-mode hold | Decide for you without your spoken yes |
| Prepare a send | Start a program | Call another person |
| Say how a program is doing | Decide a question that waits on you | Make a program |
| Read you what waits on you, with the choices | Change a program by your words | Waive a requirement, send, allow, or buy |

A program is named by its words: "start the overnight program" finds the
program whose title or template has those words. HoldSpeak says "I want to
start the program Overnight on the home box. Say yes or no." and starts it
only on your yes; "no" starts nothing. "How is the phone program doing" gets
one or two sentences: its state, how many steps are done, what waits on you
and the last decision. When no program has that name, or the program runs
already, HoldSpeak says so and asks nothing. It never makes a program on a
call. The Line and ai-phone give a call the same tools.

"Change the overnight program: add a check to every step" shapes the program
by your sentence. HoldSpeak reads each change back in one sentence and asks
"Apply? Say yes, no, or later." Yes applies the changes that can apply; a
change that lowers the bar never applies from a call and waits for you on the
desk. Later puts every change in the program's change well on the desk. See
[Programs](programs.md#change-it-on-a-call).

The exact tool palette and source scope apply to the call turn. When a held
operation is needed, the caller hears the question. The Calls window can show
the same hold; select **Yes** or **No** there when that control is available.

A finished call is retained in the Calls service and its transcript becomes a
Desk Note. The passphrase is redacted from the transcript and Note. A call
record is evidence of the turn, not proof that an external action completed;
read its receipt and the target record.

### Decide on a call

When something waits on you, HoldSpeak reads it to you: where it is from,
the question, what changed, and the choices. Each question ends with "or
later". Say a choice. HoldSpeak reads it back once, with what it will do,
and asks you to say yes. On yes, it decides, exactly as your press on the
Desk does. On no, nothing changes.

Say "later" to decide later. You can say when: "later, at one", "in two
hours", "tonight", "tomorrow". HoldSpeak asks you again then. Later changes
nothing, and the program does only what it can safely do without you.

If the call ends before your yes, nothing is decided. If you answered the
same question on your phone or on the Desk first, HoldSpeak tells you that
it is answered already. The program's ledger says "decided on a call", with
a link to the call's Note.

## Who can use your line

Calls uses two gates:

1. **Your numbers.** Add numbers in **Settings > Calls > Your numbers**. The
   stored key remains `allowed_numbers`.
   An empty list lets any caller reach the passphrase gate. It does not grant
   Desk access.
2. **Passphrase.** Calls asks for the configured passphrase at the start of
   every call. The caller has two attempts. If no passphrase is configured, or
   both attempts fail, the call ends.

Caller ID is not proof of identity. Keep the passphrase separate from Notes,
prompts, and provider settings.

## Set up calls

The active UI is the authority for setup state. Do not copy a provider key into
a Note or a Thread.

1. Open **Settings > Calls** and read each setup row.
2. Choose **The Line** or **ai-phone** in the adapter row.
3. Configure the Calls engine in **Settings > This Mac > Engines** when the
   default assignment is not suitable.
4. Set a passphrase and, when needed, add allowed caller numbers.
5. Turn Calls on only when the selected phone half is configured and running.
6. Start with the adapter's own status or test controls. Read the returned
   state before placing a real call.

For ai-phone, use its own installation and configuration instructions. A
typical checkout path is a placeholder such as
`<path-to-ai-phone>`; do not assume a particular home directory or model
endpoint. HoldSpeak does not include ai-phone and does not own its secrets.

## Make a free first call

A SIP address can avoid a carrier account when the Line or ai-phone is
reachable on the same private network. The exact SIP address is shown by the
configured adapter. A SIP client and network route are still required.

For the Line, **Settings > Calls > Line > Address to dial** shows the address
when one is available. The Line binds to the configured address; it does not
listen on every interface by default. Use the address shown by the Desk and
the network policy you selected.

## Get a real phone number

A provider number is optional. It can let an ordinary phone call the Desk or
let **Call me** ring the owner number. Provider charges, credentials, and
regional availability belong to that provider.

Configure an existing number or a provider account through the selected phone
half. Use placeholders in operational notes, for example
`<your-number>`, `<provider-account>`, and `<area-code>`. Never put a
real secret in this guide.

With ai-phone, its separate secret store remains outside HoldSpeak. With the
Line, SIP and provider secrets are held by the HoldSpeak keystore; the Calls
settings file stores only the reference needed to find them.

## The Line

The Line is the HoldSpeak-owned adapter. It runs baresip for SIP and audio,
speech recognition and speech output on the Line machine, and a text-only wire
to the hub. The audio does not travel over the hub wire.

**Settings > Calls > Line** shows where the Line runs, its state, the address,
the selected account, the adapter, the rules from Calls, and **Test call**.
A status such as Not installed, Not set up, Offline, or Not running is a
configuration state; it is not a successful call.

### Where it runs

The Line can run on this Mac or on an enrolled node on the configured network.
The source names `this_mac` and `node:<name>` as the location forms. A node
reports its machine and model facts at hello time. The hub can show a node as
ready, starting, not running, not installed, not set up, or offline.

The Line has its own Python 3.13 environment because its speech dependencies
are separate from the hub. The hub does not silently install or start that
environment.

### Install the Line on your Mac

Installation is optional and was not run for this documentation task. The
supported CLI shape is:

```bash
brew install baresip
uv python install 3.13
uv venv <line-venv> --python 3.13
uv pip install --python <line-venv> -e "<holdspeak-checkout>[line]"
<line-venv>/bin/holdspeak line models
<line-venv>/bin/holdspeak line
```

`holdspeak line models` downloads the Line speech models. Keep the venv and
model path under your control, and read the displayed licences. The CLI also
supports:

| Command | Meaning |
| --- | --- |
| `holdspeak line` | Run the Line (`--node`, `--hub`, `--bind`, and `--sip-port` are supported). |
| `holdspeak line check` | Report installed and missing pieces. |
| `holdspeak line build` | Build the audio module for the local baresip. |
| `holdspeak line models` | Download and report the speech models. |
| `holdspeak line enrol` | Redeem a one-time node code from a hub. |
| `holdspeak line unenrol` | Remove the node credential on that machine. |

The hub does not start the Line for you. When the Line is not running, **Settings ▸ Calls ▸ Line** shows these commands, each with **Copy**.

The `holdspeak line` commands:

| Command | What it does |
|---|---|
| `holdspeak line` | Run the Line on this machine (`--node`, `--hub`, `--bind`, `--sip-port`) |
| `holdspeak line check` | Show what is installed and what is missing |
| `holdspeak line build` | Build the Line's audio module for this machine's baresip again |
| `holdspeak line models` | Download the two speech models, and show their licences |

### Install the Line on another machine

The Line can run on a machine on your tailnet, for example your home box `karol`. That machine gets its own credential. The credential reaches only the Line's three wire routes on the hub, and nothing else.

1. On that machine, get the Line ready. You need a HoldSpeak checkout there. On Linux, `holdspeak line build` builds baresip 4.12.0 in your home folder, with no sudo:

   ```bash
   holdspeak line build
   holdspeak line models
   holdspeak line install --checkout <the HoldSpeak checkout on that machine>
   ```

   `holdspeak line install` makes the Line's own Python 3.13 and installs the service (a systemd user unit on Linux, a launchd agent on a Mac). Until the machine is enrolled, the service says "Not enrolled" and stops.

2. In **Settings ▸ Calls ▸ Line ▸ Where it runs**, type the machine's name in **Add a machine**, then press **Install the Line on karol**. The hub makes a one-time code. The code works one time, for 10 minutes. The sheet shows the code, the time that is left, and the whole command under **Run this on karol**, with **Copy**:

   ```bash
   holdspeak line enrol --hub <your desk's address> --code <the code> --node karol
   ```

   Run it on that machine. The Line service starts again with the new credential. When the Line there says hello to the hub, the sheet closes and the row reads **Ready**. If the code is too old, press **New code**.

   The hub in the command is the address you opened the desk on. Open the desk on its Tailscale address before you press Install, so that the other machine can reach it.

3. Select the machine's row in **Where it runs** to make it the place of the Line. Each machine row shows its platform, the cost of a call minute, and its state from its last hello. After 2 minutes with no hello, the row reads **Not running**.

To take the credential away, press **Revoke** on the machine's row, then **Revoke?** to confirm. The credential stops at once. To enrol the machine again, press **Install the Line** again.

A remote node first needs a one-time code from the hub. The node credential is
scoped to the Line wire, not to the rest of the Desk API. Do not paste a node
token into general client configuration.

### The free SIP address

When the Line reports an address, use **Address to dial** in Settings. A SIP
client on the allowed network can dial it. A tailnet or firewall controls who
can reach the address; the Calls allowed-number and passphrase gates control
who reaches the Desk.

### A Telnyx number on the Line

The Line account can be a SIP account or a provider account. Configure the
account in **Settings > Calls > Line** and enter secrets only through the
keystore control. The settings file keeps a secret reference, not the secret
value. The status can say Stored in your keystore, From the environment, or
Missing.

### A real number from Telnyx

With a Telnyx API key, HoldSpeak makes the SIP account and gets the number
for you. Open **Settings > Calls > Line**, set **The line** to **A Telnyx
number**, and open **Set up Telnyx**. There are three presses:

1. **Your key.** Paste your Telnyx API key into **Telnyx API key** and press
   **Save**. The key goes into the hub's keystore (the macOS Keychain or the
   Linux Secret Service). HoldSpeak never writes the key into a file. A key
   that is only in your shell (`TELNYX_API_KEY` in `~/.zshrc`) is not in the
   hub's environment, so save it here.
2. **Connect.** The hub makes an outbound voice profile and a SIP credential
   connection named "HoldSpeak Line" at Telnyx, with a new random SIP
   password. The row then says "Connected · sip.telnyx.com · user hs…".
   A second press uses the same connection again.
3. **A number.** Type an area code (for example `212`) and press **Find
   numbers**. Up to 10 numbers show, each with its monthly and its upfront
   cost from Telnyx. Press **Buy** on one number. The button then asks
   "Buy +1 212 555 0100 for $1.00 a month?". Only that second press buys
   the number. The hub then points the number at the line, and the row says
   "Yours: +1 212 555 0100 · assigned to the line".

**Costs.** The number costs what the row says, every month, plus the upfront
cost once, to your Telnyx account. Each call minute is charged by Telnyx as
well. The fold shows your Telnyx balance. The buy is a kernel operation
(`calls.line.buy_number`): its receipt names the number and the cost. An agent
cannot buy a number.

**Where the password lives.** The SIP password is in the hub's keystore
(`calls.line.sip_password`). The hub sends it to the Line node when the node
connects, and the node writes it only into its own `accounts` file (mode
0600). The Settings read never shows it.

If a press fails, the row says what failed, what is kept, and the next
action. For example, a wrong key: "Telnyx did not take the key… Your key is
kept. Nothing was made at Telnyx."

### Test call

**Test call** is an adapter check. When the Line is ready, it calls the
configured destination, says one sentence, and ends the call. The status can
report Ringing, Answered, No answer, Busy, Rejected, Line not running, or No
number. A successful test checks the adapter path; it does not prove a Desk
turn or an external send.

### The rules the Line takes from Calls

- `daily_limit` defaults to 20 placed calls per day; `0` means no limit.
  Incoming calls do not count.
- The Line follows the Calls passphrase, allowed-number, control-mode, and
  held-operation rules.
- The call's spoken result must not reveal the passphrase.
- Emergency-number handling is provider and adapter policy. Do not use Calls
  as an emergency service.

### The adapter

**Settings > Calls > Line > Adapter** selects **The Line** or **ai-phone**.
An empty adapter choice lets the service choose from the available phone
halves. `HOLDSPEAK_CALLS=off` disables the Calls listener and state reads;
`HOLDSPEAK_LINE=off` disables the Line adapter.

## Time to answer

Call latency depends on the speech engine, the Calls engine, the source scope,
and the phone network. The service can report **Still working** while a turn
runs. There is no fixed response-time guarantee in the source.

## Other ways to answer

What waits on you can also go to a briefing page or to Telegram, and you can
say Later on each one. **Settings > Reach** sets the channels, the digest and
what Later means. See [Reach](reach.md) and
[Programs](programs.md#decide-from-anywhere).

## For tools and agents

| Route | Meaning |
| --- | --- |
| `GET /api/calls/status` | Calls listener, engine, setup state, and active call. |
| `GET /api/calls` | The retained Calls list (up to the service's current retention). |
| `GET /api/calls/{id}` | One call and its transcript. |
| `POST /api/calls/place` | Owner-authorized outgoing call; an empty target means the configured owner number. |
| `POST /api/calls/{id}/hangup` | End one call. |
| `POST /api/calls/{id}/decide` | Approve or deny a held call operation. |
| `GET /api/calls/line/status` | Line location, state, address, machine facts, and secret status. |
| `POST /api/calls/line/test` | Run the Line's one-sentence adapter test. |
| `POST /api/calls/line/hello` | Line node hello on the text wire. |
| `POST /api/calls/line/events` | Line node event batch. |
| `POST /api/calls/line/next` | Long-poll the Line command wire. |
| `POST /api/calls/line/codes` | Mint a one-time, ten-minute node enrolment code. |
| `POST /api/calls/line/enrol` | Redeem the code for a scoped node credential. |
| `GET /api/calls/line/nodes` | List enrolled nodes and their reported state. |
| `DELETE /api/calls/line/nodes/{node}` | Revoke one node credential. |
| `GET /api/calls/line/telnyx/status` | Where the Telnyx key is, the connection, the number, and the Telnyx balance. |
| `POST /api/calls/line/telnyx/connect` | Make (or use again) the "HoldSpeak Line" SIP connection; the password goes to the keystore. |
| `GET /api/calls/line/telnyx/numbers?area=212` | Up to 10 numbers with their cost and a quote each. |
| `POST /api/calls/line/telnyx/buy` | `{phone_number, quote}`: buys the number (money). Refused without the quote of the owner's confirm press; the kernel operation `calls.line.buy_number`. |
| `POST /api/calls/line/telnyx/assign` | `{phone_number}`: point the number at the line. |

MCP calls tools have their own principal and authority checks. A route's
existence does not grant permission to use it. Read the response and receipt.

## Licence

ai-phone is an external AGPL-3.0 program; HoldSpeak does not include it. The
Line keeps its own component attributions in [NOTICE](../NOTICE). Licence,
model, and provider terms can change; read the current attribution and
provider terms before installation.
