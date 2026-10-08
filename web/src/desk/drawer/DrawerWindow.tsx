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
  EgressChip,
  FilterTokens,
  ParkReceipt,
  restoreFailedOutcome,
  restoredOutcome,
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
import { restoreMeeting } from "../api";
import { openProjectRoom } from "../shell";
import { useDesk } from "../store";
import { useCompactViewport } from "../useCompactViewport";
import { windowName } from "../windowName";
import { memberOpens, openMember } from "./open";
import { drawerWindowId, useDrawers, type OpenDrawer } from "./store";
import { useDrawerData, type DrawerRead } from "./useDrawerData";
import { urlHost } from "./members";
import {
  HandConfirmSlot,
  beginHand,
  drawerHost,
  handOriginOfRef,
  handSourceProps,
  handTargetProps,
  useDropHand,
} from "../hand";
import type { DrawerHead, DrawerMember } from "./members";
import { plainFailure } from "../surface/plainFailure";
import { registerProjectRepository, registrable, useProjectRepository } from "../projectRepository";
import "./drawer.css";

export type DrawerView = "icons" | "list";

/** `16 OBJECTS · 1 SELECTED`; a zero is never said (UX-CANON A.8). */
export function drawerReceipt(count: number, selected: number): string {
  return [count > 0 ? `${count} ${count === 1 ? "OBJECT" : "OBJECTS"}` : "", selected > 0 ? `${selected} SELECTED` : ""]
    .filter(Boolean)
    .join(" · ");
}

