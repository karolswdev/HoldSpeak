"""Speaker service functions for the TUI layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ... import db as db_module


@dataclass(frozen=True)
class SpeakerProfileData:
    """Data needed to render the speaker profile screen."""

    speaker: Any
    stats: dict[str, Any]
    meeting_groups: list[dict[str, Any]]


def get_known_speakers_map() -> dict[str, dict[str, Any]]:
    """Return speaker metadata keyed by speaker id."""
    db = db_module.get_database()
    return {
        speaker.id: {"avatar": speaker.avatar, "name": speaker.name}
        for speaker in db.get_all_speakers()
    }


def get_speaker_profile_data(speaker_id: str) -> SpeakerProfileData | None:
    """Load all data needed for the speaker profile screen."""
    db = db_module.get_database()
    speaker = db.get_speaker(speaker_id)
    if speaker is None:
        return None

    return SpeakerProfileData(
        speaker=speaker,
        stats=db.get_speaker_stats(speaker_id),
        meeting_groups=db.get_speaker_segments(speaker_id),
    )


def update_speaker_identity(speaker_id: str, new_name: str, new_avatar: str) -> tuple[bool, bool]:
    """Update speaker display name and avatar."""
    db = db_module.get_database()
    name_success = db.update_speaker_name(speaker_id, new_name)
    avatar_success = db.update_speaker_avatar(speaker_id, new_avatar)
    return name_success, avatar_success
