import { useCallback, useEffect, useRef, useState } from "react";
import {
  PreferencePane,
  SegmentedTabs,
  PaneViews,
  StatusBar,
  StringGadget,
  SurfaceState,
} from "../../desk/surface";
import { useWindowTitle } from "../../desk/surface/title";
import { useWindowInterior } from "../../desk/surface/interior";
import {
  useOnDeskChanged,
  ROOM_CHANGE_KINDS,
} from "../../desk/useDeskChangedRefresh";
import { useEngine } from "../../desk/hooks/useEngine";
import { useAgentFlightsLive } from "../../desk/agentFlights";
import { useDesk } from "../../desk/store";
import {
  openRef,
  ROOM_AT_EVENT,
  ROOM_PROPOSAL_EVENT,
  ROOM_UPDATES_EVENT,
  ROOM_WRITE_EVENT,
  takeRoomAtRequest,
  takeRoomProposalRequest,
  takeRoomUpdatesRequest,
  takeRoomWriteRequest,
} from "../../desk/openObject";
import { useRoomSendLink, retryRoomLink } from "../../desk/windowSend";
import type { CoreProps } from "../../pages/cores/core-types";
import { useProjectRoomController } from "./useProjectRoomController";
import { useReviewController } from "./review/useReviewController";
import { useUpdateController } from "./update/useUpdateController";
import { useStewardController } from "./steward/useStewardController";
import { usePrepareController } from "./prepare/usePrepareController";
import { ReviewPosture } from "./review/ReviewPosture";
import { UpdatePosture } from "./update/UpdatePosture";
import { StewardPosture } from "./steward/StewardPosture";
import { PreparePosture } from "./prepare/PreparePosture";
import { RecallFace } from "./recall/RecallFace";
import { AddSourcesWell } from "./door/DoorCore";
import { RoomPeopleSection } from "./RoomPeopleSection";
import { RoomSources } from "./RoomSources";
import { RoomOpen, roomOpenEntries } from "./RoomOpen";
import { RoomRecords } from "./RoomRecords";
import { planItemWords, useRoomItems } from "./core/Plan";
import { useRoomAsk } from "./core/Ask";
import { RoomList, type RoomEntry } from "./RoomList";
import { stateLine, isMine, dayWords } from "./now/model";
import { fetchUpdates } from "./update/api";
import { keepPlace } from "../../desk/deskMemory";
import { NEW_PROGRAM_PLACE } from "../../desk/programs/newProgram";

export { NudgeCard } from "./NudgeCard";
export {
  LifecycleChip,
  DecisionPromotionSlot,
  emblemFor,
  RowSprite,
  SourceGlyph,
} from "./core/rows";
export { sourcesWord, sentenceToken, kindToPhrase } from "./core/format";
export { nudgeCooldownToken } from "./core/NeedsYou";
export { useRoomAsk, RoomAskWell, type RoomAsk } from "./core/Ask";
export { historyEventsWords } from "./core/History";

