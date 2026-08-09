import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
// HS-109-05 — one Project, opened as its long memory in the Desk grammar.
// HS-111-06 (audit §3.5): the filed archive — a ledger timeline, lifecycle
// as surface-tokens (the StatusPill species died), decision verbs in the
// gadget grammar, the grounding receipt speaking Ask's token, and the one
// footer receipt bar.
import { useEffect, useMemo, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { MicButton } from "../../desk/components/MicButton";
import { RunsOnPicker } from "../../desk/components/RunsOnPicker";
import { runAsk, type AskRunResult } from "../../desk/ask";
import { useDesk } from "../../desk/store";
import { openPrimitive, openSurfaceOr } from "../../desk/shell";
import {
  CitationChips,
  groundedMatchCount,
  openSourceRef,
  sourceLabel,
} from "../../desk/surface/citations";
import { Material } from "../../desk/surface/Material";
import {
  ConfirmVerb,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceState,
  SurfaceVerbs,
} from "../../desk/surface/Surface";
import { CycleGadget } from "../../desk/surface/gadgets";
import { humanTime } from "../../desk/surface/format";
import { useCoreWings } from "./core-hooks";
import { apiFetch, readableError } from "../../lib/api";
import type {
  CoreProps,
  ProjectResponse,
  ProjectMeetingsResponse,
  ProjectDecisionsResponse,
  ProjectArtifactsResponse,
  SinceLastMeetingResponse,
  DecisionMomentResponse,
  DecisionTransitionResponse,
  DecisionPromoteResponse,
  MemorySearchResponse,
} from "./core-types";

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
  row: Record<string, unknown>;
};

/** Pure composition seam pinned by the timeline tests. */
export function composeProjectTimeline(
  meetings: Record<string, unknown>[],
  decisions: Record<string, unknown>[],
  artifacts: Record<string, unknown>[],
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

export function lifecycleLabel(row: Record<string, unknown>): string {
  const lifecycle = String(row.lifecycle || "recorded");
  if (lifecycle === "superseded") return "Superseded";
  return lifecycle[0].toUpperCase() + lifecycle.slice(1);
}

/** HS-111-06 — the lifecycle as the etched token it is (audit M2):
 * `lifecycleLabel()`'s text is test-locked; only the shell changed. */
export function LifecycleChip({ row }: { row: Record<string, unknown> }) {
  const lifecycle = String(row.lifecycle || "recorded");
  const tone =
    lifecycle === "accepted"
      ? "ok"
      : lifecycle === "rejected"
        ? "danger"
        : undefined;
  return (
    <span className="surface-token" data-tone={tone}>
      {lifecycleLabel(row)}
    </span>
  );
}

const PROMOTION_TYPES = [
  ["adr", "ADR"],
  ["note", "NOTE"],
  ["decision_announcement", "ANNC"],
] as const;

/** The HS-109-03 promote verbs: deterministic (the gesture is the approval)
 * or a model draft through the registered inference.run. */
export function DecisionPromotionSlot({
  decision,
  onOpenArtifact,
}: {
  decision: Record<string, unknown>;
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
      const body = await apiFetch<DecisionPromoteResponse>(path, {
        method: "POST",
        json: model ? {} : undefined,
      });
      const artifact = body.artifact ?? {};
      setArtifactId(String(artifact.id ?? ""));
    } catch (reason) {
      setDetail(readableError(reason));
    } finally {
      setBusy("");
    }
  };
  return (
    <span className="decision-promotion-slot">
      <CycleGadget
        label="Artifact kind"
        value={kind}
        options={PROMOTION_TYPES.map(([value, label]) => ({
          value,
          label,
        }))}
        onChange={setKind}
      />
      <Button dense variant="ghost" loading={busy === "direct"}
              onClick={() => void promote(false)}>
        PROMOTE
      </Button>
      <Button dense variant="ghost" loading={busy === "model"}
              onClick={() => void promote(true)}>
        DRAFT WITH MODEL
      </Button>
      {artifactId ? (
        /* The minted artifact is openable material — the one citation
           chip species carries it (HS-111-05). */
        <CitationChips
          refs={[`artifact:${artifactId}`]}
          onOpen={(ref) => onOpenArtifact?.(ref.slice("artifact:".length))}
        />
      ) : null}
      {detail ? <span className="desk-arm-refusal">✕ {detail}</span> : null}
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
      {error ? <SurfaceState error={error} onRetry={() => void ask()} /> : null}
      {result ? (
        <div className="project-memory-answer">
          <Material>{result.output}</Material>
          {receipt ? (
            /* HS-111-06 — the same fact speaks Ask's token (audit M5). */
            <p className="desk-ask-grounded">
              GROUNDED ON {groundedCount} OF {receipt.matchedCount}
            </p>
          ) : null}
          <CitationChips refs={receipt?.sourceRefs || []} onOpen={onOpenRef} />
        </div>
      ) : null}
    </SurfaceSection>
  );
}

