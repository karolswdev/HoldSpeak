/** HS-111-02 — the Journal is a machine ledger (audit para 3.2): one mono
 * line per dictation, columns time/transcript/dest/ms/taught, click a
 * row to open it in place (the cursor line). Day bands stay. */
import { useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch } from "../../../lib/api";
import { asRows, rowId, useResource } from "../../pageSupport";
import type {
  DictationJournalResponse,
  DictationJournalReplayResponse,
} from "../core-types";
import {
  isSameStreamDay,
  presentValue,
  streamDate,
  streamDayLabel,
  streamTime,
} from "../../../desk/surface/format";
import { countToken } from "../../../desk/surface";
import {
  ConfirmVerb,
  EditInPlace,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  SurfaceState,
  SurfaceStreamDay,
} from "../../../desk/surface/Surface";
import { StringGadget } from "../../../desk/surface/gadgets";

function JournalRow({
  row,
  index,
  openId,
  onToggle,
  replays,
  onReplay,
  onEditTranscript,
  onRemove,
}: {
  row: Record<string, unknown>;
  index: number;
  openId: string;
  onToggle: (id: string) => void;
  replays: Record<string, Record<string, unknown>>;
  onReplay: (row: Record<string, unknown>) => void;
  onEditTranscript: (row: Record<string, unknown>, next: string) => void;
  onRemove: (row: Record<string, unknown>) => void;
}) {
  const id = String(row.id ?? rowId(row, index));
  const replayResult = replays[id];
  const replayAfter =
    replayResult?.after && typeof replayResult.after === "object"
      ? (replayResult.after as Record<string, unknown>)
      : replayResult;
  const replayText = String(replayAfter?.final_text ?? "");
  const learning =
    row.learning && typeof row.learning === "object"
      ? (row.learning as Record<string, unknown>)
      : null;
  const similar = Number(learning?.similar ?? 0);
  const destination =
    presentValue(row.target_profile) || presentValue(row.intent);
  const took = Number(row.total_ms ?? 0);
  return (
    <SurfaceLedgerRow
      key={rowId(row, index)}
      time={streamTime(
        streamDate(row.created_at ?? row.timestamp),
      )}
      primary={String(row.transcript ?? "")}
      open={openId === id}
      onToggle={() => onToggle(id)}
      cells={
        <>
          <span className="surface-ledger-cell surface-ledger-dest">
            {destination ? `→ ${destination}` : ""}
          </span>
          <span className="surface-ledger-cell surface-ledger-ms">
            {took > 0 ? `${Math.round(took)} ms` : ""}
          </span>
          <span className="surface-ledger-cell">
            {row.corrected ? (
              <span className="surface-learned">
                TAUGHT
                {learning?.matched && similar > 0
                  ? ` · ${similar} SIMILAR`
                  : ""}
              </span>
            ) : null}
          </span>
        </>
      }
    >
      <EditInPlace
        value={String(row.transcript ?? "")}
        label="transcript"
        multiline
        onCommit={(next) => void onEditTranscript(row, next)}
      />
      <div className="surface-row-verbs">
        <Button dense onClick={() => void onReplay(row)}>
          Replay
        </Button>
        <Button
          dense
          variant="ghost"
          onClick={() =>
            void navigator.clipboard.writeText(
              String(row.transcript ?? ""),
            )
          }
        >
          Copy
        </Button>
        <ConfirmVerb
          label="Delete"
          confirmLabel="Delete?"
          onConfirm={() => void onRemove(row)}
        />
      </div>
      {replayResult ? (
        <div className="surface-preview" role="status">
          <span className="surface-preview-label">
            Replay — preview only
          </span>
          <p>
            {replayText ||
              "The replay completed without text."}
          </p>
          <div className="surface-actions">
            <Button
              dense
              variant="ghost"
              disabled={!replayText}
              onClick={() =>
                void navigator.clipboard.writeText(replayText)
              }
            >
              Copy result
            </Button>
          </div>
        </div>
      ) : null}
    </SurfaceLedgerRow>
  );
}

export function Journal() {
  const resource = useResource<DictationJournalResponse>(
    "/api/dictation/journal?limit=200",
    {},
  );
  const rows = asRows(resource.data, ["items"]);
  const [query, setQuery] = useState("");
  const [openId, setOpenId] = useState("");
  const [replays, setReplays] = useState<Record<string, Record<string, unknown>>>({});
  const filtered = rows.filter(
    (row) =>
      !query ||
      String(row.transcript ?? "")
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  const today = new Date();
  const todayCount = rows.filter((row) => {
    const date = streamDate(row.created_at ?? row.timestamp);
    return date != null && isSameStreamDay(date, today);
  }).length;
  const taughtCount = rows.filter((row) => {
    if (!row.corrected) return false;
    const date = streamDate(row.created_at ?? row.timestamp);
    return date != null && isSameStreamDay(date, today);
  }).length;
  const days: { label: string; rows: typeof filtered }[] = [];
  for (const row of filtered) {
    const label = streamDayLabel(streamDate(row.created_at ?? row.timestamp));
    const bucket = days.at(-1);
    if (bucket && bucket.label === label) bucket.rows.push(row);
    else days.push({ label, rows: [row] });
  }
  const remove = async (target: Record<string, unknown> | "all") => {
    await apiFetch(
      target === "all"
        ? "/api/dictation/journal"
        : `/api/dictation/journal/${encodeURIComponent(String(target.id))}`,
      { method: "DELETE" },
    );
    await resource.reload();
  };
  const replay = async (row: Record<string, unknown>) => {
    const result = await apiFetch<DictationJournalReplayResponse>(
      `/api/dictation/journal/${encodeURIComponent(String(row.id))}/replay`,
      { method: "POST" },
    );
    setReplays((current) => ({ ...current, [String(row.id)]: result }));
  };
  const editTranscript = async (
    row: Record<string, unknown>,
    next: string,
  ) => {
    await apiFetch(
      `/api/dictation/journal/${encodeURIComponent(String(row.id))}`,
      { method: "PUT", json: { transcript: next } },
    );
    await resource.reload();
  };
  return (
    <SurfaceSection>
      <SurfaceLedger
        count={[countToken(todayCount, "TODAY"), countToken(taughtCount, "TAUGHT")].filter(Boolean).join(" · ") || undefined}
        controls={
          <>
            <StringGadget
              label="Search the journal"
              placeholder="search"
              value={query}
              onChange={setQuery}
            />
            <ConfirmVerb
              label="Clear"
              confirmLabel="Clear all?"
              disabled={!rows.length}
              onConfirm={() => void remove("all")}
            />
          </>
        }
      >
        <SurfaceState
          loading={resource.loading}
          error={resource.error}
          empty={!filtered.length}
          emptyLabel="No dictations on this device"
          emptyGlyph="▤"
          onRetry={() => void resource.reload()}
        >
          {days.map((day) => (
            <SurfaceStreamDay key={day.label} label={day.label}>
              {day.rows.map((row, index) => (
                <JournalRow
                  key={rowId(row, index)}
                  row={row}
                  index={index}
                  openId={openId}
                  onToggle={(id) => setOpenId(openId === id ? "" : id)}
                  replays={replays}
                  onReplay={replay}
                  onEditTranscript={editTranscript}
                  onRemove={remove}
                />
              ))}
            </SurfaceStreamDay>
          ))}
        </SurfaceState>
      </SurfaceLedger>
    </SurfaceSection>
  );
}
