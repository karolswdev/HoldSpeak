import { useState } from "react";
import { apiFetch, readableError } from "../../lib/api";
import { Button } from "../../components/signal/Signal";
import { CycleGadget } from "../surface/gadgets";
import { useDesk } from "../store";

export function ProjectWell({
  noteId,
  onAdded,
  onClose,
}: {
  noteId: string;
  onAdded(receipt: string): void;
  onClose(): void;
}) {
  const projects = useDesk((state) => state.projects).filter((project) => !project.is_archived);
  const [projectId, setProjectId] = useState(projects[0]?.id ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const project = projects.find((item) => item.id === projectId);

  const add = async () => {
    if (!project || busy) return;
    setBusy(true);
    setError("");
    try {
      await apiFetch(
        `/api/projects/${encodeURIComponent(project.id)}/resources/${encodeURIComponent(`note:${noteId}`)}`,
        { method: "PUT", json: { relationship: "related" } },
      );
      onAdded(`In ${project.name || "project"}`);
      onClose();
    } catch (cause) {
      setError(readableError(cause));
    } finally {
      setBusy(false);
    }
  };

  if (!projects.length) return null;
  return (
    <div className="thought-action-well" data-testid="thought-project-well">
      <CycleGadget
        label="Project"
        value={projectId}
        options={projects.map((item) => ({ value: item.id, label: item.name || "Untitled project" }))}
        onChange={setProjectId}
        disabled={busy}
      />
      {error ? <span className="surface-token" data-tone="danger" role="alert">{error}</span> : null}
      <span className="thought-action-well-verbs">
        <Button dense variant="primary" loading={busy} disabled={!project} onClick={() => void add()}>Add</Button>
        <Button dense variant="ghost" disabled={busy} onClick={onClose}>Close</Button>
      </span>
    </div>
  );
}
