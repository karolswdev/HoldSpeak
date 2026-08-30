"""HS-152-01: Protocol contract for the thread tool executor.

The pass loop (ThreadService._run_streaming_turn) codes against the real
ThreadToolExecutor from thread_tools.py.  This module documents the
seam contract and provides a lightweight Protocol for static checking
and test fakes.  The gate builder (HS-152-02, thread_tools.py) satisfies
it.

The data classes (ToolCall) are imported by the loop; ToolCallHandle and
ToolResult live in thread_tools.py and are the single source of truth.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Optional, Protocol, runtime_checkable


@dataclass(frozen=True)
class ToolCall:
    """One tool call parsed from the model's response.

    This is the brief's input shape for ``executor.admit()``.  The loop
    constructs it from the ``tool_calls`` Delta meta and passes it as a
    dict to the real executor (which accepts ``dict[str, Any]``).
    """

    id: str
    name: str
    arguments: str  # JSON string


@runtime_checkable
class ThreadToolExecutorProtocol(Protocol):
    """The contract the thread tool loop requires from its executor.

    Documented here so both the loop and the gate builder share one
    definition.  The gate builder (thread_tools.py) satisfies this
    with the real ``ThreadToolExecutor`` class.  Test fakes in
    ``test_thread_tool_loop.py`` satisfy it directly.
    """

    def admit(
        self,
        turn_operation_id: str,
        thread_id: str,
        call: dict[str, Any],
    ) -> Any:
        """Resolve a tool call through the truth table.

        Returns a ``ToolCallHandle`` whose ``state`` is one of
        ``'admitted'``, ``'awaiting_decision'``, or ``'denied'``.
        """
        ...

    def decide(
        self,
        handle: Any,
        decision: str,
        answer: Any = None,
    ) -> None:
        """Resolve a held call: 'approve' or 'deny'."""
        ...

    def execute(
        self,
        handle: Any,
    ) -> Any:
        """Execute an admitted tool call and return a ``ToolResult``."""
        ...

    def cancel(
        self,
        handle: Any,
    ) -> None:
        """Signal cancellation for an in-flight call."""
        ...

    @property
    def on_decided(self) -> Any:
        """Callback ``(call_id: str) -> None`` set by the loop."""
        ...

    @on_decided.setter
    def on_decided(self, callback: Any) -> None: ...
