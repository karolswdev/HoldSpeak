"""Typed process.resize@1 admission and bounded geometry."""

from __future__ import annotations

import pytest

from holdspeak.kernel.model import KernelRefused, OperationRequest
from holdspeak.kernel.process_resize import ProcessResizeCodec, bounded_dimensions


COMMAND = "123e4567-e89b-12d3-a456-426614174000"


def request(**arguments):
    return OperationRequest(
        request_schema=1,
        request_id=COMMAND,
        idempotency_key="process.resize:" + COMMAND,
        name="process.resize",
        version=1,
        target_ref="process:term_test",
        placement="node:local",
        arguments={
            "cols": 100,
            "rows": 30,
            "expected_generation": "gen_test",
            "expected_pane_id": "%5",
            "command_id": COMMAND,
            "expected_sequence": 1,
            **arguments,
        },
    )


def test_resize_codec_admits_dimensions_without_content() -> None:
    admission = ProcessResizeCodec(None).validate(request())
    assert admission.native_id == COMMAND
    assert admission.head == "terminal resize 100x30"


@pytest.mark.parametrize(
    "kwargs, reason",
    [
        ({"cols": 0}, "process_resize_dimensions_out_of_bounds"),
        ({"rows": 301}, "process_resize_dimensions_out_of_bounds"),
        ({"cols": "wide"}, "process_resize_dimensions_invalid"),
        ({"cols": 1.5}, "process_resize_dimensions_invalid"),
        ({"rows": True}, "process_resize_dimensions_invalid"),
        ({"expected_pane_id": "session:0.0"}, "process_resize_prerequisite_failed"),
        ({"expires_in_seconds": float("nan")}, "process_resize_ttl_invalid"),
        ({"expires_in_seconds": float("inf")}, "process_resize_ttl_invalid"),
    ],
)
def test_resize_codec_refuses_unbounded_or_mutable_geometry(kwargs, reason) -> None:
    with pytest.raises(KernelRefused) as refused:
        ProcessResizeCodec(None).validate(request(**kwargs))
    assert refused.value.reason == reason


def test_resize_bounds_are_explicit() -> None:
    assert bounded_dimensions(1, 1) == (1, 1)
    assert bounded_dimensions(500, 300) == (500, 300)
    with pytest.raises(KernelRefused):
        bounded_dimensions(501, 300)
