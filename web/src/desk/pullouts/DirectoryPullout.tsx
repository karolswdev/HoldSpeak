/** Directory (Zone) pullout content (HS-117-15).
 *
 *  W3-ZONE (Window Program, atlas 2026-10-27): the zone drawer is a drawer
 *  on the window grammar, as the Project drawer is (#1527 DrawerWindow):
 *  the title bar is the title; a toolbar (Open, Dictate about this, the
 *  Icons | List view at its right end); the contents edge to edge as a
 *  dense one-line list (a press opens the object) or as icons; the count in
 *  the status bar (`3 objects`), never a `Contents · N` heading. */
import { useMemo, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { objectByRef, type WorldObject } from "../world";
import { normalizeRef } from "../screen/compose";
import { openScreenRef } from "../screen/open";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { productLabel } from "../../lib/productLanguage";
import {
  DeskIcon,
  IconGrid,
  ObjectList,
  SurfaceFooter,
  SurfaceState,
  Toolbar,
  ToolGlyph,
  objectSprite,
  type ObjectListRow,
  type ObjectSort,
  type ObjectSortKey,
} from "../surface";
import { drawerReceipt } from "../drawer/DrawerWindow";
import { whenWord } from "../drawer/members";
import type { PulloutContentProps } from "./types";
import "./zone-drawer.css";

type ZoneView = "icons" | "list";

interface ZoneMember {
  ref: string;
  member: WorldObject | null;
}

/** `TODAY` → `Today`, `OCT 5` → `Oct 5`: quiet sans metadata. */
function sentence(word: string): string {
  const lower = word.toLowerCase();
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

function memberTime(member: WorldObject): Date | null {
  const r = member.ref as unknown as Record<string, unknown>;
  const raw = r.lastModified || r.updatedAt || r.endedAt || r.createdAt;
  if (!raw) return null;
  const at = new Date(String(raw));
  return Number.isNaN(at.getTime()) ? null : at;
}

/** One list row per member; an unresolved member is named Unavailable. */
export function zoneRow({ ref, member }: ZoneMember, now: Date = new Date()): ObjectListRow {
  if (!member) return { id: ref, kind: "unknown", name: "Item unavailable", kindWord: "Unavailable", nameTestId: "zone-unavailable" };
  const at = memberTime(member);
  return {
    id: ref,
    kind: member.kind,
    name: member.title || "Untitled",
    kindWord: member.kind === "directory" ? "Drawer" : productLabel(member.kind),
    when: at ? sentence(whenWord(at, now)) : undefined,
    whenSort: at ? at.getTime() : undefined,
    sprite: objectSprite(member.kind, member.id),
    // A folder sorts above the objects, as on the Floor.
    group: member.kind === "directory" ? 0 : 1,
  };
}

export function DirectoryPullout({ object: o }: PulloutContentProps) {
  const items = useDesk((s) => s.items);
  const prefKey = `directory:${o.id}`;
  const saved = useDesk((s) => s.zoneViewPrefs[prefKey]?.view);
  const view: ZoneView = saved ?? "list";
  const [sort, setSort] = useState<ObjectSort>({ key: "name", dir: "asc" });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const ir = o.ref.kind === "directory" ? o.ref : null;
  const members = useMemo<ZoneMember[]>(() => {
    if (!ir) return [];
    const childRefs = (items.directory ?? [])
      .filter((directory) => directory.parentId === ir.id && directory.id !== ir.id)
      .map((directory) => qualifiedRef("directory", directory.id));
    const seen = new Set<string>();
    return [...childRefs, ...ir.memberIds].flatMap((storedRef) => {
      const member = objectByRef(items, normalizeRef(storedRef));
      const ref = member ? qualifiedRef(member.kind, member.id) : storedRef;
      if (seen.has(ref)) return [];
      seen.add(ref);
      return [{ ref, member }];
    });
  }, [items, ir]);
  const rows = useMemo(() => members.map((m) => zoneRow(m)), [members]);
  if (!ir) return null;
  const resourceRef = qualifiedRef(o.kind, o.id);
  const byRef = (ref: string | null) => members.find((m) => m.ref === ref) ?? null;
  const selected = byRef(selectedId);
  const open = (ref: string | null) => {
    const found = byRef(ref);
    if (found?.member) openScreenRef(found.ref);
  };
  const onSort = (key: ObjectSortKey) =>
    setSort((now) => (now.key === key ? { key, dir: now.dir === "asc" ? "desc" : "asc" } : { key, dir: "asc" }));
  const name = o.title || "Drawer";

  return (
    <>
      <div className="desk-pullout-body zone-drawer-body" data-interior="list" data-testid="zone-drawer">
        <Toolbar
          label="Drawer"
          trailingStays
          trailing={members.length ? (
            <span className="drawer-view" role="group" aria-label="Drawer view">
              {(["icons", "list"] as const).map((option) => (
                <Button
                  key={option}
                  dense
                  variant={view === option ? "secondary" : "ghost"}
                  aria-pressed={view === option}
                  data-on={view === option ? "" : undefined}
                  onClick={() => useDesk.getState().setZoneViewPref(prefKey, { view: option })}
                >
                  {option === "icons" ? "Icons" : "List"}
                </Button>
              ))}
            </span>
          ) : undefined}
        >
          {selected?.member ? (
            <Button dense variant="secondary" onClick={() => open(selected.ref)} data-testid="zone-open">
              <ToolGlyph kind="open" />Open
            </Button>
          ) : null}
          <Button dense variant="ghost" onClick={() => openSurfaceOr("dictate", "/dictation", resourceRef)}>
            Dictate about this
          </Button>
        </Toolbar>
        <div className="zone-drawer-scroll">
          {!rows.length ? (
            <SurfaceState empty emptyLabel="Nothing filed here" emptyGlyph="○" />
          ) : view === "icons" ? (
            <IconGrid well label={name} onClear={() => setSelectedId(null)}>
              {rows.map((row) => (
                <DeskIcon
                  key={row.id}
                  id={row.id}
                  kind={row.kind}
                  name={row.name}
                  kindWord={row.kindWord}
                  sprite={row.sprite}
                  selected={row.id === selectedId}
                  onSelect={() => setSelectedId(row.id)}
                  onOpen={() => open(row.id)}
                />
              ))}
            </IconGrid>
          ) : (
            <ObjectList
              label={name}
              rows={rows}
              density="dense"
              visibleColumns={["name", "kind", "when"]}
              sort={sort}
              onSort={onSort}
              selectedId={selectedId}
              onSelect={setSelectedId}
              onOpen={open}
            />
          )}
        </div>
        <div className="zone-drawer-filed">
          <DeskFilingStrip objectRef={resourceRef} objectKind={o.kind} objectId={o.id} />
        </div>
      </div>
      <SurfaceFooter
        receipt={<span className="drawer-receipt" data-testid="zone-facts">{drawerReceipt(rows.length, selected ? 1 : 0)}</span>}
      />
    </>
  );
}
