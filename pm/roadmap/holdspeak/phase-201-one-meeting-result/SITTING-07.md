# The sitting — HS-201-07 (the owner's desk, observed)

Plain words. Seven steps. The agent watches; the owner acts. Nothing an
agent starts touches the owner's HOME. Every step ends with a shot or a
line the owner sends.

## Before you start (once)

1. `main` holds Phase 201 (PR #587 merged). Pull it:

```bash
git checkout main && git pull
```

2. Build the web bundle if the product tells you to (it will say so).

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

## The seven steps

| # | You do | You should see | Send |
|---|---|---|---|
| 1 | Look at the arrival | One row: "No engine yet" and one button, "Choose an engine". Nothing else asks for you. | a shot |
| 2 | Choose an engine for summaries | Models. Pick your engine (your config names cloud gpt-5-mini; the .43 box is also fine). "Use this for summaries". The row on the arrival is gone. | a shot |
| 3 | Record one real meeting. Stop. | A meeting row with its length. No summary yet; no error. | a shot |
| 4 | Open the meeting. Look beside "Run summary". | The host that WILL run it, before you click. | a shot |
| 5 | Click "Run summary". Wait. | The host that DID run it, and the summary text under it. Read it. | a shot, and one line: useful, or not, and why |
| 6 | Stop the product (Ctrl-C). Start it again with the same command. Find the summary. | The same summary, in at most two moves. | a shot, and the number of moves |
| 7 | Dictate one sentence into any app. | Your words land. | one line |

## What the agent records

The startup line; the seven shots; the owner's line on the summary; the
move count; before/after row counts of the three ungated loops on the
live DB (read-only); the phase's final summary in the owner's words.

## What stops the sitting

Any step where the face does not say what this table says. The agent
writes it down as a defect with the shot, and the sitting continues to
the next step if it can. Nothing is fixed during the sitting.
