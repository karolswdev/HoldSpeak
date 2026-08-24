"""Retired v1 deferred-admission namespace.

New and recovered Meeting queue work binds through
:mod:`holdspeak.services.meeting_deferred_queue_binding` and executes only from
stored bundle evidence in :mod:`.deferred_bound`.  This module deliberately
contains no v1 planner, parent admission, child runner, or provider dispatch.
"""

from .deferred_bound import (
    BoundDeferredIntelJob,
    PARENT_KIND,
    QUEUE_SERVICE_IDENTITY,
    queue_service_principal,
)

__all__ = [
    "BoundDeferredIntelJob",
    "PARENT_KIND",
    "QUEUE_SERVICE_IDENTITY",
    "queue_service_principal",
]
