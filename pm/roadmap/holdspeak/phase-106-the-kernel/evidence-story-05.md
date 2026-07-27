# Evidence - HS-106-05

- **Story:** HS-106-05 - Thin slice I — terminal input
- **Status:** done
- **Date:** 2026-07-26

## Outcome

`process.input@1` is the second real operation driver. Terminal text now enters
through the kernel, correlates to the existing immutable delivery command by
`command_id`, claims through the executor plane, and closes from the native
receipt. `HubCommandService`, `NodeCommandProcessor`, the node envelope/result
wire shapes, `coder_steering.deliver`, and `send_text_to_pane` remain the native
protocol and executors. Delivery and coder façades preserve their prior fields
and add only `operation_id`; keys, kill, spawn, launch, dictation, Cadence, and
other typing families remain unmigrated.

The live rig below used a real spawned hub and real tmux panes. One interactive
Claude session received its prompt through the coder façade and
`submit(process.input)`; its final kernel receipt succeeded in 84.76 ms, below the
Phase-104 250 ms unarmed budget. Two separate real `claude -p --settings`
sessions exercised the unchanged PreToolUse/Stop gate rig: one owner approval
ran, one owner denial did not create its sentinel file, and the exact denial
reason reached Claude verbatim. The audit census found exactly one decision for
each proposal.

A real forked node typed into a real tmux pane, was sent SIGKILL after the text
landed but before its native receipt persisted, then restarted on the same
ledger. Reconciliation by the existing command ID returned
`indeterminate_after_node_reset`; the linked kernel receipt is
`indeterminate`. No blind retry occurred. A second guard covers the pre-claim
case: a dropped native queue item closes as a kernel refusal rather than leaving
an awaiting operation orphaned.

## Where the spine resisted

The Phase-104/94 domain lifecycle and the generic kernel lifecycle overlap but
are not identical. The generic claim originally selected only the oldest item
for a placement; that is insufficient when the authoritative native queue has
already established an exact command order or has deliberately dropped an
older item. The executor plane therefore gained a generic optional `native_id`
selector. It contains no terminal name or branch, preserves the public node
wire protocol, and lets the adapter claim the exact correlated operation. In
this slice terminal delivery is the **only** caller that passes `native_id`;
tool-call claim still uses placement order. The selector is needed because the
native queue is authoritative and can lose or reconcile one command while
other operations share the placement, but it is not yet validated by a second
heterogeneous driver. HS-106-06 must confirm or refute this general seam; this
slice generalizes it no further.

An initial implementation also allowed a placement-matched node to file an
unclaimed refusal. Review correctly identified that as a semantic weakening of
the executor plane: a node could refuse an owner-approved operation placed on
it without consuming the one-use claim. That change was reverted. The terminal
adapter now exact-claims responsibility first, then records `not_executed` as a
refusal. Admission rejection would be dishonest here because the concrete
sequence is later: the owner approved, the native in-memory queue was lost
before the node polled (for example at hub restart), and the authoritative
native row proves the send remained `sent`. The claim is therefore the node's
terminalization responsibility, not a claim that bytes ran. A kernel test pins
all three fences: same-node unclaimed refusal is rejected, same-node unclaimed
success is rejected, and another node cannot receipt the operation.

The broker still does not dispatch native drivers or expose codec payloads from
`claim`; the terminal adapter must join operation ID to command ID outside the
broker. `OperationSpec.interruption` is static, so the owner gesture is adapted
as the generic submit/approve/claim sequence rather than hidden behind a
terminal conditional. Those seams are recorded here rather than disguised as
strategy tables. Authority is constructed in one place:
`_authority_for()` resolves the native policy once and delegates encoding to
`_authority_from_policy()`; supplied snapshots use that same encoder. The unit
census monkeypatches `resolve_policy` and observes exactly one call for a send,
while the real gate audit observes one decision row per proposal. Every broker
module remains under 300 lines and the zero-driver-conditional census is green.

The executor plane resisted this driver at the receipt-without-claim boundary
(an approved command whose native row stayed `sent` after the queue vanished on
restart still owes a terminal receipt under Article XI clause 2), and it was
resolved in the **adapter** rather than by relaxing the spine. `native_id`
currently has exactly one filtered caller, and HS-106-06 must confirm or refute
it.

The effect ledger is unchanged: T01 (`coder_steering.deliver` → terminal send)
was already `covered`, and this slice moved no bypass entry to covered.

## Full-suite adjudication

The final required command, `uv run pytest -q
--ignore=tests/e2e/test_metal.py`, completed with **4,252 passed, 39 skipped,
8 failed, 1 warning in 1,001.39 seconds**. None of the eight failures is caused
by this slice:

- All three `tests/e2e/test_live_bus.py` failures reproduce together on the
  clean `origin/main` archive: **3 failed in 17.76 seconds**, with the same
  unauthenticated WebSocket retries and missing presence broadcast.
- The four induction/mesh/pack failures reproduce together on that same clean
  archive: **4 failed in 422.63 seconds**, with the same queued intel timeout,
  missing OpenAI extra, mesh 502/canary absence, and Pack-D staging result.
- `tests/uat/test_voice_notes.py::test_transcribe_up_but_unreachable_is_honest`
  is the known wording-drift failure (`Transcribe failed (HTTP 502).`).

The first post-review full run also exposed this slice's one genuine regression:
`coder_steering_routes.py` exceeded its existing 600-line density budget. The
kernel adaptation was moved into the existing `coder_steering_support.py`
concern; the final density guard is green and the route is 597 lines.

## Proof

### Captured run — 2026-07-27T04:35:31Z

- **Command:** `uv run pytest -q tests/unit/test_process_input_kernel.py tests/integration/test_process_input_real_hub.py tests/unit/test_delivery_commands.py tests/unit/test_delivery_terminal_routes.py tests/unit/test_web_routes_coders_steer.py tests/unit/test_kernel_effect_fence.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
........................................................................ [ 90%]
........                                                                 [100%]
80 passed in 11.74s
```

### Captured run — 2026-07-27T04:36:12Z

- **Command:** `bash -euo pipefail -c uv run pytest -q tests/unit/test_kernel_effect_fence.py::test_kernel_broker_modules_stay_within_line_budget tests/unit/test_kernel_effect_fence.py::test_kernel_broker_has_zero_driver_specific_conditionals && wc -l holdspeak/kernel/*.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
..                                                                       [100%]
2 passed in 0.05s
       9 holdspeak/kernel/__init__.py
      64 holdspeak/kernel/admission.py
     224 holdspeak/kernel/broker.py
     111 holdspeak/kernel/executor.py
     266 holdspeak/kernel/journal.py
      70 holdspeak/kernel/model.py
     129 holdspeak/kernel/process_input.py
      90 holdspeak/kernel/runtime.py
     144 holdspeak/kernel/tool_call.py
    1107 total
```

### Captured run — 2026-07-27T04:36:29Z

- **Command:** `uv run python /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/755cdf1e-8c7b-4e33-923d-a46dc3bb7d49/scratchpad/live_process_input_gate.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
can't find session: hs10605_approve_20791
can't find session: hs10605_deny_20791
{"gated_approve": {"decision": "approved", "output": "stdout: `GATE_APPROVE_KERNEL_10605`\n", "proposal_id": "toolu_01MqJ76TFXUZGFVtBNafgN3P", "reason_verbatim": null}, "gated_deny": {"decision": "denied", "effect_absent": true, "output": "The command was denied. Denial reason quoted verbatim: **\"denied from the desk: kernel desk says no files today\"**\n", "proposal_id": "toolu_01Agb1RdVNMG4mEskEQLE2ia", "reason_verbatim": true}, "one_decision_each": {"toolu_01Agb1RdVNMG4mEskEQLE2ia": 1, "toolu_01MqJ76TFXUZGFVtBNafgN3P": 1}, "real_send": {"latency_ms": 96.14, "marker_seen": true, "operation_id": "op_64e20d42d564463193aee7adbb02411c", "receipt": "succeeded"}}
```

### Captured run — 2026-07-27T04:37:18Z

