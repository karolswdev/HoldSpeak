/** Shared capability run section — used by recipe, chain, workflow pullouts
 * (HS-117-15). Manages all run-related state internally. */
import { useEffect, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiRequest } from "../../../lib/api";
import { useDurableDraft } from "../../../lib/durableDraft";
import { useDesk } from "../../store";
import { openSurfaceOr } from "../../shell";
import { qualifiedRef } from "../../api";
import { ContextualAssignment } from "../../../pages/cores/ContextualAssignment";
import { Material } from "../../surface/Material";
import { DotWord } from "../../surface/kit";
import { PadGadget } from "../../surface/gadgets";
import { humanizeWireValue } from "../../../lib/productLanguage";
import {
  contextualCapabilityActions,
} from "../../contextual";
import type { WorldObject } from "../../world";

export function CapabilitySection({ object: o, blocked }: {
  object: WorldObject;
  /** The window knows why it cannot run yet (an empty Sequence): this one
   *  line replaces the hub's reason under a greyed Run. */
  blocked?: string;
}) {
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

  // W2-BUILDER (atlas 2026-10-27): the material and its Run, nothing else.
  // A greyed Run says why in one line beside it; where it runs is the Run's
  // hover title (UX-CANON A.9: no placement chip on a working window); the
  // engine choice is the window's toolbar verb.
  const runReason = runBusy
    ? ""
    : blocked
      ? blocked
      : !capabilityCanRun
      ? capabilityBlockedWords(readiness)
      : !runInput.trim()
        ? `Type the material, then press ${o.kind === "recipe" ? "Ask" : "Run"}.`
        : "";
  const placementWords = supportedPlacements
    .filter((value) => !value.includes(":"))
    .map((value) => humanizeWireValue(value));
  const runTitle = [
    placementWords.length ? `Runs on ${placementWords.join(" or ").toLowerCase()}` : "",
    effectClasses?.includes("creates_artifact") ? "keeps the result" : "",
  ].filter(Boolean).join(", ");

  return (
    <section className="desk-pullout-capability" data-testid="capability-section">
      <div className="desk-chat-well">
        <div className="desk-chat-composer desk-capability-composer">
          <PadGadget
            label={runLabel}
            value={runInput}
            placeholder="Material"
            rows={7}
            inputProps={{ title: String(capability.input_help ?? "") }}
            onChange={setRunInput}
            micLabel={`Speak to fill ${runLabel.toLowerCase()} material`}
            micDraftScope={`capability:${o.kind}:${o.id}`}
          />
          <Button
            dense
            variant={o.kind === "recipe" ? "ghost" : "primary"}
            loading={runBusy}
            title={runTitle || undefined}
            onClick={() => void run()}
            disabled={
              runBusy ||
              Boolean(blocked) ||
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
          </Button>
        </div>
        {o.kind === "recipe" ? (
          <div className="desk-chat-well-foot">
            <ContextualAssignment
              label="Which engine runs it"
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
      {runReason ? (
        <DotWord tone={capabilityCanRun && !blocked ? "idle" : "warn"} className="capability-run-reason" data-testid="capability-run-reason">
          {runReason}
        </DotWord>
      ) : null}
      {runInputRecovered ? (
        <span className="quiet">Recovered local run material.</span>
      ) : null}
      {runWarning && <span className="desk-run-warning"><span aria-hidden="true">{String.fromCodePoint(0x26A0)}</span> {runWarning}</span>}
      {runOut && (
        <div className="surface-aerogel">
          <Material>{runOut}</Material>
        </div>
      )}
      {runArtifactId && (
        <Button
          dense
          onClick={() => openPullout(runArtifactId)}
        >
          Open kept Artifact
        </Button>
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

/** The one line a greyed Run says: the hub's reason in plain words. */
export function capabilityBlockedWords(readiness: { state: string; detail?: string }): string {
  const detail = String(readiness.detail || "").trim();
  if (/no model configured/i.test(detail)) return "No engine is chosen for this. Choose engine.";
  // The hub's machine words for an empty Sequence: the window's own empty
  // state says what to do (Add mode).
  if (/linear sequence/i.test(detail)) return "Add a mode, then type the material.";
  return detail || "This cannot run yet.";
}

/** The window toolbar's engine verb: opens Runs on with this object. */
export function openCapabilityEngines(o: WorldObject): void {
  openSurfaceOr("configure-runs-on", "/profiles", qualifiedRef(o.kind, o.id));
}
