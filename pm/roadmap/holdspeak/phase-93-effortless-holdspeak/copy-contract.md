# Professional product copy contract

**Decision date:** 2026-07-11<br>
**Status:** Phase-93 product-copy canon.

## Objective

HoldSpeak's interface copy must be professional, concise, factual, and useful.
The product may be visually distinctive and tactile without narrating itself,
selling itself, or turning ordinary operations into a story.

Copy exists to help a person:

- identify the current object, tool, process, destination, and state;
- understand what an action will do;
- know whether work is local, paired, private remote, or external;
- recover from failure without losing input;
- learn a capability at the moment it becomes relevant;
- inspect what happened and continue working.

## Voice

Use:

- direct, concrete language;
- short labels and sentences;
- active voice;
- canonical product nouns;
- commitment-specific verbs;
- exact destination and consequence;
- factual state and recovery information;
- neutral confidence without apology or celebration.

Avoid:

- marketing slogans inside the application;
- self-congratulation (`powerful`, `magical`, `revolutionary`, `beautiful`,
  `intelligent` when it is only praise);
- cinematic or quest-like storytelling;
- lore, faux drama, and novelty prose;
- anthropomorphizing the runtime, model, Desk, or background work;
- jokes in errors, permission, authority, security, or recovery copy;
- exclamation marks, breathless fragments, and decorative all-caps prose;
- repeating the product name where the surrounding interface already supplies
  context;
- paragraphs where a label, state, and next action are sufficient;
- vague reassurance (`You're all set`, `Something went wrong`, `We've got
  this`) without operational facts;
- implementation explanations unless the user opened an advanced diagnostic.

Qlippy may remain a visual presence. Its operational copy follows this contract:
no banter, guilt, personality monologues, or invented urgency. It states the
subject, reason, consequence, destination, and available decision.

## Copy hierarchy

Use the smallest sufficient layer:

1. **Label:** canonical noun or exact action, normally 1–4 words.
2. **State:** qualified fact such as `Needs approval`, `Paired · offline`, or
   `Meeting saved · intelligence incomplete`.
3. **Supporting line:** one sentence only when the label/state cannot explain
   prerequisite, scope, or consequence.
4. **Detail/inspector:** deeper provenance, policy, model, transport, or
   diagnostic facts on demand.
5. **Documentation:** concepts, examples, tutorials, and architecture.

Do not promote documentation prose into permanent interface chrome.

## Action copy

Buttons describe the immediate commitment:

- `Record meeting`
- `Keep as note`
- `Run release workflow on 3 items`
- `Send digest to Slack`
- `Approve and create issue in owner/repo`
- `Arm pane %7 for 15 minutes`
- `Retry transcription`
- `Use this device instead`

Generic `Open`, `Run`, `Apply`, `Approve`, `Continue`, and `Submit` are allowed
only when the visible subject and consequence make them unambiguous. A generic
verb must not conceal an external, destructive, queued, or authority-changing
effect.

## State and error copy

State copy uses one qualified axis. Do not use bare `pending`, `ready`, `local`,
or `complete` when several meanings are possible.

An actionable failure answers, in order:

1. What failed?
2. What was retained or not changed?
3. What is the next valid action?
4. Where was the operation supposed to run or send data, when relevant?

Example:

```text
Transcription failed on This device. Your recording is saved.
[Retry transcription] [Keep recording] [Open setup]
```

Do not add apology, mascot dialogue, or troubleshooting narrative before the
recovery action.

## First-use and empty-state copy

First-use copy teaches the next task, not the product vision. Empty states state
what belongs here and provide one relevant action. They do not explain the
company, congratulate the user, or enumerate the platform.

Preferred shape:

```text
No meetings yet
Record or import a meeting.
[Record meeting] [Import]
```

## Surfaces in scope

The controlled copy census includes:

- React and Swift arrival, Desk chrome, objects, tool shelf/dock, menus,
  inspectors, workrooms, Settings, dialogs, empty/loading/error states,
  notifications, Qlippy, Mission Control, attention, and receipts;
- setup, dictation, meeting, Workbench, Integration, Coder, Runs-on, authority,
  sync, and recovery journeys;
- CLI help and user-facing doctor output where it describes the same product
  concept;
- UAT instructions and public/user documentation that teach current product
  behavior.

Marketing pages may retain concise positioning outside the application, but
claims must remain factual and must not leak into operational UI. Developer and
SDK documentation may use precise implementation terms.

## Enforcement

- Maintain a versioned allow-list only for deliberate SDK, compatibility, test
  fixture, and marketing-page exceptions.
- Add a controlled census for prohibited promotional/filler patterns and
  unqualified generic verbs; treat it as a regression guard, not a substitute
  for human review.
- Every user-facing story includes a copy review of touched surfaces.
- Before/after evidence records representative production strings in context.
- The owner reads the ten primary journeys without repository context and marks
  unclear, promotional, theatrical, patronizing, or redundant copy as a
  blocking finding.