/** HS-111-06 — the delta as a token slab, never a sentence (audit M6). */
function SinceLastMeeting({ receipt }: { receipt: SinceLastMeetingResponse }) {
  const since = receipt.since_last_meeting;
  if (!receipt.current_meeting)
    return (
      <p className="project-memory-since">
        <span className="surface-token">MEETINGS 0</span>
      </p>
    );
  if (!since)
    return (
      <p className="project-memory-since">
        <span className="surface-token">FIRST MEETING</span>
      </p>
    );
  const previous = since.previous_meeting || {};
  const decisions = (since.new_decisions || []).length;
  const actions = (since.new_actions || []).length;
  const closed = (since.closed_actions || []).length;
  const delta = [
    decisions ? `+${decisions} DEC` : "",
    actions ? `+${actions} ACT` : "",
    closed ? `${closed} CLOSED` : "",
  ]
    .filter(Boolean)
    .join(" · ");
  return (
    <p className="project-memory-since">
      <span className="surface-token">
        Since {String(previous.title || previous.id || "previous meeting")}
      </span>
      <span className="surface-token">{delta || "DELTA 0"}</span>
    </p>
  );
}

export function ProjectMemoryCore({ hero, scope, scopeLabel }: CoreProps) {
  const projectId = scope?.startsWith("project:")
    ? scope.slice("project:".length)
    : "";
  const wings = useCoreWings(WINGS, "timeline");
  const [project, setProject] = useState<Record<string, unknown>>({});
  const [meetings, setMeetings] = useState<Record<string, unknown>[]>([]);
  const [decisions, setDecisions] = useState<Record<string, unknown>[]>([]);
  const [artifacts, setArtifacts] = useState<Record<string, unknown>[]>([]);
  const [since, setSince] = useState<SinceLastMeetingResponse>({});
  const [loading, setLoading] = useState(Boolean(projectId));
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
    setLoading(true);
    setError("");
    try {
      const encoded = encodeURIComponent(projectId);
      const [projectBody, meetingBody, decisionBody, artifactBody, sinceBody] =
        await Promise.all([
          apiFetch<ProjectResponse>(`/api/projects/${encoded}`),
          apiFetch<ProjectMeetingsResponse>(`/api/projects/${encoded}/meetings?limit=200`),
          apiFetch<ProjectDecisionsResponse>(
            `/api/decisions?project_id=${encoded}&limit=500`,
          ),
          apiFetch<ProjectArtifactsResponse>(`/api/projects/${encoded}/artifacts`),
          apiFetch<SinceLastMeetingResponse>(`/api/projects/${encoded}/since-last-meeting`),
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

  const openMoment = async (decision: Record<string, unknown>) => {
    try {
      const body = await apiFetch<DecisionMomentResponse>(
        `/api/decisions/${encodeURIComponent(String(decision.id))}/moment`,
      );
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
      const body = await apiFetch<DecisionTransitionResponse>(
        `/api/decisions/${encodeURIComponent(id)}/${action}`,
        {
          method: "POST",
          json: action === "supersede" ? { superseded_by: successor } : {},
        },
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
      const params = new URLSearchParams({
        query: searchQuery.trim(),
        project_id: projectId,
      });
      const body = await apiFetch<MemorySearchResponse>(`/api/memory/search?${params}`);
      setSearchHits(body.hits || []);
    } catch (reason) {
      setSearchHits([]);
      setError(readableError(reason));
    } finally {
      setSearching(false);
    }
  };

  // HS-111-06 — the timeline is a filed-archive ledger (audit M3):
  // fixed time column, mono kind tokens, open-in-place as before.
  // The composition (`composeProjectTimeline`) is untouched.
  const kindToken: Record<ProjectTimelineEntry["kind"], string> = {
    meeting: "MTG",
    decision: "DEC",
    artifact: "ART",
  };
  const ledgerTime = (iso: string): string => {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return "";
    const pad = (n: number) => String(n).padStart(2, "0");
    return `${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
  };
  const timelineFace = (
    <SurfaceSection label="Timeline">
      <SinceLastMeeting receipt={since} />
      <SurfaceState
        loading={loading}
        error={error}
        empty={!timeline.length}
        emptyLabel="No project memory yet"
        emptyGlyph="▤"
        onRetry={() => void load()}
      >
        <SurfaceLedger count={`TIMELINE ${timeline.length}`}>
          <ul className="surface-ledger-rows">
            {timeline.map((entry) => (
              <SurfaceLedgerRow
                key={`${entry.kind}:${entry.id}`}
                time={ledgerTime(entry.occurredAt)}
                primary={
                  <>
                    <span className="surface-token">
                      {kindToken[entry.kind]}
                    </span>{" "}
                    {entry.title}
                  </>
                }
                cells={
                  entry.kind === "decision" ? (
                    <span className="surface-ledger-cell">
                      <LifecycleChip row={entry.row} />
                    </span>
                  ) : undefined
                }
                onToggle={() => {
                  if (entry.kind === "meeting")
                    openSurfaceOr(
                      "review-meetings",
                      "/history",
                      `meeting:${entry.id}`,
                    );
                  else if (entry.kind === "artifact")
                    openPrimitive(`artifact:${entry.id}`);
                  else wings.setView("decisions");
                }}
              />
            ))}
          </ul>
        </SurfaceLedger>
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
                        ACCEPT
                      </Button>
                    ) : null}
                    {lifecycle === "recorded" || lifecycle === "accepted" ? (
                      /* HS-111-06 — gadget grammar (audit M4): the
                         successor is a CycleGadget, the flip an arming
                         ConfirmVerb; the naked selects died. */
                      <span className="project-memory-supersede">
                        <CycleGadget
                          label={`Successor for ${String(decision.text || decision.id)}`}
                          value={successors[String(decision.id)] || ""}
                          options={[
                            { value: "", label: "SUCCESSOR" },
                            ...candidates.map((candidate) => ({
                              value: String(candidate.id),
                              label: String(candidate.text || candidate.id),
                            })),
                          ]}
                          onChange={(next) =>
                            setSuccessors((value) => ({
                              ...value,
                              [String(decision.id)]: next,
                            }))
                          }
                        />
                        <ConfirmVerb
                          label="SUPERSEDE"
                          confirmLabel="SUPERSEDE?"
                          disabled={!successors[String(decision.id)]}
                          busy={decisionBusy === decision.id}
                          onConfirm={() => void transition(decision, "supersede")}
                        />
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

  const readToken = (() => {
    if (!readAt) return "";
    const date = new Date(readAt);
    const pad = (n: number) => String(n).padStart(2, "0");
    return ` · READ ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
  })();

  return (
    <>
      {hero ? (
        hero(verbs)
      ) : (
        <SurfaceVerbs status={projectName} />
      )}
      <div className="project-memory-core" data-view={wings.view}>
        {wings.view === "timeline" ? (
          timelineFace
        ) : wings.view === "decisions" ? (
          decisionsFace
        ) : wings.view === "search" ? (
          searchFace
        ) : (
          <ProjectAsk
            projectId={projectId}
            projectName={projectName}
            onOpenRef={openProjectRef}
          />
        )}
      </div>
      {/* HS-129-05 — the read fact and Refresh verb use shared foot slots. */}
      <SurfaceFooter
        receipt={
          <span className="surface-footer-receipt-line" role="status">
            {`PROJECT ${projectName}${readToken}`}
          </span>
        }
        verbs={
          hero ? null : (
            <span className="surface-footer-verbs-group">{verbs}</span>
          )
        }
      />
    </>
  );
}
