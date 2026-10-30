# Phone

Phone is the Desk service for reaching the owner away from the Desk. It can
send a message, ask for a call, and receive a reply or decision. It can use a
configured Calls phone-number transport.

The repository includes the Phone service and its pairing routes. It does not
include a delivered iPhone or other paired-phone application. Treat pairing as
a future client path until a client is delivered, enrolled, and visible in
**Settings > Calls > Phone**. A pairing code or QR payload alone is not proof
that a phone is connected.

## Two ways to reach your phone

| Way | What it needs | Current status |
| --- | --- | --- |
| **Configured number** | Calls enabled, an available Line or ai-phone adapter, and a configured phone number | Supported phone-number transport when those dependencies are ready |
| **Paired Phone app** | A delivered client, an owner-issued pair token, and a reachable hub | Pairing service contract exists; the client is not delivered in this repository |

The Phone service prefers a paired app when one is enrolled. Without one, it
falls back to the configured Calls number transport. The number path is for
voice calls; it does not provide SMS.

If neither transport is available, Phone reports an unavailable state such as
**No phone paired**. It does not claim that a message or call was delivered.

## Pair a phone

This is the service contract for a future Phone client; no app installation is
provided here.

1. Open **Settings > Calls > Phone**.
2. Select **Pair a phone**. The hub creates an owner-only pair token and QR
   payload that expire after 10 minutes.
3. A compatible client would scan or redeem the one-time token, then receive a
   device credential.
4. Select **Revoke** on the device row to close the device credential and its
   live connection.

The pair endpoint is owner-authorized. The QR payload names the hub that
issued it. Keep it on the intended private network and do not paste the token
into a general client setting.

## Your Apple push key

A paired iPhone gets a message or a call through Apple's push service (APNs).
The hub needs your own Apple push key to send these pushes. Without the key,
the phone row in **Settings > Calls > Phone** says **Push not ready: no Apple
push key on the hub**.

Make the key one time in the Apple developer portal:

