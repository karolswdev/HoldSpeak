"""PR review draft producer through the engine door; never posts a review."""
from __future__ import annotations
import hashlib
from typing import Any
from ..logging_config import get_logger
log = get_logger("services.delivery_review")
REVIEW_RETRY_KIND = "delivery.review"

def draft_review(service: Any, broker: Any, principal: Any, source_id: str, number: int) -> tuple[int, dict[str, Any]]:
    """Draft one PR review on the engine assigned to ``delivery.pr_review_draft``,
    through the engine door; ``(status, body)`` for the route (and for Retry)."""
    from ..services import engine_door

    context = service.action_context(source_id, number)
    if context.get("status") != "ok":
        return 404, {"error": "unknown_pr"}
    availability = ((context.get("row") or {}).get("verbs") or {}).get("draft_review") or {}
    if not availability.get("available"):
        return 409, {"error": "verb_unavailable", "verb": "draft_review",
                     "reason": availability.get("reason") or "unavailable"}
    material = service.review_material(source_id, number)
    if material.get("status") != "ok":
        return 409, {"error": "diff_unavailable", "reason": material.get("detail") or material.get("status")}
    try:
        engine = engine_door.engine_for(broker, "delivery.pr_review_draft")
    except engine_door.EngineDoorError:
        return 409, {"error": "delivery_pr_review_draft_refused", "reason": "inference_no_engine"}
    material_revision = str(material.get("revision") or "unversioned")
    diff_sha256 = hashlib.sha256(str(material.get("diff") or "").encode()).hexdigest()
    linked = material.get("linked") or []
    linked_text = "\n\n".join(str(item.get("text") or "") for item in linked)
    prompt = (
        f"Review PR #{number}. Return a concise GitHub review draft with concrete findings. "
        "Do not claim to have posted, approved, merged, or run checks.\n\n"
        f"Linked story and evidence:\n{linked_text[:48000]}\n\n"
        f"Diff:\n{str(material.get('diff') or '')[:120000]}"
    )

    def review_memory() -> Any:
        """Decisions and notes on the PR's subject (title, branch, story).

        The diff and the story are already in the prompt.
        """
        from ..db import get_database
        from ..services.memory_grounding import memory_for

        row = context.get("row") or {}
        return memory_for(
            "delivery.pr_review_draft",
            get_database(),
            query=" ".join(str(part or "") for part in (
                row.get("title"), row.get("head_ref"), material.get("story_id"),
            )),
        )

    payload = engine_door.with_memory(
        broker, engine,
        {
            "system_prompt": "You are a precise code reviewer. Findings first; cite files and lines when possible.",
            "user_prompt": prompt,
            "max_tokens": 1800,
            "temperature": None,
            "source_id": source_id,
            "number": number,
            "material_revision": material_revision,
            "diff_sha256": diff_sha256,
            "linked_revisions": [str(item.get("revision") or "") for item in linked],
        },
        review_memory,
        reserved_output_tokens=1800,
    )

    def projection(value: Any) -> dict[str, Any]:
        text = value.get("output") if isinstance(value, dict) else value
        return {"output": str(text or ""), "source_id": source_id, "number": number}

    try:
        answer = engine_door.run(
            broker, principal, "delivery.pr_review_draft", payload,
            engine=engine, deadline=300, stage=("delivery-pr-review", projection),
            retry=(REVIEW_RETRY_KIND, f"{source_id}|{number}"),
        )
    except engine_door.EngineDoorError as exc:
        return 409, {
            "error": "delivery_pr_review_draft_refused",
            "reason": "inference_" + (exc.outcome or exc.code),
            "operation_id": exc.operation_id,
        }
    published = answer.published if isinstance(answer.published, dict) else {}
    output = str(published.get("output") or "")
    artifact_id = str(published.get("artifact_id") or "")
    if not artifact_id or not output.strip():
        return 409, {"error": "delivery_pr_review_draft_refused"}
    return 200, {
        "output": output,
        "artifact_id": artifact_id,
        "result_ref": f"artifact:{artifact_id}",
        "invocation_id": answer.invocation_id,
        # The runner's kernel operation is the review's one receipt.
        "operation_id": answer.operation_id,
        "invocation": {"operation_id": answer.operation_id, "outcome": "succeeded"},
        "placement": {"source": "owner_assignment", "egress": {"scope": engine_door.egress_of(broker, answer.engine)}},
    }
