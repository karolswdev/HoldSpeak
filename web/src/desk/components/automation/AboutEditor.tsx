/** Betterment A5 — About, in place under its line (DESIGN §4).
 *
 * The chips he chose (each named, each with Remove), then the one About
 * picker (`../about/AboutPicker`, the same picker Ask uses). A press adds
 * the pick and saves at once; the typed text stays. People come from the
 * People list (read once; no list when People is not set up). */
import { useEffect, useMemo, useState } from "react";
import { useDesk } from "../../store";
import { apiFetch } from "../../../lib/api";
import { Button } from "../../../components/signal/Signal";
import { AboutPicker, aboutCandidates, type AboutCandidate } from "../about/AboutPicker";
import type { AutomationSource } from "./model";

/** The People list's names (the palette reads the same route). */
function usePeopleNames(): Array<{ id: string; name: string }> {
  const [people, setPeople] = useState<Array<{ id: string; name: string }>>([]);
  useEffect(() => {
    let live = true;
    void apiFetch<{ relationships?: Array<Record<string, unknown>> }>("/api/people/relationships")
      .then((answer) => {
        if (!live) return;
        setPeople((answer?.relationships ?? [])
          .map((row) => ({ id: String(row.id ?? ""), name: String(row.display_name ?? "") }))
          .filter((row) => row.id && row.name));
      })
      .catch(() => undefined); // People not set up: no people to find
    return () => { live = false; };
  }, []);
  return people;
}

export function AboutChips({
  sources,
  onRemove,
  busy = false,
}: {
  sources: AutomationSource[];
  onRemove?: (ref: string) => void;
  busy?: boolean;
}) {
  if (!sources.length) return null;
  return (
    <span className="automation-chips" data-testid="automation-about-chips">
      {sources.map((source) => {
        const name = source.missing ? "Missing source" : source.label;
        return (
          <span key={source.ref} className="surface-token" data-chip=""
            data-tone={source.missing ? "warn" : undefined}>
            {name}
            {onRemove ? (
              <Button dense variant="ghost" className="automation-chip-remove" disabled={busy}
                aria-label={`Remove ${name}`} onClick={() => onRemove(source.ref)}>
                ✕
              </Button>
            ) : null}
          </span>
        );
      })}
    </span>
  );
}

export function AboutEditor({
  sources,
  busy,
  onChange,
}: {
  sources: AutomationSource[];
  busy: boolean;
  onChange: (refs: string[]) => void;
}) {
  const items = useDesk((state) => state.items);
  const people = usePeopleNames();
  const candidates = useMemo(() => aboutCandidates(items, people), [items, people]);
  const refs = sources.map((source) => source.ref);
  const add = (pick: AboutCandidate) => {
    if (!refs.includes(pick.ref)) onChange([...refs, pick.ref]);
  };
  return (
    <div className="automation-about-editor" data-testid="automation-about-editor">
      <AboutChips sources={sources} busy={busy} onRemove={(ref) => onChange(refs.filter((r) => r !== ref))} />
      <AboutPicker candidates={candidates} picked={refs} onPick={add} busy={busy} />
    </div>
  );
}
