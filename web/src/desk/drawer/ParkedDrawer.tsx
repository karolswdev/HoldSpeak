/** PHILO-15 04 (gap 14) — Parked is a drawer of objects (the Phase 14
 *  charter; Muad'Dib's ruling for lane 04).
 *
 *  The screen's Parked icon opens this window: every parked object across
 *  kinds (meetings, Workbench items, Projects) in ONE ObjectList, read from
 *  `GET /api/desk/parked`. Composed of ratified species only: the drawer
 *  frame (DrawerWindow's), ObjectList, ParkReceipt, SurfaceFooter, Button.
 *
 *  A row's Open goes to where the object lives (the Meetings window, its
 *  Workbench, its Project drawer). Its verb is Restore, on that kind's own
 *  route, with the one park receipt (`RESTORED hh:mm`, or NOT RESTORED +
 *  Retry). A kind the hub could not read is named, never an empty kind.
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch } from "../../lib/api";
import {
  DotWord,
  ObjectList,
  ParkReceipt,
  Toolbar,
  ToolGlyph,
  SurfaceFooter,
  SurfaceState,
  objectSprite,
  restoreFailedOutcome,
  restoredOutcome,
  type ObjectListRow,
  type ObjectSort,
  type ObjectSortKey,
  type ParkOutcome,
} from "../surface";
import { DeskWindowFrame } from "../components/DeskWindow";
import { restoreMeeting, restoreProject, restoreWorkbenchItem } from "../api";
import { openProjectRoom } from "../shell";
import { openSourceRef } from "../surface";
import { useDesk } from "../store";
import { useOnDeskChanged } from "../useDeskChangedRefresh";
import { drawerReceipt } from "./DrawerWindow";
import { whenWord } from "./members";
import { PARKED_WINDOW_ID, useDrawers } from "./store";
import "./drawer.css";

export type ParkedKind = "meeting" | "workbench_item" | "project";

export interface ParkedItem {
  ref: string;
  kind: ParkedKind;
  id: string;
  name: string;
  when: string;
  home: { workbench_id?: string; workbench_name?: string };
}

export interface ParkedRead {
  items: ParkedItem[];
  not_read: ParkedKind[];
  /** Kinds read part way: some rows are here, the rest NOT READ. */
  partial?: ParkedKind[];
}

/** The word of a kind the hub could not read (sentence case, W3-ZONE). */
export const PARKED_KIND_WORD: Record<ParkedKind, string> = {
  meeting: "Meetings",
  workbench_item: "Automation items",
  project: "Projects",
};

/** A parked row's kind word, sentence case (W3-ZONE: no caps in a list). */
export const PARKED_ROW_KIND: Record<ParkedKind, string> = {
  meeting: "Meeting",
  workbench_item: "Automation item",
  project: "Project",
};

