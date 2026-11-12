import { useState, type ReactNode, type RefObject } from "react";
import {
  InspectorFacts,
  ListPane,
  ListView,
  SurfaceState,
  wireDayClock,
  type InspectorFact,
  type ListVerb,
  type ObjectListColumn,
  type ObjectListRow,
} from "../../desk/surface";

/** Room data and doors; the kit owns selection, fitting, menus and reading. */
export type RoomEntry = ObjectListRow & {
  facts?: InspectorFact[];
  open?(): void;
};
export const ITEM_COLUMNS: ObjectListColumn[] = [
  { key: "name", word: "Item", priority: 10, minWidth: 220 },
  { key: "kind", word: "Kind", priority: 1 },
  { key: "state", word: "State", priority: 9, minWidth: 130 },
  { key: "when", word: "Changed", priority: 2 },
];
export function RoomList({
  label,
  rows,
  columns = ITEM_COLUMNS,
  verbs = [],
  field,
  selectedId,
  onSelect,
  children,
  error,
  retry,
  retryLabel,
  loading,
  empty = "Nothing here",
  testId,
  listRef,
  notice,
  openTestId,
}: {
  notice?: ReactNode;
  openTestId?: string;
  label: string;
  rows: RoomEntry[];
  columns?: ObjectListColumn[];
  verbs?: ListVerb[];
  field?: ReactNode;
  selectedId?: string | null;
  onSelect?(id: string): void;
  children?: ReactNode;
  error?: string | null;
  retry?(): void;
  retryLabel?: string;
  listRef?: RefObject<HTMLDivElement | null>;
  loading?: boolean;
  empty?: string;
  testId?: string;
}) {
  const [picked, setPicked] = useState<string | null>(null);
  const id = selectedId === undefined ? picked : selectedId;
  const selected = rows.find((row) => row.id === id);
  const open = (key: string) => rows.find((row) => row.id === key)?.open?.();
  const actions: ListVerb[] = [
    {
      id: "open",
      testId: openTestId,
      label: "Open",
      key: "Enter",
      enabled: (row) =>
        Boolean(rows.find((entry) => entry.id === row?.id)?.open),
      run: (row) => {
        if (row) open(row.id);
      },
    },
    ...verbs,
  ];
  const pane = (
    <ListPane
      label={`${label} details`}
      listTestId={testId}
      list={
        <>
          <ListView
            label={label}
            rows={rows.map((row) => ({
              ...row,
              when:
                typeof row.when === "string" &&
                /^\d{4}-\d\d-\d\dT/.test(row.when)
                  ? wireDayClock(row.when)
                  : row.when,
              ...(!row.state &&
              typeof row.cells?.state === "string" &&
              row.cells.state
                ? {
                    state: {
                      label:
                        row.cells.state.charAt(0).toUpperCase() +
                        row.cells.state.slice(1),
                      tone: /wait|late|risk|unknown|refus|could|sign/i.test(
                        row.cells.state,
                      )
                        ? ("warn" as const)
                        : ("idle" as const),
                    },
                  }
                : {}),
            }))}
            columns={columns}
            selection
            ordered
            toolbar={{ trailing: field }}
            verbs={actions}
            selectedId={selected?.id ?? null}
            onSelect={(key) => {
              setPicked(key);
              onSelect?.(key);
            }}
            onClearSelection={() => {
              setPicked(null);
              onSelect?.("");
            }}
            onOpen={open}
            defaultVerb="open"
          />
          {notice}
          {error ? (
            <SurfaceState error={error} onRetry={retry} retryLabel={retryLabel} />
          ) : loading ? (
            <SurfaceState loading />
          ) : !rows.length ? (
            <SurfaceState empty emptyLabel={empty} />
          ) : null}
        </>
      }
    >
      {children ??
        (selected ? (
          <InspectorFacts
            name={selected.name}
            rows={selected.facts ?? []}
            data-feedback-redact="true"
          />
        ) : null)}
    </ListPane>
  );
  return listRef ? (
    <div className="surface-preference-pane" ref={listRef}>
      {pane}
    </div>
  ) : (
    pane
  );
}