- **Command:** `uv run pytest -q -s tests/integration/test_process_input_real_hub.py::test_real_sigkill_mid_send_reconciles_indeterminate_by_command_id`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
{"aggregate": "indeterminate_after_node_reset", "command_id": "dd85c6d2-afdc-4a11-9b8c-bde81c01cbb5", "kernel_receipt": "indeterminate", "operation_id": "op_03483abe14384ccfac83e719e3ef9386", "reconcile": "by_command_id", "sigkill": -9, "text_landed": "LANDED_BEFORE_SIGKILL_10605"}
.
1 passed in 0.21s
```

### Captured run — 2026-07-27T04:50:13Z

- **Command:** `uv run pytest -q tests/unit/test_process_input_kernel.py tests/integration/test_process_input_real_hub.py tests/unit/test_delivery_commands.py tests/unit/test_delivery_terminal_routes.py tests/unit/test_web_routes_coders_steer.py tests/unit/test_kernel_effect_fence.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
...F.................................................................... [ 90%]
........                                                                 [100%]
=================================== FAILURES ===================================
______________ test_real_http_process_input_types_into_real_tmux _______________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-515/test_real_http_process_input_t0')

    @pytest.mark.skipif(shutil.which("tmux") is None, reason="tmux is required for real terminal proof")
    def test_real_http_process_input_types_into_real_tmux(tmp_path: Path) -> None:
        home = tmp_path / "home"
        config = home / ".config" / "holdspeak" / "config.json"
        config.parent.mkdir(parents=True)
        config.write_text(
            json.dumps(
                {
                    "config_version": 1,
                    "control_mode": "yolo",
                    "meeting": {"web_auth_token": _OWNER_TOKEN},
                }
            ),
            encoding="utf-8",
        )
        received = tmp_path / "received.txt"
        tmux_name = f"hs10605_{os.getpid()}"
        subprocess.run(
            [
                "tmux",
                "new-session",
                "-d",
                "-s",
                tmux_name,
                f"sh -c 'IFS= read -r line; printf %s \"$line\" > {received}; sleep 3'",
            ],
            check=True,
        )
        pane = subprocess.run(
            ["tmux", "display-message", "-p", "-t", f"{tmux_name}:0.0", "#{pane_id}"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        env = os.environ.copy()
        env.update(HOME=str(home), HOLDSPEAK_WEB_PORT=str(port), PYTHONUNBUFFERED="1")

        def request(method: str, path: str, body: Any = None) -> tuple[int, dict[str, Any]]:
            data = None if body is None else json.dumps(body).encode()
            outgoing = urllib.request.Request(
                base + path,
                data=data,
                headers={
                    "content-type": "application/json",
                    "authorization": f"Bearer {_OWNER_TOKEN}",
                },
                method=method,
            )
            try:
                with urllib.request.urlopen(outgoing, timeout=10) as response:
                    return response.status, json.load(response)
            except urllib.error.HTTPError as exc:
                return exc.code, json.load(exc)

        hub = subprocess.Popen(
            [sys.executable, "-m", "holdspeak.main", "web", "--no-open"],
            cwd=_REPO,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            for _ in range(100):
                if hub.poll() is not None:
                    output = hub.stdout.read() if hub.stdout else ""
                    raise AssertionError(f"spawned hub exited early:\n{output}")
                try:
                    with urllib.request.urlopen(base + "/health", timeout=0.2):
                        break
                except Exception:
                    time.sleep(0.1)
            else:
                hub.kill()
                output = hub.stdout.read() if hub.stdout else ""
>               raise AssertionError(f"spawned hub did not become healthy:\n{output}")
E               AssertionError: spawned hub did not become healthy:

tests/integration/test_process_input_real_hub.py:112: AssertionError
=========================== short test summary info ============================
FAILED tests/integration/test_process_input_real_hub.py::test_real_http_process_input_types_into_real_tmux
1 failed, 79 passed in 23.84s
```

### Captured run — 2026-07-27T04:51:49Z

- **Command:** `uv run pytest -q tests/unit/test_process_input_kernel.py tests/integration/test_process_input_real_hub.py tests/unit/test_delivery_commands.py tests/unit/test_delivery_terminal_routes.py tests/unit/test_web_routes_coders_steer.py tests/unit/test_kernel_effect_fence.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
........................................................................ [ 90%]
........                                                                 [100%]
80 passed in 7.44s
```

### Captured run — 2026-07-27T05:16:05Z

- **Command:** `uv run pytest -q tests/unit/test_process_input_kernel.py tests/integration/test_process_input_real_hub.py tests/unit/test_delivery_commands.py tests/unit/test_delivery_terminal_routes.py tests/unit/test_web_routes_coders_steer.py tests/unit/test_kernel_effect_fence.py tests/unit/test_kernel_broker.py tests/integration/test_delivery_campaign.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
........................................................................ [ 75%]
........................                                                 [100%]
96 passed in 19.14s
```

### Captured run — 2026-07-27T05:20:33Z

- **Command:** `uv run pytest -q tests/unit/test_process_input_kernel.py tests/integration/test_process_input_real_hub.py tests/unit/test_delivery_commands.py tests/unit/test_delivery_terminal_routes.py tests/unit/test_web_routes_coders_steer.py tests/unit/test_kernel_effect_fence.py tests/unit/test_kernel_broker.py tests/integration/test_delivery_campaign.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
........................................................................ [ 74%]
.........................                                                [100%]
97 passed in 19.45s
```

### Captured run — 2026-07-27T05:21:02Z

- **Command:** `bash -euo pipefail -c uv run pytest -q tests/unit/test_kernel_effect_fence.py::test_kernel_broker_modules_stay_within_line_budget tests/unit/test_kernel_effect_fence.py::test_kernel_broker_has_zero_driver_specific_conditionals && wc -l holdspeak/kernel/*.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
..                                                                       [100%]
2 passed in 0.06s
       9 holdspeak/kernel/__init__.py
      64 holdspeak/kernel/admission.py
     224 holdspeak/kernel/broker.py
     116 holdspeak/kernel/executor.py
     270 holdspeak/kernel/journal.py
      70 holdspeak/kernel/model.py
     129 holdspeak/kernel/process_input.py
      90 holdspeak/kernel/runtime.py
     144 holdspeak/kernel/tool_call.py
    1116 total
```

### Captured run — 2026-07-27T05:23:22Z

- **Command:** `uv run pytest -q tests/unit/test_process_input_kernel.py tests/integration/test_process_input_real_hub.py tests/unit/test_delivery_commands.py tests/unit/test_delivery_terminal_routes.py tests/unit/test_web_routes_coders_steer.py tests/unit/test_kernel_effect_fence.py tests/unit/test_kernel_broker.py tests/integration/test_delivery_campaign.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
........................................................................ [ 72%]
...........................                                              [100%]
99 passed in 20.89s
```

### Captured run — 2026-07-27T05:26:33Z

- **Command:** `uv run pytest -q tests/unit/test_process_input_kernel.py tests/integration/test_process_input_real_hub.py tests/unit/test_delivery_commands.py tests/unit/test_delivery_terminal_routes.py tests/unit/test_web_routes_coders_steer.py tests/unit/test_kernel_effect_fence.py tests/unit/test_kernel_broker.py tests/integration/test_delivery_campaign.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
........................................................................ [ 72%]
...........................                                              [100%]
99 passed in 17.62s
```

### Captured run — 2026-07-27T05:28:58Z

- **Command:** `bash -c cd /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/755cdf1e-8c7b-4e33-923d-a46dc3bb7d49/scratchpad/baseline-main && PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-acfa3f9b75105e6ab/.venv/bin/pytest -q tests/e2e/test_live_bus.py::test_every_live_page_opens_exactly_one_runtime_socket`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
F                                                                        [100%]
=================================== FAILURES ===================================
____________ test_every_live_page_opens_exactly_one_runtime_socket _____________

browser = <Browser type=<BrowserType name=chromium executable_path=/Users/karol/Library/Caches/ms-playwright/chromium-1200/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing> version=143.0.7499.4>

    def test_every_live_page_opens_exactly_one_runtime_socket(browser):
        server = _make_server()
        uv = _Uvicorn(server.app)
        uv.start()
        try:
            for route in ("/live", "/dictation", "/presence", "/setup"):
                page = browser.new_page()
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                n = _count_runtime_sockets(page, f"http://127.0.0.1:{PORT}{route}")
                page.close()
>               assert n == 1, f"{route} opened {n} runtime sockets (want exactly 1)"
E               AssertionError: /live opened 3 runtime sockets (want exactly 1)
E               assert 3 == 1

tests/e2e/test_live_bus.py:96: AssertionError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
=========================== short test summary info ============================
FAILED tests/e2e/test_live_bus.py::test_every_live_page_opens_exactly_one_runtime_socket
1 failed in 5.18s
```

### Captured run — 2026-07-27T05:33:03Z

- **Command:** `uv run pytest -q tests/unit/test_process_input_kernel.py tests/integration/test_process_input_real_hub.py tests/unit/test_delivery_commands.py tests/unit/test_delivery_terminal_routes.py tests/unit/test_web_routes_coders_steer.py tests/unit/test_kernel_effect_fence.py tests/unit/test_kernel_broker.py tests/integration/test_delivery_campaign.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
........................................................................ [ 72%]
...........................                                              [100%]
99 passed in 18.98s
```

### Captured run — 2026-07-27T05:40:44Z

- **Command:** `uv run pytest -q tests/unit/test_process_input_kernel.py tests/integration/test_process_input_real_hub.py tests/unit/test_delivery_commands.py tests/unit/test_delivery_terminal_routes.py tests/unit/test_web_routes_coders_steer.py tests/unit/test_kernel_effect_fence.py tests/unit/test_kernel_broker.py tests/integration/test_delivery_campaign.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
........................................................................ [ 72%]
...........................                                              [100%]
99 passed in 19.93s
```

### Captured run — 2026-07-27T05:50:05Z

- **Command:** `uv run pytest -q tests/unit/test_process_input_kernel.py tests/integration/test_process_input_real_hub.py tests/unit/test_delivery_commands.py tests/unit/test_delivery_terminal_routes.py tests/unit/test_web_routes_coders_steer.py tests/unit/test_kernel_effect_fence.py tests/unit/test_kernel_broker.py tests/integration/test_delivery_campaign.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
........................................................................ [ 72%]
...........................                                              [100%]
99 passed in 17.79s
```

### Captured run — 2026-07-27T05:50:47Z

- **Command:** `uv run python /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/755cdf1e-8c7b-4e33-923d-a46dc3bb7d49/scratchpad/live_process_input_gate.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
can't find session: hs10605_approve_86028
can't find session: hs10605_deny_86028
{"gated_approve": {"decision": "approved", "output": "stdout: `GATE_APPROVE_KERNEL_10605`\n", "proposal_id": "toolu_01NPNEMyaJZneZHv8cXgFxB2", "reason_verbatim": null}, "gated_deny": {"decision": "denied", "effect_absent": true, "output": "The command was denied. Denial reason verbatim: \"denied from the desk: kernel desk says no files today\"\n", "proposal_id": "toolu_01UDT7DwnMN4c3Q1WiW3hPjp", "reason_verbatim": true}, "one_decision_each": {"toolu_01NPNEMyaJZneZHv8cXgFxB2": 1, "toolu_01UDT7DwnMN4c3Q1WiW3hPjp": 1}, "real_send": {"latency_ms": 124.68, "marker_seen": true, "operation_id": "op_b631257570af45b0b9b1d4a4b663f657", "receipt": "succeeded"}}
```

### Captured run — 2026-07-27T05:51:47Z

- **Command:** `bash -euo pipefail -c uv run pytest -q tests/unit/test_kernel_effect_fence.py::test_kernel_broker_modules_stay_within_line_budget tests/unit/test_kernel_effect_fence.py::test_kernel_broker_has_zero_driver_specific_conditionals && wc -l holdspeak/kernel/*.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
..                                                                       [100%]
2 passed in 0.05s
       9 holdspeak/kernel/__init__.py
      64 holdspeak/kernel/admission.py
     224 holdspeak/kernel/broker.py
     111 holdspeak/kernel/executor.py
     270 holdspeak/kernel/journal.py
      70 holdspeak/kernel/model.py
     133 holdspeak/kernel/process_input.py
      90 holdspeak/kernel/runtime.py
     144 holdspeak/kernel/tool_call.py
    1115 total
```

### Captured run — 2026-07-27T06:00:54Z

- **Command:** `bash -c cd /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/755cdf1e-8c7b-4e33-923d-a46dc3bb7d49/scratchpad/baseline-main && PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-acfa3f9b75105e6ab/.venv/bin/pytest -q tests/e2e/test_live_bus.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
FFF                                                                      [100%]
=================================== FAILURES ===================================
____________ test_every_live_page_opens_exactly_one_runtime_socket _____________

browser = <Browser type=<BrowserType name=chromium executable_path=/Users/karol/Library/Caches/ms-playwright/chromium-1200/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing> version=143.0.7499.4>

    def test_every_live_page_opens_exactly_one_runtime_socket(browser):
        server = _make_server()
        uv = _Uvicorn(server.app)
        uv.start()
        try:
            for route in ("/live", "/dictation", "/presence", "/setup"):
                page = browser.new_page()
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                n = _count_runtime_sockets(page, f"http://127.0.0.1:{PORT}{route}")
                page.close()
>               assert n == 1, f"{route} opened {n} runtime sockets (want exactly 1)"
E               AssertionError: /live opened 3 runtime sockets (want exactly 1)
E               assert 3 == 1

tests/e2e/test_live_bus.py:96: AssertionError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
_________ test_a_real_broadcast_reaches_the_presence_card_via_the_bus __________

browser = <Browser type=<BrowserType name=chromium executable_path=/Users/karol/Library/Caches/ms-playwright/chromium-1200/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing> version=143.0.7499.4>

    def test_a_real_broadcast_reaches_the_presence_card_via_the_bus(browser):
        server = _make_server()
        uv = _Uvicorn(server.app)
        uv.start()
        try:
            page = browser.new_page()
            page.goto(f"http://127.0.0.1:{PORT}/presence", wait_until="networkidle")
            page.wait_for_timeout(800)
            server.broadcast(
                "runtime_activity",
                {
                    "state": "transcribing",
                    "label": "Transcribing",
                    "source": "dictation",
                    "window": {"visible": True},
                },
            )
>           page.wait_for_function(
                "() => document.querySelector('.presence-card strong')"
                " && document.querySelector('.presence-card strong').textContent.includes('Transcribing')",
                timeout=8000,
            )

tests/e2e/test_live_bus.py:119:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-acfa3f9b75105e6ab/.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:11595: in wait_for_function
    self._sync(
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-acfa3f9b75105e6ab/.venv/lib/python3.13/site-packages/playwright/_impl/_page.py:1110: in wait_for_function
    return await self._main_frame.wait_for_function(**locals_to_params(locals()))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-acfa3f9b75105e6ab/.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:878: in wait_for_function
    await self._channel.send("waitForFunction", self._timeout, params)
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-acfa3f9b75105e6ab/.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <playwright._impl._connection.Connection object at 0x10c36ef90>
cb = <function Channel.send.<locals>.<lambda> at 0x110f0e3e0>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)

        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 8000ms exceeded.

/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-acfa3f9b75105e6ab/.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
________________ test_the_bus_reconnects_after_a_server_restart ________________

browser = <Browser type=<BrowserType name=chromium executable_path=/Users/karol/Library/Caches/ms-playwright/chromium-1200/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing> version=143.0.7499.4>

    def test_the_bus_reconnects_after_a_server_restart(browser):
        server = _make_server()
        uv = _Uvicorn(server.app)
        uv.start()
        page = browser.new_page()
        sockets: list[str] = []
        page.on("websocket", lambda ws: sockets.append(ws.url))
        try:
            page.goto(f"http://127.0.0.1:{PORT}/presence", wait_until="networkidle")
            page.wait_for_timeout(1000)
            first = sum(1 for u in sockets if u.rstrip("/").endswith("/ws"))
>           assert first == 1
E           assert 3 == 1

tests/e2e/test_live_bus.py:140: AssertionError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
=========================== short test summary info ============================
FAILED tests/e2e/test_live_bus.py::test_every_live_page_opens_exactly_one_runtime_socket
FAILED tests/e2e/test_live_bus.py::test_a_real_broadcast_reaches_the_presence_card_via_the_bus
FAILED tests/e2e/test_live_bus.py::test_the_bus_reconnects_after_a_server_restart
3 failed in 17.76s
```

### Captured run — 2026-07-27T05:52:07Z

- **Command:** `bash -o pipefail -c uv run pytest -q --ignore=tests/e2e/test_metal.py 2>&1 | tee /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/755cdf1e-8c7b-4e33-923d-a46dc3bb7d49/scratchpad/full-suite-after-review.txt`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
ssssssssssssssssssssssFFFssssssssss..................................... [  1%]
........................................................................ [  3%]
......s................................................................. [  5%]
.....................................................................ss. [  6%]
........................................................................ [  8%]
........................................................................ [ 10%]
........................................................................ [ 11%]
........................................................................ [ 13%]
........................................................................ [ 15%]
........................................................................ [ 16%]
........................................................................ [ 18%]
...............................................................F...F.... [ 20%]
...F...........F........................................................ [ 21%]
...................F.................................................... [ 23%]
........................................................................ [ 25%]
........................................................................ [ 26%]
........................................................................ [ 28%]
........................................................................ [ 30%]
.....................................................F.................. [ 31%]
........................................................................ [ 33%]
........................................................................ [ 35%]
........................................................................ [ 36%]
........................................................................ [ 38%]
........................................................................ [ 40%]
........................................................................ [ 41%]
........................................................................ [ 43%]
........................................................................ [ 45%]
........................................................................ [ 46%]
........................................................................ [ 48%]
........................................................................ [ 50%]
........................................................................ [ 51%]
........................................................................ [ 53%]
........................................................................ [ 55%]
........................s............................................... [ 56%]
........................................................................ [ 58%]
........................................................................ [ 60%]
........................................................................ [ 62%]
........................................................................ [ 63%]
........................................................................ [ 65%]
........................................................................ [ 67%]
........................................................................ [ 68%]
........................................................................ [ 70%]
........................................................................ [ 72%]
........................................................................ [ 73%]
........................................................................ [ 75%]
........................................................................ [ 77%]
........................................................................ [ 78%]
........................................................................ [ 80%]
........................................................................ [ 82%]
........................................................................ [ 83%]
........................................................................ [ 85%]
........................................................................ [ 87%]
........................................................................ [ 88%]
........................................................................ [ 90%]
........................................................................ [ 92%]
........................................................................ [ 93%]
........................................................................ [ 95%]
........................................................................ [ 97%]
........................................................................ [ 98%]
................................................                         [100%]
=================================== FAILURES ===================================
____________ test_every_live_page_opens_exactly_one_runtime_socket _____________

browser = <Browser type=<BrowserType name=chromium executable_path=/Users/karol/Library/Caches/ms-playwright/chromium-1200/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing> version=143.0.7499.4>

    def test_every_live_page_opens_exactly_one_runtime_socket(browser):
        server = _make_server()
        uv = _Uvicorn(server.app)
        uv.start()
        try:
            for route in ("/live", "/dictation", "/presence", "/setup"):
                page = browser.new_page()
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                n = _count_runtime_sockets(page, f"http://127.0.0.1:{PORT}{route}")
                page.close()
>               assert n == 1, f"{route} opened {n} runtime sockets (want exactly 1)"
E               AssertionError: /live opened 3 runtime sockets (want exactly 1)
E               assert 3 == 1

tests/e2e/test_live_bus.py:96: AssertionError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
_________ test_a_real_broadcast_reaches_the_presence_card_via_the_bus __________

browser = <Browser type=<BrowserType name=chromium executable_path=/Users/karol/Library/Caches/ms-playwright/chromium-1200/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing> version=143.0.7499.4>

    def test_a_real_broadcast_reaches_the_presence_card_via_the_bus(browser):
        server = _make_server()
        uv = _Uvicorn(server.app)
        uv.start()
        try:
            page = browser.new_page()
            page.goto(f"http://127.0.0.1:{PORT}/presence", wait_until="networkidle")
            page.wait_for_timeout(800)
            server.broadcast(
                "runtime_activity",
                {
                    "state": "transcribing",
                    "label": "Transcribing",
                    "source": "dictation",
                    "window": {"visible": True},
                },
            )
>           page.wait_for_function(
                "() => document.querySelector('.presence-card strong')"
                " && document.querySelector('.presence-card strong').textContent.includes('Transcribing')",
                timeout=8000,
            )

tests/e2e/test_live_bus.py:119:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:11595: in wait_for_function
    self._sync(
.venv/lib/python3.13/site-packages/playwright/_impl/_page.py:1110: in wait_for_function
    return await self._main_frame.wait_for_function(**locals_to_params(locals()))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:878: in wait_for_function
    await self._channel.send("waitForFunction", self._timeout, params)
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <playwright._impl._connection.Connection object at 0x112cc6ba0>
cb = <function Channel.send.<locals>.<lambda> at 0x113d83d80>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)

        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 8000ms exceeded.

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
________________ test_the_bus_reconnects_after_a_server_restart ________________

browser = <Browser type=<BrowserType name=chromium executable_path=/Users/karol/Library/Caches/ms-playwright/chromium-1200/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing> version=143.0.7499.4>

    def test_the_bus_reconnects_after_a_server_restart(browser):
        server = _make_server()
        uv = _Uvicorn(server.app)
        uv.start()
        page = browser.new_page()
        sockets: list[str] = []
        page.on("websocket", lambda ws: sockets.append(ws.url))
        try:
            page.goto(f"http://127.0.0.1:{PORT}/presence", wait_until="networkidle")
            page.wait_for_timeout(1000)
            first = sum(1 for u in sockets if u.rstrip("/").endswith("/ws"))
>           assert first == 1
E           assert 3 == 1

tests/e2e/test_live_bus.py:140: AssertionError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
________________ test_meeting_recipe_yields_a_real_open_action _________________

real_manager = <uat.conductor.runs.RunManager object at 0x11494ef30>

    def test_meeting_recipe_yields_a_real_open_action(real_manager):
        run = _boot_or_skip(real_manager, "golden-43")
>       result = real_manager.apply_recipe(run.id, "meeting-just-ended-open-actions")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/uat/test_induction_integration_43.py:52:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
uat/conductor/runs.py:387: in apply_recipe
    return self.recipes.apply(name, run_id, self, allow_intel=allow_intel)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <uat.conductor.induction.recipes.RecipeEngine object at 0x1380d5010>
name = 'meeting-just-ended-open-actions', run_id = 'run-20260727T055648-5c9621'
host = <uat.conductor.runs.RunManager object at 0x11494ef30>

    def apply(
        self, name: str, run_id: str, host: "RecipeHost", *, allow_intel: bool = True
    ) -> ApplyResult:
        order = self.registry.resolve_order(name)
        target = self.registry.load(name)

        if target.requires_intel and not allow_intel:
            raise RecipeError(
                f"recipe {name!r} requires intel (the .43 LAN endpoint) but "
                "intel is disabled for this apply"
            )

        # 1. Ensure the run is booted on the recipe's deck + cache posture.
        restarted = host.ensure_deck(run_id, target.deck, link_caches=target.link_caches)

        client = host.product_client(run_id)
        home = host.run_home(run_id)
        evaluator = ProbeEvaluator(client, home=home, run_id=run_id)

        # The combined probe is the target's own probe (includes stage the world;
        # the target's probe is the authoritative claim). Included recipes still
        # contribute their seeds/actions below.
        probe_spec = target.probe

        # 2. Probe-first idempotency.
        pre = evaluator.evaluate(probe_spec)
        if pre.ok and probe_spec:
            return ApplyResult(
                recipe=name,
                deck=target.deck,
                already_satisfied=True,
                probe=pre.to_dict(),
                restarted=restarted,
            )

        # 3. Stage: seeds (deps first), then actions (deps first).
        seed_outcomes: list[dict] = []
        action_log: list[dict] = []
        for rn in order:
            r = self.registry.load(rn)
            for seed_name in r.seeds:
                manifest = self.seed_registry.load(seed_name)
                seed_outcomes.append(Seeder(client).apply(manifest).to_dict())
            for action in r.actions:
                action_log.append(self._run_action(action, run_id, host, client))

        # 4. Verify.
        post = evaluator.evaluate(probe_spec)
        result = ApplyResult(
            recipe=name,
            deck=target.deck,
            already_satisfied=False,
            probe=post.to_dict(),
            seeds=seed_outcomes,
            actions=action_log,
            restarted=restarted,
        )
        if probe_spec and not post.ok:
>           raise RecipeVerifyError(
                f"recipe {name!r} failed to verify: {post.summary()}", result
            )
E           uat.conductor.induction.recipes.RecipeVerifyError: recipe 'meeting-just-ended-open-actions' failed to verify: meeting_with_open_actions: timed out after 180s: meetings present but none with ≥1 open actions: Pylon incident war room (UAT seed)(0,queued)

uat/conductor/induction/recipes.py:240: RecipeVerifyError
__________________ test_intel_endpoint_dead_degrades_honestly __________________

real_manager = <uat.conductor.runs.RunManager object at 0x1380c0910>

    def test_intel_endpoint_dead_degrades_honestly(real_manager):
        run = _boot_or_skip(real_manager)
>       result = real_manager.apply_recipe(run.id, "intel-endpoint-dead")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/uat/test_induction_integration_local.py:73:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
uat/conductor/runs.py:387: in apply_recipe
    return self.recipes.apply(name, run_id, self, allow_intel=allow_intel)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <uat.conductor.induction.recipes.RecipeEngine object at 0x11644a5d0>
name = 'intel-endpoint-dead', run_id = 'run-20260727T060506-cbca56'
host = <uat.conductor.runs.RunManager object at 0x1380c0910>

    def apply(
        self, name: str, run_id: str, host: "RecipeHost", *, allow_intel: bool = True
    ) -> ApplyResult:
        order = self.registry.resolve_order(name)
        target = self.registry.load(name)

        if target.requires_intel and not allow_intel:
            raise RecipeError(
                f"recipe {name!r} requires intel (the .43 LAN endpoint) but "
                "intel is disabled for this apply"
            )

        # 1. Ensure the run is booted on the recipe's deck + cache posture.
        restarted = host.ensure_deck(run_id, target.deck, link_caches=target.link_caches)

        client = host.product_client(run_id)
        home = host.run_home(run_id)
        evaluator = ProbeEvaluator(client, home=home, run_id=run_id)

        # The combined probe is the target's own probe (includes stage the world;
        # the target's probe is the authoritative claim). Included recipes still
        # contribute their seeds/actions below.
        probe_spec = target.probe

        # 2. Probe-first idempotency.
        pre = evaluator.evaluate(probe_spec)
        if pre.ok and probe_spec:
            return ApplyResult(
                recipe=name,
                deck=target.deck,
                already_satisfied=True,
                probe=pre.to_dict(),
                restarted=restarted,
            )

        # 3. Stage: seeds (deps first), then actions (deps first).
        seed_outcomes: list[dict] = []
        action_log: list[dict] = []
        for rn in order:
            r = self.registry.load(rn)
            for seed_name in r.seeds:
                manifest = self.seed_registry.load(seed_name)
                seed_outcomes.append(Seeder(client).apply(manifest).to_dict())
            for action in r.actions:
                action_log.append(self._run_action(action, run_id, host, client))

        # 4. Verify.
        post = evaluator.evaluate(probe_spec)
        result = ApplyResult(
            recipe=name,
            deck=target.deck,
            already_satisfied=False,
            probe=post.to_dict(),
            seeds=seed_outcomes,
            actions=action_log,
            restarted=restarted,
        )
        if probe_spec and not post.ok:
>           raise RecipeVerifyError(
                f"recipe {name!r} failed to verify: {post.summary()}", result
            )
E           uat.conductor.induction.recipes.RecipeVerifyError: recipe 'intel-endpoint-dead' failed to verify: runtime_endpoint_unreachable: runtime-test ok=False status='unavailable' in 0.0s: Backend 'openai_compatible' requires the 'openai' package. Install with: uv pip install holdspeak[dictation-openai]

uat/conductor/induction/recipes.py:240: RecipeVerifyError
______________ test_run_dispatched_onto_the_worker_returns_badged ______________

real_manager = <uat.conductor.runs.RunManager object at 0x138733890>

    def test_run_dispatched_onto_the_worker_returns_badged(real_manager):
        run = _boot_or_skip(real_manager, "mesh-node")

>       result = real_manager.apply_recipe(run.id, "mesh-run-on-worker")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/uat/test_mesh_dispatch.py:55:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
uat/conductor/runs.py:387: in apply_recipe
    return self.recipes.apply(name, run_id, self, allow_intel=allow_intel)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <uat.conductor.induction.recipes.RecipeEngine object at 0x138caae10>
name = 'mesh-run-on-worker', run_id = 'run-20260727T060510-0ca1fe'
host = <uat.conductor.runs.RunManager object at 0x138733890>

    def apply(
        self, name: str, run_id: str, host: "RecipeHost", *, allow_intel: bool = True
    ) -> ApplyResult:
        order = self.regi
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-07-27T06:13:33Z

- **Command:** `bash -c cd /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/755cdf1e-8c7b-4e33-923d-a46dc3bb7d49/scratchpad/baseline-main && PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-acfa3f9b75105e6ab/.venv/bin/pytest -q tests/uat/test_induction_integration_43.py::test_meeting_recipe_yields_a_real_open_action tests/uat/test_induction_integration_local.py::test_intel_endpoint_dead_degrades_honestly tests/uat/test_mesh_dispatch.py::test_run_dispatched_onto_the_worker_returns_badged tests/uat/test_packs.py::test_pack_d_stages_locally`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
FFFF                                                                     [100%]
=================================== FAILURES ===================================
________________ test_meeting_recipe_yields_a_real_open_action _________________

real_manager = <uat.conductor.runs.RunManager object at 0x10d2f52b0>

    def test_meeting_recipe_yields_a_real_open_action(real_manager):
        run = _boot_or_skip(real_manager, "golden-43")
>       result = real_manager.apply_recipe(run.id, "meeting-just-ended-open-actions")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/uat/test_induction_integration_43.py:52:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
uat/conductor/runs.py:387: in apply_recipe
    return self.recipes.apply(name, run_id, self, allow_intel=allow_intel)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <uat.conductor.induction.recipes.RecipeEngine object at 0x10d2f5a90>
name = 'meeting-just-ended-open-actions', run_id = 'run-20260727T061333-33a5cd'
host = <uat.conductor.runs.RunManager object at 0x10d2f52b0>

    def apply(
        self, name: str, run_id: str, host: "RecipeHost", *, allow_intel: bool = True
    ) -> ApplyResult:
        order = self.registry.resolve_order(name)
        target = self.registry.load(name)

        if target.requires_intel and not allow_intel:
            raise RecipeError(
                f"recipe {name!r} requires intel (the .43 LAN endpoint) but "
                "intel is disabled for this apply"
            )

        # 1. Ensure the run is booted on the recipe's deck + cache posture.
        restarted = host.ensure_deck(run_id, target.deck, link_caches=target.link_caches)

        client = host.product_client(run_id)
        home = host.run_home(run_id)
        evaluator = ProbeEvaluator(client, home=home, run_id=run_id)

        # The combined probe is the target's own probe (includes stage the world;
        # the target's probe is the authoritative claim). Included recipes still
        # contribute their seeds/actions below.
        probe_spec = target.probe

        # 2. Probe-first idempotency.
        pre = evaluator.evaluate(probe_spec)
        if pre.ok and probe_spec:
            return ApplyResult(
                recipe=name,
                deck=target.deck,
                already_satisfied=True,
                probe=pre.to_dict(),
                restarted=restarted,
            )

        # 3. Stage: seeds (deps first), then actions (deps first).
        seed_outcomes: list[dict] = []
        action_log: list[dict] = []
        for rn in order:
            r = self.registry.load(rn)
            for seed_name in r.seeds:
                manifest = self.seed_registry.load(seed_name)
                seed_outcomes.append(Seeder(client).apply(manifest).to_dict())
            for action in r.actions:
                action_log.append(self._run_action(action, run_id, host, client))

        # 4. Verify.
        post = evaluator.evaluate(probe_spec)
        result = ApplyResult(
            recipe=name,
            deck=target.deck,
            already_satisfied=False,
            probe=post.to_dict(),
            seeds=seed_outcomes,
            actions=action_log,
            restarted=restarted,
        )
        if probe_spec and not post.ok:
>           raise RecipeVerifyError(
                f"recipe {name!r} failed to verify: {post.summary()}", result
            )
E           uat.conductor.induction.recipes.RecipeVerifyError: recipe 'meeting-just-ended-open-actions' failed to verify: meeting_with_open_actions: timed out after 180s: meetings present but none with ≥1 open actions: Pylon incident war room (UAT seed)(0,queued)

uat/conductor/induction/recipes.py:240: RecipeVerifyError
__________________ test_intel_endpoint_dead_degrades_honestly __________________

real_manager = <uat.conductor.runs.RunManager object at 0x10d25dd10>

    def test_intel_endpoint_dead_degrades_honestly(real_manager):
        run = _boot_or_skip(real_manager)
>       result = real_manager.apply_recipe(run.id, "intel-endpoint-dead")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/uat/test_induction_integration_local.py:73:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
uat/conductor/runs.py:387: in apply_recipe
    return self.recipes.apply(name, run_id, self, allow_intel=allow_intel)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <uat.conductor.induction.recipes.RecipeEngine object at 0x10d25f110>
name = 'intel-endpoint-dead', run_id = 'run-20260727T061938-4aae7a'
host = <uat.conductor.runs.RunManager object at 0x10d25dd10>

    def apply(
        self, name: str, run_id: str, host: "RecipeHost", *, allow_intel: bool = True
    ) -> ApplyResult:
        order = self.registry.resolve_order(name)
        target = self.registry.load(name)

        if target.requires_intel and not allow_intel:
            raise RecipeError(
                f"recipe {name!r} requires intel (the .43 LAN endpoint) but "
                "intel is disabled for this apply"
            )

        # 1. Ensure the run is booted on the recipe's deck + cache posture.
        restarted = host.ensure_deck(run_id, target.deck, link_caches=target.link_caches)

        client = host.product_client(run_id)
        home = host.run_home(run_id)
        evaluator = ProbeEvaluator(client, home=home, run_id=run_id)

        # The combined probe is the target's own probe (includes stage the world;
        # the target's probe is the authoritative claim). Included recipes still
        # contribute their seeds/actions below.
        probe_spec = target.probe

        # 2. Probe-first idempotency.
        pre = evaluator.evaluate(probe_spec)
        if pre.ok and probe_spec:
            return ApplyResult(
                recipe=name,
                deck=target.deck,
                already_satisfied=True,
                probe=pre.to_dict(),
                restarted=restarted,
            )

        # 3. Stage: seeds (deps first), then actions (deps first).
        seed_outcomes: list[dict] = []
        action_log: list[dict] = []
        for rn in order:
            r = self.registry.load(rn)
            for seed_name in r.seeds:
                manifest = self.seed_registry.load(seed_name)
                seed_outcomes.append(Seeder(client).apply(manifest).to_dict())
            for action in r.actions:
                action_log.append(self._run_action(action, run_id, host, client))

        # 4. Verify.
        post = evaluator.evaluate(probe_spec)
        result = ApplyResult(
            recipe=name,
            deck=target.deck,
            already_satisfied=False,
            probe=post.to_dict(),
            seeds=seed_outcomes,
            actions=action_log,
            restarted=restarted,
        )
        if probe_spec and not post.ok:
>           raise RecipeVerifyError(
                f"recipe {name!r} failed to verify: {post.summary()}", result
            )
E           uat.conductor.induction.recipes.RecipeVerifyError: recipe 'intel-endpoint-dead' failed to verify: runtime_endpoint_unreachable: runtime-test ok=False status='unavailable' in 0.0s: Backend 'openai_compatible' requires the 'openai' package. Install with: uv pip install holdspeak[dictation-openai]

uat/conductor/induction/recipes.py:240: RecipeVerifyError
______________ test_run_dispatched_onto_the_worker_returns_badged ______________

real_manager = <uat.conductor.runs.RunManager object at 0x10d460cd0>

    def test_run_dispatched_onto_the_worker_returns_badged(real_manager):
        run = _boot_or_skip(real_manager, "mesh-node")

>       result = real_manager.apply_recipe(run.id, "mesh-run-on-worker")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/uat/test_mesh_dispatch.py:55:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
uat/conductor/runs.py:387: in apply_recipe
    return self.recipes.apply(name, run_id, self, allow_intel=allow_intel)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <uat.conductor.induction.recipes.RecipeEngine object at 0x10d461310>
name = 'mesh-run-on-worker', run_id = 'run-20260727T061941-bee67c'
host = <uat.conductor.runs.RunManager object at 0x10d460cd0>

    def apply(
        self, name: str, run_id: str, host: "RecipeHost", *, allow_intel: bool = True
    ) -> ApplyResult:
        order = self.registry.resolve_order(name)
        target = self.registry.load(name)

        if target.requires_intel and not allow_intel:
            raise RecipeError(
                f"recipe {name!r} requires intel (the .43 LAN endpoint) but "
                "intel is disabled for this apply"
            )

        # 1. Ensure the run is booted on the recipe's deck + cache posture.
        restarted = host.ensure_deck(run_id, target.deck, link_caches=target.link_caches)

        client = host.product_client(run_id)
        home = host.run_home(run_id)
        evaluator = ProbeEvaluator(client, home=home, run_id=run_id)

        # The combined probe is the target's own probe (includes stage the world;
        # the target's probe is the authoritative claim). Included recipes still
        # contribute their seeds/actions below.
        probe_spec = target.probe

        # 2. Probe-first idempotency.
        pre = evaluator.evaluate(probe_spec)
        if pre.ok and probe_spec:
            return ApplyResult(
                recipe=name,
                deck=target.deck,
                already_satisfied=True,
                probe=pre.to_dict(),
                restarted=restarted,
            )

        # 3. Stage: seeds (deps first), then actions (deps first).
        seed_outcomes: list[dict] = []
        action_log: list[dict] = []
        for rn in order:
            r = self.registry.load(rn)
            for seed_name in r.seeds:
                manifest = self.seed_registry.load(seed_name)
                seed_outcomes.append(Seeder(client).apply(manifest).to_dict())
            for action in r.actions:
                action_log.append(self._run_action(action, run_id, host, client))

        # 4. Verify.
        post = evaluator.evaluate(probe_spec)
        result = ApplyResult(
            recipe=name,
            deck=target.deck,
            already_satisfied=False,
            probe=post.to_dict(),
            seeds=seed_outcomes,
            actions=action_log,
            restarted=restarted,
        )
        if probe_spec and not post.ok:
>           raise RecipeVerifyError(
                f"recipe {name!r} failed to verify: {post.summary()}", result
            )
E           uat.conductor.induction.recipes.RecipeVerifyError: recipe 'mesh-run-on-worker' failed to verify: run_returned_badged: dispatch failed HTTP 502: None; run_claimed_by_worker: worker claims 0→1 (moved=True); hub provider='' scope='' (no-local=False); run_output_contains: output MISSING 'PYLON-CANARY-7' (0 chars)

uat/conductor/induction/recipes.py:240: RecipeVerifyError
__________________________ test_pack_d_stages_locally __________________________

real_client = <starlette.testclient.TestClient object at 0x10d5f4980>

    def test_pack_d_stages_locally(real_client):
        """Pack D demos without the LAN: its bad-endpoint scenario stages + verifies."""
        created = real_client.post("/api/sittings", json={"pack": "pack-d-honest-failure"}).json()
        if created["run"] is None or created["run"]["status"] != "up":
            pytest.skip("product did not boot")
        sid = created["id"]
        # Stage the dead-endpoint scenario (fully local — port 9 refused).
        staged = real_client.post(f"/api/sittings/{sid}/stage", json={"scenario_id": "d-dead-endpoint-doctor"}).json()
>       assert staged["ok"], staged
E       AssertionError: {'ok': False, 'scenario_id': 'd-dead-endpoint-doctor', 'staging': [{'error': "recipe 'intel-endpoint-dead' failed to v...--no-open`): browser auto-open disabled.
E         Press Ctrl+C to stop.'}, 'ok': False, 'recipe': 'intel-endpoint-dead', ...}]}
E       assert False

tests/uat/test_packs.py:180: AssertionError
=========================== short test summary info ============================
FAILED tests/uat/test_induction_integration_43.py::test_meeting_recipe_yields_a_real_open_action
FAILED tests/uat/test_induction_integration_local.py::test_intel_endpoint_dead_degrades_honestly
FAILED tests/uat/test_mesh_dispatch.py::test_run_dispatched_onto_the_worker_returns_badged
FAILED tests/uat/test_packs.py::test_pack_d_stages_locally - AssertionError: ...
4 failed in 422.63s (0:07:02)
```

### Captured run — 2026-07-27T06:21:34Z

- **Command:** `uv run pytest -q tests/unit/test_backend_density_guard.py::test_phase79_package_modules_stay_single_concern tests/unit/test_web_routes_coders_steer.py tests/unit/test_delivery_terminal_routes.py tests/unit/test_process_input_kernel.py tests/integration/test_process_input_real_hub.py tests/unit/test_kernel_broker.py tests/unit/test_kernel_effect_fence.py tests/integration/test_delivery_campaign.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
........................................................................ [ 91%]
.......                                                                  [100%]
79 passed in 15.77s
```

### Captured run — 2026-07-27T06:22:00Z

- **Command:** `uv run python /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/755cdf1e-8c7b-4e33-923d-a46dc3bb7d49/scratchpad/live_process_input_gate.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
can't find session: hs10605_approve_22749
can't find session: hs10605_deny_22749
{"gated_approve": {"decision": "approved", "output": "stdout: `GATE_APPROVE_KERNEL_10605`\n", "proposal_id": "toolu_01SnYXZo41wh4vsXahDC7Hkj", "reason_verbatim": null}, "gated_deny": {"decision": "denied", "effect_absent": true, "output": "The command was denied. Denial reason, quoted verbatim:\n\n> denied from the desk: kernel desk says no files today\n", "proposal_id": "toolu_01U7NZ8mkVei3xSaVauGsDGe", "reason_verbatim": true}, "one_decision_each": {"toolu_01SnYXZo41wh4vsXahDC7Hkj": 1, "toolu_01U7NZ8mkVei3xSaVauGsDGe": 1}, "real_send": {"latency_ms": 84.76, "marker_seen": true, "operation_id": "op_df144c8f50044ff9aff5af7b5dcf909a", "receipt": "succeeded"}}
```

### Captured run — 2026-07-27T06:23:23Z

- **Command:** `bash -o pipefail -c uv run pytest -q --ignore=tests/e2e/test_metal.py 2>&1 | tee /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/755cdf1e-8c7b-4e33-923d-a46dc3bb7d49/scratchpad/full-suite-final-after-density.txt`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 263833daafbb51509c73958eceeed81628e5a056

```text
ssssssssssssssssssssssFFFssssssssss..................................... [  1%]
........................................................................ [  3%]
......s................................................................. [  5%]
.....................................................................ss. [  6%]
........................................................................ [  8%]
........................................................................ [ 10%]
........................................................................ [ 11%]
........................................................................ [ 13%]
........................................................................ [ 15%]
........................................................................ [ 16%]
........................................................................ [ 18%]
...............................................................F...F.... [ 20%]
...F...........F........................................................ [ 21%]
...................F.................................................... [ 23%]
........................................................................ [ 25%]
........................................................................ [ 26%]
........................................................................ [ 28%]
........................................................................ [ 30%]
........................................................................ [ 31%]
........................................................................ [ 33%]
........................................................................ [ 35%]
........................................................................ [ 36%]
........................................................................ [ 38%]
........................................................................ [ 40%]
........................................................................ [ 41%]
........................................................................ [ 43%]
........................................................................ [ 45%]
........................................................................ [ 46%]
........................................................................ [ 48%]
........................................................................ [ 50%]
........................................................................ [ 51%]
........................................................................ [ 53%]
........................................................................ [ 55%]
........................s............................................... [ 56%]
........................................................................ [ 58%]
........................................................................ [ 60%]
........................................................................ [ 62%]
........................................................................ [ 63%]
........................................................................ [ 65%]
........................................................................ [ 67%]
........................................................................ [ 68%]
........................................................................ [ 70%]
........................................................................ [ 72%]
........................................................................ [ 73%]
........................................................................ [ 75%]
........................................................................ [ 77%]
........................................................................ [ 78%]
........................................................................ [ 80%]
........................................................................ [ 82%]
........................................................................ [ 83%]
........................................................................ [ 85%]
........................................................................ [ 87%]
........................................................................ [ 88%]
........................................................................ [ 90%]
........................................................................ [ 92%]
........................................................................ [ 93%]
........................................................................ [ 95%]
........................................................................ [ 97%]
........................................................................ [ 98%]
................................................                         [100%]
=================================== FAILURES ===================================
____________ test_every_live_page_opens_exactly_one_runtime_socket _____________

browser = <Browser type=<BrowserType name=chromium executable_path=/Users/karol/Library/Caches/ms-playwright/chromium-1200/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing> version=143.0.7499.4>

    def test_every_live_page_opens_exactly_one_runtime_socket(browser):
        server = _make_server()
        uv = _Uvicorn(server.app)
        uv.start()
        try:
            for route in ("/live", "/dictation", "/presence", "/setup"):
                page = browser.new_page()
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                n = _count_runtime_sockets(page, f"http://127.0.0.1:{PORT}{route}")
                page.close()
>               assert n == 1, f"{route} opened {n} runtime sockets (want exactly 1)"
E               AssertionError: /live opened 3 runtime sockets (want exactly 1)
E               assert 3 == 1

tests/e2e/test_live_bus.py:96: AssertionError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
_________ test_a_real_broadcast_reaches_the_presence_card_via_the_bus __________

browser = <Browser type=<BrowserType name=chromium executable_path=/Users/karol/Library/Caches/ms-playwright/chromium-1200/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing> version=143.0.7499.4>

    def test_a_real_broadcast_reaches_the_presence_card_via_the_bus(browser):
        server = _make_server()
        uv = _Uvicorn(server.app)
        uv.start()
        try:
            page = browser.new_page()
            page.goto(f"http://127.0.0.1:{PORT}/presence", wait_until="networkidle")
            page.wait_for_timeout(800)
            server.broadcast(
                "runtime_activity",
                {
                    "state": "transcribing",
                    "label": "Transcribing",
                    "source": "dictation",
                    "window": {"visible": True},
                },
            )
>           page.wait_for_function(
                "() => document.querySelector('.presence-card strong')"
                " && document.querySelector('.presence-card strong').textContent.includes('Transcribing')",
                timeout=8000,
            )

tests/e2e/test_live_bus.py:119:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:11595: in wait_for_function
    self._sync(
.venv/lib/python3.13/site-packages/playwright/_impl/_page.py:1110: in wait_for_function
    return await self._main_frame.wait_for_function(**locals_to_params(locals()))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:878: in wait_for_function
    await self._channel.send("waitForFunction", self._timeout, params)
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <playwright._impl._connection.Connection object at 0x10f21aba0>
cb = <function Channel.send.<locals>.<lambda> at 0x1102d6fc0>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)

        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 8000ms exceeded.

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
________________ test_the_bus_reconnects_after_a_server_restart ________________

browser = <Browser type=<BrowserType name=chromium executable_path=/Users/karol/Library/Caches/ms-playwright/chromium-1200/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing> version=143.0.7499.4>

    def test_the_bus_reconnects_after_a_server_restart(browser):
        server = _make_server()
        uv = _Uvicorn(server.app)
        uv.start()
        page = browser.new_page()
        sockets: list[str] = []
        page.on("websocket", lambda ws: sockets.append(ws.url))
        try:
            page.goto(f"http://127.0.0.1:{PORT}/presence", wait_until="networkidle")
            page.wait_for_timeout(1000)
            first = sum(1 for u in sockets if u.rstrip("/").endswith("/ws"))
>           assert first == 1
E           assert 3 == 1

tests/e2e/test_live_bus.py:140: AssertionError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
WARNING  holdspeak.web.routes.system:ws.py:54 Rejected WebSocket: principal=none missing_right=owner
________________ test_meeting_recipe_yields_a_real_open_action _________________

real_manager = <uat.conductor.runs.RunManager object at 0x134dd7570>

    def test_meeting_recipe_yields_a_real_open_action(real_manager):
        run = _boot_or_skip(real_manager, "golden-43")
>       result = real_manager.apply_recipe(run.id, "meeting-just-ended-open-actions")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/uat/test_induction_integration_43.py:52:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
uat/conductor/runs.py:387: in apply_recipe
    return self.recipes.apply(name, run_id, self, allow_intel=allow_intel)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <uat.conductor.induction.recipes.RecipeEngine object at 0x133bab5f0>
name = 'meeting-just-ended-open-actions', run_id = 'run-20260727T062825-bcd502'
host = <uat.conductor.runs.RunManager object at 0x134dd7570>

    def apply(
        self, name: str, run_id: str, host: "RecipeHost", *, allow_intel: bool = True
    ) -> ApplyResult:
        order = self.registry.resolve_order(name)
        target = self.registry.load(name)

        if target.requires_intel and not allow_intel:
            raise RecipeError(
                f"recipe {name!r} requires intel (the .43 LAN endpoint) but "
                "intel is disabled for this apply"
            )

        # 1. Ensure the run is booted on the recipe's deck + cache posture.
        restarted = host.ensure_deck(run_id, target.deck, link_caches=target.link_caches)

        client = host.product_client(run_id)
        home = host.run_home(run_id)
        evaluator = ProbeEvaluator(client, home=home, run_id=run_id)

        # The combined probe is the target's own probe (includes stage the world;
        # the target's probe is the authoritative claim). Included recipes still
        # contribute their seeds/actions below.
        probe_spec = target.probe

        # 2. Probe-first idempotency.
        pre = evaluator.evaluate(probe_spec)
        if pre.ok and probe_spec:
            return ApplyResult(
                recipe=name,
                deck=target.deck,
                already_satisfied=True,
                probe=pre.to_dict(),
                restarted=restarted,
            )

        # 3. Stage: seeds (deps first), then actions (deps first).
        seed_outcomes: list[dict] = []
        action_log: list[dict] = []
        for rn in order:
            r = self.registry.load(rn)
            for seed_name in r.seeds:
                manifest = self.seed_registry.load(seed_name)
                seed_outcomes.append(Seeder(client).apply(manifest).to_dict())
            for action in r.actions:
                action_log.append(self._run_action(action, run_id, host, client))

        # 4. Verify.
        post = evaluator.evaluate(probe_spec)
        result = ApplyResult(
            recipe=name,
            deck=target.deck,
            already_satisfied=False,
            probe=post.to_dict(),
            seeds=seed_outcomes,
            actions=action_log,
            restarted=restarted,
        )
        if probe_spec and not post.ok:
>           raise RecipeVerifyError(
                f"recipe {name!r} failed to verify: {post.summary()}", result
            )
E           uat.conductor.induction.recipes.RecipeVerifyError: recipe 'meeting-just-ended-open-actions' failed to verify: meeting_with_open_actions: timed out after 180s: meetings present but none with ≥1 open actions: Pylon incident war room (UAT seed)(0,queued)

uat/conductor/induction/recipes.py:240: RecipeVerifyError
__________________ test_intel_endpoint_dead_degrades_honestly __________________

real_manager = <uat.conductor.runs.RunManager object at 0x13534f1b0>

    def test_intel_endpoint_dead_degrades_honestly(real_manager):
        run = _boot_or_skip(real_manager)
>       result = real_manager.apply_recipe(run.id, "intel-endpoint-dead")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/uat/test_induction_integration_local.py:73:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
uat/conductor/runs.py:387: in apply_recipe
    return self.recipes.apply(name, run_id, self, allow_intel=allow_intel)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <uat.conductor.induction.recipes.RecipeEngine object at 0x134b6f770>
name = 'intel-endpoint-dead', run_id = 'run-20260727T063641-46a06e'
host = <uat.conductor.runs.RunManager object at 0x13534f1b0>

    def apply(
        self, name: str, run_id: str, host: "RecipeHost", *, allow_intel: bool = True
    ) -> ApplyResult:
        order = self.registry.resolve_order(name)
        target = self.registry.load(name)

        if target.requires_intel and not allow_intel:
            raise RecipeError(
                f"recipe {name!r} requires intel (the .43 LAN endpoint) but "
                "intel is disabled for this apply"
            )

        # 1. Ensure the run is booted on the recipe's deck + cache posture.
        restarted = host.ensure_deck(run_id, target.deck, link_caches=target.link_caches)

        client = host.product_client(run_id)
        home = host.run_home(run_id)
        evaluator = ProbeEvaluator(client, home=home, run_id=run_id)

        # The combined probe is the target's own probe (includes stage the world;
        # the target's probe is the authoritative claim). Included recipes still
        # contribute their seeds/actions below.
        probe_spec = target.probe

        # 2. Probe-first idempotency.
        pre = evaluator.evaluate(probe_spec)
        if pre.ok and probe_spec:
            return ApplyResult(
                recipe=name,
                deck=target.deck,
                already_satisfied=True,
                probe=pre.to_dict(),
                restarted=restarted,
            )

        # 3. Stage: seeds (deps first), then actions (deps first).
        seed_outcomes: list[dict] = []
        action_log: list[dict] = []
        for rn in order:
            r = self.registry.load(rn)
            for seed_name in r.seeds:
                manifest = self.seed_registry.load(seed_name)
                seed_outcomes.append(Seeder(client).apply(manifest).to_dict())
            for action in r.actions:
                action_log.append(self._run_action(action, run_id, host, client))

        # 4. Verify.
        post = evaluator.evaluate(probe_spec)
        result = ApplyResult(
            recipe=name,
            deck=target.deck,
            already_satisfied=False,
            probe=post.to_dict(),
            seeds=seed_outcomes,
            actions=action_log,
            restarted=restarted,
        )
        if probe_spec and not post.ok:
>           raise RecipeVerifyError(
                f"recipe {name!r} failed to verify: {post.summary()}", result
            )
E           uat.conductor.induction.recipes.RecipeVerifyError: recipe 'intel-endpoint-dead' failed to verify: runtime_endpoint_unreachable: runtime-test ok=False status='unavailable' in 0.0s: Backend 'openai_compatible' requires the 'openai' package. Install with: uv pip install holdspeak[dictation-openai]

uat/conductor/induction/recipes.py:240: RecipeVerifyError
______________ test_run_dispatched_onto_the_worker_returns_badged ______________

real_manager = <uat.conductor.runs.RunManager object at 0x13534cc30>

    def test_run_dispatched_onto_the_worker_returns_badged(real_manager):
        run = _boot_or_skip(real_manager, "mesh-node")

>       result = real_manager.apply_recipe(run.id, "mesh-run-on-worker")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/uat/test_mesh_dispatch.py:55:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
uat/conductor/runs.py:387: in apply_recipe
    return self.recipes.apply(name, run_id, self, allow_intel=allow_intel)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <uat.conductor.induction.recipes.RecipeEngine object at 0x1342f7fb0>
name = 'mesh-run-on-worker', run_id = 'run-20260727T063645-b734cf'
host = <uat.conductor.runs.RunManager object at 0x13534cc30>

    def apply(
        self, name: str, run_id: str, host: "RecipeHost", *, allow_intel: bool = True
    ) -> ApplyResult:
        order = self.regi
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```