/** `TODAY` → `Today`, `OCT 5` → `Oct 5`. */
function sentence(word: string): string {
  const lower = word.toLowerCase();
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

/** The list row of one parked object. */
export function parkedRow(item: ParkedItem, now: Date = new Date()): ObjectListRow {
  const at = item.when ? new Date(item.when) : null;
  const valid = at && !Number.isNaN(at.getTime()) ? at : null;
  const base = {
    id: item.ref,
    name: item.name,
    kindWord: PARKED_ROW_KIND[item.kind] ?? sentence(String(item.kind)),
    when: valid ? sentence(whenWord(valid, now)) : undefined,
    whenSort: valid ? valid.getTime() : undefined,
  };
  if (item.kind === "workbench_item") {
    return { ...base, kind: "workbench", sprite: objectSprite("workbench", item.id) };
  }
  return { ...base, kind: item.kind };
}

/** Open: where the parked object lives. */
export function openParkedHome(item: ParkedItem): void {
  // PHILO-17: a meeting opens in its own window.
  if (item.kind === "meeting") openSourceRef(`meeting:${item.id}`);
  else if (item.kind === "workbench_item" && item.home.workbench_id) {
    useDesk.getState().openWorkbenchWindow(item.home.workbench_id);
  } else if (item.kind === "project") openProjectRoom(item.id);
}

/** Restore: each kind on its own route (the existing receipts). */
export async function restoreParked(item: ParkedItem): Promise<void> {
  if (item.kind === "meeting") await restoreMeeting(item.id);
  else if (item.kind === "workbench_item") await restoreWorkbenchItem(item.home.workbench_id ?? "", item.id);
  else await restoreProject(item.id);
}

function useParked() {
  const [read, setRead] = useState<ParkedRead | null>(null);
  const [failed, setFailed] = useState(false);
  const [tick, setTick] = useState(0);
  useOnDeskChanged(() => setTick((n) => n + 1));
  const revision = useDrawers((s) => s.revision);
  const reread = useCallback(() => setTick((n) => n + 1), []);
  useEffect(() => {
    let live = true;
    apiFetch<ParkedRead>("/api/desk/parked").then(
      (body) => {
        if (!live) return;
        setRead({ items: Array.isArray(body?.items) ? body.items : [], not_read: body?.not_read ?? [], partial: body?.partial ?? [] });
        setFailed(false);
      },
      () => live && setFailed(true), // the last read stays on the glass
    );
    return () => {
      live = false;
    };
  }, [tick, revision]);
  return { read, failed, reread };
}

export function ParkedDrawer({ origin }: { origin: { x: number; y: number } | null }) {
  const { read, failed, reread } = useParked();
  const items = useMemo(() => read?.items ?? [], [read]);
  const rows = useMemo(() => items.map((item) => parkedRow(item)), [items]);
  const [sort, setSort] = useState<ObjectSort>({ key: "when", dir: "desc" });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<ParkOutcome | null>(null);
  const [busy, setBusy] = useState(false);
  const selected = useMemo(() => items.find((i) => i.ref === selectedId) ?? null, [items, selectedId]);
  useEffect(() => {
    if (selectedId && !selected) setSelectedId(null);
  }, [selectedId, selected]);

  const notRead = failed ? (["meeting", "workbench_item", "project"] as ParkedKind[]) : read?.not_read ?? [];
  const partial = failed ? [] : read?.partial ?? [];
  const byRef = (ref: string) => items.find((i) => i.ref === ref);
  const restore = async (refs: string[]) => {
    const targets = refs.map(byRef).filter((i): i is ParkedItem => Boolean(i));
    if (!targets.length || busy) return;
    setBusy(true);
    try {
      for (const item of targets) await restoreParked(item);
      setReceipt(restoredOutcome(refs));
      useDrawers.getState().changed();
      void useDesk.getState().refresh();
    } catch {
      setReceipt(restoreFailedOutcome(refs));
    } finally {
      setBusy(false);
      reread();
    }
  };
  const onSort = (key: ObjectSortKey) =>
    setSort((now) => (now.key === key ? { key, dir: now.dir === "asc" ? "desc" : "asc" } : { key, dir: "asc" }));

  return (
    <DeskWindowFrame
      id={PARKED_WINDOW_ID}
      title="Archive"
      label="Archive"
      kindWord="Drawer"
      glyph="▤"
      icon={<img className="drawer-winicon" src={objectSprite("parked", "parked")} alt="" />}
      className="desk-pullout drawer-window parked-drawer"
      minW={340}
      minH={280}
      defaultW={760}
      defaultH={520}
      origin={origin}
      open
      unmountOnMinimize
      onClose={() => useDrawers.getState().closeParked()}
    >
      {/* W3-ZONE (atlas 2026-10-27): the Archive shares the drawer grammar —
          the title bar is the title, a toolbar holds the verbs (only when
          there is a row to act on: no dead verbs), the list edge to edge,
          the facts in the status bar. */}
      <div className="desk-pullout-body drawer-body" data-interior="list" data-testid="parked-drawer">
        {rows.length || notRead.length ? (
          <Toolbar label="Archive">
            {rows.length ? (
              <>
                <Button dense variant="secondary" disabled={!selected} onClick={() => selected && openParkedHome(selected)}>
                  <ToolGlyph kind="open" />Open
                </Button>
                <Button
                  dense
                  variant="ghost"
                  disabled={!selected || busy}
                  loading={busy}
                  onClick={() => selected && void restore([selected.ref])}
                  data-testid="parked-restore"
                >
                  <ToolGlyph kind="retry" />Restore
                </Button>
              </>
            ) : null}
            {notRead.length ? (
              <Button dense variant="ghost" onClick={reread}>
                <ToolGlyph kind="retry" />Retry
              </Button>
            ) : null}
          </Toolbar>
        ) : null}
        <div className="drawer-scroll parked-scroll">
          {!read && !failed ? (
            <SurfaceState loading />
          ) : !rows.length && notRead.length ? null : !rows.length ? (
            <SurfaceState empty emptyLabel="Nothing parked" emptyImage={objectSprite("parked", "parked")} />
          ) : (
            <ObjectList
              label="Archive"
              rows={rows}
              density="dense"
              visibleColumns={["name", "kind", "when"]}
              // Restore is the Archive's act: a press selects, a double press
              // or Enter opens where the object lives.
              pressOpens={false}
              sort={sort}
              onSort={onSort}
              selectedId={selectedId}
              onSelect={setSelectedId}
              onOpen={(ref) => {
                const item = byRef(ref);
                if (item) openParkedHome(item);
              }}
            />
          )}
        </div>
      </div>
      <SurfaceFooter
        receipt={
          receipt ? (
            <ParkReceipt outcome={receipt} onRestore={(refs) => void restore(refs)} data-testid="parked-receipt" />
          ) : (
            <span className="drawer-receipt">
              {notRead.map((kind) => (
                <DotWord key={kind} tone="fail" data-testid="parked-not-read">
                  {PARKED_KIND_WORD[kind]} not read{partial.includes(kind) ? " · partial" : ""}
                </DotWord>
              ))}
              {drawerReceipt(rows.length, selected ? 1 : 0) || null}
            </span>
          )
        }
      />
    </DeskWindowFrame>
  );
}
