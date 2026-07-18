// HS-95-07 — the Cadence core: loops and history, hosted anywhere.
import { useState } from "react";
import type { CoreProps } from "./ActivityCore";
import {
  Button,
  EmptyState,
  InlineMessage,
  Panel,
  StatusPill,
  TextArea,
} from "../../components/signal/Signal";
import { apiFetch, readableError, type JsonRecord } from "../../lib/api";
import {
  ConfirmAction,
  ResourceState,
  asRows,
  rowId,
  useResource,
} from "../pageSupport";

export function CadenceCore({ hero }: CoreProps) {
  const status = useResource<JsonRecord>("/api/cadence/status", {});
  const loopsResource = useResource<JsonRecord>("/api/cadence/loops", {});
  const history = useResource<JsonRecord>("/api/cadence/history?limit=20", {});
  const loops = asRows(loopsResource.data, ["loops"]);
  const [replies, setReplies] = useState<Record<string, string>>({});
  const [confirm, setConfirm] = useState<{
    id: string;
    action: "kill" | "close";
  } | null>(null);
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
      setConfirm(null);
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
          <Button variant="primary" loading={busy} onClick={run}>
            Run now
          </Button>
  );
  return (
    <>
      {hero ? hero(verbs) : <div className="desk-core-verbs">{verbs}</div>}
      {message ? <InlineMessage tone="error">{message}</InlineMessage> : null}
      <div className="page-grid">
        <Panel
          className="span-8"
          title="Now"
          eyebrow={`${status.data.enabled ? "On" : "Off"} · ${String(status.data.pressure ?? "steady")}`}
        >
          <ResourceState
            loading={loopsResource.loading}
            error={loopsResource.error}
            empty={!loops.length}
            onRetry={() => void loopsResource.reload()}
          >
            <ul className="data-list">
              {loops.map((loop, index) => {
                const id = rowId(loop, index);
                const next = loop.next_action as JsonRecord | undefined;
                return (
                  <li className="cadence-row" key={id}>
                    <header>
                      <div>
                        <StatusPill
                          tone={loop.needs_review ? "warning" : "live"}
                        >
                          {String(loop.source_type ?? "loop").replace(
                            /_/g,
                            " ",
                          )}
                        </StatusPill>
                        <h3>{String(loop.title ?? "Open loop")}</h3>
                      </div>
                      <strong className="cadence-score">
                        {Number(loop.stale_score ?? 0).toFixed(0)}
                      </strong>
                    </header>
                    {next ? (
                      <div className="cadence-next">
                        <span className="signal-eyebrow">
                          Prepared next move
                        </span>
                        <strong>{String(next.title ?? "Next action")}</strong>
                        <p>{String(next.body_markdown ?? "")}</p>
                      </div>
                    ) : null}
                    {loop.source_type === "agent_question" ? (
                      <TextArea
                        aria-label={`Reply to ${String(loop.title)}`}
                        value={replies[id] ?? ""}
                        onChange={(event) =>
                          setReplies({ ...replies, [id]: event.target.value })
                        }
                      />
                    ) : null}
                    <div className="button-row">
                      {loop.source_type === "agent_question" ? (
                        <Button
                          dense
                          disabled={!replies[id]?.trim()}
                          onClick={() => void act(id, "reply")}
                        >
                          Send reply
                        </Button>
                      ) : null}
                      <Button dense onClick={() => void act(id, "snooze")}>
                        Snooze 1 day
                      </Button>
                      <Button
                        dense
                        variant="ghost"
                        onClick={() => setConfirm({ id, action: "close" })}
                      >
                        Mark done
                      </Button>
                      <Button
                        dense
                        variant="ghost"
                        onClick={() => setConfirm({ id, action: "kill" })}
                      >
                        Kill loop
                      </Button>
                    </div>
                  </li>
                );
              })}
            </ul>
          </ResourceState>
        </Panel>
        <Panel className="span-4" title="Nudge history" eyebrow="Recent">
          <ul className="data-list">
            {asRows(history.data, ["nudges"]).map((row, index) => (
              <li className="data-row" key={rowId(row, index)}>
                <div>
                  <strong>{String(row.title ?? row.status ?? "Nudge")}</strong>
                  <small>{String(row.surface ?? row.created_at ?? "")}</small>
                </div>
              </li>
            ))}
          </ul>
          {!asRows(history.data, ["nudges"]).length ? (
            <EmptyState title="No nudges yet">
              Cadence history will appear after a run.
            </EmptyState>
          ) : null}
        </Panel>
      </div>
      <ConfirmAction
        open={Boolean(confirm)}
        title={
          confirm?.action === "kill"
            ? "Kill this loop?"
            : "Mark this loop done?"
        }
        detail={
          confirm?.action === "kill"
            ? "Cadence will stop resurfacing it."
            : "This closes the loop as completed."
        }
        busy={busy}
        onConfirm={() => confirm && void act(confirm.id, confirm.action)}
        onClose={() => setConfirm(null)}
      />
    </>
  );
}
