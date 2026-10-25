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
 *
 *  Window grammar (2026-10-24): `density="dense"` is the native list view
 *  of a collection window: 30 px rows (44 px in a surface of 520 px or
 *  less), sans 12/600 sentence-case headers, sans 13 cells, a state as a
 *  dot and a word, the whole selected row in the selection blue, a hover
 *  tint, no zebra; the list fills its container and scrolls inside it.
 *  `columns` lets the provider declare its own columns (and order); a
 *  column whose key is not a built-in reads `row.cells[key]`.
 */
import { useEffect, useMemo, useRef, type CSSProperties, type KeyboardEvent, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { LampGadget } from "../gadgets";
import { useRovingRows } from "../roving";
import { listSprite } from "../../sprites";
import { lampGadgetTone, objectKindWord, objectSprite, type ObjectTone } from "./kinds";
import { nameBreaks } from "./DeskIcon";
import "./objects.css";

export type ObjectSortKey = "name" | "kind" | "when" | "state";
export interface ObjectSort {
  key: ObjectSortKey;
  dir: "asc" | "desc";
}
/** A sort over any declared column (the built-ins or a provider's own). */
export interface ObjectListSort {
  key: string;
  dir: "asc" | "desc";
}
/** A provider-declared column (window grammar): `key` is a built-in
 *  (`name`, `kind`, `when`, `state`) or a key of `row.cells`. */
export interface ObjectListColumn {
  key: string;
  /** The header word, sentence case (`Length`, `Summary`). */
  word: string;
  /** The grid track (default `minmax(0, 1fr)` for name, `120px` else). */
  track?: string;
}

/** A row state's tone: the object tones and `idle` (grey). */
export type ObjectListTone = ObjectTone | "idle";

export interface ObjectListRow {
  id: string;
  kind: string;
  name: string;
  kindWord?: string;
  /** The When word (`TODAY`, `OCT 5`, `42 MIN`). */
  when?: string;
  /** The sort value for When (e.g. epoch ms); the word sorts when absent. */
  whenSort?: number;
  /** One lamp + its word; omitted = an empty State cell. `idle` is the
   *  plain grey dot (nothing is happening: Idle, Not installed, Quiet).
   *  `live` marks a running state (`data-live` on the dot and word). */
  state?: { label: string; tone: ObjectListTone; testId?: string; live?: boolean };
  /** A person's row: a 24 px initials disc in the person's hue leads the
   *  row in place of the sprite (`hue` 0..7, `hueOf` in kit.tsx). */
  avatar?: { initials: string; hue: number };
  /** Provider cells for declared `columns` (keyed by column key). */
  cells?: Record<string, ReactNode>;
  /** Sort values for provider cells (a string cell sorts by its text). */
  sortValues?: Record<string, string | number>;
  /** A data-testid on the name text. */
  nameTestId?: string;
  sprite?: string;
  /** PHILO-14 A2: rows sort within their group first (a lower group draws
   *  above): the Floor keeps its zones (folders) above its objects. */
  group?: number;
}

const COLUMNS: ObjectListColumn[] = [
  { key: "name", word: "Name" },
  { key: "kind", word: "Kind" },
  { key: "when", word: "When" },
  { key: "state", word: "State" },
];

function sortRows(rows: ObjectListRow[], sort: ObjectListSort): ObjectListRow[] {
  const value = (row: ObjectListRow): string | number => {
    switch (sort.key) {
      case "name":
        return row.name;
      case "kind":
        return row.kindWord ?? objectKindWord(row.kind);
      case "when":
        return row.whenSort ?? row.when ?? "";
      case "state":
        return row.sortValues?.state ?? row.state?.label ?? "";
      default: {
        const given = row.sortValues?.[sort.key];
        if (given != null) return given;
        const cell = row.cells?.[sort.key];
        return typeof cell === "string" || typeof cell === "number" ? cell : "";
      }
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
  sort: ObjectListSort;
  /** Name is always shown. Omitted keeps all four columns for existing callers. */
  visibleColumns?: readonly ObjectSortKey[];
  /** Window grammar: the provider's own columns, in order (wins over
   *  `visibleColumns`). Name is always first. */
  columns?: readonly ObjectListColumn[];
  /** Window grammar: `dense` is the native list view (30 px rows). */
  density?: "default" | "dense";
  /** A press on a header: the caller flips or moves the sort. The key is a
   *  built-in sort key, or a declared column's key when `columns` is given
   *  (method form: a caller may take `string`). */
  onSort?(key: ObjectSortKey): void;
  selectedId?: string | null;
  /** PHILO-14 A2: a set selection (the Floor's Ask context). When given it
   *  wins over `selectedId`: every row in it is a selected row. */
  selectedIds?: readonly string[];
  /** Words a selected row adds to its accessible name (`in Ask context`). */
  selectedLabel?: string;
  onSelect?(id: string): void;
  onOpen?(id: string): void;
  /** PHILO-17 U30: extra props for a row (the Room's FILES: a filed object
   *  drags onto an agent, as the drawer's icons did). */
  rowProps?(row: ObjectListRow): Record<string, unknown>;
  className?: string;
}

export function ObjectList({
  label,
  rows,
  sort,
  visibleColumns,
  columns: declared,
  density = "default",
  onSort,
  selectedId,
  selectedIds,
  selectedLabel,
  onSelect,
  onOpen,
  rowProps,
  className,
}: ObjectListProps) {
  const bodyRef = useRef<HTMLDivElement>(null);
  // Dense: a touch tap opens (the phone's list view has no double press);
  // a mouse press selects and a double press or Enter opens.
  const touchPress = useRef(false);
  useRovingRows(bodyRef, { selector: ".object-list-open" });
  const sorted = useMemo(() => sortRows(rows, sort), [rows, sort]);
  const dense = density === "dense";
  const columns: ObjectListColumn[] = declared
    ? [declared.find((column) => column.key === "name") ?? COLUMNS[0], ...declared.filter((column) => column.key !== "name")]
    : COLUMNS.filter((column) => column.key === "name" || !visibleColumns || visibleColumns.includes(column.key as ObjectSortKey));
  const compactColumns = columns.length <= 2;
  const declaredTrack = (key: string) => declared?.find((column) => column.key === key)?.track;
  const tracks = columns.map((column) => declaredTrack(column.key) ?? (column.key === "name" ? "minmax(0, 1fr)"
    : column.key === "kind" ? "128px" : column.key === "when" ? "104px" : declared ? "120px" : "160px")).join(" ");
  const phoneTracks = columns.map((column) => column.key === "name" ? "minmax(0, 1fr)" : "84px").join(" ");
  const has = (key: string) => columns.some((column) => column.key === key);
  // Dense: the selected row stays in view (a restored or reopened row).
  const scrollTo = selectedIds ? null : selectedId;
  useEffect(() => {
    if (!dense || !scrollTo) return;
    const row = bodyRef.current?.querySelector<HTMLElement>(`[data-object-id="${CSS.escape(scrollTo)}"]`);
    row?.scrollIntoView?.({ block: "nearest" });
  }, [dense, scrollTo]);

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
      data-density={dense ? "dense" : undefined}
      data-compact-columns={compactColumns || undefined}
      style={{ "--object-list-columns": tracks, "--object-list-phone-columns": phoneTracks } as CSSProperties}
      role="grid"
      aria-label={label}
      aria-rowcount={rows.length + 1}
    >
      <div className="object-list-head" role="row">
        {columns.map((column) => {
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
                onClick={() => onSort?.(column.key as ObjectSortKey)}
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
          // The fold line (≤ 520 px): only filled cells show, and a middle
          // dot joins two filled cells; the first filled cell leads the
          // line (no orphan dot when an earlier cell is empty).
          const foldKeys = columns.slice(1).map((column) => column.key).filter((key) => key !== "state");
          const filled = (key: string) => {
            const value = key === "kind" ? kindWord : key === "when" ? row.when : row.cells?.[key];
            return value != null && value !== "" && value !== false;
          };
          const foldLead = foldKeys.find(filled);
          const fold = (key: string) => filled(key) ? (key === foldLead ? "lead" : "next") : undefined;
          const cellWords = columns
            .filter((column) => !["name", "kind", "when", "state"].includes(column.key))
            .map((column) => row.cells?.[column.key])
            .filter((cell): cell is string => typeof cell === "string" && cell.length > 0);
          return (
            <div
              key={row.id}
              role="row"
              className="object-list-row"
              aria-selected={selected ? "true" : "false"}
              data-selected={selected ? "true" : undefined}
              data-object-id={row.id}
              data-avatar={row.avatar ? "" : undefined}
              {...(rowProps ? rowProps(row) : {})}
            >
              <div role="gridcell" className="object-list-name" data-col="name">
                <Button
                  variant="chrome"
                  className="object-list-open"
                  aria-label={(declared
                    ? [row.name, has("kind") ? kindWord : undefined, has("when") ? row.when : undefined, ...cellWords, has("state") ? row.state?.label : undefined, selected ? selectedLabel : undefined]
                    : [row.name, kindWord, row.when, row.state?.label, selected ? selectedLabel : undefined])
                    .filter(Boolean)
                    .join(", ")}
                  onPointerDown={dense ? (event) => { touchPress.current = event.pointerType === "touch"; } : undefined}
                  onClick={() => {
                    onSelect?.(row.id);
                    if (dense && touchPress.current && onOpen) onOpen(row.id);
                    touchPress.current = false;
                  }}
                  onDoubleClick={onOpen ? () => onOpen(row.id) : undefined}
                  onKeyDown={keyDown(row.id)}
                >
                  {row.avatar ? (
                    <span className="object-list-avatar" data-hue={row.avatar.hue} aria-hidden="true">
                      {row.avatar.initials}
                    </span>
                  ) : (
                    <img
                      src={listSprite(row.sprite ?? objectSprite(row.kind, row.id))}
                      alt=""
                      draggable={false}
                    />
                  )}
                  <span className="object-list-name-text">
                    <span className="object-list-name-word" title={row.name} data-testid={row.nameTestId}>{nameBreaks(row.name)}</span>
                    {dense ? null : (
                      <span className="object-list-fold" aria-hidden="true">
                        {has("kind") ? <span className="object-list-fold-token">{kindWord}</span> : null}
                        {has("when") && row.when ? <span className="object-list-fold-token">{row.when}</span> : null}
                      </span>
                    )}
                  </span>
                </Button>
              </div>
              {columns.slice(1).map((column) => {
                switch (column.key) {
                  case "kind":
                    return <div key="kind" role="gridcell" className="object-list-cell" data-col="kind" data-fold={fold("kind")}>{kindWord}</div>;
                  case "when":
                    return <div key="when" role="gridcell" className="object-list-cell" data-col="when" data-fold={fold("when")}>{row.when ?? ""}</div>;
                  case "state":
                    return (
                      <div key="state" role="gridcell" className="object-list-state" data-col="state">
                        {row.state ? (
                          dense ? (
                            <span className="object-list-dot-word" data-tone={row.state.tone} data-live={row.state.live ? "" : undefined} data-testid={row.state.testId}>
                              <span className="kit-dot" data-tone={row.state.tone} aria-hidden="true" />
                              {row.state.label}
                            </span>
                          ) : (
                            <LampGadget label={row.state.label} on={row.state.tone !== "idle"} tone={row.state.tone === "idle" ? undefined : lampGadgetTone(row.state.tone)} />
                          )
                        ) : null}
                      </div>
                    );
                  default:
                    return (
                      <div key={column.key} role="gridcell" className="object-list-cell" data-col={column.key} data-fold={fold(column.key)}>
                        {row.cells?.[column.key] ?? ""}
                      </div>
                    );
                }
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
}
