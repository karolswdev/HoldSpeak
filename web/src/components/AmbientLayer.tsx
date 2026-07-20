import { useEffect, useMemo, useState } from "react";
import { apiFetch, readableError, type JsonRecord } from "../lib/api";
import { useRuntimeBus, useRuntimeFrame } from "../runtime/RuntimeBus";
import { useProjections } from "../desk/projections";
import { humanizeWireValue } from "../lib/productLanguage";
import { Button, InlineMessage, StatusPill } from "./signal/Signal";

type Preview = { token?: string; text?: string; kind?: "wake" | "preview" };

function PreviewCard() {
  const wake = useRuntimeFrame<Preview>("wake_preview");
  const hold = useRuntimeFrame<Preview>("dictation_preview");
  const [hiddenToken, setHiddenToken] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const preview = hold?.token
    ? { ...hold, kind: "preview" as const }
    : wake?.token
      ? { ...wake, kind: "wake" as const }
      : null;
  if (!preview?.token || preview.token === hiddenToken) return null;
  const act = async (choice: "type" | "discard") => {
    if (preview.kind === "wake" && choice === "discard") {
      setHiddenToken(preview.token ?? "");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const path =
        preview.kind === "wake"
          ? "/api/dictation/wake/type"
          : choice === "type"
            ? "/api/dictation/preview/type"
            : "/api/dictation/preview/discard";
      await apiFetch(path, {
        method: "POST",
        json: { token: preview.token },
      });
      setHiddenToken(preview.token ?? "");
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setBusy(false);
    }
  };
  return (
    <aside className="ambient-preview" aria-label="Dictation preview">
      <span className="signal-eyebrow">Preview before type</span>
      <p>{preview.text ?? "Your dictation is ready."}</p>
      {error ? <InlineMessage tone="error">{error}</InlineMessage> : null}
      <div className="button-row">
        <Button
          dense
          variant="primary"
          loading={busy}
          onClick={() => void act("type")}
        >
          Type it
        </Button>
        <Button dense variant="ghost" onClick={() => void act("discard")}>
          Discard
        </Button>
      </div>
    </aside>
  );
}

function QueueHud() {
  const summaryFrame = useRuntimeFrame<JsonRecord>("plugin_jobs");
  const jobFrame = useRuntimeFrame<JsonRecord>("plugin_job");
  const [open, setOpen] = useState(false);
  const summary = summaryFrame ?? jobFrame;
  if (!summary) return null;
  const pending = Number(summary.pending ?? summary.queued ?? 0);
  const failed = Number(summary.failed ?? 0);
  const running = Number(summary.running ?? 0);
  if (!pending && !failed && !running) return null;
  return (
    <aside className="ambient-queue">
      <Button
        dense
        variant="ghost"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <StatusPill tone={failed ? "error" : running ? "live" : "warning"}>
          {running
            ? `${running} running`
            : failed
              ? `${failed} failed`
              : `${pending} queued`}
        </StatusPill>
      </Button>
      {open ? (
        <div>
          <strong>Delivery queue</strong>
          <p>
            {pending} pending · {running} running · {failed} failed
          </p>
          <a href="/history">Open queue</a>
        </div>
      ) : null}
    </aside>
  );
}

