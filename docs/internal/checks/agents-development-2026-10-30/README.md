# Development-instructions committee — 2026-10-30

The owner requested a committee to improve `AGENTS.md` for ongoing development,
with the interface front and center, practical verification, and backend basics.
This is the record of that requested committee, not a new delivery ritual.

## Scope and method

Source base: `44b7104f7` (`origin/main` when this worktree was created).
Worktree: `/Users/karol/.codex/worktrees/agents-development/HoldSpeak`.
Branch: `docs/agents-development`.
PR: [#1635](https://github.com/karolswdev/HoldSpeak/pull/1635).

Three independent owner-started local agents, each `gpt-5.6-luna` at `xhigh`,
read the current rules and source, then checked the integrated guidance once:

| Member | Report | Final committee opinion |
| --- | --- | --- |
| UI craft and framework | [UI](ui.md) | RATIFY |
| Verification and workflow | [Verification](verification.md) | RATIFY-WITH-CONDITIONS; both wording fixes applied |
| Backend and architecture | [Backend](backend.md) | RATIFY-WITH-CONDITIONS; contract-scope clarification applied |

These are committee advice, not a Muad'Dib session's check or owner visual
acceptance. Initial report anchors refer to the source-base files before
integration; later recheck sections refer to the draft guides. The HoldSpeak
`agent.start_helper` tool refused with `launch_only` because this session is
owner-started. The three local committee agents completed the review instead.
No live desk project brief was supplied or found; the owner's chat request
and repository agreements are the brief.

## Resulting guide structure

- [Root AGENTS.md](../../../../AGENTS.md): job framing, Seven Tenets, read order,
  role/delegation rules, worktrees, test tiers, executable isolation recipe,
  quick check, shipping and honest reporting. Removes contradictory historical
  premerge gates from the active entry point.
- [web/AGENTS.md](../../../../web/AGENTS.md): Desk-owned windows and cores,
  public component APIs and import paths, window grammar, current material and
  icons, tokens, container reflow, keyboard/touch/voice, truthful words and
  egress, typed data flow, retained edits, failure/retry and named examples.
- [holdspeak/AGENTS.md](../../../../holdspeak/AGENTS.md): composed services,
  thin routes, blocking work off the event loop, hub authority, admission and
  execution, idempotency, receipts, inference, schema, aware time and contracts.
- [CLAUDE.md](../../../../CLAUDE.md) links all three guides so Claude workers
  also read the relevant scoped instructions.

The root stays focused on common decisions; UI/backend detail lives beside the
code. Canon retains its authority. Historical owner rulings remain in their
source documents and Git history. No product behavior, tests, dependencies,
model choices or owner rulings changed.

## Committee findings applied

| Finding | Applied correction |
| --- | --- |
| Old general cross-review/full-suite gates contradicted the current fast cycle | One active flow: quick check, PR/merge, watcher, postmerge review |
| Existing AGENTS test recipe lacked the mandatory lock and worker limit | Isolated HOME/cache recipe, machine lock, `-n 8 --dist worksteal`, no nested quick-check lock |
| A passed sweep does not establish PNG capture | Explicit `DESK_SWEEP_SHOTS=1`; inspect the actual shots |
| Automatic affected-test selection can miss browser files | Name required files through `QUICK_TESTS` or an explicit focused run |
| Web Button/Menu paths needed precise scope | `src/components/signal/Signal` and `src/desk/components/DeskMenu`; surface species use the public barrel |
| A blanket external-access prohibition contradicted authorized live walks | Isolated/no-egress defaults; separately authorized named device/provider runs remain outside quick check |
| Kernel requirements could be read as universal legacy coverage | Reuse an existing contract where applicable; new effects need a contract; verify actual caller wiring and state |

Known actuator config/receipt/decision gaps stay explicit. The guide does not
claim a declarative field enforces a policy or an approval dispatched work.
The initial advisory's old `UNCHECKED` wording was corrected to match the
current postmerge-review cycle.

## Verification

- Local link/heading navigation: all four changed instruction documents pass.
- Root shell recipe: `bash -n` passes; syntax inspection is not an executed
  device/provider procedure.
- Required quick check GREEN, isolated HOME and machine-wide lock: web build;
  126 Desk sweep cases (73.82 s); 27 canon checks (5.32 s); 1,185 repository
  guards (34.52 s). No Python/web implementation changed, so affected-test
  discovery selected no extra app test files.
- Sweep PNG capture was enabled; inspected Settings at 1440 and 393:
  `.tmp/evidence-shots/desk-sweep/surface-settings-1440.png` and
  `surface-settings-393.png`. These are isolated rig captures, not owner-live
  acceptance or proof that every example journey was exercised.
- Logs: `.tmp/agents-development-quick-check/{build,sweep,canon,repo}.log`;
  overall `/tmp/holdspeak-agents-development-quick-check.log`.
- Public navigation also passes across 73 documents; staged diff whitespace
  check passes.
- No new behavior tests were added for this documentation-only change.

No physical-device, live-provider, owner-desk, full-tape, deployment or owner
appearance verdict is claimed. Product source is unchanged.
