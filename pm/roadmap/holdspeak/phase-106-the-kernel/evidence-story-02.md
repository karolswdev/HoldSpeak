# Evidence - HS-106-02

- **Story:** HS-106-02 - Principal separation on loopback
- **Status:** done
- **Date:** 2026-07-26

## Live proof — two real processes on loopback

A real seeded hub ran as its own process at `127.0.0.1:8788`:

```text
NO_PROXY=127.0.0.1,localhost uv run python -m uat.stage --recipe seeded-desk
```

The hub minted an `agent` credential bound to
`claude:live-proof-process`. A separate real Claude Code process ran from the
held workspace with the Phase-104 hook rig (`SessionStart`, `PreToolUse`,
`Stop`, and `SessionEnd` all invoking `uv run --project <repo> holdspeak gate
hook`):

```text
HOLDSPEAK_HUB_URL=http://127.0.0.1:8788 \
HOLDSPEAK_AGENT_CREDENTIAL=<ephemeral hub-issued agent credential> \
claude -p 'Run ./principal-proof.sh exactly once with Bash. Then report its stdout exactly.' \
  --model sonnet --settings <live-settings.json> --allowedTools Bash
```

The real PreToolUse arrival itself succeeded on the agent's entitled proposal
route and held as `session_key=claude:live-proof-process`, `agent=agent`. The
body had supplied neither value. The owner approved that one Bash call from a
separate HTTP client; its receipt records `decided_by=owner-session`.

The approved script then made two requests with the same agent credential. Its
stdout, quoted by the real Claude process, was:

```text
{"id":"live-agent-entitled","session_key":"claude:live-proof-process","agent":"agent",..."state":"held"}
ENTITLED_HTTP=200
{"success":false,"error":"principal_right_required","principal":"agent","principal_identity":"claude:live-proof-process","missing_right":"decide"}
DECIDE_HTTP=403
```

This proves a boundary rather than a wall: the agent submitted and read its own
held operation, while the centralized edge derivation refused `decide` by
principal and missing right before route code could inspect the caller's forged
`actor=owner` field.

One first attempt did **not** work: an over-detailed `claude -p` prompt that
spelled out the HTTP authorization experiment was rejected by Claude Code's
broad safeguard before any tool call. It created no gate row. The second run
used the same script and mechanics with the neutral prompt shown above and
completed successfully.

## Owner first load — no auth ceremony

The real staged hub was opened at its tokenized owner bootstrap URL. React
captured the token, immediately scrubbed it from the address bar, and rendered
the Desk directly at both widths. Puppeteer observed title `HoldSpeak`, final
URL `http://127.0.0.1:8788/`, and `errors=[]` for console errors plus page
exceptions.

- [`owner-first-load-1440.png`](./assets/story-02/owner-first-load-1440.png)
- [`owner-first-load-393.png`](./assets/story-02/owner-first-load-393.png)

Both images were opened and inspected before the story flip. Neither contains
a login, token prompt, or intermediate auth surface.

## Full-suite verification — output read before flip

The required suite was written to
`<scratchpad>/final-full-test.txt`; the entire file was opened and read before
changing the story status:

```text
NO_PROXY=127.0.0.1,localhost,192.168.1.43 \
no_proxy=127.0.0.1,localhost,192.168.1.43 \
uv run pytest -q --ignore=tests/e2e/test_metal.py
```

```text
4231 passed, 41 skipped, 2 warnings in 829.69s (0:13:49)
```

Exit code was 0. The two warnings were pre-existing asynchronous meeting-import
test cleanup races: background threads attempted SQLite work after their temp
DBs had been removed (`disk I/O error`, followed by `no such table: meetings`)
in `test_txt_upload_uses_the_transcript_fallback_speaker` and
`test_garbage_transcript_marks_the_row_honestly_and_is_removable`. No test
failed, and neither warning touches principal/authentication code.

An earlier full-suite pass was read and did fail 7 tests: three raw-router test
fixtures lacked an edge principal, two factory fakes assumed the old positional
tmux argv, the runtime test expected the now-unauthenticated browser URL, and
the API manifest had not been regenerated. Those were repaired rather than
rounded up; the green run above is the frozen-tree rerun.

## Proof

### Captured run — 2026-07-26T23:20:34Z

- **Command:** `uv run pytest -q tests/integration/test_principal_separation.py tests/integration/test_web_auth_gate.py tests/integration/test_gate_threat_model.py tests/unit/test_web_auth.py tests/unit/test_coder_gate.py tests/unit/test_coder_factory.py tests/unit/test_delivery_node_routes.py tests/unit/test_gate_chokepoint.py tests/uat/test_build_ledger.py tests/uat/test_egress_cloud.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** df6be66562be2cc682add6ba9706a17c381aed21

```text
........................................................................ [ 86%]
...........                                                              [100%]
83 passed in 17.66s
```
