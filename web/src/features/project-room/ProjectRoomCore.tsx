// HS-167-04 — the Room face recomposed on the surface library.
// SurfaceIdentity for the band, SurfaceLedgerRow for focus items,
// MetricStrip + SurfaceStream for the rail, EgressChip for egress.
// Wings (Timeline/Decisions/Search/Ask) keep working unchanged.
import { useRef, useState } from "react";
import {
  SurfaceFooter,
  SurfaceIdentity,
  SurfaceVerbs,
  SurfaceSection,
  SurfaceState,
  SurfaceColumns,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceRows,
  SurfaceRow,
  MetricStrip,
  SurfaceStream,
  SurfaceStreamDay,
  SurfaceStreamEntry,
  ScrollHint,
  ConfirmVerb,
  EgressChip,
  ProvenanceChip,
  StateChip,
  CycleGadget,
  Material,
  CitationChips,
  groundedMatchCount,
  Disclosure,
  sourceLabel,
  humanTime,
  streamDayLabel,
  MicButton,
} from "../../desk/surface";
import { useWindowTitle } from "../../desk/surface/title";
import { Button } from "../../components/signal/Signal";
import { ContextualAssignment } from "../../pages/cores/ContextualAssignment";
import { runAsk, type AskRunResult } from "../../desk/ask";
import { openPrimitive, openSurfaceOr } from "../../desk/shell";
import { readableError } from "../../lib/api";
import type { CoreProps } from "../../pages/cores/core-types";
import type { SinceLastMeetingResponse } from "./model";
import type { RoomSnapshot, RoomSection } from "./model";
import { lifecycleLabel, type ProjectTimelineEntry } from "./model";
import { promoteDecision } from "./api";
import { useProjectRoomController } from "./useProjectRoomController";
import { useReviewController } from "./review/useReviewController";
import { ReviewPosture } from "./review/ReviewPosture";
import { useUpdateController } from "./update/useUpdateController";
import { UpdatePosture } from "./update/UpdatePosture";
import { useStewardController } from "./steward/useStewardController";
import { StewardPosture } from "./steward/StewardPosture";
import type { RoomReviewData } from "./model";
import "./project-room.css";

/* ── sub-components ── */

const PROMOTION_TYPES = [
  ["adr", "ADR"],
  ["note", "NOTE"],
  ["decision_announcement", "ANNC"],
] as const;

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

  const egressScope = result?.egress?.scope || "local";
  const egressHost = result?.egress
    ? result.egress.scope === "local"
      ? result.model || "This device"
      : result.egress.scope === "mesh"
        ? result.egress.host || "Paired"
        : result.egress.host || "Leaves device"
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
        <EgressChip
          label={egressHost}
          scope={egressScope}
          title={`Egress: ${egressHost}`}
        />
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

function humanizeToken(raw: string): string {
  return raw.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
}

/* ── Focus block — SurfaceSection per kind, SurfaceLedgerRow per item ── */

const KIND_EMBLEMS: Record<string, string> = {
  risk: "▲",
  dependency: "⫘",
  milestone: "◆",
  workstream: "◉",
  signal: "⌁",
};

const PLURAL_LABELS: Record<string, string> = {
  workstream: "Workstreams",
  milestone: "Milestones",
  risk: "Risks",
  dependency: "Dependencies",
  signal: "Signals",
};

function typeLabel(type: string) {
  return PLURAL_LABELS[type] || type[0].toUpperCase() + type.slice(1) + "s";
}

function severityChipState(severity: string): "failure" | "warning" | "idle" {
  if (severity === "critical") return "failure";
  if (severity === "high") return "warning";
  return "idle";
}

function isDueWithin7Days(dueAt: string): boolean {
  const due = new Date(dueAt).getTime();
  if (Number.isNaN(due)) return false;
  return due - Date.now() < 7 * 86_400_000 && due - Date.now() > -365 * 86_400_000;
}

