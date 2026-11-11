# PARKED: the private execution read is a PeopleService operation.
class _ParkedBody:
    @router.get("/commitments/{commitment_id}/execution")
    def commitment_execution(request: Request, commitment_id: str) -> dict[str, Any]:
        try:
            commitment = service.get_commitment(principal(request), commitment_id)
            items = []
            wb = workbenches()
            for link in commitment.get("execution_links") or []:
                if not isinstance(link, dict) or link.get("kind") != "workbench_item":
                    continue
                try:
                    item = wb.get_item(principal(request), str(link.get("workbench_id") or ""), str(link.get("item_id") or ""))
                except NotFound:
                    item = {**link, "status": "missing", "result": None, "result_artifact_id": None}
                items.append(item)
            return {"commitment": commitment, "items": items}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc
