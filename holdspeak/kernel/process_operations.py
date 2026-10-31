"""Typed registration for commands that act on an existing process."""

from typing import Any

from .model import OperationSpec
from .process_input import ProcessInputCodec
from .process_resize import ProcessResizeCodec


def process_operations(commands: Any) -> tuple[OperationSpec, ...]:
    return tuple(
        OperationSpec(codec.name, codec.version, codec, "agent.submit", "propose")
        for codec in (ProcessInputCodec(commands), ProcessResizeCodec(commands))
    )
