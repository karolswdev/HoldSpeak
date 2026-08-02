// The pull-out (HS-73-04): tap an object and it opens HERE, on the stage —
// the port of the iPad's DioPullout + the meeting drawer (PR #196). The
// world stays alive behind it; "Open full" is the ONE navigation on the
// desk; Escape or ✕ closes (it is a desk window — it survives clicks
// elsewhere and can be moved, resized, and raised).
import { useEffect, useRef, useState } from "react";
// @ts-ignore — shared ESM module (see ../sprites.d.ts)
import { spriteUrl } from "../sprites";
import { apiRequest } from "../../lib/api";
import { useDurableDraft } from "../../lib/durableDraft";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { parseLinearGraph, stepLabel } from "../graph";
import { DeskEditor, type DeskEditorHandle } from "./DeskEditor";
import { MicButton } from "./MicButton";
import { AgentAvatar } from "./AgentAvatar";
import { lineage } from "../lineage";
import { useSteering } from "../steering";
import { objectByRef, objGlow, type WorldObject } from "../world";
import { qualifiedRef } from "../api";
import { RunsOnPicker } from "./RunsOnPicker";
import { humanizeWireValue, productLabel } from "../../lib/productLanguage";
import { EgressChip, FoldGadget } from "../surface/gadgets";
import { DeskFilingStrip } from "./DeskFilingStrip";
import { DeskWindowFooter } from "./DeskWindowFooter";
import { Material } from "../surface/Material";
import {
  SurfaceCode,
  SurfaceRow,
  SurfaceRows,
  SurfaceWell,
} from "../surface/Surface";
import { humanTime } from "../surface/format";
import { DeskWindowFrame } from "./DeskWindow";
import { MeetingConflictRecovery } from "../../meetings/MeetingConflictRecovery";
import { MeetingIntelRecovery } from "../../meetings/MeetingIntelRecovery";
import {
  contextualCapabilityActions,
  contextualCoderSessions,
} from "../contextual";

const FILABLE = new Set([
  "meeting",
  "artifact",
  "note",
  "recipe",
  "chain",
  "workflow",
  "kb",
]);
const EDITABLE = new Set(["note", "kb", "recipe", "workflow"]);

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

