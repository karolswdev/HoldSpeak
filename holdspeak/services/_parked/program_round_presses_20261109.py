"""PARKED 20261109 (ops/programs-work): the four per-press round methods of ``ProgramService``.

The Programs face's round presses (open, next, answer, decide) now enter the
service where the MCP tool ``program.round`` does: ``ProgramService.round``
(``program_rounds.act``), through the HTTP descriptors in
``holdspeak/program_operations.py``. One service verb for the rounds; these
four second entries had no other caller. Kept here, as text, in the order they
stood.

Not imported. Restore with git revert of the parking commit.
"""
# ruff: noqa
# fmt: off
PARKED = True

'''
    def rounds_open(self, principal: Any, program_id: str, names: Any = None) -> dict[str, Any]:
        from .program_rounds import open_rounds

        return open_rounds(self, principal, program_id, names)

    def round_next(self, principal: Any, program_id: str, name: str) -> dict[str, Any]:
        from .program_rounds import ask

        return ask(self, principal, program_id, name)

    def round_answer(self, principal: Any, program_id: str, name: str, *, answer: Any = None, option: Any = None,
                     question_id: Any = None, skip: bool = False, not_this: bool = False,
                     apply: bool = False) -> dict[str, Any]:
        """``{question_id, answer | option | skip}`` (§12); ``not_this``: the
        answer's rows were dismissed, so it became nothing."""
        from . import program_rounds as rounds

        qid = str(question_id) if question_id else None
        if skip:
            return rounds.skip_question(self, principal, program_id, name, qid)
        if not_this:
            return rounds.not_this(self, principal, program_id, name, qid or "")
        return rounds.answer(self, principal, program_id, name, answer, question_id=qid, choice=option, apply=apply)

    def round_decide(self, principal: Any, program_id: str, name: str, choice: Any) -> dict[str, Any]:
        from .program_rounds import decide

        return decide(self, principal, program_id, name, choice)

'''
