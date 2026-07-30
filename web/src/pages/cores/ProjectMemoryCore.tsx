// HS-109-05 — one Project, opened as its long memory in the Desk grammar.
import { useEffect, useMemo, useState } from "react";
import {
  Button,
  InlineMessage,
  StatusPill,
} from "../../components/signal/Signal";
import { MicButton } from "../../desk/components/MicButton";
import { RunsOnPicker } from "../../desk/components/RunsOnPicker";
import { runAsk, type AskRunResult } from "../../desk/ask";
import { useDesk } from "../../desk/store";
import { openPrimitive, openSurfaceOr } from "../../desk/shell";
import { Material } from "../../desk/surface/Material";
import {
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceState,
  SurfaceVerbs,
} from "../../desk/surface/Surface";
import { humanTime } from "../../desk/surface/format";
import { SurfaceWings, useWindowWings } from "../../desk/surface/wings";
import { apiFetch, readableError, type JsonRecord } from "../../lib/api";
import type { CoreProps } from "./ActivityCore";

const WINGS = [
  { id: "timeline", label: "Timeline" },
  { id: "decisions", label: "Decisions" },
  { id: "search", label: "Search" },
  { id: "ask", label: "Ask" },
];

export type ProjectTimelineEntry = {
  id: string;
  kind: "meeting" | "decision" | "artifact";
  title: string;
  occurredAt: string;
  row: JsonRecord;
};

/** Pure composition seam pinned by the timeline tests. */
export function composeProjectTimeline(
  meetings: JsonRecord[],
  decisions: JsonRecord[],
  artifacts: JsonRecord[],
): ProjectTimelineEntry[] {
  const promoted = artifacts.filter(
    (row) =>
      row.status === "promoted" ||
      row.promotion_state === "promoted" ||
      Boolean(row.promoted_at),
  );
  return [
    ...meetings.map((row) => ({
      id: String(row.id),
      kind: "meeting" as const,
      title: String(row.title || "Meeting"),
      occurredAt: String(row.started_at || row.created_at || ""),
      row,
    })),
    ...decisions.map((row) => ({
      id: String(row.id),
      kind: "decision" as const,
      title: String(row.text || "Decision"),
      occurredAt: String(row.decided_at || row.created_at || ""),
      row,
    })),
    ...promoted.map((row) => ({
      id: String(row.id),
      kind: "artifact" as const,
      title: String(row.title || row.artifact_type || "Artifact"),
      occurredAt: String(row.promoted_at || row.created_at || ""),
      row,
    })),
  ].sort((a, b) => b.occurredAt.localeCompare(a.occurredAt));
}

export function lifecycleLabel(row: JsonRecord): string {
  const lifecycle = String(row.lifecycle || "recorded");
  if (lifecycle === "superseded" && row.superseded_by)
    return `Superseded → ${String(row.superseded_by)}`;
  return lifecycle[0].toUpperCase() + lifecycle.slice(1);
}

export function LifecycleChip({ row }: { row: JsonRecord }) {
  const lifecycle = String(row.lifecycle || "recorded");
  const tone =
    lifecycle === "accepted"
      ? "success"
      : lifecycle === "rejected"
        ? "error"
        : lifecycle === "superseded"
          ? "neutral"
          : "warning";
  return <StatusPill tone={tone}>{lifecycleLabel(row)}</StatusPill>;
}

export function groundedMatchCount(
  receipt: { matchedCount: number; overflowCount: number } | null,
): number {
  return receipt
    ? Math.max(0, receipt.matchedCount - receipt.overflowCount)
    : 0;
}

function sourceLabel(ref: string): string {
  const [kind, ...rest] = ref.split(":");
  return `${kind[0]?.toUpperCase() || ""}${kind.slice(1)} · ${rest.join(":")}`;
}

function openSourceRef(ref: string) {
  if (ref.startsWith("meeting:")) {
    openSurfaceOr("review-meetings", "/history", ref);
    return;
  }
  openPrimitive(ref);
}

