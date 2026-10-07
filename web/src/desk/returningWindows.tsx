// PHILO-13-07 (B2 slice two) — the window families that live outside the
// compositor's arrays come back after a reload too, in the one workspace
// document (`places`, `window/<family>`, via `deskMemory.ts`).
//
//   Each family is watched here (one subscription per store) and its record
//   kept while it is open; a close forgets it, so a closed window stays gone.
//   <ReturningWindows /> reopens each kept family ONCE per page, through the
//   family's own opener. Restore reads (a dossier GET, a terminal or session
//   re-attach) and never saves or sends.
//
//   Pullouts restored by the compositor whose record is gone (deleted
//   elsewhere) are dropped at the first Desk read, never kept invisible.
import { useEffect } from "react";
import { useDesk } from "./store";
import { keptWindow, rememberWindow } from "./deskMemory";
import { objectByRef } from "./world";
import { useDeliveryDossier } from "./deliveryDossier";
import { useDeliveryTerminal, type OpenTarget } from "./deliveryTerminal";
import { useMissionControl } from "./missioncontrol";
import { useSteering } from "./steering";
import { useTrustWindow } from "./components/TrustWindow";
import { useDrawers, type OpenDrawer, type OpenInfo } from "./drawer/store";

type DossierRecord =
  | { kind: "story"; project: string; storyId: string; source: string }
  | { kind: "phase"; project: string; phase: number };
type InspectorRecord = { kind: "project" | "integration" | "target"; id: string };

// ---- keep: each family's record while it is open -------------------------

useDeliveryDossier.subscribe((s, prev) => {
  if (s.dossier === prev.dossier && s.loading === prev.loading && s.refusal === prev.refusal) return;
  if (s.dossier?.kind === "story") {
    rememberWindow("delivery-dossier", {
      kind: "story", project: s.dossier.project, storyId: s.dossier.storyId, source: s.dossier.sourceId,
    } satisfies DossierRecord);
  } else if (s.dossier?.kind === "phase") {
    rememberWindow("delivery-dossier", {
      kind: "phase", project: s.dossier.project, phase: s.dossier.phase,
    } satisfies DossierRecord);
  } else if (!s.loading && !s.refusal) {
    rememberWindow("delivery-dossier", null); // closed
  }
});

useDeliveryTerminal.subscribe((s, prev) => {
  if (s.openTarget !== prev.openTarget) rememberWindow("delivery-terminal", s.openTarget);
});

useMissionControl.subscribe((s, prev) => {
  if (s.open !== prev.open) rememberWindow("mission-control", s.open ? true : null);
});

useSteering.subscribe((s, prev) => {
  if (s.openKey !== prev.openKey) rememberWindow("session", s.openKey);
});

useTrustWindow.subscribe((s, prev) => {
  if (s.open !== prev.open) rememberWindow("trust", s.open ? true : null);
});

// PHILO-14 A2: open drawers and their Get Info windows (their place and
// size are the frame's panelRects; the view is zoneViewPrefs).
useDrawers.subscribe((s, prev) => {
  if (s.drawers !== prev.drawers) rememberWindow("drawers", s.drawers.length ? s.drawers : null);
  if (s.infos !== prev.infos) rememberWindow("drawer-infos", s.infos.length ? s.infos : null);
});

useDesk.subscribe((s, prev) => {
  if (s.toolInspector !== prev.toolInspector) rememberWindow("tool-inspector", s.toolInspector);
  if (s.scheduleCreateWindow !== prev.scheduleCreateWindow)
    rememberWindow("schedule-create", s.scheduleCreateWindow ? true : null);
  if (s.askOpen !== prev.askOpen) rememberWindow("ask", s.askOpen ? true : null);
  if (s.editingId !== prev.editingId) rememberWindow("editor", s.editingId);
});

// ---- return: once per page ----------------------------------------------

let restored = false;
let pruned = false;
/** The pullouts the compositor brought back from the document (load time). */
const restoredPullouts = useDesk.getState().pullouts.map((p) => p.id);
/** The editor's object waits for the first Desk read. */
let pendingEditor: string | null = null;

/** Test seam: a fresh page. */
export function __resetReturningWindows(): void {
  restored = false;
  pruned = false;
  pendingEditor = null;
}

function restoreOnce(): void {
  if (restored) return;
  restored = true;
  // Read every record first: an opener may close another family (openAsk
  // closes the editor), and its subscription would forget that record.
  const dossier = keptWindow<DossierRecord>("delivery-dossier");
  const terminal = keptWindow<OpenTarget>("delivery-terminal");
  const mission = keptWindow<boolean>("mission-control");
  const session = keptWindow<string>("session");
  const trust = keptWindow<boolean>("trust");
  const inspector = keptWindow<InspectorRecord>("tool-inspector");
  const schedule = keptWindow<boolean>("schedule-create");
  const ask = keptWindow<boolean>("ask");
  pendingEditor = keptWindow<string>("editor");
  const drawers = keptWindow<OpenDrawer[]>("drawers");
  const infos = keptWindow<OpenInfo[]>("drawer-infos");

  if (dossier?.kind === "story")
    void useDeliveryDossier.getState().openStory(dossier.project, dossier.storyId, dossier.source || undefined);
  else if (dossier?.kind === "phase")
    void useDeliveryDossier.getState().openPhase(dossier.project, dossier.phase);
  if (terminal?.targetId) useDeliveryTerminal.getState().open(terminal);
  if (mission && !useMissionControl.getState().open) useMissionControl.getState().toggle();
  if (session) useSteering.getState().openSession(session);
  if (trust) useTrustWindow.getState().setOpen(true);
  const desk = useDesk.getState();
  if (inspector?.id) desk.openToolInspector(inspector.kind, inspector.id);
  if (schedule) desk.openScheduleCreate();
  if (ask) desk.openAsk();
  if (pendingEditor) rememberWindow("editor", pendingEditor); // kept until the read lands
  const drawerStore = useDrawers.getState();
  for (const drawer of Array.isArray(drawers) ? drawers : []) {
    if (drawer?.projectId) drawerStore.openDrawer(drawer.projectId, drawer.origin ?? null);
  }
  for (const info of Array.isArray(infos) ? infos : []) {
    if (info?.member?.ref && info.projectId) drawerStore.openInfo(info.member, info.projectId);
  }
}

/** After the first Desk read whose collections all answered: the editor
 * returns on its object, and a returned pullout (or editor) whose record is
 * gone is dropped. A collection that did not answer proves nothing, so the
 * check waits for the next read. */
function afterFirstRead(): void {
  if (pruned) return;
  const s = useDesk.getState();
  if (Object.values(s.status ?? {}).some((state) => state === "unreachable")) return;
  pruned = true;
  for (const id of restoredPullouts) {
    if (s.pullouts.some((p) => p.id === id) && !objectByRef(s.items, id)) s.closePullout(id);
  }
  const editor = pendingEditor;
  pendingEditor = null;
  if (!editor) return;
  if (objectByRef(s.items, editor)) s.openEditor(editor);
  else rememberWindow("editor", null);
}

/** Mounted by DeskApp once the Desk (not first value) owns the screen. */
export function ReturningWindows() {
  const updatedAt = useDesk((s) => s.updatedAt);
  useEffect(() => { restoreOnce(); }, []);
  useEffect(() => { if (updatedAt !== null) afterFirstRead(); }, [updatedAt]);
  return null;
}