1. Sign in to [developer.apple.com/account](https://developer.apple.com/account).
2. Open **Certificates, Identifiers & Profiles > Keys** and add a key.
3. Turn on **Apple Push Notifications service (APNs)** for the key, then
   register it.
4. Download the `.p8` file. Apple lets you download it one time only. Keep it
   in a safe place.
5. Write down the **Key ID** (on the key's page) and your **Team ID** (under
   **Membership details**).

Then give the key to the hub:

1. Open **Settings > Calls > Phone > Push**.
2. Paste the text of the `.p8` file into **Apple push key (.p8)**, or drop the
   file on the field. Select **Save**.
3. Type the **Key ID** and the **Team ID**, and save each one.
4. Keep the **App bundle ID** as `dev.holdspeak.mobile`, unless you build the
   app with a different bundle ID.
5. Select **Test push**. The hub sends one silent push to your paired phone
   and shows Apple's answer:
   - **Apple accepted it**: pushes work.
   - **This phone's token is stale: open the app once**: open HoldSpeak on the
     phone, then test again.
   - **Apple refused the key: check the Key ID and Team ID**: one of them, or
     the key, is wrong. Save them again.

What the hub does with the key:

- It keeps the key, the Key ID and the Team ID in your keystore (the macOS
  Keychain, or the Secret Service on Linux). Each row says only **Stored in
  your keystore** or **Missing**. No page and no route shows the key again.
- It uses the key only to sign a short token for each push to Apple. It sends
  the push only to Apple's push service.
- It never sends the key to a phone, an agent, an engine or a log.

## Reach you: when the desk sends a message or calls

Phone applies the control level **Secure**, **Normal**, or **YOLO**, the
configured **Reach you** words, quiet hours, and the operation's own
authority. In **Settings > Calls > Phone > Reach you**, each kind can be set
to **Message**, **Call**, or **Nothing**. The explicit row setting wins over
the level when the service supports that kind.

The source rules include these defaults:

| Situation | Secure | Normal | YOLO |
| --- | --- | --- | --- |
| Program core question | Message | Message, then a call after 10 minutes when the Program may call | Call at once when the Program may call; otherwise Message |
| Program step is red | Message | Message | Message; a call only when the Program may call under its rule |
| Program is done | Nothing | Message | Message |

Other kinds, such as heartbeat security, Meeting follow-up, and agent
questions, use their own configured reach row and the same authority checks.
Do not infer a call from a control level alone.

These rules still apply:

- A reply can close the reach item; the service does not repeat the same
  reach within its repeat window.
- The service does not start a new call while another call is active.
- A Program needs its **May call** permission for an agent-initiated call.
- An agent call can wait in **Needs you** for your decision.
- Quiet hours queue ordinary messages. Only an urgent call may ring when its
  authority permits it.
- A missed urgent call follows the service's retry and message policy. Read the
  resulting receipt rather than assuming a delivery.

Each reach stores the rule and route used. A pending reach is not a sent
message, and a ringing call is not an answered call.

## Quiet hours

Phone reads quiet hours from the active quiet-hours setting in **Settings >
Notices**. The Phone row can still expose the compatibility label **Change in
Rhythm**. The service queues ordinary messages during quiet hours. An urgent
call can bypass the quiet period only when the configured policy and transport
allow it.

The default and exact time zone are configuration, not a universal promise.
Read the current Settings value and the reach receipt.

## Message your phone from the desk

Open **Calls** and select its **Phone** wing. Type a message and send it when a
transport is available. A paired client would receive the message through its
push or socket path; a number transport cannot send SMS.

In **Needs you**, inspect the row before acting:

- A waiting phone message can be sent again or left waiting when the active
  control offers those verbs.
- A missed call can offer **Call again** or **Answer here**.
- A held request to call can offer **Call now** or **Let it wait**.

The exact row depends on the reach kind and its current state. Read the source,
transport, and receipt before retrying.

## What an agent can do

| Tool | Limits |
| --- | --- |
| `phone.send_message` | Text is limited to 500 characters; secrets are redacted. A Program step is limited to three messages per hour. |
| `phone.get_replies` | It waits up to one hour and returns each reply once. No reply is not consent. |
| `phone.call` | Reason is limited to 200 characters and context to 4,000. An agent request can wait in **Needs you**; it rings automatically only under Program and control rules. |
| `phone.status` | Reads paired-device state, line availability, quiet hours, and recent reach state. |

The service also limits one call's wait and retry behavior. It redacts
secrets from message and call content. A phone reply is a decision input, not
a grant of general Desk authority.

## Privacy

A configured number call goes through the selected provider or SIP route.
A future paired client may use the hub's socket and Apple push path. A hosted
Calls engine receives the text needed for its turn. Read **Settings > Calls**,
the transport state, and the receipt to identify the actual egress.

Phone has no SMS transport in this repository. Pairing credentials, provider
credentials, and engine credentials have separate stores and lifetimes.
Revoking a paired device does not delete Desk records.

## For tools and agents

| Route | What it does |
| --- | --- |
| `GET /api/phone/status` | Paired-device state, line availability, rules, quiet hours, and recent reach. |
| `POST /api/phone/pair` | Create an owner-authorized pair token and QR payload. |
| `POST /api/phone/devices` | Redeem a pair token for a device credential. |
| `GET /api/phone/devices` | List paired devices. |
| `DELETE /api/phone/devices/{id}` | Revoke a paired device. |
| `POST /api/phone/messages` | Send a Phone message. |
| `GET /api/phone/messages?after_seq=` | Read messages after a sequence. |
| `POST /api/phone/messages/{id}/read` | Mark one message read. |
| `POST /api/phone/messages/{id}/wait` | Let one message wait without changing its source record. |
| `POST /api/phone/calls` | Ask the service to reach the owner by call. |
| `GET /api/phone/calls` | List Phone call records. |
| `POST /api/phone/calls/{id}/accept|decline|end` | Accept, decline, or end a phone call. |
| `POST /api/phone/calls/{id}/ring` | Ring an eligible held call. |
| `POST /api/phone/calls/{id}/again` | Ask for the permitted retry after a missed call. |
| `GET /api/phone/events?after_seq=` | Read Phone event frames. |
| `GET /api/phone/push` | Owner only: which parts of the Apple push key are stored (never the key) and the push state. |
| `PUT /api/phone/push` | Owner only: store the `.p8` key, the Key ID, the Team ID or the bundle ID in the keystore. |
| `POST /api/phone/push/test` | Owner only: send one silent push to the paired phone and return Apple's answer. |
| WebSocket `/api/phone/ws?after_seq=` | Paired-client event and message channel. |

MCP Phone tools have their own principal and authority checks. Route existence
does not grant an agent permission to reach the owner. `HOLDSPEAK_PHONE=off`
turns the Phone service off on a hub.

## Where the idea comes from

Phone takes its model from agentring (Apache-2.0). HoldSpeak does not include
agentring. The [NOTICE](../NOTICE) file names the reused material.
