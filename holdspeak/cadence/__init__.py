"""The Cadence Engine (CAD-1) — a local-first technical chief-of-staff.

Turns existing HoldSpeak knowledge (meetings, activity, dictation, coding-agent
state) into evidence-backed nudges and nearly-complete next actions:

    Open Loop -> Next Best Action -> Nudge -> Decision

Hard invariants (see pm/roadmap/holdspeak/cadence-engine/README.md):
- Off by default (CadenceConfig.enabled is False); byte-identical when off.
- No external side effect except via the existing actuator propose/approve/execute
  path. This package performs NONE; it only reads sources and writes cadence_* rows.
- Every nudge carries evidence; killed loops stay killed; quiet hours default-on.
"""

from .models import (
    CadencePolicy,
    EvidenceRef,
    Nudge,
    NextBestAction,
    OpenLoop,
    ScoreBreakdown,
)

__all__ = [
    "OpenLoop",
    "EvidenceRef",
    "NextBestAction",
    "Nudge",
    "CadencePolicy",
    "ScoreBreakdown",
]
