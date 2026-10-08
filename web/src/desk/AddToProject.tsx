/** PHILO-15 16 (B37): a meeting joins a Project.
 *
 *  `Add to Project ▸`: ONE library Button that opens the DeskMenu species
 *  (WorkMenu, the same species the Floor's `Send to ▸` and a folded strip
 *  open) with the desk's Projects; a check marks a Project the meeting is in.
 *  A pick writes the link the hub already has (`POST
 *  /api/projects/{id}/meetings/{mid}`, `project.link`, one receipt); the
 *  Project's drawer then lists the meeting as a member. The receipt is one
 *  token beside the Button: `IN <PROJECT>`, or `NOT ADDED · <reason>`.
 */
import { useMemo, useRef, useState, type MouseEvent } from "react";
import { Button } from "../components/signal/Signal";
import { apiFetch } from "../lib/api";
import { WorkMenu, type WorkMenuEntry } from "./components/DeskMenu";
import { useDesk } from "./store";
import { plainFailure } from "./surface/plainFailure";
import "./addToProject.css";

export const meetingProjectsPath = (meetingId: string) =>
  `/api/meetings/${encodeURIComponent(meetingId)}/projects`;
export const linkMeetingPath = (projectId: string, meetingId: string) =>
  `/api/projects/${encodeURIComponent(projectId)}/meetings/${encodeURIComponent(meetingId)}`;

export function AddToProject({
  meetingId,
  variant = "ghost",
  className,
  onReceipt,
}: {
  meetingId: string;
  variant?: "ghost" | "secondary";
  className?: string;
  /** A face with a receipt slot (a footer) shows the receipt there; without
   *  it the token sits beside the Button. */
  onReceipt?: (receipt: { text: string; tone: "ok" | "danger" }) => void;
}) {
  const allProjects = useDesk((s) => s.projects);
  const projects = useMemo(() => allProjects.filter((p) => !p.is_archived), [allProjects]);
  const [at, setAt] = useState<{ x: number; y: number; keys: boolean } | null>(null);
  const [linked, setLinked] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [receipt, setOwnReceipt] = useState<{ text: string; tone: "ok" | "danger" } | null>(null);
  const setReceipt = (next: { text: string; tone: "ok" | "danger" } | null) => {
    if (onReceipt && next) onReceipt(next);
    else setOwnReceipt(next);
  };
  const buttonRef = useRef<HTMLButtonElement | null>(null);
  // No Project on the desk: no verb that does nothing (UX-CANON A.11).
  if (!meetingId || !projects.length) return null;

  const open = (event: MouseEvent<HTMLButtonElement>) => {
    if (at) {
      setAt(null);
      return;
    }
    const r = event.currentTarget.getBoundingClientRect();
    setAt({ x: r.left, y: r.bottom, keys: event.detail === 0 });
    // The Projects the meeting is in carry a check (a read; the menu opens at once).
    apiFetch<{ projects?: { project_id: string }[] }>(meetingProjectsPath(meetingId))
      .then((body) => setLinked((body.projects ?? []).map((p) => String(p.project_id))))
      .catch(() => setLinked([]));
  };

  const add = async (projectId: string, name: string) => {
    if (linked.includes(projectId)) {
      setReceipt({ text: `IN ${name.toUpperCase()}`, tone: "ok" });
      return;
    }
    setBusy(true);
    setReceipt(null);
    try {
      await apiFetch(linkMeetingPath(projectId, meetingId), { method: "POST" });
      setLinked((now) => [...now, projectId]);
      setReceipt({ text: `IN ${name.toUpperCase()}`, tone: "ok" });
      void useDesk.getState().refresh();
    } catch (reason) {
      setReceipt({ text: plainFailure("NOT ADDED", reason), tone: "danger" });
    } finally {
      setBusy(false);
    }
  };

  const entries: WorkMenuEntry[] = projects.map((p) => ({
    type: "item" as const,
    id: `add-to-project.${p.id}`,
    label: p.name || "Untitled Project",
    checked: linked.includes(p.id),
    onSelect: () => void add(p.id, p.name || "Untitled Project"),
  }));

  return (
    <span className={["add-to-project", className].filter(Boolean).join(" ")} data-testid="add-to-project">
      <Button
        ref={buttonRef}
        dense
        variant={variant}
        loading={busy}
        aria-haspopup="menu"
        aria-expanded={Boolean(at)}
        data-testid="add-to-project-button"
        onClick={open}
        onKeyDown={(e) => {
          // Escape closes the menu and stops here: the window stays open.
          if (e.key === "Escape" && at) {
            e.preventDefault();
            e.stopPropagation();
            setAt(null);
          }
        }}
      >
        Add to Project ▸
      </Button>
      {receipt ? (
        <span className="surface-token" data-tone={receipt.tone} role="status" data-testid="add-to-project-receipt">
          {receipt.text}
        </span>
      ) : null}
      {at ? (
        <WorkMenu
          className="desk-head-menu"
          label="Add to Project"
          x={at.x}
          y={at.y}
          entries={entries}
          autoFocus={at.keys}
          returnFocus={() => buttonRef.current?.focus()}
          onClose={() => setAt(null)}
        />
      ) : null}
    </span>
  );
}