export function CitationChips({
  refs,
  onOpen = openSourceRef,
}: {
  refs: string[];
  onOpen?: (ref: string) => void;
}) {
  if (!refs.length) return null;
  return (
    <div className="project-memory-citations" aria-label="Citations">
      {refs.map((ref) => (
        <button
          key={ref}
          type="button"
          className="desk-chip quiet"
          onClick={() => onOpen(ref)}
        >
          {sourceLabel(ref)}
        </button>
      ))}
    </div>
  );
}

const PROMOTION_TYPES = [
  ["adr", "ADR"],
  ["note", "Note"],
  ["decision_announcement", "Announcement"],
] as const;

/** The HS-109-03 promote verbs: deterministic (the gesture is the approval)
 * or a model draft through the registered inference.run. */
export function DecisionPromotionSlot({
  decision,
  onOpenArtifact,
}: {
  decision: JsonRecord;
  onOpenArtifact?(artifactId: string): void;
}) {
  const [kind, setKind] = useState<string>("adr");
  const [busy, setBusy] = useState("");
  const [artifactId, setArtifactId] = useState("");
  const [detail, setDetail] = useState("");
  if (String(decision.lifecycle) !== "accepted") return null;
  const id = String(decision.id);
  const promote = async (model: boolean) => {
    setBusy(model ? "model" : "direct");
    setDetail("");
    try {
      const path = model
        ? `/api/decisions/${encodeURIComponent(id)}/promote/${kind}/draft-with-model`
        : `/api/decisions/${encodeURIComponent(id)}/promote/${kind}`;
      const body = await apiFetch<JsonRecord>(path, {
        method: "POST",
        json: model ? {} : undefined,
      });
      const artifact = (body.artifact ?? {}) as JsonRecord;
      setArtifactId(String(artifact.id ?? ""));
    } catch (reason) {
      setDetail(readableError(reason));
    } finally {
      setBusy("");
    }
  };
  return (
    <span className="decision-promotion-slot">
      <label className="visually-hidden" htmlFor={`promo-kind-${id}`}>
        Artifact kind
      </label>
      <select
        id={`promo-kind-${id}`}
        className="desk-select dense"
        value={kind}
        onChange={(event) => setKind(event.target.value)}
      >
        {PROMOTION_TYPES.map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>
      <Button dense variant="ghost" loading={busy === "direct"}
              onClick={() => void promote(false)}>
        Promote
      </Button>
      <Button dense variant="ghost" loading={busy === "model"}
              onClick={() => void promote(true)}>
        Draft with model
      </Button>
      {artifactId ? (
        <button type="button" className="desk-chip quiet"
                onClick={() => onOpenArtifact?.(artifactId)}>
          {`artifact:${artifactId.slice(0, 18)}`}
        </button>
      ) : null}
      {detail ? <span className="desk-caption">{detail}</span> : null}
    </span>
  );
}

function ProjectAsk({
  projectId,
  projectName,
  onOpenRef,
}: {
  projectId: string;
  projectName: string;
  onOpenRef(ref: string): void;
}) {
  const targets = useDesk((state) => state.inferenceTargets);
  const [targetId, setTargetId] = useState("this_machine");
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState<AskRunResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const target = targets.find((item) => item.id === targetId);
  const receipt = result?.groundingReceipt;
  const groundedCount = groundedMatchCount(receipt ?? null);
  const egress = result?.egress
    ? result.egress.scope === "local"
      ? `⌂ ${result.model || "This device"}`
      : result.egress.scope === "mesh"
        ? `⇄ ${result.egress.host || "Paired"}`
        : `→ ${result.egress.host || "Leaves device"}`
    : target?.boundary === "same_device"
      ? `⌂ ${target.name}`
      : `→ ${target?.name || "This device"}`;

  const ask = async () => {
    if (!prompt.trim() || busy) return;
    setBusy(true);
    setError("");
    const answer = await runAsk({
      prompt: prompt.trim(),
      lens: "Project",
      context: [
        {
          id: projectId,
          kind: "project",
          ref: `project:${projectId}`,
          title: projectName,
        },
      ],
      inferenceTargetId: targetId,
      grounding: {
        meeting_ids: [],
        artifact_ids: [],
        refs: [`project:${projectId}`],
        expand: "summary",
      },
    });
    setBusy(false);
    if (!answer.ok) {
      setError(answer.output);
      return;
    }
    setResult(answer);
  };

  return (
    <SurfaceSection
      label="Ask this project"
      actions={
        <span
          className={`egress-badge is-${result?.egress?.scope || (target?.boundary === "same_device" ? "local" : "cloud")}`}
        >
          {egress}
        </span>
      }
    >
      <div className="desk-chat-well project-memory-ask">
        <div className="desk-chat-composer">
          <MicButton
            draftScope={`project-memory-ask-${projectId}`}
            onText={(text) =>
              setPrompt((value) => (value ? `${value} ${text}` : text))
            }
          />
          <textarea
            rows={3}
            aria-label="Ask this project"
            value={prompt}
            placeholder="Ask"
            onChange={(event) => setPrompt(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void ask();
              }
            }}
          />
          <Button
            dense
            variant="primary"
            loading={busy}
            disabled={!prompt.trim()}
            onClick={() => void ask()}
          >
            Ask
          </Button>
        </div>
        <div className="desk-chat-well-foot">
          <RunsOnPicker
            targets={targets}
            selectedId={targetId}
            onChange={setTargetId}
            disabled={busy}
          />
          <span className="desk-chip quiet">{projectName}</span>
        </div>
      </div>
      {error ? <InlineMessage tone="error">{error}</InlineMessage> : null}
      {result ? (
        <div className="project-memory-answer">
          <Material>{result.output}</Material>
          {receipt ? (
            <p className="quiet project-memory-grounded">
              Grounded on {groundedCount} of {receipt.matchedCount} matches
            </p>
          ) : null}
          <CitationChips refs={receipt?.sourceRefs || []} onOpen={onOpenRef} />
        </div>
      ) : null}
    </SurfaceSection>
  );
}

