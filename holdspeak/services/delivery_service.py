"""Transport-neutral composition for the delivery domain."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

from pathlib import Path
from typing import Any

from ..db.core import Database
from .errors import NotFound, ValidationError


@observe_service
class DeliveryService:
    """Own delivery persistence and compose delivery collaborators.

    Routes may provide test doubles for individual delivery collaborators, but
    production construction goes through this boundary rather than reaching
    into the process-global database accessor.
    """

    def __init__(self, db: Database, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()

    def list_work_attempts(self) -> list[Any]:
        return self._db.work_attempts.list()

    def command_service(
        self,
        *,
        targets: Any,
        ledger_path: Path | None,
        local_node_id: str,
        mode_loader: Any = None,
        kernel_broker: Any = None,
    ) -> Any:
        from ..db.delivery_receipts import NodeReceiptLedger
        from ..delivery.commands import HubCommandService, NodeCommandProcessor

        processor = NodeCommandProcessor(
            node_id=local_node_id,
            targets=targets,
            ledger=NodeReceiptLedger(ledger_path),
        )
        return HubCommandService(
            repo=self._db.delivery_receipts,
            processor=processor,
            local_node_id=local_node_id,
            mode_loader=mode_loader,
            kernel_broker=kernel_broker,
        )

    def launch_service(
        self,
        *,
        profiles: Any,
        registry_path: Path | None,
        map_path: Path | None,
        targets: Any,
        commands: Any,
        launches_path: Path | None,
        local_node_id: str = "local",
    ) -> Any:
        from ..delivery import DeliveryRegistry
        from ..delivery.factory_launch import LaunchLedger, LaunchService

        return LaunchService(
            profiles=profiles,
            registry=DeliveryRegistry(registry_path, map_path=map_path),
            targets=targets,
            commands=commands,
            attempts=self._db.work_attempts,
            ledger=LaunchLedger(launches_path),
            local_node_id=local_node_id,
        )

    def attempt_service(
        self, *, registry_path: Path | None, map_path: Path | None
    ) -> Any:
        from ..delivery import DeliveryRegistry
        from ..delivery.attempts import WorkAttemptService, resolver_from_registry

        registry = DeliveryRegistry(registry_path, map_path=map_path)
        return WorkAttemptService(
            self._db.work_attempts,
            resolver=resolver_from_registry(registry),
        )

    def launch_sweep(
        self,
        *,
        registry_path: Path | None,
        map_path: Path | None,
        launches_path: Path | None,
        claims_state_path: Path | None,
    ) -> Any:
        launcher = self.launch_service(
            profiles=None,
            registry_path=registry_path,
            map_path=map_path,
            targets=None,
            commands=None,
            launches_path=launches_path,
        )

        def sweep() -> None:
            launcher.bind_rider_claims(state_path=claims_state_path)
            launcher.expire_unregistered()

        return sweep

    def default_launch_service(self) -> Any:
        from ..delivery.factory_launch import default_launch_service
        from ..kernel.runtime import _service as kernel_service

        service = default_launch_service(self._db)
        service.bind_kernel(kernel_service())
        return service

    def prepare_pr_review(
        self,
        *,
        invocation_id: str,
        requested_target_id: str,
        operation_id: str,
        broker: Any,
    ) -> tuple[Any, Any, Any]:
        """Create the durable review lifecycle and resolve its target."""
        if not invocation_id:
            raise ValidationError("invocation id is required")
        from ..inference_targets import build_intel_for_target, resolve_inference_target
        from .support import RunLifecycle

        lifecycle = RunLifecycle(
            self._db,
            invocation_id,
            "program:pr-review-v1",
            operation_id=operation_id,
            broker=broker,
        )
        target = resolve_inference_target(self._db, requested_target_id)
        return lifecycle, target, build_intel_for_target(target, self._db)

    def persist_pr_review_artifact(
        self, *, name: str, user_input: str, output: str, sources: list[dict[str, Any]]
    ) -> str | None:
        from .support import _persist_run_artifact

        return _persist_run_artifact(
            db=self._db,
            kind="pr_review",
            name=name,
            user_input=user_input,
            output=output,
            sources=sources,
        )

    def actuator_proposal(self, proposal_id: str) -> Any:
        proposal = self._db.actuators.get_proposal(proposal_id)
        if proposal is None:
            raise NotFound("proposal", proposal_id)
        return proposal

    def execute_actuator_proposal(
        self, executor: Any, ctx: Any, proposal: Any, *, actor: str
    ) -> Any:
        return executor(ctx, self._db, proposal, actor=actor)
