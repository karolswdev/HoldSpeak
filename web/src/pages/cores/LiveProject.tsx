/** The existing project link, scoped to this meeting rather than the live session. */
import { useState } from "react";
import { apiFetch } from "../../lib/api";
import { asRows, useResource } from "../pageSupport";
import { useAction } from "./core-hooks";
import { ActionNotice, CycleGadget, InspectorForm, PaneInspector } from "../../desk/surface";
import { linkMeetingPath } from "../../desk/AddToProject";

export function LiveProject({ meetingId, onCancel, onAdded }: {
  meetingId: string;
  onCancel(): void;
  onAdded(name: string): void;
}) {
  const projects = useResource<Record<string, unknown>>("/api/projects", {});
  const [picked, setPicked] = useState("");
  const action = useAction();
  const rows = asRows(projects.data, ["projects"]).filter(row => !row.is_archived);
  const selected = rows.find(row => String(row.id) === picked) ?? (!picked ? rows[0] : undefined);
  const add = () => action.run(async () => {
    if (!selected) return;
    await apiFetch(linkMeetingPath(String(selected.id), meetingId), { method: "POST" });
    onAdded(String(selected.name || "Project"));
  });
  return <PaneInspector label="Add to project" testId="live-project"><InspectorForm fit="rows"
    rows={[{ label: "Project", control: <CycleGadget roster label="Project" value={String(selected?.id ?? "")} options={rows.map(row => ({ value: String(row.id), label: String(row.name || "Project") }))} disabled={projects.loading || action.busy} onChange={setPicked} /> }]}
    notice={projects.error ? <ActionNotice tone="danger" action={{label:"Try again",onClick:()=>void projects.reload()}}>{projects.error}</ActionNotice> : action.message ? <ActionNotice tone="danger">{action.message}</ActionNotice> : !projects.loading && !rows.length ? <ActionNotice tone="info">No projects</ActionNotice> : undefined}
    completion={{ cancel: onCancel, cancelDisabled: action.busy, primary: {label:"Add",disabled:!selected || projects.loading,busy:action.busy,run:()=>void add()} }}
  /></PaneInspector>;
}