export function Pullout({
  o,
  origin,
}: {
  o: WorldObject;
  /** The client point the open gesture happened at (spatial motion). */
  origin?: { x: number; y: number } | null;
}) {
  const items = useDesk((s) => s.items);
  const profiles = useDesk((s) => s.profiles);
  const inferenceTargets = useDesk((s) => s.inferenceTargets);
  const selectedIds = useDesk((s) => s.selectedIds);
  const {
    closePullout,
    openPullout,
    openEditor,
    updatePrimitive,
    answerCoder,
    speakToCoder,
    openChat,
  } = useDesk.getState();
  const [detail, setDetail] = useState<MeetingDetail | null>(null);
  const [artifacts, setArtifacts] = useState<any[]>([]);
  const [runBusy, setRunBusy] = useState(false);
  const [runOut, setRunOut] = useState("");
  const [runWarning, setRunWarning] = useState("");
  const [runState, setRunState] = useState("");
  const [runArtifactId, setRunArtifactId] = useState<string | null>(null);
  const [runInvocationId, setRunInvocationId] = useState<string | null>(null);
  const [runTargetId, setRunTargetId] = useState(
    String((o.ref as any).profileId || "this_machine"),
  );
  const [actualPlacement, setActualPlacement] = useState<Record<
    string,
    unknown
  > | null>(null);
  const [answered, setAnswered] = useState<
    "selected" | "sent" | "failed" | null
  >(null);
  // Round 9 — canon rule 1: the note's material edits IN PLACE on the
  // card. Escape reverts; Done (or ⌘Enter) commits through the real PUT.
  const [editingBody, setEditingBody] = useState(false);
  const [bodyDraft, setBodyDraft] = useState("");
  const bodyEditorRef = useRef<DeskEditorHandle | null>(null);
  const startBodyEdit = () => {
    setBodyDraft(String((o.ref as any).bodyMarkdown || ""));
    setEditingBody(true);
  };
  const commitBodyEdit = () => {
    void updatePrimitive("note", o.id, { body_markdown: bodyDraft });
    setEditingBody(false);
  };
  const contextualAction = contextualCapabilityActions(items, selectedIds).find(
    (action) => action.id === o.id && action.kind === o.kind,
  );
  const contextualCoderAction = contextualCoderSessions(
    items,
    selectedIds,
  ).find((action) => action.id === o.id);
  const {
    value: runInput,
    setDraft: setRunInput,
    recovered: runInputRecovered,
  } = useDurableDraft(
    `capability:${o.kind}:${o.id}`,
    contextualAction?.input || "",
  );
  const coderSessionId = String((o.ref as any).sessionId || o.id);
  const {
    value: coderDraft,
    setDraft: setCoderDraft,
    recovered: coderDraftRecovered,
  } = useDurableDraft(`coder-reply:${coderSessionId}`);

  // Escape scope: the focused card closes itself (DeskWindowFrame); a
  // desk-scoped Escape closes the FRONT card (the WorldStage listener).
  // Cards never close from a stray click elsewhere — windows coexist.

  useEffect(() => {
    if (o.kind === "recipe") {
      apiRequest("/api/invocations?limit=25")
        .then((r) => r.json())
        .then((data) => {
          const invocation = (data.invocations || []).find(
            (item: any) => item.definition_ref === `persona:${o.id}`,
          );
          if (!invocation) return;
          setRunInvocationId(String(invocation.id));
          setRunState(String(invocation.state));
          setActualPlacement(
            invocation.attempts?.at(-1)?.actual_placement || null,
          );
        })
        .catch(() => undefined);
    }
    if (o.kind !== "meeting") return;
    // The detail payload nests intel_status (the repo's documented gotcha).
    apiRequest(`/api/meetings/${encodeURIComponent(o.id)}`)
      .then((r) => r.json())
      .then(setDetail)
      .catch(() => setDetail(null));
    apiRequest(`/api/meetings/${encodeURIComponent(o.id)}/artifacts`)
      .then((r) => r.json())
      .then((d) => setArtifacts(d.artifacts || []))
      .catch(() => setArtifacts([]));
  }, [o.kind, o.id]);

  const resourceRef = qualifiedRef(o.kind, o.id);
  useEffect(() => {
    setRunTargetId(String((o.ref as any).profileId || "this_machine"));
    setActualPlacement(null);
  }, [o.kind, o.id]);

  const run = async () => {
    setRunBusy(true);
    setRunOut("");
    setRunWarning("");
    setRunState("running");
    setRunArtifactId(null);
    setRunInvocationId(null);
    setActualPlacement(null);
    const result = await useDesk
      .getState()
      .runCapability(
        o.kind as "recipe" | "chain" | "workflow",
        o.id,
        runInput,
        runTargetId,
      );
    setRunOut(result.output);
    // Older hubs may still send a warning; current hubs refuse unsupported graphs.
    setRunWarning(result.warning || "");
    setRunState(result.state);
    setRunArtifactId(result.artifactId);
    setRunInvocationId(result.invocationId);
    setActualPlacement(result.actualPlacement);
    setRunBusy(false);
  };

  const ir = o.ref as any;
  const capability = ir.capability || {};
  const readiness = capability.readiness || {
    state: "unavailable",
    detail: "Capability contract unavailable. Nothing was run. Reload the Desk to retry.",
  };
  const capabilityCanRun =
    readiness.state === "ready" &&
    capability.input_schema?.required?.includes("input") &&
    capability.effect_classes?.includes("creates_artifact");
  const selectedTarget =
    inferenceTargets.find((target) => target.id === runTargetId) ||
    inferenceTargets[0];
  const runLabel =
    contextualAction?.label ||
    capability.action_label ||
    (o.kind === "recipe" ? `Ask ${o.title}` : `Run ${o.title}`);
  const coderWaiting =
    o.kind === "coder" &&
    (String(ir.state || "") === "waiting" || Boolean(ir.question));
  const lin = lineage(items, ir.sources);
  const profile = profiles.find((p) => p.id === ir.profileId);
  const egress: { scope: "local" | "cloud"; text: string } | null = profile
    ? (profile.kind || "onDevice") === "onDevice"
      ? { scope: "local", text: "⌂ This device" }
      : {
          scope: "cloud",
          text: `☁ ${
            String(profile.base_url || "endpoint")
              .replace(/^https?:\/\//, "")
              .split("/")[0]
          }`,
        }
    : null;

  const artifactRow = (a: any) => (
    <SurfaceRow
      key={a.id}
      title={a.title}
      detail={humanizeWireValue(String(a.artifact_type || a.artifactType || ""))}
      onOpen={() => openPullout(a.id)}
    />
  );

  // The meeting's one facts line (round 6 phrasing): when · length · size.
  const meetingFacts =
    o.kind === "meeting" && detail
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
    <DeskWindowFrame
      id={`pullout:${o.id}`}
      glyph="▤"
      label={o.title}
      className="desk-pullout is-card"
      fitContent
      origin={origin}
      rootStyle={{ "--k": objGlow(o.kind) } as React.CSSProperties}
      icon={<img src={spriteUrl(o.kind, o.id)} alt="" width={30} height={30} />}
      title={o.title}
      open
      onClose={() => closePullout(o.id)}
      actions={
        <>
          {egress ? <EgressChip label={egress.text} scope={egress.scope} /> : null}
        {o.kind === "meeting" && (
          <button
            type="button"
            className="desk-chip quiet"
            onClick={() =>
              openSurfaceOr("review-meetings", "/history", resourceRef)
            }
          >
            Review meeting
          </button>
        )}
        {o.kind === "workflow" && (
          <button
            type="button"
            className="desk-chip quiet"
            onClick={() =>
              openSurfaceOr("build-workflow", "/workbench", resourceRef)
            }
          >
            Edit Workflow
          </button>
        )}
        </>
      }
    >
      <div className="desk-pullout-body desk-surface-body">
        {o.kind === "meeting" && (
          <>
            {meetingFacts ? (
              <p className="quiet desk-pullout-facts">{meetingFacts}</p>
            ) : null}
            {detail?.capture_status && detail.capture_status !== "finalized" ? (
              <section>
                <h3>Saved, incomplete</h3>
                <p className="quiet">
                  {detail.capture_status}
                  {detail.capture_failure ? ` · ${detail.capture_failure}` : ""}
                  {detail.provenance ? ` · from ${detail.provenance}` : ""}
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
              <p className="quiet">
                {detail?.intel_status?.state === "disabled"
                  ? "Intelligence is off. No outcomes were made for this meeting."
                  : detail?.intel_status?.state
                    ? `Intelligence ${intelligenceState(detail.intel_status.state)}`
                    : "Intelligence queued"}
              </p>
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
          </>
        )}

        {o.kind === "artifact" && (
          <>
            <section>
              <h3>{humanizeWireValue(String(ir.artifactType || "artifact"))}</h3>
              <Material>{String(ir.bodyMarkdown || "")}</Material>
            </section>
            {lin.any && (
              <section>
                <h3>Lineage</h3>
                <div className="desk-pullout-lineage">
                  {lin.via && (
                    <span className="desk-chip quiet">via {lin.via.label}</span>
                  )}
                  {lin.from.map((f) => (
                    <button
                      key={f.ref}
                      type="button"
                      className="desk-chip quiet"
                      onClick={() => f.resolved && openPullout(f.ref)}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
              </section>
            )}
          </>
        )}

        {(o.kind === "note" || o.kind === "kb") &&
          (() => {
            const body = String(ir.bodyMarkdown || "");
            const members = ((ir.memberIds as string[]) || [])
              .map((m) => ({ ref: m, member: objectByRef(items, m) }))
              .filter(({ member }) => member);
            if (o.kind === "note" && editingBody)
              return (
                <section>
                  <DeskEditor
                    ref={bodyEditorRef}
                    className="desk-pullout-markdown-editor"
                    ariaLabel={`${o.title} content`}
                    value={bodyDraft}
                    autoFocus
                    minHeight={`${Math.max(6, bodyDraft.split("\n").length + 1) * 1.55}em`}
                    placeholder="Write"
                    onChange={setBodyDraft}
                    onEscape={() => setEditingBody(false)}
                    onModEnter={commitBodyEdit}
                  />
                </section>
              );
            if (body)
              return (
                <section>
                  <Material>{body}</Material>
                </section>
              );
            if (o.kind === "kb" && members.length)
              return (
                <section>
                  <SurfaceRows>
                    {members.map(({ ref, member }) => (
                      <SurfaceRow
                        key={ref}
                        glyph={
                          <img
                            src={spriteUrl(member!.kind, member!.id)}
                            width={22}
                            height={22}
                            alt=""
                          />
                        }
                        title={member!.title}
                        detail={productLabel(member!.kind)}
                        onOpen={() => openPullout(member!.id)}
                      />
                    ))}
                  </SurfaceRows>
                </section>
              );
            return (
              <section>
                <p className="quiet">
                  Nothing written here yet — Edit adds content.
                </p>
              </section>
            );
          })()}

        {o.kind === "recipe" && (
          <section className="desk-pullout-agent">
            <div className="desk-chat-hello">
              <span className="desk-chat-hello-avatar" aria-hidden="true">
                <AgentAvatar avatar={String(ir.avatar || "")} id={o.id} size={32} />
              </span>
              <strong className="surface-primary">{o.title}</strong>
              {ir.role ? <small>{String(ir.role)}</small> : null}
            </div>
            <button
              type="button"
              className="desk-chip is-primary desk-pullout-agent-chat"
              onClick={() => openChat(o.id)}
            >
              Chat with {o.title}
            </button>
            {ir.systemPrompt ? (
              <FoldGadget title="Instructions">
                <Material>{String(ir.systemPrompt)}</Material>
              </FoldGadget>
            ) : null}
          </section>
        )}

        {(o.kind === "chain" || o.kind === "workflow") && (
          <section>
            <h3>Steps</h3>
            <ol className="desk-pullout-steps">
              {(
                (o.kind === "workflow" && ir.graphJson
                  ? (parseLinearGraph(ir.graphJson)?.map(stepLabel) ?? [
                      "Graphed on iPad",
                    ])
                  : null) ||
                (ir.steps as string[]) ||
                (ir.prompt ? [ir.prompt] : [])
              ).map((st, i) => (
                <li key={i}>{st}</li>
              ))}
            </ol>
          </section>
        )}

        {o.kind === "coder" && (
          <section>
            <p className="quiet">
              {String(ir.model || "")} · {String(ir.state || "")}
            </p>
            {ir.question ? (
              <Material className="desk-coder-question">
                {String(ir.question)}
              </Material>
            ) : null}
            <div className="desk-coder-answer">
              {coderWaiting ? (
                <>
                  {contextualCoderAction ? (
                    <div className="desk-coder-context">
                      <strong>
                        Selected source · {contextualCoderAction.source.title}
                      </strong>
                      {/* HS-111-07 — the selected text folds behind the
                          RAW pattern (it is wire until sent). */}
                      <FoldGadget title="RAW · SELECTED TEXT">
                        <SurfaceWell
                          head={`RAW · ${contextualCoderAction.source.title.toUpperCase()}`}
                        >
                          <SurfaceCode>
                            {contextualCoderAction.source.text}
                          </SurfaceCode>
                        </SurfaceWell>
                      </FoldGadget>
                      <button
                        type="button"
                        className="desk-chip"
                        onClick={() => {
                          setAnswered(null);
                          void speakToCoder(
                            String(ir.agent || "claude"),
                            String(ir.sessionId || o.id),
                            contextualCoderAction.source.text,
                          ).then((ok) => setAnswered(ok ? "sent" : "failed"));
                        }}
                      >
                        {answered === "sent"
                          ? `Sent ${contextualCoderAction.source.title}`
                          : answered === "failed"
                            ? `Retry sending ${contextualCoderAction.source.title}`
                            : contextualCoderAction.label}
                      </button>
                    </div>
                  ) : null}
                  <div className="desk-chat-well">
                    <div className="desk-chat-composer">
                      <MicButton
                        label="Hold to answer"
                        draftScope={`coder-reply:${coderSessionId}`}
                        onText={(t) =>
                          setCoderDraft((current) =>
                            current ? `${current} ${t}` : t,
                          )
                        }
                      />
                      <textarea
                        className="desk-coder-draft-input"
                        aria-label="Coder reply draft"
                        value={coderDraft}
                        placeholder="Reply"
                        rows={2}
                        onChange={(event) => setCoderDraft(event.target.value)}
                      />
                      <button
                        type="button"
                        className="desk-chip"
                        disabled={!coderDraft.trim()}
                        onClick={() => {
                          setAnswered(null);
                          const retained = coderDraft.trim();
                          void speakToCoder(
                            String(ir.agent || "claude"),
                            coderSessionId,
                            retained,
                          ).then((ok) => {
                            setAnswered(ok ? "sent" : "failed");
                            if (ok) setCoderDraft("");
                          });
                        }}
                      >
                        {answered === "failed" ? "Retry reply" : "Send reply"}
                      </button>
                    </div>
                  </div>
                  <span className="quiet desk-coder-answer-state" role="status">
                    {answered === "sent"
                      ? "Sent"
                      : answered === "failed"
                        ? "Delivery failed. Your reply remains editable."
                        : coderDraftRecovered
                          ? "Recovered local reply draft."
                          : "Hold to fill or type a reply."}
                  </span>
                  <button
                    type="button"
                    className="desk-chip quiet"
                    onClick={() => {
                      void answerCoder(
                        String(ir.agent || "claude"),
                        String(ir.sessionId || o.id),
                      ).then((ok) => setAnswered(ok ? "selected" : "failed"));
                    }}
                  >
                    {answered === "selected"
                      ? "Dictation target"
                      : "Use the hotkey"}
                  </button>
                </>
              ) : null}
              <button
                type="button"
                className="desk-chip quiet"
                onClick={() => {
                  closePullout(o.id);
                  useSteering
                    .getState()
                    .openSession(
                      `${String(ir.agent || "claude")}:${String(ir.sessionId || o.id)}`,
                    );
                }}
              >
                Watch live
              </button>
            </div>
          </section>
        )}

        {["recipe", "chain", "workflow"].includes(o.kind) && (
          <section className="desk-pullout-capability">
            {readiness.state !== "ready" && (
              <p className="desk-run-warning">
                {readiness.detail || "Unavailable here."}
              </p>
            )}
            <div className="desk-chat-well">
              <div className="desk-chat-composer">
                <MicButton
                  label={`Hold to fill ${runLabel.toLowerCase()} material`}
                  draftScope={`capability:${o.kind}:${o.id}`}
                  onText={(text) =>
                    setRunInput((current) =>
                      current ? `${current} ${text}` : text,
                    )
                  }
                />
                <input
                  value={runInput}
                  placeholder="Material"
                  aria-label={runLabel}
                  title={String(capability.input_help || "")}
                  onChange={(e) => setRunInput(e.target.value)}
                />
                <button
                  type="button"
                  className={
                    o.kind === "recipe" ? "desk-chip" : "desk-chip is-primary"
                  }
                  onClick={() => void run()}
                  disabled={
                    runBusy ||
                    !capabilityCanRun ||
                    !runInput.trim() ||
                    !selectedTarget?.readiness.available
                  }
                >
                  {runBusy
                    ? "Running…"
                    : runState === "failed" || runState === "empty"
                      ? "Retry"
                      : o.kind === "recipe"
                        ? "Ask"
                        : "Run"}
                </button>
              </div>
              <div className="desk-chat-well-foot">
                <RunsOnPicker
                  targets={inferenceTargets}
                  selectedId={runTargetId}
                  onChange={setRunTargetId}
                  disabled={runBusy}
                />
              </div>
            </div>
            {runInputRecovered ? (
              <span className="quiet">Recovered local run material.</span>
            ) : null}
            <div className="desk-pullout-capability-foot">
              <span className="quiet">
                Runs on{" "}
                {(capability.supported_placements || ["this_machine"])
                  .map((value: string) => humanizeWireValue(value))
                  .join(" · ")}
                {capability.effect_classes?.length
                  ? ` · ${capability.effect_classes
                      .map((value: string) => humanizeWireValue(value))
                      .join(" · ")}`
                  : ""}
              </span>
              <button
                type="button"
                className="desk-chip quiet"
                onClick={() =>
                  openSurfaceOr("configure-runs-on", "/profiles", resourceRef)
                }
              >
                Configure Runs on
              </button>
            </div>
            {runWarning && <p className="desk-run-warning">⚠ {runWarning}</p>}
            {runOut && (
              <div className="surface-aerogel">
                <Material>{runOut}</Material>
              </div>
            )}
            {runArtifactId && (
              <button
                type="button"
                className="desk-chip"
                onClick={() => openPullout(runArtifactId)}
              >
                Open kept Artifact
              </button>
            )}
            {runInvocationId && (
              <p className="quiet desk-run-receipt">
                Receipt ·{" "}
                {String(
                  actualPlacement?.target_name ||
                    actualPlacement?.target_id ||
                    runTargetId,
                )}
                {actualPlacement?.engine
                  ? ` · ${String(actualPlacement.engine)}`
                  : ""}
                {actualPlacement?.model
                  ? ` · ${String(actualPlacement.model)}`
                  : ""}
                {actualPlacement?.boundary
                  ? ` · ${String(actualPlacement.boundary)}`
                  : ""}
                {actualPlacement?.fallback_reason
                  ? ` · fallback: ${String(actualPlacement.fallback_reason)}`
                  : ""}
                {runState ? ` · ${runState}` : ""}
                {` · ${runInvocationId}`}
              </p>
            )}
          </section>
        )}

        {FILABLE.has(o.kind) ? (
          <DeskFilingStrip
            objectRef={resourceRef}
            objectKind={o.kind}
            objectId={o.id}
          />
        ) : null}
      </div>

      <DeskWindowFooter>
        {FILABLE.has(o.kind) && !editingBody && (
          <button
            type="button"
            className="desk-chip quiet"
            onClick={() => openSurfaceOr("dictate", "/dictation", resourceRef)}
          >
            Dictate about this
          </button>
        )}
        {o.kind === "meeting" && (
          <button
            type="button"
            className="desk-chip quiet"
            onClick={() => openSurfaceOr("record-live", "/live", resourceRef)}
          >
            Record follow-up
          </button>
        )}
        {o.kind === "note" ? (
          editingBody ? (
            <>
              <MicButton
                label="Hold to fill"
                draftScope={`card-edit:${o.id}`}
                onText={(text) => bodyEditorRef.current?.insertAtCursor(text)}
              />
              <button
                type="button"
                className="desk-chip quiet"
                onClick={() => setEditingBody(false)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="desk-chip is-primary"
                onClick={commitBodyEdit}
              >
                Done
              </button>
            </>
          ) : (
            <button
              type="button"
              className="desk-chip is-primary"
              onClick={startBodyEdit}
            >
              Edit
            </button>
          )
        ) : (
          EDITABLE.has(o.kind) && (
            <button
              type="button"
              className="desk-chip is-primary"
              onClick={() => openEditor(o.id)}
            >
              Edit
            </button>
          )
        )}
      </DeskWindowFooter>
    </DeskWindowFrame>
  );
}
