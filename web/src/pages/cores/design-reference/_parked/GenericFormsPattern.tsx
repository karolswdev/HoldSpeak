/* Parked generic form specimen: replaced by the real Settings You pattern.
 * Kept as history; it is not part of the live Components reference. */
import { useEffect, useRef, useState } from "react";
import { Button } from "../../../../components/signal/Signal";
import { ActionNotice, CycleGadget, GadgetRow, StateChip, StringGadget } from "../../../../desk/surface";
import "./GenericFormsPattern.css";

type ExampleState = "ordinary" | "busy" | "failed" | "empty" | "long";

export function LegacyFormsPattern({ state }: { state: ExampleState }) {
  const [title, setTitle] = useState("Sprint review notes");
  const [scope, setScope] = useState("Project room");
  const [savedTitle, setSavedTitle] = useState("Sprint review notes");
  const [savedScope, setSavedScope] = useState("Project room");
  const [lifecycle, setLifecycle] = useState<"idle" | "saving" | "failed" | "saved" | "invalid">("idle");
  const saveTimer = useRef<number | null>(null);

  useEffect(() => {
    if (saveTimer.current !== null) {
      window.clearTimeout(saveTimer.current);
      saveTimer.current = null;
    }
    if (state === "busy") setLifecycle("saving");
    if (state === "failed") setLifecycle("failed");
    if (state === "empty") setTitle("");
    if (state === "ordinary") {
      setTitle("Sprint review notes");
      setLifecycle("idle");
    }
    if (state === "long") {
      setTitle("Sprint review notes for the local release review and owner handoff");
      setLifecycle("idle");
    }
  }, [state]);

  useEffect(() => () => {
    if (saveTimer.current !== null) window.clearTimeout(saveTimer.current);
  }, []);

  const dirty = title !== savedTitle || scope !== savedScope;
  const beginSave = () => {
    if (!title.trim()) {
      setLifecycle("invalid");
      return;
    }
    setLifecycle("saving");
    const valueAtStart = { title, scope };
    if (saveTimer.current !== null) window.clearTimeout(saveTimer.current);
    saveTimer.current = window.setTimeout(() => {
      setSavedTitle(valueAtStart.title);
      setSavedScope(valueAtStart.scope);
      setLifecycle("saved");
      saveTimer.current = null;
    }, 120);
  };
  const retry = () => {
    if (!title.trim()) {
      setLifecycle("invalid");
      return;
    }
    const valueAtStart = { title, scope };
    setLifecycle("saving");
    if (saveTimer.current !== null) window.clearTimeout(saveTimer.current);
    saveTimer.current = window.setTimeout(() => {
      setSavedTitle(valueAtStart.title);
      setSavedScope(valueAtStart.scope);
      setLifecycle("saved");
      saveTimer.current = null;
    }, 120);
  };
  const message = lifecycle === "invalid"
    ? "Title required."
    : lifecycle === "failed"
      ? "Save failed."
      : lifecycle === "saving"
        ? "Saving."
        : lifecycle === "saved"
          ? dirty ? "Saved · newer edits remain." : "Saved."
          : dirty ? "Unsaved changes."
            : "Ready to edit.";

  return (
    <section className="reference-example" data-testid="reference-form" aria-label="Form pattern">
      <div className="reference-example-head">
        <div>
          <h2>Project note</h2>
        </div>
        <StateChip state={lifecycle === "failed" ? "failure" : lifecycle === "saving" ? "working" : lifecycle === "saved" ? "success" : lifecycle === "invalid" ? "warning" : "active"} label={lifecycle === "idle" ? (dirty ? "DIRTY" : "READY") : lifecycle.toUpperCase()} />
      </div>
      <div className="reference-form-fields">
        <GadgetRow label="Title">
          <StringGadget label="Project note title" value={title} placeholder="PROJECT NOTE TITLE" onChange={(next) => { setTitle(next); if (lifecycle === "saved") setLifecycle("idle"); }} />
        </GadgetRow>
        <GadgetRow label="Scope">
          <CycleGadget label="Project scope" value={scope} options={[{ value: "Project room", label: "Project room" }, { value: "Team record", label: "Team record" }]} onChange={setScope} />
        </GadgetRow>
      </div>
      <ActionNotice tone={lifecycle === "failed" || lifecycle === "invalid" ? "danger" : lifecycle === "saved" ? "ok" : "info"} icon={lifecycle === "saved" ? "✓" : lifecycle === "failed" || lifecycle === "invalid" ? "!" : "·"} action={lifecycle === "failed" ? { label: "Retry", onClick: retry } : undefined}>
        {message}
      </ActionNotice>
      <div className="reference-actions">
        <Button variant="primary" disabled={lifecycle === "saving"} loading={lifecycle === "saving"} onClick={beginSave}>Save note</Button>
        {lifecycle === "saved" ? <Button variant="ghost" onClick={() => setLifecycle("idle")}>Continue editing</Button> : null}
      </div>
    </section>
  );
}

