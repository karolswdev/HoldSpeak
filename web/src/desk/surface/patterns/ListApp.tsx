import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useCompactViewport } from "../../useCompactViewport";
import { useHasWindowBack, useWindowBack } from "../back";
import { readableError } from "../../../lib/api";
import { useGuideView } from "../../walk/viewState";
import { StringGadget } from "../gadgets";
import { ListView } from "../objects";
import type { ObjectListProps, ObjectListRow } from "../objects/ObjectList";
import { StatusBar, type StatusBarItem } from "../kit";
import { useWindowInterior } from "../interior";
import { SurfaceState } from "../Surface";
import { hasWords } from "../content";
import { ListPane } from "./ListPane";
import { PreferencePane } from "./PreferencePane";
import { InspectorFacts, type InspectorFact } from "./PreferencePane";

export type ListPage<T> = { rows: T[]; total?: number };
export type ListRead = { query: string; offset: number; limit: number };

/** One read lifecycle, including paged reads and acknowledged row/frame changes.
 * A later read wins. A row changed during a read wins over that read's copy. */
export function useListApp<P extends ListPage<unknown>>({
  read,
  keyOf,
  search,
  pageSize = 100,
  initialPicked = null,
  initialPage,
  groups,
}: {
  groups?: ObjectListProps["groups"];
  read(request: ListRead): Promise<P>;
  keyOf(row: P["rows"][number]): string;
  /** Omit for server Find; provide for a complete, locally filtered list. */
  search?(row: P["rows"][number], query: string): boolean;
  pageSize?: number;
  initialPicked?: string | null;
  initialPage?: P;
}) {
  useWindowInterior("list");
  type T = P["rows"][number];
  const [page, setPage] = useState<P | null>(initialPage ?? null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [picked, setPicked] = useState<string | null>(initialPicked);
  const [more, setMore] = useState(false);
  const round = useRef(0),
    patches = useRef(new Map<string, T | null>());
  const now = useRef({ page, query, keyOf });
  now.current = { page, query, keyOf };
  const serverQuery = search ? "" : query;
  const load = useCallback(
    async (append = false, clearOnFailure = false) => {
      const mine = ++round.current,
        before = new Map(patches.current);
      const previous = now.current.page?.rows ?? [];
      if (append) setMore(true);
      else setLoading(true);
      try {
        const answer = await read({
          query: serverQuery,
          offset: append ? previous.length : 0,
          limit: append ? pageSize : Math.max(pageSize, previous.length),
        });
        if (mine !== round.current) return;
        const rows = new Map(
          (append ? [...previous, ...answer.rows] : answer.rows).map((row) => [
            now.current.keyOf(row),
            row,
          ]),
        );
        for (const [id, row] of patches.current) {
          if (before.has(id) && before.get(id) === row) continue;
          if (row) rows.set(id, row);
          else rows.delete(id);
        }
        setPage({ ...answer, rows: [...rows.values()] });
        setError("");
      } catch (cause) {
        if (mine === round.current) {
          if (clearOnFailure) setPage(null);
          setError(readableError(cause));
        }
      } finally {
        if (mine === round.current) {
          setLoading(false);
          setMore(false);
        }
      }
    },
    [read, serverQuery, pageSize],
  );
  useEffect(() => {
    // Invalidate immediately, including the server Find debounce interval.
    round.current++;
    setLoading(true);
    const timer = serverQuery.trim()
      ? window.setTimeout(() => {
          void load(false, !search);
        }, 200)
      : undefined;
    if (!timer) void load(false, !search);
    return () => {
      round.current++;
      window.clearTimeout(timer);
    };
  }, [load]);
  const rows = (page?.rows ?? []) as T[];
  const visible = search
    ? rows.filter((row) => search(row, query.trim().toLocaleLowerCase()))
    : rows;
  const selected = visible.find((row) => keyOf(row) === picked) ?? null;
  useEffect(() => {
    if (!loading && picked && !selected) setPicked(null);
  }, [loading, picked, selected]);
  useGuideView(
    () => ({ picked, query }),
    (saved) => {
      setPicked(saved.picked);
      setQuery(saved.query);
    },
  );
  const change = (id: string, row: T | null) => {
    patches.current.set(id, row);
    setPage(
      (current) =>
        current && {
          ...current,
          rows: row
            ? current.rows.some((item) => keyOf(item) === id)
              ? current.rows.map((item) => (keyOf(item) === id ? row : item))
              : [row, ...current.rows]
            : current.rows.filter((item) => keyOf(item) !== id),
        },
    );
  };
  return {
    page,
    rows,
    visible,
    groups,
    selected,
    picked,
    setPicked,
    query,
    setQuery,
    loading,
    error,
    more,
    serverSearch: !search,
    total: page?.total ?? rows.length,
    reload: () => load(),
    showMore: () => load(true),
    apply: (row: T) => change(keyOf(row), row),
    drop: (id: string) => change(id, null),
  };
}

/** PreferencePane → ListPane → ListView/selection pane → StatusBar. No app CSS. */
export function ListApp<T>({
  app,
  label,
  ids,
  list,
  row,
  words,
  pane,
  status = [],
  children,
  notice,
  onSelect,
  layout,
  listShare,
  paneOpen,
  onPaneBack,
  overview,
  transient,
}: {
  transient?: Parameters<typeof StatusBar>[0]["transient"];
  /** Facts of the collection when no object is selected. Omit to give the list its whole seat. */
  overview?: readonly InspectorFact[];
  onPaneBack?(): void;
  paneOpen?: boolean;
  layout?: "deck";
  listShare?: Parameters<typeof ListPane>[0]["listShare"];
  app: Pick<
    ReturnType<typeof useListApp<ListPage<T>>>,
    | "visible"
    | "selected"
    | "picked"
    | "setPicked"
    | "query"
    | "setQuery"
    | "loading"
    | "error"
    | "reload"
    | "serverSearch"
  > & { groups?: ObjectListProps["groups"] };
  label: string;
  ids: {
    windowTestId: string;
    listTestId: string;
    paneTestId: string;
    toolbarTestId: string;
    statusTestId: string;
    loadingTestId?: string;
  };
  list: Omit<
    ObjectListProps,
    "rows" | "label" | "selectedId" | "onSelect" | "onClearSelection"
  >;
  row(item: T): ObjectListRow;
  words: {
    find: string;
    empty: string;
    noMatch: string;
    select?: string;
    failed?: string;
  };
  pane?(selected: T | null): ReactNode;
  status?: (StatusBarItem | false | null | undefined)[];
  children?: ReactNode;
  /** A failed action keeps the selection and any open form in place. */
  notice?: ReactNode;
  onSelect?(): void;
}) {
  const [open, setOpen] = useState(false);
  const compact = useCompactViewport(),
    hosted = useHasWindowBack();
  useGuideView(
    () => open,
    setOpen,
    layout === "deck" ? () => setOpen(false) : undefined,
  );
  const shown = open || paneOpen;
  const onBackRef = useRef(onPaneBack);
  onBackRef.current = onPaneBack;
  const back = () => {
    setOpen(false);
    onBackRef.current?.();
  };
  useEffect(() => {
    if (layout === "deck" && app.picked) setOpen(true);
  }, [layout, app.picked]);
  const state =
    app.error || (app.loading && !app.visible.length) ? (
      <SurfaceState
        data-testid={ids.loadingTestId}
        loading={app.loading}
        error={
          app.error
            ? words.failed
              ? `${words.failed} · ${app.error}`
              : app.error
            : undefined
        }
        onRetry={() => void app.reload()}
      />
    ) : null;
  const empty = !app.visible.length
    ? app.query.trim()
      ? words.noMatch
      : words.empty
    : null;
  const detail = pane?.(app.selected);
  const preview = <>{state}{detail ?? (state ? null : empty ? <p>{empty}</p> : !app.selected && overview?.length ? <div className="surface-collection-overview"><InspectorFacts header={false} name={`${label} facts`} rows={overview} /></div> : null)}</>;
  return (
    <PreferencePane label={label} testId={ids.windowTestId}>
      {layout === "deck" ? (
        <DeckBack label={label} open={Boolean(shown) && hasWords(preview)} onBack={back} />
      ) : null}
      <ListPane
        notice={notice}
        onReveal={() => setOpen(true)}
        hostBack={compact && hosted}
        backLabel={label}
        deck={layout === "deck"}
        listShare={listShare}
        open={open || paneOpen}
        onBack={back}
        label={`Selected ${label.toLocaleLowerCase()}`}
        listTestId={ids.listTestId}
        previewTestId={ids.paneTestId}
        list={
          <>
            <ListView
              ordered
              groups={app.groups}
              {...list}
              label={label}
              rows={app.visible.map(row)}
              selectedId={app.selected ? row(app.selected).id : null}
              onSelect={(id) => {
                app.setPicked(id);
                setOpen(true);
                onSelect?.();
              }}
              onClearSelection={() => app.setPicked(null)}
              onOpen={(id) => {
                setOpen(true);
                list.onOpen?.(id);
              }}
              toolbar={{
                ...list.toolbar,
                testId: ids.toolbarTestId,
                trailing:
                  list.toolbar?.trailing ??
                  (layout === "deck" && compact && shown ? null : (
                    <StringGadget
                      label={words.find}
                      type={app.serverSearch ? "search" : "text"}
                      value={app.query}
                      onChange={app.setQuery}
                    />
                  )),
              }}
            />
          </>
        }
      >
        {preview}
      </ListPane>
      <StatusBar data-testid={ids.statusTestId} parts={status} transient={transient} />
      {children}
    </PreferencePane>
  );
}

function DeckBack({
  label,
  open,
  onBack,
}: {
  label: string;
  open: boolean;
  onBack(): void;
}) {
  const compact = useCompactViewport(),
    callback = useRef(onBack);
  callback.current = onBack;
  useWindowBack(
    compact && open
      ? { label: "Back", onBack: () => callback.current() }
      : null,
    [compact, open, label],
  );
  return null;
}
