// PHILO-9-04 CANVAS (PROPOSAL, not built) - a copy of
// web/src/desk/components/DeskSortableTable.tsx with two marked changes:
//   1. every sort header is the library Button (UX-CANON A.1); the sorted
//      column keeps its arrow and reads `aria-pressed`;
//   2. `foldColumns`: at a narrow width (<= 720 px) the named columns leave
//      the grid; their values ride a second line in the first column's cell
//      (the consumer draws it), and their sort Buttons join the first
//      sortable header, so every sort stays reachable at 393.
import "@w/desk/components/list-view.css";
import { useRef, type KeyboardEvent, type ReactNode } from "react";
import { Button } from "@w/components/signal/Signal";
import { useRovingRows } from "@w/desk/surface/roving";
import { SurfaceState } from "@w/desk/surface/Surface";

export interface Column<T> {
  key: string;
  label: string;
  sortable?: boolean;
  render: (item: T) => ReactNode;
  width?: string;
}

export interface DeskSortableTableProps<T> {
  data: T[];
  columns: Column<T>[];
  sort: { key: string; dir: "asc" | "desc" };
  onSort: (key: string, dir: "asc" | "desc") => void;
  rowKey: (item: T) => string;
  onRowClick?: (item: T) => void;
  onRowDoubleClick?: (item: T) => void;
  rowActions?: (item: T) => ReactNode;
  selectedKey?: string | null;
  emptyLabel?: string;
  groupBy?: (item: T) => string;
  className?: string;
  /** An accessible row name for table consumers whose cells are abbreviated. */
  rowLabel?: (item: T) => string;
  /** Lets a consumer retain a row-specific keyboard verb without a second table. */
  onRowKeyDown?: (event: KeyboardEvent<HTMLTableRowElement>, item: T) => void;
  onRowContextMenu?: (event: React.MouseEvent<HTMLTableRowElement>, item: T) => void;
  /** PROPOSAL 2: column keys that fold into the first column at <= 720 px. */
  foldColumns?: string[];
}

/** PROPOSAL 1: the one sort verb, the library Button. */
function SortButton({
  label,
  current,
  dir,
  onSort,
  narrowOnly,
}: {
  label: string;
  current: boolean;
  dir: "asc" | "desc";
  onSort: () => void;
  narrowOnly?: boolean;
}) {
  return (
    <Button
      variant="ghost"
      dense
      aria-pressed={current}
      className={`desk-sortable-table-sort${current ? " is-current" : ""}${narrowOnly ? " is-narrow-only" : ""}`}
      onClick={onSort}
    >
      {label}
      {current ? (
        <span className="desk-sortable-table-direction" aria-hidden="true">
          {dir === "asc" ? " ↑" : " ↓"}
        </span>
      ) : null}
    </Button>
  );
}

/**
 * The Desk's one dense table face. Callers own their record sort, so a table
 * can present domain-specific ordering while this component owns the shared
 * header, focus, selection, group, and action grammar.
 */
