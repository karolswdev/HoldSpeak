# Activity Pre-Briefing

HoldSpeak already records what you browse locally, when you turn that on. Activity
pre-briefing turns that ledger into something useful at the moment you sit down to
dictate: a small set of quiet cards above the dictation cockpit that name what you
were looking at recently, cite where each one came from, and offer one action you can
take right then.

It is the opposite of a feed. There are at most three cards. They are dismissible. They
never run on their own.

If you are new here, read [Getting Started](./GETTING_STARTED.md) first.

> **Off until activity is on.** Pre-briefing reads the activity ledger you already
> control. Until you turn activity tracking on, there are no records to read, and the
> Pre-briefing block stays hidden. Turning activity off makes it disappear again.

## What you see

Open the **Dictation** page. If activity is on and you have touched a few things
recently, a "Pre-briefing" block sits above the cockpit tabs. The header says what it
is and how honest it is: "Local · source-cited".

Inside, you get up to three cards:

- **A windowed summary.** "You touched 3 things since recently" with a stat tile and a
  chip per source (for example, `safari/default`, `firefox/work`). This is the
  one-glance answer to "did anything change since I was last here?".
- **Per-record cards.** "You were looking at `github_issue owner/repo#123`" with a
  one-line summary (visits, domain, last-seen date) and a row of citation chips: the
  entity in the accent color, the browser and profile it came from, and the date you
  last saw it.

Each card is a quiet note. It does not steal focus from whatever you are typing.

## What the citation means

Every card names where its information came from. The entity chip on the left is what
HoldSpeak recognised the page as, when it was a known kind of thing (a GitHub issue, a
pull request, a Jira ticket, a calendar event); otherwise the chip falls back to the
page title or URL. The source chip is the browser and profile that recorded the visit,
for example `safari/default`, which is useful if you keep work and home in separate
browser profiles. The date chip is the day you last opened the URL. That is the date
of the last recorded visit, not a per-session timestamp; if you opened a page four
times last Tuesday, the chip says Tuesday.

You can verify any of this on the **Activity** page (`/activity`), which is the full
ledger the pre-briefing reads from.

## What the actions do

Each card offers up to two buttons.

- **Dismiss.** Closes the card and remembers that you did. The same card will not come
  back. Dismissals are stored locally with the rest of your HoldSpeak data.
- **Dictate with this** (per-record cards only). Pins the record so your next
  dictation can use it as context. A confirmation strip appears just below the cards
  with the entity name and a **Clear** button. The pin survives a page reload so the
  affordance stays visible until you use it or clear it.

That is the whole action surface. The pre-briefing never opens a URL, never sends
anything, and never runs a command. It surfaces and offers; you decide.

## How the relevance is chosen

The cards are picked by a simple rule, not a learned model. HoldSpeak looks at the
records you have touched since your previous meeting (or, if there is none, in the
last day) and ranks them by how recent they are, whether they are a known kind of
thing (issues and tickets rank above a bare page), and whether they belong to a
project you have set up. Weak signals do not appear; a stale page from days ago will
not become a card.

This is on purpose. Quiet beats noisy: a card you see should be worth your second of
attention. The picking is fully deterministic, so two refreshes a minute apart will
give you the same answer.

## What it does not do

A short list, written plainly, because a privacy-shaped feature deserves it.

- It does not watch your desktop apps. The only thing it reads is what activity
  tracking already records, which is browser history (and whatever enrichment you set
  up for it).
- It does not call out. Computing the cards happens on your machine, against your
  local SQLite database. Nothing about your activity leaves your laptop because of
  pre-briefing.
- It does not learn from your dictation. The relevance rule is a fixed heuristic, so
  it does not adjust to what you type or what you accept.
- It does not act on its own. Clicking a button is the only thing that fires
  anything. Dismissals are stored, the "Dictate with this" pin is stored, and that is
  the entire surface.

## Turning it off

Pre-briefing is gated by the activity tracking toggle. To turn it off:

1. Open the **Activity** page (`/activity`).
2. Switch **Activity tracking** off.

The Pre-briefing block on the dictation cockpit will disappear on the next page load.
You can leave activity on and individually dismiss cards you do not want to see, too;
either way, you decide what surfaces.

## Where the records come from

The records the pre-briefing surfaces are the same ones the
[Activity](./CONNECTOR_DEVELOPMENT.md) page shows. They are imported from local
browser history (Safari, Firefox, Chromium-family) with the readers HoldSpeak ships,
and optionally enriched with what you have connected (for example, GitHub or Jira
metadata). If you have not set any of this up, there will be no records and no cards.

The full ledger and its privacy controls live on `/activity`. The pre-briefing is just
a different way of reading what is already there.
