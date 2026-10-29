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
**ai-phone**. With no explicit choice, the service selects The Line when
baresip or an enrolled node is available, then ai-phone when it is available.
The relevant process and adapter must still be running.

The call turn uses the configured Calls engine. The source does not require a
particular provider, host, endpoint, or model name. Read **Settings > Calls**
and **Settings > This Mac > Engines** before you run a call.

## What a call can do

| HoldSpeak can do | HoldSpeak asks first | HoldSpeak does not do from a call |
| --- | --- | --- |
| Read permitted Desk records | Send a prepared action | Change a setting |
| Write a Note or add a task | Post a send or other held egress | Change an engine or account |
| Propose a decision or add Project work | A control-mode hold | Confirm a decision for you |
| Prepare a send | | Call another person |

The exact tool palette and source scope apply to the call turn. When a held
operation is needed, the caller hears the question. The Calls window can show
the same hold; select **Yes** or **No** there when that control is available.

A finished call is retained in the Calls service and its transcript becomes a
Desk Note. The passphrase is redacted from the transcript and Note. A call
record is evidence of the turn, not proof that an external action completed;
read its receipt and the target record.

## Who can use your line

Calls uses two gates:

1. **Allowed numbers.** Add numbers in **Settings > Calls > Allowed numbers**.
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

Provider-specific setup and pricing are not verified by this repository guide.
Use the provider's current instructions and read the Line status before a
call.

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

MCP calls tools have their own principal and authority checks. A route's
existence does not grant permission to use it. Read the response and receipt.

## Licence

ai-phone is an external AGPL-3.0 program; HoldSpeak does not include it. The
Line keeps its own component attributions in [NOTICE](../NOTICE). Licence,
model, and provider terms can change; read the current attribution and
provider terms before installation.
