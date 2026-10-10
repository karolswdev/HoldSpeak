// The Desk route — the web app's front door (HS-73-02).
//
// React + Vite in the one Web tree. Full-bleed: the world owns the viewport;
// chrome is the floating
// minimal cluster (DeskChrome); a fresh desk shows the guiding empty state.
// PHILO-17 (owner 2026-10-10, "Yes, everything must become one desk"): the
// Screen (ChairHome) is the one desk. The spatial Floor, its list view, its
// atmosphere and its file drop are parked in desk/_parked/floor/.
import { lazy, Suspense, useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../components/signal/Signal";
import { useDesk } from "./store";
import { DeskReceiptRow } from "./components/DeskReceiptRow";
import { useCompactViewport } from "./useCompactViewport";
import { ChairHome } from "./chair"; import { ReturningWindows } from "./returningWindows"; // PHILO-13-07 (B2)
import { DeskChrome } from "./components/DeskChrome";
import { RecordOrb } from "./components/RecordOrb";
import { useChatImport } from "./hooks/useChatImport";
import { MissionControlConveyor } from "./components/MissionControlConveyor";
import { SessionPullout, PanePicker } from "./components/SessionPullout";
import { LaneWindow } from "./lane/LaneWindow";
import { DeliveryBoard } from "./components/DeliveryBoard";
import { DeliveryDossierWindow } from "./components/DeliveryDossierWindow";
import { DeliveryTerminalWindow } from "./components/DeliveryTerminalWindow";
import { NewWorkbenchChooser } from "./components/NewWorkbenchChooser";
import { ScheduleCreateWindow } from "./components/ScheduleCreateWindow";
import { AttentionDrawer } from "./components/AttentionDrawer";
import { AskPanel } from "./components/AskPanel";
import { HandSheet } from "./components/HandSheet";
import { DragLayer } from "./hand";
import { DeskToolInspector } from "./components/DeskToolInspector";
import { Dock, Expose, SnapGhost, Switcher } from "./components/DeskWindow";
import { CompositorLayer } from "./compositor/CompositorLayer";
import { SurfaceWindows } from "./components/SurfaceWindows";
import { TrustWindow } from "./components/TrustWindow";
import { InlineEditor } from "./components/InlineEditor";
import { Pullout } from "./components/Pullout";
import { ApplicationBoundary } from "./components/ApplicationBoundary";
import { objectByRef } from "./world";
import { useProjections } from "./projections";
import { takeFirstValueNoteOpen } from "./firstValue";
import { useSettleState } from "./settleState";
import { DeskDeleteHost } from "./deleteReceipt";
import { DrawerWindows } from "./drawer";
import { ConductorWindows } from "./conductor";
import "./desk.css";

// Object-specific heavyweight windows cross an actual user-open boundary
// before their code enters the Desk runtime.
const RoadmapWindow = lazy(() =>
  import("./components/RoadmapWindow").then((module) => ({
    default: module.RoadmapWindow,
  })),
);
const RepoWindow = lazy(() =>
  import("./components/RepoWindow").then((module) => ({
    default: module.RepoWindow,
  })),
);
const WorkbenchWindow = lazy(() =>
  import("./components/WorkbenchWindow").then((module) => ({
    default: module.WorkbenchWindow,
  })),
);

/** HS-148-02: the root attribute gate for the glyph column.
 * Reads from localStorage so story-03's rig can flip it;
 * valid values: "none" | "launcher" | "all"; default "launcher". */
function menuGlyphsVariant(): string {
  if (typeof window === "undefined") return "launcher";
  const raw = localStorage.getItem("hs:menu-glyphs");
  if (raw === "none" || raw === "launcher" || raw === "all") return raw;
  return "launcher";
}

/** PHILO-8-02 round three — the one delete listener and its receipt sit
 * ABOVE every DeskApp render branch (the setup-pending and setup-failure
 * branch returns early), so a failed refresh never unmounts it and never
 * commits a pending delete or takes its Undo away. */
export default function DeskApp() {
  return (
    <>
      <DeskDeleteHost />
      <DeskFaces />
    </>
  );
}

function DeskFaces() {
  const compact = useCompactViewport();
  const items = useDesk((s) => s.items);
  const updatedAt = useDesk((s) => s.updatedAt);
  const roadmapWindows = useDesk((s) => s.roadmapWindows);
  const repositoryWindows = useDesk((s) => s.repositoryWindows);
  const workbenchWindows = useDesk((s) => s.workbenchWindows);
  const setup = useDesk((s) => s.setup);
  const loading = useDesk((s) => s.loading);
  const editingId = useDesk((s) => s.editingId);
  const pullouts = useDesk((s) => s.pullouts);
  const askOpen = useDesk((s) => s.askOpen);
  const error = useDesk((s) => s.error);
  const { refresh } = useDesk.getState();
  const [refreshFailure, setRefreshFailure] = useState<string | null>(null);
  const settled = useSettleState((s) => s.settled);
  useEffect(() => () => useSettleState.getState().setSettled(false), []);

  const refreshDesk = useCallback(async () => {
    setRefreshFailure(null);
    try {
      await refresh();
      const open = new URLSearchParams(window.location.search).get("open");
      if (open) { useDesk.getState().openPullout(open); const url = new URL(window.location.href); url.searchParams.delete("open"); window.history.replaceState(window.history.state, "", url); } // B2 (Astra P2 #747): a link opens once; a reload never replays it over the restored editor
    } catch (caught) {
      setRefreshFailure(
        caught instanceof Error && caught.message
          ? caught.message
          : "HoldSpeak could not load your Desk.",
      );
    }
  }, [refresh]);

  // `updatedAt` changes only after the first combined desk/setup refresh has
  // settled. Keep the room quiet while that server-owned arrival choice is
  // unknown; later background refreshes preserve the normal Chair.
  // PHILO-13-13 C3-W: once a setup snapshot was read, a later read that
  // loses it (the hub went down) keeps the Desk and its frame. The Dock says
  // OFFLINE · AS OF and the failed read is named on the receipt line
  // (dataSlice `READ <collection>` + Retry); the error face never replaces
  // a Desk the owner already has (UX-CANON: errors never overlap the UI).
  const lastSetup = useRef(setup);
  if (setup) lastSetup.current = setup;
  const shownSetup = setup ?? lastSetup.current;
  const setupFailure =
    (refreshFailure
      ? `Your Desk is still unchanged. ${refreshFailure} Retry to check it again.`
      : null) ??
    (updatedAt !== null && shownSetup === null
      ? error || "Your Desk is still unchanged. HoldSpeak could not read setup status. Retry to check it again."
      : null);
  const setupPending = !setupFailure && updatedAt === null && (loading || shownSetup === null);
  const arrivalRequired = shownSetup?.arrival_required === true;
  useEffect(() => {
    if (arrivalRequired) useSettleState.getState().setSettled(false);
  }, [arrivalRequired]);
  const chairOpenCards = pullouts
    .map((pullout) => ({ ...pullout, object: objectByRef(items, pullout.id) }))
    .filter((pullout) => Boolean(pullout.object));

  useEffect(() => {
    // HS-140-02 stages Keep's note while first value owns HOME. Only the
    // server-authorized normal Desk reveal may consume and visibly open it.
    if (arrivalRequired) return;
    const ref = takeFirstValueNoteOpen();
    if (ref) useDesk.getState().openPullout(ref);
  }, [arrivalRequired]);

  useEffect(() => {
    void refreshDesk();
    void useProjections.getState().refresh(true);
  }, [refreshDesk]);

  // HS-151-07: one-time import of localStorage chat threads.
  useChatImport();

  const total = Object.values(items).reduce((n, l) => n + l.length, 0);
  const empty = updatedAt !== null && total === 0;

  if (setupPending || setupFailure) {
    return (
      <div
        className="desk-next desk-arrival-pending"
        id="desk-next"
        data-menu-glyphs={menuGlyphsVariant()}
        aria-busy="true"
        aria-label="Preparing HoldSpeak"
      >
        {setupFailure ? (
          <div role="alert">
            <p>{setupFailure}</p>
            <Button variant="primary" onClick={() => void refreshDesk()}>
              Retry
            </Button>
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <div className="desk-next" id="desk-next" data-menu-glyphs={menuGlyphsVariant()} data-settled={settled && !arrivalRequired ? "true" : undefined}>
      {!arrivalRequired && <DeskChrome showDailyStarts={!empty} />}
      {/* PHILO-3-01 — the owner's ruling: at phone width a standing write
          receipt is a full-width row between the bar and the work. */}
      {!arrivalRequired && compact && <DeskReceiptRow />}
      {/* PHILO-17: the Screen is the one desk; a stored "floor" loads it. */}
      <ChairHome arrivalRequired={arrivalRequired} />
      {/* The Chair's primary Ask AI verb opens the one Ask panel. */}
      {!arrivalRequired && askOpen && <AskPanel />}
      {/* Hand to agent (Conductor K3): the launch sheet, the Ask AI posture, on every face. */}
      {!arrivalRequired && <HandSheet />}
      {/* PHILO-14 C3: the drag's ghost and dotted path, over every window. */}
      {!arrivalRequired && <DragLayer />}
      {/* HS-135-13: the InlineEditor ("New Agent" from a Workbench sets
          editingId; this renders the editor). */}
      {!arrivalRequired && editingId && (() => {
        const o = objectByRef(items, editingId);
        return o ? <InlineEditor key={o.id} o={o} u={{ x: 0.5, y: 0.4 }} /> : null;
      })()}
      {/* The object windows (pullouts), and the first-value note staged
          before reveal. */}
      {!arrivalRequired && chairOpenCards.map((pullout) => (
        <Pullout key={pullout.id} o={pullout.object!} pulloutId={pullout.id} origin={pullout.origin} />
      ))}
      {/* PersonaChat retired by HS-151-07; threads pullout is the one chat surface. */}
      {!arrivalRequired && <><ReturningWindows /* PHILO-13-07 (B2): the other families return once */ /><DeskToolInspector /></>}
      {!arrivalRequired && <MissionControlConveyor />}
      {!arrivalRequired && <DeliveryBoard />}
      {!arrivalRequired && <DeliveryDossierWindow />}
      {!arrivalRequired && <DeliveryTerminalWindow />}
      {!arrivalRequired && roadmapWindows.map((roadmap) => (
        <ApplicationBoundary key={roadmap.slug} label="Roadmap">
          <Suspense fallback={null}>
              <RoadmapWindow slug={roadmap.slug} origin={roadmap.origin} />
          </Suspense>
        </ApplicationBoundary>
      ))}
      {!arrivalRequired && repositoryWindows.map((repository) => (
        <ApplicationBoundary key={repository.id} label="Repository">
          <Suspense fallback={null}>
              <RepoWindow repositoryId={repository.id} origin={repository.origin} />
          </Suspense>
        </ApplicationBoundary>
      ))}
      {!arrivalRequired && workbenchWindows.map((wb) => (
        <ApplicationBoundary key={wb.id} label="Workbench">
          <Suspense fallback={null}>
              <WorkbenchWindow workbenchId={wb.id} origin={wb.origin} />
          </Suspense>
        </ApplicationBoundary>
      ))}
      {!arrivalRequired && <NewWorkbenchChooser />}
      {!arrivalRequired && <ScheduleCreateWindow />}
      {!arrivalRequired && <PanePicker />}
      {!arrivalRequired && <SessionPullout />}
      {/* PHILO-14 A2: a Project opens as a drawer; Get Info is its own window. */}
      {!arrivalRequired && <DrawerWindows />}
      {!arrivalRequired && <ConductorWindows />}
      {!arrivalRequired && <LaneWindow />}
      {!arrivalRequired && <AttentionDrawer />}
      {/* Recovery remains direct and in-place: FirstWords opens Setup through
          this existing surface registry without restoring the whole Desk. */}
      <SurfaceWindows
        key={arrivalRequired ? "first-value-recovery" : "desk"}
        firstValueRecoveryOnly={arrivalRequired}
      />
      {!arrivalRequired && <TrustWindow />}
      {!arrivalRequired && <Dock center={<RecordOrb />} />}
      {!arrivalRequired && <SnapGhost />}
      {/* PHILO-16: the compositor (Esc back, stage follows, the dividers). */}
      {!arrivalRequired && <CompositorLayer />}
      {!arrivalRequired && <Expose />}
      {!arrivalRequired && <Switcher />}
    </div>
  );
}
