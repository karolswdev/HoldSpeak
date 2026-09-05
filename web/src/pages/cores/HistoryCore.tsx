// HS-170-04 — the Meetings face, rewritten to the settled design.
// Board: display headline + Record/Import + stream rows + SurfaceSplit detail.
import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import { useCallback, useEffect, useMemo, useState } from "react";
import { openSurfaceOr } from "../../desk/shell";
import type { CoreProps, MeetingsListResponse, MeetingDetailResponse } from "./core-types";
import { Button } from "../../components/signal/Signal";
import { apiFetch, apiBlob, readableError } from "../../lib/api";
import { asRows } from "../pageSupport";
import { useResource } from "../pageSupport";
import { ConfirmVerb, SurfaceSplit } from "../../desk/surface/Surface";
import { countToken } from "../../desk/surface";
import { EgressChip } from "../../desk/surface/gadgets";
import { useCoreWings } from "./core-hooks";
import { renderHeroSlot } from "./core-layout";
import {
  WINGS, clockTime, download, needsIntelligence, type Receipt,
  MeetingDetail, ImportSection, CatalogRail,
} from "./history";

/** HS-170-04 — the display headline: `N meeting(s) need intelligence` (accent)
 *  or `Nothing needs you` (muted) or `No meetings yet` when empty. */
function meetingsHeadline(
  meetingRows: Record<string, unknown>[],
  loading: boolean,
): { text: string; accent: boolean } {
  if (loading) return { text: "", accent: false };
  if (meetingRows.length === 0) return { text: "No meetings yet", accent: false };
  const offWithWords = meetingRows.filter(needsIntelligence).length;
  if (offWithWords > 0) {
    const noun = offWithWords === 1 ? "meeting needs" : "meetings need";
    return { text: `${offWithWords} ${noun} intelligence`, accent: true };
  }
  return { text: "Nothing needs you", accent: false };
}

export function HistoryCore({ hero, scope }: CoreProps) {
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
  const [selected, setSelected] = useState<Record<string, unknown> | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [removing, setRemoving] = useState(false);
  const [openedRequestedMeetingId, setOpenedRequestedMeetingId] = useState<
    string | null
  >(null);
  const [requestedMeetingError, setRequestedMeetingError] = useState("");

  // Intelligence run state
  const [runningId, setRunningId] = useState<string | null>(null);
  const [runHost, setRunHost] = useState<string | null>(null);

  const meetings = useResource<MeetingsListResponse>("/api/meetings?limit=100", {});
  const meetingRows = useMemo(
    () => asRows(meetings.data, ["meetings"]),
    [meetings.data],
  );

  // Open requested meeting from scope
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

  // Run intelligence on a meeting
  const handleRunIntelligence = useCallback(async (meetingId: string) => {
    setRunningId(meetingId);
    setRunHost(null);
    try {
      const result = await apiFetch<{ jobId: string; state: string; host: string }>(
        `/api/meetings/${encodeURIComponent(meetingId)}/intelligence/run`,
        { method: "POST" },
      );
      setRunHost(result.host ?? "THIS DEVICE");
      setReceipt({ text: `QUEUED ${clockTime(new Date().toISOString())}` });
      // Poll for completion
      const poll = setInterval(async () => {
        try {
          const statusResp = await apiFetch<MeetingDetailResponse>(
            `/api/meetings/${encodeURIComponent(meetingId)}`,
          );
          const intelStatus = statusResp?.intel_status;
          const state = typeof intelStatus === "object" && intelStatus !== null
            ? String((intelStatus as Record<string, unknown>).state ?? "")
            : String(intelStatus ?? "");
          if (state !== "queued" && state !== "running" && state !== "pending") {
            clearInterval(poll);
            setRunningId(null);
            setRunHost(null);
            void meetings.reload();
          }
        } catch {
          clearInterval(poll);
          setRunningId(null);
          setRunHost(null);
        }
      }, 3000);
      // Safety timeout
      setTimeout(() => {
        clearInterval(poll);
        setRunningId((current) => {
          if (current === meetingId) {
            void meetings.reload();
            return null;
          }
          return current;
        });
        setRunHost(null);
      }, 120_000);
    } catch (reason) {
      setRunningId(null);
      setRunHost(null);
      const msg = readableError(reason);
      setReceipt({ text: `REFUSED · ${msg}`, tone: "danger" });
    }
  }, [meetings]);

  // The headline
  const headline = meetingsHeadline(meetingRows, meetings.loading);

  // Verbs in the head
  const verbs = (
    <>
      <Button
        variant="primary"
        dense
        onClick={() => openSurfaceOr("record-live", "/live", scope)}
      >
        Record meeting
      </Button>
      <Button
        dense
        variant="ghost"
        onClick={() => {
          wings.setDoorOpen(false);
          wings.setView("record");
        }}
      >
        Import
      </Button>
    </>
  );

  // Footer export verbs
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
        text: `REFUSED · ${readableError(reason)}`,
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
        text: `REFUSED · ${readableError(reason)}`,
        tone: "danger",
      });
    } finally {
      setRemoving(false);
    }
  };

  const rail = (
    <CatalogRail
      meetingRows={meetingRows}
      meetings={meetings}
      selected={selected}
      setSelected={setSelected}
      onRunIntelligence={(id) => void handleRunIntelligence(id)}
      runningId={runningId}
      runHost={runHost}
      narrowed={Boolean(selected)}
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
      onRunIntelligence={
        selected && needsIntelligence(selected)
          ? () => void handleRunIntelligence(String(selected.id))
          : undefined
      }
    />
  );

  const face = wings.view === "record" ? (
    <ImportSection
      onDone={() => wings.setView("outcomes")}
      onImported={() => void meetings.reload()}
      scope={scope}
    />
  ) : wings.view === "artifacts" ? (
    selected ? (
      detailPane("artifacts")
    ) : (
      rail
    )
  ) : (
    <>
      {/* HS-170-04: the headline (display step, ONE per face) */}
      <div className="meetings-headline" data-accent={headline.accent || undefined}>
        <span className="surface-display" data-testid="meetings-headline">
          {headline.text}
        </span>
      </div>

      {/* Head verbs */}
      <div className="meetings-head-verbs">
        {verbs}
      </div>

      {/* The stream + detail split */}
      <div className="surface-split-railed">
        <SurfaceSplit
          main={rail}
          detailOpen={Boolean(selected)}
          detail={detailPane("outcomes")}
        />
      </div>
    </>
  );

  return (
    <>
      {renderHeroSlot(hero, null)}
      {requestedMeetingError ? (
        <div className="surface-state-error">
          <span>{requestedMeetingError}</span>
          <Button dense variant="ghost" onClick={() => {
            setRequestedMeetingError("");
            setOpenedRequestedMeetingId(null);
          }}>
            Retry
          </Button>
        </div>
      ) : null}
      {face}
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
              : countToken(meetingRows.length, "RECORD") ?? "RECORDS"}
          </span>
        }
        verbs={
          selected && wings.view !== "record" ? (
            <span className="surface-footer-verbs-group">
              <Button dense variant="ghost" onClick={() => void exportMeeting("markdown")}>
                MD
              </Button>
              <Button dense variant="ghost" onClick={() => void exportMeeting("srt")}>
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
