// HS-158-05 extraction — the state/effects/handlers that lived inside
// ProjectMemoryCore, exposed as a controller hook.  WEB-ARC-003: the
// main load lifecycle is a discriminated `loadStatus` instead of
// contradictory loading+error booleans.

import { useEffect, useMemo, useState } from "react";
import { readableError } from "../../lib/api";
import { openSurfaceOr } from "../../desk/shell";
import { openSourceRef } from "../../desk/surface/citations";
import { useCoreWings } from "../../pages/cores/core-hooks";
import type { SinceLastMeetingResponse } from "./model";
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
  const [meetings, setMeetings] = useState<Record<string, unknown>[]>([]);
  const [decisions, setDecisions] = useState<Record<string, unknown>[]>([]);
  const [artifacts, setArtifacts] = useState<Record<string, unknown>[]>([]);
  const [since, setSince] = useState<SinceLastMeetingResponse>({});
  const [loadStatus, setLoadStatus] = useState<LoadStatus>(
    projectId ? "loading" : "idle",
  );
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
      const [projectBody, meetingBody, decisionBody, artifactBody, sinceBody] =
        await Promise.all([
          api.fetchProject(projectId),
          api.fetchProjectMeetings(projectId),
          api.fetchProjectDecisions(projectId),
          api.fetchProjectArtifacts(projectId),
          api.fetchSinceLastMeeting(projectId),
        ]);
      setProject(projectBody);
      setMeetings(meetingBody.meetings || []);
      setDecisions(decisionBody.decisions || []);
      setArtifacts(artifactBody.artifacts || []);
      setSince(sinceBody);
      setReadAt(Date.now());
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setLoadStatus("ready");
    }
  };

  useEffect(() => {
    void load();
  }, [projectId]); // eslint-disable-line react-hooks/exhaustive-deps

  const timeline = useMemo(
    () => composeProjectTimeline(meetings, decisions, artifacts),
    [meetings, decisions, artifacts],
  );
  const projectName = String(project.name || scopeLabel || "Project");

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
    error,
    // Data
    project,
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
