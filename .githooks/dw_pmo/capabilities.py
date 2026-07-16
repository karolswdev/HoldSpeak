"""The counterpart capabilities declaration (HS-94-01).

``dw capabilities --json`` is how a consumer decides compatibility
BEFORE reading a source: the schema versions this CLI serves, the
status vocabulary its write verbs accept, the mutation verbs
themselves, and the resolved roadmap root. Consumers take their
status/verb vocabulary FROM this document instead of hard-coding a
second list (PLATFORM-CONTRACT §5.1). Pure read — building the
document touches nothing.
"""

from __future__ import annotations

from pathlib import Path

from .model import DONE_STATUSES, STORY_STATUSES, DwError
from .paths import rel, roadmap_dir

CAPABILITIES_SCHEMA = 1

# The mutation vocabulary the CLI accepts, `<noun>.<verb>` form —
# one list, declared here, matching the subcommands the gate admits.
MUTATION_VERBS = (
    "story.create",
    "story.status",
    "story.evidence",
    "phase.create",
    "phase.close",
    "evidence.capture",
    "contract.new",
)

# Read surfaces a consumer may shell to (dotted for subcommands).
READ_COMMANDS = (
    "capabilities",
    "state",
    "events",
    "sessions",
    "context",
    "next",
    "check",
    "gate",
    "verify",
    "doctor",
    "projects",
    "tree",
    "evidence.manifest",
    "evidence.asset",
)


def build_capabilities(root: Path) -> dict:
    from . import __version__
    from .events import EVENTS_SCHEMA
    from .manifest import EVIDENCE_SCHEMA
    from .sessions import SESSIONS_SCHEMA
    from .statefeed import FEED_SCHEMA

    try:
        roadmap_rel = rel(roadmap_dir(root), root)
    except DwError:
        roadmap_rel = None
    return {
        "capabilities_schema": CAPABILITIES_SCHEMA,
        "dw_version": __version__,
        "schemas": {
            "feed_schema": FEED_SCHEMA,
            "events_schema": EVENTS_SCHEMA,
            "sessions_schema": SESSIONS_SCHEMA,
            "evidence_schema": EVIDENCE_SCHEMA,
        },
        "statuses": sorted(STORY_STATUSES),
        "done_statuses": sorted(DONE_STATUSES),
        "verbs": list(MUTATION_VERBS),
        "commands": list(READ_COMMANDS),
        "roadmap_dir": roadmap_rel,
        "features": {
            "events_cursor": True,
            "evidence_manifest": True,
            "evidence_asset": True,
        },
    }
