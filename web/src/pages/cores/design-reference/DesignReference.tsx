import { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { DeskComposer } from "../../../desk/components/DeskComposer";
import { AskSourceFrame } from "../../../desk/components/AskSourceFrame";
import { RepositoryBrowserView } from "../../../desk/components/RepositoryBrowserView";
import { useRepositoryBrowser, type RepositoryReadAdapter } from "../../../desk/components/RepositoryBrowserController";
import type { RepoFile } from "../../../desk/repository";
import {
  CycleGadget,
  FilterTokens,
  StringGadget,
  SurfaceRows,
  SurfaceRow,
  SurfaceSection,
  SurfaceSplit,
  SurfaceState,
  SurfaceWell,
  SurfaceFooter,
  ActionNotice,
  ProgressPlan,
  ProvenanceChip,
  Receipt,
  StateChip,
  type PlanStep,
  ReadingDocument,
} from "../../../desk/surface";
import type { CoreProps } from "../core-types";
import { ControlsGallery } from "./ControlsGallery";
import { EditingReference, type EditingPreset } from "./EditingReference";
import { OwnerPreferencesReference, type OwnerPreferencesState } from "./OwnerPreferencesReference";
import "./design-reference.css";

type Pattern = "forms" | "editing" | "reading" | "lists" | "resources" | "conversation" | "progress" | "controls";
type ExampleState = "ordinary" | "busy" | "failed" | "empty" | "long" | "resumed" | OwnerPreferencesState | EditingPreset;

/*
 * Forms renders the Settings You fields and writer through local IO; Editing
 * renders the active Thought editor and voice recovery through local IO;
 * Resources renders the repository browser through local reads. Reading, Lists,
 * Conversation, and Progress remain bounded specimens of their library
 * surfaces. Components itself is a fixture, not a second production consumer.
 */

const PATTERNS: Array<{ id: Pattern; label: string }> = [
  { id: "forms", label: "Forms" },
  { id: "editing", label: "Editing" },
  { id: "reading", label: "Reading" },
  { id: "lists", label: "Lists" },
  { id: "resources", label: "Resources" },
  { id: "conversation", label: "Conversation" },
  { id: "progress", label: "Progress" },
  { id: "controls", label: "Controls" },
];

const STATES: Array<{ id: ExampleState; label: string }> = [
  { id: "ordinary", label: "Ordinary" },
  { id: "busy", label: "Busy" },
  { id: "failed", label: "Failed" },
  { id: "empty", label: "Empty" },
  { id: "long", label: "Long" },
];

const FORM_STATES: Array<{ id: OwnerPreferencesState; label: string }> = [
  { id: "saved", label: "Saved" },
  { id: "edited", label: "Edited" },
  { id: "saving", label: "Saving" },
  { id: "refused", label: "Refused" },
  { id: "retried", label: "Retried" },
  { id: "newer", label: "Newer edit" },
];

const EDITING_STATES: Array<{ id: EditingPreset; label: string }> = [
  { id: "ordinary", label: "Ordinary" },
  { id: "retained", label: "Retained words" },
  { id: "newer", label: "Newer draft" },
  { id: "read-only", label: "Read only" },
  { id: "linked", label: "Linked items" },
];

const RESOURCE_FILES: RepoFile[] = [
  { name: "src", path: "src", type: "dir", status: null },
  { name: "README.md", path: "README.md", type: "file", status: "M" },
];
const RESOURCE_SOURCE = "# HoldSpeak\n\nA registered repository.\nRead this file in the current view.\n";

const READING_RESULT = `# Decision record

The team chose a local review pass for the next release. The result keeps the
source beside the decision so a reader can check the reason without leaving
the desk.

## What changed

- Keep the working note in the project record.
- Show the next action beside the result.
- Mark the source as local when the desk has not sent data.

The [source note](door:source-note) contains the short evidence trail. A
reader can inspect it, keep an excerpt, and return to the result in the same
window.

## Next action

Review the release checklist after the local specimen reaches a saved state.
`;

const SOURCE_NOTE = `# Source note

Local review record · release checklist · 09:41

The decision was recorded on this desk for the next review pass.
`;

const EXCERPT = "The team chose a local review pass for the next release.";

const LONG_READING_APPENDIX = `

## Evidence

The release checklist keeps the decision beside its source. The first review
confirmed the owner, the scope, and the next action.

## Review notes

The second pass found no change to the local route. The record stays readable
when the result is longer than the window.

## Open questions

The team will check the final receipt after the next local run. A new result
can replace this one without changing the source note.

## Follow-up

Keep the decision available while the work item is selected. The action stays
at the end of the reading surface.

## Ownership

The project room owns the note while this review is open. A later pass can
replace the local result, but it keeps the same source boundary and the same
next action. That makes the record useful during a long review without moving
the reader into another window.

## Decision trail

The first pass checked the owner and scope. The second pass checked the source
note. The final pass records the result beside the action so the next person
can continue from the same place. Each section stays in the reading flow and
can be scanned with the heading structure.

## Handoff

When the release review is complete, keep the decision with the project note.
The handoff has one clear destination: review the checklist, confirm the
source, and record the next result locally. The controls remain at the end of
this surface so the reader can reach them after reading the evidence.
`;

const LIST_ITEMS = [
  { id: "release-checklist", title: "Release checklist", detail: "Seven checks · updated today", kind: "Project" },
  { id: "team-notes", title: "Team notes", detail: "Three decisions · updated yesterday", kind: "Record" },
  { id: "runtime-plan", title: "Runtime plan", detail: "Local routing · updated Monday", kind: "Plan" },
];

const FAILED_REQUEST_PAYLOAD = "Can we keep the release note local while we review it?";
const FAILED_REPLY_PAYLOAD = "The reply is available locally for the captured request.";

const STATE_OPTIONS: Record<Pattern, Array<{ id: ExampleState; label: string }>> = {
  forms: FORM_STATES,
  editing: EDITING_STATES,
  reading: [STATES[0], STATES[3], STATES[4]],
  lists: [STATES[0], STATES[3]],
  resources: [STATES[0], STATES[1], STATES[2], STATES[3], { id: "resumed", label: "Resumed" }],
  conversation: [STATES[0], STATES[1], STATES[2], STATES[3], STATES[4]],
  progress: [STATES[0], STATES[1], STATES[2]],
  controls: [],
};

function PatternSelector({ pattern, onChange }: { pattern: Pattern; onChange: (value: Pattern) => void }) {
  return (
    <FilterTokens
      options={PATTERNS.map((item) => ({ value: item.id, label: item.label }))}
      value={pattern}
      onChange={(value) => onChange(value as Pattern)}
      label="Patterns"
      className="reference-pattern-selector"
    />
  );
}

function StateSelector({ pattern, state, onChange }: { pattern: Pattern; state: ExampleState; onChange: (value: ExampleState) => void }) {
  if (pattern === "controls") return null;
  const options = STATE_OPTIONS[pattern];
  const value = options.some((item) => item.id === state) ? state : options[0].id;
  return (
    <div className="reference-state-selector" data-testid="reference-state-selector" aria-label="Example state">
      <span className="reference-selector-label">Preset</span>
      <CycleGadget
        label="Example state"
        value={value}
        options={options.map((item) => ({ value: item.id, label: item.label }))}
        onChange={(value) => onChange(value as ExampleState)}
      />
    </div>
  );
}

function ReadingPattern({ state }: { state: ExampleState }) {
  const [sourceOpen, setSourceOpen] = useState(false);
  const [keptExcerpt, setKeptExcerpt] = useState("");
  const source = state === "long" ? `${READING_RESULT}${LONG_READING_APPENDIX}` : READING_RESULT;
  const openSource = () => setSourceOpen(true);
  const toggleSource = () => setSourceOpen((open) => !open);
  const hasResult = state !== "empty";
  useEffect(() => {
    setSourceOpen(false);
    if (state === "empty") setKeptExcerpt("");
  }, [state]);
  return (
    <section className="reference-example" data-testid="reference-reading" aria-label="Reading pattern">
      <div className="reference-example-head">
        <ProvenanceChip source="Desk record" boundary="Local" />
      </div>
      {state === "empty" ? (
        <SurfaceState
          empty
          emptyLabel="No decision selected"
          emptyGlyph="○"
          onAction={sourceOpen ? undefined : openSource}
          actionLabel={sourceOpen ? undefined : "Open source"}
        />
      ) : (
        <ReadingDocument data-testid="reference-reading-document" className="reference-reading-document" noteDoors={{ "source-note": openSource }}>{source}</ReadingDocument>
      )}
      <div className="reference-actions">
        {hasResult ? <Button variant="primary" onClick={() => setKeptExcerpt(EXCERPT)}>Keep excerpt</Button> : null}
        {hasResult || sourceOpen ? <Button variant="ghost" onClick={toggleSource}>{sourceOpen ? "Close source" : "Open source"}</Button> : null}
      </div>
      {keptExcerpt ? <SurfaceWell head="KEPT EXCERPT"><p className="reference-receipt" data-testid="reference-kept-excerpt" role="status">{keptExcerpt}</p></SurfaceWell> : null}
      {sourceOpen ? <SurfaceWell head="SOURCE NOTE"><ReadingDocument data-testid="reference-source-note" className="reference-source-note">{SOURCE_NOTE}</ReadingDocument></SurfaceWell> : null}
    </section>
  );
}

function ListsPattern({ state }: { state: ExampleState }) {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(LIST_ITEMS[0].id);
  const [emptyReleased, setEmptyReleased] = useState(state !== "empty");
  useEffect(() => setEmptyReleased(state !== "empty"), [state]);
  const rows = useMemo(() => LIST_ITEMS.filter((item) => `${item.title} ${item.detail} ${item.kind}`.toLowerCase().includes(query.toLowerCase())), [query]);
  const visibleRows = state === "empty" && !emptyReleased ? [] : rows;
  const selectedItem = state === "empty" && !emptyReleased ? undefined : visibleRows.find((item) => item.id === selected);
  return (
    <section className="reference-example" data-testid="reference-list" aria-label="List pattern" id="reference-panel-lists">
      <div className="reference-example-head"><div><h2>Work items</h2></div><StateChip state={state === "empty" ? "idle" : "active"} label={visibleRows.length ? `${visibleRows.length} SHOWN` : "EMPTY"} /></div>
      <StringGadget label="Filter work items" value={query} placeholder="FILTER WORK ITEMS" onChange={setQuery} />
      {visibleRows.length ? (
        <SurfaceSplit
          main={<SurfaceRows>{visibleRows.map((item) => <SurfaceRow key={item.id} title={item.title} detail={item.detail} meta={item.kind} selected={selected === item.id} onOpen={() => setSelected(item.id)} />)}</SurfaceRows>}
          detail={selectedItem ? <div className="reference-list-detail"><h3>{selectedItem.title}</h3><p>{selectedItem.detail}</p><Button className="reference-list-back" variant="ghost" aria-label="Back to work items" onClick={() => setSelected("")}>Back</Button><Button className="reference-list-clear" variant="ghost" aria-label="Clear selection" onClick={() => setSelected("")}>Clear selection</Button></div> : null}
          detailOpen={Boolean(selectedItem)}
        />
      ) : <SurfaceState empty emptyLabel={state === "empty" && !emptyReleased ? "No work items loaded" : "No matching work items"} emptyGlyph="○" onAction={() => state === "empty" ? setEmptyReleased(true) : setQuery("")} actionLabel={state === "empty" && !emptyReleased ? "Show work items" : "Clear filter"} />}
      {selectedItem ? <p className="reference-receipt" role="status">Selected: {selectedItem.title}</p> : null}
    </section>
  );
}

function ResourcesPattern({ state }: { state: ExampleState }) {
  const adapter = useMemo<RepositoryReadAdapter>(() => ({
    tree: async (path) => {
      if (path === "src" && state === "failed") throw new Error("fixture refusal");
      if (path === "src" && state === "busy") return new Promise<RepoFile[]>(() => {});
      return state === "empty" ? [] : path === "src" ? [{ name: "index.ts", path: "src/index.ts", type: "file" }] : RESOURCE_FILES;
    },
    file: async (path) => path === "README.md" ? RESOURCE_SOURCE : "export const ready = true;\n",
  }), [state]);
  const browser = useRepositoryBrowser(adapter);
  const presetStarted = useRef(false);
  useEffect(() => {
    if (presetStarted.current || browser.busy || state === "empty") return;
    presetStarted.current = true;
    if (state === "failed" || state === "busy") browser.navigate("src");
    if (state === "resumed") browser.inspect("README.md");
  }, [browser, state]);
  return <section className="reference-example reference-resource" data-testid="reference-resource" aria-label="Resource pattern">
    <div className="reference-example-head"><div><h2>Registered repository</h2><p className="reference-receipt">RepoWindow · read and inspect</p></div></div>
    <RepositoryBrowserView browser={browser} />
  </section>;
}

type ConversationMessage = { role: "user" | "assistant"; text: string; replyTo?: string };

function ConversationPattern({ state }: { state: ExampleState }) {
  const [draft, setDraft] = useState("");
  const [sourceQuote, setSourceQuote] = useState("The source stays beside the decision.");
  const [sourceOpen, setSourceOpen] = useState(true);
  const [localReturn, setLocalReturn] = useState(false);
  const [messages, setMessages] = useState<ConversationMessage[]>([
    { role: "user", text: "Can we keep the release note local while we review it?" },
    { role: "assistant", text: "Yes. Keep the source beside the decision." },
  ]);
  const [replyState, setReplyState] = useState<"ready" | "busy" | "failed">("ready");
  const failedRequest = useRef<string | null>(null);
  const retryTimer = useRef<number | null>(null);

  useEffect(() => {
    if (retryTimer.current !== null) {
      window.clearTimeout(retryTimer.current);
      retryTimer.current = null;
    }
    if (state === "failed") {
      failedRequest.current = FAILED_REQUEST_PAYLOAD;
      setReplyState("failed");
      setMessages([{ role: "user", text: FAILED_REQUEST_PAYLOAD }]);
    } else {
      failedRequest.current = null;
      if (state === "busy") setReplyState("busy");
      else {
        setReplyState("ready");
        if (state === "empty") setMessages([]);
        if (state === "ordinary") setMessages([
          { role: "user", text: "Can we keep the release note local while we review it?" },
          { role: "assistant", text: "Yes. Keep the source beside the decision." },
        ]);
        if (state === "long") setMessages([
          { role: "user", text: "Keep the review local." },
          { role: "assistant", text: "The source stays beside the result." },
          { role: "user", text: "Show the next action at the end." },
          { role: "assistant", text: "The action remains in the composer." },
        ]);
      }
    }
  }, [state]);

  useEffect(() => () => {
    if (retryTimer.current !== null) window.clearTimeout(retryTimer.current);
  }, []);

  const send = () => {
    const value = draft.trim();
    if (!value || replyState === "busy") return;
    setMessages((items) => [...items, { role: "user", text: value }, { role: "assistant", text: "Yes. The source stays beside the result." }]);
    setDraft("");
  };
  const retry = () => {
    const request = failedRequest.current;
    if (!request || replyState === "busy" || retryTimer.current !== null) return;
    setReplyState("busy");
    retryTimer.current = window.setTimeout(() => {
      setMessages((items) => [...items, { role: "assistant", text: FAILED_REPLY_PAYLOAD, replyTo: request }]);
      setReplyState("ready");
      retryTimer.current = null;
    }, 120);
  };
  const empty = state === "empty" && messages.length === 0;
  return (
    <section className="reference-example" data-testid="reference-conversation" aria-label="Conversation pattern">
      <div className="reference-example-head"><div><h2>Review thread</h2></div><StateChip state={replyState === "failed" ? "failure" : replyState === "busy" ? "working" : "active"} label={replyState === "failed" ? "REPLY FAILED" : replyState === "busy" ? "SENDING" : "Reply ready"} /></div>
      {empty ? <SurfaceState empty emptyLabel="No messages" emptyGlyph="○" onAction={() => setMessages([{ role: "user", text: "Can we keep the release note local?" }])} actionLabel="Show thread" /> : <SurfaceRows>{messages.map((message, index) => <SurfaceRow key={`${message.role}-${index}`} title={message.role === "user" ? "You" : "Desk reply"} detail={message.text} meta={message.role === "user" ? "you" : "local"} />)}</SurfaceRows>}
      {replyState === "failed" ? <ActionNotice tone="danger" icon="!" action={{ label: "Retry", onClick: retry }}>Reply failed.</ActionNotice> : null}
      <div className="reference-conversation-source" data-testid="reference-conversation-source">
        <AskSourceFrame quote={sourceQuote} open={sourceOpen} onToggle={setSourceOpen}
          onClear={() => setSourceQuote("")} onBack={() => setLocalReturn(true)} />
        {localReturn ? <span className="reference-receipt" role="status">LOCAL RETURN</span> : null}
      </div>
      <div className="desk-pr-compose" data-specimen="true">
        <DeskComposer className="desk-mic-row" value={draft} onChange={setDraft} placeholder="Write a review note" multiline rows={3} mic={false} micDraftScope="design-reference-conversation" actionLabel={replyState === "failed" || replyState === "busy" ? "Retry" : "Send locally"} actionDisabled={replyState === "busy" || (replyState !== "failed" && !draft.trim())} actionBusy={replyState === "busy"} onAction={replyState === "failed" || replyState === "busy" ? retry : send} />
      </div>
    </section>
  );
}

function ProgressPattern({ state }: { state: ExampleState }) {
  const [run, setRun] = useState<"running" | "success" | "failed">(state === "failed" ? "failed" : state === "ordinary" ? "success" : "running");
  useEffect(() => { if (state === "failed") setRun("failed"); else if (state === "ordinary") setRun("success"); else if (state === "busy") setRun("running"); }, [state]);
  const steps: PlanStep[] = run === "success"
    ? [{ id: "prepare", label: "Prepare review", status: "done" }, { id: "check", label: "Check source", status: "done" }, { id: "record", label: "Record result", status: "done" }]
    : run === "failed"
      ? [{ id: "prepare", label: "Prepare review", status: "done" }, { id: "check", label: "Check source", status: "failed", detail: "Local source needs another read." }, { id: "record", label: "Record result", status: "queued" }]
      : [{ id: "prepare", label: "Prepare review", status: "done" }, { id: "check", label: "Check source", status: "running", progress: 0.55 }, { id: "record", label: "Record result", status: "queued" }];
  return (
    <section className="reference-example" data-testid="reference-progress" aria-label="Progress pattern">
      <div className="reference-example-head"><div><h2>Review run</h2></div><StateChip state={run === "success" ? "success" : run === "failed" ? "failure" : "working"} label={run.toUpperCase()} /></div>
      <ProgressPlan steps={steps} ariaLabel="Local review progress" receipt={run === "success" ? <Receipt status="ok" label="Review complete" timestamp="now" /> : run === "failed" ? <Receipt status="danger" label="Needs retry" /> : <ProvenanceChip source="This Mac" />} action={run === "failed" ? { label: "Retry", onClick: () => setRun("running") } : run === "success" ? { label: "Run again", onClick: () => setRun("running") } : undefined} />
      <div className="reference-actions"><Button variant="ghost" onClick={() => setRun("success")}>Finish review</Button><Button variant="ghost" onClick={() => setRun("failed")}>Fail locally</Button></div>
    </section>
  );
}

function PatternPanel({ pattern, state }: { pattern: Pattern; state: ExampleState }) {
  switch (pattern) {
    case "forms": return <OwnerPreferencesReference state={FORM_STATES.some((item) => item.id === state) ? state as OwnerPreferencesState : "saved"} />;
    case "editing": return <EditingReference key={state} preset={EDITING_STATES.some((item) => item.id === state) ? state as EditingPreset : "ordinary"} />;
    case "reading": return <ReadingPattern state={state} />;
    case "lists": return <ListsPattern state={state} />;
    case "resources": return <ResourcesPattern key={state} state={state} />;
    case "conversation": return <ConversationPattern state={state} />;
    case "progress": return <ProgressPattern state={state} />;
    case "controls": return <section className="reference-controls" data-testid="reference-controls" id="reference-panel-controls"><ControlsGallery hero={() => null} /></section>;
  }
}

export function DesignReference({ hero }: CoreProps) {
  const [pattern, setPattern] = useState<Pattern>("forms");
  const [state, setState] = useState<ExampleState>("saved");
  const [resetEpoch, setResetEpoch] = useState(0);
  const reset = () => { setPattern("forms"); setState("saved"); setResetEpoch((epoch) => epoch + 1); };
  const activeLabel = PATTERNS.find((item) => item.id === pattern)?.label ?? "Forms";
  return (
    <>
      {hero ? hero(null) : null}
      <SurfaceSection className="design-reference-shell" data-testid="design-reference">
        <div className="reference-toolbar" aria-label="Pattern controls">
          <PatternSelector pattern={pattern} onChange={(next) => { setPattern(next); if (next !== "controls") setState(next === "forms" ? "saved" : "ordinary"); }} />
          <StateSelector pattern={pattern} state={state} onChange={setState} />
          <Button dense variant="ghost" onClick={reset}>Reset</Button>
        </div>
        <div className="reference-panel" data-active-pattern={pattern} data-state={state} aria-label={`${activeLabel} pattern`} id={`reference-panel-${pattern}`}>
          <PatternPanel key={`${pattern}-${resetEpoch}`} pattern={pattern} state={state} />
        </div>
      </SurfaceSection>
      <SurfaceFooter receipt={<StateChip state="idle" label="LOCAL SPECIMEN" />} egress={<ProvenanceChip source="This Mac" />} />
    </>
  );
}