function FocusKindSection({ kind, kindItems, count }: { kind: string; kindItems: RoomSnapshot["items"]["focus"]; count: number }) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const emblem = KIND_EMBLEMS[kind] ?? "●";
  return (
    <SurfaceSection label={`${typeLabel(kind).toUpperCase()} ${count}`}>
      <span data-testid="focus-type-label" hidden>{typeLabel(kind)}</span>
      <span data-testid="focus-count-chip" hidden>{count}</span>
      <ScrollHint axis="y" scrollRef={scrollRef}>
        <div ref={scrollRef}>
          <SurfaceLedger count="" cols="room">
            <ul className="surface-ledger-rows">
              {kindItems.map((item) => {
                const dueWarn = item.dueAt ? isDueWithin7Days(item.dueAt) : false;
                return (
                  <SurfaceLedgerRow
                    key={item.id}
                    lead={emblem}
                    primary={item.title}
                    time={item.createdAt ? humanTime(item.createdAt) : ""}
                    cells={
                      <>
                        {item.severity ? (
                          <span data-testid="focus-severity" data-severity={item.severity} data-tone={
                            item.severity === "critical" ? "danger"
                            : item.severity === "high" ? "warn"
                            : undefined
                          }>
                            <StateChip
                              state={severityChipState(item.severity)}
                              label={humanizeToken(item.severity)}
                            />
                          </span>
                        ) : null}
                        {item.dueAt ? (
                          <span className="surface-token" data-testid="focus-due" data-tone={dueWarn ? "warn" : undefined}>
                            {item.dueAt}
                          </span>
                        ) : null}
                      </>
                    }
                    trailing={"▸"}
                    wrap
                  />
                );
              })}
            </ul>
          </SurfaceLedger>
        </div>
      </ScrollHint>
    </SurfaceSection>
  );
}

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
  const grouped: Record<string, typeof items.focus> = {};
  for (const item of items.focus) {
    const kind = item.itemType || "other";
    if (!grouped[kind]) grouped[kind] = [];
    grouped[kind].push(item);
  }
  return (
    <div data-testid="focus-block">
      {Object.entries(grouped).map(([kind, kindItems]) => {
        const count = items.totalsByType[kind] ?? kindItems.length;
        return <FocusKindSection key={kind} kind={kind} kindItems={kindItems} count={count} />;
      })}
    </div>
  );
}

/* ── Right rail — MetricStrip + SurfaceStream for changes ── */

