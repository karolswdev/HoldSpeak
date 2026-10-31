# Direction: briefing packages and the channels he decides on (PG-DIRECTION)

Owner, 2026-10-31, ruling the open decision of PG-LANG §15.10 and overriding
the Calls rule "HoldSpeak does not do from a call: Confirm a decision for you"
(`docs/calls.md:44`):

> "No - calls can absolutely occur, for decision making purposes. As long as
> they can bring context over, as well as allow me to defer (so call isn't huge
> pressure) then we are good. The magic about it should be to also integrate
> with telegram and provide 'briefing packages', that allow you to quickly make
> choices on a web interface, guarded by a token, to provide async direction
> when needed, and so on."

Sources: `PROGRAMS-DESIGN-2026-10-28.md` §6 (core questions, the ladder),
`PROGRAM-LANGUAGE-2026-10-31.md` (§10 the ecosystem, §13b JRN4 to JRN7, §15.10),
`PROGRAM-JOURNEYS-2026-10-31.md` (J2 the dreaming night, J6 the Phone and the
Line), `docs/calls.md`, `docs/phone.md`, `docs/REACH_RUNNER.md`, the code on
`main` at `222292a7e`. Canvas: `canvases/direction-2026-10-31.html` (the
briefing page at 393 and 1440 in two directions with the recommended one
marked, the Telegram message, the call as a transcript, Settings ▸ Reach, the
Needs you rows). The owner's "go with suggestions" (2026-10-27) pre-approves
the recommended direction; he judges it live on his desk.

