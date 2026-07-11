import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Button, InlineMessage, TextArea } from "../../components/signal/Signal";
import { ApiError, apiFetch, readableError } from "../../lib/api";
import {
  cancelCapture,
  speakToFillSupported,
  startCapture,
  stopAndTranscribe,
} from "../../lib/speakToFill";

type CaptureState = "idle" | "listening" | "transcribing" | "success" | "failed";
type FailureCategory =
  | "permission_denied"
  | "missing_model"
  | "rejected_token"
  | "unreachable_hub"
  | "delivery_conflict"
  | "transcription_failed"
  | "no_speech"
  | "unknown";

function failureCategory(error: unknown): FailureCategory {
  if (error instanceof DOMException && error.name === "NotAllowedError")
    return "permission_denied";
  if (error instanceof ApiError) {
    if (error.status === 401 || error.status === 403) return "rejected_token";
    if (error.status === 409) return "delivery_conflict";
    if (error.status === 503) return "missing_model";
    return "transcription_failed";
  }
  if (error instanceof TypeError) return "unreachable_hub";
  return "unknown";
}

const FAILURE_COPY: Record<FailureCategory, string> = {
  permission_denied: "Microphone access is off. Your text is still here.",
  missing_model: "Local transcription is not ready. Your text is still here.",
  rejected_token: "This hub rejected the connection. Your text is still here.",
  unreachable_hub: "The hub could not be reached. Your text is still here.",
  delivery_conflict: "That delivery conflicted with another request. Your text is still here.",
  transcription_failed: "Transcription did not finish. Your text is still here.",
  no_speech: "No words were detected. Type below or hold to try again.",
  unknown: "That did not finish. Your text is still here.",
};

export function FirstWords({ onDismiss }: { onDismiss?: () => void }) {
  const [text, setText] = useState("");
  const [state, setState] = useState<CaptureState>("idle");
  const [failure, setFailure] = useState<FailureCategory | null>(null);
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const attempt = useRef("");
  const listening = useRef(false);
  const holding = useRef(false);

  const startAttempt = async () => {
    const result = await apiFetch<{ attempt?: { id?: string } }>(
      "/api/setup/first-value/start",
      { method: "POST", json: { destination: "this_machine" } },
    );
    attempt.current = String(result.attempt?.id ?? "");
  };

  const finishAttempt = async (
    outcome: "success" | "failure",
    category?: FailureCategory,
  ) => {
    if (!attempt.current) return;
    const id = attempt.current;
    attempt.current = "";
    await apiFetch(`/api/setup/first-value/${encodeURIComponent(id)}/finish`, {
      method: "POST",
      json: {
        outcome,
        steps: 1,
        decisions: 0,
        destination: "this_machine",
        ...(category ? { failure_category: category } : {}),
      },
    });
  };

  const fail = (category: FailureCategory) => {
    setFailure(category);
    setState("failed");
    void finishAttempt("failure", category).catch(() => undefined);
  };

  const begin = async () => {
    if (listening.current || state === "transcribing") return;
    holding.current = true;
    setFailure(null);
    setMessage("");
    try {
      await startAttempt();
      await startCapture();
      if (!holding.current) {
        await cancelCapture();
        fail("unknown");
        return;
      }
      listening.current = true;
      setState("listening");
    } catch (error) {
      fail(failureCategory(error));
    }
  };

  const stop = async () => {
    holding.current = false;
    if (!listening.current) return;
    listening.current = false;
    setState("transcribing");
    try {
      const result = (await stopAndTranscribe()).trim();
      if (!result) {
        fail("no_speech");
        return;
      }
      setText(result);
      setState("success");
      setFailure(null);
      await finishAttempt("success").catch(() => undefined);
    } catch (error) {
      fail(failureCategory(error));
    }
  };

  const dismiss = async (disposition: "dismissed" | "needs_help") => {
    setSaving(true);
    try {
      await apiFetch("/api/setup/onboarding", {
        method: "PUT",
        json: { disposition },
      });
      onDismiss?.();
    } catch (error) {
      setMessage(readableError(error));
    } finally {
      setSaving(false);
    }
  };

  const keep = async () => {
    if (!text.trim()) return;
    setSaving(true);
    try {
      await apiFetch("/api/notes", {
        method: "POST",
        json: {
          title: "First dictation",
          body_markdown: text,
          tags: ["dictation"],
        },
      });
      setMessage("Kept as a note on your Desk.");
    } catch (error) {
      setMessage(readableError(error));
    } finally {
      setSaving(false);
    }
  };

  const supported = speakToFillSupported();
  return (
    <section className="desk-first-words" aria-labelledby="first-words-title">
      <span className="signal-eyebrow">Your first words</span>
      <h1 id="first-words-title">Say one sentence</h1>
      <p>Hold to speak. Your words stay editable here before you use them.</p>
      <button
        type="button"
        className={`desk-first-talk is-${state}`}
        disabled={!supported || state === "transcribing"}
        aria-label={state === "failed" ? "Hold to retry dictation" : "Hold to dictate"}
        onPointerDown={(event) => {
          event.preventDefault();
          void begin();
        }}
        onPointerUp={() => void stop()}
        onPointerLeave={() => {
          if (holding.current) void stop();
        }}
        onKeyDown={(event) => {
          if ((event.key === " " || event.key === "Enter") && !event.repeat) {
            event.preventDefault();
            void begin();
          }
        }}
        onKeyUp={(event) => {
          if (event.key === " " || event.key === "Enter") {
            event.preventDefault();
            void stop();
          }
        }}
      >
        {state === "listening"
          ? "Listening… release when done"
          : state === "transcribing"
            ? "Writing your words…"
            : state === "failed"
              ? "Hold to retry"
              : "Hold to speak"}
      </button>
      {!supported ? (
        <InlineMessage tone="error">
          Browser microphone capture is unavailable. You can type below or open Setup.
        </InlineMessage>
      ) : null}
      {failure ? (
        <InlineMessage tone="error">{FAILURE_COPY[failure]}</InlineMessage>
      ) : null}
      <TextArea
        aria-label="Your dictated text"
        rows={4}
        value={text}
        onChange={(event) => setText(event.target.value)}
        placeholder="Your words will appear here—or type them now."
      />
      {message ? <InlineMessage tone="info">{message}</InlineMessage> : null}
      <div className="button-row">
        <Button
          disabled={!text.trim()}
          onClick={() => void navigator.clipboard.writeText(text)}
        >
          Copy
        </Button>
        <Button disabled={!text.trim()} loading={saving} onClick={() => void keep()}>
          Keep as Note
        </Button>
        <Link className="btn btn--secondary" to="/setup">
          Setup
        </Link>
      </div>
      {state === "success" ? (
        <div className="desk-first-success">
          <strong>It worked on this machine.</strong>
          <Link className="btn btn--ghost" to="/profiles">
            Add an intelligent rewrite · choose Runs on
          </Link>
        </div>
      ) : null}
      <div className="button-row">
        <Button variant="ghost" loading={saving} onClick={() => void dismiss("dismissed")}>
          Continue later
        </Button>
        {failure ? (
          <Button variant="ghost" loading={saving} onClick={() => void dismiss("needs_help")}>
            I need help
          </Button>
        ) : null}
      </div>
    </section>
  );
}
