// Parked 2026-11-11: the Room uses the shared selection and inspector grammar.
// @ts-nocheck
// HS-169-03 — the Room rebuilt to the ratified canvas.
// Four questions: What needs me now? What am I watching? What changed
// since I last looked? What did we decide and what do I owe people?
// Two wings: ROOM · HISTORY. Ask well at the foot. No counters of zero,
// no REV, no raw field names, the name said once.
//
// The Room is a composition (2026-11-08): the window frame, the two wings,
// the postures' routing and the shared read and store wiring. Each section
// lives in ./core/<Section>.tsx; each posture in its own folder.
import { useCallback, useEffect, useRef, useState } from "react";
import { DotWord, StatusBar, SurfaceSection, SurfaceState } from "../../desk/surface";
import { Loading } from "../../desk/surface/kit";
import { useWindowTitle } from "../../desk/surface/title";
import { useOnDeskChanged } from "../../desk/useDeskChangedRefresh";
import { useEngine } from "../../desk/hooks/useEngine";
import {
  ROOM_AT_EVENT, ROOM_PROPOSAL_EVENT, ROOM_UPDATES_EVENT, ROOM_WRITE_EVENT, takeRoomAtRequest,
  takeRoomProposalRequest, takeRoomUpdatesRequest, takeRoomWriteRequest, type RoomPlace,
} from "../../desk/openObject";
import { Unreadable } from "../../desk/surface/send";
import { retryRoomLink, useRoomSendLink } from "../../desk/windowSend";
import { mergeReceipt, useAgentFlights, useAgentFlightsLive } from "../../desk/agentFlights";
import { FlightVerbs } from "../../desk/components/AgentFlight";
import { Button } from "../../components/signal/Signal";
import type { CoreProps } from "../../pages/cores/core-types";
import type { RoomReviewData } from "./model";
import { RoomReadsContext } from "./roomReads";
import { useProjectRoomController } from "./useProjectRoomController";
import { useReviewController } from "./review/useReviewController";
import { useUpdateController } from "./update/useUpdateController";
import { fetchUpdates } from "./update/api";
import { useStewardController } from "./steward/useStewardController";
import { usePrepareController } from "./prepare/usePrepareController";
import type { FiledNoteRequest } from "./RoomFiledNotesSection";
import { RecallFace } from "./recall/RecallFace";
import "./project-room.css";
import { formatTimeShort } from "./core/format";
import { HealthNotRead, RoomHead } from "./core/RoomHead";
import { NeedsYouSection } from "./core/NeedsYou";
import { ItemsSection, useRoomItems } from "./core/Plan";
import { SourcesSection } from "./core/Sources";
import { BriefSection } from "./core/Brief";
import { OpenSection } from "./core/Open";
import { cadenceItems } from "./core/Cadence";
import { HistoryWing, ReceiptsSection, historyEventsWords } from "./core/History";
import { useRoomAsk } from "./core/Ask";
import { ROOM_PROGRAM_CHANGE_KINDS, RoomFiledNotes, RoomFold } from "./core/Folds";
import { RoomSlot, useRoomReadsGate } from "./core/slots";
import { roomPosture } from "./core/Postures";

// Every name other modules and tests import from the Room core.
export { NudgeCard } from "./NudgeCard";
export { LifecycleChip, DecisionPromotionSlot, emblemFor, RowSprite, SourceGlyph } from "./core/rows";
export { sourcesWord, sentenceToken, kindToPhrase } from "./core/format";
export { nudgeCooldownToken } from "./core/NeedsYou";
export { useRoomAsk, RoomAskWell, type RoomAsk } from "./core/Ask";
export { historyEventsWords } from "./core/History";

/** PHILO-17 (phonepass, Astra r2): a Room window that changes Project (the
 *  window's scope) remounts its core, so every first-read flag and the gate
 *  start again for the new Project. */
export function ProjectRoomCore(props: CoreProps) {
  return <ProjectRoomCoreFor key={props.scope ?? ""} {...props} />;
}

