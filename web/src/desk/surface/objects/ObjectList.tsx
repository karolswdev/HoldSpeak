import { MiddleText } from "../MiddleText";
import { hasWords, labelCaption } from "../content";
import { sentenceChildren } from "../words";
import { faceTimeWords } from "../format";
import { useGuideView } from "../../walk/viewState";
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
 *  selects; Enter opens.
 *
 *  W1-KIT (2026-10-27) — one press opens: in a dense collection list a
 *  plain press OPENS the row's object (objects open, Phase 14). A ⌘-, ⌃- or
 *  shift-press, Space and a programmatic click select only; Enter opens the
 *  focused row. `pressOpens={false}` keeps press-to-select for a list whose
 *  open is an act (Setup's readiness rows run their fix).
 *
 *  On a narrow surface (520 px or less) the rows fold to two lines, so the
 *  column header is hidden and the sort lives in a dense "Sort" verb in the
 *  nearest toolbar's sort slot (kit Toolbar), or in place when no toolbar
 *  holds one.
 *
 *  Window grammar (2026-10-24): `density="dense"` is the native list view
 *  of a collection window: 30 px rows (44 px in a surface of 520 px or
 *  less), sans 12/600 sentence-case headers, sans 13 cells, a state as a
 *  dot and a word, the whole selected row in the selection blue, a hover
 *  tint, no zebra; the list fills its container and scrolls inside it.
 *  `columns` lets the provider declare its own columns (and order); a
 *  column whose key is not a built-in reads `row.cells[key]`.
 */
import { Children, cloneElement, isValidElement, useContext, useEffect, useId, useLayoutEffect, useMemo, useRef, useState, type CSSProperties, type KeyboardEvent, type MouseEvent, type ReactNode } from "react";
import { PaneNotice, PaneNoticeContext } from "../patterns/PreferencePane";
import { PaneViewContext, paneViewEntries } from "../patterns/PaneViews";
import { fitStrip } from "../fitStrip";
import { createPortal } from "react-dom";
import { Lamp, type LampProps } from "../live/Lamp";
import { Meter, type MeterProps } from "../live/Meter";
import { Button } from "../../../components/signal/Signal";
import { GadgetLabelContext, SelectionFieldContext, LampGadget, CheckGadget, CycleGadget } from "../gadgets";
import { useRovingRows } from "../roving";
import { useWholeRows } from "./wholeRows";
import { listSprite } from "../../sprites";
import { stateTone, Toolbar, DotWord, VERB_OVERFLOW_WORD } from "../kit";
import { useStripFit } from "../stripMenu";
import { lampGadgetTone, objectKindWord, objectSprite, type ObjectTone } from "./kinds";
import { nameBreaks } from "./DeskIcon";
import "./objects.css";
import "./selection-list.css";
import { ListPaneDepth } from "../patterns/ListPane";
import { useWindowId } from "../../components/window/windowIdContext";
import { publishListMenu, clearListMenu, ownsListMenu } from "../../components/window/listMenu";
import { WorkMenu, type WorkMenuEntry } from "../../components/DeskMenu";

function SelectionState({state}: {state: Omit<NonNullable<ObjectListRow["state"]>, "tone"> & {tone: ObjectListTone | "parked"}}) {
  return <span className="object-list-dot-word" title={state.label} data-tone={state.tone} data-live={state.live ? "" : undefined} data-testid={state.testId}><span className="kit-dot" data-tone={state.tone} aria-hidden="true" /><span>{sentenceChildren(state.label)}</span></span>;
}

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
  /** Dense-list track. Selection-list facts use their measured content width. */
  track?: string;
  /** Larger numbers stay longer when this list's own container narrows. */
  priority?: number;
  /** Minimum for editable cells and dense lists, including cell padding. */
  minWidth?: number;
}

/** A row state's tone: the object tones and `idle` (grey). */
export type ObjectListTone = ObjectTone | "idle";

