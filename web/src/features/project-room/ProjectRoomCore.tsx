// HS-158-05 adoption — the Room face on the desk. Orientation band from
// /room data, focus block, honest absent/degraded states. Existing wings
// (Timeline/Decisions/Search/Ask) keep working unchanged.
import { useState } from "react";
import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import { Button } from "../../components/signal/Signal";
import { MicButton } from "../../desk/components/MicButton";
import { ContextualAssignment } from "../../pages/cores/ContextualAssignment";
import { runAsk, type AskRunResult } from "../../desk/ask";
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
  SurfaceColumns,
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
import { useWindowTitle } from "../../desk/surface/title";
import { readableError } from "../../lib/api";
import type { CoreProps } from "../../pages/cores/core-types";
import type { SinceLastMeetingResponse } from "./model";
import type { RoomSnapshot, RoomSection } from "./model";
import { lifecycleLabel, type ProjectTimelineEntry } from "./model";
import { promoteDecision } from "./api";
import { useProjectRoomController } from "./useProjectRoomController";
import { useReviewController } from "./review/useReviewController";
import { ReviewPosture } from "./review/ReviewPosture";
import type { RoomReviewData } from "./model";
import "./project-room.css";

/* ── sub-components (unchanged from ProjectMemoryCore) ── */

const PROMOTION_TYPES = [
  ["adr", "ADR"],
  ["note", "NOTE"],
  ["decision_announcement", "ANNC"],
] as const;