function Qlippy() {
  const { subscribe } = useRuntimeBus();
  const projections = useProjections((state) => state.ambient);
  const [enabled, setEnabled] = useState(false);
  const [cards, setCards] = useState<Array<JsonRecord & { frameType: string }>>(
    [],
  );
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let current = true;
    void apiFetch<JsonRecord>("/api/settings")
      .then((settings) => {
        const presence = settings.presence;
        if (!current || !presence || typeof presence !== "object") return;
        const gate = presence as JsonRecord;
        setEnabled(gate.enabled === true && gate.mascot === true);
      })
      .catch(() => {
        if (current) setEnabled(false);
      });
    return () => {
      current = false;
    };
  }, []);
  useEffect(
    () =>
      subscribe("*", (frame) => {
        if (
          !["actuator_proposed", "aftercare_ready", "learning_event"].includes(
            frame.type,
          ) ||
          !frame.data ||
          typeof frame.data !== "object"
        )
          return;
        // Runtime frames are only wake-up hints. Qlippy's actionable wording
        // comes from the same durable projection used by the Desk and HUD.
        if (frame.type !== "learning_event") {
          void useProjections.getState().refreshAmbient();
          return;
        }
        setCards((current) =>
          [
            ...current.filter(
              (card) => card.id !== (frame.data as JsonRecord).id,
            ),
            { ...(frame.data as JsonRecord), frameType: frame.type },
          ].slice(-4),
        );
      }),
    [subscribe],
  );
  useEffect(() => {
    if (enabled) void useProjections.getState().refreshAmbient();
  }, [enabled]);
  const projection = projections.find(
    (row) =>
      row.attention_state === "needs_attention" ||
      row.attention_state === "unseen",
  );
  const card = cards[0];
  if (!enabled || (!projection && !card)) return null;
  const dismiss = () => setCards((current) => current.slice(1));
  const decide = async (decision: "approved" | "rejected") => {
    if (!card?.meeting_id || !card.id) return dismiss();
    setBusy(true);
    try {
      await apiFetch(
        `/api/meetings/${encodeURIComponent(String(card.meeting_id))}/proposals/${encodeURIComponent(String(card.id))}/decision`,
        { method: "POST", json: { decision } },
      );
      dismiss();
    } finally {
      setBusy(false);
    }
  };
  return (
    <aside className="ambient-qlippy" aria-label="Qlippy">
      <div className="qlippy-face" aria-hidden="true">
        ◉
      </div>
      <div>
        <span className="signal-eyebrow">
          {projection
            ? `${humanizeWireValue(String(projection.projection_kind))} · ${humanizeWireValue(String(projection.subject_label))}`
            : card!.frameType.replace(/_/g, " ")}
        </span>
        <strong>
          {projection?.title ??
            String(
              card?.title ??
                card?.label ??
                (card?.frameType === "learning_event"
                  ? "HoldSpeak learned"
                  : "Something is ready"),
            )}
        </strong>
        <p>
          {projection?.summary ??
            String(
              card?.preview ??
                card?.detail ??
                card?.body ??
                "Review this moment when you are ready.",
            )}
        </p>
        <div className="button-row">
          {projection ? (
            <Button
              dense
              variant="primary"
              onClick={() => {
                window.location.href = projection.detail_url;
              }}
            >
              Review source
            </Button>
          ) : card!.frameType === "actuator_proposed" ? (
            <>
              <Button
                dense
                variant="primary"
                loading={busy}
                onClick={() => void decide("approved")}
              >
                Approve
              </Button>
              <Button
                dense
                variant="ghost"
                onClick={() => void decide("rejected")}
              >
                Decline
              </Button>
            </>
          ) : null}
          <Button
            dense
            variant="ghost"
            onClick={() =>
              projection
                ? void useProjections
                    .getState()
                    .present(projection.id, "dismiss")
                : dismiss()
            }
          >
            Dismiss
          </Button>
        </div>
      </div>
    </aside>
  );
}

function Waveform() {
  const level = useRuntimeFrame<number | { level?: number }>("audio_level");
  const value = typeof level === "number" ? level : Number(level?.level ?? 0);
  if (!value) return null;
  return (
    <div className="ambient-waveform" aria-label="Microphone active">
      {Array.from({ length: 9 }, (_, index) => (
        <span
          key={index}
          style={{
            height: `${Math.max(4, Math.min(42, value * 38 * (1 - Math.abs(4 - index) * 0.1)))}px`,
          }}
        />
      ))}
    </div>
  );
}

function GenerationTheater() {
  const status = useRuntimeFrame<JsonRecord>("intel_status");
  const active = useMemo(
    () =>
      ["running", "streaming", "analyzing"].includes(
        String(status?.state ?? status?.status ?? ""),
      ),
    [status],
  );
  if (!active) return null;
  return (
    <div className="ambient-theater" role="status">
      <span aria-hidden="true">✦</span>
      <strong>{String(status?.label ?? "Analyzing meeting")}</strong>
      <small>
        {String(status?.detail ?? "Transcript analysis is running.")}
      </small>
    </div>
  );
}

export function AmbientLayer() {
  return (
    <>
      <QueueHud />
      <PreviewCard />
      <Qlippy />
      <Waveform />
      <GenerationTheater />
    </>
  );
}
