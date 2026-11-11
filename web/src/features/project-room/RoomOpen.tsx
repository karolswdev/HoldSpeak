import { useState, type ReactNode } from "react";
import {
  InspectorForm,
  PreferenceWell,
  InspectorBody,
  InspectorActions,
  wireDayClock,
  ListView,
  ReadingDocument,
  InspectorQuestion,
  PaneInspector,
  PadGadget,
  StringGadget,
  LivePane,
  Material,
  SurfaceState,
  type ListVerb,
} from "../../desk/surface";
import { openRef, openDecisionRecord, refOpener } from "../../desk/openObject";
import { PaneViewContext } from "../../desk/surface/patterns/PaneViews";
import { useDesk } from "../../desk/store";
import type { ProjectRoomController } from "./useProjectRoomController";
import type { RoomSnapshot, RoomNeedsYouItem } from "./model";
import type { RoomAsk } from "./core/Ask";
import { RoomList, type RoomEntry } from "./RoomList";
import { GenericNudgeCard, NudgeCard } from "./NudgeCard";
import { needsYouWhyWords, whyFaceWords } from "./model";
import {
  useAgentFlights,
  flightForItem,
  flightLabel,
  isInFlight,
} from "../../desk/agentFlights";
import { openCoderSession } from "../../desk/shell";
import * as api from "./api";
import { handOriginOfRow, openHand } from "../../desk/agentHand";
import {
  runAsProgram,
  runAsProgramRefusal,
} from "../../desk/programs/RunAsProgram";

const needsId = (row: RoomNeedsYouItem, index: number) =>
  row.itemId
    ? `item:${row.itemId}`
    : row.proposalId
      ? `proposal:${row.proposalId}`
      : `need:${row.actionItemId || row.entityId || row.meetingId || row.relationshipId || row.url || row.watchId || index}`;

export function roomOpenEntries(
  room: RoomSnapshot,
  proposals: ProjectRoomController["proposals"],
  items: RoomEntry[],
  openNeed: (row: RoomNeedsYouItem) => void = () => {},
  setEdit: (id: string) => void = () => {},
): RoomEntry[] {
  const needs = room.needsYou.state === "ok" ? room.needsYou.items : [];
  const rows: RoomEntry[] = [
    ...needs.map((row, index): RoomEntry => ({
      id: needsId(row, index),
      name: row.title,
      kind: row.proposalKind === "decision" ? "decision" : "action",
      kindWord: row.itemId
        ? "Plan item"
        : row.proposalId
          ? "Question"
          : row.direction === "theirs"
            ? "Task"
            : "Question",
      state: {
        label:
          row.direction === "theirs"
            ? `Waits on ${row.owner || row.ownerHint || "others"}`
            : "Waits on you",
        tone: "warn",
      },
      when: wireDayClock(row.since),
      facts: [
        { label: "From", value: row.meetingTitle || row.source },
        { label: "What it says", value: row.originalText || row.title },
        { label: "Reason", value: whyFaceWords(needsYouWhyWords(row)) },
        { label: "Owner", value: row.owner || row.ownerHint },
        { label: "Due", value: row.dueAt || row.dueHint },
      ],
      open: () => openNeed(row),
    })),
    ...(room.now?.state === "ok"
      ? room.now.risks.map((row, i) => ({
          id: row.ref?.replace(/^project_item:/, "item:") || `risk:${i}`,
          name: row.text,
          kind: "risk",
          kindWord: "Risk",
          cells: { state: row.token },
          facts: [
            { label: "From", value: row.source },
            { label: "What it says", value: row.text },
          ],
          open: refOpener(row.ref) ?? undefined,
        }))
      : []),
    ...(room.commitments.state === "ok"
      ? room.commitments.items
          .filter(
            (row) =>
              !needs.some((need) => need.actionItemId === row.actionItemId),
          )
          .map((row) => ({
            id: `commitment:${row.id}`,
            name: row.text,
            kind: "action",
            kindWord: "Task",
            facts: [
              { label: "Owner", value: row.owner },
              { label: "Due", value: row.dueAt },
            ],
            open: row.actionItemId
              ? (refOpener(`action_item:${row.actionItemId}`) ?? undefined)
              : undefined,
          }))
      : []),
    ...items
      .filter(
        (row) =>
          ![
            "closed",
            "resolved",
            "done",
            "retired",
            "mitigated",
            "reached",
            "dropped",
          ].includes(String(row.cells?.state).toLowerCase()),
      )
      .map((row) => ({ ...row, id: `item:${row.id}` })),
    ...(room.decisions.state === "ok"
      ? room.decisions.items
          .filter(
            (row) =>
              row.kind !== "action" ||
              (!row.done &&
                !(
                  room.commitments.state === "ok" &&
                  room.commitments.items.some(
                    (item) => item.id === row.commitmentId,
                  )
                )),
          )
          .map((row) => ({
            id: `decision:${row.id}`,
            name: row.text,
            kind: row.kind === "action" ? "action" : "decision",
            kindWord: row.kind === "action" ? "Task" : "Decision",
            when: wireDayClock(row.at),
            cells: { state: "Decided" },
            facts: [
              { label: "From", value: row.meetingTitle || row.source },
              { label: "What it says", value: row.text },
              { label: "Was", value: row.was?.text },
            ],
            open: () => openDecisionRecord(row.id),
          }))
      : []),
    ...(room.programs?.state === "ok"
      ? room.programs.programs.map((row) => ({
          id: `program:${row.id}`,
          name: row.title,
          kind: "program",
          kindWord: "Program",
          cells: { state: row.state_word },
          facts: [
            { label: "From", value: "Programs" },
            { label: "Steps", value: `${row.done} of ${row.total}` },
          ],
          open: () => openRef(`program:${row.id}`),
        }))
      : []),
  ];
  // A proposal can arrive on the full proposals read before the Room projection.
  for (const proposal of proposals)
    if (
      proposal.state === "proposed" &&
      !rows.some((row) => row.id === `proposal:${proposal.id}`)
    )
      rows.unshift({
        id: `proposal:${proposal.id}`,
        name: proposal.text,
        kind: proposal.kind,
        kindWord: "Question",
        cells: { state: "Waits on you" },
        facts: [{ label: "What it says", value: proposal.text }],
        open: () => setEdit(proposal.id),
      });
  return [...new Map(rows.map((row) => [row.id, row])).values()];
}

