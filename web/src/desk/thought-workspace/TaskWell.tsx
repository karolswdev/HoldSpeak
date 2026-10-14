import { useEffect, useState } from "react";
import { apiFetch, readableError } from "../../lib/api";
import { Button } from "../../components/signal/Signal";
import { CycleGadget, StringGadget } from "../surface/gadgets";

type Person = { id?: string; display_name?: string };

export function TaskWell({
  noteId,
  initialText,
  onAdded,
  onClose,
}: {
  noteId: string;
  initialText: string;
  onAdded(receipt: string): void;
  onClose(): void;
}) {
  const [task, setTask] = useState(initialText);
  const [owner, setOwner] = useState("Me");
  const [due, setDue] = useState("");
  const [people, setPeople] = useState<Person[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let live = true;
    void apiFetch<{ relationships?: Person[] }>("/api/people/relationships")
      .then((body) => { if (live) setPeople(body.relationships ?? []); })
      .catch(() => undefined);
    return () => { live = false; };
  }, []);

  const add = async () => {
    if (!task.trim() || busy) return;
    setBusy(true);
    setError("");
    try {
      await apiFetch("/api/door/items", {
        method: "POST",
        json: {
          task: task.trim(),
          owner: owner || "Me",
          due: due || null,
          source_type: "thought",
          source_ref: `note:${noteId}`,
        },
      });
      onAdded(`Task added${owner && owner !== "Me" ? ` · ${owner}` : ""}`);
      onClose();
    } catch (cause) {
      setError(readableError(cause));
    } finally {
      setBusy(false);
    }
  };

  const options = [
    { value: "Me", label: "Me" },
    ...people
      .filter((person) => String(person.display_name ?? "").trim())
      .map((person) => ({ value: String(person.display_name), label: String(person.display_name) })),
  ];

  return (
    <div className="thought-action-well" data-testid="thought-task-well">
      <StringGadget label="Task" caption value={task} onChange={setTask} disabled={busy} />
      <div className="thought-action-well-row">
        <CycleGadget label="Who" value={owner} options={options} onChange={setOwner} disabled={busy} />
        <StringGadget label="When" type="date" value={due} onChange={setDue} disabled={busy} />
      </div>
      {error ? <span className="surface-token" data-tone="danger" role="alert">{error}</span> : null}
      <span className="thought-action-well-verbs">
        <Button dense variant="primary" loading={busy} disabled={!task.trim()} onClick={() => void add()}>Add</Button>
        <Button dense variant="ghost" disabled={busy} onClick={onClose}>Close</Button>
      </span>
    </div>
  );
}
