import { useMemo } from "react";
import { Button } from "../../components/signal/Signal";
import { useDesk } from "../store";
import { KIND_GLYPH } from "../tools";
import { openProjectRoom } from "../shell";
import { phoneGo } from "../components/DeskMenuBar";
import { VERBS, verbLabel, type VerbContext } from "../verbRegistry";
import type { WorkMenuEntry } from "../components/DeskMenu";

/** The phone Go face uses the same rows and actions as the menu-bar Go.
 * Four frequent doors belong to the Dock; this is the complete Go index. */
export function GoHome() {
  const projects = useDesk((state) => state.projects);
  const selectedIds = useDesk((state) => state.selectedIds);
  const ctx: VerbContext = { selectedRef: selectedIds.length === 1 ? selectedIds[0] : null };
  const entries = useMemo(() => {
    const row = (verbId: string, label?: string): WorkMenuEntry | null => {
      const verb = VERBS.find((candidate) => candidate.id === verbId);
      if (!verb) return null;
      return {
        type: "item",
        id: verb.id,
        label: label ?? verbLabel(verb, ctx),
        glyph: verb.glyph,
        ghost: verb.ghost(ctx),
        onSelect: () => verb.run(ctx),
      };
    };
    return phoneGo(row, projects ?? [], openProjectRoom);
  }, [projects, ctx.selectedRef]);

  return (
    <section className="desk-go-home" aria-label="Go">
      <div className="desk-go-home-list" role="menu" aria-label="Go menu">
        {entries.map((entry, index) => {
          if (entry.type === "sep") {
            return <span key={entry.id ?? `go-sep-${index}`} role="separator" className="desk-go-home-sep" />;
          }
          if (entry.type === "sub") {
            return (
              <div key={entry.id} className="desk-go-home-group">
                <h2 className="desk-go-home-group-title">{entry.label}</h2>
                {entry.entries.filter((child): child is Extract<WorkMenuEntry, { type: "item" }> => child.type === "item").map((child) => <GoRow key={child.id} entry={child} />)}
              </div>
            );
          }
          return <GoRow key={entry.id} entry={entry} />;
        })}
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
      aria-disabled={entry.ghost ? true : undefined}
      onClick={() => { if (!entry.ghost) entry.onSelect(); }}
    >
      <span className="desk-go-home-glyph" aria-hidden="true">{entry.glyph ?? KIND_GLYPH.project}</span>
      <span>{entry.label}</span>
      {entry.ghost ? <span className="desk-go-home-reason">{entry.ghost}</span> : null}
    </Button>
  );
}