export interface ObjectListRow {
  id: string;
  kind: string;
  name: string;
  kindWord?: string;
  /** Optional second line in the same selection row. */
  detail?: ReactNode;
  leadingLamp?: LampProps;
  meter?: MeterProps;
  /** The meter follows this fact column; omitted, it follows the name. */
  meterColumn?: string;
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

/** Text state components still use the same ellipsis and full-value title as
 * plain cells. Editors retain their own input and focus ownership. */
function spokenCell(value: ReactNode): string {
  if(typeof value === "string" || typeof value === "number") return String(value);
  if(Array.isArray(value)) return value.map(spokenCell).join(" ");
  return isValidElement<{children?:ReactNode}>(value) ? spokenCell(value.props.children) : "";
}

function cellContent(value: ReactNode): ReactNode {
  if (typeof value === "string" || typeof value === "number") return <span className="object-list-value" title={String(value)}>{value}</span>;
  if (isValidElement<{ children: ReactNode; title?: string }>(value) && value.type === DotWord && typeof value.props.children === "string") {
    return cloneElement(value, { title: value.props.title ?? value.props.children }, <span className="object-list-value">{value.props.children}</span>);
  }
  return value ?? "";
}

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

/** One declaration feeds the selection bar, context menu and app menu.
 * Without enabled, a verb needs a selection. Collection verbs explicitly allow null. */
export interface ListVerb {
  variant?: "primary" | "stop";
  /** Menu-only verbs stay in the app/context menu and Actions. */
  toolbar?: boolean;
  dispatching?: boolean;
  id: string;
  label: string;
  key?: string;
  symbol?: "+" | "−";
  testId?: string;
  /** Destination disclosure at the act, shared by all three verb faces. */
  title?: string;
  enabled?: (selection: ObjectListRow | null) => boolean;
  run(selection: ObjectListRow | null): void;
  items?: readonly ListVerb[];
}

function listVerbEnabled(verb: ListVerb, selection: ObjectListRow | null): boolean {
  return verb.enabled?.(selection) ?? Boolean(selection);
}

export function listVerbEntries(verbs: readonly ListVerb[], selection: ObjectListRow | null): WorkMenuEntry[] {
  return verbs.map((verb) => verb.items && listVerbEnabled(verb, selection)
    ? { type: "sub", id: verb.id, label: verb.label, entries: listVerbEntries(verb.items, selection) }
    : { type: "item", id: verb.id, label: verb.label, keycap: verb.key === "Enter" ? "Return" : verb.key, title: verb.title,
      disabled: !listVerbEnabled(verb, selection),
      onSelect: () => { if (listVerbEnabled(verb, selection)) verb.run(selection); } });
}

/** A list scope is data, shared by the Find row and its folded menu. */
export type ListScope = { id: string; label: string; disabled?: boolean } & (
  | { kind: "tick"; checked: boolean; onChange(checked: boolean): void }
  | { kind: "cycle"; value: string; options: readonly {value: string; label: string}[]; onChange(value: string): void }
);
function scopeEntries(scopes: readonly ListScope[]): WorkMenuEntry[] {
  return scopes.map(scope => scope.kind === "tick"
    ? {type:"item",id:`scope-${scope.id}`,label:scope.label,checked:scope.checked,disabled:scope.disabled,onSelect:()=>scope.onChange(!scope.checked)}
    : {type:"sub",id:`scope-${scope.id}`,label:scope.label,entries:scope.options.map(option => ({type:"item",id:`scope-${scope.id}-${option.value}`,label:option.label,checked:option.value === scope.value,disabled:scope.disabled,onSelect:()=>scope.onChange(option.value)}))});
}

export interface ObjectListProps {
  /** The list's accessible name (e.g. `Payments ledger cutover`). */
  label: string;
  rows: ObjectListRow[];
  /** One empty message in the list well; no selectable placeholder row. */
  empty?: string;
  /** Captions name rowgroups; they are never rows or keyboard stops. */
  groups?: readonly { id: number; label: string; count?: number | true; tone?: "ask"; more?: ListVerb }[];
  sort?: ObjectListSort;
  /** Name is always shown. Omitted keeps all four columns for existing callers. */
  visibleColumns?: readonly ObjectSortKey[];
  /** Window grammar: the provider's own columns, in order (wins over
   *  `visibleColumns`). Name stays present in the declared order. */
  columns?: readonly ObjectListColumn[];
  /** A names-only preference list needs no column caption. */
  headerless?: boolean;
  /** Window grammar: `dense` is the native list view (30 px rows). */
  density?: "default" | "dense";
  /** OS selection grammar: 26 px rows, no row verbs, one selected row. */
  selection?: boolean;
  verbs?: readonly ListVerb[];
  /** A row menu can use a subset of the same declared verbs. */
  rowVerbs?: readonly ListVerb[];
  /** End a bounded well on whole rows; on by default for every list. */
  wholeRows?: boolean;
  /** The object window draws the published selection entries in its toolbar. */
  externalToolbar?: boolean;
  /** Draw the declared verbs above the list, with an optional find field. */
  toolbar?: { trailing?: ReactNode; scopes?: readonly ListScope[]; testId?: string };
  defaultVerb?: string;
  /** Keep input order for a chain or an authored list of jobs. */
  ordered?: boolean;
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
  /** Give back an empty selection after a local guide. */
  onClearSelection?(): void;
  onOpen?(id: string): void;
  /** W1-KIT: a plain press opens the row (default: on for a dense list).
   *  False keeps press-to-select (a list whose open is an act). */
  pressOpens?: boolean;
  /** PHILO-17 U30: extra props for a row (the Room's FILES: a filed object
   *  drags onto an agent, as the drawer's icons did). */
  rowProps?(row: ObjectListRow): Record<string, unknown>;
  className?: string;
}

export function ObjectList({
  label,
  empty,
  rows,
  groups,
  sort = { key: "name", dir: "asc" },
  visibleColumns,
  columns: declared,
  headerless = false,
  density = "default",
  selection = false,
  verbs = [],
  rowVerbs, wholeRows = true,
  toolbar, externalToolbar,
  defaultVerb,
  ordered = false,
  onSort,
  selectedId,
  selectedIds,
  selectedLabel,
  onSelect,
  onClearSelection,
  onOpen,
  pressOpens,
  rowProps,
  className,
}: ObjectListProps) {
  const windowId = useWindowId();
  const inner = useContext(ListPaneDepth) > 0 || !toolbar;
  const menuOwner = useId();
  const bodyRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  useRovingRows(bodyRef, { selector: selection ? ".object-list-row" : ".object-list-open" });
  useWholeRows(listRef, bodyRef, wholeRows);
  const [localSelected, setLocalSelected] = useState<string | null>(null);
  const pickedId = selectedId === undefined ? localSelected : selectedId;
  const picked = rows.find((row) => row.id === pickedId) ?? null;
  const [menu, setMenu] = useState<{ x: number; y: number; id: string | null; opener?: HTMLElement } | null>(null);
  const chosen = useRef(pickedId);
  chosen.current = pickedId;
  const choose = (id: string) => {
    const changed = chosen.current !== id;
    chosen.current = id;
    setLocalSelected(id);
    if (changed) onSelect?.(id);
  };
  useGuideView(() => pickedId, (saved) => {
    if (saved === chosen.current) return;
    if (saved) choose(saved);
    else {setLocalSelected(null); chosen.current = null; onClearSelection?.();}
  });
  const openRow = (id: string) => {
    const row = rows.find((entry) => entry.id === id) ?? null;
    const verb = verbs.find((entry) => entry.id === defaultVerb);
    if (verb) {
      if (!listVerbEnabled(verb, row)) return;
      if (verb.items) {
        const opener = [...(bodyRef.current?.querySelectorAll<HTMLElement>(".object-list-row") ?? [])].find(entry => entry.dataset.objectId === id);
        const rect = opener?.getBoundingClientRect();
        setSubmenu(verb.id);
        setMenu({ x: rect?.left ?? 0, y: rect?.bottom ?? 0, id, opener });
      } else verb.run(row);
    }
    else onOpen?.(id);
  };
  const [submenu, setSubmenu] = useState<string | null>(null);
  useEffect(() => {
    if (selection && windowId && ownsListMenu(windowId, menuOwner)) publishListMenu(windowId, menuOwner, listVerbEntries(verbs, picked));
  });
  useEffect(() => {
    if (selection && (toolbar || externalToolbar) && windowId) publishListMenu(windowId, menuOwner, listVerbEntries(verbs, picked));
    return () => { if (windowId) clearListMenu(windowId, menuOwner); };
  }, [windowId, menuOwner, selection, Boolean(toolbar), externalToolbar]);
  const menuRow = rows.find((row) => row.id === menu?.id) ?? null;
  const sorted = useMemo(() => ordered ? rows : sortRows(rows, sort), [rows, sort, ordered]);
  const dense = density === "dense";
  // W1-KIT: a plain press opens a dense list's object.
  const opensOnPress = Boolean(onOpen) && (pressOpens ?? dense);
  // The narrow sort verb rides the nearest toolbar's sort slot.
  const [sortSlot, setSortSlot] = useState<HTMLElement | null>(null);
  useLayoutEffect(() => {
    if (!dense || !onSort) return;
    const found = nearestSortSlot(listRef.current);
    setSortSlot((now) => (now === found ? now : found));
  });
  const declaredColumns: ObjectListColumn[] = declared
    ? (declared.some(column => column.key === "name") ? [...declared] : [COLUMNS[0], ...declared])
    : COLUMNS.filter((column) => column.key === "name" || !visibleColumns || visibleColumns.includes(column.key as ObjectSortKey));
  const [viewport, setViewport] = useState<{compact:boolean; ids:string[]}>({compact:false,ids:[]});
  useLayoutEffect(() => {
    const list = listRef.current, well = bodyRef.current;
    if (!selection || !list || !well) return;
    let frame = 0;
    const update = () => {
      const compact = list.clientWidth > 0 && list.clientWidth <= 520, box = well.getBoundingClientRect();
      const ids = [...well.querySelectorAll<HTMLElement>(".object-list-row")].filter(row => {const r=row.getBoundingClientRect();return r.bottom>box.top+1 && r.top<box.bottom-1;}).map(row=>row.dataset.objectId!);
      setViewport(old => old.compact===compact && old.ids.join("\0")===ids.join("\0") ? old : {compact,ids});
    };
    const schedule = () => {cancelAnimationFrame(frame); frame=requestAnimationFrame(update);};
    const watch = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(schedule);
    watch?.observe(list); watch?.observe(well); well.addEventListener("scroll",schedule,{passive:true}); update();
    return () => {watch?.disconnect();well.removeEventListener("scroll",schedule);cancelAnimationFrame(frame);};
  }, [selection, sorted]);
  const visibleRows = viewport.ids.length ? rows.filter(row=>viewport.ids.includes(row.id)) : rows;
  const columns = declaredColumns.filter(column => !selection || !viewport.compact || column.key==="name" || visibleRows.some(row =>
    row.meter && row.meterColumn===column.key || hasWords(column.key==="state" ? row.state?.label : column.key==="when" ? row.when : column.key==="kind" ? row.kindWord || row.kind : row.cells?.[column.key])));
  const foldIntoName = columns[0]?.key === "when";
  const layoutId = `list-${useId().replace(/:/g, "")}`;
  const [headerWidths, setHeaderWidths] = useState<Record<string, number>>({});
  const [requiredColumns,setRequiredColumns] = useState<string[]>(["state"]);
  const [controlColumns,setControlColumns] = useState<string[]>([]);
  const columnKey = columns.map((column) => `${column.key}:${column.word}`).join("|");
  useLayoutEffect(() => {
    if (!selection || !listRef.current) return;
    const measure = () => {
      const next: Record<string, number> = {};
      const facts = new Set(["state"]), controls = new Set<string>();
      const intrinsic = (node: HTMLElement) => {
        const copy = node.cloneNode(true) as HTMLElement;
        copy.style.cssText = "position:absolute;visibility:hidden;display:flex;width:max-content;max-width:none";
        // Keep the real row/header inheritance, padding and control styles.
        node.parentElement!.append(copy);
        const width = Math.ceil(copy.getBoundingClientRect().width);
        copy.remove();
        return width;
      };
      listRef.current?.querySelectorAll<HTMLElement>(".object-list-th[data-col]").forEach(header => {
        next[header.dataset.col!] = intrinsic(header);
      });
      // Pills are facts, not optional clipped text. Reserve their whole intrinsic width.
      listRef.current?.querySelectorAll<HTMLElement>(".object-list-row [data-col]").forEach(cell=>{
        if (cell.querySelector("button, input, select, textarea, [role=combobox], [role=checkbox], [role=radio]")) controls.add(cell.dataset.col!);
        if (controls.has(cell.dataset.col!) || cell.querySelector(".kit-dotword, .object-list-dot-word")) facts.add(cell.dataset.col!);
        if (cell.dataset.col === "name" || !cell.textContent?.trim()) return;
        // Every row counts, in view or not: a fact column that follows the rows
        // in view changes its width during a scroll and cuts the pills below.
        next[cell.dataset.col!] = Math.max(next[cell.dataset.col!] ?? 0, intrinsic(cell));
      });
      setRequiredColumns(old=>old.join("|")===[...facts].join("|")?old:[...facts]);
      setControlColumns(old=>old.join("|")===[...controls].join("|")?old:[...controls]);
      // A hidden pane has no geometry. Wait for its allocation before fitting.
      if (listRef.current?.clientWidth) setHeaderWidths((old) => JSON.stringify(old) === JSON.stringify(next) ? old : next);
    };
    measure();
    let current = true;
    void document.fonts?.ready.then(() => { if (current) measure(); });
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(measure);
    observer?.observe(listRef.current);
    document.fonts?.addEventListener("loadingdone", measure);
    return () => { current = false; observer?.disconnect(); document.fonts?.removeEventListener("loadingdone", measure); };
  }, [selection, columnKey, sort.key, sort.dir, rows, viewport.ids.join("\0")]);
  const minimum = (column: ObjectListColumn) => selection && column.key !== "name" && !controlColumns.includes(column.key) && headerWidths[column.key]
    ? headerWidths[column.key]
    : Math.max(
    column.minWidth ?? (/^\d+px$/.test(column.track ?? "") ? parseFloat(column.track!) : column.key === "name" ? 96 : 112),
    headerWidths[column.key] ?? column.word.length * 8 + 24,
  );
  const fitTracks = (shown: ObjectListColumn[]) => shown.map((column) => {
    if (column.key === "name") return "minmax(min(96px, 30%), 1fr)";
    if (requiredColumns.includes(column.key) && column.key !== "state") return `minmax(0, ${minimum(column)}px)`;
    return `${minimum(column)}px`;
  }).join(" ");
  // Each rule asks this list's container, so a narrow window on a wide desk
  // drops exactly the same whole columns. The identity column is never removed.
  // Empty viewport columns yield their seat after the normal priority fit;
  // they must not bring lower-priority columns back into the name seat.
  const keptColumns = new Set(columns.map(column=>column.key));
  let shown = [...declaredColumns];
  const dropOrder = declaredColumns.filter(column => column.key !== "name" && !requiredColumns.includes(column.key)).sort((a, b) => (a.priority ?? 0) - (b.priority ?? 0) || declaredColumns.indexOf(b) - declaredColumns.indexOf(a));
  const fitRules = dropOrder.map((column, index) => {
    // A leading time that folds under the name always folds in a compact
    // list (520 px), also when its measured width would fit beside the name.
    const fits = shown.reduce((sum, entry) => sum + minimum(entry), 2);
    const threshold = index === 0 && foldIntoName && ["when", "with"].includes(column.key) ? Math.max(fits, 521) : fits;
    shown = shown.filter((entry) => entry !== column);
    const scope = `[data-list-layout="${layoutId}"]`;
    const folded = foldIntoName && ["when", "with"].includes(column.key) ? `${scope} [data-folded-col="${column.key}"] { display: inline; } ${scope} .object-list-row[data-has-when] { height: var(--object-list-two-line-height); min-height: var(--object-list-two-line-height); }` : "";
    return `@container object-list (width < ${threshold}px) { ${scope} > .object-list-head, ${scope} > .object-list-rows .object-list-row { grid-template-columns: ${fitTracks(shown.filter(column=>keptColumns.has(column.key)))}; } ${scope} [data-col="${column.key}"] { display: none; } ${folded} }`;
  }).join("\n");
  const compactColumns = (selection ? declaredColumns : columns).length <= 2;
  const declaredTrack = (key: string) => declared?.find((column) => column.key === key)?.track;
  const tracks = columns.map((column) => declaredTrack(column.key) ?? (column.key === "name" ? "minmax(0, 1fr)"
    : column.key === "kind" ? "128px" : column.key === "when" ? "104px" : declared ? "120px" : "160px")).join(" ");
  const phoneTracks = columns.map((column) => columns.length <= 2 ? "minmax(0, 1fr)" : column.key === "name" ? "minmax(0, 1fr)" : column.key === "state" ? "104px" : "84px").join(" ");
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
  // A pointer press has `detail` 1 (Space and element.click() have 0); a
  // modifier press is a multi-select gesture and only selects.
  const press = (id: string) => (event: MouseEvent<HTMLButtonElement>) => {
    onSelect?.(id);
    const modified = event.metaKey || event.ctrlKey || event.shiftKey || event.altKey;
    if (opensOnPress && !modified && event.detail === 1) onOpen?.(id);
  };
  const sortVerb = dense && onSort ? (
    <ListSortVerb columns={columns} sort={sort} onSort={(key) => onSort(key as ObjectSortKey)} />
  ) : null;
  const barVerbs = verbs.filter(verb => verb.toolbar !== false);
  const menuVerbs = verbs.filter(verb => verb.toolbar === false);
  const verbPlate = (verb: ListVerb, row: ObjectListRow | null, caption?: string) => listVerbButton(verb, row, (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    setMenu({ x: rect.left, y: rect.bottom, id: row?.id ?? null, opener: event.currentTarget }); setSubmenu(verb.id);
  }, submenu === verb.id, caption);
  const verbBar = verbs.length ? <div className="object-list-verbs" >
    {barVerbs.map((verb) => verbPlate(verb, picked))}
  </div> : null;
  const renderRow = (row: ObjectListRow) => {
    const selected = selection ? row.id === pickedId : selectedIds ? selectedIds.includes(row.id) : row.id === selectedId;
    const kindWord = row.kindWord ?? objectKindWord(row.kind);
    // The fold line (≤ 520 px): only filled cells show, and a middle
    // dot joins two filled cells; the first filled cell leads the
    // line (no orphan dot when an earlier cell is empty).
    const foldKeys = columns.filter(column => column.key !== "name").map((column) => column.key).filter((key) => key !== "state");
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
    const nameCell = (<div key="name" role="gridcell" className="object-list-name" data-col="name">
          {selection ? <span className="object-list-selection-name" title={row.name}>
            {row.cells?.tick}
            {row.sprite ? <img src={listSprite(row.sprite)} alt="" draggable={false} /> : null}
            <span className="object-list-selection-text"><MiddleText className="object-list-selection-title" value={row.name} testId={row.nameTestId} />{row.detail || (foldIntoName && (row.when || typeof row.cells?.with === "string")) ? <span className="object-list-detail" data-feedback-redact="true" title={typeof row.detail === "string" ? row.detail : undefined}>{foldIntoName && row.when ? <span data-folded-col="when">{faceTimeWords(row.when)}{row.detail || row.cells?.with ? " · " : ""}</span> : null}{foldIntoName && typeof row.cells?.with === "string" ? <span data-folded-col="with">{row.cells.with}{row.detail ? " · " : ""}</span> : null}{row.detail}</span> : null}</span>
            {row.meter && (!row.meterColumn || row.meterColumn === "name") ? <Meter {...row.meter} /> : null}
            <span className="object-list-lamp-seat">{row.leadingLamp ? <Lamp {...row.leadingLamp} /> : row.state ? <Lamp state={row.state.tone === "ask" ? "waiting" : row.state.tone === "ok" ? "done" : row.state.tone === "fail" ? "failed" : row.state.tone === "info" ? "working" : "off"} label={row.state.label} /> : null}</span>
          </span> : <Button
            variant="chrome"
            className="object-list-open"
            aria-label={(declared
              ? [row.name, has("kind") ? kindWord : undefined, has("when") ? row.when : undefined, ...cellWords, has("state") ? row.state?.label : undefined, selected ? selectedLabel : undefined]
              : [row.name, kindWord, row.when, row.state?.label, selected ? selectedLabel : undefined])
              .filter(Boolean)
              .join(", ")}
            onClick={press(row.id)}
            onDoubleClick={onOpen && !opensOnPress ? () => onOpen(row.id) : undefined}
            onKeyDown={keyDown(row.id)}
          >
            {row.avatar && !dense ? (
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
              <span className="object-list-name-word" data-control-label title={row.name} data-testid={row.nameTestId}>{nameBreaks(row.name)}</span>
              {dense ? null : (
                <span className="object-list-fold" aria-hidden="true">
                  {has("kind") ? <span className="object-list-fold-token">{kindWord}</span> : null}
                  {has("when") && row.when ? <span className="object-list-fold-token" data-face-time>{faceTimeWords(row.when)}</span> : null}
                </span>
              )}
            </span>
          </Button>}
        </div>);
    return (
      <div
        key={row.id}
        role="row"
        aria-label={selection ? [row.name,row.detail,...columns.filter(column=>column.key!=="name").map(column=>column.key==="state" ? row.state?.label : column.key==="when" ? faceTimeWords(row.when ?? "") : column.key==="kind" ? kindWord : spokenCell(row.cells?.[column.key]))].filter(Boolean).join(" ") : undefined}
        className="object-list-row"
        aria-selected={selected ? "true" : "false"}
        data-selected={selected ? "true" : undefined}
        title={selection ? [row.name, ...columns.filter(column => column.key !== "name").map((column) => {
          const value = column.key === "kind" ? kindWord : column.key === "when" ? row.when : column.key === "state" ? row.state?.label : row.cells?.[column.key];
          return typeof value === "string" || typeof value === "number" ? `${column.word}: ${value}` : null;
        })].filter(Boolean).join(" · ") : undefined}
        data-object-id={row.id}
        data-kind={row.kind}
        data-detail={row.detail ? "true" : undefined}
        data-has-when={foldIntoName && row.when ? "" : undefined}
        data-avatar={row.avatar && !dense ? "" : undefined}
        tabIndex={selection ? (selected || (!picked && row === sorted[0]) ? 0 : -1) : undefined}
        onClick={selection ? (event) => {
          choose(row.id);
          if (!(event.target as HTMLElement).closest("input, select, button")) event.currentTarget.focus();
        } : undefined}
        onFocus={selection ? (event) => { if (event.target === event.currentTarget) choose(row.id); } : undefined}
        onDoubleClick={selection ? (event) => { if (!(event.target as HTMLElement).closest("input, select, button")) { choose(row.id); openRow(row.id); } } : undefined}
        onContextMenu={selection ? (event) => { event.preventDefault(); choose(row.id); event.currentTarget.focus(); setMenu({ x: event.clientX, y: event.clientY, id: row.id, opener: event.currentTarget }); } : undefined}
        onKeyDown={selection ? (event) => {
          if ((event.target as HTMLElement).closest("input, select, button")) return;
          if (event.key === "Enter") { event.preventDefault(); openRow(row.id); }
          else if (event.key === "ContextMenu" || (event.shiftKey && event.key === "F10")) {
            event.preventDefault(); const rect = event.currentTarget.getBoundingClientRect();
            setMenu({ x: rect.left, y: rect.bottom, id: row.id, opener: event.currentTarget });
          } else {
            const chord = `${event.altKey ? "Alt+" : ""}${event.ctrlKey ? "Ctrl+" : ""}${event.metaKey ? "Meta+" : ""}${event.shiftKey ? "Shift+" : ""}${event.key}`;
            const verb = verbs.find((entry) => entry.key === chord || (entry.key === "Delete" && chord === "Backspace"));
            if (verb && listVerbEnabled(verb, row)) { event.preventDefault(); verb.run(row); }
          }
        } : undefined}
        {...(rowProps ? rowProps(row) : {})}
      >
        {columns.map((column) => {
          switch (column.key) {
            case "name": return nameCell;
            case "kind":
              return <div key="kind" role="gridcell" className="object-list-cell" data-col="kind" data-fold={fold("kind")}><span className="object-list-value" title={kindWord}>{kindWord}</span></div>;
            case "when":
              return <div key="when" role="gridcell" className="object-list-cell" data-col="when" data-face-time data-fold={fold("when")}>{selection ? <span className="object-list-value" title={row.when}>{faceTimeWords(row.when ?? "")}</span> : faceTimeWords(row.when ?? "")}</div>;
            case "state":
              return (
                <div key="state" role="gridcell" className="object-list-state" data-col="state">
                  {row.state ? (
                    (dense || selection) ? (
                      <SelectionState state={{...row.state, tone: selection ? row.state.tone : stateTone(row.state.label) ?? row.state.tone}} />
                    ) : (
                      <LampGadget label={row.state.label} on={row.state.tone !== "idle"} tone={row.state.tone === "idle" ? undefined : lampGadgetTone(row.state.tone)} />
                    )
                  ) : null}
                </div>
              );
            default:
              return (
                <div key={column.key} role="gridcell" className="object-list-cell" data-col={column.key} data-required-column={requiredColumns.includes(column.key) || undefined} data-fold={fold(column.key)}>
                  {cellContent(row.cells?.[column.key])}
                  {row.meter && row.meterColumn === column.key ? <Meter {...row.meter} /> : null}
                </div>
              );
          }
        })}
      </div>
    );
  };
  return (<>
    {selection && toolbar ? <SelectionToolbar label={label} testId={toolbar.testId} trailing={toolbar.trailing} scopes={toolbar.scopes} inner={inner}
      verbs={verbBar} entries={listVerbEntries(barVerbs, picked)} menuEntries={listVerbEntries(menuVerbs, picked)} /> : null}
    <div
      ref={listRef}
      onFocusCapture={selection && windowId ? () => publishListMenu(windowId, menuOwner, listVerbEntries(verbs, picked)) : undefined}
      className={`object-list${selection ? " object-list--selection" : ""}${className ? ` ${className}` : ""}`}
      data-list-layout={selection ? layoutId : undefined}
      data-whole-rows={wholeRows || undefined}
      data-empty={(!rows.length && !groups?.some(group => group.more && typeof group.count === "number" && group.count > 0)) || undefined}
      data-density={dense ? "dense" : undefined}
      data-compact-columns={compactColumns || undefined}
      style={{ "--object-list-columns": selection ? fitTracks(columns) : tracks, "--object-list-phone-columns": phoneTracks } as CSSProperties}
      role="grid"
      aria-label={label}
      aria-rowcount={rows.length + (headerless ? 0 : 1)}
    >
      {selection ? <style>{fitRules}</style> : null}
      {!rows.length && empty ? <PaneNotice>{empty}</PaneNotice> : null}
      {sortVerb ? (sortSlot ? createPortal(sortVerb, sortSlot) : <div className="object-list-sortline">{sortVerb}</div>) : null}
      {!headerless ? <div className="object-list-head" role="row">
        {columns.map((column) => {
          const active = sort.key === column.key;
          return (
            <div
              key={column.key}
              role="columnheader"
              className="object-list-th"
              data-caption={labelCaption(column.word)}
              data-col={column.key} data-required-column={requiredColumns.includes(column.key) || undefined}
              data-priority={column.priority ?? 0}
              aria-sort={active ? (sort.dir === "asc" ? "ascending" : "descending") : "none"}
            >
              {onSort ? <Button
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
              </Button> : <span>{column.word}</span>}
            </div>
          );
        })}
      </div> : null}
      {selection && !toolbar && !externalToolbar && verbs.length ? <SelectionToolbar label={`${label} actions`} inner verbs={verbBar} entries={listVerbEntries(barVerbs, picked)} menuEntries={listVerbEntries(menuVerbs, picked)} /> : null}
      <div className="object-list-rows" role={groups ? "presentation" : "rowgroup"} ref={bodyRef}>
        <GadgetLabelContext.Provider value={true}>{groups ? <>
          {groups.map(group => {
            const members = sorted.filter(row => row.group === group.id);
            const remaining = typeof group.count === "number" ? group.count - members.length : 0;
            const more = remaining > 0 ? group.more : undefined;
            return members.length || more ? <div key={group.id} role="rowgroup" aria-label={group.label} className="object-list-group">
              <div className="object-list-group-label" data-tone={group.tone} role="presentation"><span>{group.label}</span>{group.count != null ? <span>{group.count === true ? members.length : group.count}</span> : null}</div>{members.map(renderRow)}
              {more ? <Toolbar label={`${group.label} more`}>
                {verbPlate(more, null, `${more.label} (${remaining} more)`)}
              </Toolbar> : null}
            </div> : null;
          })}
          {sorted.filter(row => !groups.some(group => group.id === row.group)).map(renderRow)}
        </> : sorted.map(renderRow)}</GadgetLabelContext.Provider>
      </div>
      {menu ? <WorkMenu label={`${label} actions`} x={menu.x} y={menu.y} autoFocus anchor="below"
        entries={listVerbEntries((submenu ? verbs.find((verb) => verb.id === submenu)?.items : null) ?? rowVerbs ?? verbs, menuRow)}
        opener={menu.opener} onClose={() => { setMenu(null); setSubmenu(null); }} returnFocus={() => menu.opener?.focus()} /> : null}
    </div>
  </>);
}

/** The nearest toolbar sort slot above a list: the first `.kit-toolbar-sort`
 *  found walking up from the list that is not inside the list itself. */
function nearestSortSlot(list: HTMLElement | null): HTMLElement | null {
  if (!list) return null;
  for (let node = list.parentElement; node; node = node.parentElement) {
    const slot = [...node.querySelectorAll<HTMLElement>(".kit-toolbar-sort")].find((el) => !list.contains(el));
    if (slot) return slot;
    if (node.classList.contains("desk-window-shell")) break;
  }
  return null;
}

/** The narrow list's sort: one dense verb (`Sort ▾`) that opens the columns
 *  as library Buttons; the active one carries its direction and a second
 *  press on it flips the order. Shown only on a narrow surface (CSS). */
function ListSortVerb({
  columns,
  sort,
  onSort,
}: {
  columns: ObjectListColumn[];
  sort: ObjectListSort;
  onSort(key: string): void;
}) {
  const anchor = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);
  const active = columns.find((column) => column.key === sort.key);
  const dirWord = sort.dir === "asc" ? "ascending" : "descending";
  return (
    <span className="object-list-sortverb">
      <Button
        ref={anchor}
        dense
        variant="secondary"
        aria-haspopup="true"
        aria-expanded={open}
        aria-label={active ? `Sort: ${active.word}, ${dirWord}` : "Sort"}
        data-testid="object-list-sort-verb"
        onClick={() => setOpen((now) => !now)}
      >
        Sort ▾
      </Button>
      {open && anchor.current ? <WorkMenu label="Sort by" x={anchor.current.getBoundingClientRect().left} y={anchor.current.getBoundingClientRect().bottom}
        opener={anchor.current} autoFocus onClose={() => {setOpen(false);anchor.current?.focus();}} returnFocus={() => anchor.current?.focus()}
        entries={columns.map(column => ({type:"item", id:column.key, label:column.word, checked:column.key === sort.key,
          title:column.key === sort.key ? dirWord : undefined, onSelect:() => onSort(column.key)}))} /> : null}
    </span>
  );
}

/** A pane's verbs use the same plates, fitting and menu as a selection list. */
export function VerbToolbar({ label, verbs, trailing, trailingVerbs = [], testId }: { label: string; verbs: readonly ListVerb[]; trailing?: ReactNode; trailingVerbs?: readonly ListVerb[]; testId?: string }) {
  const [menu, setMenu] = useState<{ x: number; y: number; opener: HTMLButtonElement; verb: ListVerb } | null>(null);
  const shown = verbs.filter(verb => verb.toolbar !== false);
  return <><SelectionToolbar label={label} testId={testId} trailing={trailing}
    verbs={<>{shown.map(verb => listVerbButton(verb, null, event => { const rect = event.currentTarget.getBoundingClientRect(); setMenu({ x: rect.left, y: rect.bottom, opener: event.currentTarget, verb }); }, menu?.verb.id === verb.id))}</>}
    entries={listVerbEntries(shown, null)} trailingEntries={listVerbEntries(trailingVerbs, null)} menuEntries={listVerbEntries(verbs.filter(verb => verb.toolbar === false), null)} />
    {menu ? <WorkMenu label={menu.verb.label} x={menu.x} y={menu.y} opener={menu.opener} entries={listVerbEntries(menu.verb.items ?? [], null)} autoFocus onClose={() => setMenu(null)} /> : null}</>;
}
function listVerbButton(verb: ListVerb, row: ObjectListRow | null, onItems: (event: MouseEvent<HTMLButtonElement>) => void, expanded: boolean, caption?: string) {
  const label = caption ?? verb.label;
  return <Button key={verb.id} dense dispatching={verb.dispatching} variant={verb.variant === "stop" ? "danger" : verb.variant ?? "secondary"} data-list-verb={verb.id} data-list-stop={verb.variant === "stop" || undefined} data-testid={verb.testId}
    aria-label={label} title={verb.title ?? (verb.key ? `${label} (${verb.key === "Enter" ? "Return" : verb.key})` : label)}
    aria-haspopup={verb.items ? "menu" : undefined} aria-expanded={verb.items ? expanded : undefined} disabled={!listVerbEnabled(verb, row)}
    onClick={event => verb.items ? onItems(event) : verb.run(row)}>{caption ?? verb.symbol ?? verb.label}</Button>;
}

/** The shared strip measures its verbs before folding them into one menu. */
function SelectionToolbar({ label, testId, trailing, scopes = [], inner = false, verbs, entries, menuEntries = [], trailingEntries = [] }: {
  label: string; testId?: string; trailing?: ReactNode; scopes?: readonly ListScope[]; inner?: boolean; verbs: ReactNode; entries: WorkMenuEntry[]; menuEntries?: WorkMenuEntry[]; trailingEntries?: WorkMenuEntry[];
}) {
  const { ref: findRef, fits: scopeFits } = useStripFit<HTMLSpanElement>(Boolean(scopes.length), scopes.map(scope => `${scope.id}:${scope.kind === "tick" ? scope.checked : scope.value}`).join("|"));
  const [narrow, setNarrow] = useState(false);
  const foldedScopes = scopes.length > 0 && (!scopeFits || narrow);
  const extraEntries = [...menuEntries, ...(narrow ? trailingEntries : [])];
  const ref = useRef<HTMLSpanElement>(null), probe = useRef<HTMLSpanElement>(null);
  const view = useContext(PaneViewContext);
  const paneNotice = useContext(PaneNoticeContext);
  const declared = Children.toArray(isValidElement<{children:ReactNode}>(verbs) ? verbs.props.children : verbs);
  const stop = (button: ReactNode) => isValidElement<Record<string,unknown>>(button) && button.props["data-list-stop"] && !button.props.disabled;
  const dead = (button: ReactNode) => isValidElement<Record<string,unknown>>(button) && button.props.disabled;
  const buttons = [...declared.filter(stop), ...declared.filter(button => !stop(button) && !dead(button)), ...declared.filter(button => !stop(button) && dead(button))];
  const [shown,setShown] = useState(buttons.length), [viewFits,setViewFits] = useState(true);
  const signature = entries.map(entry=>`${entry.id}:${entry.type==="sep"?"":entry.label}`).join("|");
  useLayoutEffect(()=>{
    const seat=ref.current, natural=probe.current;
    if(!seat||!natural)return;
    const measure=()=>{
      const toolbar=seat.closest(".kit-toolbar");
      setNarrow(Boolean(toolbar && toolbar.clientWidth>0 && toolbar.clientWidth<=520));
      const width=seat.clientWidth;
      if(!width){setShown(buttons.length);return;}
      const sizes=Array.from(natural.children).map(child=>child.getBoundingClientRect().width);
      const more=sizes.pop()??0;
      const viewWidth=view ? (sizes.pop()??0) : 0;
      const gap=parseFloat(getComputedStyle(seat).gap)||0;
      const withView=width-viewWidth-(view ? gap : 0);
      const total=sizes.reduce((sum,n)=>sum+n,0)+gap*Math.max(0,sizes.length-1);
      const needsMore=Boolean(extraEntries.length || foldedScopes || total>withView);
      const foldView=Boolean(view && stop(buttons[0]) && (sizes[0]??0)+(needsMore ? more+gap : 0)>withView);
      setViewFits(!foldView);
      const available=foldView ? width : withView;
      const forceMore=Boolean(extraEntries.length || foldedScopes || foldView);
      if(!forceMore&&total<=available){setShown(sizes.length);return;}
      setShown(forceMore ? fitStrip(available-more-gap,sizes,0,gap).length : fitStrip(available,sizes,more,gap).length);
    };
    measure();
    const observer=typeof ResizeObserver==="undefined"?null:new ResizeObserver(measure);
    observer?.observe(seat); observer?.observe(natural);
    return ()=>observer?.disconnect();
  },[signature,foldedScopes,buttons.length,menuEntries.length,narrow,trailingEntries.length,declared.map(button => isValidElement<Record<string,unknown>>(button) ? Boolean(button.props.disabled) : false).join(",")]);
  useLayoutEffect(() => {
    const row = findRef.current;
    const width = row?.querySelector<HTMLElement>(".object-list-scopes")?.getBoundingClientRect().width;
    // Keep the complete scope allocation while folded, so a wider Find row
    // can unfold again rather than shrinking to the remaining field.
    if (row?.parentElement && width) row.parentElement.style.setProperty("--object-list-scoped-width", `${Math.ceil(width + (trailing ? 252 : 0))}px`);
  }, [scopeFits, scopes, trailing]);
  const anchor = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);
  const rect = open ? anchor.current?.getBoundingClientRect() : null;
  const folded = [...buttons.slice(shown).flatMap(button => {
    const id = isValidElement<Record<string,unknown>>(button) ? button.props["data-list-verb"] : undefined;
    return entries.filter(entry => entry.id === id);
  }), ...(view && !viewFits && isValidElement<Parameters<typeof paneViewEntries>[0]>(view) && Array.isArray(view.props.tabs) ? [{type:"sub" as const,id:"pane-view",label:"View",entries:paneViewEntries(view.props)}] : []), ...extraEntries, ...(foldedScopes ? scopeEntries(scopes) : [])];
  const more = <Button data-list-overflow="" ref={anchor} dense variant="secondary" aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen(!open)}>{VERB_OVERFLOW_WORD} ▾</Button>;
  return <><Toolbar label={label} data-testid={testId} trailing={(trailing && !(narrow && trailingEntries.length)) || (scopes.length && !foldedScopes) ? <span ref={findRef} className="object-list-find-row" data-scoped={scopes.length > 0 || undefined}>
    {!foldedScopes && scopes.length ? <span className="object-list-scopes">{scopes.map(scope => scope.kind === "tick"
      ? <CheckGadget key={scope.id} label={scope.label} variant="token" checked={scope.checked} disabled={scope.disabled} onChange={scope.onChange} />
      : <CycleGadget key={scope.id} label={scope.label} value={scope.value} options={[...scope.options]} disabled={scope.disabled} onChange={scope.onChange} />)}</span> : null}
    {trailing && !(narrow && trailingEntries.length) ? <span className="object-list-find"><SelectionFieldContext.Provider value={true}>{trailing}</SelectionFieldContext.Provider></span> : null}
  </span> : undefined} className={`object-list-toolbar${inner ? " object-list-inner-toolbar" : ""}`}>
    <span ref={ref} className="object-list-toolbar-strip">{[...buttons.slice(0,shown).filter(stop), viewFits ? view : null, ...buttons.slice(0,shown).filter(button => !stop(button))]}{folded.length ? more : null}</span>
    <span ref={probe} className="object-list-verb-measure" aria-hidden="true" inert>{buttons.map((button,i)=>isValidElement<Record<string,unknown>>(button)?cloneElement(button,{key:i,ref:undefined,"data-testid":undefined,id:undefined,"aria-label":undefined,title:undefined,tabIndex:-1,onClick:undefined}):button)}{view ? <span>{view}</span> : null}<Button dense variant="secondary" tabIndex={-1}>{VERB_OVERFLOW_WORD} ▾</Button></span>
    {rect ? <WorkMenu label={`${label} actions`} x={rect.left} y={rect.bottom} entries={folded} autoFocus
      opener={anchor.current} returnFocus={() => anchor.current?.focus()} onClose={() => setOpen(false)} /> : null}
  </Toolbar>{paneNotice ? <div className="surface-list-notice"><PaneNotice>{paneNotice}</PaneNotice></div> : null}</>;
}
