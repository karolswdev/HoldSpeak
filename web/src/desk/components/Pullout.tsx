// The pull-out (HS-73-04): tap an object and it opens HERE, on the stage —
// the port of the iPad's DioPullout + the meeting drawer (PR #196). The
// world stays alive behind it; "Open full" is the ONE navigation on the
// desk; Escape or ✕ closes (it is a desk window — it survives clicks
// elsewhere and can be moved, resized, and raised).
import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { Link } from "react-router-dom";
// @ts-ignore — shared ESM module (see ../sprites.d.ts)
import { spriteUrl } from "../sprites";
import { apiRequest } from "../../lib/api";
import { useDurableDraft } from "../../lib/durableDraft";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { parseLinearGraph, stepLabel } from "../graph";
import { MicButton } from "./MicButton";
import { lineage } from "../lineage";
import { useSteering } from "../steering";
import { objGlow, type WorldObject } from "../world";
import { qualifiedRef } from "../api";
import { RunsOnPicker } from "./RunsOnPicker";
import { DeskWindowFrame } from "./DeskWindow";
import { workroomHref } from "../../workrooms/context";
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

export function Pullout({ o }: { o: WorldObject }) {
  const reducedMotion = useReducedMotion();
  const items = useDesk((s) => s.items);
  const profiles = useDesk((s) => s.profiles);
  const inferenceTargets = useDesk((s) => s.inferenceTargets);
  const selectedIds = useDesk((s) => s.selectedIds);
  const backId = useDesk((s) => s.pulloutBackId);
  const {
    closePullout,
    openPullout,
    openEditor,
    fileIntoDir,
    removeFromDir,
    answerCoder,
    speakToCoder,
    openChat,
    openToolInspector,
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
  const [filing, setFiling] = useState(false);
  const [relationships, setRelationships] = useState<any>(null);
  const [knowledgeChoices, setKnowledgeChoices] = useState<any[]>([]);
  const [projectChoices, setProjectChoices] = useState<any[]>([]);
  const [relationshipError, setRelationshipError] = useState("");
  const [answered, setAnswered] = useState<
    "selected" | "sent" | "failed" | null
  >(null);
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

  useEffect(() => {
    // A desk window closes deliberately (✕ or Escape) — never from a stray
    // click elsewhere on the desk; arranged windows coexist.
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closePullout();
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
    };
  }, []);

  useEffect(() => {
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
  const refreshRelationships = async () => {
    if (!FILABLE.has(o.kind)) return;
    try {
      const [axesRes, knowledgeRes, projectRes] = await Promise.all([
        apiRequest(
          `/api/desk/relationships/${encodeURIComponent(resourceRef)}`,
        ),
        apiRequest("/api/kbs"),
        apiRequest("/api/projects"),
      ]);
      const [axes, knowledge, projects] = await Promise.all([
        axesRes.json(),
        knowledgeRes.json(),
        projectRes.json(),
      ]);
      setRelationships(axes);
      setKnowledgeChoices((knowledge.kbs || []).filter((k: any) => !k.deleted));
      setProjectChoices(
        (projects.projects || []).filter((p: any) => !p.is_archived),
      );
      setRelationshipError("");
    } catch (error) {
      setRelationshipError(String(error));
    }
  };

  useEffect(() => {
    setRelationships(null);
    setRunTargetId(String((o.ref as any).profileId || "this_machine"));
    setActualPlacement(null);
    void refreshRelationships();
  }, [o.kind, o.id]);

  const toggleRelationship = async (
    axis: "knowledge" | "projects",
    ownerId: string,
    active: boolean,
  ) => {
    const base = axis === "knowledge" ? "kbs" : "projects";
    try {
      await apiRequest(
        `/api/${base}/${encodeURIComponent(ownerId)}/${axis === "knowledge" ? "members" : "resources"}/${encodeURIComponent(resourceRef)}`,
        {
          method: active ? "DELETE" : "PUT",
          ...(axis === "projects" && !active
            ? {
                headers: { "content-type": "application/json" },
                body: JSON.stringify({ relationship: "member" }),
              }
            : {}),
        },
      );
      await refreshRelationships();
      await useDesk.getState().refresh();
    } catch (error) {
      setRelationshipError(String(error));
    }
  };

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
  const zones = items.directory || [];
  const lin = lineage(items, ir.sources);
  const profile = profiles.find((p) => p.id === ir.profileId);
  const egress = profile
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
    <button
      key={a.id}
      type="button"
      className="desk-pullout-row"
      onClick={() => openPullout(a.id)}
    >
      <span className="desk-pullout-row-type">
        {a.artifact_type || a.artifactType}
      </span>
      <span className="desk-pullout-row-title">{a.title}</span>
    </button>
  );

  return (
    <DeskWindowFrame
      id="pullout"
      glyph="▤"
      label={o.title}
      className="desk-pullout"
      rootStyle={{ "--k": objGlow(o.kind) } as React.CSSProperties}
      icon={<img src={spriteUrl(o.kind, o.id)} alt="" width={30} height={30} />}
      title={o.title}
      open
      onClose={closePullout}
      leading={
        backId ? (
          <button
            type="button"
            className="desk-chip quiet"
            onClick={() => openPullout(backId)}
            aria-label="Back"
          >
            ←
          </button>
        ) : null
      }
      actions={
        <>
          {egress && (
          <span className={`egress-badge is-${egress.scope}`}>
            {egress.text}
          </span>
        )}
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
          <Link
            className="desk-chip quiet"
            to={workroomHref("/workbench", {
              action: "edit-workflow",
              subjectRef: resourceRef,
            })}
          >
            Edit Workflow
          </Link>
        )}
        </>
      }
    >
      <div className="desk-pullout-body">
        {o.kind === "meeting" && (
          <>
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
                  closePullout();
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
              <section>
                <h3>Summary</h3>
                <p>{detail.intel.summary}</p>
              </section>
            ) : (
              <section>
                <h3>Intelligence</h3>
                <p className="quiet">
                  {detail?.intel_status?.state
                    ? `Intelligence ${intelligenceState(detail.intel_status.state)}`
                    : "Intelligence queued"}
                </p>
              </section>
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
                {artifacts.map(artifactRow)}
              </section>
            )}
          </>
        )}

        {o.kind === "artifact" && (
          <>
            <section>
              <h3>{String(ir.artifactType || "artifact")}</h3>
              <pre className="desk-pullout-md">
                {String(ir.bodyMarkdown || "")}
              </pre>
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

        {(o.kind === "note" || o.kind === "kb") && (
          <section>
            <pre className="desk-pullout-md">
              {String(
                ir.bodyMarkdown ||
                  (ir.memberIds || [])
                    .map((m: string) => `· ${m}`)
                    .join("\n") ||
                  "",
              )}
            </pre>
          </section>
        )}

        {o.kind === "recipe" && (
          <section>
            <p className="quiet">{String(ir.role || "")}</p>
            <pre className="desk-pullout-md">
              {String(ir.systemPrompt || "")}
            </pre>
            <button
              type="button"
              className="desk-chip"
              onClick={() => openChat(o.id)}
            >
              Chat with {o.title}
            </button>
          </section>
        )}

        {(o.kind === "chain" || o.kind === "workflow") && (
          <section>
            <h3>Steps</h3>
            <ul>
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
            </ul>
          </section>
        )}

        {o.kind === "coder" && (
          <section>
            <p className="quiet">
              {String(ir.model || "")} · {String(ir.state || "")}
            </p>
            {ir.question ? (
              <pre className="desk-pullout-md">{String(ir.question)}</pre>
            ) : null}
            <div className="desk-coder-answer">
              {coderWaiting ? (
                <>
                  {contextualCoderAction ? (
                    <div className="desk-coder-context">
                      <strong>
                        Selected source · {contextualCoderAction.source.title}
                      </strong>
                      <pre>{contextualCoderAction.source.text}</pre>
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
                    rows={3}
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
                  closePullout();
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
          <section>
            <div className="desk-capability-contract">
              <strong>
                {o.kind === "recipe"
                  ? "Persona"
                  : o.kind === "chain"
                    ? "Sequence"
                    : "Workflow"}
              </strong>
              <span className={`desk-chip quiet is-${readiness.state}`}>
                {readiness.state === "ready" ? "Ready" : "Unavailable here"}
              </span>
              <p className="quiet">
                {capability.input_help ||
                  "Choose the material this capability should work on."}
              </p>
              {readiness.detail && (
                <p className="desk-run-warning">{readiness.detail}</p>
              )}
              <p className="quiet">
                Runs on{" "}
                {(capability.supported_placements || ["this_machine"]).join(
                  " · ",
                )}
                {capability.effect_classes?.length
                  ? ` · ${capability.effect_classes.join(" · ")}`
                  : ""}
              </p>
              <button
                type="button"
                className="desk-chip quiet"
                onClick={() =>
                  openSurfaceOr("configure-runs-on", "/profiles", resourceRef)
                }
              >
                Configure Runs on
              </button>
              {o.kind === "chain" && (
                <p className="quiet">
                  Sequence is the linear compatibility form.
                </p>
              )}
              {o.kind === "workflow" && (
                <Link
                  className="desk-chip quiet"
                  to={workroomHref("/workbench", {
                    action: "edit-workflow",
                    subjectRef: resourceRef,
                  })}
                >
                  Edit this Workflow
                </Link>
              )}
            </div>
            <div className="desk-pullout-run">
              <RunsOnPicker
                targets={inferenceTargets}
                selectedId={runTargetId}
                onChange={setRunTargetId}
                disabled={runBusy}
              />
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
                aria-label="Run material"
                onChange={(e) => setRunInput(e.target.value)}
              />
              {runInputRecovered ? (
                <span className="quiet">Recovered local run material.</span>
              ) : null}
              <button
                type="button"
                className="desk-chip"
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
                    ? `Retry ${runLabel}`
                    : runLabel}
              </button>
            </div>
            {runWarning && <p className="desk-run-warning">⚠ {runWarning}</p>}
            {runOut && <pre className="desk-pullout-md">{runOut}</pre>}
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
                {` · ${runInvocationId}`}
              </p>
            )}
          </section>
        )}

        {FILABLE.has(o.kind) && relationships && (
          <section
            className="desk-relationship-axes"
            aria-label="Organization and context"
          >
            <h3>Where it belongs</h3>
            <p>
              {relationships.zone
                ? `Zone: ${relationships.zone.directory_id}`
                : "Desk root"}
            </p>

            <h3>Knowledge</h3>
            <div className="desk-pullout-lineage">
              {knowledgeChoices.map((knowledge) => {
                const active = (relationships.knowledge || []).some(
                  (row: any) => row.knowledge_id === knowledge.id,
                );
                return (
                  <button
                    key={knowledge.id}
                    type="button"
                    className={`desk-chip quiet${active ? " in-zone" : ""}`}
                    aria-pressed={active}
                    onClick={() =>
                      void toggleRelationship("knowledge", knowledge.id, active)
                    }
                  >
                    {active ? "✓ " : "+ "}
                    {knowledge.name}
                  </button>
                );
              })}
              {!knowledgeChoices.length && (
                <span className="quiet">No Knowledge yet</span>
              )}
            </div>

            <h3>Projects</h3>
            <div className="desk-pullout-lineage">
              {projectChoices.map((project) => {
                const active = (relationships.projects || []).some(
                  (row: any) => row.project_id === project.id,
                );
                return (
                  <span className="desk-project-choice" key={project.id}>
                    <button
                      type="button"
                      className={`desk-chip quiet${active ? " in-zone" : ""}`}
                      aria-label={`${active ? "Remove from" : "Assign to"} ${project.name} Project`}
                      aria-pressed={active}
                      onClick={() =>
                        void toggleRelationship("projects", project.id, active)
                      }
                    >
                      {active ? "✓ " : "+ "}
                      {project.name}
                    </button>
                    <button
                      type="button"
                      className="desk-chip quiet"
                      aria-label={`Inspect ${project.name} Project`}
                      onClick={() =>
                        openToolInspector("project", String(project.id))
                      }
                    >
                      Inspect
                    </button>
                  </span>
                );
              })}
              {!projectChoices.length && (
                <span className="quiet">No Projects yet</span>
              )}
            </div>
          </section>
        )}
        {relationshipError && (
          <p className="desk-run-warning" role="alert">
            {relationshipError}
          </p>
        )}
      </div>

      <footer className="desk-pullout-foot">
        {FILABLE.has(o.kind) && (
          <button
            type="button"
            className="desk-chip quiet"
            onClick={() =>
              openSurfaceOr("dictate", "/dictation", resourceRef)
            }
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
        {EDITABLE.has(o.kind) && (
          <button
            type="button"
            className="desk-chip"
            onClick={() => openEditor(o.id)}
          >
            Edit
          </button>
        )}
        {FILABLE.has(o.kind) && zones.length > 0 && (
          <div className="desk-pullout-file">
            <button
              type="button"
              className="desk-chip quiet"
              onClick={() => setFiling((v) => !v)}
            >
              Move to…
            </button>
            {filing &&
              zones.map((z) => {
                const members = ((z as any).memberIds as string[]) || [];
                const inZone =
                  members.includes(o.id) || members.includes(resourceRef);
                return (
                  <button
                    key={String(z.id)}
                    type="button"
                    className={"desk-chip quiet" + (inZone ? " in-zone" : "")}
                    onClick={() => {
                      setFiling(false);
                      void (inZone
                        ? removeFromDir(o.id, String(z.id), o.kind)
                        : fileIntoDir(o.id, String(z.id), o.kind));
                    }}
                  >
                    {inZone ? "✓ " : ""}
                    {String(z.name || z.id)}
                  </button>
                );
              })}
          </div>
        )}
      </footer>
    </DeskWindowFrame>
  );
}
