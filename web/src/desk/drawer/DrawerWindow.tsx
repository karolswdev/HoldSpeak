/** PHILO-14 A2 — a Project is a drawer (ratified board A-2, A-2L, A-2 at 393).
 *
 *  The head is the Room's intelligence line (needs you, the target date,
 *  status, the object count), the Icons | List view (remembered per drawer)
 *  and the Room one press away. The body is the Project's objects as icons
 *  (IconGrid of DeskIcons with their lamps) or as a real list (ObjectList:
 *  Name, Kind, When, State; sort by header). The status bar counts the
 *  objects and the selection; the toolbar holds Open, Get Info and Register
 *  (W6, atlas pass 3: no dead foot).
 *
 *  The ruling (lane A2): the drawer is the Project's face; the Room is its
 *  intelligence, one press away (the `Room` Button in the head).
 */
import { useEffect, useMemo, useState } from "react";
import { Button } from "../../components/signal/Signal";
import {
  DeskIcon,
  Toolbar,
  ToolbarFold,
  ToolGlyph,
  StatusBar,
  ParkReceipt,
  restoreFailedOutcome,
  restoredOutcome,
  IconGrid,
  ObjectList,
  DotWord,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  SurfaceState,
  humanTime,
  objectSprite,
  type ObjectSort,
  type ObjectSortKey,
  type StatusStripItem,
} from "../surface";
import { RoomAskWell, SourceGlyph, emblemFor, useRoomAsk } from "../../features/project-room/ProjectRoomCore";
import type { RoomSnapshot } from "../../features/project-room/model";
import { openProjectRoomAt, refOpener } from "../openObject";
import { DeskWindowFrame } from "../components/DeskWindow";
import { restoreMeeting } from "../api";
import { openProjectRoom } from "../shell";
import { useDesk } from "../store";
import { useCompactViewport } from "../useCompactViewport";
import { spriteUrl } from "../sprites";
import { windowName } from "../windowName";
import { memberOpens, openMember } from "./open";
import { drawerWindowId, useDrawers, type OpenDrawer } from "./store";
import { useDrawerData, type DrawerRead } from "./useDrawerData";
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
import { RoomPrograms } from "../programs/RoomPrograms";
import { plainReason } from "../surface/plainFailure";
import { registerProjectRepository, registrable, useProjectRepository } from "../projectRepository";
import "./drawer.css";

export type DrawerView = "icons" | "list";

/** `16 objects · 1 selected` in sentence case (W3-B, atlas 2026-10-27: no
 *  mono caps in a status bar); a zero is never said (UX-CANON A.8). */
export function drawerReceipt(count: number, selected: number): string {
  return [count > 0 ? `${count} ${count === 1 ? "object" : "objects"}` : "", selected > 0 ? `${selected} selected` : ""]
    .filter(Boolean)
    .join(" · ");
}

/** The Room window's head facts, each a dot and a sentence-case word
 *  (W2-BUILDER, atlas 2026-10-27: no caps tokens): the reads that failed
 *  (A.10), Partial, `N need you`, the target, the status, the object count.
 *  A zero is never said (A.8). */
export function headItems(head: DrawerHead, count: number, failed: readonly DrawerRead[]): StatusStripItem[] {
  const items: StatusStripItem[] = [];
  // A failed read is named, never an empty or complete drawer (A.10).
  for (const read of failed) {
    items.push({ key: `fail-${read}`, lamp: "fail", text: `${sentenceWord(read)} not read`, testId: "drawer-not-read" });
  }
  if (failed.length && count > 0) items.push({ key: "partial", text: "Partial", testId: "drawer-partial" });
  if (head.needsYou > 0) items.push({ key: "need", lamp: "warn", text: `${head.needsYou} need you` });
  if (head.target) {
    items.push({ key: "target", text: `${head.targetPassed ? "Overdue" : "Target"} ${dateWord(head.target)}` });
  }
  // An unread section is never spoken as ON TRACK.
  if (head.status && !(failed.length && head.statusTone === "ok")) {
    items.push({ key: "status", lamp: head.statusTone, text: sentenceWord(head.status) });
  }
  if (count > 0) items.push({ key: "objects", text: `${count} ${count === 1 ? "object" : "objects"}` });
  return items;
}

