import { useEffect, useState } from "react";
import {
  CycleGadget,
  ObjectReader,
  ReadingDocument,
  PaneActions,
  SurfaceState,
  wireDayClock,
  type ListVerb,
} from "../../desk/surface";
import { refOpener } from "../../desk/openObject";
import { pageTitle, useStandingPagesRead } from "../../desk/standingPages";
import { useDesk } from "../../desk/store";
import { RoomList, roomReadingText, type RoomEntry } from "./RoomList";
import { RoomFiledNotes } from "./core/Folds";
import type { FiledNoteRequest } from "./RoomFiledNotesSection";
import type { RoomSnapshot } from "./model";
import type { ProjectRoomController } from "./useProjectRoomController";
import { cadenceWords, savedWords } from "./core/Cadence";
import { refusalWord } from "../../desk/surface/egress";
import { wireWords } from "../../desk/surface/words";
import { fetchUpdate } from "./update/api";
import { type ProjectUpdate } from "./update/model";
import { kindToPhrase } from "./core/format";

export function RoomRecords({
  view,
  room,
  ctrl,
  fileRequest,
  onFileHandled,
  onSelectItem,
  itemIds,
  onOpenUpdate,
}: {
  view: string;
  room: RoomSnapshot;
  ctrl: ProjectRoomController;
  fileRequest: FiledNoteRequest;
  onFileHandled(): void;
  onSelectItem(id: string): void;
  itemIds: string[];
  onOpenUpdate(id: string): Promise<boolean>;
}) {
  if (view === "files")
    return (
      <RoomFiledNotes
        projectId={room.projectId}
        ctrl={ctrl}
        request={fileRequest}
        onRequestHandled={onFileHandled}
        presentationReady
      />
    );
  if (view === "pages") return <RoomPages projectId={room.projectId} />;
  if (view === "brief")
    return <RoomBrief room={room} onOpenUpdate={onOpenUpdate} />;
  return (
    <Records
      key={view}
      view={view}
      room={room}
      ctrl={ctrl}
      onSelectItem={onSelectItem}
      itemIds={itemIds}
    />
  );
}
function Records({
  view,
  room,
  ctrl,
  onSelectItem,
  itemIds,
}: {
  view: string;
  room: RoomSnapshot;
  ctrl: ProjectRoomController;
  onSelectItem(id: string): void;
  itemIds: string[];
}) {
  const [filter, setFilter] = useState("all");
  let rows: RoomEntry[] = [];
  if (view === "history")
    rows = [
      ...(room.changes.state === "ok"
        ? room.changes.recent
            .filter((row) => filter === "all" || row.kind.startsWith(filter))
            .map((row) => ({
              id: row.id,
              name: row.subject || row.label || kindToPhrase(row.kind),
              detail: row.actionLabel,
              kind: row.itemType || "artifact",
              kindWord: row.kind.startsWith("github")
                ? "GitHub"
                : row.kind.startsWith("jira")
                  ? "Jira"
                  : "Room",
              when: row.occurredAt || "",
              facts: [
                {
                  label: "From",
                  value:
                    row.targetRef === `project:${room.projectId}`
                      ? room.project.name
                      : undefined,
                },
                {
                  label: "What it says",
                  value: row.label || kindToPhrase(row.kind),
                },
              ],
              open:
                row.itemId && itemIds.includes(row.itemId)
                  ? () => onSelectItem(row.itemId!)
                  : row.targetRef
                    ? (refOpener(row.targetRef) ?? undefined)
                    : undefined,
            }))
        : []),
      ...(filter === "writes" && room.receipts.state === "ok"
        ? room.receipts.items.map((row) => ({
            id: `receipt:${row.id}`,
            name: row.title,
            kind: "artifact",
            kindWord: "Write",
            when: row.timestamp,
            cells: { state: row.outcome },
            facts: [
              { label: "Operation", value: row.op.replaceAll("_", " ") },
              {
                label: "Reason",
                value: row.reason ? refusalWord(row.reason) : "",
              },
              { label: "Origin", value: row.origin },
              { label: "Caller", value: row.caller },
            ],
          }))
        : []),
    ];
  if (
    view === "cadence" &&
    room.updates.state === "ok" &&
    room.updates.automation
  ) {
    const automation = room.updates.automation;
    rows = [
      {
        id: automation.id,
        name: automation.name,
        kind: "automation",
        facts: [
          { label: "Schedule", value: cadenceWords(room) },
          { label: "Saved", value: savedWords(room) },
          { label: "Instruction", value: automation.instruction },
        ],
        open: () => useDesk.getState().openWorkbenchWindow(automation.id),
      },
    ];
  }
  return (
    <RoomList
      label={
        view === "history"
          ? "History"
          : view === "cadence"
            ? "Cadence"
            : "Brief"
      }
      rows={rows}
      field={
        view === "history" ? (
          <CycleGadget
            label="Source"
            value={filter}
            onChange={setFilter}
            options={[
              { value: "all", label: "All" },
              { value: "github", label: "GitHub" },
              { value: "jira", label: "Jira" },
              { value: "writes", label: "Writes" },
            ]}
          />
        ) : undefined
      }
      error={
        view === "history" && room.changes.state === "degraded"
          ? "Could not read the history · Nothing changed"
          : undefined
      }
      retry={() => {
        void ctrl.load();
      }}
      empty={view === "history" ? "No history yet" : "No records"}
    />
  );
}
function RoomBrief({
  room,
  onOpenUpdate,
}: {
  room: RoomSnapshot;
  onOpenUpdate(id: string): Promise<boolean>;
}) {
  const latest =
    room.updates.state === "ok" ? room.updates.recent[0] : undefined;
  const id = latest ? String(latest.id) : "";
  const revision = latest
    ? `${latest.id}:${latest.draft_revision}:${latest.updated_at}:${latest.lifecycle}`
    : "";
  const [read, setRead] = useState<{
    id: string;
    revision: string;
    update?: ProjectUpdate;
    error?: string;
  }>();
  const [attempt, setAttempt] = useState(0);
  const [openFailed, setOpenFailed] = useState(false);
  const open = () => {
    setOpenFailed(false);
    void onOpenUpdate(id).then(
      (opened) => setOpenFailed(!opened),
      () => setOpenFailed(true),
    );
  };
  useEffect(() => {
    setOpenFailed(false);
    if (!id) return;
    let live = true;
    void fetchUpdate(id)
      .then((update) => {
        if (live) setRead({ id, revision, update });
      })
      .catch(() => {
        if (live)
          setRead({
            id,
            revision,
            error: "Could not read the brief · Nothing changed · Try again",
          });
      });
    return () => {
      live = false;
    };
  }, [id, revision, attempt]);
  const current =
    read?.id === id && read.revision === revision ? read : undefined;
  return (
    <RoomList
      label="Brief"
      reader
      rows={[]}
      verbs={[
        {
          id: "open-update",
          label: "Open update",
          enabled: () => Boolean(current?.update),
          run: open,
        },
      ]}
      empty="No brief"
      loading={Boolean(id) && !current}
    >
      {current?.update ? (
        <ObjectReader
          label="Brief"
          key={`${current.update.id}:${current.update.draftRevision}:${openFailed}`}
          facts={[
            { label: "State", value: wireWords(current.update.lifecycle) },
            { label: "Changed", value: wireDayClock(current.update.updatedAt) },
          ]}
        >
          {openFailed ? (
            <SurfaceState
              error="Could not open the update · The brief stays here · Try again"
              onRetry={open}
            />
          ) : null}
          <ReadingDocument>
            {roomReadingText(current.update.bodyMd)}
          </ReadingDocument>
        </ObjectReader>
      ) : current?.error ? (
        <SurfaceState
          error={current.error}
          onRetry={() => setAttempt((value) => value + 1)}
        />
      ) : undefined}
    </RoomList>
  );
}
function RoomPages({ projectId }: { projectId: string }) {
  const { pages } = useStandingPagesRead("project", projectId);
  const [picked, setPicked] = useState<string | null>(null);
  const [source, setSource] = useState("");
  const page = pages.find((row) => row.slug === picked);
  const refs = [
    ...new Map(
      (page?.sentences.flatMap((row) => row.refs) ?? []).map((ref) => [
        ref.ref,
        ref,
      ]),
    ).values(),
  ];
  const selectedRef = refs.find((ref) => ref.ref === source) ?? refs[0];
  const opener = selectedRef ? refOpener(selectedRef.ref) : null;
  const verbs: ListVerb[] = [
    {
      id: "source",
      label: "Open source",
      enabled: () => Boolean(opener),
      run: () => opener?.(),
    },
  ];
  return (
    <RoomList
      label="Pages"
      rows={pages.map((row) => ({
        id: row.slug,
        name: pageTitle(row),
        kind: "artifact",
        kindWord: "Page",
        when: wireDayClock(row.built_at),
        cells: { state: row.stale ? "Sources changed" : "" },
      }))}
      selectedId={picked}
      onSelect={(id) => {
        setPicked(id);
        setSource("");
      }}
      verbs={verbs}
      field={
        page && refs.length ? (
          <PaneActions>
            <CycleGadget
              roster
              label="Source"
              value={selectedRef?.ref ?? ""}
              onChange={setSource}
              options={refs.map((ref) => ({
                value: ref.ref,
                label: ref.token,
              }))}
            />
          </PaneActions>
        ) : undefined
      }
      empty="No pages"
    >
      {page ? (
        <ObjectReader
          key={page.slug}
          label={pageTitle(page)}
          facts={[
            { label: "Built", value: wireDayClock(page.built_at) },
            { label: "State", value: page.stale ? "Sources changed" : "" },
          ]}
        >
          <ReadingDocument>
            {page.sentences.map((row) => row.text).join("\n\n")}
          </ReadingDocument>
        </ObjectReader>
      ) : undefined}
    </RoomList>
  );
}