Tenets check (Constitution, the Seven Tenets). (1) No new safety machinery:
the token model is the Line's one-time code and the Phone's pair token
(`docs/calls.md` "Install the Line on another machine", `docs/phone.md` "Pair a
phone") turned to one package; the call's hold is the existing `program.start`
hold (`holdspeak/mcp/palettes.py:207`). (2) The point is his first real use away
from the desk: a night of Programs that waits on him at 06:30 is answered in
the kitchen in ten seconds. (3) No second inbox: Needs you stays the one list
of what waits on him; a package is a view of a Needs you row for a channel.
(4) Product words follow ASD-STE100 ("Later", "Decide", "Revoke", "Sent to
Telegram"). (5) The page composes the kit; nothing is drawn by hand. (6)
Workbench on steroids: the page is one window of the desk grammar on a
phone. (7) A Senior Software Architect with reports decides from a train,
with the evidence one press away.

## 1. The job

He runs Programs hands-off (YOLO overnight, J2) and hands-on at definition.
Either way some items wait on him: a core question, Your word on a merge, a
requirement left, a merge ask at Secure, a proposal of an agent. Today he
answers them only on the desk, or with JRN5 and JRN6 (not built) as a prepared
answer from a call and a press on a paired phone app that is not delivered
(`docs/phone.md` "The repository … does not include a delivered iPhone …
application"). So a night that meets one question at 03:12 waits until he sits
down.

He wants to give direction asynchronously, from where he is, in seconds, and
without pressure. Three promises carry the ruling:

1. **Context comes over.** Every channel carries the same package: the
   question in his words, what changed and why, each choice with its
   consequence, and a link to the evidence. A call reads it; Telegram shows
   it in eight lines; the page shows all of it.
2. **Defer is free.** **Later** is a choice on every channel, at the same
   rank as the others. It has no penalty: the item keeps its place, the
   engine does the safe thing it may do (§7), and the item comes back at a
   time he names.
3. **One ledger.** One decision record, whatever the channel, written by the
   item's own verb (`program.decide` for a Program,
   `holdspeak/services/program_service.py:1942`). The ledger line names the
   channel: "Decided on a call", "Decided from Telegram", "Decided from the
   briefing page". The first answer decides; a second answer on another
   channel hears "answered already".

**A briefing package is one held item, or a digest of several, rendered for a
channel. He decides on the desk, by a push on his phone, on a call, from
Telegram, or on a tokened page served by his hub over the tailnet. Every
answer is the same verb with the same record, and Later is always one of the
answers.**

## 2. What it is not

- **Not a second inbox.** Needs you (`holdspeak/services/needs_you_membership.py:1`)
  stays the one meaning of "waits on you". A package has no list of its own
  on the desk; the Needs you row says where it was sent.
- **Not a chat bot that argues.** The bot sends packages and takes answers:
  a button, "yes", "later 2h", or one sentence. It does not hold a
  conversation, explain itself or ask follow-up questions. A free sentence
  becomes one proposed change (a shaping sentence for a Program, PG-LANG §4)
  or his words on the item; it is never a turn of a chat.
- **Nothing per step.** A package goes out for an item that waits on him,
  never for "step 4 started". A Program that runs well sends nothing until
  its digest.
- **No public page without a token.** The page answers only on a token
  bound to one package, over the tailnet by default. A relay that makes it
  reachable off the tailnet is named in §6 and is not built.
- **Never a payment or credential form.** The page never asks for a key, a
  password, a passphrase or a card. A package about money (a spend beyond a
  limit, a Telnyx number) shows the amount and the choices; the buy itself
  stays on the desk (`calls.line.buy_number` needs the quote of his press,
  `docs/calls.md` "A real number from Telnyx").
- **Not a new trust level.** An answer on a channel is his press only after
  the channel proves it is him: the paired Telegram chat, the passphrase on
  the call, the token on the page. No agent can send a package to anyone
  else, and no agent can answer one.

## 3. The nouns

### The held item

Anything that waits on him and has its own verb. The Program kinds are the
`DECIDE_CHOICES` of `program.decide` (`holdspeak/services/program_service.py:138`; the tool at `holdspeak/mcp/families/program.py:267`):

| Held item | Its verb today | Choices | Away from the desk |
|---|---|---|---|
| Core question (`core`) | `program.decide kind=core` | Go on · Park | yes |
| Your word on a requirement (`requirement`, word kind) | `program.decide kind=requirement` | Met · Unmet · Send back (Waive needs a typed reason) | yes; Waive only on the page with a typed line |
| A requirement left at the end (the rule kind `requirement_left`, decided as `requirement`) | the same | Met · Unmet · Send back | yes |
| Merge ask (`merge`, Secure, or Your word holds it) | `program.decide kind=merge` | Merge · Not yet | yes; Merge needs a second tap on Telegram (§5) |
| A finding (`finding`) | `program.decide kind=finding` | Fix now · Later · Skip | yes |
| A parked step (`parked`) | `program.decide kind=parked` | Resume · Skip | yes |
| An agent's proposal (`requirement_proposed`, `step_change`, `step_amend`) | `program.decide` with `proposal_id` | Add · Skip / Apply · Skip / Send · Skip | yes |
| An agent at its limit (`limited`) | `program.decide kind=limited` | Continue · Wait | yes |
| A race winner, an added step (`race`, `add_step`) | `program.decide` | as built | yes |

Holds the desk has outside Programs (the Needs you sources,
`web/src/desk/needs/needsFace.ts:374` to `:617`):

| Held item | Source | Its verb | Away from the desk |
|---|---|---|---|
| A decision to review (R4) | `decision` | `decision_record` accept or edit | yes (Accept · Later); edit on the desk |
| A meeting's proposals (aftercare) | `meeting.proposals` | `proposal.confirm` · `proposal.dismiss` | yes, one package per meeting |
| A project review proposal | `proposal` (`holdspeak/services/project_service.py:688`) | `project.decide_proposal` | yes |
| A prepared send | `send` (`needs_you_membership.py:1989`) | Send · Discard | the page only: the Send preview names the destination (UX-CANON A.9); never a Telegram tap |
| An agent's question (R5) | `coder` | his answer is typed to the agent | yes: Telegram text or the page's field |
| A gate hold or a helper Allow | `gate` | Allow · Deny | the page only (authority, owner 2026-09-29) |
| A held call (Call you about …?) | `phone` | Call now · Let it wait | yes |
| A Calls held operation | `/api/calls/{id}/decide` | yes · no | on the call only (it is that call) |
| Door tasks due now | `door` (R1) | not a decision | in the digest as one line ("3 tasks are due today"), no buttons |
| Meeting blockers (R2, R3) | `blocker`, `meeting` | repair on the desk | in the digest as one line, no buttons |

A held item is named by one **ref** everywhere: `program:<id>/step:<sid>/<kind>`
(with `/<finding_id>`, `/<requirement_id>` or `/<proposal_id>`),
`decision:<id>`, `meeting-proposals:<meeting_id>`, `project-proposal:<id>`,
`send:<id>`, `coder:<session>`, `gate:<id>`, `phone-call:<id>`. The ref is the
Needs you row's id where one exists.

### The briefing package

One held item, or a **digest** of several, rendered for a channel. It is
composed on the hub, frozen when it is made (the words he read are the
words in the record), and it holds:

1. **The head**: where it is from (the Program and the step, or the
   meeting, the project) and how long it has waited.
2. **The question**, in one sentence of his words where it has them: the
   core question's reason (`program_rules.is_core`,
   `holdspeak/services/program_rules.py:93`), the requirement's sentence, the
   proposal's `say` line.
3. **What changed and why**: at most three lines (the step's last
   checkpoints, the finding, the diff summary "4 files, +120 −18").
4. **The choices**, each with its consequence in a few words: "Go on: the
   step may change holdspeak/db/", "Park: the other steps go on".
5. **Later**, always, with the next touch (§7).
6. **The evidence**: links that open on the page as read-only panes: the
   PR, the check log tail, a shot, the step's brief, the Program text
   (PG-LANG §3) with the step's lines marked.

A digest is up to twelve held items in one package, ordered as Needs you
ranks them, with the night's "Since last night" head when a Program with
`night` ran (J2). One token covers the digest; each item in it is decided
alone.

### The channel

| Channel | What it carries | Who proves it is him | State in the repository |
|---|---|---|---|
| **Desk** | the Needs you row and the Program window | the desk's owner token | as built |
| **Phone app push** | the head, the question, the item's verbs (JRN6) | the paired device credential | the service is built; the app is not delivered (`docs/phone.md`) |
| **A call** (the Line or ai-phone) | the package read aloud, the choices, "or later" | allowed numbers, then the passphrase (`docs/calls.md` "Who can use your line") | the call turn is built; deciding on it is new (§4) |
| **Telegram** | the package in eight lines, inline buttons, the page link | the one paired chat id | a Cadence bot exists (`holdspeak/cadence_telegram.py`); reach through it is new (§5) |
| **The briefing page** | all of the package, with evidence | the token in the link | new (§6) |
| **Email** (stretch, parked) | the digest as text with the page link | none: a link in a mail is only a link | not designed further; the Send's email channel exists (`holdspeak/services/channel_email.py`) |

### The decision record

One record per answer, whatever the channel: the item's own verb writes it.
For a Program that is `program.decide`, which writes the checkpoint
(`program_service.py:3521`) and, for a Skip or a merge by rule, the proposed
Desk decision (`holdspeak/services/program_decisions.py:57`). The new part is
one field, `via`, on the checkpoint and on the package: `desk`, `phone`,
`call`, `telegram`, `page`. The ledger line adds the channel:

```
06:41 · Go on: the fix needs holdspeak/db/ · decided on a call
06:42 · Later, back at 13:00 · from Telegram
07:05 · Met: the People window at 393 has no clipped text · decided from the briefing page
```

The call's transcript Note (`docs/calls.md` "A finished call is retained …")
is linked from the line. A Telegram answer keeps the message id; a page
answer keeps the package id.

## 4. The call that decides

### The contract

1. **It opens with the package, in his words.** After the passphrase, a
   call that HoldSpeak placed about a held item (or a call he placed that
   asks "what waits on me") reads the package: the head ("Overnight on the
   home box, step 7"), the question, at most one line of what changed, and
   the choices by name. It ends every question with "or later".
2. **A spoken choice is read back once, then decided.** "Go on" becomes:
   "You said go on for step 7 of Overnight on the home box: the fix may
   change holdspeak/db/. Say yes to decide, or no." On "yes" HoldSpeak calls
   the item's verb as his press, `via=call`, and says "Decided." On "no"
   nothing changes and the question is asked again once. The read-back is
   verbatim: it names the full title, the step and the consequence.
3. **"Later" defers with no penalty.** "Later", "not now", "wait" and "ask
   me later" on a decision hold are Later, not No (today `_NO` in
   `holdspeak/calls/runner.py:55` counts "wait" and "not now" as no; a
   decision hold reads them as Later). He may say the next touch: "later,
   at one", "in two hours", "tonight", "tomorrow". With no time, the next
   touch is his default (§7). HoldSpeak says "Later, at 13:00. I will ask
   again then." Later needs no read-back: it changes nothing.
4. **Interruption-safe.** A call that drops, goes silent for the hold's
   wait, or ends between the choice and the yes decides nothing. The item
   stays held, and the ledger line is "Asked on a call 06:41 · no answer".
   An item answered on another channel while the call speaks is not asked:
   "Step 7 is answered already: Go on, on your phone." The first answer wins.
5. **One item at a time, then the next.** A digest on a call is read item
   by item; "skip" moves to the next item and is Later with the default
   touch; "that is all" ends the reading and leaves the rest held.
6. **The transcript line lands in the ledger.** The checkpoint line names
   the call and links its transcript Note; the passphrase is redacted from
   the Note as it is today.
7. **What a call never decides.** A waive (it needs a typed reason), a
   prepared send (the destination is named at the act, on the desk or the
   page), a gate hold, a buy, a setting, a credential. For those the call
   says "This needs your press on the desk or on the page. I sent you the
   page." and sends the page link to Telegram when it is paired.

### What the engine does while he defers

| Level | The held item | While he defers |
|---|---|---|
| Secure, Normal | any | the step waits; the other steps go on as the plan allows |
| YOLO | a core question | **provisional: the engine parks the step and goes on with the rest**; the line is "Parked for now: you said later · Overturnable"; at the next touch the question comes back and his Go on resumes the step from its checkpoint |
| YOLO | a merge ask, Your word | the step waits (a merge is never provisional; `program_rules.Decision` says "never a merge", `program_rules.py:47`) |
| YOLO | a finding (SHOULD), a proposal | the engine's rule applies as at YOLO today (Later as a Door task, Skip) and is listed under Decided for you with Overturn |

The engine never takes the core question's "Go on" for him: a core question
goes to him at every level (`PROGRAMS-DESIGN-2026-10-28.md:211`). Parking is
the one reversible move it has.

### The palette

`program.decide` joins the call palette as a held tool, the same hold as
`program.start`: `CALL_HELD_PROGRAM = {"program.start", "program.decide"}`
(`holdspeak/mcp/palettes.py:207`). The palette's comment "Config and
authority tools are never on a call" (`palettes.py:197`) gains the one
exception, ruled: `program.decide` (AUTHORITY, `holdspeak/mcp/tool_authority.py:341`)
is on a call only as a held tool, decided by his spoken yes after the
passphrase. The call prompt (`holdspeak/calls/service.py:52`) gains: "To
answer what waits on him, read the package, name the choices and say 'or
later'; call program.decide with his choice: it waits for his spoken yes."
`hold_words` (`calls/service.py:199`) gains the decision's read-back.

The other held items' verbs (`proposal.confirm`, `project.decide_proposal`,
a decision record's accept) join the same way in DIR8, each held.

### The Calls doc rule, amended

In this PR, the rule cell of `docs/calls.md:44` changes from "Confirm a
decision for you" to "Decide for you without your spoken yes". That sentence
is true today (a call decides nothing) and stays true after DIR8. The full
table and section below replace "What a call can do" when DIR8 merges, so
the user doc never claims what the code does not do (Article VI.3):

```markdown
| HoldSpeak can do | HoldSpeak asks first | HoldSpeak does not do from a call |
| --- | --- | --- |
| Read permitted Desk records | Send a prepared action | Change a setting |
| Write a Note or add a task | Post a send or other held egress | Change an engine or account |
| Propose a decision or add Project work | A control-mode hold | Decide for you without your spoken yes |
| Prepare a send | Start a program | Call another person |
| Say how a program is doing | Decide a question that waits on you | Make a program |
| Read you what waits on you, with the choices | | Waive a requirement, send, allow, or buy |

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
```

## 5. Telegram

### The bot

- **One bot, one owner chat.** HoldSpeak uses one Telegram bot that he
  makes with BotFather, and it talks to one chat: his. The Cadence bot
  (`holdspeak/cadence_telegram.py`) is the same bot: its `/brief`, its
  nudges and the morning brief stay, and reach joins them. There is never a
  second bot.
- **Pairing by a code on the desk.** Settings ▸ Reach ▸ Telegram ▸ **Pair
  Telegram** makes a one-time code (six digits, ten minutes, the Line's
  enrolment shape). The sheet shows "Send /pair 482 913 to your bot" with
  **Copy** and the time left. The first chat that sends it is paired; the
  code is then spent; the row reads "Paired · Karol". **Unpair** removes the
  chat. Today's static `pairing_code` setting (`holdspeak/config/integrations.py:263`,
  `_pair` at `cadence_telegram.py:98`) is replaced by the one-time code; a
  second chat can never pair while one is paired.
