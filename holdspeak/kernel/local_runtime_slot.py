"""Which inference dispatch takes the local runtime lease.

The local runtime lease (``local_runtime_lease``) exists so that two large
local artifacts are not loaded at one time.  Some adapters load their OWN
small in-process model, never the assigned chat artifact.  An embedding model
is one: it is a separate, small model, so its calls neither take the lease nor
wait for it.  A live local chat or dictation call is then never refused by a
background embed batch, and the reverse.
"""
from __future__ import annotations

from typing import Any

#: The set is closed: a new slot is a reviewed line.
OWN_LOCAL_SLOTS = frozenset({"embedding"})


def own_local_slot(adapter: Any) -> bool:
    """True when the adapter declares a slot that loads its own small model."""
    return str(getattr(adapter, "local_runtime_slot", "") or "") in OWN_LOCAL_SLOTS


def takes_local_runtime_lease(revision: Any, adapter: Any) -> bool:
    """True when this dispatch must hold the one local runtime lease."""
    return (
        revision.schema_version >= 2
        and revision.boundary == "same_device"
        and not own_local_slot(adapter)
    )
