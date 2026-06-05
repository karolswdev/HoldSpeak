"""HoldSpeak persistence layer.

Phase 31 decomposition: per-domain repositories (MeetingRepository, IntelRepository)
behind the Database container. Re-exports the full public surface so
existing `from holdspeak.db import X` imports keep working.
"""
from .models import *  # noqa: F401,F403
from .base import BaseRepository  # noqa: F401
from .meetings import MeetingRepository  # noqa: F401
from .intel import IntelRepository  # noqa: F401
from .actuators import ActuatorRepository  # noqa: F401
from .corrections import DictationCorrectionRepository  # noqa: F401
from .core import *  # noqa: F401,F403
from .core import (  # noqa: F401  explicit: names import * may skip
    Database,
    DEFAULT_DB_PATH,
    SCHEMA_VERSION,
    SCHEMA_SQL,
)
