"""Companion-extension event ingestion.

HS-9-03. A locally installed Firefox WebExtension can post visible,
opt-in active-tab events to the local HoldSpeak runtime over the
loopback API. This module is the contract between that extension
and `activity_records`.

What this module *will not* accept, regardless of payload:

  - Any field whose name implies sensitive content (cookies, body,
    headers, page bodies, form data, credentials, screenshots).
  - URLs with a scheme other than `http` / `https`.
  - Events flagged `private` or `incognito`.
  - Events whose `visited_at` cannot be parsed as ISO-8601.

Every rejection is reported with a stable `reason` string so the
extension can present it to the user; the parser does not raise on
bad events. The runtime ingests the accepted events as
`activity_records` rows with `source_browser="firefox_ext"` and
re-uses `extract_activity_entity` + project mapping.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable, Optional
from urllib.parse import urlsplit

from .activity_entities import extract_activity_entity
from .db import ActivityRecord, MeetingDatabase

EXTENSION_SOURCE_BROWSER = "firefox_ext"
ALLOWED_SCHEMES = frozenset({"http", "https"})

# Field names that imply sensitive content. Any incoming event
# carrying one of these — even if empty — is rejected.
FORBIDDEN_FIELDS = frozenset(
    {
        "body",
        "page_body",
        "html",
        "page_html",
        "content",
        "page_content",
        "form",
        "form_data",
        "form_values",
        "fields",
        "input",
        "inputs",
        "password",
        "credentials",
        "credential",
        "cookies",
        "cookie",
        "headers",
        "header",
        "screenshot",
        "screenshot_data",
        "image",
        "images",
        "selection",
        "selected_text",
        "clipboard",
    }
)

# Fields the parser knows how to use. Anything outside this set is
# ignored at parse time; anything inside FORBIDDEN_FIELDS is a hard
# reject. This keeps the contract narrow and explicit.
ALLOWED_FIELDS = frozenset(
    {
        "url",
        "title",
        "visited_at",
        "tab_id",
        "tab_index",
        "window_id",
        "private",
        "incognito",
        "entity_type",
        "entity_id",
        "source_profile",
    }
)


@dataclass(frozen=True)
class ParsedExtensionEvent:
    """An event that passed validation and is safe to ingest."""

    url: str
    title: str
    visited_at: datetime
    source_profile: str = ""
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None


@dataclass(frozen=True)
class IngestResult:
    """Outcome of a single ingestion batch."""

    accepted: tuple[int, ...]  # ids of upserted activity_records rows
    rejected: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    project_rule_updates: int = 0

    def to_payload(self) -> dict[str, Any]:
        return {
            "accepted": list(self.accepted),
            "rejected": list(self.rejected),
            "project_rule_updates": self.project_rule_updates,
        }


def parse_extension_event(raw: Any) -> tuple[Optional[ParsedExtensionEvent], Optional[str]]:
    """Validate one raw event from the extension.

    Returns `(event, None)` on success or `(None, reason)` on
    rejection. `reason` is a short stable string the extension can
    log or display to the user.
    """
    if not isinstance(raw, dict):
        return None, "event_must_be_object"

    # Hard-reject any field whose name implies sensitive content,
    # even if the value is empty / falsy. The intent is the
    # important signal — an extension that ships a `cookies` field
    # at all is misconfigured.
    sensitive_keys = [
        key for key in raw.keys() if str(key).lower() in FORBIDDEN_FIELDS
    ]
    if sensitive_keys:
        return None, f"forbidden_field:{sorted(sensitive_keys)[0]}"

    if raw.get("private") is True or raw.get("incognito") is True:
        return None, "private_browsing_blocked"

    url_value = raw.get("url")
    if not isinstance(url_value, str) or not url_value.strip():
        return None, "url_required"
    parsed = urlsplit(url_value.strip())
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        return None, f"scheme_not_allowed:{parsed.scheme.lower() or 'empty'}"
    if not parsed.netloc:
        return None, "url_missing_host"

    visited_raw = raw.get("visited_at")
    if not isinstance(visited_raw, str) or not visited_raw.strip():
        return None, "visited_at_required"
    try:
        # `fromisoformat` is strict enough to reject "now" / "today".
        # The extension is expected to send UTC ISO-8601.
        visited_at = datetime.fromisoformat(visited_raw.replace("Z", "+00:00"))
    except ValueError:
        return None, "visited_at_not_iso"

    title = raw.get("title", "") or ""
    if not isinstance(title, str):
        return None, "title_must_be_string"

    source_profile = raw.get("source_profile", "") or ""
    if not isinstance(source_profile, str):
        return None, "source_profile_must_be_string"

    entity_type = raw.get("entity_type")
    if entity_type is not None and not isinstance(entity_type, str):
        return None, "entity_type_must_be_string"

    entity_id = raw.get("entity_id")
    if entity_id is not None and not isinstance(entity_id, str):
        return None, "entity_id_must_be_string"

    return (
        ParsedExtensionEvent(
            url=url_value.strip(),
            title=title.strip(),
            visited_at=visited_at,
            source_profile=source_profile.strip(),
            entity_type=entity_type.strip().lower() if entity_type else None,
            entity_id=entity_id.strip() if entity_id else None,
        ),
        None,
    )


def ingest_extension_events(
    db: MeetingDatabase,
    raw_events: Iterable[Any],
) -> IngestResult:
    """Validate, normalize, and upsert a batch of extension events."""
    accepted: list[int] = []
    rejected: list[dict[str, Any]] = []

    for index, raw in enumerate(raw_events):
        event, reason = parse_extension_event(raw)
        if event is None:
            rejected.append({"index": index, "reason": reason})
            continue

        entity_type = event.entity_type
        entity_id = event.entity_id
        if not entity_type or not entity_id:
            entity = extract_activity_entity(event.url, title=event.title)
            entity_type = entity_type or entity.entity_type
            entity_id = entity_id or entity.entity_id

        record: ActivityRecord = db.upsert_activity_record(
            source_browser=EXTENSION_SOURCE_BROWSER,
            source_profile=event.source_profile,
            url=event.url,
            title=event.title or None,
            last_seen_at=event.visited_at,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        accepted.append(record.id)

    project_rule_updates = 0
    if accepted:
        project_rule_updates = db.apply_activity_project_rules()

    return IngestResult(
        accepted=tuple(accepted),
        rejected=tuple(rejected),
        project_rule_updates=int(project_rule_updates),
    )
