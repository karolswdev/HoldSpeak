# Parked: the Desk no longer sends actor; the produced route refuses authority arguments.
from __future__ import annotations
class _ParkedBody:
    def decide(descriptor: Any) -> Callable[..., Awaitable[Any]]:
        async def api_gate_decide(proposal_id: str, request: Request) -> Any:
            # The desk's Approve and Deny still send ``actor``; the service never read
            # it (the decider is the edge's principal), so the shell drops the word.
            return await shell(request, descriptor.name, lambda body: {
                **{k: v for k, v in body.items() if k != "actor"}, "proposal_id": proposal_id}, 200)
        return api_gate_decide
