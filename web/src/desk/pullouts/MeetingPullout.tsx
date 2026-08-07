import { SurfaceFooter } from "../surface/SurfaceFooter";
/** Meeting pullout content (HS-117-15). */
import { useEffect, useState } from "react";
import { apiRequest } from "../../lib/api";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { humanizeWireValue } from "../../lib/productLanguage";
import { Material } from "../surface/Material";
import {
  SurfaceRow,
  SurfaceRows,
  SurfaceState,
} from "../surface/Surface";
import { humanTime } from "../surface/format";
import { MeetingConflictRecovery } from "../../meetings/MeetingConflictRecovery";
import { MeetingIntelRecovery } from "../../meetings/MeetingIntelRecovery";
import type { PulloutContentProps } from "./types";

interface MeetingDetail {
  intel?: { summary?: string; action_items?: any[]; topics?: string[] } | null;
  intel_status?: { state?: string } | null;
  capture_status?: string;
  capture_failure?: string | null;
  provenance?: string;
  [key: string]: unknown;
}

function intelligenceState(value: string): string {
  const labels: Record<string, string> = {
    pending: "queued",
    complete: "succeeded",
    partial: "incomplete",
    failed: "failed",
    running: "running",
  };
  return labels[value] || value.replace(/_/g, " ");
}

export function MeetingPullout({ object: o, onClose }: PulloutContentProps) {
  const { closePullout, openPullout } = useDesk.getState();
  const [detail, setDetail] = useState<MeetingDetail | null>(null);
  const [artifacts, setArtifacts] = useState<any[]>([]);
  const resourceRef = qualifiedRef(o.kind, o.id);

  useEffect(() => {
    apiRequest(`/api/meetings/${encodeURIComponent(o.id)}`)
      .then((r) => r.json())
      .then(setDetail)
      .catch(() => setDetail(null));
    apiRequest(`/api/meetings/${encodeURIComponent(o.id)}/artifacts`)
      .then((r) => r.json())
      .then((d) => setArtifacts(d.artifacts || []))
      .catch(() => setArtifacts([]));
  }, [o.id]);

  const artifactRow = (a: any) => (
    <SurfaceRow
      key={a.id}
      title={a.title}
      detail={humanizeWireValue(String(a.artifact_type || a.artifactType || ""))}
      onOpen={() => openPullout(a.id)}
    />
  );

  const meetingFacts = detail
    ? [
        humanTime(String(detail.started_at || "")),
        Number(detail.duration) > 0
          ? `${Math.max(1, Math.round(Number(detail.duration) / 60))} min`
          : "",
        Array.isArray(detail.segments) && detail.segments.length
          ? `${detail.segments.length} segment${
              detail.segments.length === 1 ? "" : "s"
            }`
          : "",
      ]
        .filter(Boolean)
        .join(" · ")
    : "";

  return (
    <>
      <div className="desk-pullout-body desk-surface-body">
        {meetingFacts ? (
          <p className="quiet desk-pullout-facts">{meetingFacts}</p>
        ) : null}
        {detail?.capture_status && detail.capture_status !== "finalized" ? (
          <section>
            <h3>Saved, incomplete</h3>
            <p className="quiet">
              {humanizeWireValue(detail.capture_status)}
              {detail.capture_failure ? ` · ${humanizeWireValue(detail.capture_failure)}` : ""}
              {detail.provenance ? ` · from ${humanizeWireValue(detail.provenance)}` : ""}
            </p>
          </section>
        ) : null}
        <MeetingConflictRecovery
          meetingId={o.id}
          onResolved={async (result) => {
            if (result.deleted) {
              closePullout(o.id);
            } else if (result.meeting) {
              setDetail(result.meeting as MeetingDetail);
            }
            await useDesk.getState().refresh();
          }}
        />
        <MeetingIntelRecovery
          meetingId={o.id}
          onChanged={async () => {
            const meeting = await apiRequest(
              `/api/meetings/${encodeURIComponent(o.id)}`,
            );
            setDetail(await meeting.json());
            await useDesk.getState().refresh();
          }}
        />
        {detail?.intel?.summary ? (
          <p className="surface-say">{detail.intel.summary}</p>
        ) : (
          <SurfaceState
            empty
            emptyLabel={
              detail?.intel_status?.state === "disabled"
                ? "Intelligence off"
                : detail?.intel_status?.state
                  ? `Intelligence ${intelligenceState(detail.intel_status.state)}`
                  : "Intelligence queued"
            }
          />
        )}
        {detail?.intel?.action_items &&
          detail.intel.action_items.length > 0 && (
            <section>
              <h3>Action items</h3>
              <ul>
                {detail.intel.action_items
                  .slice(0, 8)
                  .map((a: any, i: number) => (
                    <li key={i}>
                      {typeof a === "string"
                        ? a
                        : a.task || a.text || a.title || ""}
                    </li>
                  ))}
              </ul>
            </section>
          )}
        {artifacts.length > 0 && (
          <section>
            <h3>Artifacts</h3>
            <SurfaceRows>{artifacts.map(artifactRow)}</SurfaceRows>
          </section>
        )}
        <DeskFilingStrip
          objectRef={resourceRef}
          objectKind={o.kind}
          objectId={o.id}
        />
      </div>
      <SurfaceFooter verbs={<> <button
          type="button"
          className="desk-chip quiet"
          onClick={() =>
            openSurfaceOr("dictate", "/dictation", resourceRef)
          }
        >
          Dictate about this
        </button>
        <button
          type="button"
          className="desk-chip quiet"
          onClick={() => openSurfaceOr("record-live", "/live", resourceRef)}
        >
          Record follow-up
        </button> </>} />
    </>
  );
}
