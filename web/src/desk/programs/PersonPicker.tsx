/* Programs "Person" (2026-11-08): who reviews the person-gated steps. The
 * same grammar as the Agent and Review rows (RunsOnPicker): a ghost Button
 * that opens a WorkMenu. The rows are the desk's one People roster read
 * (`loadPeople`, the screen's members store: readiness, then the list),
 * read when the menu opens, never on the first paint. */
import { useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { WorkMenu, type WorkMenuEntry } from "../components/DeskMenu";
import { loadPeople, useScreenMembersStore } from "../screen/members";

export interface PersonChoice {
  id: string;
  name: string;
}

/** The quiet word when no person is chosen. */
export const NOBODY = "Nobody yet";

export function PersonPicker({ value, onPick, disabled, "data-testid": testId }: {
  value: PersonChoice | null;
  onPick(choice: PersonChoice | null): void;
  disabled?: boolean;
  "data-testid"?: string;
}) {
  const opener = useRef<HTMLButtonElement | null>(null);
  const [open, setOpen] = useState(false);
  const [reading, setReading] = useState(false);
  const people = useScreenMembersStore((state) => state.people);
  const toggle = () => {
    const next = !open;
    setOpen(next);
    if (next) {
      setReading(true);
      void loadPeople().finally(() => setReading(false));
    }
  };
  const rect = open ? opener.current?.getBoundingClientRect() : null;
  const persons = people?.state === "ready" ? people.persons : [];
  const note = reading && !people ? "Reading People…"
    : people?.state === "failed" ? "People did not load"
      : people?.state === "locked" ? "People is not set up"
        : people && !persons.length ? "No people yet" : "";
  const entries: WorkMenuEntry[] = [
    { type: "item", id: "nobody", label: NOBODY, checked: value ? undefined : "exclusive", onSelect: () => onPick(null) },
    { type: "sep", id: "people" },
    ...persons.map((person): WorkMenuEntry => ({
      type: "item", id: `person:${person.id}`, label: person.name,
      checked: value?.id === person.id ? "exclusive" : undefined,
      onSelect: () => onPick({ id: person.id, name: person.name }),
    })),
    ...(note ? [{ type: "note" as const, id: "note", label: note }] : []),
  ];
  return (
    <>
      <Button ref={opener} dense variant="ghost" className="pg-runs-on" aria-haspopup="menu" aria-expanded={open}
        disabled={disabled} onClick={toggle} data-testid={testId}>
        {value ? value.name : NOBODY}
        <svg className="kit-toolbar-more-caret" width={10} height={10} viewBox="0 0 10 10" fill="none" stroke="currentColor"
          strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
          <path d="M2.5 3.75L5 6.25l2.5-2.5" />
        </svg>
      </Button>
      {open && rect ? (
        <WorkMenu label="Person" x={rect.left} y={rect.bottom} opener={opener.current} autoFocus
          returnFocus={() => opener.current?.focus()} entries={entries} onClose={() => setOpen(false)} />
      ) : null}
    </>
  );
}
