# dogfood/ — the HoldSpeak dogfooding harness

A self-contained rig for exercising **all** of HoldSpeak against believable
data, on real metal, and recording what works. Built in Phase 67.

What's here:

```
dogfood/
├── PROTOCOL.md          # THE test protocol — fillable, two tiers, ~58 checks
├── RESULTS-TEMPLATE.md  # per-run header (env + rollup + verdict)
├── results/             # your dated, filled-in copies (gitignored)
│
├── setup.sh             # build the isolated sandbox HOME + a config
├── hs                   # run holdspeak against the sandbox (never your real ~)
├── env.sh               # `source` it for an interactive session (defines `hs`)
├── make_fixtures.py     # render scenarios → 16 kHz say audio (.sh wrapper too)
│
├── repos/               # 3 mock projects with .hs/ + KB + completed-stage history
│   ├── ledgerline/      #   fintech ledger (architect, incident)
│   ├── questline/       #   SaaS product app (product, delivery)
│   └── pylon-infra/     #   k8s platform (incident, delivery)
├── scenarios/           # *.yaml — 6 meetings (all 5 MIR profiles + balanced) + dictation
├── transcripts/         # committed .vtt/.srt/.txt for the transcript-import path
└── _audio/              # generated WAVs + ground-truth scripts (gitignored)
```

## Quick start

```bash
# 1. one-time: build the isolated sandbox (config wired to .43 intel)
dogfood/setup.sh

# 2. render the audio fixtures (needs macOS `say`)
python dogfood/make_fixtures.py        # or: dogfood/make_fixtures.sh

# 3. sanity-check the runtime in isolation
dogfood/hs doctor

# 4. open the protocol and start checking things off
cp dogfood/PROTOCOL.md dogfood/results/$(date +%F).md
$EDITOR dogfood/results/$(date +%F).md
```

Interactive shell instead of the `dogfood/hs` prefix:

```bash
source dogfood/env.sh
hs doctor
hs import dogfood/_audio/meeting-pylon-incident-warroom.wav --title "Cert outage"
hs web
```

## How isolation works

`dogfood/hs` runs the repo's installed `holdspeak` with `HOME` pointed at
`dogfood/_home`, so config (`_home/.config/holdspeak`) and the DB
(`_home/.local/share/holdspeak`) never touch your real ones. `setup.sh`
symlinks your real `~/.cache/huggingface` and `~/Models` into the sandbox so
Whisper/GGUF are reused, not re-downloaded. Wipe and restart any time:
`rm -rf dogfood/_home && dogfood/setup.sh`.

## The two tiers

- **Tier 1 — Plumbing** (`setup.sh --tier1`): no LLM, no mic. Fast and
  deterministic. The opt-in pytest covers the deterministic core:
  `HOLDSPEAK_DOGFOOD=1 uv run pytest -q tests/e2e/test_dogfood_plumbing_e2e.py`.
- **Tier 2 — Real metal** (`setup.sh`, default): real `say` → Whisper → intel
  on `.43`. Proves the LLM-shaped features actually produce output. Override the
  endpoint with `DOGFOOD_INTEL_BASE_URL` / `DOGFOOD_INTEL_MODEL`.

## The mock repos

Each is a believable, internally-consistent project (real-ish source tree,
`.hs/` context, a `.holdspeak/project.yaml` KB, `STAGES.md` of completed work,
ADRs, a postmortem). They give dictation a project to ground against and give
meetings a domain. The meeting scenarios reference each repo's real open
questions (ledgerline's write-path scaling + the LL-118 double-post; questline's
guilds-vs-activation call + Q3 scope; pylon's PI-204 cert outage + autoscaler
migration), so the intel pipeline has genuine material to chew on. They are not
git repos — `.hs/` + `.holdspeak/` are the project anchors.

## Scenarios → fixtures

`scenarios/*.yaml` are the source of truth. `meeting` scenarios render to one
combined WAV (multi-voice, brief inter-speaker gaps) for `hs import`; `dictation`
scenarios render one WAV per utterance. Each render also drops a
`<id>.script.txt` ground truth next to the audio so you can eyeball
transcription/intel quality. Add a scenario by dropping a new YAML in
`scenarios/` (the plumbing pytest validates its shape).

`python dogfood/make_fixtures.py --list | --dry-run | --only <id> | --kind meeting`