export function RoomOpen({
  room,
  ctrl,
  items,
  actions,
  field,
  selected,
  onSelect,
  onReview,
  ask,
}: {
  room: RoomSnapshot;
  ctrl: ProjectRoomController;
  items: RoomEntry[];
  actions: ListVerb[];
  field: ReactNode;
  selected: string | null;
  onSelect(id: string): void;
  onReview(): void;
  ask: RoomAsk;
}) {
  const flights = useAgentFlights((state) => state.flights);
  const [edit, setEdit] = useState<string | null>(null),
    [question, setQuestion] = useState<string | null>(null);
  const [nudgeStates, setNudgeStates] = useState<
    Record<string, import("./model").NudgeLocal>
  >({});
  const [failure, setFailure] = useState("");
  const [nudge, setNudge] = useState<string | null>(null);
  const needs = room.needsYou.state === "ok" ? room.needsYou.items : [];
  const openNeed = (row: RoomNeedsYouItem) => {
    if (row.proposalId) {
      setEdit(row.proposalId);
      return;
    }
    if (row.source === "delta") {
      onReview();
      return;
    }
    if (row.actionItemId) {
      openRef(`action:${row.actionItemId}`);
      return;
    }
    if (row.relationshipId) {
      useDesk
        .getState()
        .openSurfaceWindow("open-people", `person:${row.relationshipId}`);
      return;
    }
    if (row.meetingId) {
      openRef(`meeting:${row.meetingId}`);
      return;
    }
    if (row.url && /^https?:\/\//.test(row.url))
      window.open(row.url, "_blank", "noopener");
  };
  const rows = roomOpenEntries(
    room,
    ctrl.proposals,
    items,
    openNeed,
    setEdit,
  ).map((row) => {
    const need = needs.find((item, index) => needsId(item, index) === row.id);
    const flight = need ? flightForItem(flights, need) : null;
    return flight && flightLabel(flight)
      ? { ...row, detail: flightLabel(flight) || undefined }
      : row;
  });
  const proposal = ctrl.proposals.find(
    (row) => `proposal:${row.id}` === selected,
  );
  const need = needs.find((row, index) => needsId(row, index) === selected);
  const flight = need ? flightForItem(flights, need) : null;
  const target = proposal
    ? `${proposal.id}:${proposal.text}:${proposal.ownerHint}:${proposal.dueHint}`
    : selected || "";
  const hand = need
    ? handOriginOfRow({ ...need, projectId: room.projectId })
    : null;
  const selectedItem = items.find((row) => `item:${row.id}` === selected);
  const runProposal = async (verb: "confirm" | "dismiss") => {
    if (!proposal) return;
    const result =
      verb === "confirm"
        ? await ctrl.handleConfirmProposal(proposal.id)
        : await ctrl.handleDismissProposal(proposal.id);
    if (result && "ok" in result && !result.ok) setFailure(result.error);
    else setQuestion(null);
  };
  const verbs: ListVerb[] = [
    ...actions,
    {
      id: "ask",
      label: "Ask",
      enabled: () => Boolean(ask.prompt.trim()) && !ask.busy,
      run: () => {
        void ask.ask();
      },
    },
    {
      id: "confirm",
      label: "Confirm",
      enabled: () => Boolean(proposal) && !ctrl.proposalBusy,
      run: () => {
        void runProposal("confirm");
      },
    },
    {
      id: "edit",
      label: "Edit",
      enabled: () => Boolean(proposal),
      run: () => setEdit(proposal!.id),
    },
    {
      id: "dismiss",
      label: "Dismiss",
      enabled: () => Boolean(proposal) && !ctrl.proposalBusy,
      run: () => setQuestion(target),
    },
    {
      id: "file",
      label: "File meeting",
      enabled: () => Boolean(need?.meetingId && need.kind === "meeting_match"),
      run: () => {
        if (need?.meetingId)
          void api
            .associateMeeting(room.projectId, need.meetingId)
            .then(() => ctrl.load())
            .catch(() =>
              setFailure(
                "Could not file the meeting · Nothing changed · Try again",
              ),
            );
      },
    },
    {
      id: "session",
      label: "Session",
      enabled: () => Boolean(flight?.sessionKey),
      run: () => {
        if (flight?.sessionKey) openCoderSession(flight.sessionKey);
      },
    },
    {
      id: "pr",
      label: "Open PR",
      title: flight?.pr?.url,
      enabled: () => Boolean(flight?.pr?.url),
      run: () => {
        if (flight?.pr?.url) window.open(flight.pr.url, "_blank", "noopener");
      },
    },
    {
      id: "hand",
      label: "Hand to an agent session",
      enabled: () => Boolean(hand) && !isInFlight(flight),
      run: () => {
        if (hand) openHand(hand);
      },
    },
    {
      id: "run-program",
      label: "Run as a program",
      enabled: () =>
        Boolean(need?.actionItemId || selectedItem) && !isInFlight(flight),
      run: () => {
        const origin = need?.actionItemId
          ? {
              kind: "action" as const,
              id: need.actionItemId,
              projectId: room.projectId,
            }
          : selectedItem
            ? {
                kind: "project_item" as const,
                id: selectedItem.id,
                title: selectedItem.name,
                goal: selectedItem.name,
                projectId: room.projectId,
              }
            : null;
        if (origin)
          void runAsProgram(origin).catch((cause) =>
            setFailure(runAsProgramRefusal(cause, origin.kind)),
          );
      },
    },
    {
      id: "nudge",
      label: "Nudge",
      enabled: () => Boolean(need?.nudge || need?.verb === "nudge"),
      run: () => setNudge(target),
    },
  ];
  let inspector: ReactNode;
  if (edit && proposal?.id === edit)
    inspector = (
      <ProposalEdit
        key={target}
        proposal={proposal}
        ctrl={ctrl}
        onClose={() => setEdit(null)}
      />
    );
  else if (question === target && proposal)
    inspector = (
      <InspectorQuestion
        actionId="remove"
        targetId={target}
        question={`Dismiss ${proposal.text}?`}
        keeps={["The meeting and its notes"]}
        cancel={() => setQuestion(null)}
        onDisarm={() => setQuestion(null)}
        verb={{
          label: "Dismiss",
          run: () => {
            void runProposal("dismiss");
          },
          busy: ctrl.proposalBusy === proposal.id,
        }}
      />
    );
  else if (nudge === target && need)
    inspector = need.nudge ? (
      <GenericNudgeCard nudge={need.nudge} />
    ) : (
      <NudgeCard
        key={target}
        local={nudgeStates[target]}
        onLocal={(next) =>
          setNudgeStates((previous) => ({ ...previous, [target]: next }))
        }
        needsYouItem={need}
        nudgeItem={ctrl.nudges.find((row) => row.pr_url === need.url)}
        person={
          room.health.state === "ok"
            ? room.health.people?.find(
                (person) => person.relationshipId === need.relationshipId,
              )
            : undefined
        }
        onReload={() => {
          void ctrl.load();
        }}
      />
    );
  else if (ask.result || ask.busy) inspector = <RoomAnswer ask={ask} />;
  return (
    <RoomList
      label="Open"
      rows={rows}
      selectedId={selected}
      onSelect={(id) => {
        onSelect(id);
        ask.clearResult();
        setEdit(null);
        setNudge(null);
        setQuestion(null);
      }}
      verbs={verbs}
      field={field}
      error={failure}
      empty="Nothing open"
      testId="room-open-list"
    >
      {inspector}
    </RoomList>
  );
}
function ProposalEdit({
  proposal,
  ctrl,
  onClose,
}: {
  proposal: ProjectRoomController["proposals"][number];
  ctrl: ProjectRoomController;
  onClose(): void;
}) {
  const [text, setText] = useState(proposal.text),
    [owner, setOwner] = useState(proposal.ownerHint || ""),
    [due, setDue] = useState(proposal.dueHint || ""),
    [error, setError] = useState("");
  return (
    <PaneInspector label="Edit proposal">
      <InspectorForm
        rows={[
          {
            label: "Text",
            control: (
              <div data-feedback-redact="true">
                <PadGadget label="Text" value={text} onChange={setText} />
              </div>
            ),
          },
          {
            label: "Owner",
            control: (
              <StringGadget label="Owner" value={owner} onChange={setOwner} />
            ),
          },
          {
            label: "Due",
            control: <StringGadget label="Due" value={due} onChange={setDue} />,
          },
          {
            label: "Was",
            control: (
              <span data-feedback-redact="true">
                {proposal.originalText || proposal.text}
              </span>
            ),
          },
        ]}
        notice={error ? <SurfaceState error={error} /> : undefined}
        completion={{
          cancel: onClose,
          primary: {
            label: "Save and confirm",
            disabled: !text.trim(),
            busy: ctrl.proposalBusy === proposal.id,
            run: () => {
              void ctrl
                .handleConfirmProposal(proposal.id, { text, owner, due })
                .then((result) => {
                  if (result.ok) onClose();
                  else setError(result.error);
                });
            },
          },
        }}
      />
    </PaneInspector>
  );
}

function RoomAnswer({ ask }: { ask: RoomAsk }) {
  const [picked, setPicked] = useState<string | null>(null);
  const answer = ask.result;
  const sources = answer?.lookedAt?.length
    ? answer.lookedAt.map((row) => ({ ref: row.ref, title: row.title }))
    : (answer?.contextIds ?? []).map((ref, index) => ({
        ref,
        title: answer?.contextTitles[index] || ref,
      }));
  const rows = [
    ...new Map(
      sources.map((row) => [
        row.ref,
        { id: row.ref, name: row.title, kind: "source" },
      ]),
    ).values(),
  ];
  return (
    <PaneInspector label="Answer">
      <InspectorBody>
        <PreferenceWell>
          {answer?.ok ? (
            <div data-feedback-redact="true">
              <ReadingDocument>{answer.output}</ReadingDocument>
            </div>
          ) : (
            <SurfaceState
              loading={ask.busy}
              error={answer?.output}
              onRetry={() => {
                void ask.ask();
              }}
            />
          )}
          {rows.length ? (
            <PaneViewContext.Provider value={null}>
              <ListView
                label="Answer sources"
                rows={rows}
                selection
                headerless
                selectedId={picked}
                onSelect={setPicked}
                onOpen={(id) => refOpener(id)?.()}
                defaultVerb="open-source"
                verbs={[
                  {
                    id: "open-source",
                    label: "Open source",
                    enabled: (row) => Boolean(row && refOpener(row.id)),
                    run: (row) => {
                      if (row) refOpener(row.id)?.();
                    },
                  },
                ]}
              />
            </PaneViewContext.Provider>
          ) : null}
        </PreferenceWell>
        {rows.length ? (
          <InspectorActions completion={{ done: ask.clearResult }} />
        ) : null}
      </InspectorBody>
    </PaneInspector>
  );
}