function RightRail({ room }: { room: RoomSnapshot }) {
  const { meetings, resources, changes, sources } = room;
  const meetingsCount = meetings.state === "ok" ? meetings.count : 0;
  const resourcesCount = resources.state === "ok" ? resources.count : 0;
  const watchesCount = sources.state === "ok" ? ((sources as Record<string, unknown>).count as number ?? 0) : 0;
  const changesCount = changes.state === "ok" ? changes.recent.length : 0;
  const scrollRef = useRef<HTMLDivElement>(null);

  return (
    <div data-testid="project-room-rail">
      <MetricStrip
        dense
        items={[
          { label: "Meetings", value: meetingsCount },
          { label: "Resources", value: resourcesCount },
          { label: "Watches", value: watchesCount },
          { label: "Changes", value: changesCount },
        ]}
      />

      {meetings.state === "ok" ? (
        <div data-testid="rail-meetings" hidden>
          <span data-testid="rail-meetings-count">{meetings.count}</span>
          {meetings.latest ? (
            <span data-testid="rail-meetings-latest">
              {String((meetings.latest as Record<string, unknown>).title || "Latest")}
            </span>
          ) : null}
        </div>
      ) : null}

      {resources.state === "ok" ? (
        <div data-testid="rail-resources" hidden>
          <span data-testid="rail-resources-count">{resources.count}</span>
        </div>
      ) : null}

      {changes.state === "ok" ? (
        <div data-testid="rail-changes" hidden>
          <span data-testid="rail-changes-count">{changes.recent.length}</span>
        </div>
      ) : null}

      {changes.state === "ok" && changes.recent.length > 0 ? (
        <ScrollHint axis="y" scrollRef={scrollRef}>
          <div ref={scrollRef}>
            <SurfaceStream count="" countLabel="">
              <SurfaceStreamDay label={streamDayLabel(new Date(changes.recent[0].occurredAt || Date.now()))}>
                {(() => {
                  const grouped: { label: string; items: typeof changes.recent }[] = [];
                  for (const change of changes.recent) {
                    const last = grouped[grouped.length - 1];
                    if (last && last.label === change.label) {
                      last.items.push(change);
                    } else {
                      grouped.push({ label: change.label, items: [change] });
                    }
                  }
                  return grouped.map((group, gi) =>
                    group.items.length > 1 ? (
                      <SurfaceStreamEntry key={gi} dense>
                        <Disclosure label={`${group.items.length} ${group.label}`} defaultOpen={false} variant="raw">
                          {group.items.map((c, ci) => (
                            <div key={c.id || ci} className="room-change-row">
                              <span data-testid="rail-change-row">{c.label}</span>
                              {c.occurredAt ? <span className="room-change-time">{humanTime(c.occurredAt)}</span> : null}
                            </div>
                          ))}
                        </Disclosure>
                      </SurfaceStreamEntry>
                    ) : (
                      <SurfaceStreamEntry
                        key={group.items[0].id || gi}
                        when={group.items[0].occurredAt ? humanTime(group.items[0].occurredAt) : undefined}
                        dense
                      >
                        <span data-testid="rail-change-row">{group.items[0].label}</span>
                      </SurfaceStreamEntry>
                    ),
                  );
                })()}
              </SurfaceStreamDay>
            </SurfaceStream>
          </div>
        </ScrollHint>
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

  const reviewData: RoomReviewData | null =
    ctrl.room?.review.state === "ok"
      ? (ctrl.room.review as RoomReviewData & { state: "ok" })
      : null;

  const reviewCtrl = useReviewController(
    ctrl.projectId,
    reviewData,
    () => void ctrl.load(),
  );

  const updateCtrl = useUpdateController(
    ctrl.projectId,
    () => void ctrl.load(),
  );

  const stewardCtrl = useStewardController(
    ctrl.projectId,
    () => void ctrl.load(),
  );

  const runtimeTitle = ctrl.loadStatus === "ready" && ctrl.projectName !== "Project"
    ? ctrl.projectName
    : null;
  useWindowTitle(runtimeTitle, [runtimeTitle]);

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

  const activePosture =
    reviewCtrl.posture === "active" ? "review"
    : updateCtrl.posture !== "off" ? "updates"
    : stewardCtrl.posture !== "off" ? "steward"
    : undefined;

  const pendingCount = reviewData?.pending_count ?? 0;

  const stewardSection = ctrl.room?.steward;
  const lastRun = stewardSection?.state === "ok" && Array.isArray((stewardSection as Record<string, unknown>).runs)
    ? ((stewardSection as Record<string, unknown>).runs as Array<Record<string, unknown>>)[0] ?? null
    : null;
  const lastRunChip = lastRun ? (
    <StateChip
      state={String(lastRun.state) === "completed" ? "success" : "idle"}
      label={`RUN ${String(lastRun.id ?? "").replace(/^pstrun_/, "")}`}
    />
  ) : null;

  const postureVerbs = (
    <>
      {reviewCtrl.primaryVerb ? (
        <Button
          dense
          variant="primary"
          loading={reviewCtrl.loading}
          onClick={() => void reviewCtrl.enterReview()}
          data-testid="review-verb"
          data-verb="review"
        >
          {reviewCtrl.primaryVerb}
          {pendingCount > 0 ? (
            <span className="surface-token">{pendingCount}</span>
          ) : null}
        </Button>
      ) : null}
      <Button
        dense
        loading={updateCtrl.loading}
        onClick={() => void updateCtrl.enterUpdates()}
        data-testid="updates-verb"
        data-verb="updates"
      >
        Updates
      </Button>
      <Button
        dense
        loading={stewardCtrl.loading}
        onClick={() => void stewardCtrl.enterSteward()}
        data-testid="steward-verb"
        data-verb="steward"
      >
        Steward
      </Button>
    </>
  );

  const heroVerbs = (
    <>
      {postureVerbs}
      <Button dense variant="ghost" onClick={() => void ctrl.load()}>
        Refresh
      </Button>
    </>
  );

  if (!ctrl.projectId)
    return <SurfaceState empty emptyLabel="Open a Project" emptyGlyph={"▤"} />;

  const readReceipt = (() => {
    if (!ctrl.readAt) return "";
    const date = new Date(ctrl.readAt);
    const pad = (n: number) => String(n).padStart(2, "0");
    return `READ ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
  })();

  const identityBand = ctrl.room ? (
    <RoomIdentityBand room={ctrl.room} />
  ) : null;

  const postureStrip = (
    <SurfaceVerbs active={activePosture} status={lastRunChip}>
      {postureVerbs}
    </SurfaceVerbs>
  );

  if (reviewCtrl.posture === "active") {
    return (
      <>
        {hero ? hero(heroVerbs) : null}
        {identityBand}
        {postureStrip}
        <ReviewPosture ctrl={reviewCtrl} />
      </>
    );
  }

  if (updateCtrl.posture !== "off") {
    return (
      <>
        {hero ? hero(heroVerbs) : null}
        {identityBand}
        {postureStrip}
        <UpdatePosture ctrl={updateCtrl} />
      </>
    );
  }

  if (stewardCtrl.posture !== "off") {
    return (
      <>
        {hero ? hero(heroVerbs) : null}
        {identityBand}
        {postureStrip}
        <StewardPosture ctrl={stewardCtrl} />
      </>
    );
  }

  return (
    <>
      {hero ? hero(heroVerbs) : null}
      {ctrl.room ? (
        <>
          {identityBand}
          {postureStrip}
          <SurfaceColumns
            main={
              <>
                <FocusBlock room={ctrl.room} />
                <DegradedNotice label="meetings" section={ctrl.room.meetings} />
                <DegradedNotice label="resources" section={ctrl.room.resources} />
                <DegradedNotice label="changes" section={ctrl.room.changes} />
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
      <SurfaceFooter
        receipt={
          <span className="surface-footer-receipt-line" role="status">
            {readReceipt ? (
              <><ProvenanceChip source="project" boundary={ctrl.projectName} /> {readReceipt}</>
            ) : (
              <ProvenanceChip source="project" boundary={ctrl.projectName} />
            )}
          </span>
        }
        verbs={
          <Button dense variant="ghost" onClick={() => void ctrl.load()}>
            Refresh
          </Button>
        }
      />
    </>
  );
}

/* ── RoomIdentityBand — SurfaceIdentity composition ── */

function lifecycleChipState(lifecycle: string): "success" | "failure" | "idle" {
  if (lifecycle === "active" || lifecycle === "in_progress") return "success";
  if (lifecycle === "archived" || lifecycle === "closed") return "failure";
  return "idle";
}

function postureChipState(posture: string): "active" | "idle" {
  return posture === "green" || posture === "on_track" ? "active" : "idle";
}

function RoomIdentityBand({ room }: { room: RoomSnapshot }) {
  const { project } = room;

  return (
    <div data-testid="orientation-band" aria-label="Project orientation">
      <SurfaceIdentity
        name={project.name}
        nameTestId="project-room-name"
        chips={
          <>
            {project.lifecycle ? (
              <span data-testid="orientation-lifecycle" data-lifecycle={project.lifecycle}>
                <StateChip state={lifecycleChipState(project.lifecycle)} label={humanizeToken(project.lifecycle)} />
              </span>
            ) : null}
            {project.posture ? (
              <span data-testid="orientation-posture" data-posture={project.posture} title={project.postureReason || undefined}>
                <StateChip state={postureChipState(project.posture)} label={humanizeToken(project.posture)} />
              </span>
            ) : null}
            {room.revision > 0 ? (
              <span className="surface-token" data-testid="orientation-revision">
                REV {room.revision}
              </span>
            ) : null}
          </>
        }
        outcome={project.outcomeText || undefined}
        trailing={
          project.updatedAt ? (
            <span className="surface-token" data-testid="orientation-activity">
              {humanTime(project.updatedAt)}
            </span>
          ) : undefined
        }
      />
      {project.purpose ? (
        project.purpose.length > 160 ? (
          <Disclosure label="more" defaultOpen variant="raw">
            <div className="surface-identity-purpose" data-testid="orientation-purpose">{project.purpose}</div>
          </Disclosure>
        ) : (
          <div className="surface-identity-purpose" data-testid="orientation-purpose">{project.purpose}</div>
        )
      ) : null}
    </div>
  );
}
