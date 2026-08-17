import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
// HS-95-07 — the Cadence core: loops and history, hosted anywhere.
// HS-98-01 — re-crafted as the reference NATIVE surface: composed from
// the surface kit on the window material (DESIGN_SYSTEM.md, "The
// surface idiom"), no page grammar.
import { useState } from "react";
import type {
  CoreProps,
  CadenceStatusResponse,
  CadenceLoopsResponse,
  CadenceHistoryResponse,
} from "./core-types";
import { Button } from "../../components/signal/Signal";
import { LampGadget, PadGadget } from "../../desk/surface/gadgets";
import { apiFetch } from "../../lib/api";
import { asRows, rowId, useResource } from "../pageSupport";
import {
  ConfirmVerb,
  SurfaceColumns,
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceState,
} from "../../desk/surface/Surface";
import { useAction } from "./core-hooks";
import { CoreResourceGuard, renderHeroSlot } from "./core-layout";
import { deSnake, humanTime, presentValue } from "../../desk/surface/format";
import { SYSTEM } from "../../desk/systemSprites";

export function CadenceCore({ hero }: CoreProps) {
  const status = useResource<CadenceStatusResponse>("/api/cadence/status", {});
  const loopsResource = useResource<CadenceLoopsResponse>("/api/cadence/loops", {});
  const history = useResource<CadenceHistoryResponse>("/api/cadence/history?limit=20", {});
  const loops = asRows(loopsResource.data, ["loops"]);
  const nudges = asRows(history.data, ["nudges"]);
  const [replies, setReplies] = useState<Record<string, string>>({});
  const [replyReceipt, setReplyReceipt] = useState("");
  const action = useAction();
  const act = async (id: string, verb: string) => {
    await action.run(async () => {
      await apiFetch(`/api/cadence/loops/${encodeURIComponent(id)}/${verb}`, {
        method: "POST",
        json: verb === "snooze" ? { hours: 24 } : {},
      });
      await loopsResource.reload();
      await history.reload();
    });
  };
  // HS-132-11 — the answer goes to the waiting agent. A refusal rides the
  // existing local error channel (named by the route); the send leaves an
  // in-flow receipt, because the answered loop closes and leaves the list.
  const sendReply = async (id: string) => {
    const text = (replies[id] ?? "").trim();
    if (!text) return;
    setReplyReceipt("");
    await action.run(async () => {
      const result = await apiFetch<{ pane?: string }>(
        `/api/cadence/loops/${encodeURIComponent(id)}/reply`,
        { method: "POST", json: { text } },
      );
      setReplyReceipt(`Sent to ${result.pane || "the agent"}`);
      setReplies((prev) => ({ ...prev, [id]: "" }));
      await loopsResource.reload();
      await history.reload();
    });
  };
  const run = async () => {
    await action.run(async () => {
      await apiFetch("/api/cadence/run-now", { method: "POST", json: {} });
      await loopsResource.reload();
    });
  };
  const verbs = (
    <Button variant="primary" dense loading={action.busy} onClick={run}>
      Run now
    </Button>
  );
  return (
    <>
      {renderHeroSlot(
        hero,
        verbs,
        <>
          <img src={SYSTEM.cadenceMetronome} alt="" width={16} height={16} className="desk-chrome-sprite" style={{ verticalAlign: "middle", marginRight: 4, imageRendering: "pixelated" }} draggable={false} />
          {status.data.enabled ? "On" : "Off"}
          {presentValue(status.data.pressure)
            ? ` · ${presentValue(status.data.pressure)}`
            : ""}
        </>,
      )}
      {action.message ? <SurfaceState error={action.message} /> : null}
      {replyReceipt ? (
        <p className="surface-receipt-line" data-tone="ok" role="status">
          ✓ {replyReceipt}
        </p>
      ) : null}
      <SurfaceColumns
        main={
          <SurfaceSection label="Now">
            <CoreResourceGuard
              resource={loopsResource}
              empty={!loops.length}
              emptyLabel="No open loops"
              emptyImage={SYSTEM.emptyLoops}
              actionLabel="Run now"
              onAction={() => void run()}
            >
              <SurfaceRows>
                {loops.map((loop, index) => {
                  const id = rowId(loop, index);
                  const next = loop.next_action as Record<string, unknown> | undefined;
                  const score = Number(loop.stale_score ?? 0);
                  const isQuestion = loop.source_type === "agent_question";
                  return (
                    <SurfaceRow
                      key={id}
                      title={String(loop.title ?? "Open loop")}
                      detail={
                        <>
                          {loop.needs_review ? (
                            <LampGadget on tone="warn" label="review" />
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
                              onClick={() => void sendReply(id)}
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
                            busy={action.busy}
                            onConfirm={() => void act(id, "close")}
                          />
                          <ConfirmVerb
                            label="Kill loop"
                            confirmLabel="Kill?"
                            busy={action.busy}
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
                        <PadGadget
                          label={`Reply to ${String(loop.title)}`}
                          value={replies[id] ?? ""}
                          onChange={(next) =>
                            setReplies({ ...replies, [id]: next })
                          }
                        />
                      ) : null}
                    </SurfaceRow>
                  );
                })}
              </SurfaceRows>
            </CoreResourceGuard>
          </SurfaceSection>
        }
        side={
          <SurfaceSection label="Nudge history">
            <CoreResourceGuard
              resource={history}
              empty={!nudges.length}
              emptyLabel="No nudges yet"
              emptyImage={SYSTEM.emptyNudges}
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
            </CoreResourceGuard>
          </SurfaceSection>
        }
      />
      <SurfaceFooter />
    </>
  );
}
