"""Firefox companion connector pack.

HS-11-03. Wraps the phase-9 `activity_extension` ingester as a
phase-11 connector pack with manifest metadata, declared
captured fields, and a privacy-boundary contract.

The actual ingestion logic lives in `holdspeak/activity_extension.py`
(HS-9-03). This pack adds the manifest layer + makes the
captured-fields contract explicit.

Privacy contract (also enforced at parse time by
`activity_extension.FORBIDDEN_FIELDS`):

  - The extension only sends URL + title + visited_at + tab/window
    identifiers.
  - It does NOT send page bodies, cookies, headers, form data,
    credentials, screenshots, selection text, or any field whose
    name implies sensitive content.
  - Private / incognito events are rejected at the parser.
  - Only http(s) URLs are accepted.
"""

from __future__ import annotations

from ..activity_extension import (
    ALLOWED_FIELDS,
    EXTENSION_SOURCE_BROWSER,
    FORBIDDEN_FIELDS,
)
from ..connector_sdk import ConnectorManifest, validate_manifest

# The fields the extension is *allowed* to send. Mirrors
# `activity_extension.ALLOWED_FIELDS` but exposed here so the
# pack manifest can declare the captured-fields surface
# explicitly. Anything outside this set is silently ignored
# at parse time; anything in `FORBIDDEN_FIELDS` is hard-rejected.
CAPTURED_FIELDS: frozenset[str] = ALLOWED_FIELDS

# Re-exported for the pack's privacy story.
REJECTED_FIELDS: frozenset[str] = FORBIDDEN_FIELDS

MANIFEST: ConnectorManifest = validate_manifest(
    {
        "id": EXTENSION_SOURCE_BROWSER,
        "label": "Firefox companion",
        "version": "0.1.0",
        "kind": "extension_events",
        "capabilities": ["records"],
        "description": (
            "Loopback POSTs from a locally installed Firefox "
            "WebExtension. URL + title + visited_at + tab/window "
            "ids only — no page bodies, no cookies, no form data, "
            "no private-browsing events."
        ),
        "requires_cli": None,
        "requires_network": True,
        "permissions": ["loopback:http", "write:activity_records"],
        "source_boundary": (
            "Loopback POSTs from a local Firefox WebExtension. "
            "The extension is loaded as a temporary add-on and "
            "removed on browser restart — no extension-store "
            "distribution path."
        ),
        "dry_run": True,
    }
)
