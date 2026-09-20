# The sitting — HS-201-07 (the owner's desk, observed)

Plain words. One gate and seven steps. The agent watches; the owner acts.
Nothing an agent starts touches the owner's HOME. Every step ends with a
shot or a line the owner sends.

This script says what the faces say after stories 09, 10 and 11. The
rehearsal of 2026-09-20 (`audits/rehearsal-07-opus.md`) walked the desk at
`321247d2` and found the old script wrong at steps 1, 2 and 3.

## Before you start (once)

1. `main` holds Phase 201. Pull it:

```bash
git checkout main && git pull
```

2. Build the web bundle if the product tells you to. It says so.

## Start the product from main

```bash
cd /Users/karol/dev/tools/HoldSpeak && HOLDSPEAK_WEB_PORT=8765 \
  HOLDSPEAK_BACKEND_REVISION="$(git rev-parse HEAD)" \
  uv run holdspeak web --no-open
```

The first lines say which build and which database this is:

```
HoldSpeak runtime identity: backend_commit=<sha> frontend_build=<id> database_path=/Users/karol/.local/share/holdspeak/holdspeak.db
```

Send that line. Then open http://127.0.0.1:8765 in your browser.

## The gate and the seven steps

| # | You do | You should see | Send |
|---|---|---|---|
| 0 | The first screen says VOICE TYPING. Speak one sentence, or click "Continue later". | Your desk. | one line: which of the two you did |
| 1 | Look at the arrival. | A SETUP row and one button, "Choose an engine". The row says "No engine yet" when the desk has neither engine, or "No engine for summaries" when only the summary half is missing (it names what is missing, `web/src/desk/chair/meetingPathBlocker.ts:91-96`). The head above it counts what asks. An offer, such as "Connect calendar", does not count. | a shot |
| 2 | Click "Choose an engine". | Models. Click "Add an engine". Type the address of your engine. Click "Check". The engine reads READY. Click "Use this for summaries". The SETUP row on the arrival is gone. | a shot |
| 3 | Record one real meeting and stop it. Or click "Import" and choose a sound file. | A meeting row with its length. No summary yet. No error. | a shot |
| 4 | Open the meeting. Look beside "Run summary". | The host that WILL run it, before you click. | a shot |
| 5 | Click "Run summary". Wait. | The host that DID run it, and the summary text under it. Read it. | a shot, and one line: useful, or not, and why |
| 6 | Stop the product (Ctrl-C). Start it again with the same command. Find the summary. | The same summary, in two moves or less. | a shot, and the number of moves |
| 7 | Open a different app and click in a text box. Hold the Right Option key (⌥R), say one sentence, then release the key. | Your words become text in that app, at the cursor. | one line: what you said, and what landed |

Your engine address is the one you use today. The Models field shows an
example of the shape. A cloud engine from your configuration is also
correct here.

The key for step 7 is the one the product names at start:
`Voice typing hotkey is active: hold ⌥R, speak, release.`
(`holdspeak/web_runtime.py:580`; the default is Right Option,
`holdspeak/config/ui.py:15`). If the start says the hotkey is not
available, give HoldSpeak permission for Accessibility and Input
Monitoring, then start it again.

## What the agent records

The startup line; the gate line; the seven shots; the owner's line on the
summary; the move count; before and after row counts of the three ungated
loops on the live database (read only); the phase's final summary in the
owner's words.

## What stops the sitting

Any step where the face does not say what this table says. The agent
writes it down as a defect with the shot. The sitting continues to the
next step if it can. Nothing is fixed during the sitting.
