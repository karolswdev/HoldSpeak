# Evidence - HS-93-03

- **Story:** HS-93-03 - One professional product voice
- **Status:** done
- **Date:** 2026-07-15

## Proof

### Captured run — 2026-07-16T05:56:03Z

- **Command:** `.venv/bin/python scripts/phase93_copy_census.py --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 716172bd526feb56aa0996e1e2247815879c2c79

```text
{
  "candidate_count": 4183,
  "copy_contract_version": 1,
  "counts_by_classification": {
    "detail": 1091,
    "error_recovery": 161,
    "label": 2546,
    "state": 43,
    "supporting_line": 342
  },
  "counts_by_client": {
    "cli_and_guides": 1836,
    "hub": 151,
    "swift": 1121,
    "web": 1075
  },
  "inventory": [
    {
      "classification": "label",
      "client": "cli_and_guides",
      "context": "heading",
      "line": 1,
      "path": "README.md",
      "text": "HoldSpeak"
    },
    {
      "classification": "label",
      "client": "cli_and_guides",
      "context": "label",
      "line": 4,
      "path": "README.md",
      "text": "HoldSpeak logo, a held key with rising soundwaves"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 7,
      "path": "README.md",
      "text": "One local copilot, two modes: dictation that types anywhere and learns how you work, and meetings that end with decisions, actions, and follow-ups instead of a recording. Nothing leaves your machine."
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 9,
      "path": "README.md",
      "text": "![License: Apache-2.0](https://github.com/karolswdev/HoldSpeak/blob/main/LICENSE)"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 10,
      "path": "README.md",
      "text": "![Tests](https://github.com/karolswdev/HoldSpeak/actions/workflows/test.yml)"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 11,
      "path": "README.md",
      "text": "![Python 3.10+](https://www.python.org/downloads/)"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 12,
      "path": "README.md",
      "text": "![Platform: macOS | Linux](#platform-support)"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 14,
      "path": "README.md",
      "text": "Hold a key and speak, and your words land in whatever app you are in,"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 15,
      "path": "README.md",
      "text": "optionally rewritten by your own model with your project's context. Record or"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 16,
      "path": "README.md",
      "text": "import a meeting, and it comes back as reviewable decisions, action items, and"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 17,
      "path": "README.md",
      "text": "typed artifacts, with a follow-up panel that shows what is still open. One"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 18,
      "path": "README.md",
      "text": "local runtime on macOS and Linux does both, for the two places a developer's"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 19,
      "path": "README.md",
      "text": "voice does work: the keyboard and the meeting. Whisper runs locally; the LLM is"
    },
    {
      "classification": "supporting_line",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 20,
      "path": "README.md",
      "text": "one you run or point at. No cloud, no account, no telemetry."
    },
    {
      "classification": "supporting_line",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 22,
      "path": "README.md",
      "text": "> **Status: 0.x, early but real.** HoldSpeak is on PyPI ( )."
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 23,
      "path": "README.md",
      "text": "> The features are mature; APIs, config, and defaults can still change while it is"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 24,
      "path": "README.md",
      "text": "> pre-1.0. Upgrades are safe by default (your data is backed up first). Feedback"
    },
    {
      "classification": "label",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 25,
      "path": "README.md",
      "text": "> and contributions welcome."
    },
    {
      "classification": "label",
      "client": "cli_and_guides",
      "context": "heading",
      "line": 27,
      "path": "README.md",
      "text": "The two modes"
    },
    {
      "classification": "label",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 29,
      "path": "README.md",
      "text": "| Dictate | Meet |"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 31,
      "path": "README.md",
      "text": "| Pixel art microphone with hold-to-talk waves | Pixel art meeting notebook with action items |"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 32,
      "path": "README.md",
      "text": "| Hold the hotkey, speak, release: the text goes into the active app. Turn on the dictation pipeline and rough speech is routed by intent, enriched with your project's context, and rewritten for its target (Codex, Claude, the terminal, the browser, your editor). Every run lands in the dictation journal; one tap on a wrong result teaches the correction memory. Voice commands map a spoken keyword to a real action (open a URL, launch an app, run a command). Say the wake phrase and it listens hands-free, with the result previewed, never typed, until you confirm; an optional preview mode does the same for every dictation (the card shows the text first, Type it commits, Discard drops it). The spoken language setting pins any of Whisper's 99 languages, and the spoken-symbol dictionary types your own vocabulary (\"double colon\" becomes ). Activity pre-briefing offers what you touched recently as dictation context, source-cited. | Capture mic and system audio live with speaker labels, or import a recording or a transcript file you already have (vtt and srt keep their real timestamps and speaker names). 14 built-in plugins call your LLM to pull typed artifacts out of the transcript: decisions, action items, ADRs, risk registers, incident timelines. Meeting aftercare then shows what is open, decided, and changed since last time; an accepted action can become a filed issue, and the digest or follow-up draft can go to your team through Send to Slack, all on a propose, approve, execute flow that never acts without you. The archive is searchable and filterable by date, speaker, tag, and open actions. |"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 34,
      "path": "README.md",
      "text": "This is what they look like in the product, not in pixel art. A saved meeting"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 35,
      "path": "README.md",
      "text": "comes back as typed, reviewable artifacts:"
    },
    {
      "classification": "label",
      "client": "cli_and_guides",
      "context": "label",
      "line": 38,
      "path": "README.md",
      "text": "A saved meeting open at /history: the transcript on the left, and on the right a stack of artifact cards (a Risk register table with impact, likelihood, mitigation, and owner; Decisions and open questions; typed Requirements), each with a confidence score and a copy button."
    },
    {
      "classification": "supporting_line",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 40,
      "path": "README.md",
      "text": "A meeting after intelligence ran: a risk register, decisions, and requirements, each extracted by an LLM-backed plugin and rendered read-only at /history."
    },
    {
      "classification": "label",
      "client": "cli_and_guides",
      "context": "heading",
      "line": 42,
      "path": "README.md",
      "text": "The Desk"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 44,
      "path": "README.md",
      "text": "Launch and the browser opens on the Desk: everything the two"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 45,
      "path": "README.md",
      "text": "modes produce, living as objects in one spatial world. Meetings, notes,"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 46,
      "path": "README.md",
      "text": "Knowledge, Personas, and their Artifacts appear on the Desk; Zones are"
    },
    {
      "classification": "supporting_line",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 47,
      "path": "README.md",
      "text": "shelves you drag things onto; tap anything and it opens in place."
    },
    {
      "classification": "label",
      "client": "cli_and_guides",
      "context": "label",
      "line": 50,
      "path": "README.md",
      "text": "The HoldSpeak Desk: pixel-art objects (meetings as cassettes, notes, a Knowledge plant, an Artifact page) floating on a warm dark stage; a Q3 release Zone tray holding one filed Meeting; Coder session avatars on a right-edge rail; a record orb bottom-center; a compact HoldSpeak menu and an egress badge top-left."
    },
    {
      "classification": "supporting_line",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 52,
      "path": "README.md",
      "text": "The front door: the world your voice work lives in. The orb records, the rail asks, the tray files."
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 54,
      "path": "README.md",
      "text": "The Desk is where the loops close. Press the orb and the hub records a"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 55,
      "path": "README.md",
      "text": "meeting; when it ends, the meeting lands on the stage as an object. Rope a"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 56,
      "path": "README.md",
      "text": "few objects together with the lasso and **Ask AI** about exactly that pile:"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 57,
      "path": "README.md",
      "text": "the answer prints as a card you keep or bin, and a kept card records every"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 58,
      "path": "README.md",
      "text": "object it read plus your instruction. The boundary badge names This device,"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 59,
      "path": "README.md",
      "text": "a paired device, a private endpoint, or an external service. See"
    },
    {
      "classification": "label",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 60,
      "path": "README.md",
      "text": "The Desk."
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 62,
      "path": "README.md",
      "text": "Ground this ask.** The composer carries an attach control: pick meetings,"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 63,
      "path": "README.md",
      "text": "expand each one to its digest, its transcript, or any artifact it produced,"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 64,
      "path": "README.md",
      "text": "and the gauge measures the selection against the model's window before you"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 65,
      "path": "README.md",
      "text": "run. The question is answered from those records (the hub reads them from"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 66,
      "path": "README.md",
      "text": "its own store), the kept card names them, and an unknown reference refuses"
    },
    {
      "classification": "supporting_line",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 67,
      "path": "README.md",
      "text": "with its id instead of guessing."
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 69,
      "path": "README.md",
      "text": "Talk to your Personas.** Tap an avatar on the rail and it opens a"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 70,
      "path": "README.md",
      "text": "conversation, not a one-shot prompt: turns accumulate, the thread survives a"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 71,
      "path": "README.md",
      "text": "reload, each reply wears the badge for where that turn actually ran, and any"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 72,
      "path": "README.md",
      "text": "reply can be kept on the Desk as an Artifact. The attach control rides the"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 73,
      "path": "README.md",
      "text": "chat composer too, so a conversation can be grounded on the meetings it is"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 76,
      "path": "README.md",
      "text": "Open a model.** The rail also lists every model the hub can run: its own"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 77,
      "path": "README.md",
      "text": "engine and each Runs on destination's model. One tap opens a chat pinned to that model,"
    },
    {
      "classification": "supporting_line",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 78,
      "path": "README.md",
      "text": "through the same conversation surface, grounding included."
    },
    {
      "classification": "label",
      "client": "cli_and_guides",
      "context": "heading",
      "line": 80,
      "path": "README.md",
      "text": "Data boundaries"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 82,
      "path": "README.md",
      "text": "Every run names its destination.** Transcription and model-backed work can"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 83,
      "path": "README.md",
      "text": "run on this device, a paired device, a private endpoint, or an external"
    },
    {
      "classification": "label",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 84,
      "path": "README.md",
      "text": "OpenAI-compatible service."
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 85,
      "path": "README.md",
      "text": "Name those as reusable **Runs on destinations** and assign one per Persona;"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 86,
      "path": "README.md",
      "text": "the destination definition syncs across your surfaces while the API key stays"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 87,
      "path": "README.md",
      "text": "on each one. A destination can name another of your machines: run"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 88,
      "path": "README.md",
      "text": "there and every run against that destination executes on"
    },
    {
      "classification": "supporting_line",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 89,
      "path": "README.md",
      "text": "that node, with its own model and keys."
    },
    {
      "classification": "supporting_line",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 90,
      "path": "README.md",
      "text": "See Security & privacy and Models."
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 91,
      "path": "README.md",
      "text": "It learns how you work, and shows you the receipts.** The dictation"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 92,
      "path": "README.md",
      "text": "journal records what you said, what it typed, where it routed, and how long"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 93,
      "path": "README.md",
      "text": "it took. Fix a wrong result in one tap and the correction memory learns; the"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 94,
      "path": "README.md",
      "text": "learning digest reports a real \"learned from N similar\" count, honest at"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 95,
      "path": "README.md",
      "text": "zero; replay an old utterance through the updated pipeline and watch the"
    },
    {
      "classification": "supporting_line",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 96,
      "path": "README.md",
      "text": "routing change. See the learning loop."
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 97,
      "path": "README.md",
      "text": "Meetings end with their loops closed.** A meeting produces artifacts,"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 98,
      "path": "README.md",
      "text": "an aftercare digest, and approval-gated actions where most tools stop at"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 99,
      "path": "README.md",
      "text": "a transcript. Actuators are off by default, audited, and only ever run"
    },
    {
      "classification": "detail",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 100,
      "path": "README.md",
      "text": "exactly what you previewed. See"
    },
    {
      "classification": "label",
      "client": "cli_and_guides",
      "context": "detail",
      "line": 101,
      "path": "README.md",
      "text": "meeti
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-07-16T05:56:04Z

- **Command:** `uv run pytest -q tests/unit/test_product_copy.py tests/unit/test_product_language.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 716172bd526feb56aa0996e1e2247815879c2c79

```text
...............                                                          [100%]
15 passed in 0.87s
```
