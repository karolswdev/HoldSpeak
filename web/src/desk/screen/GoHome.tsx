import { useMemo } from "react";
import { ZoneRenameRow } from "../components/ZoneRenameRow";
import { Button } from "../../components/signal/Signal";
import { useDesk } from "../store";
import { KIND_GLYPH } from "../tools";
import { openProjectRoom } from "../shell";
import { phoneGo } from "../components/DeskMenuBar";
import { VERBS, verbLabel, type VerbContext } from "../verbRegistry";
import { WorkMenuSep, type WorkMenuEntry } from "../components/DeskMenu";
import { SurfaceSection } from "../surface/Surface";
import { qualifiedRef } from "../api";
import { visibleRootDirectories } from "./compose";
import { openScreenRef } from "./open";
import { useBuilderTools } from "../builderTools";
import { useLaunchers } from "../components/window/launcherRegistry";

/** The phone Go face uses the same rows and actions as the menu-bar Go
 * (betterment shell S1: the manifest's Go groups); this is the complete Go
 * index. */
export function GoHome() {
  const projects = useDesk((state) => state.projects);
  const items = useDesk((state) => state.items);
  const selectedIds = useDesk((state) => state.selectedIds);
  const ctx: VerbContext = { selectedRef: selectedIds.length === 1 ? selectedIds[0] : null };
  const launchers = useLaunchers();
  const builder = useBuilderTools((state) => state.on);
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
    // Betterment shell S1: the same rows as Go, in the same order. A
    // separator starts a section; a submenu after a separator is its own
    // section (Builder, New); a submenu inside a section draws its rows in
    // place, under its name (Projects, Drawers).
    const go = phoneGo({
      row,
      projects: projects ?? [],
      openProject: openProjectRoom,
      drawers: visibleRootDirectories(items).map((d) => ({ ref: qualifiedRef("directory", d.id), name: d.name })),
      openDrawer: openScreenRef,
      launchers,
      builder,
    });
    const out: { id: string; label: string; entries: WorkMenuEntry[]; sub?: boolean }[] = [];
    let current = { id: "go-apps", label: "Apps", entries: [] as WorkMenuEntry[] };
    out.push(current);
    for (let i = 0; i < go.length; i++) {
      const entry = go[i];
      if (entry.type === "sep") {
        const next = go[i + 1];
        if (next?.type === "sub") {
          out.push({ id: next.id, label: next.label, entries: next.entries, sub: true });
          i += 1;
          current = { id: `${next.id}-after`, label: "", entries: [] };
          out.push(current);
          continue;
        }
        current = { id: entry.id ?? `go-sep-${i}`, label: SECTION_LABEL[entry.id ?? ""] ?? "", entries: [] };
        out.push(current);
        continue;
      }
      current.entries.push(entry);
    }
    return out.filter((section) => section.entries.length > 0);
  }, [projects, items, ctx.selectedRef, launchers, builder]);

  return (
    <section className="desk-go-home" aria-label="Go">
      <div className="desk-go-home-list desk-menu-list" role="menu" aria-label="Go menu" data-menu-context="launcher">
        {sections.map((section) => (
          <SurfaceSection key={section.id} label={section.label} className={`desk-go-home-group${section.sub ? " is-sub" : ""}`}>
            {section.entries.map((entry, index) => entry.type === "sub"
              ? (
                <SurfaceSection key={entry.id} label={entry.label} className="desk-go-home-group desk-go-home-sub">
                  {entry.entries.map((inner) => inner.type === "item" ? <GoRow key={inner.id} entry={inner} /> : null)}
                </SurfaceSection>
              )
              : entry.type === "sep"
                ? <WorkMenuSep key={entry.id ?? index} />
                : entry.type === "item" ? <GoRow key={entry.id} entry={entry} /> : null)}
          </SurfaceSection>
        ))}
      </div>
    </section>
  );
}

/** The section names of the phone home, by the separator that opens them. */
const SECTION_LABEL: Record<string, string> = { "go-work-sep": "Work" };

function GoRow({ entry }: { entry: Extract<WorkMenuEntry, { type: "item" }> }) {
  const renamingDrawer = useDesk((state) => state.renamingZoneId);
  if (renamingDrawer && entry.id === `zone:${renamingDrawer}`) {
    return <ZoneRenameRow zoneId={renamingDrawer} title={typeof entry.label === "string" ? entry.label : "New drawer"} placement="inrow" />;
  }
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
