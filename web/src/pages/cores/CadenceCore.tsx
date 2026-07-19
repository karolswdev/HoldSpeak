// HS-95-07 — the Cadence core: loops and history, hosted anywhere.
// HS-98-01 — re-crafted as the reference NATIVE surface: composed from
// the surface kit on the window material (DESIGN_SYSTEM.md, "The
// surface idiom"), no page grammar.
import { useState } from "react";
import type { CoreProps } from "./ActivityCore";
import {
  Button,
  InlineMessage,
  StatusPill,
  TextArea,
} from "../../components/signal/Signal";
import { apiFetch, readableError, type JsonRecord } from "../../lib/api";
import { asRows, rowId, useResource } from "../pageSupport";
import {
  ConfirmVerb,
  SurfaceColumns,
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceState,
  SurfaceVerbs,
} from "../../desk/surface/Surface";
import { deSnake, humanTime, presentValue } from "../../desk/surface/format";
import { spriteUrl } from "../../desk/sprites";

export function CadenceCore({ hero }: CoreProps) {
  const status = useResource<JsonRecord>("/api/cadence/status", {});
  const loopsResource = useResource<JsonRecord>("/api/cadence/loops", {});
  const history = useResource<JsonRecord>("/api/cadence/history?limit=20", {});
  const loops = asRows(loopsResource.data, ["loops"]);
  const nudges = asRows(history.data, ["nudges"]);
  const [replies, setReplies] = useState<Record<string, string>>({});
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const act = async (id: string, action: string) => {
    setBusy(true);
    setMessage("");
    try {
      await apiFetch(`/api/cadence/loops/${encodeURIComponent(id)}/${action}`, {
        method: "POST",
        json:
          action === "snooze"
            ? { hours: 24 }
            : action === "reply"
              ? { text: replies[id] ?? "" }
              : {},
      });
      await loopsResource.reload();
      await history.reload();
    } catch (error) {
      setMessage(readableError(error));
    } finally {
      setBusy(false);
    }
  };
  const run = async () => {
    setBusy(true);
    try {
      await apiFetch("/api/cadence/run-now", { method: "POST", json: {} });
      await loopsResource.reload();
    } catch (error) {
      setMessage(readableError(error));
    } finally {
      setBusy(false);
    }
  };
  const verbs = (
    <Button variant="primary" dense loading={busy} onClick={run}>
      Run now
    </Button>
  );
  return (
    <>
      {hero ? (
        hero(verbs)
      ) : (
        <SurfaceVerbs
          status={
            <>
              {status.data.enabled ? "On" : "Off"}
              {presentValue(status.data.pressure)
                ? ` · ${presentValue(status.data.pressure)}`
                : ""}
            </>
          }
        >
          {verbs}
        </SurfaceVerbs>
      )}
      {message ? <InlineMessage tone="error">{message}</InlineMessage> : null}
      <SurfaceColumns
        main={
          <SurfaceSection label="Now">
            <SurfaceState
              loading={loopsResource.loading}
              error={loopsResource.error}
              empty={!loops.length}
              emptyLabel="No open loops"
              emptyImage={spriteUrl("note", "cadence-empty")}
              onRetry={() => void loopsResource.reload()}
            >
              <SurfaceRows>
                {loops.map((loop, index) => {
                  const id = rowId(loop, index);
                  const next = loop.next_action as JsonRecord | undefined;
                  const score = Number(loop.stale_score ?? 0);
                  const isQuestion = loop.source_type === "agent_question";
                  return (
                    <SurfaceRow
                      key={id}
                      title={String(loop.title ?? "Open loop")}
                      detail={
                        <>
                          {loop.needs_review ? (
                            <StatusPill tone="warning">review</StatusPill>
                          ) : null}{" "}
                          {deSnake(loop.source_type)}
                        </>
                      }
                      meta={score > 0 ? score.toFixed(0) : undefined}
                      verbs={
                        <>
                          {isQuestion ? (
                            <Button
                              dense
                              disabled={!replies[id]?.trim()}
                              onClick={() => void act(id, "reply")}
                            >
                              Send reply
                            </Button>
                          ) : null}
                          <Button
                            dense
                            variant="ghost"
                            onClick={() => void act(id, "snooze")}
                          >
                            Snooze 1 day
                          </Button>
                          <ConfirmVerb
                            label="Mark done"
                            confirmLabel="Done?"
                            busy={busy}
                            onConfirm={() => void act(id, "close")}
                          />
                          <ConfirmVerb
                            label="Kill loop"
                            confirmLabel="Kill?"
                            busy={busy}
                            onConfirm={() => void act(id, "kill")}
                          />
                        </>
                      }
                    >
                      {next ? (
                        <div className="surface-next-move">
                          <strong>{String(next.title ?? "Next action")}</strong>
                          <p>{String(next.body_markdown ?? "")}</p>
                        </div>
                      ) : null}
                      {isQuestion ? (
                        <TextArea
                          aria-label={`Reply to ${String(loop.title)}`}
                          value={replies[id] ?? ""}
                          onChange={(event) =>
                            setReplies({ ...replies, [id]: event.target.value })
                          }
                        />
                      ) : null}
                    </SurfaceRow>
                  );
                })}
              </SurfaceRows>
            </SurfaceState>
          </SurfaceSection>
        }
        side={
          <SurfaceSection label="Nudge history">
            <SurfaceState
              loading={history.loading}
              error={history.error}
              empty={!nudges.length}
              emptyLabel="No nudges yet"
              emptyImage={spriteUrl("note", "cadence-nudges")}
              onRetry={() => void history.reload()}
            >
              <SurfaceRows>
                {nudges.map((row, index) => (
                  <SurfaceRow
                    key={rowId(row, index)}
                    title={String(row.title ?? row.status ?? "Nudge")}
                    detail={presentValue(row.surface) || undefined}
                    meta={humanTime(row.created_at) || undefined}
                  />
                ))}
              </SurfaceRows>
            </SurfaceState>
          </SurfaceSection>
        }
      />
    </>
  );
}
