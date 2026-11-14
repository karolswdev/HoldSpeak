import { useState } from "react";
import {
  InspectorForm,
  PaneInspector,
  PreferencePane,
  StringGadget,
  type ListVerb,
  wireDayClock,
} from "../../../desk/surface";
import { openRef, refOpener } from "../../../desk/openObject";
import { openProjectRoom } from "../../../desk/shell";
import { useMemoryChanges } from "../../../desk/memoryChanges";
import { RoomList, type RoomEntry } from "../RoomList";
import { useRecallController } from "./useRecallController";
import { RECALL_FILTERS, type RecallFilter } from "./model";

export function MemorySnippet({ value }: { value: string }) {
  return (
    <>
      {value
        .split(/(<mark>.*?<\/mark>)/gi)
        .map((part, i) =>
          /^<mark>.*<\/mark>$/i.test(part) ? (
            <mark key={i}>{part.replace(/^<mark>|<\/mark>$/gi, "")}</mark>
          ) : (
            part
          ),
        )}
    </>
  );
}
export function RecallFace({ initialQuery = "" }: { initialQuery?: string }) {
  const ctrl = useRecallController(initialQuery);
  const held = useMemoryChanges(ctrl.reread);
  const [picked, setPicked] = useState<string | null>(null),
    [edit, setEdit] = useState(""),
    [value, setValue] = useState("");
  const result = ctrl.result;
  const decisions = [
    ...result.current,
    ...result.disputed,
    ...result.superseded,
  ];
  const decision = decisions.find((row) => row.id === picked);
  const owed = result.owed.find((row) => row.id === picked);
  const belief = result.beliefs.find((row) => row.id === picked);
  const project = decision?.project || owed?.project || belief?.project;
  const source = decision?.source || owed?.source;
  const rows: RoomEntry[] = [
    ...decisions.map((row) => ({
      id: row.id,
      name: row.text,
      kind: "decision",
      kindWord: "Decision",
      cells: { state: row.state },
      when: row.decided_at || "",
      facts: [
        { label: "What it says", value: row.rationale },
        { label: "Support", value: row.support },
        { label: "Acceptance", value: row.acceptance },
        { label: "Successor", value: row.successor?.text },
        {
          label: "Reason",
          value: row.dispute_reason || row.supersession_reason,
        },
        { label: "Source", value: row.source?.title },
      ],
      open: refOpener(row.ref) ?? undefined,
    })),
    ...result.owed.map((row) => ({
      id: row.id,
      name: row.text,
      kind: "action",
      kindWord: "Commitment",
      cells: { state: row.status },
      facts: [
        { label: "Owner", value: row.owner || undefined },
        { label: "Due", value: row.due_at || undefined },
        { label: "Source", value: row.source?.title },
      ],
      open: refOpener(row.ref) ?? undefined,
    })),
    ...result.beliefs
      .filter((row) => !held(row.evidence.map((evidence) => evidence.ref)))
      .map((row) => ({
        id: row.id,
        name: row.text,
        kind: "memory",
        kindWord: "Belief",
        cells: { state: row.state },
        facts: [
          { label: "Sources", value: row.source_count },
          { label: "Seen", value: row.seen },
          ...row.evidence.map((evidence, i) => ({
            key: `evidence:${i}`,
            label: evidence.against ? "Against" : "Evidence",
            value: evidence.token,
          })),
          ...row.history.map((history, i) => ({
            key: `history:${i}`,
            label: wireDayClock(history.at),
            value: `${history.text} · ${history.reason}`,
          })),
        ],
      })),
    ...[...result.meetings, ...result.briefs, ...result.also].map((row, i) => ({
      id: `${row.source_ref}:${i}`,
      name: row.title,
      kind: row.kind,
      kindWord: row.kind.replaceAll("_", " "),
      when: row.occurred_at,
      facts: [
        { label: "What it says", value: <MemorySnippet value={row.snippet} /> },
        {
          label: "Related to",
          value: row.relationship
            ? `${row.relationship.replaceAll("_", " ")} · ${row.related_to}`
            : row.related_to,
        },
      ],
      open: refOpener(row.source_ref) ?? undefined,
    })),
  ];
  const verbs: ListVerb[] = [
    {
      id: "search",
      label: "Search",
      enabled: () => ctrl.status !== "searching",
      run: () => {
        void ctrl.search();
      },
    },
    {
      id: "carry",
      label: decision?.carried ? "Carried" : "Carry into brief",
      enabled: () =>
        Boolean(
          decision && decision.state === "current" && !decision.carried,
        ) && !ctrl.busy,
      run: () => {
        if (decision)
          void ctrl.carry(decision.id, decision.project?.id ?? null);
      },
    },
    {
      id: "source",
      label: "Open source",
      enabled: () => Boolean(source),
      run: () => {
        if (source) openRef(`meeting:${source.meeting_id}`);
      },
    },
    {
      id: "successor",
      label: "Open successor",
      enabled: () => Boolean(decision?.successor),
      run: () => {
        if (decision?.successor)
          openRef(`decision_record:${decision.successor.id}`);
      },
    },
    {
      id: "project",
      label: "Open project",
      enabled: () => Boolean(project),
      run: () => {
        if (project) openProjectRoom(project.id);
      },
    },
    {
      id: "owner",
      label: "Name an owner",
      enabled: () => Boolean(owed && !owed.owner),
      run: () => {
        setEdit("owner");
        setValue("");
      },
    },
    {
      id: "due",
      label: "Set a date",
      enabled: () => Boolean(owed && !owed.due_at),
      run: () => {
        setEdit("due");
        setValue("");
      },
    },
    {
      id: "done",
      label: "Done",
      enabled: () => Boolean(owed?.owner && owed.due_at) && !ctrl.busy,
      run: () => {
        if (owed) void ctrl.markDone(owed.action_item_id);
      },
    },
    ...(belief?.evidence ?? [])
      .filter((row) => row.opens)
      .map((row, i) => ({
        id: `evidence:${i}`,
        label: `Open ${row.token}`,
        run: () => openRef(row.ref),
      })),
  ];
  return (
    <PreferencePane label="Recall" testId="recall-results">
      <RoomList
        label={ctrl.result.recent ? "Recent on this desk" : "Memory"}
        rows={rows}
        selectedId={picked}
        onSelect={(id) => {
          setPicked(id);
          setEdit("");
        }}
        verbs={verbs}
        scopes={[{id:"kind", label:"Memory kind", kind:"cycle", value:ctrl.filter,
          options:RECALL_FILTERS, onChange:value => ctrl.setFilter(value as RecallFilter)}]}
        field={<StringGadget label="Search memory" value={ctrl.query} onChange={ctrl.setQuery}
          onKeyDown={event => {if (event.key === "Enter" && !event.nativeEvent.isComposing) {event.preventDefault(); void ctrl.search();}}} />}

        loading={ctrl.reading || ctrl.status === "searching"}
        error={ctrl.error}
        retry={() => {
          void ctrl.reread();
        }}
        empty={ctrl.result.recent ? "No recent work" : "Nothing matches"}
      >
        {edit && owed ? (
          <PaneInspector
            label={edit === "owner" ? "Name an owner" : "Set a date"}
          >
            <InspectorForm
              rows={[
                {
                  label: edit === "owner" ? "Owner" : "Due",
                  control: (
                    <StringGadget
                      label={edit === "owner" ? "Owner" : "Due"}
                      value={value}
                      onChange={setValue}
                    />
                  ),
                },
              ]}
              completion={{
                cancel: () => setEdit(""),
                primary: {
                  label: "Save",
                  busy: Boolean(ctrl.busy),
                  disabled: !value.trim(),
                  run: () => {
                    void (
                      edit === "owner"
                        ? ctrl.nameOwner(owed.action_item_id, value)
                        : ctrl.setDate(owed.action_item_id, value)
                    ).then((ok) => {
                      if (ok) setEdit("");
                    });
                  },
                },
              }}
            />
          </PaneInspector>
        ) : undefined}
      </RoomList>
    </PreferencePane>
  );
}
