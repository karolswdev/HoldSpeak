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
import type { RoomSnapshot, RoomProposalItem, RoomSuggestedSourceItem } from "./model";
import { composeProjectTimeline } from "./model";
import * as api from "./api";

// HS-169-03: two wings only — ROOM (home) and HISTORY.
const WINGS = [
  { id: "room", label: "Room" },
  { id: "history", label: "History" },
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
  // The unscoped surface is Desk memory, which has neither a Room nor a
  // History: a wing that leads nowhere would be a verb that does nothing
  // (UX-CANON A.11).
  const wings = useCoreWings(projectId ? WINGS : [], "room");
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
  const [readAt, setReadAt] = useState<string | null>(null);

  // HS-172-03: proposals
  const [proposals, setProposals] = useState<RoomProposalItem[]>([]);
  const [proposalBusy, setProposalBusy] = useState("");

  // HS-172-06: suggested sources
  const [suggestedSources, setSuggestedSources] = useState<RoomSuggestedSourceItem[]>([]);
  const [suggestionBusy, setSuggestionBusy] = useState("");

  // HS-173-04: proposed nudges
  const [nudges, setNudges] = useState<api.NudgeItem[]>([]);

  // HS-169-03: POST /room/read after first paint and on Refresh.
  const postRead = async () => {
    if (!projectId) return;
    try {
      const res = await api.markRoomRead(projectId);
      setReadAt(res.read_at || new Date().toISOString());
    } catch {
      // Non-fatal: the read marker is a convenience.
      setReadAt(new Date().toISOString());
    }
  };

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
      // HS-169-03: readAt from the wire's sinceRead section (the PREVIOUS read).
      if (snapshot.sinceRead.state === "ok") {
        setReadAt(snapshot.sinceRead.readAt);
      }
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

    // Phase 3: HS-172-03/06 proposals + suggested sources + HS-173-04 nudges (non-blocking)
    // Confirmed proposals are now in the /room decisions list (wire HS-172-03).
    try {
      const [pendingProps, suggestions, proposedNudges] = await Promise.all([
        api.fetchProjectProposals(projectId, "proposed"),
        api.fetchSuggestedSources(projectId),
        api.fetchNudges(projectId, "proposed"),
      ]);
      setProposals(pendingProps);
      setSuggestedSources(suggestions);
      setNudges(proposedNudges);
    } catch {
      // Non-fatal: the face renders without proposals/suggestions/nudges
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
    room?.project.name || project.name || scopeLabel || (projectId ? "Project" : "Desk memory"),
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
    // Memory ranks the child message that matched, but the Desk opens the
    // parent conversation.  Other qualified refs are already parent refs.
    openSourceRef(ref.startsWith("thread:") ? ref.split("#", 1)[0] : ref);
  };

  // HS-172-03: proposal actions
  const handleConfirmProposal = async (
    proposalId: string,
    edits?: { text?: string; owner?: string; due?: string },
  ) => {
    setProposalBusy(proposalId);
    try {
      await api.confirmProposal(proposalId, edits);
      // Reload to pick up the confirmed state and new D&C row
      void load();
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setProposalBusy("");
    }
  };

  const handleDismissProposal = async (proposalId: string) => {
    setProposalBusy(proposalId);
    try {
      await api.dismissProposal(proposalId);
      // Optimistic remove
      setProposals((prev) => prev.filter((p) => p.id !== proposalId));
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setProposalBusy("");
    }
  };

  // HS-172-06: suggested source actions
  const handleAddSuggestion = async (ref: string) => {
    setSuggestionBusy(ref);
    try {
      await api.addSuggestedSource(projectId, ref);
      // Reload to pick up the new Watch source
      void load();
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setSuggestionBusy("");
    }
  };

  const handleDismissSuggestion = async (ref: string) => {
    setSuggestionBusy(ref);
    try {
      await api.dismissSuggestedSource(projectId, ref);
      // Optimistic remove
      setSuggestedSources((prev) => prev.filter((s) => s.reference !== ref));
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setSuggestionBusy("");
    }
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
    // HS-172-03: proposals
    proposals,
    proposalBusy,
    handleConfirmProposal,
    handleDismissProposal,
    // HS-172-06: suggested sources
    suggestedSources,
    suggestionBusy,
    handleAddSuggestion,
    handleDismissSuggestion,
    // HS-173-04: nudges
    nudges,
    // Actions
    load,
    postRead,
    search,
    openMoment,
    transition,
    openProjectRef,
  } as const;
}

export type ProjectRoomController = ReturnType<typeof useProjectRoomController>;
