"""Local activity-intelligence ledger.

Extracted verbatim from core.py in Phase 31 (HS-31-03); carved into concern
mixins in Phase 79 (HS-79-01) — the Phase-63 discipline. The public surface is
unchanged: ``ActivityRepository`` composes the mixins over ``BaseRepository``.
"""
from __future__ import annotations

from ..base import BaseRepository
from .annotations import ActivityAnnotationsMixin
from .candidates import ActivityCandidatesMixin
from .enrichment import ActivityEnrichmentMixin
from .records import ActivityRecordsMixin
from .rules import ActivityRulesMixin
from .settings import ActivitySettingsMixin


class ActivityRepository(
    ActivityRecordsMixin,
    ActivitySettingsMixin,
    ActivityRulesMixin,
    ActivityEnrichmentMixin,
    ActivityAnnotationsMixin,
    ActivityCandidatesMixin,
    BaseRepository,
):
    """Local activity-intelligence ledger."""
