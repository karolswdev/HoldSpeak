# Firefox companion extension

The extension sends the URL and title of your active Firefox tab to your local HoldSpeak runtime. Activity pre-briefing uses this data to see your browsing as it happens.

The extension is not on addons.mozilla.org. It lives in this repository. You load it as a temporary add-on.

## Install

1. Start HoldSpeak with `holdspeak web`. Note the `http://127.0.0.1:<port>` address in the output.
2. In Firefox, open `about:debugging#/runtime/this-firefox`.
3. Click **Load Temporary Add-on…**. Select `extensions/firefox/manifest.json`.
4. Open `about:addons`. Open the options of **HoldSpeak Companion (local)**.
5. Set the runtime URL to the address from step 1.
6. Browse as usual.

Firefox removes a temporary add-on when it restarts. Load it again each session.

## Check that it works

Open the Activity page of HoldSpeak. A row with the source `firefox_ext` appears after your next tab change.

If no row appears:

- Open the browser console (`Ctrl+Shift+J`) and enable the Debug level. The message `[holdspeak-companion] runtime not reachable` means the runtime URL is wrong.
- Check that HoldSpeak runs on the port in the options.
- Use a normal window. The extension ignores private windows.

## What the extension sends

The extension listens for tab activation and for a finished page load. For each event it posts to `/api/activity/extension/events`:

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

- The runtime binds to `127.0.0.1` by default. If you bind it to another address, you own that risk.
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
