// HS-158-05 adoption — the controller now uses GET /room as the FIRST
// render (one request for orientation + focus + counts). The legacy
// detail fetches (meetings/decisions/artifacts/since-last-meeting)
// become progressive follow-ups feeding the existing timeline/decision
// wings. WEB-ARC-003: discriminated loadStatus. WEB-STA-001/002:
// orientation renders before slow sections; one failed section never
// blanks the rest.

import { useEffect, useMemo, useState } from "react";
import { readableError } from "../../lib/api";
import { openSurfaceOr } from "../../desk/shell";
import { openSourceRef } from "../../desk/surface/citations";
import { useCoreWings } from "../../pages/cores/core-hooks";
import type { SinceLastMeetingResponse } from "./model";
import type { RoomSnapshot } from "./model";
import { composeProjectTimeline } from "./model";
import * as api from "./api";

const WINGS = [
  { id: "timeline", label: "Timeline" },
  { id: "decisions", label: "Decisions" },
  { id: "search", label: "Search" },
  { id: "ask", label: "Ask" },
];

/** Discriminated load lifecycle — idle (no scope), loading, or ready
 *  (data fetched or fetch failed; error carries the reason). */
export type LoadStatus = "idle" | "loading" | "ready";

export function useProjectRoomController(
  scope: string | undefined,
  scopeLabel: string | undefined,
) {
  const projectId = scope?.startsWith("project:")
    ? scope.slice("project:".length)
    : "";
  const wings = useCoreWings(WINGS, "timeline");
  const [project, setProject] = useState<Record<string, unknown>>({});
  const [room, setRoom] = useState<RoomSnapshot | null>(null);
  const [meetings, setMeetings] = useState<Record<string, unknown>[]>([]);
  const [decisions, setDecisions] = useState<Record<string, unknown>[]>([]);
  const [artifacts, setArtifacts] = useState<Record<string, unknown>[]>([]);
  const [since, setSince] = useState<SinceLastMeetingResponse>({});
  const [loadStatus, setLoadStatus] = useState<LoadStatus>(
    projectId ? "loading" : "idle",
  );
  const [detailStatus, setDetailStatus] = useState<"idle" | "loading" | "ready">("idle");
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchHits, setSearchHits] = useState<Record<string, unknown>[]>([]);
  const [searched, setSearched] = useState(false);
  const [searching, setSearching] = useState(false);
  const [decisionBusy, setDecisionBusy] = useState("");
  const [successors, setSuccessors] = useState<Record<string, string>>({});
  const [readAt, setReadAt] = useState<number | null>(null);

  const load = async () => {
    if (!projectId) return;
    setLoadStatus("loading");
    setError("");
    try {
      // Phase 1: one /room request gives orientation + focus + counts
      const snapshot = await api.fetchProjectRoom(projectId);
      setRoom(snapshot);
      // Populate project from the room orientation for backward compat
      setProject({
        id: snapshot.project.id,
        name: snapshot.project.name,
        description: snapshot.project.description,
        is_archived: snapshot.project.isArchived,
        meeting_count: snapshot.project.meetingCount,
        created_at: snapshot.project.createdAt,
        updated_at: snapshot.project.updatedAt,
      });
      setReadAt(Date.now());
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setLoadStatus("ready");
    }

    // Phase 2: progressive detail fetches for timeline/decisions wings
    // These are non-blocking; the first paint does not wait for them.
    setDetailStatus("loading");
    try {
      const [meetingBody, decisionBody, artifactBody, sinceBody] =
        await Promise.all([
          api.fetchProjectMeetings(projectId),
          api.fetchProjectDecisions(projectId),
          api.fetchProjectArtifacts(projectId),
          api.fetchSinceLastMeeting(projectId),
        ]);
      setMeetings(meetingBody.meetings || []);
      setDecisions(decisionBody.decisions || []);
      setArtifacts(artifactBody.artifacts || []);
      setSince(sinceBody);
    } catch (reason) {
      // Detail failure does not blank the room face (WEB-STA-002)
      if (!error) setError(readableError(reason));
    } finally {
      setDetailStatus("ready");
    }
  };

  useEffect(() => {
    void load();
  }, [projectId]); // eslint-disable-line react-hooks/exhaustive-deps

  const timeline = useMemo(
    () => composeProjectTimeline(meetings, decisions, artifacts),
    [meetings, decisions, artifacts],
  );
  const projectName = String(
    room?.project.name || project.name || scopeLabel || "Project",
  );

  const openMoment = async (decision: Record<string, unknown>) => {
    try {
      const body = await api.fetchDecisionMoment(String(decision.id));
      const moment = body.moment || {};
      const meetingId = String(
        moment.meeting_id || decision.source_meeting_id || "",
      );
      if (meetingId) {
        openSurfaceOr(
          "review-meetings",
          "/history",
          `meeting:${meetingId}?segment=${Number(moment.segment_index) || 0}`,
        );
      }
    } catch (reason) {
      setError(readableError(reason));
    }
  };

  const transition = async (
    decision: Record<string, unknown>,
    action: "accept" | "supersede",
  ) => {
    const id = String(decision.id);
    const successor = successors[id];
    if (action === "supersede" && !successor) return;
    setDecisionBusy(id);
    setError("");
    try {
      const body = await api.transitionDecision(
        id,
        action,
        action === "supersede" ? { superseded_by: successor } : {},
      );
      const updated = body.decision as Record<string, unknown>;
      setDecisions((rows) =>
        rows.map((row) => (row.id === id ? updated : row)),
      );
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setDecisionBusy("");
    }
  };

  const openProjectRef = (ref: string) => {
    if (ref.startsWith("decision:")) {
      wings.setView("decisions");
      return;
    }
    openSourceRef(ref);
  };

  const search = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    setSearched(true);
    setError("");
    try {
      const body = await api.searchProjectMemory(searchQuery.trim(), projectId);
      setSearchHits(body.hits || []);
    } catch (reason) {
      setSearchHits([]);
      setError(readableError(reason));
    } finally {
      setSearching(false);
    }
  };

  return {
    projectId,
    loadStatus,
    detailStatus,
    error,
    // Data
    project,
    room,
    meetings,
    decisions,
    artifacts,
    since,
    readAt,
    // Derived
    timeline,
    projectName,
    // Wings
    view: wings.view,
    setView: wings.setView,
    // Search
    searchQuery,
    searchHits,
    searched,
    searching,
    setSearchQuery,
    // Decision operations
    decisionBusy,
    successors,
    setSuccessors,
    // Actions
    load,
    search,
    openMoment,
    transition,
    openProjectRef,
  } as const;
}

export type ProjectRoomController = ReturnType<typeof useProjectRoomController>;
