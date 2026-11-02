# Reach

**Settings ▸ Reach** sets how HoldSpeak reaches you when something waits on you and you are not at the desk. It has the channels, Telegram, when to reach you, quiet hours, the digest and what **Later** means. (This section was **Notices** before.)

What you can decide from each channel, and how, is in [Programs](programs.md#decide-from-anywhere). Remote MCP access is a different feature: see [Reach in the user guide](USER_GUIDE.md#reach).

## Channels

| Channel | What the row shows |
|---|---|
| **Desk** | **Always**. Needs you on the desk always has each item. |
| **Phone app** | The paired phone, or "No phone is paired". **Open Calls settings** pairs one (see [Phone](phone.md)). |
| **Telegram** | **Not paired**, **Waiting for your bot** or **Paired · <name>**, with **Pair Telegram** or **Unpair**. The row says "Messages go through Telegram's servers". |
| **Calls** | The state of your call path. **Open Calls settings** sets it up (see [Calls](calls.md)). |

## Pair Telegram

HoldSpeak uses one bot (the same bot as Cadence) and one chat: yours.

1. Make a bot with BotFather in Telegram and copy its token.
2. In the **Bot token** row, paste the token and press **Save**. HoldSpeak keeps it in your keystore (the macOS Keychain, or the Secret Service on Linux). The row then says **Stored in your keystore**; before that, **Missing**. **Replace** puts in a new token. No page shows the token again. A token that is still in the config file is moved into the keystore one time, and the file entry is made empty.
3. Press **Pair Telegram**. The row shows "Send /pair <code> to your bot", the minutes left and **Copy**. The code has six digits and is good for ten minutes. **New code** makes a new one.
4. Send `/pair <code>` to your bot from your own Telegram chat. The first chat that sends the code is your chat. The row then says **Paired · <name>**.

While a chat is paired, no other chat can pair. **Unpair** removes the chat. **Pair Telegram** is off until the token is stored.

## When to reach you

The ladder shows each rung in the order HoldSpeak tries them, with its wait: **Desk** (at once, always), **Phone** (the Phone app's push: **At once** or **Off**), **Telegram** (the choices below) and **Call** (by your **Reach you** rules, when Calls is set). An answer on any rung stops the ladder.

**Telegram** sets when an item goes to Telegram:

| Choice | What HoldSpeak does |
|---|---|
| **At once** (the default) | It sends each item when it starts to wait. |
| **After 10 min** | It sends an item when it waited 10 minutes and you did not answer it on the desk. |
| **Only the digest** | It sends only the daily digest. |
| **Off** | It sends nothing to Telegram. |

The **Reach you** rows set, for each kind, **Message**, **Call** or **Nothing** for the Phone. They were in **Settings ▸ Calls ▸ Phone** before. See [Phone](phone.md#reach-you-when-the-desk-sends-a-message-or-calls).

## Quiet hours

Reach and the Phone use one set of quiet hours. During quiet hours, Telegram sends no message and no digest. The messages wait until the quiet hours end.

## Digest and Later

**Digest** sets the time of the daily digest: **End of quiet hours** (the default), or 06:00, 07:00, 08:00, 09:00, 10:00, 12:00 or 18:00. HoldSpeak sends one digest a day at that time, only when something waits on you, and not when Telegram is **Off**. **Send the digest now** sends it at once (Telegram must be paired).

The digest is a plain list: "3 wait on you", one line for each item ("Finding · <program> · step 2"), and "Open your desk to see each one." It has no buttons.

**One morning message.** In the morning you get one message, not three:

- After a night program, the message is the night's "Since last night" line, with how many of the night's items wait on you and their page link.
- Else it is the digest, when something waits on you.
- When a Cadence loop is due, the same message ends with the Cadence brief's line, for example "Cadence: Create issue: watchdog. 3 open loops." When nothing waits, that line goes alone.

While Telegram is not **Off**, Cadence sends no morning brief of its own. Send `/brief` to the bot for the whole brief with its buttons.

**Later means** sets what a plain "later" means:

| Choice | The item comes back |
|---|---|
| **In 2 hours** (the default) | In 2 hours. If that time is in your quiet hours, at the end of the quiet hours. |
| **End of quiet hours** | At the next end of your quiet hours. |
| **Tomorrow** | Tomorrow, at the hour your quiet hours end. |

Later decides nothing. A deferred item leaves the Needs you count, and its row says "Later · back at 13:00". At that time it comes back. When you deferred it on Telegram or on the briefing page, Telegram sends it again. The times you can say are in [Programs](programs.md#later-and-when-it-comes-back).

## One page for several items

A briefing page can hold up to 12 items that wait on you, in order. Each item has its own question and choices, and you decide each one alone. A decided item shows its one line; the others stay open. The top of the page says how many still wait, for example "1 waits on you.". The page lives 12 hours. The morning message after a night program links one page for all the items of that night that wait on you.

Tools make such a page with `POST /api/reach/packages` and `{"refs": [...], "kind": "digest"}`. A digest goes as its link only: it takes no `send`.

## Items from outside a program

A page can also hold these items. Each choice runs the same action as the button on your desk:

| Item | Ref | Choices |
|---|---|---|
| A decision to review | `decision:<id>` | **Confirm**: the decision is accepted and leaves your review list. |
| A call that an agent asks to make | `phone-call:<id>` | **Call now**: your phone rings now. **Let it wait**: no call, and it stays on your desk. |
| A meeting's proposed action | `meeting-proposal:<id>` | The page shows the preview first: where it goes and the lines it sends or writes. **Do it**: HoldSpeak does it now. **Not this**: nothing is done or sent. |
| A project review's proposal | `project-proposal:<id>` | The page shows what **Accept** adds or records. **Accept** or **Dismiss**. |
| An audit's findings, its fix program, a lesson | `program:<id>:<item id>` (the id of its Your turn row) | The same choices as on the desk: **File** or **Skip**; **Make** or **Skip**; **Keep for this program**, **Keep for HoldSpeak** or **Skip**. The page names the program as the place, not a step. |
| A program step's agent asks a question | `program:<id>:<step>:answer` | One text field, the only input on the page: your answer. HoldSpeak types it to the agent. On Telegram, reply to the message with your answer. |
| A document that is ready to send | `send:<id>` | The page shows the preview first: the destination and the lines that go. **Send**: HoldSpeak sends it now. **Discard**: nothing is sent. This item goes on the page only: a Telegram message for it has no Send button. |
| A desk agent asks a question outside a program | `coder:<agent>:<session>` | One text field: your answer. HoldSpeak types it to the agent. |

When you answered the item on your desk first, the page says "Answered already on your desk." and decides nothing. A page with several items also shows plain lines with no buttons: the Door tasks due today, and the lines the desk adds (a blocker, for example "The meeting recorder has no microphone."). A held tool call never goes on a page: it stays on your desk.

## What may travel, and a late answer

Only knowledge travels: a question, a choice among the presses HoldSpeak offers, or a to-do. A permission (a held tool call, an approval) never goes to a page, Telegram or a call; it stays on your desk. Each page and each Telegram message records why it went (its `because`: the kind of item and, when the ladder sent it, the rule).

A late or wrong answer gets one plain answer back, and nothing else happens:

| What happened | What you see |
|---|---|
| The item was answered already | "Answered at 21:46 from the desk" (or "from Telegram", "on the call", "from the briefing page"). |
| The choice was not one of the item's choices | "That choice was not on offer". |
| The answer named no choice | "Choose one". The item still waits. |
| A Later could not be kept | "Could not keep that for later; it still waits". |
| The agent asks something else now (another question, or a permission prompt), after the page was made | "The agent asks something else now. Nothing was typed; it waits on your desk". Your answer is typed only to the question the page showed, and HoldSpeak checks it again right before it types. |

## The ladder

The ladder has a fixed order today: the desk, the Phone app, Telegram, a call. You cannot change it.

- The desk shows the item at once.
- The Phone app and a call follow the Phone's rules ([Phone](phone.md)).
- Telegram follows your choice under **When to reach you**.
- Telegram never sends one item two times in five minutes, and never more than three messages in one hour for one step.
- An answer on any channel stops the ladder. A Telegram message about an item that you answered somewhere else changes to show the answer.

## What a brief says

The briefing page, the Telegram message and a call say the same lines in the same order. First, what the program is for (its goal). Then what the step was doing (its title and the first sentence of its brief). Then what happened, in plain words: for example "The step could not push its branch: this repository has no remote." or "The check went red on pytest.". Then the question in one sentence, for example "Start the step again, or stop it?", and the steps that wait on this answer. Then each choice with what it does to the program, for example **Resume**: "Try the step again. It will fail the same way until the repository has a remote." A brief line never holds a path, a command, a hash or the raw error text. The raw error, the check log, the brief and the program text are behind their own words on the page. After you decide, the page shows one line, for example "Resume · 18:18. The step starts again. Nothing else waits on you.", and nothing else.

## What is never sent

A Telegram message holds only the item: where it is from, the brief's lines, each choice with what it does, and the page link. It never holds a secret, a diff, a file, a brief, a transcript, a log or another person's notes. HoldSpeak checks each message before it leaves and stops a message that holds a diff, a bot token or a private key.

Each send is egress. Its record names the destination ("Telegram · owner chat") and a digest of the message. It never holds the bot token.

## For tools and agents

| Route | What it does |
|---|---|
| `GET /api/reach`, `PUT /api/reach` | Read or change the Reach settings (`telegram`, `later_means`, `digest`, `phone_app`). |
| `PUT /api/reach/telegram/token` | Store the bot token in the keystore. |
| `POST /api/reach/telegram/pair`, `DELETE /api/reach/telegram/pair` | Start pairing (a code), or unpair. |
| `POST /api/reach/digest` | Send the digest now. |
| `POST /api/reach/later` | Later on one item (`ref`, `later`). |
| `POST /api/reach/packages` | Make the briefing page for one item; `send: ["telegram"]` also sends it. |
| `POST /api/reach/packages/{id}/revoke`, `GET /api/reach/packages?program_id=` | End a page, or list the open pages. |

The MCP tools are `phone.brief`, `phone.later` and `phone.status` (it also tells Telegram's state, the ladder and the open pages). Only you can change Reach, make a page or say Later.

`HOLDSPEAK_TELEGRAM=off` turns off every Telegram send and the poll. Test hubs set it.
