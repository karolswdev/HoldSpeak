# Firefox companion extension

The repository contains a temporary Firefox companion. It builds a small active-tab event (URL, title, time, and tab/window identifiers) and posts it to the configured HoldSpeak runtime. When ingestion is admitted, Activity pre-briefing uses the accepted records to see your browsing as it happens.

The extension is not on addons.mozilla.org. It lives in this repository. You load it as a temporary add-on.

## Install

1. Start HoldSpeak with `holdspeak web`. Note the `http://127.0.0.1:<port>` address in the output.
2. In Firefox, open `about:debugging#/runtime/this-firefox`.
3. Click **Load Temporary Add-on…**. Select `extensions/firefox/manifest.json`.
4. Open `about:addons`. Open the options of **HoldSpeak Companion (local)**.
5. Set the runtime URL to the address from step 1.
6. Browse as usual.

Firefox removes a temporary add-on when it restarts. Load it again each session.

The current add-on sends no `Authorization` or `X-HoldSpeak-Token` header. The web edge normally requires the runtime credential for `/api` routes, so source inspection does not establish a working authenticated extension path in this checkout. The sections below describe the payload and privacy contract.
Successful ingestion requires working authentication and an accepted runtime response.

## Check that it works

The add-on attempts a POST after the next tab change. If the request is admitted, the Activity page shows a row with source `firefox_ext`.

If no row appears:

- Open the browser console (`Ctrl+Shift+J`) and enable the Debug level. The message `[holdspeak-companion] runtime not reachable` means the configured URL could not be reached. `runtime rejected batch` includes the HTTP status; check the runtime credential and route admission before changing the browser setup.
- Check that HoldSpeak runs on the port in the options.
- Use a normal window. The extension ignores private windows.

## What the extension sends

The extension listens for tab activation and for a finished page load. For each event it posts this body to `/api/activity/extension/events`:

```json
{"events": [{"url": "https://example.com", "title": "Example", "visited_at": "2026-10-29T12:00:00Z", "tab_id": 1, "window_id": 1}]}
```

The event fields are:

- `url`
- `title`
- `visited_at`
- `tab_id`
- `window_id`

## What the extension never does

- It does not read page text, forms, or selected text.
- It does not read or send cookies, headers, or credentials.
- It does not send events from private windows.
- It does not send URLs that are not `http` or `https`.
- It does not contact any host except the runtime URL you set.

The runtime enforces this also. The parser in `holdspeak/activity_extension.py` rejects any event that has a field in `FORBIDDEN_FIELDS`, even when the field is empty.

## Trust and storage

- The runtime binds to `127.0.0.1` by default. The options page accepts another runtime URL.
The add-on does not add remote API authentication, so that field does not establish supported remote access.
- The extension stores only the runtime URL, in `browser.storage.local`. It does not buffer or replay events.
- The extension uses the `tabs`, `activeTab`, and `storage` permissions.

## Source

```
extensions/firefox/
├── manifest.json    # WebExtension manifest (version 2)
├── background.js    # Tab listeners and the POST
├── options.html     # Runtime URL setting
└── options.js       # Saves the URL to browser.storage.local
```

## See also

- [Activity pre-briefing](ACTIVITY_PREBRIEFING.md)
- [Connector Development](CONNECTOR_DEVELOPMENT.md): the connector contract this extension follows.
- [Security & Privacy](SECURITY.md)
