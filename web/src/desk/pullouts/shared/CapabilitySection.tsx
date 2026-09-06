/** Shared capability run section — used by recipe, chain, workflow pullouts
 * (HS-117-15). Manages all run-related state internally. */
import { useEffect, useState } from "react";
import { apiRequest } from "../../../lib/api";
import { useDurableDraft } from "../../../lib/durableDraft";
import { useDesk } from "../../store";
import { openSurfaceOr } from "../../shell";
import { qualifiedRef } from "../../api";
import { MicButton } from "../../components/MicButton";
import { ContextualAssignment } from "../../../pages/cores/ContextualAssignment";
import { Material } from "../../surface/Material";
import { SurfaceState } from "../../surface/Surface";
import { humanizeWireValue } from "../../../lib/productLanguage";
import {
  contextualCapabilityActions,
} from "../../contextual";
import type { WorldObject } from "../../world";

export function CapabilitySection({ object: o }: { object: WorldObject }) {
  const items = useDesk((s) => s.items);
  const selectedIds = useDesk((s) => s.selectedIds);
  const { openPullout } = useDesk.getState();

  const [runBusy, setRunBusy] = useState(false);
  const [runOut, setRunOut] = useState("");
  const [runWarning, setRunWarning] = useState("");
  const [runState, setRunState] = useState("");
  const [runArtifactId, setRunArtifactId] = useState<string | null>(null);
  const [runInvocationId, setRunInvocationId] = useState<string | null>(null);
  const [actualPlacement, setActualPlacement] = useState<Record<
    string,
    unknown
  > | null>(null);

  const contextualAction = contextualCapabilityActions(items, selectedIds).find(
    (action) => action.id === o.id && action.kind === o.kind,
  );
  const {
    value: runInput,
    setDraft: setRunInput,
    recovered: runInputRecovered,
  } = useDurableDraft(
    `capability:${o.kind}:${o.id}`,
    contextualAction?.input || "",
  );

  const resourceRef = qualifiedRef(o.kind, o.id);

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
  }, [o.kind, o.id]);

  useEffect(() => {
    setActualPlacement(null);
  }, [o.kind, o.id]);

  const capRaw = "capability" in o.ref ? o.ref.capability : null;
  const capability = (capRaw && typeof capRaw === "object" ? capRaw : {}) as Record<string, unknown>;
  const readiness = (capability.readiness && typeof capability.readiness === "object"
    ? capability.readiness
    : { state: "unavailable", detail: "No model configured" }) as { state: string; detail?: string };
  const inputSchema = capability.input_schema as { required?: string[] } | undefined;
  const effectClasses = capability.effect_classes as string[] | undefined;
  const supportedPlacements = (capability.supported_placements || ["this_machine"]) as string[];
  const capabilityCanRun =
    readiness.state === "ready" &&
    inputSchema?.required?.includes("input") &&
    effectClasses?.includes("creates_artifact");
  const runLabel =
    contextualAction?.label ||
    String(capability.action_label || "") ||
    (o.kind === "recipe" ? `Ask ${o.title}` : `Run ${o.title}`);

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
      );
    setRunOut(result.output);
    setRunWarning(result.warning || "");
    setRunState(result.state);
    setRunArtifactId(result.artifactId);
    setRunInvocationId(result.invocationId);
    setActualPlacement(result.actualPlacement);
    setRunBusy(false);
  };

  return (
    <section className="desk-pullout-capability">
      {readiness.state !== "ready" ? (
        <SurfaceState error={readiness.detail || "Unavailable"} />
      ) : null}
      <div className="desk-chat-well">
        <div className="desk-chat-composer">
          <MicButton
            label={`Speak to fill ${runLabel.toLowerCase()} material`}
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
            title={String(capability.input_help ?? "")}
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
              !runInput.trim()
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
        {o.kind === "recipe" ? (
          <div className="desk-chat-well-foot">
            <ContextualAssignment
              label="Run assignment"
              capabilityId="recipe.run"
              scope={{
                kind: "subject",
                subject_kind: "recipe",
                subject_id: o.id,
                capability_id: "recipe.run",
              }}
            />
          </div>
        ) : null}
      </div>
      {runInputRecovered ? (
        <span className="quiet">Recovered local run material.</span>
      ) : null}
      <div className="desk-pullout-capability-foot">
        <span className="quiet">
          Runs on{" "}
          {supportedPlacements
            .map((value: string) => humanizeWireValue(value))
            .join(" · ")}
          {effectClasses?.length
            ? ` · ${effectClasses
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
          Assignments
        </button>
      </div>
      {runWarning && <span className="desk-run-warning"><span aria-hidden="true">{String.fromCodePoint(0x26A0)}</span> {runWarning}</span>}
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
          Receipt
          {actualPlacement?.model
            ? ` · ${String(actualPlacement.model)}`
            : ""}
          {runState ? ` · ${humanizeWireValue(runState)}` : ""}
        </p>
      )}
    </section>
  );
}
