# Phone

Phone lets your desk reach you when you are away from it. The desk sends a message to your phone, or it calls your phone. A voice tells you why it calls, takes your answer and gives the answer back to the desk as your decision. You can also call the desk from your phone and ask it questions.

Phone uses [Calls](calls.md) for the voice. Set up Calls first.

## Two ways to reach your phone

| Way | What it needs | Works today |
|---|---|---|
| **Your number** | A real phone line in ai-phone (we recommend Telnyx; see [Get a real phone number](calls.md#get-a-real-phone-number)) | Yes. Calls only. Any phone, also when it is locked, on cellular, with no app. |
| **The HoldSpeak app** | The HoldSpeak app for iPhone, paired with your hub | Not yet. The app is a program on your desk: "Phone: the iPhone rings". |

When a phone is paired, a call rings the app first. If you do not answer in 30 seconds, the call goes to your number, if you have a line.

The number has no text messages (ai-phone cannot send SMS). Until a phone is paired, a message stays on the desk. **Needs you** shows it as "No phone is paired", with **Let it wait**.

## Pair a phone

Do this when the HoldSpeak app is on your phone.

1. Turn on Tailscale on your phone.
2. Open **Settings ▸ Calls ▸ Phone** on the desk. Press **Pair a phone**. The desk shows a QR code for 10 minutes.
3. Scan the QR code with the app. The app is now paired.

The QR code holds the address of the hub that you pressed **Pair** on, and a code that works one time. To stop a phone, press **Revoke** on its row. The phone is disconnected at once.

## Reach you: when the desk sends a message or calls

The desk decides by your control level (Secure, Normal or YOLO). A message comes first. A call comes only when the message gets no reply, or when the thing is urgent.

| What happens | Secure | Normal | YOLO |
|---|---|---|---|
| A program has a core question | Message | Message. A call after 10 minutes with no reply, if the program may call | A call at once, if the program may call. Else a message |
| A program step stays red | Message | Message | Message. A call, if the program may call and it is the night's program |
| A program is done | Nothing | Message | Message |

The desk has rules for three more things, but it does not use them yet: a security or data-loss problem from the heartbeat (Secure: message, Normal: call, YOLO: urgent call), the follow-up asks of a meeting (Secure: nothing, else a message), and an agent's question that the desk cannot answer (Secure: message, Normal: a message and a call after 10 minutes when you are away, YOLO: call).

In **Settings ▸ Calls ▸ Phone ▸ Reach you**, you can set each row to **Message**, **Call** or **Nothing**. Your word wins over the level.

These rules are always true:

- When you reply to a message, the desk stops. It does not call you about it.
- The desk does not reach you two times in 5 minutes about the same thing.
- The desk does not call you while a call is on. It sends a message.
- A program may call you only when **May call** is on for it. The **Overnight** template turns it on.
- An urgent call that you miss rings one more time after 60 seconds. Then it is a message.

Each time the desk reaches you, it writes the rule it used. A program shows it under **Decided for you**.

## Quiet hours

Phone uses the quiet hours of **Settings ▸ Rhythm** (default 22:00 to 08:00). In quiet hours:

- A message is kept. Your phone gets it when it connects again. No push comes in the morning.
- Only an urgent call rings.

## Message your phone from the desk

Open **Calls ▸ Phone**. Type or speak a line, and send it. Your replies from the phone show in the same thread.

In **Needs you**:

- "Asked on your phone · 12 min · no reply": press **Call now**, or **Let it wait**.
- "Missed call: …": press **Call again**, or **Answer here** to reply from the desk.
- "Call you about …?": an agent asks to call you. Press **Call now**, or **Let it wait**.

## What an agent can do

| An agent can | The limits |
|---|---|
| Send you a message (`phone.send_message`) | 500 characters or less. No secrets. A program step can send 3 in an hour. |
| Wait for your reply (`phone.get_replies`) | It waits up to one hour. It gets each reply one time. No reply is not a yes. |
| Ask to call you (`phone.call`) | The call waits for your press in **Needs you**. It rings at once only if the agent's program may call and your level is not Secure. An agent that the desk started cannot call you. |
| Read the status (`phone.status`) | The paired phones, the line, quiet hours and the last time the desk reached you. |

The voice on a call reads only what the agent gives it: one reason, and the context. When the call ends, the agent gets the words of the call, why it ended, its length and your decision.

## Privacy

Your messages and your calls stay on your tailnet and your hub, with these exceptions:

- A call on your number goes through your carrier.
- A push to the app goes through Apple's push service. The push is signed, and a long message is cut.
- A hosted engine, if you set one for **Phone calls** in Settings ▸ Engines, gets the words of the call.

## For tools and agents

| Route | What it does |
|---|---|
| `GET /api/phone/status` | The paired phones, the line, quiet hours, the rules and the last reach |
| `POST /api/phone/pair` | A pairing code for 10 minutes, and what the QR code says |
| `GET /api/phone/devices` | The paired phones |
| `DELETE /api/phone/devices/{id}` | Revoke a phone |
| `POST /api/phone/messages` | Send a message (`{"text": "…", "reply_to": "…"}`) |
| `GET /api/phone/messages?after_seq=` | The messages after a sequence number |
| `POST /api/phone/calls` | Ask for a call (`{"reason": "…", "context": "…", "urgent": false}`) |
| `GET /api/phone/calls` | The calls |
| `GET /api/phone/events?after_seq=` | The event log, from a sequence number |

The MCP tools are `phone.send_message`, `phone.get_replies`, `phone.call` and `phone.status`. Each change is a `phone_changed` frame. `HOLDSPEAK_PHONE=off` turns Phone off on a hub.

## Where the idea comes from

Phone takes its model from agentring (Apache-2.0). HoldSpeak does not include agentring. The `NOTICE` file names what we took.
