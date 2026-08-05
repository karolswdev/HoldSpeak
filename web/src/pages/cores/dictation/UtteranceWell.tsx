// The durable-draft textarea with the deliver/rehearse button row.
import { Button } from "../../../components/signal/Signal";
import { openSurfaceOr } from "../../../desk/shell";
import { RunsOnPicker } from "../../../desk/components/RunsOnPicker";
import { PadGadget, StringGadget } from "../../../desk/surface/gadgets";
import type { InferenceTarget } from "../../../desk/api";

export function UtteranceWell({
  utterance,
  setUtterance,
  projectRoot,
  setProjectRoot,
  busy,
  error,
  previewOnly,
  actions,
  targets,
  targetId,
  onRun,
  onDeliver,
  onRunElsewhere,
  onKeepDraft,
}: {
  utterance: string;
  setUtterance: (next: string) => void;
  projectRoot: string;
  setProjectRoot: (next: string) => void;
  busy: boolean;
  error: string;
  previewOnly: boolean;
  actions: string[];
  targets: InferenceTarget[];
  targetId: string;
  onRun: () => void;
  onDeliver: (text: string) => void;
  onRunElsewhere: (id: string) => void;
  onKeepDraft: () => void;
}) {
  return (
    <>
      <div className="speak-well">
        <PadGadget
          label="Utterance"
          value={utterance}
          onChange={setUtterance}
          mic={false}
          placeholder="UTTERANCE"
        />
      </div>
      <div className="surface-actions speak-run-row">
        <Button
          variant="primary"
          loading={busy}
          disabled={!utterance.trim()}
          onClick={() => (previewOnly ? void onRun() : void onDeliver(utterance))}
        >
          {previewOnly
            ? error && actions.includes("retry")
              ? "Retry rehearsal"
              : "Rehearse"
            : error && actions.includes("retry")
              ? "Retry delivery"
              : "Deliver"}
        </Button>
        <span className="speak-grounding">
          <span className="speak-grounding-label">Grounding</span>
          <StringGadget
            label="Project root: optional grounding scope, saved only on this device"
            placeholder="project root"
            value={projectRoot}
            onChange={setProjectRoot}
          />
        </span>
      </div>
      {error ? (
        <div className="surface-actions">
          {actions.includes("copy") ? (
            <Button
              dense
              onClick={() => void navigator.clipboard.writeText(utterance)}
            >
              Copy
            </Button>
          ) : null}
          {actions.includes("keep_as_note") ? (
            <Button dense onClick={onKeepDraft}>
              Keep as Note
            </Button>
          ) : null}
          {actions.includes("setup") ? (
            <Button
              dense
              variant="secondary"
              onClick={() => openSurfaceOr("configure-setup", "/setup")}
            >
              Setup
            </Button>
          ) : null}
        </div>
      ) : null}
      {error && actions.includes("alternate_runs_on") && targets.length ? (
        <RunsOnPicker
          targets={targets}
          selectedId={targetId}
          onChange={(id) => void onRunElsewhere(id)}
          disabled={busy}
        />
      ) : null}
    </>
  );
}
