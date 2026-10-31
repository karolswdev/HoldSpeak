import { useEffect, useMemo, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch } from "../../lib/api";
import { agentWord, flightLabel, useAgentFlights } from "../agentFlights";
import { openAgentLane, openProjectRoom } from "../shell";
import { useDesk } from "../store";
import { objectByRef } from "../world";
import { normalizeRef } from "../screen/compose";
import { ActionNotice, DotWord, SurfaceWell } from "../surface";
import type { TerminalDescriptor } from "./types";

export interface WorkspaceOverviewProps {
  descriptor: TerminalDescriptor;
  selectedProjectName: string | null;
  onOpenTerminal(): void;
}

function originRef(value: unknown): string | null {
  if (typeof value === "string" && value.includes(":")) return value;
  if (!value || typeof value !== "object") return null;
  const row = value as { kind?: unknown; id?: unknown };
  return typeof row.kind === "string" && typeof row.id === "string" ? `${row.kind}:${row.id}` : null;
}

function stateWords(state: string): string {
  const clean = state.trim().toLowerCase();
  if (!clean || clean === "live" || clean === "working" || clean === "registered") return "Live";
  if (clean === "waiting" || clean === "awaiting_response" || clean === "needs_you") return "Needs you";
  if (clean === "done" || clean === "checked") return "Done";
  if (clean === "expired") return "Launch expired";
  if (clean === "resume_failed" || clean === "failed") return "Launch failed";
  return clean.replaceAll("_", " ");
}

function stateTone(state: string): "info" | "warn" | "ok" | "idle" {
  const clean = state.trim().toLowerCase();
  if (clean === "waiting" || clean === "awaiting_response" || clean === "needs_you") return "warn";
  if (clean === "done" || clean === "checked" || clean === "merged") return "ok";
  if (clean === "expired" || clean === "resume_failed" || clean === "failed") return "warn";
  if (clean === "live" || clean === "working" || clean === "registered") return "info";
  return "idle";
}

function firstLine(value: string): string {
  const line = value.split(/\r?\n/, 1)[0]?.trim() ?? "";
  return line.length > 180 ? `${line.slice(0, 177).trimEnd()}…` : line;
}

/** The selected job landing above the session inventory. It answers what the
 * shell belongs to and the next useful press without repeating Context's
 * complete provenance ledger. */
export function WorkspaceOverview({ descriptor, selectedProjectName, onOpenTerminal }: WorkspaceOverviewProps) {
  const context = descriptor.context;
  const flights = useAgentFlights((state) => state.flights);
  const sessions = useAgentFlights((state) => state.sessions);
  const items = useDesk((state) => state.items);
  const flight = context.launch ? flights.find((row) => row.launchId === context.launch?.id) ?? null : null;
  const session = context.launch ? sessions.find((row) => row.flight?.launchId === context.launch?.id) ?? null : null;
  const briefRef = originRef(context.launch?.origin_ref);
  const [brief, setBrief] = useState<{ title: string; body: string } | null>(null);
  const [briefError, setBriefError] = useState(false);
  const [briefReadNonce, setBriefReadNonce] = useState(0);

  useEffect(() => {
    if (context.launch) void useAgentFlights.getState().load();
  }, [context.launch?.id]);

  useEffect(() => {
    let alive = true;
    setBriefError(false);
    const indexed = briefRef ? objectByRef(items, normalizeRef(briefRef)) : null;
    const indexedBody = indexed && "bodyMarkdown" in indexed.ref ? String(indexed.ref.bodyMarkdown ?? "") : "";
    setBrief(indexed ? { title: indexed.title, body: indexedBody } : null);
    if (!briefRef?.startsWith("note:")) return () => { alive = false; };
    void apiFetch<{ note?: { title?: string; body_markdown?: string } }>(`/api/notes/${encodeURIComponent(briefRef.slice("note:".length))}`)
      .then((answer) => {
        if (!alive) return;
        setBrief({ title: String(answer.note?.title ?? indexed?.title ?? "Brief"), body: String(answer.note?.body_markdown ?? indexedBody) });
      })
      .catch(() => { if (alive) setBriefError(true); });
    return () => { alive = false; };
  }, [briefRef, items, briefReadNonce]);

  const title = useMemo(() => (
    firstLine(brief?.title ?? "")
    || firstLine(flight?.title ?? "")
    || descriptor.label
    || descriptor.session
    || "Terminal workspace"
  ), [brief?.title, descriptor.label, descriptor.session, flight?.title]);
  const project = context.project?.name ?? selectedProjectName;
  const agent = flight ? agentWord(flight.agent) : context.launch ? "Agent" : descriptor.agent !== "pane" ? agentWord(descriptor.agent) : null;
  const status = flight ? (flightLabel(flight) ?? stateWords(flight.state)) : stateWords(context.launch?.state ?? descriptor.state);
  const tone = stateTone(flight?.state ?? context.launch?.state ?? descriptor.state);
  const briefWords = firstLine(brief?.body ?? "");
  const projectLabel = context.project ? "Project" : "Project target";
  const openAgent = context.launch ? () => openAgentLane(context.launch!.id) : null;
  const openProject = context.project ? () => openProjectRoom(context.project!.id) : null;
  // A blocked session without the producer's actual question is still an
  // agent door, not a question we can answer on its behalf.
  const question = session?.question ? firstLine(session.question.trim()) || null : null;
  const primaryAction = question && openAgent ? openAgent : onOpenTerminal;
  const primaryLabel = question && openAgent ? "Answer question" : "Open terminal";

  return <div className="terminals-workspace-overview" data-testid="terminal-job-overview">
    <SurfaceWell head={<span>Selected workspace</span>}>
      <div className="terminals-overview-heading">
        <strong>{title}</strong>
        <DotWord tone={tone} live={tone === "info"}>{status}</DotWord>
      </div>
      {project || agent ? <div className="terminals-overview-facts" role="list" aria-label="Workspace facts">
        {project ? <span className="terminals-overview-fact" role="listitem">
          <span className="terminals-overview-fact-label">{projectLabel}</span>
          {context.project && openProject ? <Button dense variant="ghost" onClick={openProject}>{project}</Button> : <strong>{project}</strong>}
        </span> : null}
        {agent ? <span className="terminals-overview-fact" role="listitem">
          <span className="terminals-overview-fact-label">Agent</span>
          <strong>{agent}</strong>
        </span> : null}
      </div> : null}
      {briefWords ? <p className="terminals-overview-brief">{briefWords}</p> : null}
      {question ? <p className="terminals-overview-question">{question}</p> : null}
      {briefError ? <ActionNotice tone="info">Brief is not available here. The terminal stays open. <Button dense variant="ghost" onClick={() => setBriefReadNonce((value) => value + 1)}>Retry</Button></ActionNotice> : null}
      {!project && !briefWords && !agent ? <p className="terminals-overview-quiet">Shell · No filed job</p> : null}
      <div className="terminals-overview-actions">
        <Button dense variant="primary" onClick={primaryAction}>{primaryLabel}</Button>
        {openAgent && !(question && openAgent) ? <Button dense variant="secondary" onClick={openAgent}>Open agent</Button> : null}
        {question && openAgent ? <Button dense variant="secondary" onClick={onOpenTerminal}>Open terminal</Button> : null}
      </div>
    </SurfaceWell>
  </div>;
}
