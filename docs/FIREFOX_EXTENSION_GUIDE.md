# Firefox companion extension — local install guide

> HS-9-03. The extension is **not distributed via addons.mozilla.org**;
> it lives in this repo and is loaded as a temporary add-on for
> personal local use only.

## What it does

The companion extension posts active-tab URL + title to the running
local HoldSpeak runtime so the activity ledger reflects browsing in
near-real-time, instead of waiting for Firefox's history database to
flush.

## What it intentionally does NOT do

- Read page body / DOM / form fields / selected text.
- Read or send cookies, headers, credentials.
- Send anything from private-browsing windows.
- Send anything for non-`http(s)` URLs.
- Talk to anything other than the local loopback runtime.

The receiving parser
(`holdspeak/activity_extension.py:FORBIDDEN_FIELDS`) hard-rejects
events that ship any of those fields, even if empty. This is
defense-in-depth — the extension itself never builds those fields.

## Local install (Firefox)

1. Start the HoldSpeak runtime: `holdspeak web` (note the
   `http://127.0.0.1:<port>` line in stdout — the port is randomly
   assigned per launch).
2. In Firefox, open `about:debugging#/runtime/this-firefox`.
3. Click **Load Temporary Add-on…** and select
   `extensions/firefox/manifest.json` from this repo.
4. Open the extension's options page (`about:addons` →
   "HoldSpeak Companion" → Options) and set the runtime URL to
   match the port from step 1.
5. Browse normally. Tab activations and load completions show up
   in `/activity` under `source_browser=firefox_ext`.

The temporary add-on is removed on Firefox restart — re-load it via
step 3 each session. This is intentional: the extension is for
personal local use and is not packaged for distribution.

## Verifying it works

After loading the extension, open `/activity` in your browser. The
"Recent activity" panel should refresh on the next tab change with
a `firefox_ext` row. If it doesn't:

- Check Firefox's browser console (`Ctrl+Shift+J`) for
  `[holdspeak-companion] runtime not reachable` — the runtime URL
  in options likely doesn't match the runtime port.
- Confirm the runtime is actually running on the configured port.
- Confirm your browsing is in a regular (non-private) window.

## Threat model

- **Trust boundary**: The extension is part of the local toolchain.
  A malicious extension on the same machine could already read the
  active tab via `tabs` permission directly — this extension
  doesn't widen that surface.
- **Network**: The extension only talks to the loopback URL the
  user configured. The runtime binds to `127.0.0.1` by default; if
  the user changes that to `0.0.0.0` they own the consequences.
- **Persistence**: The extension stores only the runtime URL in
  `browser.storage.local`. No event content is buffered or replayed.

## Source layout

```
extensions/firefox/
├── manifest.json    # WebExtension manifest (manifest_version: 2)
├── background.js    # Tab activation / load listener + POST
├── options.html     # Runtime URL setting
└── options.js       # Persists runtime URL via browser.storage
```
