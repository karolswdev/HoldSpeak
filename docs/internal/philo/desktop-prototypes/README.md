# Thin-host research prototypes

Status: **research only**, macOS ARM64, source snapshot `675401a…`.
These are separate minimal Electron and Tauri hosts for the **same existing
production Web bundle**. They do not add a desktop application to HoldSpeak's
shipping packages. No domain store, HTTP client or UI kit is duplicated.

## Observed result

- Electron 41.10.7 loaded the production bundle and displayed the expected
  `Artifacts: No runtime in host rendering probe` error at 1440 and 393 CSS
  widths. The renderer had no Node `process` or `require` global. Its exposed
  host object contains only kind and disabled capability flags.
- Tauri 2.11.6 built with clone-local Rust 1.98.1. Its hidden WKWebView logged
  page load start and finish for the same server. It registered no Rust native
  commands and no capabilities. This is load-event evidence, not visual parity.
- Both used temporary HOME/profile directories. The server returns 503 for API
  and WebSocket requests. It starts no HoldSpeak runtime or database.

[Environment and bundle hash](results/environment.json),
[Electron probe](results/electron-probe.json), and
[Tauri load log](results/tauri-probe.log) preserve the observations.
[Wide](results/electron-1440.png) and [compact](results/electron-393.png)
Electron captures show the error surface, **not** a populated Desk or a design
mockup. Native scaling can make PNG pixels larger than CSS viewport dimensions.

The recorded Electron duration includes an explicit 2.5-second settle wait.
It is not a startup benchmark. These results do not justify choosing a host.
The [ADR](../adr/desktop-host.md) keeps the decision open pending populated
journeys, rendering comparisons, permissions, packaging and resource measures.

## Reproduce

Build the current web bundle with the repository's normal web build. From the
repository root, serve it with:

```sh
python docs/internal/philo/desktop-prototypes/serve.py
```

The server binds only `127.0.0.1:18789`. Then, in a separate terminal:

```sh
npm ci --prefix docs/internal/philo/desktop-prototypes/electron
PHILO_PROBE_OUT="$(mktemp -d)" HOME="$(mktemp -d)" \
  docs/internal/philo/desktop-prototypes/electron/node_modules/.bin/electron \
  docs/internal/philo/desktop-prototypes/electron
```

With Rust and platform prerequisites installed:

```sh
cargo build --locked --manifest-path docs/internal/philo/desktop-prototypes/tauri/Cargo.toml
PHILO_PROBE_OUT="$(mktemp -d)" HOME="$(mktemp -d)" \
  docs/internal/philo/desktop-prototypes/tauri/target/debug/holdspeak-philo-tauri-probe
```

A custom `CARGO_TARGET_DIR` changes the executable path. The recorded run used
clone-local Cargo/Rustup caches and target output under `.tmp/philo`. No shell
profile or system toolchain was changed. Stop the static server when finished.

## Boundaries and next experiments

Electron denies permission requests, popup creation and navigation/requests
outside the fixed loopback origin. Its sandbox and context isolation are on.
Tauri restricts top-level navigation to that origin and grants no native
commands. This does not certify every platform WebView network or permission
behavior. Neither exposes arbitrary shell, file or process methods.

The next prototype must use a disposable fixture hub, still with no owner data,
then verify the same representative journeys and native denial cases in both
hosts. Keep signing, update, tray, global shortcut and file-dialog experiments
separate from the production UI. See the bounded interface and measurement
protocol in the ADR before adding any native authority.
