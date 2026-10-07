/** PHILO-14 A2 — a Project is a drawer (ratified board A-2, A-2L, A-2 at 393).
 *
 *  The head is the Room's intelligence line (needs you, the target date,
 *  status, the object count), the Icons | List view (remembered per drawer)
 *  and the Room one press away. The body is the Project's objects as icons
 *  (IconGrid of DeskIcons with their lamps) or as a real list (ObjectList:
 *  Name, Kind, When, State; sort by header). The footer counts the objects
 *  and the selection, and holds Get Info and Open.
 *
 *  The ruling (lane A2): the drawer is the Project's face; the Room is its
 *  intelligence, one press away (the `Room` Button in the head).
 */
import { useEffect, useMemo, useState } from "react";
import { Button } from "../../components/signal/Signal";
import {
  DeskIcon,
  FilterTokens,
  IconGrid,
  LampGadget,
  ObjectList,
  SurfaceFooter,
  SurfaceState,
  objectSprite,
  type ObjectSort,
  type ObjectSortKey,
} from "../surface";
import { DeskWindowFrame } from "../components/DeskWindow";
import { openProjectRoom } from "../shell";
import { useDesk } from "../store";
import { useCompactViewport } from "../useCompactViewport";
import { windowName } from "../windowName";
import { memberOpens, openMember } from "./open";
import { drawerWindowId, useDrawers, type OpenDrawer } from "./store";
import { useDrawerData } from "./useDrawerData";
import type { DrawerHead, DrawerMember } from "./members";
import "./drawer.css";

export type DrawerView = "icons" | "list";

/** `16 OBJECTS · 1 SELECTED`; a zero is never said (UX-CANON A.8). */
export function drawerReceipt(count: number, selected: number): string {
  return [count > 0 ? `${count} ${count === 1 ? "OBJECT" : "OBJECTS"}` : "", selected > 0 ? `${selected} SELECTED` : ""]
    .filter(Boolean)
    .join(" · ");
}

function HeadFacts({ head, count }: { head: DrawerHead; count: number }) {
  return (
    <div className="drawer-facts" data-testid="drawer-facts">
      {head.needsYou > 0 ? <LampGadget label={`${head.needsYou} NEED YOU`} on tone="warn" /> : null}
      {head.target ? (
        <span className="drawer-fact" data-tone={head.targetPassed ? "fail" : undefined}>
          {head.targetPassed ? "OVERDUE" : "TARGET"} <b>{head.target}</b>
        </span>
      ) : null}
      {head.status ? (
        <span className="drawer-fact" data-tone={head.statusTone}>
          STATUS <b>{head.status}</b>
        </span>
      ) : null}
      {count > 0 ? (
        <span className="drawer-fact">
          <b>{count}</b> {count === 1 ? "OBJECT" : "OBJECTS"}
        </span>
      ) : null}
    </div>
  );
}

export function DrawerWindow({ drawer }: { drawer: OpenDrawer }) {
  const { projectId } = drawer;
  const data = useDrawerData(projectId);
  const compact = useCompactViewport();
  const prefKey = `project:${projectId}`;
  const saved = useDesk((s) => s.zoneViewPrefs[prefKey]?.view);
  // 1440 shows icons, 393 a list (the PROPOSAL's mold rule); a choice the
  // owner made in this drawer wins and is remembered.
  const view: DrawerView = saved ?? (compact ? "list" : "icons");
  const [sort, setSort] = useState<ObjectSort>({ key: "name", dir: "asc" });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const members = data.members;
  const selected = useMemo(() => members.find((m) => m.id === selectedId) ?? null, [members, selectedId]);
  useEffect(() => {
    if (selectedId && !selected) setSelectedId(null);
  }, [selectedId, selected]);

  const name = windowName({ kind: "project", name: data.name }, projectId);
  const byId = (id: string) => members.find((m) => m.id === id);
  const open = (member: DrawerMember | undefined | null) => {
    if (member && memberOpens(member)) openMember(member);
  };
  const info = (member: DrawerMember | null) => {
    if (member) useDrawers.getState().openInfo(member, projectId);
  };
  const onSort = (key: ObjectSortKey) =>
    setSort((now) => (now.key === key ? { key, dir: now.dir === "asc" ? "desc" : "asc" } : { key, dir: "asc" }));

  return (
    <DeskWindowFrame
      id={drawerWindowId(projectId)}
      title={name}
      label={name}
      kindWord="Drawer"
      glyph="▤"
      icon={<img className="drawer-winicon" src={objectSprite("project", projectId)} alt="" />}
      className="desk-pullout drawer-window"
      minW={340}
      minH={280}
      defaultW={900}
      defaultH={600}
      origin={drawer.origin}
      open
      unmountOnMinimize
      onClose={() => useDrawers.getState().closeDrawer(projectId)}
    >
      <div className="desk-pullout-body drawer-body">
        <div className="drawer-scroll">
          <div className="drawer-head">
            <HeadFacts head={data.head} count={members.length || 0} />
            <span className="drawer-head-verbs">
              <FilterTokens
                label="Drawer view"
                value={view}
                onChange={(next) => useDesk.getState().setZoneViewPref(prefKey, { view: next as DrawerView })}
                options={[
                  { value: "icons", label: "Icons" },
                  { value: "list", label: "List" },
                ]}
              />
              <Button dense variant="ghost" onClick={() => openProjectRoom(projectId)}>
                Room
              </Button>
            </span>
          </div>
          {data.error && !members.length ? (
            <SurfaceState error={data.error} onRetry={data.reload} />
          ) : data.loading ? (
            <SurfaceState loading />
          ) : !members.length ? (
            <SurfaceState empty emptyLabel="Nothing filed here" />
          ) : view === "icons" ? (
            <IconGrid label={name} onClear={() => setSelectedId(null)}>
              {members.map((m) => (
                <DeskIcon
                  key={m.id}
                  id={m.id}
                  kind={m.kind}
                  name={m.name}
                  kindWord={m.kindWord}
                  sprite={m.sprite}
                  selected={m.id === selectedId}
                  lamp={m.lamp ? { tone: m.lamp.tone, label: m.lamp.label } : undefined}
                  onSelect={() => setSelectedId(m.id)}
                  onOpen={() => open(m)}
                />
              ))}
            </IconGrid>
          ) : (
            <ObjectList
              label={name}
              rows={members}
              sort={sort}
              onSort={onSort}
              selectedId={selectedId}
              onSelect={setSelectedId}
              onOpen={(id) => open(byId(id))}
            />
          )}
        </div>
      </div>
      <SurfaceFooter
        receipt={<span className="drawer-receipt">{drawerReceipt(members.length, selected ? 1 : 0)}</span>}
        verbs={
          <>
            <Button dense variant="ghost" disabled={!selected} onClick={() => info(selected)}>
              Get Info
            </Button>
            <Button dense variant="secondary" disabled={!selected || !memberOpens(selected)} onClick={() => open(selected)}>
              Open
            </Button>
          </>
        }
      />
    </DeskWindowFrame>
  );
}