- **The secret in the keystore.** The bot token moves from the config file
  (`credential_service.py:20` writes `cadence_telegram.bot_token` into the
  settings) to the keystore slot `reach.telegram.bot_token` (the macOS
  Keychain or the Secret Service, the Line's pattern, `holdspeak/line/secrets.py:1`).
  On the first start after DIR5, a token found in the config is moved into
  the keystore and blanked in the file, with one log line. The row says
  "Stored in your keystore" or "Missing"; no read shows it again.
- **Off for rigs.** `HOLDSPEAK_TELEGRAM=off` turns the poller and every send
  off on a hub (a new isolation switch, default on, for every rig hub in
  `tests/e2e/glass_infra.py`).
- **Outbound only.** The bot reads updates by long poll (`getUpdates`,
  `poll_once` at `cadence_telegram.py:252`), so Telegram never needs to reach
  the hub; the hub stays on the tailnet. Today no live caller runs
  `poll_once` (only the daily brief is pushed, `holdspeak/runtime/cadence.py:114`);
  DIR5 runs it in one daemon thread, off the event loop.
- **Each send is egress.** Every call to the Bot API goes through
  `run_external_egress` with its destination and data class
  (`cadence_telegram.py:46`); a package send uses the data class
  `reach_package`. He set up the channel in Settings: that setting is the
  confirming act for reaching him (Article IV.2's clarification); a send to
  anyone else does not exist.

### The message

At most eight lines, plain text (no Markdown that a title could break):

```
Overnight on the home box · step 7 · waits 3 h
The fix needs holdspeak/db/, outside what the program owns.
Changed: 2 files in holdspeak/services/, check green.
Go on: the step may change holdspeak/db/.
Park: the other steps go on.
Open the page: https://karols-macbook-pro.tailad9943.ts.net/b/Xr4…

[ Go on ]  [ Park ]  [ Later ▾ ]
```

- The buttons are the item's own choices and **Later**. Later opens a
  second row: **1 h** · **13:00** · **Tonight** · **Tomorrow**.
- **One tap decides a reversible choice.** A choice that cannot be undone
  (Merge; a Skip of a requirement proposal that drops it) asks a second tap
  in place: the message edits to "Merge #1712 to main? [ Merge ] [ Not
  now ]", the Cadence kill pattern (`cadence_telegram.py:176`). The second
  tap expires after two minutes.
- **After the answer the message edits itself**: the buttons go, and the
  last line reads "Decided: Go on · 06:41" (or "Later · back at 13:00", or
  "Answered already on a call"). Nothing is sent as a second message.
- The page link is there when the hub has a tailnet address
  (`holdspeak/recordings/tailnet.py:1`); with none, the line is "Open it on
  your desk."

### Replies as text

A reply to the message (Telegram's reply, or the next text in the chat
while one package is open) is read by rule, no model, in this order:

| He writes | It becomes |
|---|---|
| a choice's word ("go on", "park", "met", "merge") | that choice; Merge still asks the second tap |
| "yes", "ok" | the first choice when there are two choices and it is the step's way forward; else "Which one: Go on or Park?" |
| "no" | the second choice when it is a Not yet or a Park; else asks which |
| "later", "later 2h", "later 13:00", "tonight", "tomorrow" | Later with that next touch (§7) |
| "waive: <reason>" | refused: "Waive on the page, with your reason." and the link |
| any other sentence, on a Program item | **a shaping sentence** (PG-LANG §4) on that Program: `program.shape` with `preview: true`; the bot answers with the diff's `say` line and a page link to the change well; below YOLO nothing applies until his Apply on the page or the desk; at YOLO it applies as PG-LANG §4.6 says and is Overturnable |
| any other sentence, on an agent's question | his words, typed to the agent at its next turn end, as the desk's answer is |
| any other sentence, on anything else | kept as his words on the item ("your words: …" in its Needs you row); nothing is decided |

### The digest

One message at a time he sets (default: the end of his quiet hours, the
morning brief's time, `runtime/cadence.py:111`), and only when something
waits on him. It is one package of up to twelve items: a head line ("3 wait
on you · 1 night ran"), one line per item with its kind word, and one
button, **Open the page**. The morning brief of Cadence and the night's
"Since last night" (J2) become its head, so there is one morning message,
not three. Each item also has its own message when it was sent alone; the
digest does not repeat buttons for those.

### What is never sent to Telegram

Telegram's servers see every message (a bot chat is not end-to-end
encrypted). So a message carries the question and the choices, and the page
carries the context:

- never a secret, a token other than the page link's, a passphrase, a key,
  an address book entry;
- never a diff, a file's content, a brief, a transcript, a log;
- never other people's private notes or People records (the People
  boundary, owner 2026-10-06, binds agents; a message is no agent but it
  leaves the device);
- titles and step names are sent; a title that matches the redaction rules
  of `phone.send_message` (`docs/phone.md` "secrets are redacted") is
  redacted the same way.

### Rate and quiet hours

Shared with the Phone, one budget for both: never twice in five minutes for
the same item (`REPEAT_MINUTES`, `holdspeak/phone/phone_rules.py:46`), at
most three messages per hour for one Program step (`docs/phone.md` "What an
agent can do"), and quiet hours from the one store (`read_quiet_hours`,
`holdspeak/services/heartbeat_service.py:153`) queue every message to their
end; the digest then carries them as one.

## 6. The briefing page

### The address

`https://<the hub's tailnet address>/b/<token>`, served by the hub. The
hub's tailnet address is the one Tailscale Serve proxies to it (`pm/STATUS.md`:
"the hub is also on the tailnet (Tailscale Serve, …, tailnet only)"), so the
page opens on his phone when the phone is on his tailnet. **A relay** (a
small public forwarder that holds no data and passes `/b/<token>` only) is
named here for later and is not built; Tailscale Funnel is the same idea
and is not turned on.

