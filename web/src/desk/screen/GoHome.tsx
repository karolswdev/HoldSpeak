import { useMemo } from "react";
import { Button } from "../../components/signal/Signal";
import { useDesk } from "../store";
import { KIND_GLYPH } from "../tools";
import { openProjectRoom } from "../shell";
import { phoneGo } from "../components/DeskMenuBar";
import { VERBS, verbLabel, type VerbContext } from "../verbRegistry";
import { WorkMenuSep, type WorkMenuEntry } from "../components/DeskMenu";
import { SurfaceSection } from "../surface/Surface";
import { qualifiedRef } from "../api";
import { rootDirectories } from "./compose";
import { openScreenRef } from "./open";

/** The phone Go face uses the same rows and actions as the menu-bar Go.
 * Four frequent doors belong to the Dock; this is the complete Go index. */
export function GoHome() {
  const projects = useDesk((state) => state.projects);
  const items = useDesk((state) => state.items);
  const selectedIds = useDesk((state) => state.selectedIds);
  const ctx: VerbContext = { selectedRef: selectedIds.length === 1 ? selectedIds[0] : null };
  const sections = useMemo(() => {
    const row = (verbId: string, label?: string): WorkMenuEntry | null => {
      const verb = VERBS.find((candidate) => candidate.id === verbId);
      // Betterment shell S0 (UX-CANON A.11): a verb that cannot run is withheld.
      if (!verb || verb.ghost(ctx)) return null;
      return {
        type: "item",
        id: verb.id,
        label: label ?? verbLabel(verb, ctx),
        glyph: verb.glyph,
        onSelect: () => verb.run(ctx),
      };
    };
    const go = phoneGo(row, projects ?? [], openProjectRoom);
    const drawers = rootDirectories(items);
    if (drawers.length) {
      const at = go.findIndex((entry) => entry.id === "go-new-sep");
      go.splice(at < 0 ? go.length : at, 0, {
        type: "sep", id: "go-drawers-sep",
      }, {
        type: "sub", id: "go-drawers", label: "Drawers",
        entries: drawers.map((directory) => {
          const ref = qualifiedRef("directory", directory.id);
          return { type: "item" as const, id: ref, label: directory.name || "Drawer", glyph: KIND_GLYPH.zone, onSelect: () => openScreenRef(ref) };
        }),
      });
    }
    return [
      {
        id: "go-apps", label: "Apps",
        entries: go.filter((entry) => (entry.type === "item" && !entry.id.startsWith("go-project-")) || entry.id === "go-places-sep"),
      },
      {
        id: "go-projects", label: "Projects",
        entries: go.filter((entry) => entry.type === "item" && entry.id.startsWith("go-project-")),
      },
      ...go.filter((entry): entry is Extract<WorkMenuEntry, { type: "sub" }> => entry.type === "sub"),
    ].filter((section) => section.entries.length > 0);
  }, [projects, items, ctx.selectedRef]);

  return (
    <section className="desk-go-home" aria-label="Go">
      <div className="desk-go-home-list desk-menu-list" role="menu" aria-label="Go menu" data-menu-context="launcher">
        {sections.map((section) => (
          <SurfaceSection key={section.id} label={section.label} className="desk-go-home-group">
            {section.entries.map((entry, index) => entry.type === "sep"
              ? <WorkMenuSep key={entry.id ?? index} />
              : entry.type === "item" ? <GoRow key={entry.id} entry={entry} /> : null)}
          </SurfaceSection>
        ))}
      </div>
    </section>
  );
}

function GoRow({ entry }: { entry: Extract<WorkMenuEntry, { type: "item" }> }) {
  return (
    <Button
      variant="chrome"
      role="menuitem"
      className="desk-go-home-row"
      data-object-id={entry.id.startsWith("zone:") ? entry.id : undefined}
      onClick={() => entry.onSelect()}
    >
      <span className="desk-menu-glyph" aria-hidden="true">{entry.glyph ?? KIND_GLYPH.project}</span>
      <span className="desk-menu-label">{entry.label}</span>
    </Button>
  );
}
