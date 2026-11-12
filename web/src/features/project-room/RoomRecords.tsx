import { useState } from "react";
import {
  CycleGadget,
  LivePane,
  ReadingDocument,
  PaneActions,
  wireDayClock,
  type ListVerb,
} from "../../desk/surface";
import { refOpener } from "../../desk/openObject";
import { pageTitle, useStandingPagesRead } from "../../desk/standingPages";
import { useDesk } from "../../desk/store";
import { RoomList, type RoomEntry } from "./RoomList";
import { RoomFiledNotes } from "./core/Folds";
import type { FiledNoteRequest } from "./RoomFiledNotesSection";
import type { RoomSnapshot } from "./model";
import type { ProjectRoomController } from "./useProjectRoomController";
import { cadenceWords, savedWords } from "./core/Cadence";
import { refusalWord } from "../../desk/surface/egress";
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
  return (
    <Records
      key={view}
      view={view}
      room={room}
      ctrl={ctrl}
      onSelectItem={onSelectItem}
      itemIds={itemIds}
      onOpenUpdate={onOpenUpdate}
    />
  );
}
function Records({
  view,
  room,
  ctrl,
  onSelectItem,
  itemIds,
  onOpenUpdate,
}: {
  view: string;
  room: RoomSnapshot;
  ctrl: ProjectRoomController;
  onSelectItem(id: string): void;
  itemIds: string[];
  onOpenUpdate(id: string): Promise<boolean>;
}) {
  const [filter, setFilter] = useState("all");
  const [failedUpdate, setFailedUpdate] = useState<string | null>(null);
  const openUpdate = async (id: string) => {
    try {
      if (await onOpenUpdate(id)) setFailedUpdate(null);
      else setFailedUpdate(id);
    } catch {
      setFailedUpdate(id);
    }
  };
  let rows: RoomEntry[] = [];
  if (view === "history")
    rows = [
      ...(room.changes.state === "ok"
        ? room.changes.recent
            .filter((row) => filter === "all" || row.kind.startsWith(filter))
            .map((row) => ({
              id: row.id,
              name: row.label || kindToPhrase(row.kind),
              kind: row.itemType || "artifact",
              kindWord: row.kind.startsWith("github")
                ? "GitHub"
                : row.kind.startsWith("jira")
                  ? "Jira"
                  : "Room",
              when: row.occurredAt || "",
              facts: [
                { label: "From", value: row.targetRef },
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
  if (view === "brief" && room.updates.state === "ok")
    rows = room.updates.recent.map((row) => ({
      id: String(row.id),
      name: String(row.title || row.summary || "Project update"),
      kind: "artifact",
      kindWord: "Update",
      when: String(row.updated_at || row.created_at || ""),
      facts: [
        { label: "State", value: String(row.lifecycle || "") },
        {
          label: "What it says",
          value: String(row.body_md || row.summary || ""),
        },
      ],
      open: () => {
        void openUpdate(String(row.id));
      },
    }));
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
          : failedUpdate
            ? "Could not read the update · Nothing changed"
            : undefined
      }
      retry={() => {
        if (failedUpdate) void openUpdate(failedUpdate);
        else void ctrl.load();
      }}
      empty={view === "history" ? "No history yet" : "No records"}
    />
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
        open: () => setPicked(row.slug),
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
        <LivePane
          label={pageTitle(page)}
          well={
            <div
              className="surface-preference-pane"
              data-feedback-redact="true"
            >
              <ReadingDocument>
                {page.sentences.map((row) => row.text).join("\n\n")}
              </ReadingDocument>
            </div>
          }
          facts={[
            { label: "Built", value: wireDayClock(page.built_at) },
            { label: "State", value: page.stale ? "Sources changed" : "" },
          ]}
        />
      ) : undefined}
    </RoomList>
  );
}