### The token

- **Single purpose.** A token is bound to one package. It opens that
  package's page and answers its items; it reaches no other hub route.
- **Strong and stored hashed.** 32 random bytes, base64url (43 characters).
  The hub stores only its SHA-256 (the agent credentials' pattern,
  `docs/REACH_RUNNER.md` "The hub stores only the token hash").
- **Expiring.** 24 hours for one item, 12 hours for a digest. After expiry
  the page shows "This page has expired." and the one line "Open the item
  on your desk"; no data.
- **Revocable.** **Revoke** on the Needs you row and on the package's line
  in the Program's Reach line. A revoked token answers like an expired one.
- **Read many, decide once.** He may open the page as often as he likes
  until it expires. Each item on it is decided once; after that the item
  shows its outcome and no verbs. A digest's token stays readable until all
  its items are answered or it expires.
- **No session, no cookie.** The page sets no cookie and keeps nothing in
  storage. It sends the token in the path only, never in `?token=` (the
  edge reads `?token=` as the owner token, `holdspeak/web_auth.py:92`).
- **At the edge.** `/b/<token>` is outside `/api/`, so the edge admits it
  (`holdspeak/principals.py:848`). Its data routes `/api/b/{token}` are
  admitted by one exception, `briefing_route(verb, path)`, as
  `phone_device_route` is (`principals.py:850`); the handler checks the
  token's hash, its expiry and its revocation, and is the only authority.
  The page's principal is `BRIEFING` with one right, `BRIEFING_ANSWER`, on
  that package. No owner right, no agent right.
- **Never in a log.** The hub's access log is off (`holdspeak/web_server.py:829`);
  the package row stores only the hash; the Telegram send's egress record
  stores the destination (`telegram:sendmessage:<chat>`), and its payload is
  recorded by digest, not by text (DIR5 checks this; §16).
- **Headers.** `Cache-Control: no-store`, `Referrer-Policy: no-referrer`
  (the token is in the path), `X-Robots-Tag: noindex`, and a
  Content-Security-Policy of `default-src 'self'; script-src 'self';
  connect-src 'self'; frame-ancestors 'none'`.

### The face

One window of the desk grammar, in the same kit, at phone width first. The
recommended direction is **A, the brief** (canvas, "The page: two
directions"):

- **Title bar**: the package's head ("Overnight on the home box · step 7").
  No close gadget: it is the whole page.
- **Toolbar**: nothing on one item; on a digest, `FilterTokens` "Waits on
  you · Decided" and the count words.
- **The question well** (the Your turn well, the ember rule): the question
  in display type once, the head's facts in 12 px ("waits 3 h · YOLO ·
  Programs"), and **the choices as library Buttons** in a column at 393
  (each 44 px), in a row at 1440, each with its consequence under it in
  secondary type. **Later ▾** is the last plated Button: a `WorkMenu` with
  **In 1 hour**, **At 13:00**, **Tonight**, **Tomorrow at 07:00** and **At
  a time…** (a `StringGadget` with its mic, "14:30" or "after the standup"
  is refused: "Say a time, for example 14:30"). A waive opens a `PadGadget`
  for the reason under the row, in place.
- **What changed**: a `ListView` of three rows at most (checkpoint lines).
- **Evidence**: `FoldGadget` panes, read only: **PR #1712** (title, files,
  +/−, checks as `DotWord`s; the link opens GitHub), **Check log** (the last
  40 lines in `SurfaceCode`), **Shot** (the image), **Brief** (the first 40
  lines), **Program text** (the Program text, PG-LANG §3, read only, the
  step's lines marked, in the `TextPane` once LANG2 ships it; `SurfaceCode`
  until then). Each pane loads when it opens.
