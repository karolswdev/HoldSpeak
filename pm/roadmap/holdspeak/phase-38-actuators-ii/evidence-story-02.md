# Evidence — HS-38-02: GitHub write connector (`gh issue create`)

**Date:** 2026-06-04. **Branch:** `phase-38/hs-38-01-write-connector-framework`.

## What shipped

The first **real** write connector on the HS-38-01 framework: an approved proposal becomes
an actual GitHub issue via `gh issue create`, narrowly gated so it can do exactly one thing
and nothing else.

### Files

- **`holdspeak/plugins/builtin/github_issue_actuator.py` (new)** — the same two-half safety
  split as Phase-37's `followup_ticket_actuator`:
  - **`GithubIssueActuator`** (`kind=actuator`, cap `["actuator"]`) — `run(context)` proposes
    a GitHub issue for the first **unowned** action item; the payload carries
    `repo` / `title` / `body` (repo from `context["github_repo"]`). It never reaches out —
    nothing-unowned or no-repo raises → the host records a plain `error` (no proposal).
    `reversible=False` (a filed issue closes, it doesn't trivially undo).
  - **`GITHUB_ISSUE_MANIFEST`** — a `WriteConnectorManifest`, permission `shell:exec`,
    `allowed_argv_prefixes=(("gh", "issue", "create"),)` — and nothing else.
  - **`build_github_issue_connector(*, runner=…, timeout_seconds=…)`** — `build_gated_connector`
    with a `plan` that builds `["gh","issue","create","--repo",repo,"--title",title,"--body",body]`
    from the **stored** payload, and an `interpret` that raises on a non-zero `gh` exit
    (→ executor `failed` + audit) and otherwise returns `{"url", "issue"}` parsed from `gh`'s
    stdout. `runner` defaults to `subprocess.run`; tests inject a fake.
  - **`register_github_issue_actuator(host)`** — opt-in, **not** in `register_builtin_plugins`.

### Why this is safe

- **`gh issue create` only.** The subcommand is hard-coded in `plan`; only the *values* of
  `--repo`/`--title`/`--body` come from the payload. The manifest allow-check refuses any
  argv that is not `gh issue create …` **before** egress (asserted: a `gh repo delete` plan
  refuses with the runner never invoked).
- **No shell, no injection.** The argv is an explicit list run without a shell, so a hostile
  payload value (`repo="acme/app; rm -rf /"`, `title="$(whoami)"`) stays an inert *argument*
  to `gh issue create` — it can never change the subcommand or chain a second command
  (asserted).
- **Host-side gated connector** (this story's decision) — the executor injects it, mirroring
  Phase-37's `build_outbox_connector`, **not** a discovered connector pack. Auth is the
  operator's already-authenticated local `gh`; this connector manages no tokens.
- **Off by default** — the actuator is opt-in + capability-blocked; the connector is only
  reached after approval + the `allow_actuators` policy gate + payload parity + `shell:exec`.
  The default plugin set + routing are unchanged.

## Verification

### Targeted — actuator + connector + full loop

```
$ uv run pytest -q tests/unit/test_github_issue_actuator.py
12 passed in 0.53s
```

- **Faithful proposal** — `target=github` / `action=create_issue` / payload `repo`+`title`+
  `body`, preview names the repo; nothing-unowned → `error`; no `github_repo` → `error`;
  capability off → `blocked`.
- **argv + allow-check** — the connector builds the exact `gh issue create` argv and returns
  the parsed `{url, issue}`; the manifest admits `gh issue create` and refuses `gh repo
  delete` / `gh issue close`; payload metacharacters stay argv tokens (no injection).
- **Refusal before egress** — a non-allow-listed argv raises `ConnectorOperationRefused`
  with the runner (spy) never invoked.
- **Full loop (injected runner)** — execute-before-approval is refused (no `gh` call);
  approve → execute → `executed` with `{"url": ".../issues/9", "issue": 9}` + audit
  `proposed→approved→executed`; a non-zero `gh` exit → `failed` + audit (error carries the
  `gh` stderr); a runner that raises → `failed`.
- **Default set** — `github_issue_actuator` is not in `register_builtin_plugins`.

### Full suite + lint

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2104 passed, 15 skipped in 62.97s        # +12 vs HS-38-01 (the new connector tests)
$ uv run ruff check holdspeak/plugins/builtin/github_issue_actuator.py tests/unit/test_github_issue_actuator.py
All checks passed!
$ uv run ruff check --select F821 holdspeak/plugins/builtin/github_issue_actuator.py
All checks passed!
```

The default suite makes **no real `gh` call** — every test injects a fake runner.

## Notes

- **Manual / opt-in real run (documented, not CI):** with an authenticated local `gh` and a
  throwaway repo, an end-to-end check is
  `build_github_issue_connector()` (real `subprocess.run`) driven through the executor on an
  approved proposal whose payload `repo` points at the throwaway repo → a real issue is
  filed and its URL returned. Not run here (remote, no throwaway repo); the injected-runner
  loop proves the wiring deterministically.
- The actuator reads the target repo from `context["github_repo"]`; wiring that context key
  from project config is a downstream concern (the actuator's `run()` stays pure — the `gh`
  call lives only in the connector, reached only after approval + the gate).
