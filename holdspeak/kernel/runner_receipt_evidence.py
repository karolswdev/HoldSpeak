"""One-shot object capability for Runner-owned inference disposition evidence."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from weakref import WeakSet

from .model import KernelRefused

RUNNER_RECEIPT_EVIDENCE_REQUIRED = "runner_receipt_evidence_required"
_MINT = object()
_ISSUED: WeakSet[RunnerReceiptEvidence] = WeakSet()
_ISSUER_INSTALLED = False


@dataclass(frozen=True, eq=False)
class RunnerReceiptEvidence:
    operation_id: str
    outcome: str
    result_ref: str
    runner_signal: str
    send_phase: str
    mint: Any = None

    def __post_init__(self) -> None:
        if self.mint is not _MINT:
            raise KernelRefused(RUNNER_RECEIPT_EVIDENCE_REQUIRED)


RunnerReceiptEvidenceIssuer = Callable[..., RunnerReceiptEvidence]


def _install_runner_receipt_evidence_issuer() -> RunnerReceiptEvidenceIssuer:
    global _ISSUER_INSTALLED
    if _ISSUER_INSTALLED:
        raise KernelRefused(RUNNER_RECEIPT_EVIDENCE_REQUIRED)
    _ISSUER_INSTALLED = True

    def issue(*, operation_id: str, outcome: str, result_ref: str,
              runner_signal: str, send_phase: str) -> RunnerReceiptEvidence:
        outcome_value = str(outcome)
        signal_value = str(runner_signal)
        phase_value = str(send_phase)
        lawful = {
            "compatibility_no_generation": {("failed", "provider_no_generation")},
            "known_no_generation_transient": {("failed", "provider_no_generation")},
            "provider_permanent_no_generation": {("failed", "provider_no_generation")},
            "permission_denied": {("refused", "provider_no_generation")},
            "local_capacity_unavailable": {("refused", "pre_send")},
            "invalid_typed_output": {("failed", "provider_returned")},
            "effect_indeterminate": {("failed", "provider_returned")},
            "physical_outcome_unknown": {("indeterminate", "dispatch_intent")},
            "dispatch_outcome_unknown": {("failed", "dispatch_intent")},
            "kernel_refused": {("refused", "pre_send"), ("refused", "dispatch_intent")},
            "unclassified_pre_send": {("failed", "pre_send")},
            "none": {
                ("succeeded", "provider_returned"), ("failed", "provider_returned"),
                ("failed", "pre_send"), ("refused", "pre_send"),
                ("cancelled", "pre_send"), ("indeterminate", "pre_send"),
                ("cancelled", "dispatch_intent"), ("indeterminate", "dispatch_intent"),
            },
        }
        if (outcome_value, phase_value) not in lawful.get(signal_value, set()):
            raise KernelRefused(RUNNER_RECEIPT_EVIDENCE_REQUIRED)
        evidence = RunnerReceiptEvidence(
            operation_id=str(operation_id), outcome=outcome_value,
            result_ref=str(result_ref), runner_signal=signal_value,
            send_phase=phase_value, mint=_MINT,
        )
        _ISSUED.add(evidence)
        return evidence

    return issue


def consume_runner_receipt_evidence(
    evidence: Any, *, operation_id: str, outcome: str, result_ref: str,
) -> RunnerReceiptEvidence:
    if not isinstance(evidence, RunnerReceiptEvidence) or evidence not in _ISSUED:
        raise KernelRefused(RUNNER_RECEIPT_EVIDENCE_REQUIRED)
    if (
        evidence.operation_id != str(operation_id)
        or evidence.outcome != str(outcome)
        or evidence.result_ref != str(result_ref)
    ):
        raise KernelRefused(RUNNER_RECEIPT_EVIDENCE_REQUIRED)
    _ISSUED.discard(evidence)
    return evidence


__all__ = [
    "RUNNER_RECEIPT_EVIDENCE_REQUIRED", "RunnerReceiptEvidence",
    "consume_runner_receipt_evidence",
]
