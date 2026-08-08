import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
// HS-117-09 — decomposed shell: sub-components live in ./history/.
import { useEffect, useMemo, useState } from "react";
import { openSurfaceOr } from "../../desk/shell";
import type {
  CoreProps,
  MeetingsListResponse,
  MeetingsFacetsResponse,
  AllActionItemsResponse,
  SpeakersResponse,
  ProjectsListResponse,
  IntelJobsResponse,
  PluginJobsResponse,
  MeetingDetailResponse,
} from "./core-types";
import { Button } from "../../components/signal/Signal";
import { apiBlob, apiFetch, readableError } from "../../lib/api";
import { asRows, useResource } from "../pageSupport";
import { ConfirmVerb, SurfaceSplit, SurfaceState } from "../../desk/surface/Surface";
import { EgressChip } from "../../desk/surface/gadgets";
import { useLedgerFilter } from "../../desk/surface/LedgerFilter";
import { useCoreWings } from "./core-hooks";
import { renderHeroSlot } from "./core-layout";
import {
  WINGS, stateToken, clockTime, download, type Receipt,
  MeetingDetail, ImportSection, CatalogRail, DoorSection,
} from "./history";

export function HistoryCore({ hero, scope }: CoreProps) {
  // Scope arrives as a prop (a qualified ref, e.g. "meeting:<id>") — the
  // flat wrapper decodes the URL; the desk passes it straight.
  const requestedMeetingScope =
    scope && scope.startsWith("meeting:")
      ? scope.slice("meeting:".length)
      : null;
  const [requestedMeetingId, requestedMeetingQuery = ""] =
    requestedMeetingScope?.split("?", 2) ?? [null, ""];
  const requestedMomentSegment = requestedMeetingQuery
    ? Number(new URLSearchParams(requestedMeetingQuery).get("segment"))
    : null;
  const wings = useCoreWings(WINGS, "outcomes", "Meeting plumbing");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [speaker, setSpeaker] = useState("");
  const [tag, setTag] = useState("");
  const [openActions, setOpenActions] = useState(false);
  const [selected, setSelected] = useState<Record<string, unknown> | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [removing, setRemoving] = useState(false);
  const [openedRequestedMeetingId, setOpenedRequestedMeetingId] = useState<
    string | null
  >(null);
  const [requestedMeetingError, setRequestedMeetingError] = useState("");
  const [queueStatus, setQueueStatus] = useState("pending");
  const meetingParams = new URLSearchParams({ limit: "100" });
  if (dateFrom) meetingParams.set("date_from", dateFrom);
  if (dateTo) meetingParams.set("date_to", dateTo);
  if (speaker) meetingParams.set("speaker", speaker);
  if (tag) meetingParams.set("tag", tag);
  if (openActions) meetingParams.set("has_open_actions", "true");
  const meetings = useResource<MeetingsListResponse>(`/api/meetings?${meetingParams}`, {});
  const facets = useResource<MeetingsFacetsResponse>("/api/meetings/facets", {});
  const actions = useResource<AllActionItemsResponse>("/api/all-action-items", {});
  const speakers = useResource<SpeakersResponse>("/api/speakers", {});
  const projects = useResource<ProjectsListResponse>("/api/projects", {});
  const intel = useResource<IntelJobsResponse>(
    `/api/intel/jobs?status=${queueStatus}&limit=50&history_limit=5`,
    {},
  );
  const plugin = useResource<PluginJobsResponse>(
    `/api/plugin-jobs?status=${queueStatus}&limit=50`,
    {},
  );
  const meetingRows = useMemo(
    () => asRows(meetings.data, ["meetings"]),
    [meetings.data],
  );
  const {
    query,
    setQuery,
    tokens,
    removeToken,
    clear: clearFilter,
    filtered: filteredMeetings,
    isActive: isFilterActive,
    total: meetingTotal,
  } = useLedgerFilter(meetingRows, {
    key: "meetings",
    match: (meeting, search) =>
      String(meeting.title ?? "").toLowerCase().includes(search.toLowerCase()),
  });
  const requestedMeeting = useMemo(
    () =>
      requestedMeetingId
        ? (meetingRows.find(
            (row) => String(row.id) === requestedMeetingId,
          ) ?? null)
        : null,
    [meetingRows, requestedMeetingId],
  );
  useEffect(() => {
    if (
      !requestedMeetingId ||
      openedRequestedMeetingId === requestedMeetingId ||
      meetings.loading
    )
      return;
    setOpenedRequestedMeetingId(requestedMeetingId);
    setRequestedMeetingError("");
    wings.setView("outcomes");
    if (requestedMeeting) {
      setSelected(requestedMeeting);
      return;
    }
    void apiFetch<MeetingDetailResponse>(
      `/api/meetings/${encodeURIComponent(requestedMeetingId)}`,
    )
      .then(setSelected)
      .catch((reason) => setRequestedMeetingError(readableError(reason)));
  }, [
    meetings.loading,
    openedRequestedMeetingId,
    requestedMeeting,
    requestedMeetingId,
  ]);
  const verbs = (
    <>
      <Button
        variant="primary"
        dense
        onClick={() => {
          wings.setDoorOpen(false);
          wings.setView("record");
        }}
      >
        Import
      </Button>
      <Button
        dense
        variant="secondary"
        onClick={() => openSurfaceOr("record-live", "/live", scope)}
      >
        Record meeting
      </Button>
    </>
  );
  const filtered = Boolean(
    isFilterActive || speaker || tag || dateFrom || dateTo || openActions,
  );
  /* HS-111-03 — the footer's export/delete verbs act on the OPEN
     record; receipts land in the same bar's center channel. */
  const exportMeeting = async (format: string) => {
    if (!selected) return;
    const id = String(selected.id);
    try {
      download(
        await apiBlob(
          `/api/meetings/${encodeURIComponent(id)}/export?format=${format}`,
        ),
        `holdspeak-meeting-${id}.${format === "markdown" ? "md" : format}`,
      );
      setReceipt({
        text: `EXPORTED ${format === "markdown" ? "MD" : format.toUpperCase()} ${clockTime(new Date().toISOString())}`,
      });
    } catch (reason) {
      setReceipt({
        text: `⚠ REFUSED · ${readableError(reason)}`,
        tone: "danger",
      });
    }
  };
  const removeSelected = async () => {
    if (!selected) return;
    setRemoving(true);
    try {
      await apiFetch(`/api/meetings/${encodeURIComponent(String(selected.id))}`, {
        method: "DELETE",
      });
      setSelected(null);
      setReceipt({ text: `DELETED ${clockTime(new Date().toISOString())}` });
      void meetings.reload();
    } catch (reason) {
      setReceipt({
        text: `⚠ REFUSED · ${readableError(reason)}`,
        tone: "danger",
      });
    } finally {
      setRemoving(false);
    }
  };
  const needing = filteredMeetings.filter((row) => stateToken(row).tone).length;

  const rail = (
    <CatalogRail
      meetingRows={filteredMeetings}
      meetings={meetings}
      facets={facets}
      selected={selected}
      setSelected={setSelected}
      query={query}
      setQuery={setQuery}
      filterTokens={tokens}
      removeFilterToken={removeToken}
      clearFilter={clearFilter}
      filterActive={isFilterActive}
      filterTotal={meetingTotal}
      filtersOpen={filtersOpen}
      setFiltersOpen={setFiltersOpen}
      dateFrom={dateFrom}
      setDateFrom={setDateFrom}
      dateTo={dateTo}
      setDateTo={setDateTo}
      speaker={speaker}
      setSpeaker={setSpeaker}
      tag={tag}
      setTag={setTag}
      openActions={openActions}
      setOpenActions={setOpenActions}
      needing={needing}
    />
  );

  const door = (
    <DoorSection
      actions={actions}
      speakers={speakers}
      projects={projects}
      intel={intel}
      plugin={plugin}
      queueStatus={queueStatus}
      setQueueStatus={setQueueStatus}
    />
  );

  const detailPane = (paneView: "outcomes" | "artifacts") => (
    <MeetingDetail
      meeting={selected}
      view={paneView}
      momentSegmentIndex={requestedMomentSegment}
      onClose={() => setSelected(null)}
      onDeleted={() => void meetings.reload()}
      onReceipt={setReceipt}
    />
  );

  const face = wings.doorOpen ? (
    door
  ) : wings.view === "record" ? (
    <ImportSection
      onDone={() => wings.setView("outcomes")}
      onImported={() => void meetings.reload()}
      scope={scope}
    />
  ) : wings.view === "artifacts" ? (
    selected ? (
      detailPane("artifacts")
    ) : (
      /* The wing works from cold: no record open → the catalog, so
         the hand can pick one. Never a dead-end empty state. */
      rail
    )
  ) : (
    <div className="surface-split-railed">
      <SurfaceSplit
        main={rail}
        detailOpen={Boolean(selected)}
        detail={detailPane("outcomes")}
      />
    </div>
  );

  return (
    <>
      {renderHeroSlot(hero, verbs)}
      {requestedMeetingError ? (
        <SurfaceState
          error={requestedMeetingError}
          onRetry={() => {
            setRequestedMeetingError("");
            setOpenedRequestedMeetingId(null);
          }}
        />
      ) : null}
      {face}
      {/* HS-129-05 — receipt and verbs occupy their frame-owned slots. */}
      <SurfaceFooter
        egress={<EgressChip />}
        receipt={
          <span
            className="surface-footer-receipt-line"
            data-tone={receipt?.tone}
            role="status"
          >
            {receipt
              ? receipt.text
              : `${filteredMeetings.length} RECORDS${filtered ? " · FILTERED" : ""}`}
          </span>
        }
        verbs={
          selected && !wings.doorOpen && wings.view !== "record" ? (
            <span className="surface-footer-verbs-group">
              <Button
                dense
                variant="ghost"
                onClick={() => void exportMeeting("markdown")}
              >
                MD
              </Button>
              <Button
                dense
                variant="ghost"
                onClick={() => void exportMeeting("txt")}
              >
                TXT
              </Button>
              <Button
                dense
                variant="ghost"
                onClick={() => void exportMeeting("json")}
              >
                JSON
              </Button>
              <Button
                dense
                variant="ghost"
                onClick={() => void exportMeeting("srt")}
              >
                SRT
              </Button>
              <ConfirmVerb
                label="Delete"
                confirmLabel="Delete?"
                busy={removing}
                onConfirm={() => void removeSelected()}
              />
            </span>
          ) : null
        }
      />
    </>
  );
}
