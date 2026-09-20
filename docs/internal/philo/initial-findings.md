# Philo initial source findings

These observations describe `675401a857b85336d4acaa8c65383dfc9636e4c8`.
They establish the planning direction. They do not prove full runtime behaviour.

| Finding | Evidence | Implication |
| --- | --- | --- |
| The kernel has an execution plane | `holdspeak/kernel/broker.py:17` inherits `ExecutorPlane`; `holdspeak/kernel/executor.py:28` claims work and validates warrants | The read-only Process surface does not define the kernel's full role. |
| Admission checks authority | `holdspeak/kernel/broker.py:295` checks principal, rights, prerequisites and interruption policy; `holdspeak/kernel/admission.py:31` rejects client authority fields | An architecture map must include admission and authority, not only journal writes. |
| Restart uncertainty has a concrete state | `holdspeak/kernel/broker.py:24` changes invalidated admitting/waiting operations to `indeterminate` with a terminal receipt | Preserve implementation vocabulary. Do not replace it with a speculative generic state machine. |
| A drop can prepare input without running it | `web/src/desk/dropMatrix.ts:23` declares source-holding rules for recipes, chains and workflows | Describe the actual source/target matrix and commit behaviour. Do not infer universal drag support. |
| Common window and verb contracts exist | `web/src/desk/components/DeskWindow.tsx:510`, `web/src/desk/components/DeskWindow.tsx:556`, `web/src/desk/verbRegistry.ts:49`, `web/src/desk/verbRegistry.ts:133` | Extract existing props and commands before proposing abstractions. |
| Canonical prose contains a modal conflict | `docs/internal/ARCHITECTURE_WEB_FRONTEND.md:96` recommends Dialog for modal focus; `docs/internal/UX-CANON.md:32` prohibits product modals | Record a documentation conflict. The higher face canon governs; do not propagate this paragraph into the SRS. |
| Existing reference tooling has an explicit owner | `docs/API_SURFACE.md:3`, `CONTRIBUTING.md:65` | Extend the API generator instead of adding a competing endpoint roster. |

## Verification performed

In the independent clone:

```text
$ python3 scripts/check_docs.py
Documentation navigation: 38 files checked; local targets and Markdown headings resolve.

$ python3 scripts/check_docs.py docs/internal/philo/README.md
Documentation navigation: 1 files checked; local targets and Markdown headings resolve.

$ python3 -m unittest discover -s tests/unit -p test_docs_navigation.py
Ran 9 tests in 0.016s
OK

$ git diff --check
(exit 0, no output)
```

Snapshot JSON also parsed through `python3 -m json.tool`.
No pytest suite, live hub, owner DB, microphone, model call or desktop typing
was used to establish these findings. No language certification is claimed.
Full drift and runtime checks remain obligations for their future changes.

`dw doctor` exited 1 because the baseline managed agent-docs block is stale.
Its checks for Python, hooks, the DW CLI and roadmap passed.
The eventual commit gate is a separate check.

## Publication checks

Final navigation check: all seven authored Markdown files passed.
The nine navigation tests passed. All three archived-source hashes matched.
The staged whitespace check passed for authored files. The full staged check
reports the original briefs' Markdown hard-break spaces, one trailing blank
line and a seven-equals MISSION underline. The underline is source text, not a
merge conflict. These bytes remain unchanged to preserve the input hashes.

The initial unstaged whitespace check above did not inspect untracked files.
It must not be read as a full staged-input check.
