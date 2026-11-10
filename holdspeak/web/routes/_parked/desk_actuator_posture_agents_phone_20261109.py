# PARKED: desk proposals wait for an owner decision in every posture.
class _ParkedBody:
    def apply(self, proposal: Any, target: str) -> Any:
        return apply_control_posture(self._ctx, self._db, proposal, executors=self._executors(target))