function ProjectRoomCoreFor({ hero, scope, scopeLabel }: CoreProps) {
  const ctrl = useProjectRoomController(scope, scopeLabel);
  const [addingSources, setAddingSources] = useState(false);
  useAgentFlightsLive();
  // R1 (owner 2026-11-08): the Needs you rows open under the status line.
  const [needsOpen, setNeedsOpen] = useState(false);
  const agentFlights = useAgentFlights((s) => s.flights);
  const loading = ctrl.loadStatus === "loading";
  // A write in another window (a meeting filed, an update published, an
  // agent's write) shows in this Room with no reload.
  useOnDeskChanged(() => { void ctrl.load(true); }, ROOM_PROGRAM_CHANGE_KINDS);

  const reviewData: RoomReviewData | null =
    ctrl.room?.review.state === "ok"
      ? (ctrl.room.review as RoomReviewData & { state: "ok" })
      : null;

  const reviewCtrl = useReviewController(
    ctrl.projectId, reviewData, () => void ctrl.load(),
  );

  const projectUpdateAutomationId = ctrl.room?.updates.state === "ok"
    ? ctrl.room.updates.automation?.id
    : undefined;
  const updateCtrl = useUpdateController(
    ctrl.projectId, () => void ctrl.load(),
    projectUpdateAutomationId,
  );

  const stewardCtrl = useStewardController(
    ctrl.projectId, () => void ctrl.load(),
  );

  // PHILO-13-15 (C5): the Room link { projectId, updateId, destinationId }
  // from `Send to ▸`: the linked update opens in the Update posture (also
  // when the Room is open on another update), its well picked. A failed
  // latest-update read opens the SEND well with the failure and Retry (P8).
  const { openUpdate } = updateCtrl;
  const openLinkedUpdate = useCallback(async (updateId: string) => {
    if (!ctrl.projectId) return false;
    // A failed read rejects: the link shows the failure with Retry (windowSend.tsx).
    const u = (await fetchUpdates(ctrl.projectId)).find((x) => x.id === updateId);
    if (!u) return false;
    openUpdate(u);
    return true;
  }, [ctrl.projectId, openUpdate]);
  const sendFailed = useRoomSendLink(ctrl.projectId, openLinkedUpdate);

  // PHILO-13-14 (C4): the palette's `Draft update for <project>` opens this
  // Room in its Update posture, as the `Draft update` Button does.
  const { enterUpdates } = updateCtrl;
  useEffect(() => {
    const projectId = ctrl.projectId;
    if (!projectId) return;
    const take = () => { if (takeRoomUpdatesRequest(projectId)) void enterUpdates(); };
    take();
    window.addEventListener(ROOM_UPDATES_EVENT, take);
    return () => window.removeEventListener(ROOM_UPDATES_EVENT, take);
  }, [ctrl.projectId, enterUpdates]);
  // Betterment P4 (projects): the palette's and the Object menu's `Draft
  // update` press the head's own Draft update here, once the engine roster
  // is read (the head's Button waits for the same read).
  const writeEngine = useEngine("project.update_draft");
  const [writeAsked, setWriteAsked] = useState(false);
  useEffect(() => {
    const projectId = ctrl.projectId;
    if (!projectId) return;
    const take = () => { if (takeRoomWriteRequest(projectId)) setWriteAsked(true); };
    take();
    window.addEventListener(ROOM_WRITE_EVENT, take);
    return () => window.removeEventListener(ROOM_WRITE_EVENT, take);
  }, [ctrl.projectId]);
  const { write } = updateCtrl;
  useEffect(() => {
    if (!writeAsked || writeEngine.state === "unread") return;
    setWriteAsked(false);
    void write(writeEngine.state === "set");
  }, [writeAsked, writeEngine.state, write]);
  // PHILO-14 A2b: a proposal row elsewhere (Needs you) opens this Room with
  // that proposal selected in OPEN HERE. `seq` counts the requests, so the
  // same proposal asked for again is revealed again (A5b, Astra r1).
  const [proposalRequest, setProposalRequest] = useState({ id: "", seq: 0 });
  const [fileRequest, setFileRequest] = useState<FiledNoteRequest>(null);
  const fileSeq = useRef(0);
  const onFileRequestHandled = useCallback((seq: number) => {
    setFileRequest((current) => current?.seq === seq ? null : current);
  }, []);
  const selectedProposalId = proposalRequest.id;
  const sendFailure = sendFailed && ctrl.projectId ? (
    <div data-send="well" data-testid="send-well" data-doc={`project:${ctrl.projectId}`} role="group"
      aria-label="Send the latest update">
      <SurfaceSection label="SEND">
        <Unreadable what="LATEST UPDATE" testid="room-latest-unreadable"
          onRetry={() => retryRoomLink(ctrl.projectId as string)} />
      </SurfaceSection>
    </div>
  ) : null;

  // HS-200-41 — one controller, two faces: UNFINISHED sits in the body as a
  // section, the well stays sticky at the foot (F5).
  const askCtrl = useRoomAsk(ctrl.projectId, ctrl.projectName);
  const itemsRead = useRoomItems(ctrl.projectId ?? "", ctrl.room?.revision ?? 0);

  // HS-200-11 — the Prepare posture: one manual preparation path over the
  // Room's read sources, its carried decisions and its open commitments.
  const prepareCtrl = usePrepareController(ctrl.projectId, () => void ctrl.load());

  // PHILO-14 A5b (Astra r1 on #965): a proposal request REVEALS the
  // proposal, whatever the Room shows. Every posture (Review, Update,
  // Steward, Prepare) closes the way its own Close does, except Update,
  // which steps aside with no write, the Room goes to its ROOM wing (not
  // History), and the selected row scrolls into view.
  // Every posture steps aside the way its own Close does; the Update posture
  // NEVER writes (Muad'Dib's ruling on Astra r2): its text, kept draft and
  // failure stay; Draft update brings the editor back. `keepSteward`: the
  // Steward request.
  const leavePostures = (keepSteward = false) => {
    if (reviewCtrl.posture !== "off") reviewCtrl.exitReview();
    updateCtrl.stepAside();
    if (!keepSteward && stewardCtrl.posture !== "off") stewardCtrl.exitSteward();
    if (prepareCtrl.posture !== "off") prepareCtrl.exit();
  };
  const revealProposal = useRef<(id: string) => void>(() => undefined);
  revealProposal.current = (id: string) => {
    leavePostures();
    if (ctrl.view !== "room") ctrl.setView("room");
    setNeedsOpen(true);
    setProposalRequest((prev) => ({ id, seq: prev.seq + 1 }));
  };
  // Phase 16 (Astra r1 M3): the Room window's History and Steward verbs
  // (the drawer's FilterBar and Sources) REVEAL their place, as a proposal
  // request does: every other posture steps aside first (Update without a
  // write), then History shows its wing, or Steward its posture.
  const revealPlace = useRef<(place: RoomPlace) => void>(() => undefined);
  revealPlace.current = (place: RoomPlace) => {
    if (typeof place === "object" && place.kind === "file") {
      leavePostures();
      if (ctrl.view !== "room") ctrl.setView("room");
      setFileRequest({ ref: place.ref, seq: ++fileSeq.current });
      return;
    }
    if (place === "room") {
      leavePostures();
      if (ctrl.view !== "room") ctrl.setView("room");
      return;
    }
    if (place === "history") {
      leavePostures();
      if (ctrl.view !== "history") ctrl.setView("history");
      return;
    }
    leavePostures(true);
    if (ctrl.view !== "room") ctrl.setView("room");
    if (stewardCtrl.posture === "off") void stewardCtrl.enterSteward();
  };
  useEffect(() => {
    const projectId = ctrl.projectId;
    if (!projectId) return;
    const take = () => {
      const place = takeRoomAtRequest(projectId);
      if (place) revealPlace.current(place);
    };
    take();
    window.addEventListener(ROOM_AT_EVENT, take);
    return () => window.removeEventListener(ROOM_AT_EVENT, take);
  }, [ctrl.projectId]);
  useEffect(() => {
    const projectId = ctrl.projectId;
    if (!projectId) return;
    const take = () => {
      const proposal = takeRoomProposalRequest(projectId);
      if (proposal) revealProposal.current(proposal);
    };
    take();
    window.addEventListener(ROOM_PROPOSAL_EVENT, take);
    return () => window.removeEventListener(ROOM_PROPOSAL_EVENT, take);
  }, [ctrl.projectId]);
  const roomBodyRef = useRef<HTMLDivElement | null>(null);
  const [itemRequest, setItemRequest] = useState({ id: "", seq: 0 });
  const revealedItemSeq = useRef(0);
  const openHistoryItem = (id: string) => {
    if (!itemsRead.items?.some((item) => item.id === id)) return;
    ctrl.setView("room");
    setItemRequest((previous) => ({ id, seq: previous.seq + 1 }));
  };
  useEffect(() => {
    if (ctrl.view !== "room" || !itemRequest.seq || revealedItemSeq.current === itemRequest.seq) return;
    const row = Array.from(roomBodyRef.current?.querySelectorAll<HTMLElement>("[data-item-id]") ?? [])
      .find((node) => node.dataset.itemId === itemRequest.id);
    if (!row) return;
    revealedItemSeq.current = itemRequest.seq;
    row.scrollIntoView?.({ block: "center" });
    row.focus({ preventScroll: true });
  });
  // PHILO-17 (phonepass): the body is drawn when its sections' first reads
  // resolve, or at the cap (core/slots.tsx).
  const { reportRead, shown, place } = useRoomReadsGate(Boolean(ctrl.room));
  const extrasRead = ctrl.extrasStatus === "ready";
  const revealedSeq = useRef(0);
  // Once per request: when the row is drawn (the wing switch and a posture's
  // close render first), it scrolls into view; a later re-read never pulls
  // the owner back to it.
  useEffect(() => {
    if (!proposalRequest.seq || revealedSeq.current === proposalRequest.seq) return;
    // The selected row's line carries the testid and `aria-current`; the
    // `data-selected` mark is on its `li` (desk/surface/Surface.tsx
    // SurfaceLedgerRow), so the old `[data-testid][data-selected]` never matched.
    const row = roomBodyRef.current?.querySelector<HTMLElement>(
      "[data-testid=proposal-row][aria-current=true]",
    );
    if (!row) return;
    revealedSeq.current = proposalRequest.seq;
    row.scrollIntoView?.({ block: "center" });
  });

  const runtimeTitle =
    ctrl.loadStatus === "ready" && ctrl.projectName !== "Project"
      ? ctrl.projectName : null;
  useWindowTitle(runtimeTitle, [runtimeTitle]);

  const readPosted = useRef(false);
  useEffect(() => {
    if (ctrl.loadStatus === "ready" && ctrl.room && !readPosted.current) {
      readPosted.current = true;
      void ctrl.postRead();
    }
  }, [ctrl.loadStatus]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleRefresh = useCallback(() => {
    readPosted.current = false;
    void ctrl.load().then(() => void ctrl.postRead());
  }, [ctrl]); // eslint-disable-line react-hooks/exhaustive-deps

  const pendingCount = reviewData?.pendingCount ?? 0;

  // The unscoped surface is Desk memory: the recall face (HS-200-13,
  // posture 5) -- CURRENT / SUPERSEDED / OWED over one query, never a
  // dead empty state.
  // HS-200-11's `q:<sentence>` scope (`Find support` opens Desk memory WITH
  // the sentence, searched; counsel P1-5) reaches the recall face here.
  if (!ctrl.projectId)
    return <RecallFace initialQuery={scope?.startsWith("q:") ? scope.slice("q:".length).trim() : ""} />;

  // Posture routing: Review > Update > Steward > Prepare > Room
  const posture = roomPosture({
    hero, onRefresh: handleRefresh, sendFailure, reviewCtrl, updateCtrl, stewardCtrl, prepareCtrl,
    askCtrl, projectName: ctrl.projectName, onOpenRef: ctrl.openProjectRef,
  });
  if (posture) return posture;

  const sourceCount = ctrl.room?.sources.state === "ok"
    ? ctrl.room.sources.items.filter((x) => !x.suggested).length : 0;

  // W1 (2026-10-27): the History status bar is one line, `42 events ·
  // since Oct 1`; a failed read says so (never a quiet claim).
  const historyReceipt = ctrl.room?.changes.state === "ok"
    ? historyEventsWords(ctrl.room.changes.recent)
    : "History unavailable";
  // Conductor F2 (K6): a commitment an agent's merged PR closed names
  // itself on the receipt line (K4's follow-through: the PR, the close).
  const merged = mergeReceipt(agentFlights, ctrl.projectId);
  // Window grammar (2026-10-24): the foot is the kit StatusBar, in warm
  // sentence-case words with a lamp; the merged PR's Open PR (and its
  // egress chip) are the bar's verbs.
  const footerItems = ctrl.view !== "history" ? [
    merged ? {
      key: "merged",
      lamp: "ok" as const,
      testId: "room-merge-receipt",
      // PHILO-15 B51/B52: the PR by its own title and number (the item's
      // title only when the hub has not read the PR's yet).
      text: `${merged.pr?.title || merged.title} · PR #${merged.pr?.number ?? ""} merged ${formatTimeShort(merged.mergedAt ?? "")}`.trim(),
    } : null,
    // R1: when the update runs and with which engine, and the saved time.
    ...(ctrl.room ? cadenceItems(ctrl.room) : []),
  ] : [
    { key: "history", testId: "room-footer-receipt", text: historyReceipt },
  ];
  // Betterment P3: the Now wing has no READ · NEXT CHECK receipt and no
  // Refresh (the window refreshes itself on every desk change).

  return (
    <>
      {ctrl.room ? (
        <RoomReadsContext.Provider value={reportRead}>
        <div className="room-body" data-testid="room-body" ref={roomBodyRef}
          data-settling={shown ? undefined : "true"} aria-busy={shown ? undefined : true}>
          {shown ? null : <div className="room-settling-line"><Loading /></div>}
          {sendFailure}
          {ctrl.readError ? <div className="room-failure-title" title={ctrl.errorTitle || undefined}><SurfaceState error={ctrl.readError} onRetry={handleRefresh} /></div> : null}
          {ctrl.lastRead && !ctrl.readError ? (
            <div className="room-failure-title" data-testid="room-last-read">
              <SurfaceState error="Could not read the Project again · The last read stays · Refresh"
                onRetry={handleRefresh} retryLabel="Refresh" />
            </div>
          ) : null}
          {ctrl.view === "room" ? (
            <>
              {/* The mast (the language, 2026-11-08): the project, its facts,
                  Draft update and History; the spine; the Ask field. */}
              <div className="room-section-rise" style={{ animationDelay: "0ms" }}>
                <RoomHead
                  room={ctrl.room}
                  updateCtrl={updateCtrl}
                  ask={askCtrl}
                  pendingCount={pendingCount}
                  needsOpen={needsOpen}
                  onNeeds={() => setNeedsOpen((open) => !open)}
                  onHistory={() => ctrl.setView("history")}
                  quiet={addingSources}
                />
              </div>
              {ctrl.room.health.state === "degraded" ? <HealthNotRead onRetry={handleRefresh} /> : null}
              <RoomSlot id="needs" place={place("needs")} own={{ extras: extrasRead }} delay="40ms"
                empty={!needsOpen}>
                {needsOpen ? (
                  <NeedsYouSection
                    room={ctrl.room}
                    ctrl={ctrl}
                    reviewCtrl={reviewCtrl}
                    selectedProposalId={selectedProposalId}
                    pendingCount={pendingCount}
                  />
                ) : null}
              </RoomSlot>
              {/* The language, 2026-11-08 (the bold canvas RoomBold): What
                  changed and the folds on the left, What is open on the right
                  at 720 px of container width or more; one column under it. */}
              <div className="room-now" data-testid="room-now">
                <div className="room-now-cols">
                  <div className="room-now-left">
                    <RoomSlot id="brief" place={place("brief")} delay="50ms">
                      <BriefSection room={ctrl.room} updateCtrl={updateCtrl} />
                    </RoomSlot>
                    {/* Files and Sources side by side (stacked on the phone);
                        the Plan, when the Project has items, beside them. Keep
                        Files' place even if its read resolves after the cap. */}
                    <div className="room-folds room-folds-line" data-testid="room-folds">
                      <RoomSlot id="files" place={{ waiting: place("files").waiting }} delay="80ms">
                        <RoomFiledNotes projectId={ctrl.projectId} ctrl={ctrl} request={fileRequest}
                          onRequestHandled={onFileRequestHandled}
                          presentationReady={shown && !place("files").waiting} />
                      </RoomSlot>
                      <RoomSlot id="sources" place={place("sources")} own={{ extras: extrasRead }} delay="82ms">
                        <RoomFold title="Sources" token={sourceCount || undefined}
                          open={addingSources || ctrl.room.sources.state === "degraded" || undefined} testId="room-fold-sources">
                          <SourcesSection room={ctrl.room} onReload={() => ctrl.load()} stewardCtrl={stewardCtrl} ctrl={ctrl} onAdding={setAddingSources} />
                        </RoomFold>
                      </RoomSlot>
                      <RoomSlot id="items" place={place("items")} delay="85ms" data-section="items">
                        <RoomFold title="Plan" token={itemsRead.items?.length || undefined} testId="room-fold-plan">
                          <ItemsSection read={itemsRead} />
                        </RoomFold>
                      </RoomSlot>
                    </div>
                  </div>
                  <div className="room-now-right">
                    <RoomSlot id="open" place={place("open")} delay="60ms">
                      <OpenSection room={ctrl.room} projectId={ctrl.projectId} nudges={ctrl.nudges}
                        onReload={() => void ctrl.load()} onRefresh={handleRefresh} />
                    </RoomSlot>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <>
              <HistoryWing room={ctrl.room}
                itemIds={itemsRead.items?.map((item) => item.id) ?? []} onOpenItem={openHistoryItem} onRetry={handleRefresh}
                onPrepare={() => prepareCtrl.enterPrepare()} />
              {/* PHILO-17 U31: the writes are what happened: History holds
                  them, folded under the stream (PHILO-17 refit). */}
              <div className="room-folds room-history-folds">
                <RoomFold title="Writes" token={ctrl.room.receipts.state === "ok" ? ctrl.room.receipts.items.length || undefined : undefined} testId="room-fold-writes">
                  <ReceiptsSection room={ctrl.room} />
                </RoomFold>
              </div>
            </>
          )}
        </div>
        </RoomReadsContext.Provider>
      ) : loading ? (
        <Loading data-testid="room-loading" />
      ) : ctrl.error ? (
        // PHILO-13-04 ledger, paid in B1: a plain failure name and Try again,
        // never the hub's own text. W6-G words: one sans sentence, the reason
        // in the hover title only.
        <div className="room-error" role="alert" data-testid="room-load-failed" title={ctrl.errorTitle || undefined}>
          <DotWord tone="fail">{ctrl.error}</DotWord>
          <Button dense variant="primary" onClick={handleRefresh} data-testid="room-load-retry">Try again</Button>
        </div>
      ) : null}
      {footerItems ? (
        <StatusBar
          data-testid="room-status"
          items={footerItems}
          verbs={ctrl.view !== "history" && merged ? (
            <FlightVerbs flight={merged} title={merged.pr?.title || merged.title} />
          ) : undefined}
        />
      ) : null}
    </>
  );
}