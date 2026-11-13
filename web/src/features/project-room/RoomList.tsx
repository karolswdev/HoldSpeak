import { useState, type ReactNode, type RefObject } from "react";
import {
  InspectorFacts,
  PaneInspector,
  ListPane,
  ListView,
  SurfaceState,
  PreferencePane,
  PaneNotice,
  ReadingDocument,
  wireDayClock,
  stateTone,
  type InspectorFact,
  type ListVerb,
  type ListScope,
  type ObjectListColumn,
  type ObjectListRow,
} from "../../desk/surface";

import { faceTimeWords, presentValue } from "../../desk/surface/format";
import { objectSprite } from "../../desk/surface/objects/kinds";
import { nameIsFile } from "../../desk/surface/objects/fitName";
import { claimChipTitle } from "./update/model";
import { nameWord, wireWords, stateWords } from "../../desk/surface/words";

/** Room data and doors; the kit owns selection, fitting, menus and reading. */
export type RoomEntry = ObjectListRow & {
  facts?: InspectorFact[];
  open?(): void;
};
function roomListState(row: RoomEntry): ObjectListRow["state"] {
  const label = roomWord(row.state?.label || String(row.cells?.state || ""));
  const tone = stateTone(label) ?? row.state?.tone ?? "info";
  return label ? {...row.state, label, tone: tone === "parked" ? "idle" : tone} : undefined;
}
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
  scopes,
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
  scopes?: readonly ListScope[];
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
                state: roomListState(row),
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
          )}
        selection
        ordered
        toolbar={{ trailing: field, scopes }}
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
          <RoomFacts entry={selected} />
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

/** Paths use the file object; the facts and heading remain kit pieces. */
export function RoomFacts({ entry }: { entry: RoomEntry }) {
  const facts = <InspectorFacts name={entry.name} rows={roomFacts(entry.facts ?? [])} data-feedback-redact="true" />;
  return nameIsFile(entry.name)
    ? <PaneInspector label={entry.name} object={<img src={objectSprite("artifact", entry.id, "rest", 32)} alt="" width={32} height={32} />}>
        <InspectorFacts header={false} name={entry.name} rows={roomFacts(entry.facts ?? [])} data-feedback-redact="true" />
      </PaneInspector>
    : facts;
}

/** Put the subject before the generator's kind/severity prefix in a list. */
export function roomClaimWords(text: string): Pick<ObjectListRow, "name" | "detail"> {
  const name = claimChipTitle(text, Infinity) ?? text;
  return {
    name: roomReadingText(name),
    detail: name !== text ? roomReadingText(text.slice(0, text.lastIndexOf(name))).replace(/:\s*$/, "") : undefined,
  };
}

/** Account keys are not project names. Keep the hub's real label otherwise. */
export function roomSourceName(provider: string, label: string): string {
  return provider === "jira" && label.includes("|") ? "Jira account" : nameWord(label);
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
  return facts.flatMap((fact) => {
    if (typeof fact.value !== "string") return [fact];
    const value = presentValue(fact.value);
    if (!value || /^(?:Due\s*[·:]\s*)?(?:unknown|none|n\/a)$/i.test(value)) return [];
    return [{ ...fact, value:
      ["State", "Kind", "Support", "Acceptance", "Lifecycle", "Likelihood", "Impact", "Severity", "From"].includes(fact.label)
        ? roomWord(value)
        : ["Due", "Due date", "When read", "Read", "Checked", "Opened", "Changed", "Created"].includes(fact.label)
          ? faceTimeWords(value)
          : ["What it says", "Text"].includes(fact.label)
            ? <ReadingDocument>{roomReadingText(value)}</ReadingDocument>
            : value,
    }];
  });
}
export function roomReadingText(text: string): string {
  return text
    .replace(/^(#{1,6}\s+)(.+)$/gm, (_, mark: string, heading: string) => mark + stateWords(heading))
    .replace(/\b(Risk|Milestone|Dependency|Signal|Workstream|Item|Action item) \[(critical|high|medium|low)\]:/g,
      (_, kind: string, severity: string) => `${kind} · ${roomWord(severity)}:`)
    .replace(/[ \t]+--[ \t]+([a-z_]+)(?=$|[,.;]|\s+\(due)/gm,
      (_, state: string) => ` · ${roomWord(state)}`)
    .replace(/[ \t]+--[ \t]+(owner|due)[ \t]+/g,
      (_, label: string) => ` · ${roomWord(label)} `)
    .replace(/\bat_risk\b/g, "At risk")
    .replace(
      /(\b(?:State|Lifecycle):\s*)([a-z_]+)/g,
      (_, label: string, value: string) => label + roomWord(value),
    );
}