- **Status bar**: "Expires in 21 h · from HoldSpeak on Karol's MacBook Pro"
  (the hub's device name; no address, A.9).

B, the board (the Program window read only with the Your turn well on top),
is shown on the canvas as the other direction. It carries more context and
costs two screens at 393 before the choices.

### What the page writes

The same decision record: `POST /api/b/{token}/answer {ref, choice, reason?,
later?}` calls the item's own verb with the owner as principal and
`via=page` (the token proves him; the record says the page). The ledger
line is "Decided from the briefing page". The answer is refused, by name,
when the item was answered already ("Answered already: Go on, on a call at
06:41"), when the item is gone ("This step is merged"), or when the token
has expired.

### After it is decided

The well settles: the choices go, the outcome takes their place ("Go on ·
06:41 · decided here"), and the evidence stays readable. Nothing else is
pressable. The Telegram message, if any, edits itself the same second.

### What the desk shows

The Needs you row of the item says where it was sent, in its line, not in a
chip (owner 2026-10-25, UX-CANON A.9):

- "Step 7 asks you: the fix needs holdspeak/db/ · sent to Telegram 06:30 ·
  page open 23 h" with **Go on** · **Park** · **Later ▾** · **Revoke**
  (Revoke only while a page is open; it ends the token, not the item).
- "… · later, back at 13:00" when deferred (the row is in the Later group,
  §7).
- On the Program window: the Reach line under Decided for you
  (`docs/internal/betterment/phone/PHONE-DESIGN-2026-10-28.md:116`) gains
  "Sent to Telegram 06:30 · page open · Revoke".
- A Your turn row gains **Send to my phone** in its `WorkMenu` (Copy page
  link, Send to Telegram): the first slice's way to make a page by hand.

## 7. Defer as a first-class answer, everywhere

### The words

Later is one choice with a next touch:

| He says or presses | The next touch |
|---|---|
| Later (no time) | his default, Settings ▸ Reach ▸ **Later means** (default: in 2 hours, or the end of quiet hours when that is sooner than 2 hours away from their start) |
| In 1 hour, "in two hours", "later 2h", "later 30m" | now plus that |
| At 13:00, "at one", "later 13:00" | that time today, or tomorrow when it has passed |
| Tonight | 19:00 today |
| Tomorrow | the end of quiet hours tomorrow (07:00 by default) |

The parser is a rule over these forms (no model); anything else asks "Say a
time, for example 14:30." The words are the same on the desk (a `WorkMenu`
on the Needs you row), the page, Telegram and the call.

### The next touch

A deferred item leaves the count of Needs you and sits in a **Later** group
at the end of the list, with "back at 13:00" in its line (the "waiting"
rule's shape: listed, not counted, `needs_you_membership.py:28`). At the
next touch it comes back to the count and the ladder starts again at the
channel where he deferred it. A deferral never lowers the bar: the item is
the same item, with the same verbs.

### The escalation ladder

| Rung | When | Setting |
|---|---|---|
| 1. Desk | at once: the Needs you row | always |
| 2. Phone app push | at once, when a phone is paired | Settings ▸ Reach ▸ Phone app: On · Off |
| 3. Telegram | at once when no phone app is paired; else after **Telegram after** (default 10 minutes) with no answer | Settings ▸ Reach ▸ Telegram: At once · After 10 min · Only the digest · Off |
| 4. A call | by `phone_rules.reach` as built: a core question at Normal after 10 minutes with no answer when the Program may call; at YOLO at once when it may call (`phone_rules.py:7` to `:17`) | Settings ▸ Reach ▸ Calls, per kind: Call · Message · Nothing (the Phone's Reach you rows, moved here) |

Rules on top of the ladder: his word per kind wins over the level (as
built); an answer anywhere stops the ladder; never twice for one item within
one quiet-hours period (a deferred item that comes back inside quiet hours
waits for their end); never a call while a call is on; never a rung he
turned off.

### The engine's provisional move

At YOLO only, and only for a core question: the engine parks the step and
goes on with the rest (§4 table), marked Overturnable. Below YOLO the step
waits. A merge, an egress, a buy, a setting and a credential are never
provisional at any level.

## 8. Security and egress

### Who may send what where

- **Only to him.** A package goes to his own channels only: the desk, his
  paired phone, his own number (Calls' "Your numbers"), his one paired
  Telegram chat, a page whose token is in a message to one of those. There
  is no field for another address.
- **No agent sends a package.** An agent's `phone.send_message` stays as
  built (text, 500 characters, three per hour per step). The package path is
  the hub's: the reach rules decide, not the agent. The MCP tool
  `phone.brief` (§11) is owner only.
- **No agent answers one.** The page's principal is `BRIEFING`; the call's
  decision is his spoken yes after the passphrase; the Telegram answer is
  the paired chat's. An agent credential reaches none of these routes.
- **The egress article.** Telegram and the call's provider are egress to a
  third party (Article III). It is disclosed where the choice is made:
  Settings ▸ Reach's Telegram row says "Messages go through Telegram's
  servers" as a fact row, and the Calls row says the call's route as built.
  Working windows show no host or scope chip (UX-CANON A.9).
- **Tokens never in logs**, the page refuses after expiry or revocation,
  and pairing is one-time.

### Threats

| Threat | What stops it |
|---|---|
| A page link is forwarded or seen over his shoulder | the token opens one package only; it expires (24 h, 12 h); Revoke on the desk; the page shows no secrets and decides only that package's items |
| Someone guesses a token | 256 random bits; the hub compares hashes; a wrong token costs a 404 with no timing difference worth having; ten wrong tokens a minute from one address are refused for a minute |
| The page's script reads the desk's owner token | the desk keeps the owner token in `localStorage` per origin (`web/src/lib/auth.ts:5`), and the page is on the same origin; the page is its own entry (`web/briefing.html`) that never imports `web/src/lib/auth.ts` (a guard test), renders package text as text (no HTML from a package), and runs under `script-src 'self'` |
| A title or a finding carries script or a link to trick him | package text is text; the only links are the evidence links the hub made (GitHub PR URL, the hub's own panes) |
| The link leaks by Referer to GitHub | `Referrer-Policy: no-referrer`; evidence links open with `rel="noreferrer"` |
| A second Telegram chat pairs | the code is one-time, ten minutes, and refused while a chat is paired |
| The bot token leaks | it is in the keystore, joined into the URL only at call time (`cadence_telegram.py:32`), redacted from every log line (`_redact`, `cadence_telegram.py:64`) |
| A forged Telegram update | updates come from Telegram's API to our long poll only (no webhook to forge); a callback from any chat but the paired one is refused ("Not paired.", `cadence_telegram.py:155`) |
| A caller who is not him decides on a call | allowed numbers, then the passphrase, then the read-back and his yes (as `program.start`) |
| A noisy line hears "yes" | the read-back names the title, the step and the consequence; "no" or silence decides nothing; a decision is Overturnable where the item allows |
| Two answers race (call and Telegram) | the item's verb runs under the Program lock; the first answer decides; the second gets "answered already" |
| A package sent while he sleeps wakes him | quiet hours queue it; only an urgent call rings, as built |

## 9. Faces

All kit, no modal, no prose, every verb the library `Button`, no counter of
zero, egress at the act (UX-CANON A.1 to A.9).

- **Settings ▸ Reach.** The rail item Notices becomes **Reach** (one rail
  item, not a new one; Tenet 3). One paper, the Accounts grid of label and
  control:
  - **Channels**: Desk (always, no control), Phone app (the paired phone's
    `DotWord` and On · Off; Pair a phone stays in Settings ▸ Calls ▸ Phone),
    Telegram (`DotWord` "Paired · Karol" or "Not paired", **Pair Telegram**
    or **Unpair**, the bot token row "Stored in your keystore" with
    **Replace**, the fact row "Messages go through Telegram's servers"),
    Calls (`DotWord` "Ready for calls" from the Calls status, **Open Calls
    settings**).
  - **When to reach you**: Telegram as a `CycleGadget` (At once · After 10
    min · Only the digest · Off); the Reach you rows per kind (Message ·
    Call · Nothing), moved from Settings ▸ Calls ▸ Phone.
  - **Quiet hours** (moved from Notices: the same store and control).
  - **Digest**: the time (`CycleGadget` of times, default "End of quiet
    hours") and **Send the digest now** (it sends to his own channels; it is
    egress he presses).
  - **Later means**: In 2 hours · End of quiet hours · Tomorrow.
  - The Cadence and Morning brief groups stay under it, folded.
- **The Needs you row** (`web/src/desk/needs/needsFace.ts`): no channel
  chips; the row's line says "sent to Telegram 06:30 · page open 23 h" or
  "later, back at 13:00"; the verbs are the item's own plus **Later ▾** and,
  while a page is open, **Revoke**. A Later group at the end, listed and not
  counted.
- **The Program window's Reach line**: "Reach: Telegram at once, then a call
  after 10 min · quiet 22:00 to 07:00" and, per sent package, "Step 7 · sent
  to Telegram 06:30 · page open · Revoke".
- **The briefing page** at 393 and 1440 (§6, canvas).

### Delight (four moments)

1. **The message settles.** The Telegram message edits itself into its
   outcome ("Decided: Go on · 06:41"), and the page's well settles into the
   same words at the same second.
2. **The count ticks down live.** He decides on the train; the desk's Needs
   you count ticks down and the Program's step lamp turns from ember to
   working blue, with the track's dot drawn on.
3. **"That is all."** A call that read three items ends with "That is all.
   Two decided, one later at 13:00." and the ledger has three lines.
4. **Later has a face.** The deferred row shows "back at 13:00" in the
   Later group, and at 13:00 it rises into the list with the first-paint
   fade.

## 10. The ecosystem

- **Programs first.** Every Program held item of §3 (DIR1 to DIR8). The
  Dreaming night (J2) ends with one digest whose head is "Since last
  night", which is JRN4's phone message turned into a package; JRN4 becomes
  that digest.
- **Then every other held item**, in this order (DIR10): decisions to review
  (R4, including the Program's proposed decisions), meeting proposals
  (aftercare), project review proposals, agents' questions (`coder`), held
  calls; prepared sends and gate holds on the page only; Door tasks and
  blockers as digest lines with no buttons.
- **The Note's morning digest.** The handover note "Program: <title>" keeps
  its "Since last night"; the digest's head is its first line, and the page
  links the note read only.
- **JRN5 and JRN6.** JRN5's prepared answer stays for one case: he says an
  answer on a call and then "put it on my desk" instead of yes. JRN6 (the
  item's verbs on a phone push) is rung 2 of the ladder and uses the same
  package and the same `via=phone` record. JRN7 is DIR8.
- **The Phone app, when it ships**, keeps what only an app can do: a push
  that rings through Do Not Disturb for an urgent call, the call itself in
  the app, the mic, the thread. Telegram adds what needs no app: buttons and
  text today, the digest. The page adds the context: the evidence, the
  Program text, a waive with its reason, a send's preview. With the app
  paired, push is rung 2 and Telegram is rung 3; without it, Telegram is
  rung 2.
- **Reach Runner** (`docs/REACH_RUNNER.md`) is a scheduled client of the
  hub's MCP; it is not a channel to him and is unchanged.

## 11. The contract for the lanes

### Tables (minimal, additive; the next SCHEMA_VERSION, 89 today, after PG-LANG's columns if they land first)

```
CREATE TABLE IF NOT EXISTS briefing_packages (
    id TEXT PRIMARY KEY,                 -- "pkg-<12 hex>"
    kind TEXT NOT NULL,                  -- item | digest
    refs_json TEXT NOT NULL,             -- ["program:…/step:…/core", …]
    body_json TEXT NOT NULL,             -- the frozen package as composed
    token_hash TEXT NOT NULL UNIQUE,     -- sha256 of the page token
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revoked_at TEXT,
    sent_json TEXT NOT NULL DEFAULT '[]',     -- [{via, at, message_id?}]
    answers_json TEXT NOT NULL DEFAULT '{}'   -- {ref: {choice, via, at, later_until?}}
);
CREATE TABLE IF NOT EXISTS held_later (
    ref TEXT PRIMARY KEY,
    until TEXT NOT NULL,
    via TEXT NOT NULL,
    at TEXT NOT NULL,
    package_id TEXT
);
ALTER TABLE program_checkpoints ADD COLUMN via TEXT;   -- desk | phone | call | telegram | page; NULL = desk
```

Two tables and one column. No token table: the token is the package's. The
schema snapshot is regenerated.

### Routes (every handler through `run_in_threadpool`)

```
GET  /b/{token}                          the page shell (web/briefing.html); 404 shell for a bad token
GET  /api/b/{token}                      {package, items:[{ref, state, outcome?}], expires_at}     BRIEFING
GET  /api/b/{token}/evidence/{ref}/{pane} {pane: pr | log | shot | brief | text, body}             BRIEFING
POST /api/b/{token}/answer               {ref, choice, reason?, later?} → {item, outcome}           BRIEFING
GET  /api/reach                          channels, ladder, quiet hours, digest, open packages       OWNER
PUT  /api/reach                          the settings of §9                                         OWNER
POST /api/reach/packages                 {refs, kind, send: [telegram|phone|none]} → {id, link}     OWNER
POST /api/reach/packages/{id}/revoke                                                               OWNER
POST /api/reach/later                    {ref, later} → {until}                                     OWNER
POST /api/reach/telegram/pair            → {code, expires_at}                                       OWNER
DELETE /api/reach/telegram/pair                                                                     OWNER
POST /api/reach/digest                   send the digest now                                        OWNER
```

`principals.py` gains `briefing_route` and `PrincipalKind.BRIEFING`; each new
route gets its residual-set entry and the api-surface regen; times through
`local_now`.

### MCP

The `channel` family is the Send: a document to a saved destination through
prepare, preview and his Send press (`holdspeak/channel_operations.py:35` to
`:300`, `holdspeak/mcp/families/channel.py:1`). A package to him is not a
send to a destination and must not wait for a Send press, so it does not
belong there. It belongs with reach, in the existing `phone` family
(`holdspeak/mcp/families/phone.py`):

| Tool | Does | Who |
|---|---|---|
| `phone.brief` | `{refs, kind, send?}`: make a package and send it to his channels by the ladder, or only make the page link | owner (an orchestrating agent asks him through Needs you as today) |
| `phone.later` | `{ref, later}` | owner |
| `phone.status` | gains `telegram`, `ladder`, `open_packages` | as built |
| `program.decide` | gains `via` (desk default) and `later` | owner, as built; in the CALL palette as a held tool (DIR8) |

`tool_authority.py`: `phone.brief` WORK, `phone.later` WORK.

### The frame

`desk_changed("reach", package_id, verb)` with verb `sent`, `answered`,
`revoked`, `expired`, `later`; `program_changed` as built after an answer.
The Needs you aggregate reads the open packages and the Later rows.

### Fixtures (recorded from the rig)

`reach.package.json` (one core question, one Your word, one merge ask, a
digest of four; recorded from a rig Program through
`scripts/record_program_fixtures.py`), `reach.page.json` (the
`/api/b/{token}` answer, open, decided, expired), `telegram.updates.json` (a
`/pair`, a button tap, a second tap for Merge, "later 2h", a free sentence,
an unpaired chat; recorded from the Bot API in a scratch bot once, then
replayed through the `caller=` seam of `TelegramSurface`,
`cadence_telegram.py:71`), `calls.decide.json` (a call's turns: the package
read, "go on", the read-back, "yes"; and "later, at one"). The test diet:
recorded answers, never typed ones.

### The switches

`HOLDSPEAK_TELEGRAM=off` (no poller, no send), added to every rig hub's
isolation switches with the others (`HOLDSPEAK_PHONE=off`,
`HOLDSPEAK_CALLS=off`, `HOLDSPEAK_LINE=off`). The page needs no switch: it
reads nothing of the machine.

## 12. The slices

One branch per slice, each a PR in the fast cycle. `hs/` is `holdspeak/`,
`desk/` is `web/src/desk/`.

| Slice | Lane | What | Done when (tier) |
|---|---|---|---|
| **DIR1** | HUB | the package composer for the Program held items of §3; `briefing_packages`; the token (mint, hash, expiry, revoke); `briefing_route` and `BRIEFING`; `/b/{token}`, `GET /api/b/{token}`, the evidence panes, `POST /api/b/{token}/answer` through `program.decide` with `via=page`; `program_checkpoints.via` and the ledger words; `POST /api/reach/packages` and revoke; the headers | a rig Program's core question makes a package; its token reads it and answers it once (`via=page`, "Decided from the briefing page"); a second answer is "answered already"; an expired and a revoked token read nothing; the token reaches no other route (a census over every `/api` route with the briefing principal); the hash only is stored (T1 `tests/unit/test_reach_packages.py`, `tests/integration/test_desk_reach.py`) |
| **DIR2** | FACES | the page: `web/briefing.html` and `web/src/briefing/`, direction A, in the kit; the evidence folds; the settled state; the expired face | from `reach.page.json`: a press on Go on renders the settled outcome; Later ▾ at 13:00 renders "Later · back at 13:00"; the expired face has no data (T2 `web/src/briefing/__tests__/briefing.app.test.tsx`); the sweep's page-route case `/b/<rig token>` at 1440 and 393 is green (T3); the guard: no import of `web/src/lib/auth.ts` under `web/src/briefing/` (T2) |
| **DIR3** | FACES | the Needs you row's line and Revoke; **Send to my phone** ▸ Copy page link on a Program Your turn row; the Reach line's package line | a press on Copy page link makes a package and puts the link on the clipboard; the row's line says "page open 23 h"; Revoke ends it (T2 `needs.app.test.tsx`, `programs.app.test.tsx`) |
| | | **DIR1 to DIR3 are the first slice on his desk: the page for a Program's held item, over the tailnet, with a token, and no third party.** | |
| DIR4 | HUB + FACES | Later everywhere: `held_later`, the words parser, the Later group in Needs you, the return at the next touch, the YOLO provisional park | "later 2h", "at one", "tonight", "tomorrow" map to their times; a deferred item leaves the count and comes back; at YOLO a deferred core question parks its step Overturnable and Go on resumes it from its checkpoint; a merge ask only waits (T1 `test_reach_later.py`, T2) |
| DIR5 | HUB | Telegram reach: the keystore slot and the move from the config file; `HOLDSPEAK_TELEGRAM=off`; the one-time pairing; the long-poll thread; the message render (eight lines); buttons, the second tap, the edit after the answer; text replies by rule; rate and quiet hours shared with the Phone | over `telegram.updates.json`: a tap decides once (`via=telegram`); Merge asks a second tap; "later 2h" defers; an unpaired chat reads nothing; a second chat cannot pair; the bot token never appears in a log line or an egress record (T1 `test_reach_telegram.py`) |
| DIR6 | FACES | Settings ▸ Reach (Notices renamed): channels, Pair Telegram with its code, the ladder, quiet hours moved, the digest, Later means; the Reach you rows moved from Settings ▸ Calls ▸ Phone | from a recorded `/api/reach`: each row draws its state; Pair Telegram shows the code and its time; the sweep's settings case at 1440 and 393 (T2 `settings.app.test.tsx`, T3) |
| DIR7 | HUB | the ladder in the reach rules (the `telegram` rung, its order, never twice in quiet hours); the digest composer (Since last night, the Cadence brief, the held items) as one morning message; JRN4 folded in | the rig's night ends with one digest and no second message; a message in quiet hours waits for their end; an answer stops the ladder (T1 `test_reach_ladder.py`) |
| DIR8 | HUB | the call that decides (JRN7): `program.decide` held in the CALL palette; the package read; the read-back; yes, no and Later on a decision hold; interruption-safety; the transcript link in the ledger; the other held verbs held the same way; `docs/calls.md` "What a call can do" replaced with §4's text | the Calls rig decides a core question after "yes"; "no" and silence decide nothing; "later, at one" defers to 13:00; a dropped call leaves the item held; an item answered on Telegram first is "answered already" (T1 `tests/unit/test_calls_decide.py`, the Calls rig) |
| DIR9 | HUB | a free sentence on Telegram becomes `program.shape` preview (after LANG3); the page shows the change well read only with Apply | a recorded sentence returns its `say` line and a page whose Apply applies the rows (T1, T2) |
| DIR10 | HUB + FACES | the other held items of §3 as packages: decisions to review, meeting proposals, project proposals, agents' questions, held calls; sends and gate holds on the page only; Door tasks and blockers as digest lines | each source makes a package whose answer runs its own verb with `via`; a send on the page shows its preview with the destination and sends only on Send (T1, T2) |
| DIR11 | DOCS | `docs/reach.md` (new: Telegram, the page, Later, the ladder; ASD-STE100, no dashes), `docs/phone.md` and `docs/calls.md` updated, `docs/programs.md` (decide from anywhere), the skill, `RECIPE.md` "PG-DIRECTION", TRACKER, UX-CANON "Shipped", the generated docs | `scripts/gen_docs.sh` clean; the doc drift guard green |
| DIR12 | (parked) | email as a channel: the digest as text with the page link | parked until he asks |

Sequence: DIR1 → DIR2 → DIR3 (the first slice on his desk); then DIR4
(Later), DIR5 (Telegram) and DIR6 (Settings) in parallel by file ownership;
DIR7; DIR8 after LANG5's call palette work or alone (it needs only the
existing palette); DIR9 after LANG3; DIR10; DIR11 rides each slice and closes
the set.

## 13. What he presses

1. At 06:30 his phone shows a Telegram message: "Overnight on the home box ·
   step 7 · waits 3 h. The fix needs holdspeak/db/ …" He presses **Open
   the page**. The page shows the question, the two files changed and the
   check green. He opens **PR #1712**: two files. He presses **Go on**. The
   well settles: "Go on · 06:31 · decided here". The message edits itself.
2. On the desk later, the Program's ledger says "06:31 · Go on · decided
   from the briefing page", and step 7 is merged.
3. At 12:10 his phone rings: "Two things wait on you." He says "go on" to
   the first, then "yes" to the read-back. To the second he says "later, at
   five". "Later, at 17:00. That is all."
4. In Settings ▸ Reach he presses **Pair Telegram** once, sends the code to
   his bot, and sets the digest to 07:30.

## 14. Decisions for the owner (defaults chosen; say if another is wanted)

1. **One bot.** The Cadence bot is the reach bot; its static pairing code
   becomes a one-time code; its token moves to the keystore. Default: yes.
2. **A tap that cannot be undone needs a second tap on Telegram** (Merge,
   a Skip that drops a proposal). Default: two taps. The other choice: Merge
   only on the page or the desk.
3. **At YOLO, a deferred core question parks its step and the rest go on**,
   Overturnable; below YOLO the step waits. Default: yes. The other choice:
   the step waits at every level.
4. **Settings ▸ Notices becomes Settings ▸ Reach** (quiet hours, channels,
   ladder, digest, Later means, with Cadence and the Morning brief folded
   in), and the Reach you rows move there from Settings ▸ Calls ▸ Phone.
   Default: yes. The other choice: a new rail item Reach beside Notices.
5. **The page is on the tailnet only**; the relay is named, not built.
   Default: tailnet only.
6. **Token lifetimes**: 24 h for one item, 12 h for a digest; read many,
   decide once. Default: as written.
7. **What a call or a Telegram tap never decides**: a waive (it needs a
   typed reason), a send, a gate hold, a buy, a setting. Default: these go
   to the page or the desk.
8. **The digest is one morning message** at the end of quiet hours, holding
   the Cadence brief and the night's "Since last night". Default: yes.
9. **Later's default touch**: in 2 hours (or the end of quiet hours).
   Default: as written.
10. **A free sentence on Telegram about a Program is a shaping sentence**,
    previewed, applied only by his Apply below YOLO. Default: yes.

## 15. How we know it worked

**The scripted walk** (a rig hub with the recorded fixtures, then on his
desk with his bot and his phone on the tailnet):

1. A rig Program at Normal; step 3 has a Your word requirement "The People
   window at 393 has no clipped text", and its check is green: the step
   waits on him at MERGE.
2. The hub makes a package (`phone.brief`), and the recorded Telegram
   caller receives one `sendMessage` of at most eight lines with the
   buttons **Met** · **Unmet** · **Later ▾** and the page link.
3. The page `GET /api/b/{token}` answers with the package; the Shot pane
   opens the shot.
4. `POST /api/b/{token}/answer {choice: met}`: the requirement is Met,
   the checkpoint says "Met: The People window at 393 has no clipped text ·
   decided from the briefing page" with `via=page`, the Telegram message is
   edited to "Decided: Met · 07:05", and the Program merges step 3 by rule.
5. A recorded Telegram tap on the same message after that answers
   "Answered already from the briefing page"; nothing changes.
6. The same Program, step 4 meets a core question. The Calls rig places the
   call: the package is read, he says "later, at one", the item is in the
   Later group with "back at 13:00", the count drops by one; at YOLO the
   step is parked Overturnable and step 5 runs.
7. At 13:00 (the rig's clock) the item comes back; the call reads it; "go
   on"; the read-back; "yes"; the step resumes from its checkpoint; the
   ledger has "Later, back at 13:00 · on a call" and "Go on · decided on a
   call" with the transcript link.
8. The token of step 3's package after 24 hours reads "This page has
   expired." and no data; a revoked token the same.

**Also:** the census that the briefing principal reaches no `/api` route but
its own; a grep of the rig's logs and egress records for the bot token and
the page tokens finds nothing; on his desk, a night that waited on him is
answered from his phone in under a minute.

## 16. Could not establish

- **Whether the page can share the kit without the desk's auth client.**
  The kit's species may import API helpers that read `web/src/lib/auth.ts`;
  the import graph of `web/src/desk/surface` was not walked. DIR2 proves it
  with its guard; if the kit pulls auth in, DIR2 adds a thin kit entry.
- **A second Vite entry.** The build has one app entry (`web/index.html`)
  and `web/atmospheres.html`; how `web/briefing.html` fits the build stamp
  and `holdspeak/static/_built` serving was not read.
- **Whether the egress record keeps the payload text.** `run_external_egress`
  takes `payload_material` (`cadence_telegram.py:50`); whether it stores the
  text or a digest was not read. A package text has no secrets by §5, but the
  page link's token is in it; DIR5 must store a digest or redact the token.
- **The loop watch and the frames.** Whether `HOLDSPEAK_LOOP_WATCH` or any
  `desk_changed` frame names a request path (which would carry the token)
  was not checked.
- **Telegram's limits.** The Bot API's message edit window and the rate per
  chat were not measured; the design sends at most a few messages an hour.
- **Speech of "later, at one".** The Line's speech recognition was not run on
  times; the parser accepts digits and the words one to twelve, and asks
  again on anything else.
- **The phone browser on the tailnet.** Whether his phone runs Tailscale is
  not known; without it, the link does not open, and the message says so on
  the first send that fails.
- **The paired Phone app.** It is not delivered (`docs/phone.md`); rung 2 of
  the ladder is designed on the service contract only.
