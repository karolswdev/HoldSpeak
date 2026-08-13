"""The dictation capture path (HS-63-03).

Transcribe-and-type, the hotkey handlers, the tmux agent-reply path, and
voice-command dispatch — verbatim moves out of WebRuntime.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Any, Callable, Optional

import numpy as np

from ..logging_config import get_logger
from ..speech_session import HOLD_DRAIN_SECONDS as _HOLD_DRAIN_SECONDS
from ..speech_session import SpeechSessionRefused, admit_one_shot_session, fatal_speech_signal
from .dictation_delivery import DictationDeliveryMixin
from .dictation_previews import DictationPreviewMixin
from .dictation_processing import DictationProcessingMixin
from .dictation_session import HoldSessionMixin

log = get_logger("web_runtime")

# HS-32-03: the owner string a meeting uses to hold the shared
# ``VoiceTypingSession`` audio floor. One arbiter for hotkey / device /
# meeting capture; while a meeting holds this, hotkey/device ``begin()``
# is rejected, and a meeting can't start while either holds the floor.
_MEETING_AUDIO_OWNER = "meeting"


class BrowserTranscription:
    """One browser utterance's text plus the LIVE authority its pipeline runs under.

    HS-131-09: the browser pipeline stages (classify, rewrite) are real model
    calls, so they must be children of the utterance's own parent. The one-shot
    parent therefore stays open until :meth:`close`, and the caller reports the
    honest terminal outcome — a pipeline that RAISED closes the parent ``failed``.
    """

    __slots__ = ("text", "provider", "_session")

    def __init__(self, text: str, provider: Any, session: Any) -> None:
        self.text = str(text)
        self.provider = provider
        self._session = session

    @property
    def owns_parent(self) -> bool:
        """True when closing this handle closes a parent (the one-shot case)."""
        return self._session is not None

    def close(self, outcome: str = "succeeded") -> str:
        """Close the one-shot parent with its honest outcome; a no-op inside an interval."""
        if self._session is None:
            return ""
        return str(self._session.close(outcome))


class DictationCaptureMixin(
    HoldSessionMixin,
    DictationPreviewMixin,
    DictationDeliveryMixin,
    DictationProcessingMixin,
):
    def _transcribe_and_type(
        self,
        audio: np.ndarray,
        *,
        on_complete: Optional[Callable[[str], None]] = None,
        agent_reply_session: Any | None = None,
        session: Any = None,
    ) -> Optional[str]:
        """Run transcription, text processing, and typing for a captured chunk.

        Shared between the local hotkey path and the device-driven
        voice-typing path (HS-14-05). Always flips voice state back
        to ``idle`` in its ``finally``. ``on_complete`` (HS-14-07)
        receives the typed text on success and is intentionally
        invoked outside the typing try-block — typing failures
        still surface the transcript to the device.

        Returns the parent's honest terminal outcome: ``"failed"`` when the
        transcription or the pipeline RAISED, otherwise ``None`` (the caller closes
        ``succeeded``). Recording the failure here is what stops a session whose
        work blew up from closing as a success.
        """
        completed_text: Optional[str] = None
        #: Non-empty when this tail raised; the parent must not close succeeded.
        failure: list[str] = []
        # HS-131-09 (Sol OQ5): the live session travels EXPLICITLY down this
        # closure — there is no ambient "current dictation session" field to read.
        # THIS closure owns these three handles for its whole life: the
        # transcription admission (one Whisper child), the provider admission
        # (one child per pipeline model call, against the session's frozen plan),
        # and the immutable fence that discards late text.
        admission = None if session is None else session.transcription()
        provider = None if session is None else session.provider()
        fence = None if session is None else session.fence
        with self.transcription_lock:
            try:
                text = self._ensure_transcriber_loaded().transcribe(audio, admission=admission)
                if not text:
                    self._set_runtime_activity(
                        "complete",
                        source="dictation",
                        label="No speech",
                        detail="No speech detected.",
                        last_event="dictation_no_speech",
                        last_error="",
                    )
                    return
                if fence is not None and fence.discarded("dictation text processing"):
                    return
                text = self.text_processor.process(text)
                # HS-52-04: voice command dispatch. A configured, enabled keyword fires
                # an action instead of being typed; on a match we return early and type
                # nothing. Off by default and on no match this is inert (byte-identical).
                #
                # HS-131-15 closes the interval between the two: the fence was
                # checked BEFORE `text_processor.process`, and dispatch then ran
                # with no further election — so a cancellation landing in between
                # still fired a macro, which is a real connector/typing EFFECT.
                # Dispatch now happens INSIDE the same lock-protected election
                # that cancellation contends for. A cancellation winner discards
                # and returns; it is not treated as an ordinary unmatched command.
                def _dispatch_voice_command() -> Any:
                    voice_command = self._maybe_dispatch_voice_command(
                        text, agent_reply_session
                    )
                    if voice_command is None:
                        return None
                    if voice_command.ok:
                        self._set_runtime_activity(
                            "complete",
                            source="dictation",
                            label="Command",
                            detail=voice_command.preview,
                            last_event="voice_command_fired",
                            last_error="",
                        )
                        self._mark_first_dictation()
                    else:
                        with self.state_lock:
                            self.runtime_status["last_error"] = (
                                f"Voice command failed: {voice_command.error}"
                            )
                        self._set_runtime_activity(
                            "error",
                            source="dictation",
                            label="Command failed",
                            detail=voice_command.preview,
                            last_event="voice_command_failed",
                            last_error=voice_command.error,
                        )
                    if session is not None:
                        # Command publication won. Settle the speech parent before
                        # releasing the same election; cancellation cannot overwrite
                        # an effect that has already fired.
                        session.close("succeeded")
                    return voice_command

                if fence is not None:
                    dispatched, voice_command = fence.publish(
                        "dictation voice-command dispatch", _dispatch_voice_command
                    )
                    if not dispatched:
                        return
                else:
                    voice_command = _dispatch_voice_command()
                if voice_command is not None:
                    return
                self._set_runtime_activity(
                    "processing",
                    source="dictation",
                    detail="Processing dictation.",
                    last_event="dictation_processing",
                    last_error="",
                )
                text = self._maybe_run_dictation_pipeline(
                    text,
                    audio_duration_s=len(audio) / 16000.0,
                    transcribed_at=datetime.now(),
                    agent_reply_session=agent_reply_session,
                    admission=provider,
                )
                if not text:
                    # Either nothing survived the pipeline or the session was
                    # fenced mid-run: no preview, no delivery, no journal row.
                    return
                # HS-75-01: preview before it types (opt-in; the P60 wake
                # grammar on hold-key dictation). An agent-reply session is
                # never previewed — answering the coder is an explicit,
                # targeted act (the companion flow stays immediate). Off by
                # default this block is inert: byte-identical typing.
                from ..operation_policy import resolve_dictation_policy

                policy_snapshot, dictation_policy = resolve_dictation_policy(self.config)
                with self.state_lock:
                    self.runtime_status["last_operation_policy"] = policy_snapshot

                def _publish_text() -> None:
                    nonlocal completed_text
                    completed_text = text
                    with self.state_lock:
                        self.runtime_status["last_transcription"] = text
                        self.runtime_status["last_error"] = ""
                    print(f"-> {text}")

                if agent_reply_session is None and dictation_policy.requires_review:
                    def _publish_preview() -> None:
                        _publish_text()
                        self._arm_dictation_preview(text)
                        if on_complete is not None:
                            on_complete(text)
                        if session is not None:
                            session.close("succeeded")

                    if fence is not None:
                        published, _value = fence.publish(
                            "dictation preview publication", _publish_preview
                        )
                        if not published:
                            completed_text = None
                    else:
                        _publish_preview()
                    return

                def _deliver_text() -> None:
                    _publish_text()
                    delivered = self._try_tmux_agent_reply(text, agent_reply_session)
                    if delivered:
                        self._set_runtime_activity(
                            "complete",
                            source="dictation",
                            label="Sent",
                            detail="Sent dictated text to the agent session.",
                            last_event="dictation_delivered",
                            last_error="",
                        )
                        self._mark_first_dictation()
                    else:
                        try:
                            paste_target_profile = self._paste_target_profile(
                                agent_reply_session
                            )
                            self._set_runtime_activity(
                                "typing",
                                source="dictation",
                                detail="Typing dictated text.",
                                last_event="dictation_typing",
                                last_error="",
                            )
                            # Delivery performs its OWN existing effect admission and
                            # idempotency. The speech fence elects only whether this
                            # exact handoff may begin; it is not a second effect receipt.
                            from ..desktop_typing import type_text_from_owner_gesture

                            type_text_from_owner_gesture(
                                text,
                                typer=self.typer,
                                gesture="hold_release",
                                target_profile=paste_target_profile,
                                submit=False,
                                requested_target=(
                                    "agent_fallback"
                                    if agent_reply_session is not None
                                    else "focused"
                                ),
                                delivery_method="desktop_fallback",
                            )
                            self._set_runtime_activity(
                                "complete",
                                source="dictation",
                                label="Typed",
                                detail="Dictated text was inserted.",
                                last_event="dictation_typed",
                                last_error="",
                            )
                            self._mark_first_dictation()
                        except Exception as exc:
                            with self.state_lock:
                                self.runtime_status["last_error"] = f"Typing failed: {exc}"
                                self.runtime_status["text_injection_enabled"] = False
                                self.runtime_status["text_injection_error"] = (
                                    f"{type(exc).__name__}: {exc}"
                                )
                            self._set_runtime_activity(
                                "error",
                                source="dictation",
                                detail="Typing failed.",
                                last_event="dictation_typing_failed",
                                last_error=f"{type(exc).__name__}: {exc}",
                            )
                            log.warning(f"Typing failed in web mode: {exc}")
                    if on_complete is not None and completed_text is not None:
                        try:
                            on_complete(completed_text)
                        except Exception as exc:
                            log.warning(f"on_complete hook raised: {exc}")
                    if session is not None:
                        # Effect/publication first settles the speech parent before
                        # releasing the SAME election. The caller's final close is
                        # idempotent and cannot be overwritten by cancellation.
                        session.close("succeeded")

                if fence is not None:
                    published, _value = fence.publish(
                        "dictation delivery handoff", _deliver_text
                    )
                    if not published:
                        completed_text = None
                        return
                else:
                    _deliver_text()
            except Exception as exc:
                if fatal_speech_signal(exc):
                    # Admission, revision, provider, expiry, and cancellation are
                    # control outcomes. The session owner maps them honestly; this
                    # broad UI failure path must not rename them "Transcription failed".
                    raise
                failure.append(f"{type(exc).__name__}")
                with self.state_lock:
                    self.runtime_status["last_error"] = f"Transcription failed: {exc}"
                self._set_runtime_activity(
                    "error",
                    source="dictation",
                    detail="Transcription failed.",
                    last_event="dictation_transcription_failed",
                    last_error=f"{type(exc).__name__}: {exc}",
                )
                log.error(f"Transcription failed in web mode: {exc}")
            finally:
                self._set_voice_state("idle", update_activity=False)
        return "failed" if failure else None

    def transcribe_audio(
        self,
        audio,
        *,
        principal: Any | None = None,
        mic_handle: str = "",
    ) -> str:
        """Transcribe browser-captured audio for speak-to-fill (HS-78-01).

        The runtime's OWN transcriber (one model, one lock; the MLX thread
        pinning lives inside it) + the same punctuation/spoken-symbol pass
        dictation gets. No journaling (a speak-to-fill is the user typing
        with their voice, not a dictation run), no persistence, no egress.

        This is the NO-PIPELINE seam: the transcription is the whole tail, so a
        one-shot parent closes the moment this returns. A caller that will run
        pipeline stages must use :meth:`transcribe_audio_admitted` instead, so
        classify/rewrite become children of the SAME parent.
        """
        handle = self.transcribe_audio_admitted(
            audio, principal=principal, mic_handle=mic_handle
        )
        handle.close("succeeded")
        return handle.text

    def transcribe_audio_admitted(
        self,
        audio,
        *,
        principal: Any | None = None,
        mic_handle: str = "",
    ) -> Any:
        """Transcribe under a live authority and HAND THAT AUTHORITY BACK.

        HS-131-09 (Sol OQ3): INSIDE an active open-mic interval this utterance
        JOINS that interval's parent — one visible interval is one authority, and
        its inactivity lease refreshes inside this utterance's first Whisper child
        claim. OUTSIDE one, a one-shot click admits ONE short authenticated
        ``dictation.session``.

        The returned handle carries the provider admission and stays OPEN until
        the caller closes it, so the browser pipeline's classify/rewrite calls run
        as trusted children of this same parent instead of as unwrapped runtime
        work after the parent had already closed.
        """
        from ..speech_session import browser_mic_sessions

        interval = None
        if principal is not None:
            interval = browser_mic_sessions().resolve(principal, mic_handle)
        if interval is not None:
            with self.transcription_lock:
                text = self._ensure_transcriber_loaded().transcribe(
                    audio, admission=interval.transcription()
                )
            processed = "" if not text else self.text_processor.process(text)
            # The interval owns its parent's lifetime; this utterance never closes it.
            return BrowserTranscription(processed, interval.session.provider(), None)
        session = admit_one_shot_session(
            principal=principal, config_snapshot=self.config
        )
        try:
            with self.transcription_lock:
                text = self._ensure_transcriber_loaded().transcribe(
                    audio, admission=session.transcription()
                )
        except BaseException:
            session.close("failed")
            raise
        processed = "" if not text else self.text_processor.process(text)
        return BrowserTranscription(processed, session.provider(), session)

    def _kick_off_transcribe(
        self,
        audio: np.ndarray,
        *,
        on_complete: Optional[Callable[[str], None]] = None,
        agent_reply_session: Any | None = None,
        source: str = "dictation",
        session: Any = None,
    ) -> None:
        if len(audio) < 1600:
            # Mechanical: nothing reaches a model, so the admitted session closes
            # immediately instead of holding authority over an abandoned tail.
            if session is not None:
                session.close("succeeded")
            self._set_voice_state("idle", update_activity=False)
            self._set_runtime_activity(
                "complete",
                source=source,
                label="Too short",
                detail="Recording was too short.",
                last_event="dictation_too_short",
                last_error="",
            )
            return
        self._set_voice_state(
            "transcribing",
            source=source,
            detail="Transcribing audio.",
            last_event="dictation_transcribing",
            last_error="",
        )

        def _run() -> None:
            outcome = "succeeded"
            try:
                outcome = (
                    self._transcribe_and_type(
                        audio,
                        on_complete=on_complete,
                        agent_reply_session=agent_reply_session,
                        session=session,
                    )
                    or "succeeded"
                )
            except SpeechSessionRefused:
                # A liveness/revision/authority refusal is not a provider crash.
                # Preserve the named control outcome on the parent receipt.
                outcome = "refused"
                raise
            except BaseException:
                # Nothing else should reach here (the tail records ordinary UI
                # failures), but a parent must never close succeeded over an
                # escaped provider failure or unexpected exception.
                outcome = "failed"
                raise
            finally:
                # The parent closes the moment its bounded tail finishes
                # (Sol Amendment 2), never on the 90-second drain alone — with the
                # tail's HONEST outcome, not a default success.
                if session is not None:
                    session.close(outcome)

        threading.Thread(target=_run, daemon=True).start()

    def _on_hotkey_press(self) -> None:
        if self.runtime_stop_event.is_set():
            return
        if self.recorder is None:
            self._set_runtime_activity(
                "error",
                source="hotkey",
                detail="Voice typing hotkey is unavailable.",
                last_event="dictation_hotkey_unavailable",
                last_error=str(self.runtime_status.get("global_hotkey_error") or ""),
            )
            return
        generation, _lock = self._hold_state()
        token = generation.begin()
        # HS-32-03: no explicit "is a meeting active?" check — the shared
        # `voice_session` arbiter is the single owner model. While a meeting
        # holds the floor (owner="meeting"), `begin()` returns False here.
        try:
            accepted = self.voice_session.begin(self.recorder, owner="hotkey")
        except Exception as exc:
            with self.state_lock:
                self.runtime_status["last_error"] = f"Recording failed: {exc}"
            self._set_voice_state(
                "idle",
                source="hotkey",
                detail="Recording failed.",
                last_event="dictation_recording_failed",
                last_error=f"{type(exc).__name__}: {exc}",
            )
            log.error(f"Recording failed in web mode: {exc}")
            return
        if not accepted:
            log.info("hotkey_press_ignored_session_active")
            self._set_runtime_activity(
                "complete",
                source="hotkey",
                label="Busy",
                detail="Another HoldSpeak audio session is active.",
                last_event="dictation_recording_busy",
                last_error="",
            )
            return
        # HS-131-09: ONE `dictation.session` per accepted press, admitted here —
        # off the release-to-landed hot path. A refusal (or a release that won the
        # race) tears the capture down instead of recording unadmitted audio.
        if self._admit_hold_session(token) is None:
            try:
                self.voice_session.end(owner="hotkey")
            except Exception as exc:
                log.warning("hold teardown after refusal failed: %s", type(exc).__name__)
            self._set_voice_state("idle", source="hotkey", update_activity=False)
            return
        self._set_voice_state(
            "recording",
            source="hotkey",
            detail="HoldSpeak is listening.",
            last_event="dictation_recording_started",
            last_error="",
        )

    def _on_hotkey_release(self) -> None:
        # Sol Amendment 1: retiring the generation FIRST is what lets a release
        # beat an in-flight admission — that admission then cancels its own
        # parent and this release discards the audio.
        generation, lock = self._hold_state()
        with lock:
            generation.retire()
            session = self._hold_session
            self._hold_session = None
        # No meeting check: `end("hotkey")` returns None when the hotkey
        # doesn't own the floor (e.g. a meeting holds it), so this is a no-op.
        try:
            audio = self.voice_session.end(owner="hotkey")
        except Exception as exc:
            with self.state_lock:
                self.runtime_status["last_error"] = f"Recording error: {exc}"
            self._set_voice_state(
                "idle",
                source="hotkey",
                detail="Recording stop failed.",
                last_event="dictation_recording_stop_failed",
                last_error=f"{type(exc).__name__}: {exc}",
            )
            log.error(f"Recording error in web mode: {exc}")
            if session is not None:
                session.cancel_and_close()
            return
        if audio is None:
            if session is not None:
                session.cancel_and_close()
            self._set_voice_state("idle", source="hotkey", last_event="dictation_recording_ignored")
            return
        if session is None:
            # The press never produced a live parent (refused, or this release won
            # the acquisition race). Unadmitted audio is DISCARDED — no
            # transcription child may exist for it.
            log.info("hold release discarded audio: no admitted dictation session")
            self._set_voice_state("idle", source="hotkey", last_event="dictation_recording_ignored")
            return
        # Sol Amendment 2: seal the admitted ceiling to the now-known real end.
        # This one parent-state transition is ON the release-to-landed hot path
        # and is counted in the A/B accounting.
        try:
            session.seal(time.time() + _HOLD_DRAIN_SECONDS)
        except Exception as exc:
            log.error("hold deadline seal failed: %s", type(exc).__name__)
            session.cancel_and_close()
            self._set_voice_state("idle", source="hotkey", last_event="dictation_recording_ignored")
            return

        self._kick_off_transcribe(audio, source="hotkey", session=session)
