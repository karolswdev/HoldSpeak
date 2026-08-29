// HS-117-09 — extracted from HistoryCore (lines 938-1098).
import { useState } from "react";
import { Button } from "../../../components/signal/Signal";
import {
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  SurfaceState,
} from "../../../desk/surface/Surface";
import {
  CheckGadget,
  CycleGadget,
  GadgetGroup,
  GadgetRow,
  StringGadget,
} from "../../../desk/surface/gadgets";
import { spriteUrl } from "../../../desk/sprites";
import { SPARSE_THRESHOLD } from "../../../desk/surface/sparse";
import { asRows, rowId } from "../../pageSupport";
import { stateToken, durationToken, ledgerDate } from "./helpers";
import { StateTokenSpan } from "./StateTokenSpan";
import type { MeetingsFacetsResponse } from "../core-types";
import { apiFetch } from "../../../lib/api";
import {
  LedgerFilterBar,
  type LedgerFilterToken,
} from "../../../desk/surface/LedgerFilter";

export function CatalogRail({
  meetingRows,
  meetings,
  facets,
  selected,
  setSelected,
  query,
  setQuery,
  filterTokens,
  removeFilterToken,
  clearFilter,
  filterActive,
  filterTotal,
  filtersOpen,
  setFiltersOpen,
  dateFrom,
  setDateFrom,
  dateTo,
  setDateTo,
  speaker,
  setSpeaker,
  tag,
  setTag,
  openActions,
  setOpenActions,
  needing,
}: {
  meetingRows: Record<string, unknown>[];
  meetings: { loading: boolean; error: string; reload(): Promise<unknown> };
  facets: { data: Record<string, unknown> };
  selected: Record<string, unknown> | null;
  setSelected: (row: Record<string, unknown> | null) => void;
  query: string;
  setQuery: (value: string) => void;
  filterTokens: LedgerFilterToken[];
  removeFilterToken: (field: string, value: string) => void;
  clearFilter: () => void;
  filterActive: boolean;
  filterTotal: number;
  filtersOpen: boolean;
  setFiltersOpen: (fn: (open: boolean) => boolean) => void;
  dateFrom: string;
  setDateFrom: (value: string) => void;
  dateTo: string;
  setDateTo: (value: string) => void;
  speaker: string;
  setSpeaker: (value: string) => void;
  tag: string;
  setTag: (value: string) => void;
  openActions: boolean;
  setOpenActions: (value: boolean) => void;
  needing: number;
}) {
  return (
    <SurfaceSection label="Meetings">
      <SurfaceLedger
        cols="meetings"
        count={`${meetingRows.length} RECORDS${needing ? ` · ${needing} NEEDS YOU` : ""}`}
        controls={
          <>
            <LedgerFilterBar
              query={query}
              onQueryChange={setQuery}
              tokens={filterTokens}
              onRemoveToken={removeFilterToken}
              onClear={clearFilter}
              total={filterTotal}
              matchCount={meetingRows.length}
              isActive={filterActive}
              itemCount={filterTotal}
            />
            {filterTotal >= SPARSE_THRESHOLD ? (
              <Button
                dense
                variant="ghost"
                aria-expanded={filtersOpen}
                onClick={() => setFiltersOpen((open) => !open)}
              >
                Filters
              </Button>
            ) : null}
          </>
        }
      >
        {filtersOpen ? (
          /* Filters apply on change (the resource re-fetches on param
             change); one RESET verb, no submit wall. */
          <GadgetGroup label="Filters">
            <GadgetRow label="SPEAKER">
              <CycleGadget
                label="Speaker"
                value={speaker}
                onChange={setSpeaker}
                options={[
                  { value: "", label: "ANY" },
                  ...asRows(facets.data, ["speakers"]).map((row) => ({
                    value: String(row.id ?? row.name ?? row.value),
                    label: String(row.name ?? row.label ?? row.value),
                  })),
                ]}
              />
            </GadgetRow>
            <GadgetRow label="TAG">
              <CycleGadget
                label="Tag"
                value={tag}
                onChange={setTag}
                options={[
                  { value: "", label: "ANY" },
                  ...(Array.isArray(facets.data.tags)
                    ? facets.data.tags
                    : []
                  ).map((value) => ({ value: String(value) })),
                ]}
              />
            </GadgetRow>
            <GadgetRow label="FROM">
              <StringGadget
                label="From date"
                type="date"
                mic={false}
                value={dateFrom}
                onChange={setDateFrom}
              />
            </GadgetRow>
            <GadgetRow label="TO">
              <StringGadget
                label="To date"
                type="date"
                mic={false}
                value={dateTo}
                onChange={setDateTo}
              />
            </GadgetRow>
            <GadgetRow label="OPEN ACTIONS">
              <CheckGadget
                label="Only meetings with open actions"
                checked={openActions}
                onChange={setOpenActions}
              />
            </GadgetRow>
            <div className="surface-actions">
              <Button
                dense
                variant="ghost"
                onClick={() => {
                  clearFilter();
                  setDateFrom("");
                  setDateTo("");
                  setSpeaker("");
                  setTag("");
                  setOpenActions(false);
                }}
              >
                Reset
              </Button>
            </div>
          </GadgetGroup>
        ) : null}
        <SurfaceState
          loading={meetings.loading}
          error={meetings.error}
          empty={!meetingRows.length}
          emptyLabel="Nothing here yet"
          emptyImage={spriteUrl("meeting", "archive-empty")}
          onRetry={() => void meetings.reload()}
        >
          <ul className="surface-ledger-rows">
            {meetingRows.map((row, index) => {
              const token = stateToken(row);
              const isOpen = Boolean(
                selected && String(selected.id) === String(row.id),
              );
              const recoverable = [
                "capture_failed",
                "recoverable",
                "recording",
              ].includes(String(row.capture_status ?? ""));
              const originLine = row.calendar_event_id ? (
                <span
                  className="surface-ledger-origin"
                  data-meeting-origin="calendar-event"
                >
                  {`FROM ${String(row.calendar_source_label || "CALENDAR").toUpperCase()}`}
                  {row.calendar_event_title
                    ? ` · ${String(row.calendar_event_title).toUpperCase()}`
                    : ""}
                </span>
              ) : null;
              return (
                <SurfaceLedgerRow
                  key={rowId(row, index)}
                  time={ledgerDate(row.started_at ?? row.created_at)}
                  primary={
                    originLine ? (
                      <>
                        {String(row.title ?? "Meeting")}
                        {originLine}
                      </>
                    ) : (
                      String(row.title ?? "Meeting")
                    )
                  }
                  open={isOpen}
                  onToggle={() => setSelected(isOpen ? null : row)}
                  cells={
                    <>
                      <span className="surface-ledger-cell">
                        {`${Number(row.segment_count ?? 0)} SEG`}
                      </span>
                      <span className="surface-ledger-cell">
                        {durationToken(row.duration_seconds)}
                      </span>
                      <span className="surface-ledger-cell">
                        <StateTokenSpan token={token} />
                      </span>
                    </>
                  }
                >
                  {recoverable ? (
                    <div className="surface-row-verbs">
                      <Button
                        dense
                        onClick={() =>
                          void apiFetch(
                            `/api/meetings/${encodeURIComponent(String(row.id))}/capture/recover`,
                            { method: "POST" },
                          ).then(() => meetings.reload())
                        }
                      >
                        Recover saved work
                      </Button>
                    </div>
                  ) : null}
                </SurfaceLedgerRow>
              );
            })}
          </ul>
        </SurfaceState>
      </SurfaceLedger>
    </SurfaceSection>
  );
}