export function DeskSortableTable<T>({
  data,
  columns,
  sort,
  onSort,
  rowKey,
  onRowClick,
  onRowDoubleClick,
  rowActions,
  selectedKey,
  emptyLabel = "Empty",
  groupBy,
  className,
  rowLabel,
  onRowKeyDown,
  onRowContextMenu,
  foldColumns = [],
}: DeskSortableTableProps<T>) {
  const fold = new Set(foldColumns);
  const firstSortable = columns.find((c) => c.sortable)?.key;
  const sortOf = (key: string) =>
    () => onSort(key, sort.key === key && sort.dir === "asc" ? "desc" : "asc");
  const rootRef = useRef<HTMLDivElement>(null);
  useRovingRows(rootRef, { selector: ".desk-sortable-table-row" });

  const groups = new Map<string, T[]>();
  for (const item of data) {
    const label = groupBy?.(item) ?? "";
    const items = groups.get(label) ?? [];
    items.push(item);
    groups.set(label, items);
  }
  const hasActions = Boolean(rowActions);
  const columnCount = columns.length + (hasActions ? 1 : 0);
  const cx = ["desk-sortable-table-wrap", className].filter(Boolean).join(" ");

  return (
    <div ref={rootRef} className={cx}>
      <table className="desk-sortable-table">
        <colgroup>
          {columns.map((column) => (
            <col key={column.key} style={column.width ? { width: column.width } : undefined} />
          ))}
          {hasActions ? <col className="desk-sortable-table-actions-col" /> : null}
        </colgroup>
        <thead>
          <tr>
            {columns.map((column) => {
              const isCurrent = sort.key === column.key;
              return (
                <th
                  key={column.key}
                  scope="col"
                  className={fold.has(column.key) ? "is-fold" : undefined}
                  aria-sort={
                    column.sortable && isCurrent
                      ? sort.dir === "asc"
                        ? "ascending"
                        : "descending"
                      : undefined
                  }
                >
                  {column.sortable ? (
                    <span className="desk-sortable-table-sorts">
                      <SortButton label={column.label} current={isCurrent} dir={sort.dir} onSort={sortOf(column.key)} />
                      {column.key === firstSortable
                        ? columns
                            .filter((c) => c.sortable && fold.has(c.key))
                            .map((c) => (
                              <SortButton
                                key={c.key}
                                label={c.label}
                                current={sort.key === c.key}
                                dir={sort.dir}
                                onSort={sortOf(c.key)}
                                narrowOnly
                              />
                            ))
                        : null}
                    </span>
                  ) : (
                    column.label
                  )}
                </th>
              );
            })}
            {hasActions ? <th className="desk-sortable-table-actions-head" aria-hidden="true" /> : null}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr className="desk-sortable-table-empty">
              <td colSpan={columnCount}><SurfaceState empty emptyLabel={emptyLabel} /></td>
            </tr>
          ) : (
            Array.from(groups, ([label, items]) => (
              <GroupRows
                key={label || "rows"}
                label={label}
                items={items}
                columns={columns}
                rowKey={rowKey}
                rowActions={rowActions}
                selectedKey={selectedKey}
                onRowClick={onRowClick}
                onRowDoubleClick={onRowDoubleClick}
                rowLabel={rowLabel}
                onRowKeyDown={onRowKeyDown}
                onRowContextMenu={onRowContextMenu}
                columnCount={columnCount}
                fold={fold}
              />
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

function GroupRows<T>({
  label,
  items,
  columns,
  rowKey,
  rowActions,
  selectedKey,
  onRowClick,
  onRowDoubleClick,
  rowLabel,
  onRowKeyDown,
  onRowContextMenu,
  columnCount,
  fold,
}: Omit<DeskSortableTableProps<T>, "data" | "sort" | "onSort" | "emptyLabel" | "groupBy" | "className"> & {
  label: string;
  items: T[];
  columnCount: number;
  fold: Set<string>;
}) {
  return (
    <>
      {label ? (
        <tr className="desk-sortable-table-group">
          <th colSpan={columnCount} scope="colgroup">{label}</th>
        </tr>
      ) : null}
      {items.map((item) => {
        const key = rowKey(item);
        return (
          <tr
            key={key}
            className="desk-sortable-table-row"
            data-selected={selectedKey === key || undefined}
            aria-label={rowLabel?.(item)}
            onClick={() => onRowClick?.(item)}
            onDoubleClick={() => onRowDoubleClick?.(item)}
            onKeyDown={(event) => {
              onRowKeyDown?.(event, item);
              // Rows are the roving stops. Enter activates a focused row,
              // while a nested button keeps its native activation path.
              if (
                !event.defaultPrevented &&
                event.currentTarget === event.target &&
                event.key === "Enter"
              ) {
                onRowClick?.(item);
              }
            }}
            onContextMenu={(event) => onRowContextMenu?.(event, item)}
          >
            {columns.map((column) => (
              <td key={column.key} className={fold.has(column.key) ? "is-fold" : undefined}>{column.render(item)}</td>
            ))}
            {rowActions ? (
              <td className="desk-sortable-table-actions">{rowActions(item)}</td>
            ) : null}
          </tr>
        );
      })}
    </>
  );
}
