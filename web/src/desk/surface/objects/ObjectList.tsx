/** PHILO-14 B1 — ObjectList: a drawer's list view (board A-2L; 393: A-2).
 *
 *  A real list, not a text-mode one: columns Name (sprite + name), Kind,
 *  When, State (one lamp + its word). The header is a strip of sort gadgets
 *  (raised; the active one sunken, `aria-sort` on its column header). A row
 *  is selected by a press; the selection IS the row (the blue plate) — no
 *  `[ ]` mark. In a narrow `surface` container (520 px or less) Kind and
 *  When fold under the name (the FoldLine of DeskListView, without its
 *  marks) and the row stays at least 44 px tall.
 *
 *  Keyboard: one Tab stop; arrows walk the rows (useRovingRows); Space
 *  selects; Enter (or a double press) opens.
 */
import { useMemo, useRef, type KeyboardEvent } from "react";
import { Button } from "../../../components/signal/Signal";
import { LampGadget } from "../gadgets";
import { useRovingRows } from "../roving";
import { listSprite } from "../../sprites";
import { lampGadgetTone, objectKindWord, objectSprite, type ObjectTone } from "./kinds";
import "./objects.css";

export type ObjectSortKey = "name" | "kind" | "when" | "state";
export interface ObjectSort {
  key: ObjectSortKey;
  dir: "asc" | "desc";
}

export interface ObjectListRow {
  id: string;
  kind: string;
  name: string;
  kindWord?: string;
  /** The When word (`TODAY`, `OCT 5`, `42 MIN`). */
  when?: string;
  /** The sort value for When (e.g. epoch ms); the word sorts when absent. */
  whenSort?: number;
  /** One lamp + its word; omitted = an empty State cell. */
  state?: { label: string; tone: ObjectTone };
  sprite?: string;
  /** PHILO-14 A2: rows sort within their group first (a lower group draws
   *  above): the Floor keeps its zones (folders) above its objects. */
  group?: number;
}

const COLUMNS: { key: ObjectSortKey; word: string }[] = [
  { key: "name", word: "Name" },
  { key: "kind", word: "Kind" },
  { key: "when", word: "When" },
  { key: "state", word: "State" },
];

function sortRows(rows: ObjectListRow[], sort: ObjectSort): ObjectListRow[] {
  const value = (row: ObjectListRow): string | number => {
    switch (sort.key) {
      case "kind":
        return row.kindWord ?? objectKindWord(row.kind);
      case "when":
        return row.whenSort ?? row.when ?? "";
      case "state":
        return row.state?.label ?? "";
      default:
        return row.name;
    }
  };
  const sign = sort.dir === "asc" ? 1 : -1;
  return [...rows].sort((a, b) => {
    const grouped = (a.group ?? 0) - (b.group ?? 0);
    if (grouped) return grouped;
    const va = value(a);
    const vb = value(b);
    const order =
      typeof va === "number" && typeof vb === "number"
        ? va - vb
        : String(va).localeCompare(String(vb));
    return order * sign || a.name.localeCompare(b.name);
  });
}

export interface ObjectListProps {
  /** The list's accessible name (e.g. `Payments ledger cutover`). */
  label: string;
  rows: ObjectListRow[];
  sort: ObjectSort;
  /** A press on a header: the caller flips or moves the sort. */
  onSort?(key: ObjectSortKey): void;
  selectedId?: string | null;
  /** PHILO-14 A2: a set selection (the Floor's Ask context). When given it
   *  wins over `selectedId`: every row in it is a selected row. */
  selectedIds?: readonly string[];
  /** Words a selected row adds to its accessible name (`in Ask context`). */
  selectedLabel?: string;
  onSelect?(id: string): void;
  onOpen?(id: string): void;
  className?: string;
}

export function ObjectList({
  label,
  rows,
  sort,
  onSort,
  selectedId,
  selectedIds,
  selectedLabel,
  onSelect,
  onOpen,
  className,
}: ObjectListProps) {
  const bodyRef = useRef<HTMLDivElement>(null);
  useRovingRows(bodyRef, { selector: ".object-list-open" });
  const sorted = useMemo(() => sortRows(rows, sort), [rows, sort]);

  // Enter OPENS on keydown (its native click prevented); every other
  // activation — pointer, Space, element.click(), assistive press — is ONE
  // click and SELECTS.
  const keyDown = (id: string) => (event: KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      onOpen?.(id);
    }
  };
  return (
    <div
      className={`object-list${className ? ` ${className}` : ""}`}
      role="grid"
      aria-label={label}
      aria-rowcount={rows.length + 1}
    >
      <div className="object-list-head" role="row">
        {COLUMNS.map((column) => {
          const active = sort.key === column.key;
          return (
            <div
              key={column.key}
              role="columnheader"
              className="object-list-th"
              data-col={column.key}
              aria-sort={active ? (sort.dir === "asc" ? "ascending" : "descending") : "none"}
            >
              <Button
                variant="chrome"
                className="object-list-sort"
                aria-pressed={active ? "true" : "false"}
                onClick={() => onSort?.(column.key)}
              >
                {column.word}
                {active ? (
                  <span className="object-list-sort-mark" aria-hidden="true">
                    {sort.dir === "asc" ? "▲" : "▼"}
                  </span>
                ) : null}
              </Button>
            </div>
          );
        })}
      </div>
      <div className="object-list-rows" role="rowgroup" ref={bodyRef}>
        {sorted.map((row) => {
          const selected = selectedIds ? selectedIds.includes(row.id) : row.id === selectedId;
          const kindWord = row.kindWord ?? objectKindWord(row.kind);
          return (
            <div
              key={row.id}
              role="row"
              className="object-list-row"
              aria-selected={selected ? "true" : "false"}
              data-selected={selected ? "true" : undefined}
              data-object-id={row.id}
            >
              <div role="gridcell" className="object-list-name" data-col="name">
                <Button
                  variant="chrome"
                  className="object-list-open"
                  aria-label={[row.name, kindWord, row.when, row.state?.label, selected ? selectedLabel : undefined]
                    .filter(Boolean)
                    .join(", ")}
                  onClick={() => onSelect?.(row.id)}
                  onDoubleClick={onOpen ? () => onOpen(row.id) : undefined}
                  onKeyDown={keyDown(row.id)}
                >
                  <img
                    src={listSprite(row.sprite ?? objectSprite(row.kind, row.id))}
                    alt=""
                    draggable={false}
                  />
                  <span className="object-list-name-text">
                    <span className="object-list-name-word">{row.name}</span>
                    <span className="object-list-fold" aria-hidden="true">
                      <span className="object-list-fold-token">{kindWord}</span>
                      {row.when ? <span className="object-list-fold-token">{row.when}</span> : null}
                    </span>
                  </span>
                </Button>
              </div>
              <div role="gridcell" className="object-list-cell" data-col="kind">
                {kindWord}
              </div>
              <div role="gridcell" className="object-list-cell" data-col="when">
                {row.when ?? ""}
              </div>
              <div role="gridcell" className="object-list-state" data-col="state">
                {row.state ? (
                  <LampGadget label={row.state.label} on tone={lampGadgetTone(row.state.tone)} />
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
