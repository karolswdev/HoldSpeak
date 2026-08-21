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
from .journal import DictationJournalRepository  # noqa: F401
from .milestones import MilestoneRepository, FIRST_DICTATION_SUCCESS  # noqa: F401
from .dictation_delivery import DictationDeliveryRepository  # noqa: F401
from .cadence import CadenceRepository  # noqa: F401
from .mesh_relay import MeshRelayRepository  # noqa: F401
from .mesh_worker import MeshWorkerRepository  # noqa: F401
from .invocations import CapabilityInvocationRepository  # noqa: F401
from .projections import DeskProjection, ProjectionRepository  # noqa: F401
from .decisions import (  # noqa: F401
    DecisionLifecycleReceipt,
    DecisionRecord,
    DecisionRepository,
    DecisionTransitionRefused,
    backfill_decisions,
    derive_decision_id,
)
from .memory import (  # noqa: F401
    MemoryHit,
    MemoryRepository,
    MemorySearchResult,
    rebuild_memory_index,
)
from .primitives import (  # noqa: F401
    NoteRepository,
    KBRepository,
    RecipeRepository,
    ChainRepository,
    WorkflowRepository,
    DirectoryRepository,
    DirectoryMembershipRepository,
)
from .refinement_thoughts import RefinementThoughtRepository  # noqa: F401
from .scheduled_recordings import (  # noqa: F401
    ScheduledRecording,
    ScheduledRecordingRepository,
)
from .schema import SCHEMA_VERSION, SCHEMA_SQL  # noqa: F401
from .core import *  # noqa: F401,F403
from .reconcile import reconcile_schema  # noqa: F401
from .core import (  # noqa: F401  explicit: names import * may skip
    Database,
    DEFAULT_DB_PATH,
    backup_database,
    get_observer,
    restore_database,
)
