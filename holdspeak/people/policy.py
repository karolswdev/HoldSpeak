"""Hard policy limits for People PR1, independent of the UI."""

from __future__ import annotations

from enum import StrEnum


class Visibility(StrEnum):
    LEADER_PRIVATE = "leader_private"
    SHARED_INTENT = "shared_intent"


class PeopleOperation(StrEnum):
    READ = "read"
    WRITE = "write"
    CAPTURE = "capture"
    INFERENCE = "inference"
    SYNC = "sync"
    EXPORT = "export"
    EGRESS = "egress"
    SEARCH_PERSIST = "search_persist"
    MCP_READ = "mcp_read"
    MCP_WRITE = "mcp_write"


class PeopleUse(StrEnum):
    """Employment-domain uses that must stay impossible, even in later UI work."""

    INDIVIDUAL_SCORING = "individual_scoring"
    RANKING_OR_COMPARISON = "ranking_or_comparison"
    PERFORMANCE_RECOMMENDATION = "performance_recommendation"
    PAY_OR_PROMOTION_RECOMMENDATION = "pay_or_promotion_recommendation"
    DISCIPLINE_OR_TERMINATION_RECOMMENDATION = "discipline_or_termination_recommendation"
    PRODUCTIVITY_OR_ACTIVITY_PROXY = "productivity_or_activity_proxy"
    SENTIMENT_OR_PERSONALITY_INFERENCE = "sentiment_or_personality_inference"
    HEALTH_OR_BURNOUT_INFERENCE = "health_or_burnout_inference"
    LOYALTY_OR_FLIGHT_RISK_INFERENCE = "loyalty_or_flight_risk_inference"
    AUTOMATIC_OPPORTUNITY_ALLOCATION = "automatic_opportunity_allocation"
    SOURCE_CITED_DRAFT = "source_cited_draft"


class PeoplePolicy:
    """PR1 allows only this-device owner reads/writes of encrypted records."""

    _LOCAL_ALLOWED = frozenset({PeopleOperation.READ, PeopleOperation.WRITE})
    _MCP_ALLOWED = frozenset({PeopleOperation.MCP_READ, PeopleOperation.MCP_WRITE})

    @classmethod
    def allows(cls, visibility: Visibility, operation: PeopleOperation) -> bool:
        if not isinstance(visibility, Visibility):
            return False
        if operation in cls._LOCAL_ALLOWED:
            return True
        # The separately capability-gated MCP adapter is the one deliberate PR1
        # disclosure path.  The policy still refuses leader-private material even
        # when the parent process was granted People MCP access.
        return visibility is Visibility.SHARED_INTENT and operation in cls._MCP_ALLOWED

    @classmethod
    def refusal(cls, visibility: Visibility, operation: PeopleOperation) -> str | None:
        return None if cls.allows(visibility, operation) else "people_operation_unsupported"

    @staticmethod
    def refusal_for_use(use: PeopleUse) -> str:
        """PR1 runs no People intelligence; prohibited employment uses stay named.

        Keeping the domain refusal separate from the generic no-inference response
        prevents a future drafting feature from accidentally admitting scoring or
        employment decisions merely because model access becomes available.
        """
        if use is PeopleUse.SOURCE_CITED_DRAFT:
            return "people_inference_unsupported"
        return "people_employment_use_prohibited"