/** HS-111-06 -- the lifecycle as the etched token it is (audit M2):
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
      const body = await promoteDecision(id, kind, model);
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
        /* The minted artifact is openable material -- the one citation
           chip species carries it (HS-111-05). */
        <CitationChips
          refs={[`artifact:${artifactId}`]}
          onOpen={(ref) => onOpenArtifact?.(ref.slice("artifact:".length))}
        />
      ) : null}
      {detail ? <span className="desk-arm-refusal">{"✕"} {detail}</span> : null}
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
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState<AskRunResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const receipt = result?.groundingReceipt;
  const groundedCount = groundedMatchCount(receipt ?? null);
  const egress = result?.egress
    ? result.egress.scope === "local"
      ? `⌂ ${result.model || "This device"}`
      : result.egress.scope === "mesh"
        ? `⇄ ${result.egress.host || "Paired"}`
        : `→ ${result.egress.host || "Leaves device"}`
    : "Uses assignment";

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
          className={`egress-badge is-${result?.egress?.scope || "local"}`}
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
          <ContextualAssignment
            label="Project"
            capabilityId="ask.answer"
            scope={{
              kind: "subject",
              subject_kind: "project",
              subject_id: projectId,
              capability_id: "ask.answer",
            }}
          />
          <span className="desk-chip quiet">{projectName}</span>
        </div>
      </div>
      {error ? <SurfaceState error={error} onRetry={() => void ask()} /> : null}
      {result ? (
        <div className="project-memory-answer">
          <Material>{result.output}</Material>
          {receipt ? (
            /* HS-111-06 -- the same fact speaks Ask's token (audit M5). */
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

/** HS-111-06 -- the delta as a token slab, never a sentence (audit M6). */
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

/* ── Orientation band (WEB-NOW-001 P1 subset, WEB-LC-001/002) ── */

/** Humanize a machine token for the glass: underscores to spaces,
 *  sentence case. The DOM keeps the machine value in a data- attribute. */
function humanizeToken(raw: string): string {
  return raw.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
}

/** Lifecycle chip for the orientation band — maps lifecycle to a token
 *  with the appropriate tone. */
function OrientationLifecycleChip({ lifecycle }: { lifecycle: string | null }) {
  if (!lifecycle) return null;
  const label = humanizeToken(lifecycle);
  const tone =
    lifecycle === "active" || lifecycle === "in_progress"
      ? "ok"
      : lifecycle === "archived" || lifecycle === "closed"
        ? "danger"
        : undefined;
  return (
    <span className="surface-token" data-tone={tone} data-testid="orientation-lifecycle" data-lifecycle={lifecycle}>
      {label}
    </span>
  );
}

/** Posture fact — separate from lifecycle per WEB-LC-001/002. */
function OrientationPosture({ posture, reason }: { posture: string | null; reason: string | null }) {
  if (!posture) return null;
  const label = humanizeToken(posture);
  return (
    <span className="surface-token" data-testid="orientation-posture" data-posture={posture} title={reason || undefined}>
      {label}
    </span>
  );
}

/** The orientation band: name/purpose/outcome + lifecycle + posture as
 *  separate facts (WEB-LC-001/002). Nothing fabricated when absent (Art VI).
 *
 *  HS-158-05 R2: band label symmetry — both purpose and outcome carry
 *  micro-eyebrows (PURPOSE / OUTCOME) as one deliberate system.
 *  Token-row hierarchy — identity facts left, meta facts quieter right. */
function OrientationBand({ room }: { room: RoomSnapshot }) {
  const { project } = room;
  return (
    <section className="project-room-orientation" data-testid="orientation-band" aria-label="Project orientation">
      <h2 className="project-room-name" data-testid="project-room-name">
        {project.name}
      </h2>
      {project.purpose ? (
        <div className="project-room-purpose" data-testid="orientation-purpose">
          <span className="project-room-eyebrow" data-testid="purpose-eyebrow">PURPOSE</span>
          <p>{project.purpose}</p>
        </div>
      ) : null}
      {project.outcomeText ? (
        <div className="project-room-outcome" data-testid="orientation-outcome">
          <span className="project-room-eyebrow" data-testid="outcome-eyebrow">OUTCOME</span>
          <p>{project.outcomeText}</p>
        </div>
      ) : null}
      <div className="project-room-facts" data-testid="orientation-facts">
        <span className="project-room-facts-identity" data-testid="facts-identity">
          <OrientationLifecycleChip lifecycle={project.lifecycle} />
          <OrientationPosture posture={project.posture} reason={project.postureReason} />
        </span>
        <span className="project-room-facts-meta" data-testid="facts-meta">
          {room.revision > 0 ? (
            <span className="surface-token" data-testid="orientation-revision">
              REV {room.revision}
            </span>
          ) : null}
          {project.updatedAt ? (
            <span className="surface-token" data-testid="orientation-activity">
              {humanTime(project.updatedAt)}
            </span>
          ) : null}
        </span>
      </div>
    </section>
  );
}

/* ── Focus block (WEB-NOW-001: items grouped by kind, honest totals) ── */

function FocusBlock({ room }: { room: RoomSnapshot }) {
  const items = room.items;
  if (items.state === "absent") return null;
  if (items.state === "degraded") {
    return (
      <div data-testid="focus-degraded" data-error-code={items.error_code} title={items.error_code}>
        <SurfaceSection label="Focus">
          <SurfaceState error="Items unavailable right now." />
        </SurfaceSection>
      </div>
    );
  }
  // ok state
  if (items.total === 0) {
    return (
      <div data-testid="focus-block">
        <SurfaceSection label="Focus">
          <SurfaceState
            empty
            emptyLabel="No material yet."
            emptyGlyph={"▤"}
          />
        </SurfaceSection>
      </div>
    );
  }
  // Group focus items by kind
  const grouped: Record<string, typeof items.focus> = {};
  for (const item of items.focus) {
    const kind = item.itemType || "other";
    if (!grouped[kind]) grouped[kind] = [];
    grouped[kind].push(item);
  }
  /** Proper per-kind plural labels — no naive suffix. */
  const PLURAL_LABELS: Record<string, string> = {
    workstream: "Workstreams",
    milestone: "Milestones",
    risk: "Risks",
    dependency: "Dependencies",
    signal: "Signals",
  };
  const typeLabel = (type: string) =>
    PLURAL_LABELS[type] || type[0].toUpperCase() + type.slice(1) + "s";
  return (
    <div data-testid="focus-block">
    <SurfaceSection label="Focus">
      {Object.entries(grouped).map(([kind, kindItems]) => {
        const count = items.totalsByType[kind] ?? kindItems.length;
        return (
          <div key={kind} className="project-room-focus-group">
            <span className="project-room-focus-label">
              <span className="surface-token" data-testid="focus-type-label">
                {typeLabel(kind)}
              </span>
              <span className="project-room-count-chip" data-testid="focus-count-chip">
                {count}
              </span>
            </span>
            <SurfaceRows>
              {kindItems.map((item) => {
                const severityTone =
                  item.severity === "critical" ? "danger"
                  : item.severity === "high" ? "warn"
                  : undefined;
                return (
                  <SurfaceRow
                    key={item.id}
                    title={item.title}
                    meta={
                      <>
                        {item.severity ? (
                          <span
                            className="surface-token"
                            data-tone={severityTone}
                            data-testid="focus-severity"
                            data-severity={item.severity}
                          >
                            {humanizeToken(item.severity)}
                          </span>
                        ) : null}
                        {item.dueAt ? (
                          <span className="project-room-date-token" data-testid="focus-due">
                            <span className="project-room-date-glyph" aria-hidden="true">{"▪"}</span>
                            {item.dueAt}
                          </span>
                        ) : null}
                      </>
                    }
                  />
                );
              })}
            </SurfaceRows>
          </div>
        );
      })}
    </SurfaceSection>
    </div>
  );
}

/* ── Right rail: meetings, resources, changes from the /room projection ── */

function RightRail({ room }: { room: RoomSnapshot }) {
  const { meetings, resources, changes } = room;
  return (
    <div data-testid="project-room-rail">
      {/* Meetings count + latest */}
      {meetings.state === "ok" ? (
        <div className="project-room-rail-section" data-testid="rail-meetings">
          <div className="project-room-rail-label">
            <span className="surface-token">Meetings</span>
            <span className="project-room-count-chip" data-testid="rail-meetings-count">
              {meetings.count}
            </span>
          </div>
          {meetings.latest ? (
            <span className="project-room-rail-value" data-testid="rail-meetings-latest">
              {String((meetings.latest as Record<string, unknown>).title || "Latest")}
            </span>
          ) : (
            <span className="project-room-rail-absent">None yet</span>
          )}
        </div>
      ) : null}

      {/* Resources count + latest */}
      {resources.state === "ok" ? (
        <div className="project-room-rail-section" data-testid="rail-resources">
          <div className="project-room-rail-label">
            <span className="surface-token">Resources</span>
            <span className="project-room-count-chip" data-testid="rail-resources-count">
              {resources.count}
            </span>
          </div>
          {resources.latest ? (
            <span className="project-room-rail-value">
              {String((resources.latest as Record<string, unknown>).title || "Latest")}
            </span>
          ) : (
            <span className="project-room-rail-absent">None yet</span>
          )}
        </div>
      ) : null}

      {/* Recent changes — the projection's changes section */}
      {changes.state === "ok" ? (
        <div className="project-room-rail-section" data-testid="rail-changes">
          <div className="project-room-rail-label">
            <span className="surface-token">Changes</span>
            <span className="project-room-count-chip" data-testid="rail-changes-count">
              {changes.recent.length}
            </span>
          </div>
          {changes.recent.length > 0 ? (
            changes.recent.map((change, i) => (
              <div key={change.id || String(i)} className="project-room-change-row" data-testid="rail-change-row">
                <span>{change.label}</span>
                {change.occurredAt ? (
                  <span className="project-room-date-token">
                    {humanTime(change.occurredAt)}
                  </span>
                ) : null}
              </div>
            ))
          ) : (
            <span className="project-room-rail-absent">No recent changes</span>
          )}
        </div>
      ) : null}
    </div>
  );
}

/* ── Degraded section inline notice ── */

function DegradedNotice({ label, section }: { label: string; section: RoomSection<unknown> }) {
  if (section.state !== "degraded") return null;
  return (
    <p className="project-room-degraded" data-testid={`degraded-${label}`} role="status">
      <span className="surface-token" data-tone="warn">
        {label.toUpperCase()} UNAVAILABLE
      </span>
    </p>
  );
}

/* ── main core ── */

export function ProjectRoomCore({ hero, scope, scopeLabel }: CoreProps) {
  const ctrl = useProjectRoomController(scope, scopeLabel);
  const loading = ctrl.loadStatus === "loading";
  const detailLoading = ctrl.detailStatus === "loading";

  // HS-160-06 — extract the typed review section from the room snapshot.
  // When the section is ok, it carries pending_count/open_review_id/last_accepted_at.
  const reviewData: RoomReviewData | null =
    ctrl.room?.review.state === "ok"
      ? (ctrl.room.review as RoomReviewData & { state: "ok" })
      : null;

  const reviewCtrl = useReviewController(
    ctrl.projectId,
    reviewData,
    () => void ctrl.load(),
  );

  // HS-158-05 — push the scoped Project's name into the window head;
  // null keeps the manifest label (loading / unscoped states).
  const runtimeTitle = ctrl.loadStatus === "ready" && ctrl.projectName !== "Project"
    ? ctrl.projectName
    : null;
  useWindowTitle(runtimeTitle, [runtimeTitle]);

  // HS-111-06 -- the timeline is a filed-archive ledger (audit M3):
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
      <SinceLastMeeting receipt={ctrl.since} />
      <SurfaceState
        loading={detailLoading}
        error={ctrl.error}
        empty={!detailLoading && !ctrl.timeline.length}
        emptyLabel="No project memory yet"
        emptyGlyph={"▤"}
        onRetry={() => void ctrl.load()}
      >
        <SurfaceLedger count={`TIMELINE ${ctrl.timeline.length}`}>
          <ul className="surface-ledger-rows">
            {ctrl.timeline.map((entry) => (
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
                  else ctrl.setView("decisions");
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
      actions={<span className="quiet">{ctrl.decisions.length}</span>}
    >
      <SurfaceState
        loading={detailLoading}
        error={ctrl.error}
        empty={!detailLoading && !ctrl.decisions.length}
        emptyLabel="No decisions recorded"
        emptyGlyph={"✓"}
        onRetry={() => void ctrl.load()}
      >
        <SurfaceRows>
          {ctrl.decisions.map((decision) => {
            const lifecycle = String(decision.lifecycle || "recorded");
            const candidates = ctrl.decisions.filter(
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
                onOpen={() => void ctrl.openMoment(decision)}
                verbs={
                  <>
                    {lifecycle === "recorded" ? (
                      <Button
                        dense
                        loading={ctrl.decisionBusy === decision.id}
                        onClick={() => void ctrl.transition(decision, "accept")}
                      >
                        ACCEPT
                      </Button>
                    ) : null}
                    {lifecycle === "recorded" || lifecycle === "accepted" ? (
                      /* HS-111-06 -- gadget grammar (audit M4): the
                         successor is a CycleGadget, the flip an arming
                         ConfirmVerb; the naked selects died. */
                      <span className="project-memory-supersede">
                        <CycleGadget
                          label={`Successor for ${String(decision.text || decision.id)}`}
                          value={ctrl.successors[String(decision.id)] || ""}
                          options={[
                            { value: "", label: "SUCCESSOR" },
                            ...candidates.map((candidate) => ({
                              value: String(candidate.id),
                              label: String(candidate.text || candidate.id),
                            })),
                          ]}
                          onChange={(next) =>
                            ctrl.setSuccessors((value) => ({
                              ...value,
                              [String(decision.id)]: next,
                            }))
                          }
                        />
                        <ConfirmVerb
                          label="SUPERSEDE"
                          confirmLabel="SUPERSEDE?"
                          disabled={!ctrl.successors[String(decision.id)]}
                          busy={ctrl.decisionBusy === decision.id}
                          onConfirm={() => void ctrl.transition(decision, "supersede")}
                        />
                      </span>
                    ) : null}
                    <DecisionPromotionSlot decision={decision} onOpenArtifact={(id) => ctrl.openProjectRef(`artifact:${id}`)} />
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
            draftScope={`project-memory-search-${ctrl.projectId}`}
            onText={(text) =>
              ctrl.setSearchQuery((value) => (value ? `${value} ${text}` : text))
            }
          />
          <input
            type="search"
            aria-label="Search this project"
            value={ctrl.searchQuery}
            placeholder="Search"
            onChange={(event) => ctrl.setSearchQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") void ctrl.search();
            }}
          />
          <Button
            dense
            variant="primary"
            loading={ctrl.searching}
            disabled={!ctrl.searchQuery.trim()}
            onClick={() => void ctrl.search()}
          >
            Search
          </Button>
        </div>
      </div>
      <SurfaceState
        loading={ctrl.searching}
        error={ctrl.error}
        empty={ctrl.searched && !ctrl.searchHits.length}
        emptyLabel="No matches in this project"
        emptyGlyph={"⌕"}
        onRetry={() => void ctrl.search()}
      >
        <SurfaceRows>
          {ctrl.searchHits.map((hit) => (
            <SurfaceRow
              key={String(hit.source_ref)}
              title={String(hit.title || sourceLabel(String(hit.source_ref)))}
              detail={String(hit.snippet || "")}
              meta={
                <span className="desk-chip quiet">
                  {String(hit.kind || "Memory")}
                </span>
              }
              onOpen={() => ctrl.openProjectRef(String(hit.source_ref))}
            />
          ))}
        </SurfaceRows>
      </SurfaceState>
    </SurfaceSection>
  );

  const verbs = (
    <>
      {/* HS-160-06: WEB-NOW-002 — review verb when pending_count > 0 */}
      {reviewCtrl.primaryVerb ? (
        <Button
          dense
          variant="primary"
          loading={reviewCtrl.loading}
          onClick={() => void reviewCtrl.enterReview()}
          data-testid="review-verb"
        >
          {reviewCtrl.primaryVerb}
        </Button>
      ) : null}
      <Button dense variant="ghost" onClick={() => void ctrl.load()}>
        Refresh
      </Button>
    </>
  );
  if (!ctrl.projectId)
    return <SurfaceState empty emptyLabel="Open a Project" emptyGlyph={"▤"} />;

  const readToken = (() => {
    if (!ctrl.readAt) return "";
    const date = new Date(ctrl.readAt);
    const pad = (n: number) => String(n).padStart(2, "0");
    return ` · READ ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
  })();

  // HS-160-06 — when the review posture is active, it replaces the
  // entire working field (same window, NO modal — WEB-IA-003).
  if (reviewCtrl.posture === "active") {
    return (
      <>
        {hero ? hero(verbs) : <SurfaceVerbs />}
        {ctrl.room ? <OrientationBand room={ctrl.room} /> : null}
        <ReviewPosture ctrl={reviewCtrl} />
      </>
    );
  }

  return (
    <>
      {hero ? (
        hero(verbs)
      ) : (
        /* When the room is loaded, the orientation band carries the
           identity and lifecycle — no need to repeat the name here
           (defect 4: de-duplication). */
        <SurfaceVerbs />
      )}
      {/* Orientation band renders before slow sections (WEB-STA-001) */}
      {ctrl.room ? (
        <>
          {/* Orientation band spans full width, always */}
          <OrientationBand room={ctrl.room} />
          {/* HS-158-05 R2: two-column desktop composition via SurfaceColumns.
              At 560px+ container width the focus block is left (~3fr),
              the right rail (~2fr) carries meetings/resources/changes.
              Below 560px everything stacks as today. */}
          <SurfaceColumns
            main={
              <>
                <FocusBlock room={ctrl.room} />
                {/* Degraded sections show inline (WEB-STA-002, never overlay) */}
                <DegradedNotice label="meetings" section={ctrl.room.meetings} />
                <DegradedNotice label="resources" section={ctrl.room.resources} />
                <DegradedNotice label="changes" section={ctrl.room.changes} />
                {/* Absent sections render NOTHING (Art VI) — no teaser placeholders */}
              </>
            }
            side={<RightRail room={ctrl.room} />}
          />
        </>
      ) : loading ? (
        <SurfaceState loading />
      ) : null}
      <div className="project-memory-core" data-view={ctrl.view}>
        {ctrl.view === "timeline" ? (
          timelineFace
        ) : ctrl.view === "decisions" ? (
          decisionsFace
        ) : ctrl.view === "search" ? (
          searchFace
        ) : (
          <ProjectAsk
            projectId={ctrl.projectId}
            projectName={ctrl.projectName}
            onOpenRef={ctrl.openProjectRef}
          />
        )}
      </div>
      {/* HS-129-05 -- the read fact and Refresh verb use shared foot slots. */}
      <SurfaceFooter
        receipt={
          <span className="surface-footer-receipt-line" role="status">
            {`PROJECT ${ctrl.projectName}${readToken}`}
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
