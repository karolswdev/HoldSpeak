"""The two speech control signals (HS-131-09).

Every speech model call goes through the engine door (``services/engine_door``)
as a child of its live session. These are the only two error types a speech
call raises to its caller: a named refusal (``SpeechSessionRefused``, in
``plan.py``) or a model failure named by contract and a SAFE reason
(:class:`SpeechProviderFailure`).
"""

from __future__ import annotations

from typing import Optional

from .plan import SpeechSessionRefused


class SpeechProviderFailure(RuntimeError):
    """A model failure named by contract and a short SAFE reason only.

    Backend exception text can carry file paths, endpoint bodies, or echoed
    transcript fragments. The kernel journal must never receive that, so this is
    the only error string a speech child ever raises: the exception TYPE name, or
    an explicit sanitized reason.
    """

    def __init__(
        self, contract: str, exc: Optional[BaseException] = None, *, reason: str = ""
    ) -> None:
        short = reason or (type(exc).__name__ if exc is not None else "model_error_result")
        super().__init__(f"{contract}:{short}")
        self.contract = contract
        self.reason = short


def fatal_speech_signal(exc: BaseException) -> bool:
    """True for the speech CONTROL signals that may never degrade to raw text.

    HS-131-15 (Sol Amendment 3). Session refusal, provider failure, expiry or
    revocation, and child-budget refusal all arrive as one of these two types.
    They are not "a stage had a bad day": they mean the work was never
    authorized or must not publish. A broad ``except Exception`` that swallows
    them turns a refusal into a successful-looking raw-text result.

    DIR-F-003 degradation still applies to every ORDINARY stage failure.
    """
    return isinstance(exc, (SpeechSessionRefused, SpeechProviderFailure))


__all__ = ["SpeechProviderFailure", "fatal_speech_signal"]