function SinceLastMeeting({ receipt }: { receipt: JsonRecord }) {
  const since = receipt.since_last_meeting as JsonRecord | null | undefined;
  if (!receipt.current_meeting)
    return <p className="project-memory-since quiet">No project meetings</p>;
  if (!since)
    return <p className="project-memory-since quiet">First project meeting</p>;
  const previous = (since.previous_meeting || {}) as JsonRecord;
  const changed =
    ((since.new_decisions as unknown[]) || []).length +
    ((since.new_actions as unknown[]) || []).length +
    ((since.closed_actions as unknown[]) || []).length;
  return (
    <p className="project-memory-since">
      <strong>
        Since {String(previous.title || previous.id || "previous meeting")}
      </strong>
      <span>{changed ? `${changed} changes` : "No changes"}</span>
    </p>
  );
}

export function ProjectMemoryCore({ hero, scope, scopeLabel }: CoreProps) {
  const projectId = scope?.startsWith("project:")
    ? scope.slice("project:".length)
    : "";
  const [view, setView] = useState("timeline");
  const [project, setProject] = useState<JsonRecord>({});
  const [meetings, setMeetings] = useState<JsonRecord[]>([]);
  const [decisions, setDecisions] = useState<JsonRecord[]>([]);
  const [artifacts, setArtifacts] = useState<JsonRecord[]>([]);
  const [since, setSince] = useState<JsonRecord>({});
  const [loading, setLoading] = useState(Boolean(projectId));
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchHits, setSearchHits] = useState<JsonRecord[]>([]);
  const [searched, setSearched] = useState(false);
  const [searching, setSearching] = useState(false);
  const [decisionBusy, setDecisionBusy] = useState("");
  const [successors, setSuccessors] = useState<Record<string, string>>({});

  useWindowWings(
    <SurfaceWings wings={WINGS} active={view} onChange={setView} />,
    [view],
  );

  const load = async () => {
    if (!projectId) return;
    setLoading(true);
    setError("");
    try {
      const encoded = encodeURIComponent(projectId);
      const [projectBody, meetingBody, decisionBody, artifactBody, sinceBody] =
        await Promise.all([
          apiFetch<JsonRecord>(`/api/projects/${encoded}`),
          apiFetch<JsonRecord>(`/api/projects/${encoded}/meetings?limit=200`),
          apiFetch<JsonRecord>(
            `/api/decisions?project_id=${encoded}&limit=500`,
          ),
          apiFetch<JsonRecord>(`/api/projects/${encoded}/artifacts`),
          apiFetch<JsonRecord>(`/api/projects/${encoded}/since-last-meeting`),
        ]);
      setProject(projectBody);
      setMeetings((meetingBody.meetings as JsonRecord[]) || []);
      setDecisions((decisionBody.decisions as JsonRecord[]) || []);
      setArtifacts((artifactBody.artifacts as JsonRecord[]) || []);
      setSince(sinceBody);
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [projectId]);

  const timeline = useMemo(
    () => composeProjectTimeline(meetings, decisions, artifacts),
    [meetings, decisions, artifacts],
  );
  const projectName = String(project.name || scopeLabel || "Project");

  const openMoment = async (decision: JsonRecord) => {
    try {
      const body = await apiFetch<JsonRecord>(
        `/api/decisions/${encodeURIComponent(String(decision.id))}/moment`,
      );
      const moment = (body.moment || {}) as JsonRecord;
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
    decision: JsonRecord,
    action: "accept" | "supersede",
  ) => {
    const id = String(decision.id);
    const successor = successors[id];
    if (action === "supersede" && !successor) return;
    setDecisionBusy(id);
    setError("");
    try {
      const body = await apiFetch<JsonRecord>(
        `/api/decisions/${encodeURIComponent(id)}/${action}`,
        {
          method: "POST",
          json: action === "supersede" ? { superseded_by: successor } : {},
        },
      );
      const updated = body.decision as JsonRecord;
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
      setView("decisions");
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
      const params = new URLSearchParams({
        query: searchQuery.trim(),
        project_id: projectId,
      });
      const body = await apiFetch<JsonRecord>(`/api/memory/search?${params}`);
      setSearchHits((body.hits as JsonRecord[]) || []);
    } catch (reason) {
      setSearchHits([]);
      setError(readableError(reason));
    } finally {
      setSearching(false);
    }
  };

  const timelineFace = (
    <SurfaceSection
      label="Timeline"
      actions={<span className="quiet">{timeline.length}</span>}
    >
      <SinceLastMeeting receipt={since} />
      <SurfaceState
        loading={loading}
        error={error}
        empty={!timeline.length}
        emptyLabel="No project memory yet"
        emptyGlyph="▤"
        onRetry={() => void load()}
      >
        <SurfaceRows>
          {timeline.map((entry) => (
            <SurfaceRow
              key={`${entry.kind}:${entry.id}`}
              glyph={
                entry.kind === "meeting"
                  ? "▣"
                  : entry.kind === "decision"
                    ? "✓"
                    : "◇"
              }
              title={entry.title}
              detail={`${entry.kind[0].toUpperCase()}${entry.kind.slice(1)} · ${humanTime(entry.occurredAt)}`}
              meta={
                entry.kind === "decision" ? (
                  <LifecycleChip row={entry.row} />
                ) : undefined
              }
              onOpen={() => {
                if (entry.kind === "meeting")
                  openSurfaceOr(
                    "review-meetings",
                    "/history",
                    `meeting:${entry.id}`,
                  );
                else if (entry.kind === "artifact")
                  openPrimitive(`artifact:${entry.id}`);
                else setView("decisions");
              }}
            />
          ))}
        </SurfaceRows>
      </SurfaceState>
    </SurfaceSection>
  );

  const decisionsFace = (
    <SurfaceSection
      label="Decisions"
      actions={<span className="quiet">{decisions.length}</span>}
    >
      <SurfaceState
        loading={loading}
        error={error}
        empty={!decisions.length}
        emptyLabel="No decisions recorded"
        emptyGlyph="✓"
        onRetry={() => void load()}
      >
        <SurfaceRows>
          {decisions.map((decision) => {
            const lifecycle = String(decision.lifecycle || "recorded");
            const candidates = decisions.filter(
              (row) =>
                row.id !== decision.id &&
                row.lifecycle !== "rejected" &&
                row.lifecycle !== "superseded",
            );
            return (
              <SurfaceRow
                key={String(decision.id)}
                title={String(decision.text || "Decision")}
                detail={String(
                  decision.rationale || humanTime(decision.decided_at) || "",
                )}
                meta={<LifecycleChip row={decision} />}
                onOpen={() => void openMoment(decision)}
                verbs={
                  <>
                    {lifecycle === "recorded" ? (
                      <Button
                        dense
                        loading={decisionBusy === decision.id}
                        onClick={() => void transition(decision, "accept")}
                      >
                        Accept
                      </Button>
                    ) : null}
                    {lifecycle === "recorded" || lifecycle === "accepted" ? (
                      <span className="project-memory-supersede">
                        <label>
                          <span className="sr-only">Successor</span>
                          <select
                            aria-label={`Successor for ${String(decision.text || decision.id)}`}
                            value={successors[String(decision.id)] || ""}
                            onChange={(event) =>
                              setSuccessors((value) => ({
                                ...value,
                                [String(decision.id)]: event.target.value,
                              }))
                            }
                          >
                            <option value="">Successor</option>
                            {candidates.map((candidate) => (
                              <option
                                key={String(candidate.id)}
                                value={String(candidate.id)}
                              >
                                {String(candidate.text || candidate.id)}
                              </option>
                            ))}
                          </select>
                        </label>
                        <Button
                          dense
                          variant="ghost"
                          disabled={!successors[String(decision.id)]}
                          loading={decisionBusy === decision.id}
                          onClick={() => void transition(decision, "supersede")}
                        >
                          Supersede
                        </Button>
                      </span>
                    ) : null}
                    <DecisionPromotionSlot decision={decision} onOpenArtifact={(id) => openProjectRef(`artifact:${id}`)} />
                  </>
                }
              />
            );
          })}
        </SurfaceRows>
      </SurfaceState>
    </SurfaceSection>
  );

  const searchFace = (
    <SurfaceSection label="Search this project">
      <div className="desk-chat-well project-memory-search">
        <div className="desk-chat-composer">
          <MicButton
            draftScope={`project-memory-search-${projectId}`}
            onText={(text) =>
              setSearchQuery((value) => (value ? `${value} ${text}` : text))
            }
          />
          <input
            type="search"
            aria-label="Search this project"
            value={searchQuery}
            placeholder="Search"
            onChange={(event) => setSearchQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") void search();
            }}
          />
          <Button
            dense
            variant="primary"
            loading={searching}
            disabled={!searchQuery.trim()}
            onClick={() => void search()}
          >
            Search
          </Button>
        </div>
      </div>
      <SurfaceState
        loading={searching}
        error={error}
        empty={searched && !searchHits.length}
        emptyLabel="No matches in this project"
        emptyGlyph="⌕"
        onRetry={() => void search()}
      >
        <SurfaceRows>
          {searchHits.map((hit) => (
            <SurfaceRow
              key={String(hit.source_ref)}
              title={String(hit.title || sourceLabel(String(hit.source_ref)))}
              detail={String(hit.snippet || "")}
              meta={
                <span className="desk-chip quiet">
                  {String(hit.kind || "Memory")}
                </span>
              }
              onOpen={() => openProjectRef(String(hit.source_ref))}
            />
          ))}
        </SurfaceRows>
      </SurfaceState>
    </SurfaceSection>
  );

  const verbs = (
    <Button dense variant="ghost" onClick={() => void load()}>
      Refresh
    </Button>
  );
  if (!projectId)
    return <SurfaceState empty emptyLabel="Open a Project" emptyGlyph="▤" />;

  return (
    <>
      {hero ? (
        hero(verbs)
      ) : (
        <SurfaceVerbs status={projectName}>{verbs}</SurfaceVerbs>
      )}
      <div className="project-memory-core" data-view={view}>
        {view === "timeline" ? (
          timelineFace
        ) : view === "decisions" ? (
          decisionsFace
        ) : view === "search" ? (
          searchFace
        ) : (
          <ProjectAsk
            projectId={projectId}
            projectName={projectName}
            onOpenRef={openProjectRef}
          />
        )}
      </div>
    </>
  );
}
