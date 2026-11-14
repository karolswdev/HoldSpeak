"""Room failure words, with the shared service error codes and context."""
from .errors import NotFound


def room_not_found(kind: str, identity: str) -> NotFound:
    error = NotFound(kind, identity)
    error.detail = f"The {kind.replace('_', ' ')} is not available."
    error.args = (error.detail,)
    return error
