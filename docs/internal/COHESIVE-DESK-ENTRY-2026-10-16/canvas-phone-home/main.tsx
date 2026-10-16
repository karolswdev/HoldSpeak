// Direction only: shared menu material, real library controls and actual Dock.
import { createRoot } from "react-dom/client";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import "@w/desk/screen/screen.css";
import { Button } from "@w/components/signal/Signal";
import { SurfaceSection } from "@w/desk/surface/Surface";
import { Dock } from "@w/desk/components/window/Dock";
import { WorkMenuSep, type WorkMenuEntry } from "@w/desk/components/DeskMenu";
import { phoneGo } from "@w/desk/components/DeskMenuBar";
import { VERBS, verbLabel, type VerbContext } from "@w/desk/verbRegistry";
import { KIND_GLYPH } from "@w/desk/tools";
import { EMPTY_ITEMS, fromWireDirectory, qualifiedRef } from "@w/desk/api";
import { rootDirectories } from "@w/desk/screen/compose";
import { openScreenRef } from "@w/desk/screen/open";
import { openProjectRoom } from "@w/desk/shell";
import "./canvas.css";

type Item = Extract<WorkMenuEntry, { type: "item" }>;
const ctx: VerbContext = { selectedRef: null };
const projects = [{ id: "project_canvas_migration", name: "Architecture migration — release readiness and rollback checkpoints" }];
const directories = [
  fromWireDirectory({ id: "dir_canvas_meetings", name: "Meetings", parent_id: null, member_ids: [], created_at: "2026-10-16T00:00:00Z" })!,
  fromWireDirectory({ id: "dir_canvas_architecture", name: "Architecture decisions and platform migration review records", parent_id: null, member_ids: [], created_at: "2026-10-16T00:00:00Z" })!,
];
function row(id: string, label?: string): WorkMenuEntry | null {
  const verb = VERBS.find(candidate => candidate.id === id);
  if (!verb) return null;
  return { type: "item", id: verb.id, label: label ?? verbLabel(verb, ctx), glyph: verb.glyph, ghost: verb.ghost(ctx), onSelect: () => verb.run(ctx) };
}
const entries = phoneGo(row, projects, openProjectRoom);
const drawers = rootDirectories({ ...EMPTY_ITEMS, directory: directories });
const at = entries.findIndex(entry => entry.id === "go-new-sep");
entries.splice(at, 0, { type: "sep", id: "go-drawers-sep" }, {
  type: "sub", id: "go-drawers", label: "Drawers", entries: drawers.map(directory => {
    const ref = qualifiedRef("directory", directory.id);
    return { type: "item", id: ref, label: directory.name, glyph: KIND_GLYPH.zone, onSelect: () => openScreenRef(ref) };
  }),
});
const sections = [
  { id: "go-apps", label: "Apps", entries: entries.filter(entry => (entry.type === "item" && !entry.id.startsWith("go-project-")) || entry.id === "go-places-sep") },
  { id: "go-projects", label: "Projects", entries: entries.filter(entry => entry.type === "item" && entry.id.startsWith("go-project-")) },
  ...entries.filter((entry): entry is Extract<WorkMenuEntry, { type: "sub" }> => entry.type === "sub"),
];

function GoRow({ entry }: { entry: Item }) {
  // A declared visual ghost specimen; the registry remains unchanged.
  const reason = entry.id === "go-project-project_canvas_migration" ? "Unavailable" : entry.ghost;
  return <Button variant="chrome" role="menuitem" className={`desk-go-home-row${reason ? " is-ghost" : ""}`} data-object-id={entry.id.startsWith("zone:") ? entry.id : undefined} aria-disabled={reason ? true : undefined} onClick={() => { if (!reason) entry.onSelect(); }}>
    <span className="desk-menu-glyph" aria-hidden="true">{entry.glyph ?? KIND_GLYPH.project}</span>
    <span className="desk-menu-label">{entry.label}</span>
    {reason ? <span className="desk-go-home-reason quiet">{reason}</span> : null}
  </Button>;
}
function Canvas() {
  return <main className="desk-next canvas-desk"><div className="desk-screen"><section className="desk-go-home" aria-label="Go"><div className="desk-go-home-list desk-menu-list" role="menu" aria-label="Go menu" data-menu-context="launcher">
    {sections.filter(section => section.entries.length > 0).map(section => <SurfaceSection key={section.id} label={section.label} className="desk-go-home-group">{section.entries.map((entry, index) => entry.type === "sep" ? <WorkMenuSep key={entry.id ?? index}/> : entry.type === "item" ? <GoRow key={entry.id} entry={entry}/> : null)}</SurfaceSection>)}
  </div></section></div><Dock/></main>;
}
createRoot(document.getElementById("root")!).render(<Canvas/>);
