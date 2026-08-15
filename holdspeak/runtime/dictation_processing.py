"""Voice-command and provider-pipeline processing for dictation capture."""
from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from ..dictation_runner import dispatch_voice_command, process_transcript


class DictationProcessingMixin:
    def _maybe_dispatch_voice_command(
        self, text: str, agent_reply_session: Any | None = None
    ) -> Any:
        # HS-52-04: thin delegate to the carved dispatch seam. Injects the runtime
        # typer for `type_text` macros and surfaces a matched command as a runtime
        # activity. Returns a VoiceCommandResult if a command fired (caller types
        # nothing), else None.
        def _type(t: str) -> None:
            from ..desktop_typing import type_text_from_owner_gesture

            macro_id = hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]
            type_text_from_owner_gesture(
                t,
                typer=self.typer,
                gesture="hold_release",
                target_profile=self._paste_target_profile(agent_reply_session),
                submit=False,
                macro_ref=f"voice-macro:{macro_id}",
                requested_target="focused",
                delivery_method="voice_macro",
            )

        def _activity(label: str) -> None:
            self._set_runtime_activity(
                "processing",
                source="dictation",
                label=label,
                detail=label,
                last_event="voice_command_match",
                last_error="",
            )

        return dispatch_voice_command(
            text,
            config=self.config,
            type_writer=_type,
            on_activity=_activity,
        )

    def _maybe_run_dictation_pipeline(
        self,
        text: str,
        *,
        audio_duration_s: float,
        transcribed_at: datetime,
        agent_reply_session: Any | None = None,
        journal_source: str = "hotkey",
        admission: Any = None,
    ) -> str:
        # HS-118-08: the hotkey path now delegates to process_transcript so
        # both hotkey and browser share the same factored function.
        import asyncio

        def _run() -> str:
            return asyncio.run(
                process_transcript(
                    text,
                    source=journal_source,
                    context=None,
                    config=self.config,
                    server=self.server,
                    agent_reply_session=agent_reply_session,
                    admission=admission,
                )
            )

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            # No loop is the expected hotkey-thread case. Do not wrap the pipeline
            # call itself in this catch: speech control signals subclass
            # RuntimeError and must escape once, without a second provider attempt.
            return _run()

        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(_run).result()


__all__ = ["DictationProcessingMixin"]
