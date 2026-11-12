import { useState, type ReactNode, type RefObject } from "react";
import {
  InspectorFacts,
  ListPane,
  ListView,
  SurfaceState,
  PreferencePane,
  PaneNotice,
  ReadingDocument,
  wireDayClock,
  type InspectorFact,
  type ListVerb,
  type ObjectListColumn,
  type ObjectListRow,
} from "../../desk/surface";

import { nameWord, wireWords, stateWords } from "../../desk/surface/words";

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
  reader = false,
  openTestId,
}: {
  reader?: boolean;
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
    ...(!reader
      ? [
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
          } satisfies ListVerb,
        ]
      : []),
    ...verbs,
  ];
  const list = (
    <>
      <ListView
        label={label}
        rows={
          reader
            ? []
            : rows.map((row) => ({
                ...row,
                kindWord: wireWords(row.kindWord || row.kind),
                when:
                  typeof row.when === "string" &&
                  /^\d{4}-\d\d-\d\dT/.test(row.when)
                    ? wireDayClock(row.when)
                    : row.when,
                state: undefined,
                cells: {
                  ...row.cells,
                  "state-word": roomWord(
                    row.state?.label || String(row.cells?.state || ""),
                  ),
                },
              }))
        }
        columns={columns
          .filter(
            (column) =>
              column.key === "name" ||
              rows.some((row) =>
                column.key === "kind"
                  ? Boolean(row.kindWord || row.kind)
                  : column.key === "when"
                    ? Boolean(row.when)
                    : column.key === "state"
                      ? Boolean(row.state?.label || row.cells?.state)
                      : Boolean(row.cells?.[column.key]),
              ),
          )
          .map((column) =>
            column.key === "state" ? { ...column, key: "state-word" } : column,
          )}
        selection
        ordered
        toolbar={{ trailing: field }}
        verbs={
          reader
            ? actions.map((verb) => ({
                ...verb,
                enabled: () =>
                  verb.enabled?.(selected ?? null) ?? Boolean(selected),
                run: () => verb.run(selected ?? null),
              }))
            : actions
        }
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
      ) : !rows.length && !children ? (
        <PaneNotice>{empty}</PaneNotice>
      ) : null}
    </>
  );
  const pane = reader ? (
    <PreferencePane label={label}>
      {list}
      {children}
    </PreferencePane>
  ) : (
    <ListPane label={`${label} details`} listTestId={testId} list={list}>
      {children ??
        (selected ? (
          <InspectorFacts
            name={selected.name}
            rows={roomFacts(selected.facts ?? [])}
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

/** Enum words and provider names are presentation, never changes to saved text. */
export function roomWord(value: string): string {
  return nameWord(value) !== value
    ? nameWord(value)
    : stateWords(
        value.replaceAll("_", " ").replace(/^./, (word) => word.toUpperCase()),
      );
}
export function roomFacts(facts: readonly InspectorFact[]): InspectorFact[] {
  return facts.map((fact) => ({
    ...fact,
    value:
      typeof fact.value !== "string" || !fact.value.trim() ? (
        fact.value
      ) : ["State", "Kind", "Support", "Acceptance", "Lifecycle"].includes(
          fact.label,
        ) ? (
        roomWord(fact.value)
      ) : fact.label === "From" ? (
        roomWord(fact.value)
      ) : fact.label === "What it says" || fact.label === "Text" ? (
        <ReadingDocument>{roomReadingText(fact.value)}</ReadingDocument>
      ) : (
        fact.value
      ),
  }));
}
export function roomReadingText(text: string): string {
  return text
    .replace(/\bat_risk\b/g, "At risk")
    .replace(
      /(--\s+)([a-z_]+)(?=$|[,.;])/gm,
      (_, label: string, value: string) => label + roomWord(value),
    )
    .replace(
      /(\b(?:State|Lifecycle):\s*)([a-z_]+)/g,
      (_, label: string, value: string) => label + roomWord(value),
    );
}
