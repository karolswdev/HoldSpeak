"""The wake-word runtime glue (HS-63-03, originally HS-60).

Listener lifecycle, the armed-capture handoff, the preview/type fork, and
the one-shot token store — verbatim moves out of WebRuntime.
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, Optional

import numpy as np

from ..logging_config import get_logger
from ..speech_session import SpeechSessionRefused, fatal_speech_signal

log = get_logger("web_runtime")

# HS-32-03: the owner string a meeting uses to hold the shared
# ``VoiceTypingSession`` audio floor. One arbiter for hotkey / device /
# meeting capture; while a meeting holds this, hotkey/device ``begin()``
# is rejected, and a meeting can't start while either holds the floor.
_MEETING_AUDIO_OWNER = "meeting"



log = get_logger("web_runtime")


class WakeWordGlueMixin:
    # HS-131-09: the ONE thread-safe slot the in-flight wake session is
    # registered in. Stopping the listener is an authority revocation, so it must
    # be able to REACH the capture that is already running: without a carrier, a
    # `wake.session` admitted a moment before the stop kept its parent live, kept
    # dispatching children, and could still issue a preview or type.
    _wake_session: Any = None
    _wake_session_lock: Any = None
    # Sol round 2: admission is not instantaneous, so the slot alone leaves a
    # window — a stop landing between `admit` and `register` sees an EMPTY slot
    # and the newly admitted session survives it. The same monotonic generation
    # rule the desktop hold and the browser open use closes it: the token is taken
    # BEFORE admitting, a stop retires it, and the loser cancels its own parent.
    _wake_generation: Any = None

    def _wake_session_slot(self) -> Any:
        if self._wake_session_lock is None:
            self._wake_session_lock = threading.Lock()
        return self._wake_session_lock

    def _wake_stop_generation(self) -> Any:
        if self._wake_generation is None:
            from ..speech_session import SessionGeneration

            self._wake_generation = SessionGeneration()
        return self._wake_generation

    def _register_wake_session(self, session: Any, token: int) -> bool:
        """Publish this session ATOMICALLY with the token re-check.

        Returns False when a stop won the race: the caller cancels the parent it
        just admitted and discards the audio. Both the token check and the slot
        write happen under the slot lock, so a stop can never land "between" them.
        """
        with self._wake_session_slot():
            if not self._wake_stop_generation().is_live(token):
                return False
            self._wake_session = session
            return True

    def _release_wake_session(self, session: Any) -> None:
        """Clear the slot only if it still holds THIS session."""
        with self._wake_session_slot():
            if self._wake_session is session:
                self._wake_session = None

    def _cancel_wake_session(self) -> str:
        """Retire the generation and cancel whatever capture is in flight.

        Retiring under the SAME lock the registration re-checks is what makes an
        admission that is still in flight lose: it finds its token stale and
        cancels itself, so a stop is never silently outlived by a session admitted
        a microsecond earlier.
        """
        with self._wake_session_slot():
            self._wake_stop_generation().retire()
            session, self._wake_session = self._wake_session, None
        if session is None:
            return ""
        try:
            outcome = str(session.cancel_and_close())
        except Exception as exc:
            log.error("wake session cancel failed: %s", type(exc).__name__)
            return ""
        log.info("wake session cancelled by listener stop")
        return outcome

    # ── HS-60: the wake word ────────────────────────────────────────────

    def _sync_wake_word(self) -> None:
        """Start/stop the wake listener to match config (live via settings)."""
        want = bool(getattr(getattr(self.config, "wake_word", None), "enabled", False))
        have = self._wake_listener is not None
        if want and not have:
            self._start_wake_listener()
        elif not want and have:
            self._stop_wake_listener()

    def _start_wake_listener(self) -> None:
        from ..wake_word import (
            FRAME_SAMPLES,
            SAMPLE_RATE as WAKE_RATE,
            OpenWakeWordDetector,
            WakeWordListener,
            wake_word_available,
        )

        if not wake_word_available():
            log.warning(
                "Wake word is enabled but the engine is not installed; "
                "install it with: pip install 'holdspeak[wakeword]'"
            )
            return
        cfg = self.config.wake_word
        try:
            detector = OpenWakeWordDetector(cfg.model)
        except Exception:
            # First enable: fetch the models — the feature's ONE network
            # moment (~7 MB from the openWakeWord GitHub releases), stated in
            # the settings copy and the docs.
            try:
                from ..wake_word import download_wake_models

                log.info(
                    f"Downloading the wake models for {cfg.model!r} "
                    "(one-time, from the openWakeWord GitHub releases)…"
                )
                download_wake_models(cfg.model)
                detector = OpenWakeWordDetector(cfg.model)
            except Exception as exc:
                log.warning(f"Wake model {cfg.model!r} unavailable: {exc}")
                return
        import queue as queue_mod

        try:
            import sounddevice as sd
        except Exception as exc:  # pragma: no cover - portaudio missing
            log.warning(f"Wake word needs sounddevice: {exc}")
            return

        wake_queue: Any = queue_mod.Queue(maxsize=64)

        def _cb(indata, _frames, _time, _status) -> None:
            try:
                wake_queue.put_nowait(indata[:, 0].copy())
            except queue_mod.Full:  # drop, never block the audio thread
                pass

        try:
            stream = sd.InputStream(
                samplerate=WAKE_RATE,
                channels=1,
                dtype="int16",
                blocksize=FRAME_SAMPLES,
                callback=_cb,
            )
            stream.start()
        except Exception as exc:
            log.warning(f"Wake word could not open the microphone: {exc}")
            return
        self._wake_queue = wake_queue
        self._wake_stream = stream

        def _frames():
            # Self-healing floor respect: while ANY owner holds the audio
            # floor (hotkey, device, meeting, or a wake capture), the
            # listener pauses (frames drain unscored); it resumes when free.
            listener = self._wake_listener
            if listener is not None:
                if self.voice_session.active_owner is not None:
                    listener.pause()
                else:
                    listener.resume()
            try:
                return wake_queue.get(timeout=0.5)
            except queue_mod.Empty:
                # Keep the loop alive through quiet stream hiccups.
                return np.zeros(FRAME_SAMPLES, dtype=np.int16)

        self._wake_listener = WakeWordListener(
            detector=detector,
            frames=_frames,
            on_detect=self._on_wake_detect,
            threshold=cfg.threshold,
        )
        self._wake_listener.start()
        log.info(f"Wake word active: {cfg.model!r} (threshold {cfg.threshold})")

    def _stop_wake_listener(self) -> None:
        # The in-flight capture goes FIRST: its fence must be flipped before the
        # stream closes, so a transcription already inside the model cannot come
        # back and reach preview issuance or typing.
        self._cancel_wake_session()
        listener, self._wake_listener = self._wake_listener, None
        if listener is not None:
            try:
                listener.stop()
            except Exception:
                pass
        stream, self._wake_stream = self._wake_stream, None
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass
        self._wake_queue = None

    def _on_wake_detect(self, score: float) -> None:
        """A detection: acquire the floor, arm visibly, capture, hand off.

        Runs on the listener thread; the frame queue keeps filling from the
        stream callback, so the capture reads the same source.
        """
        from ..wake_word import ArmedCapture

        cfg = self.config.wake_word
        if not self.voice_session.acquire("wake"):
            return  # someone holds the floor; never contend
        audio = None
        try:
            self._set_runtime_activity(
                "armed",
                source="wake",
                label="Armed",
                detail=f"Say your sentence ({int(cfg.armed_window_seconds)} s window).",
                last_event="wake_armed",
                last_error="",
            )
            try:
                self.server.broadcast(
                    "wake_armed",
                    {"window_seconds": cfg.armed_window_seconds, "score": round(float(score), 3)},
                )
            except Exception:
                pass
            capture = ArmedCapture(window_seconds=cfg.armed_window_seconds)
            # A hard iteration cap so a dead stream can never wedge the floor.
            max_iterations = int((cfg.armed_window_seconds + 20.0) / 0.08)
            queue_ref = self._wake_queue
            for _ in range(max_iterations):
                if capture.state in ("captured", "expired"):
                    break
                if self.runtime_stop_event.is_set() or queue_ref is None:
                    break
                try:
                    frame = queue_ref.get(timeout=1.0)
                except Exception:
                    continue
                capture.feed(frame)
            audio = capture.result()
        finally:
            self.voice_session.release("wake")
        if audio is None or len(audio) < 1600:
            self._set_runtime_activity(
                "complete",
                source="wake",
                label="Disarmed",
                detail="Nothing was spoken.",
                last_event="wake_disarmed",
                last_error="",
            )
            return
        self._transcribe_wake(audio)

    def _transcribe_wake(self, audio: np.ndarray) -> None:
        """The wake outcome: the NORMAL pipeline, then preview or (opt-in) type.

        `action="preview"` (the default) journals the run (source `wake`),
        stores a one-shot preview token, and broadcasts `wake_preview` —
        it NEVER types. `action="type"` is the user's explicit opt-in and
        behaves like a hotkey run's tail.

        HS-131-09: the capture that reached here is ONE bounded `wake.session`
        under the narrow `wake-capture` SERVICE identity, whose authority basis is
        derived from the owner's persisted wake configuration. Its transcription
        is a child of that parent; any resulting typing keeps its own separate
        effect admission.
        """
        cfg = self.config.wake_word
        # The token is taken BEFORE admission (Sol round 2): a stop from here on
        # retires it, and this capture then cancels itself instead of surviving.
        token = self._wake_stop_generation().begin()
        session = self._admit_wake_session(cfg)
        if session is None:
            return
        if not self._register_wake_session(session, token):
            # The stop won. The freshly admitted parent is cancelled, the audio is
            # discarded, and no Whisper child ever exists for it.
            log.info("wake session cancelled: a listener stop won the acquisition race")
            session.cancel_and_close()
            self._set_runtime_activity(
                "complete",
                source="wake",
                label="Stopped",
                detail="The wake listener stopped before this capture ran.",
                last_event="wake_session_stopped",
                last_error="",
            )
            return
        outcome = "succeeded"
        try:
            outcome = self._transcribe_wake_admitted(audio, cfg, session) or "succeeded"
        except SpeechSessionRefused:
            outcome = "refused"
            raise
        except BaseException:
            outcome = "failed"
            raise
        finally:
            self._release_wake_session(session)
            # The parent's outcome is the SESSION's, not a child's: a failed
            # transcription already has its own honest child receipt — and a
            # session whose tail raised closes FAILED, never succeeded.
            session.close(outcome)

    def _admit_wake_session(self, cfg: Any) -> Any:
        """Admit ONE bounded `wake.session`, or refuse by name (no OWNER synthesis)."""
        from ..speech_session import SpeechSessionRefused, admit_wake_session

        try:
            return admit_wake_session(wake_config=cfg, config_snapshot=self.config)
        except SpeechSessionRefused as exc:
            log.error("wake session refused: %s", exc.reason)
            self._set_runtime_activity(
                "error",
                source="wake",
                label="Not admitted",
                detail="The wake capture was not admitted.",
                last_event="wake_session_refused",
                last_error=exc.reason,
            )
            return None
        except Exception as exc:
            log.error("wake session admission failed: %s", type(exc).__name__)
            return None

    def _transcribe_wake_admitted(
        self, audio: np.ndarray, cfg: Any, session: Any
    ) -> Optional[str]:
        # HS-131-09 (Sol OQ5): this frame owns its own handles for its whole life
        # — the transcription admission, the provider admission every pipeline
        # model call runs under, and the immutable fence that discards late text.
        admission = session.transcription()
        provider = session.provider()
        fence = session.fence
        with self.transcription_lock:
            try:
                self._set_runtime_activity(
                    "transcribing",
                    source="wake",
                    detail="Turning your speech into text…",
                    last_event="wake_transcribing",
                    last_error="",
                )
                text = self._ensure_transcriber_loaded().transcribe(audio, admission=admission)
                if not text:
                    self._set_runtime_activity(
                        "complete",
                        source="wake",
                        label="No speech",
                        detail="No speech detected.",
                        last_event="wake_no_speech",
                        last_error="",
                    )
                    return
                if fence.discarded("wake text processing"):
                    return
                text = self.text_processor.process(text)
                final = self._maybe_run_dictation_pipeline(
                    text,
                    audio_duration_s=len(audio) / 16000.0,
                    transcribed_at=datetime.now(),
                    journal_source="wake",
                    admission=provider,
                )
                if not final:
                    # Nothing survived, or the session was fenced mid-run: no
                    # preview is issued and nothing is typed.
                    return
                if cfg.action == "type":
                    def _deliver() -> None:
                        self._set_runtime_activity(
                            "typing",
                            source="wake",
                            detail="Typing into the active app.",
                            last_event="wake_typing",
                            last_error="",
                        )
                        # Delivery keeps its OWN separate effect admission past this
                        # speech election; nothing here duplicates that receipt.
                        from ..desktop_typing import type_text_from_owner_gesture

                        type_text_from_owner_gesture(
                            final,
                            typer=self.typer,
                            gesture="wake_utterance",
                            submit=False,
                            requested_target="focused",
                            delivery_method="wake_type",
                        )
                        self._set_runtime_activity(
                            "complete",
                            source="wake",
                            label="Typed",
                            detail=final[:120],
                            last_event="wake_typed",
                            last_error="",
                        )
                        session.close("succeeded")

                    delivered, _value = fence.publish("wake delivery handoff", _deliver)
                    if not delivered:
                        return
                    return

                def _publish_preview() -> None:
                    # The preview default: one active preview at a time.
                    import uuid as uuid_mod

                    token = uuid_mod.uuid4().hex
                    self.wake_previews.clear()
                    self.wake_previews[token] = {
                        "text": final,
                        "transcript": text,
                        "created_at": datetime.now().isoformat(),
                    }
                    try:
                        self.server.broadcast(
                            "wake_preview",
                            {"token": token, "transcript": text, "text": final},
                        )
                    except Exception:
                        pass
                    self._set_runtime_activity(
                        "complete",
                        source="wake",
                        label="Preview ready",
                        detail=final[:120],
                        last_event="wake_preview",
                        last_error="",
                    )
                    session.close("succeeded")

                published, _value = fence.publish(
                    "wake preview publication", _publish_preview
                )
                if not published:
                    return
            except Exception as exc:
                if fatal_speech_signal(exc):
                    raise
                self._set_runtime_activity(
                    "error",
                    source="wake",
                    detail="Wake transcription failed.",
                    last_event="wake_failed",
                    last_error=f"{type(exc).__name__}: {exc}",
                )
                # The swallow stays (a wake failure is not a crash), but the
                # SESSION's outcome is now honest.
                return "failed"
        return None

    def consume_wake_preview(self, token: str) -> Optional[str]:
        """One-shot: return the stored preview text and burn the token."""
        entry = self.wake_previews.pop(str(token or ""), None)
        return None if entry is None else str(entry.get("text", ""))

    def _type_wake_preview(self, token: str) -> Optional[str]:
        """The Type-it route's handler: burn the token, type the stored text."""
        text = self.consume_wake_preview(token)
        if text is None:
            return None
        try:
            from ..desktop_typing import type_text_from_owner_gesture

            type_text_from_owner_gesture(
                text,
                typer=self.typer,
                gesture="wake_preview_type",
                preview_ref=f"wake-preview:{token}",
                submit=False,
                requested_target="focused",
                delivery_method="wake_preview",
            )
        except Exception as exc:
            self._set_runtime_activity(
                "error",
                source="wake",
                detail="Typing the wake preview failed.",
                last_event="wake_type_failed",
                last_error=f"{type(exc).__name__}: {exc}",
            )
            return None
        self._set_runtime_activity(
            "complete",
            source="wake",
            label="Typed",
            detail=text[:120],
            last_event="wake_preview_typed",
            last_error="",
        )
        return text