/** `AT RISK` → `At risk`. */
function sentenceWord(word: string): string {
  const lower = String(word).toLowerCase();
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

/** `NOV 5` → `Nov 5`. */
function dateWord(word: string): string {
  return String(word).replace(/[A-Z]{3,}/g, (month) => month.charAt(0) + month.slice(1).toLowerCase());
}

/** The head facts drawn as dot + word (DotWord), never a mono caps strip. */
function HeadFacts({ items }: { items: readonly StatusStripItem[] }) {
  if (!items.length) return null;
  return (
    <span className="drawer-head-facts">
      {items.map((item) => item.lamp ? (
        <DotWord key={item.key} tone={item.lamp} data-testid={item.testId}>{item.text}</DotWord>
      ) : (
        <span key={item.key} className="kit-dotword drawer-head-fact" data-testid={item.testId}>{item.text}</span>
      ))}
    </span>
  );
}

/** A source's scope in words: a connection reference (`site|account`) or a
 *  bare host is the provider's name (UX-CANON A.9 as amended 2026-10-25: no
 *  host or address on a working row). */
export function sourceScopeWords(provider: string, scope: string): string {
  const name = provider === "jira" ? "Jira" : provider === "github" ? "GitHub" : provider === "confluence" ? "Confluence" : sentenceWord(provider || "Source");
  if (!scope) return name;
  if (scope.includes("|") || scope.includes("@") || /^[\w-]+(\.[\w-]+)+(:\d+)?$/.test(scope)) return name;
  return scope;
}

/** The Room window's Sources: one kit LedgerRow per accepted source (the
 *  provider's plate, the scope, its one state word). Pause, Resume and
 *  Remove live in the Room's Steward posture (the Section's Steward verb). */
export function sourceRows(room: RoomSnapshot | null): Array<{
  id: string; plate: string; scope: string; meta: string; tone?: "ok" | "warn" | "fail"; provider: string;
}> {
  if (!room || room.sources.state !== "ok") return [];
  return room.sources.items
    .filter((src) => !src.suggested)
    .map((src) => {
      const checked = src.checkedAt ? checkedWords(humanTime(src.checkedAt)) : "";
      const provider = src.provider;
      if (src.state === "cant_check") return { id: src.watchId, plate: emblemFor(src.provider), scope: src.scope, meta: "Can't check", tone: "fail" as const, provider };
      if (src.state === "paused") return { id: src.watchId, plate: emblemFor(src.provider), scope: src.scope, meta: "Paused", provider };
      if (src.freshness === "stale") {
        return { id: src.watchId, plate: emblemFor(src.provider), scope: src.scope, meta: checked ? `Stale · checked ${checked}` : "Stale", tone: "warn" as const, provider };
      }
      return {
        id: src.watchId,
        plate: emblemFor(src.provider),
        scope: src.scope,
        meta: checked ? `Checked ${checked}` : "Never checked",
        tone: checked ? ("ok" as const) : undefined,
        provider,
      };
    });
}

/** `1m ago` → `1 min ago`, `3h ago` → `3 h ago`, `2d ago` → `2 days ago`:
 *  a quiet sans fact, never a mono caps token. */
export function checkedWords(time: string): string {
  return time
    .replace(/^(\d+)m ago$/, "$1 min ago")
    .replace(/^(\d+)h ago$/, (_, n) => `${n} ${n === "1" ? "hour" : "hours"} ago`)
    .replace(/^(\d+)d ago$/, (_, n) => `${n} ${n === "1" ? "day" : "days"} ago`);
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
      setRegisterFailure(`Not registered · ${plainReason(reason)}`);
    } finally {
      setRegistering(false);
    }
  };
  const info = (member: DrawerMember | null) => {
    useDrawers.getState().openInfo(member ?? projectInfoMember(projectId, name), projectId);
  };
  // PHILO-14 C3: drop to hand. A work item drags out of the icons; an agent
  // here takes it; the selection's Hand to coder is the same hand by press
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
  // Phase 16: the Room window's Sources and its AskWell (the Room's own
  // ask: the same controller, the same well, the model's egress chip).
  const sources = sourceRows(data.room);
  const ask = useRoomAsk(projectId, data.name);
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
      // PHILO-16: the drawer is its project's Room (Window ▸ Gather).
      room={`project:${projectId}`}
      open
      unmountOnMinimize
      onClose={() => useDrawers.getState().closeDrawer(projectId)}
    >
      <div className="desk-pullout-body drawer-body" data-interior="editor">
        {/* W3-B (atlas 2026-10-27): the title bar is the title (no second
            name in the body); the view and the Room's doors are the
            toolbar's verbs; the head facts are the status bar's. */}
        <Toolbar
          label="Drawer"
          data-testid="drawer-filter"
          trailingStays
          trailing={(
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
          )}
        >
          <Button dense variant="secondary" onClick={() => openProjectRoom(projectId)}>
            <ToolGlyph kind="project" />Room
          </Button>
          {/* W6 (atlas pass 3, defect 13): the foot's verbs live here. Open
              shows only for a selection that opens (never a ghost); at
              phone width the quiet verbs fold into More ▾. */}
          {selected && memberOpens(selected) ? (
            <Button dense variant="secondary" onClick={() => open(selected)} title={selected.url || undefined}
              data-testid="drawer-open">
              <ToolGlyph kind="open" />Open
            </Button>
          ) : null}
          {data.failed.length ? (
            <Button dense variant="ghost" onClick={data.retry}>
              <ToolGlyph kind="retry" />Retry
            </Button>
          ) : null}
          <ToolbarFold
            data-testid="drawer-fold"
            verbs={[
              { key: "history", label: "History", testId: "drawer-history", onSelect: () => openProjectRoomAt(projectId, "history") },
              ...(selectedHand ? [{ key: "hand", label: "Hand to agent", testId: "drawer-hand", onSelect: handSelected }] : []),
              { key: "info", label: "Get Info", testId: "drawer-get-info", onSelect: () => info(selected) },
              ...(toRegister ? [{ key: "register", label: "Register", testId: "drawer-register", busy: registering, onSelect: () => void register() }] : []),
            ]}
          />
        </Toolbar>
        <div className="drawer-scroll">
          <HandConfirmSlot host={host} />
          {data.loading ? (
            <SurfaceState loading />
          ) : !members.length && data.failed.length ? null : !members.length ? (
            <SurfaceState empty emptyLabel="Nothing filed here" emptyImage={spriteUrl("project", projectId)} emptyKind="project" />
          ) : view === "icons" ? (
            <IconGrid well label={name} onClear={() => setSelectedId(null)}>
              {members.map((m) => {
                // No drag gesture at 393 in any view (Astra P3 on #946): the hand
                // there is the footer's Hand to coder.
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
          {data.room ? (
            <SurfaceSection
              label="Sources"
              count={sources.length || null}
              data-testid="drawer-sources"
              actions={(
                <Button dense variant="ghost" data-testid="drawer-steward" onClick={() => openProjectRoomAt(projectId, "steward")}>
                  Watch sources
                </Button>
              )}
            >
              {sources.length ? (
                <SurfaceLedger label="Sources" cols="kit">
                  <ul className="surface-ledger-rows">
                    {sources.map((src) => (
                      <SurfaceLedgerRow
                        key={src.id}
                        data-testid="drawer-source-row"
                        lead={<SourceGlyph source={src.provider} />}
                        primary={sourceScopeWords(src.provider, src.scope)}
                        meta={<DotWord tone={src.tone ?? "idle"}>{src.meta}</DotWord>}
                      />
                    ))}
                  </ul>
                </SurfaceLedger>
              ) : null}
            </SurfaceSection>
          ) : null}
          {/* Programs (2026-10-28, §9b): the Room's Programs fold. */}
          {data.room?.programs?.state === "ok" ? <RoomPrograms programs={data.room.programs.programs} /> : null}
          {data.room ? (
            <RoomAskWell ask={ask} projectId={projectId} onOpenRef={(ref) => refOpener(ref)?.()} />
          ) : null}
        </div>
      </div>
      <StatusBar
        data-testid="drawer-status"
        items={[{
          key: "facts",
          text: receipt ? (
            <ParkReceipt outcome={receipt} onRestore={(ids) => void restore(ids)} data-testid="drawer-park-receipt" />
          ) : registerFailure ? (
            <span className="drawer-receipt" data-tone="fail" role="status">{registerFailure}</span>
          ) : (
            <span className="drawer-receipt" data-testid="drawer-facts">
              <HeadFacts items={headItems(data.head, members.length || 0, data.failed)} />
              {selected ? <span className="kit-dotword drawer-head-fact">1 selected</span> : null}
            </span>
          ),
        }]}
      />
    </DeskWindowFrame>
  );
}