const TABS = [
  { id: "open", label: "Open" },
  { id: "plan", label: "Plan" },
  { id: "sources", label: "Sources" },
  { id: "updates", label: "Updates" },
];
const VIEWS = [
  { id: "now", label: "Now" },
  { id: "prepare", label: "Prepare" },
  { id: "review", label: "Review" },
  { id: "people", label: "People" },
  { id: "files", label: "Files" },
  { id: "history", label: "History" },
  { id: "pages", label: "Pages" },
  { id: "brief", label: "Brief" },
  { id: "recall", label: "Recall" },
  { id: "steward", label: "Steward" },
  { id: "cadence", label: "Cadence" },
];
export function ProjectRoomCore(props: CoreProps) {
  return <Room key={props.scope ?? ""} {...props} />;
}
function Room({ scope, scopeLabel }: CoreProps) {
  useWindowInterior("list");
  useAgentFlightsLive();
  const ctrl = useProjectRoomController(scope, scopeLabel);
  const refresh = useCallback(() => ctrl.load(true), [ctrl.load]);
  useOnDeskChanged(refresh, [...ROOM_CHANGE_KINDS, "program"]);
  const room = ctrl.room;
  const review = useReviewController(
    ctrl.projectId,
    room?.review.state === "ok" ? room.review : null,
    refresh,
  );
  const update = useUpdateController(
    ctrl.projectId,
    refresh,
    room?.updates.state === "ok" ? room.updates.automation?.id : undefined,
  );
  const steward = useStewardController(ctrl.projectId, refresh);
  const prepare = usePrepareController(ctrl.projectId, refresh);
  const items = useRoomItems(ctrl.projectId ?? "", room?.revision ?? 0);
  const ask = useRoomAsk(ctrl.projectId, ctrl.projectName, true);
  const engine = useEngine("project.update_draft");
  const [tab, setTab] = useState("open"),
    [view, setView] = useState("now");
  const [adding, setAdding] = useState(false),
    [selected, setSelected] = useState<string | null>(null);
  const [fileRequest, setFileRequest] =
    useState<import("./RoomFiledNotesSection").FiledNoteRequest>(null);
  const readPosted = useRef(false);
  const firstPaint = useRef(false);
  useWindowTitle(ctrl.loadStatus === "ready" ? ctrl.projectName : null, [
    ctrl.projectName,
    ctrl.loadStatus,
  ]);
  useEffect(() => {
    if (room && !readPosted.current) {
      readPosted.current = true;
      void ctrl.postRead();
    }
  }, [room, ctrl.postRead]);
  const changeView = (next: string) => {
    setView(next);
    setAdding(false);
    if (next === "prepare" && prepare.posture === "off")
      void prepare.enterPrepare(ask.prompt);
    if (next === "review" && review.posture === "off")
      void review.enterReview();
    if (next === "steward" && steward.posture === "off")
      void steward.enterSteward();
  };
  const draft = () => {
    setTab("updates");
    setView("now");
    void update.write(engine.state === "set");
  };
  const actions = [
    {
      id: "draft",
      label: "Draft update",
      testId: "updates-verb",
      enabled: () => !update.draftBusy && engine.state !== "unread",
      run: draft,
    },
    {
      id: "program",
      label: "New program",
      run: () => {
        keepPlace(NEW_PROGRAM_PLACE, JSON.stringify({ title: "" }));
        useDesk
          .getState()
          .openSurfaceWindow("open-programs", `project:${ctrl.projectId}`);
      },
    },
    {
      id: "source",
      label: "Add source",
      testId: "room-add-source",
      run: () => {
        setTab("sources");
        setView("now");
        setAdding(true);
      },
    },
  ];
  const linkedUpdate = useCallback(
    async (id: string) => {
      const found = (await fetchUpdates(ctrl.projectId)).find(
        (row) => row.id === id,
      );
      setTab("updates");
      setView("now");
      if (!found) return false;
      update.openUpdate(found);
      return true;
    },
    [ctrl.projectId, update.openUpdate],
  );
  const fileHandled = useCallback(() => setFileRequest(null), []);
  const sendFailed = useRoomSendLink(ctrl.projectId, linkedUpdate);
  const requestHandler = useRef(() => {});
  requestHandler.current = () => {
    const id = ctrl.projectId;
    if (!id) return;
    if (takeRoomUpdatesRequest(id)) {
      setTab("updates");
      setView("now");
      void update.enterUpdates();
    }
    if (takeRoomWriteRequest(id)) draft();
    const proposal = takeRoomProposalRequest(id);
    if (proposal) {
      setTab("open");
      setView("now");
      setSelected(`proposal:${proposal}`);
    }
    const place = takeRoomAtRequest(id);
    if (place) {
      setTab("open");
      if (typeof place === "object") {
        setFileRequest({ ref: place.ref, seq: Date.now() });
        setView("files");
      } else changeView(place === "room" ? "now" : place);
    }
  };
  useEffect(() => {
    requestHandler.current();
    const take = () => requestHandler.current();
    const names = [
      ROOM_AT_EVENT,
      ROOM_PROPOSAL_EVENT,
      ROOM_UPDATES_EVENT,
      ROOM_WRITE_EVENT,
    ];
    names.forEach((name) => window.addEventListener(name, take));
    return () =>
      names.forEach((name) => window.removeEventListener(name, take));
  }, [ctrl.projectId]);
  if (
    room &&
    ctrl.extrasStatus === "ready" &&
    (items.items !== null || items.failed)
  )
    firstPaint.current = true;
  if (!ctrl.projectId)
    return (
      <RecallFace
        initialQuery={scope?.startsWith("q:") ? scope.slice(2) : ""}
      />
    );
  if (!room || !firstPaint.current)
    return (
      <PreferencePane label="The Room">
        <SurfaceState
          loading={
            ctrl.loadStatus === "loading" ||
            Boolean(room && !firstPaint.current)
          }
          error={ctrl.readError || ctrl.error || undefined}
          onRetry={refresh}
        />
      </PreferencePane>
    );
  const field = (
    <StringGadget
      label="Ask this project"
      placeholder="Ask this project"
      value={ask.prompt}
      onChange={ask.setPrompt}
      inputRef={ask.inputRef}
      onKeyDown={(event) => {
        if (event.key === "Enter" && !event.nativeEvent.isComposing) {
          event.preventDefault();
          setTab("open");
          setView("now");
          void ask.ask();
        }
      }}
    />
  );
  const planRows: RoomEntry[] = (items.items ?? []).map((item) => ({
    id: item.id,
    open:
      tab !== "plan"
        ? () => {
            setTab("plan");
            setView("now");
            setSelected(item.id);
          }
        : undefined,
    name: item.title,
    kind: item.item_type,
    kindWord: item.item_type === "risk" ? "Risk" : "Plan item",
    cells: {
      state: planItemWords(item),
      owner: item.owner || "",
    },
    facts: [
      { label: "From", value: "Project plan" },
      { label: "What it says", value: item.summary || item.title },
      { label: "Due", value: item.due_at },
      ...planDetails(item.details_json),
    ],
  }));
  const openRows = roomOpenEntries(room, ctrl.proposals, planRows).length;
  const needs =
    (room.needsYou.state === "ok"
      ? room.needsYou.items.filter(isMine).length
      : 0) || (room.review.state === "ok" ? room.review.pendingCount : 0);
  const sources =
    room.sources.state === "ok"
      ? room.sources.items.filter((row) => !row.suggested).length
      : 0;
  const line = stateLine(
    room,
    room.sources.state === "ok" &&
      room.sources.items.some((row) => row.freshness === "stale"),
  );
  const failed =
    ctrl.readError ||
    ctrl.error ||
    (ctrl.lastRead ? "Could not read the project again · Last read stays" : "");
  let content;
  if (adding)
    content = (
      <AddSourcesWell
        projectId={ctrl.projectId}
        onAdded={() => {
          setAdding(false);
          refresh();
        }}
        onCancel={() => setAdding(false)}
      />
    );
  else if (view === "prepare")
    content = (
      <PreparePosture
        onClose={() => setView("now")}
        ctrl={prepare}
        projectName={ctrl.projectName}
        onOpenRef={ctrl.openProjectRef}
        onResultChange={(purpose) => {
          ask.setPrompt(purpose);
          setView("now");
        }}
      />
    );
  else if (view === "review")
    content = <ReviewPosture ctrl={review} onClose={() => setView("now")} />;
  else if (view === "steward")
    content = (
      <StewardPosture
        ctrl={steward}
        onOpenReview={(id) => {
          void review.enterReview(id);
          setView("review");
        }}
        onOpenUpdate={async (id) => {
          await linkedUpdate(id);
        }}
      />
    );
  else if (view === "people")
    content = <RoomPeopleSection projectId={ctrl.projectId} />;
  else if (view === "recall") content = <RecallFace />;
  else if (view !== "now")
    content = (
      <RoomRecords
        view={view}
        room={room}
        ctrl={ctrl}
        fileRequest={fileRequest}
        onFileHandled={fileHandled}
        itemIds={planRows.map((row) => row.id.replace(/^item:/, ""))}
        onOpenUpdate={linkedUpdate}
        onSelectItem={(id) => {
          setTab("plan");
          setView("now");
          setSelected(id);
        }}
      />
    );
  else if (tab === "updates")
    content = (
      <UpdatePosture ctrl={update} projectActions={actions} field={field} />
    );
  else if (tab === "sources")
    content = (
      <RoomSources
        room={room}
        ctrl={ctrl}
        verbs={actions}
        field={field}
        onReload={refresh}
      />
    );
  else if (tab === "plan")
    content = (
      <RoomList
        label="Plan"
        rows={planRows}
        selectedId={selected}
        onSelect={setSelected}
        columns={[
          { key: "name", word: "Plan item", minWidth: 220, priority: 10 },
          { key: "state", word: "State", minWidth: 130, priority: 9 },
          { key: "owner", word: "Owner", minWidth: 130, priority: 2 },
        ]}
        verbs={actions}
        field={field}
        error={
          items.failed
            ? "Could not read the plan · Nothing changed · Try again"
            : null
        }
        retry={items.retry}
        loading={!items.items && !items.failed}
        empty="No plan items"
      />
    );
  else
    content = (
      <RoomOpen
        room={room}
        ctrl={ctrl}
        items={planRows}
        actions={actions}
        field={field}
        selected={selected}
        onSelect={setSelected}
        onReview={() => changeView("review")}
        ask={ask}
      />
    );
  return (
    <PreferencePane
      label="The Room"
      testId="room-body"
      style={{ paddingTop: 8 }}
    >
      {failed ? <SurfaceState error={failed} onRetry={refresh} /> : null}
      {sendFailed ? (
        <SurfaceState
          error="Could not read the latest update · Nothing changed · Try again"
          onRetry={() => retryRoomLink(ctrl.projectId)}
        />
      ) : null}
      <SegmentedTabs
        label="Project lists"
        value={tab}
        tabs={TABS}
        onChange={(next) => {
          setTab(next);
          setView("now");
          setAdding(false);
          setSelected(null);
          if (next === "updates") void update.enterUpdates();
        }}
      >
        <PaneViews
          label="Project view"
          value={view}
          tabs={VIEWS}
          onChange={changeView}
        >
          {content}
        </PaneViews>
      </SegmentedTabs>
      <StatusBar
        items={[
          {
            key: "health",
            text: line.text.split(":")[0],
            lamp:
              line.tone === "danger" || line.tone === "warn"
                ? "fail"
                : undefined,
            priority: 10,
            testId: "room-headline",
          },
          needs
            ? {
                key: "needs",
                text: `${needs} waits on you`,
                lamp: "ask",
                priority: 10,
              }
            : null,
          openRows
            ? { key: "open", text: `${openRows} open`, priority: 3 }
            : null,
          sources
            ? { key: "sources", text: `${sources} sources`, priority: 2 }
            : null,
          room.now?.state === "ok" && room.now.lastUpdateAt
            ? {
                key: "update",
                text: `Last update ${dayWords(room.now.lastUpdateAt)}`,
                priority: 1,
              }
            : null,
          update.error
            ? { key: "update-error", text: update.error, lamp: "fail" }
            : null,
        ]}
      />
    </PreferencePane>
  );
}

function planDetails(raw: string | null) {
  if (!raw) return [];
  try {
    const details: unknown = JSON.parse(raw);
    if (details && typeof details === "object" && !Array.isArray(details))
      return Object.entries(details).map(([key, value]) => ({
        label: key
          .replaceAll("_", " ")
          .replace(/^./, (letter) => letter.toUpperCase()),
        value: typeof value === "string" ? value : JSON.stringify(value),
      }));
  } catch {
    /* The source can hold unstructured details. */
  }
  return [{ label: "Details", value: raw }];
}
