# HS-14-03 evidence — PSK auth + handshake protocol

## What shipped

- `holdspeak/config.py` — added `DeviceConfig` (single field
  `psk: str = ""`) and wired it into `Config` as
  `Config.device`. Round-trips through `Config.load()` /
  `Config.save()`. The empty-default lets existing installs
  upgrade without an immediate config-file rewrite — a PSK is
  only generated when something actually asks for one.

- `holdspeak/device_audio.py` — handshake protocol additions:
  - Constants: `DEVICE_HANDSHAKE_VERSION = 1`,
    `WS_CLOSE_INVALID_HANDSHAKE = 4001`,
    `WS_CLOSE_PSK_MISMATCH = 4003`,
    `WS_CLOSE_DUPLICATE_LABEL = 4009`.
  - `DeviceHandshake` (Pydantic v2 BaseModel,
    `model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)`):
    fields are `type: Literal["hello"]`, `device_id: str`,
    `label: str`, `psk: str`, `version: int`. A field
    validator on `device_id`/`label`/`psk` rejects empty
    (post-strip) strings.
  - `parse_handshake(payload: Any) -> DeviceHandshake` —
    rejects non-dict payloads and wraps Pydantic
    `ValidationError` in `InvalidHandshakeError`.
  - `verify_psk(provided, expected) -> bool` — short-circuits
    to `False` on either side empty so a freshly-installed
    instance with no PSK on disk cannot be authenticated by
    sending an empty string. Otherwise uses
    `hmac.compare_digest` on the UTF-8-encoded bytes.
  - Typed exceptions: `HandshakeError` (base),
    `InvalidHandshakeError` (`code = 4001`),
    `PskMismatchError` (`code = 4003`). HS-14-04 reads
    `exc.code` rather than re-deriving the close-code policy.
    `DuplicateLabelError` (already in the registry) maps to
    `WS_CLOSE_DUPLICATE_LABEL` at the route call site.
  - PSK lifecycle: `generate_device_psk()` returns
    `secrets.token_urlsafe(24)` (~32 chars; well above the
    ≥24-char floor in the spec). `ensure_device_psk(config)`
    is a no-op when a PSK is already set, otherwise generates
    + saves. `rotate_device_psk(config)` always regenerates +
    saves. Both accept an explicit `save_path` for tests.

- `holdspeak/commands/device.py` — new `run_device_psk_command`
  runner. `show` ensures + prints; `rotate` regenerates +
  prints + logs `device_psk_rotated`. Unknown action → exit
  code 2 with usage string on stderr.

- `holdspeak/main.py` — argparse `device-psk` subcommand with
  nested `show` / `rotate` actions; dispatch
  `args.command == "device-psk"` to `run_device_psk_command`.

## Out (per story scope)

- WebSocket route + lifecycle — HS-14-04.
- Per-device PSKs / federation — phase 15+.
- TLS / WSS termination — phase 15 (cross-network).

## Test runs

`uv run --extra test pytest tests/unit/test_device_handshake.py`

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/karol/dev/HoldSpeak
configfile: pyproject.toml
plugins: timeout-2.4.0, cov-7.0.0, anyio-4.12.1, asyncio-1.3.0, mock-3.15.1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 25 items

tests/unit/test_device_handshake.py .........................            [100%]

============================== 25 passed in 0.34s ==============================
```

`tests/unit/test_device_handshake.py` ships 25 cases (story
required ≥4) across five concerns: handshake schema (valid,
missing-field, extra-field, wrong-type-literal, empty-string,
whitespace-only, non-dict, JSON round-trip), PSK compare
(match, mismatch, empty-provided, empty-expected, both-empty,
length-mismatch-no-raise), close-code constants (distinct
4xxx range, error-class carries code), PSK lifecycle (generate
returns ≥24 url-safe chars, generate is random, ensure
generates+persists, ensure no-ops on preset PSK, rotate
replaces+persists, Config.load/save round-trips device.psk),
and the CLI runner (show prints existing PSK, rotate replaces
and prints, unknown action exits 2 with usage on stderr).

Regression sweep on audio + controller + web_runtime + config:

`uv run --extra test pytest -q tests/unit/test_device_handshake.py
tests/unit/test_device_registry.py
tests/unit/test_remote_audio_recorder.py
tests/unit/test_audio_source_contract.py
tests/unit/test_audio_resample.py
tests/unit/test_audio_devices_pulse.py
tests/unit/test_controller.py
tests/unit/test_web_runtime.py
tests/unit/test_config.py`

```
........................................................................ [ 44%]
........................................................................ [ 88%]
..................                                                       [100%]
162 passed in 0.70s
```

CLI smoke test in an isolated `HOME`:

```
$ HOME=/tmp/holdspeak-cli-smoke uv run python -m holdspeak.main device-psk show
d2LaFC0ZzKm_CRsAp9NAssom5jEELww4

$ HOME=/tmp/holdspeak-cli-smoke uv run python -m holdspeak.main device-psk rotate
Rf9-_HCE-Btjrepgrqe2sOzks3uA0oyW
```

Both runs wrote/updated the PSK in
`$HOME/.config/holdspeak/config.json` as expected.

## Notes

- **Why a top-level `device` section vs a flat `device_psk` field.**
  HS-14-04 will add WebSocket-related runtime knobs (queue size,
  auth-failure log policy, etc.); a section makes those grow
  cleanly.
- **Why `verify_psk` short-circuits on empty inputs.** Before
  generating a PSK on first run, `config.device.psk` is the
  empty string. Reaching `hmac.compare_digest("", "")` returns
  `True` — a footgun if the route ever forgot to call
  `ensure_device_psk` first. Refusing empty inputs makes the
  auth-empty case fail loud.
- **Why exception classes carry the close code.** HS-14-04
  needs to map handshake failures onto `await ws.close(code=...)`
  without re-deriving which exception means which code. Putting
  `code` on the exception class lets the route do
  `await ws.close(code=exc.code)` and stay terse.