function HeadFacts({ head, count, failed }: { head: DrawerHead; count: number; failed: readonly DrawerRead[] }) {
  return (
    <div className="drawer-facts" data-testid="drawer-facts">
      {/* A failed read is named, never an empty or complete drawer (A.10). */}
      {failed.map((read) => (
        <span key={read} className="drawer-fact" data-tone="fail" data-testid="drawer-not-read">
          {read} · <b>NOT READ</b>
        </span>
      ))}
      {failed.length && count > 0 ? (
        <span className="drawer-fact" data-tone="fail" data-testid="drawer-partial">
          <b>PARTIAL</b>
        </span>
      ) : null}
      {head.needsYou > 0 ? <LampGadget label={`${head.needsYou} NEED YOU`} on tone="warn" /> : null}
      {head.target ? (
        <span className="drawer-fact" data-tone={head.targetPassed ? "fail" : undefined}>
          {head.targetPassed ? "OVERDUE" : "TARGET"} <b>{head.target}</b>
        </span>
      ) : null}
      {/* An unread section is never spoken as ON TRACK. */}
      {head.status && !(failed.length && head.statusTone === "ok") ? (
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

/** The Project itself as a drawer member: what Get Info opens with nothing selected. */
export function projectInfoMember(projectId: string, name: string): DrawerMember {
  return {
    id: projectId,
    ref: `project:${projectId}`,
    kind: "project",
    name,
    kindWord: "Project",
    sprite: objectSprite("project", projectId),
    facts: {},
  };
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
  // PHILO-13-02 on the surviving face: the park made from this drawer's Info
  // window, with Restore (one press), also when the drawer is now empty.
  const receipt = useDrawers((s) => s.receipts[projectId]);
  const restore = async (ids: string[]) => {
    const store = useDrawers.getState();
    try {
      for (const id of ids) await restoreMeeting(id);
      store.setReceipt(projectId, restoredOutcome(ids));
      store.changed();
      void useDesk.getState().refresh();
    } catch {
      store.setReceipt(projectId, restoreFailedOutcome(ids));
    }
  };
  const byId = (id: string) => members.find((m) => m.id === id);
  const open = (member: DrawerMember | undefined | null) => {
    if (member && memberOpens(member)) openMember(member);
  };
  // PHILO-15 16: Get Info with nothing selected is the Project's own Info
  // (its REPOSITORY, CLONED or not; Register when the Room watches one).
  const repository = useProjectRepository(projectId);
  const [registering, setRegistering] = useState(false);
  const [registerFailure, setRegisterFailure] = useState("");
  const toRegister = registrable(repository.state);
  const register = async () => {
    if (!toRegister) return;
    setRegistering(true);
    setRegisterFailure("");
    try {
      await registerProjectRepository(projectId, toRegister);
      repository.reload();
    } catch (reason) {
      setRegisterFailure(plainFailure("NOT REGISTERED", reason));
    } finally {
      setRegistering(false);
    }
  };
  const info = (member: DrawerMember | null) => {
    useDrawers.getState().openInfo(member ?? projectInfoMember(projectId, name), projectId);
  };
  // PHILO-14 C3: drop to hand. A work item drags out of the icons; an agent
  // here takes it; the selection's Hand to agent is the same hand by press
  // (the keyboard path, and the only one at 393).
  const host = drawerHost(projectId);
  const drag = useDropHand((s) => s.drag);
  const handOf = (member: DrawerMember | null) =>
    member ? handOriginOfRef(member.ref, member.name, projectId) : null;
  const selectedHand = handOf(selected);
  const handSelected = () => {
    if (!selected || !selectedHand) return;
    void beginHand(selectedHand, {
      host,
      source: { kind: selected.kind, id: selected.id, sprite: selected.sprite },
    });
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
            <HeadFacts head={data.head} count={members.length || 0} failed={data.failed} />
            <span className="drawer-head-verbs">
              {data.failed.length ? (
                <Button dense variant="ghost" onClick={data.retry}>
                  Retry
                </Button>
              ) : null}
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
          <HandConfirmSlot host={host} />
          {data.loading ? (
            <SurfaceState loading />
          ) : !members.length && data.failed.length ? null : !members.length ? (
            <SurfaceState empty emptyLabel="Nothing filed here" />
          ) : view === "icons" ? (
            <IconGrid label={name} onClear={() => setSelectedId(null)}>
              {members.map((m) => {
                // No drag gesture at 393 in any view (Astra P3 on #946): the hand
                // there is the footer's Hand to agent.
                const hand = compact ? null : handOf(m);
                return (
                  <DeskIcon
                    key={m.id}
                    id={m.id}
                    kind={m.kind}
                    name={m.name}
                    kindWord={m.kindWord}
                    sprite={m.sprite}
                    spriteSelected={m.spriteSelected}
                    selected={m.id === selectedId}
                    lamp={m.lamp ? { tone: m.lamp.tone, label: m.lamp.label } : undefined}
                    onSelect={() => setSelectedId(m.id)}
                    onOpen={() => open(m)}
                    drop={drag?.over === m.ref}
                    ghost={drag?.host === host && drag.source.id === m.id}
                    {...(hand ? handSourceProps({ origin: hand, source: { kind: m.kind, id: m.id, sprite: m.sprite }, host }) : {})}
                    {...handTargetProps(m.ref)}
                  />
                );
              })}
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
        egress={selected?.url ? <EgressChip label={urlHost(selected.url)} scope="cloud" /> : null}
        receipt={
          receipt ? (
            <ParkReceipt outcome={receipt} onRestore={(ids) => void restore(ids)} data-testid="drawer-park-receipt" />
          ) : registerFailure ? (
            <span className="drawer-receipt" data-tone="fail" role="status">{registerFailure}</span>
          ) : (
            <span className="drawer-receipt">{drawerReceipt(members.length, selected ? 1 : 0)}</span>
          )
        }
        verbs={
          <>
            {toRegister ? (
              <Button dense variant="ghost" loading={registering} onClick={() => void register()} data-testid="drawer-register">
                Register
              </Button>
            ) : null}
            <Button dense variant="ghost" onClick={() => info(selected)} data-testid="drawer-get-info">
              Get Info
            </Button>
            {selectedHand ? (
              <Button dense variant="ghost" onClick={handSelected} data-testid="drawer-hand">
                Hand to agent
              </Button>
            ) : null}
            <Button dense variant="secondary" disabled={!selected || !memberOpens(selected)} onClick={() => open(selected)}>
              Open
            </Button>
          </>
        }
      />
    </DeskWindowFrame>
  );
}
