import { useWindowMast } from "../../desk/surface";
import { useGuideView } from "../../desk/walk/viewState";
/* ListApp owns the collection. Object doors use the bounded reader below. */
import { useCallback, useEffect, useRef, useState } from "react";
import { readableError } from "../../lib/api";
import { qualifiedRef } from "../../desk/api";
import { useDesk } from "../../desk/store";
import { openRef } from "../../desk/openObject";
import { openProjectRoom, openSurfaceOr } from "../../desk/shell";
import { useOnDeskChanged } from "../../desk/useDeskChangedRefresh";
import { forgetDraft, keepDraft, keptDraft } from "../../desk/deskMemory";
import { NEW_DECISION_DRAFT, isNewDecisionScope } from "../../desk/newDecision";
import { useCopyReceipt } from "../../desk/hooks/useCopyReceipt";
import { setDecisionReaderObject } from "../../desk/decisionReaderObject";
import { DeskFilingStrip } from "../../desk/components/DeskFilingStrip";
import { DecisionRecordSendSheet } from "../../desk/documentSendsLazy";
import { runAsProgram, runAsProgramRefusal } from "../../desk/programs/RunAsProgram";
import { DeskDecisionEditor, useDeskDecisionEdit } from "../../desk/pullouts/views/DeskDecisionEdit";
import { ObjectReader, InspectorQuestion, PaneActions, PreferenceWell, ReadingDocument, ListView, SegmentedTabs, useWindowTitle, SurfaceState, PreferencePane, ListPane, InspectorFacts, ListApp, useListApp, type ListVerb, type ObjectListRow, type SpineTone } from "../../desk/surface";
import { Loading, StatusBar, countWords } from "../../desk/surface/kit";
import { wireDate } from "../../desk/surface/format";
import { plainReason } from "../../desk/surface/plainFailure";
import { useWindowInterior } from "../../desk/surface/interior";
import { useWindowBack } from "../../desk/surface/back";
import { useCompactViewport } from "../../desk/useCompactViewport";
import { ObjectActions, type ObjectVerb } from "../../desk/decisions/ObjectActions";
import { DecisionComposer, type NewDecisionAbout } from "../../desk/decisions/Composer";
import * as hub from "../../desk/decisions/api";
import type { CoreProps } from "./core-types";
import "../../desk/decisions/reader.css";
import { ShowMe } from "../../desk/walk/ShowMe";

type Row = hub.LedgerRow & { projectName?: string };
type Rec = hub.DecisionRecord;
type Pick = { kind: "record"; id: string } | { kind: "meeting"; row: Row };

/** One page of the ledger. */
const PAGE = 100;
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** `Oct 24`: a day in mono. */
function dayWords(value: string | null | undefined): string {
  const date = value ? wireDate(value) : null;
  return date ? `${MONTHS[date.getMonth()]} ${date.getDate()}` : "";
}

/** `just now`, `4 min ago`, `3 h ago`, then the day. */
function sinceWord(value: string | null | undefined, now: number = Date.now()): string {
  const at = value ? wireDate(value) : null;
  if (!at) return "";
  const minutes = Math.floor((now - at.getTime()) / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  if (minutes < 12 * 60) return `${Math.floor(minutes / 60)} h ago`;
  return `on ${dayWords(value)}`;
}

/** Where a decision stands, in one of the six meaning colours. */
type Standing = "proposed" | "decided" | "committed" | "disputed" | "superseded" | "retired";
const STANDING: Record<Standing, { word: string; tone: SpineTone; lamp: "ask" | "info" | "ok" | "warn" | "fail" }> = {
  proposed: { word: "Proposed", tone: "brass", lamp: "ask" },
  decided: { word: "Decided", tone: "steel", lamp: "info" },
  committed: { word: "Committed", tone: "moss", lamp: "ok" },
  disputed: { word: "Disputed", tone: "coral", lamp: "fail" },
  superseded: { word: "Superseded", tone: "graphite", lamp: "info" },
  retired: { word: "Retired", tone: "graphite", lamp: "info" },
};

function standing({ lifecycle, status, committed }: { lifecycle?: string | null; status?: string | null; committed?: unknown }): Standing {
  const life = String(lifecycle ?? "").toLowerCase();
  const own = String(status ?? "").toLowerCase();
  if (life === "superseded" || own === "superseded") return "superseded";
  if (life === "disputed") return "disputed";
  if (own === "proposed") return "proposed";
  if (own === "deprecated" || own === "rejected" || life === "deprecated" || life === "rejected") return "retired";
  return committed ? "committed" : "decided";
}

const rowKey = (row: Row) => (row.record_id ? `record:${row.record_id}` : `${row.source}:${row.id}`);

function fromRecord(record: Rec): Row {
  return {
    source: record.source_type === "desk" ? "desk" : "meeting", id: record.source_id || record.id,
    text: (record.title || "").trim() || record.decision_text, rationale: record.rationale,
    decided_at: record.created_at ?? null, lifecycle: record.lifecycle, status: record.status ?? null,
    record_id: record.id, committed_to: record.committed_to ?? null, committed: Boolean(record.committed_to),
  };
}

/** A record's About and Why, as the from-desk producer writes them into its
 *  rationale (`About: …` then `Why: …`); any other rationale is the Why. */
function rationaleParts(rationale: string | null | undefined): { about: string; why: string } {
  const text = String(rationale || "");
  const about = text.match(/(?:^|\n\n)About:\s*([^\n]*(?:\n(?!Why:)[^\n]*)*)/i)?.[1]?.trim() || "";
  const why = text.match(/(?:^|\n\n)Why:\s*([\s\S]*)/i)?.[1]?.trim() || "";
  return { about, why: why || (!about ? text.trim() : "") };
}

function workName(type: string): string {
  return ({ story: "story", project: "project", meeting: "meeting", decision: "decision", note: "note", workbench: "automation", thread: "thread" } as Record<string, string>)[type] ?? "work";
}

export function DecisionsCore({ scope, scopeLabel }: CoreProps) {
  const projects = useDesk((state) => state.projects);
  const recordScope = scope?.startsWith("record:") ? scope.slice("record:".length) : "";
  const decisionScope = scope?.startsWith("decision:") ? scope.slice("decision:".length) : "";
  const onlyRecords = scope?.startsWith("records:") ? scope.slice("records:".length).split(",").map((id) => id.trim()).filter(Boolean) : [];
  const composeScope = isNewDecisionScope(scope);
  const aboutId = composeScope && scope?.includes(":project:") ? scope.slice(scope.indexOf(":project:") + ":project:".length) : "";
  const about: NewDecisionAbout | null = aboutId
    ? { id: aboutId, name: scopeLabel || projects.find((item) => item.id === aboutId)?.name || "Project" }
    : null;

  const [readVersion, setReadVersion] = useState(0);
  const [current, setCurrent] = useState(scope === "current");
  const [picked, setPicked] = useState<Pick | null>(null);
  const [composing, setComposing] = useState(composeScope);
  const [pickError, setPickError] = useState("");
  const [creating, setCreating] = useState(false);
  const [writing, setWriting] = useState(false);
  const [writeFailure, setWriteFailure] = useState("");
  const writingRef = useRef(false);
  const creatingRef = useRef(false);
  const read = useCallback(async ({ query, offset, limit }: { query: string; offset: number; limit: number }) => {
    let answer: { rows: Row[]; total: number };
    const only = scope?.startsWith("records:") ? scope.slice("records:".length).split(",").map(id => id.trim()).filter(Boolean) : [];
    if (only.length) {
      const found = await Promise.all(only.map(id => hub.readRecord(id).then(r => r?.id ? fromRecord(r) : null, () => null)));
      const kept = found.filter((row): row is Row => Boolean(row))
        .filter(row => !current || ["decided", "committed", "proposed"].includes(standing(row)))
        .filter(row => !query.trim() || row.text.toLowerCase().includes(query.trim().toLowerCase()));
      answer = { rows: offset ? [] : kept, total: kept.length };
    } else {
      const body = await hub.readLedger({ q: query, current, limit, offset });
      const rows = Array.isArray(body?.decisions) ? body.decisions : [];
      answer = { rows, total: Number(body?.page?.total ?? rows.length) };
    }
    // The ledger has no project field. The record owns its filing and sources.
    const rows = await Promise.all(answer.rows.map(async row => {
      const record = row.record_id ? await hub.readRecord(row.record_id).catch(() => null) : null;
      const id = record?.project_id || record?.sources?.find(source => source.source_type === "project")?.source_ref;
      return { ...row, projectName: useDesk.getState().projects.find(project => project.id === id)?.name || rationaleParts(record?.rationale ?? row.rationale).about };
    }));
    return { ...answer, rows };
  }, [scope, current]);
  const app = useListApp({ read, keyOf: rowKey, pageSize: PAGE, initialPicked: onlyRecords[0] ? `record:${onlyRecords[0]}` : null });
  useWindowMast({ line: app.page ? countWords(app.total ?? app.rows.length, "decision") ?? undefined : undefined, figures: [{ value: app.rows.filter(row => ["proposed", "disputed"].includes(standing(row))).length, label: "to decide", tone: "ask" }] });
  const { rows, total, more, setPicked: setSelectedKey } = app;
  useOnDeskChanged(app.reload, ["action", "action_item", "decision", "decision_record", "follow_through"]);
  useGuideView(() => ({picked,composing}), saved => {setPicked(saved.picked);setComposing(saved.composing);}, () => {setPicked(null);setComposing(false);}, 1);

  // The window's scope picks: a record, a meeting's decision (read by its id,
  // never found in the page), only some records (the first picked), the composer.
  const pickReads = useRef(0);
  useEffect(() => {
    setPickError("");
    setComposing(composeScope);
    if (composeScope) { setPicked(null); setSelectedKey(null); return; }
    if (recordScope) { setSelectedKey(`record:${recordScope}`); setPicked({ kind: "record", id: recordScope }); return; }
    if (onlyRecords[0]) { setPicked(null); setSelectedKey(`record:${onlyRecords[0]}`); return; }
    if (decisionScope) {
      const mine = ++pickReads.current;
      void hub.readLedger({ decisionId: decisionScope, limit: 1 })
        .then((body) => {
          if (mine !== pickReads.current) return;
          const row = body?.decisions?.[0];
          if (row) pickRow(row);
          else setPickError("This decision is not on the desk.");
        })
        .catch((reason) => { if (mine === pickReads.current) setPickError(readableError(reason)); });
      return;
    }
    setPicked(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scope]);

  const pickRow = (row: Row) => {
    pickReads.current += 1;
    setPickError("");
    setComposing(false);
    if (row.record_id) {
      setPicked({ kind: "record", id: row.record_id });
      useDesk.getState().openSurfaceWindow("open-decisions", `record:${row.record_id}`);
    }
    else if (row.source === "desk") openRef(`desk_decision:${row.id}`);
    else {
      setPicked({ kind: "meeting", row });
      useDesk.getState().openSurfaceWindow("open-decisions", `decision:${row.id}`);
    }
  };
  // Back to the rail; a scoped window forgets its scope, so a reload shows the rail.
  const back = () => {
    pickReads.current += 1;
    setPicked(null);
    setComposing(false);
    setPickError("");
    if (scope && scope !== "current") useDesk.getState().openSurfaceWindow("open-decisions", undefined);
  };
  const compact = useCompactViewport();
  const backRef = useRef(back);
  backRef.current = back;
  const onFace = picked;
  const away = Boolean(onFace || pickError);
  useWindowBack(compact && away ? { onBack: () => backRef.current(), testId: "decision-reader-back" } : null, [compact, away]);

  // The composer's words are kept for a reload; Cancel forgets them.
  const [title, setTitleState] = useState(() => keptDraft(NEW_DECISION_DRAFT.title) ?? "");
  const [why, setWhyState] = useState(() => keptDraft(NEW_DECISION_DRAFT.why) ?? "");
  useEffect(() => {
    if (!composeScope) return;
    setTitleState(keptDraft(NEW_DECISION_DRAFT.title) ?? "");
    setWhyState(keptDraft(NEW_DECISION_DRAFT.why) ?? "");
  }, [composeScope]);
  const setTitle = (next: string) => { keepDraft(NEW_DECISION_DRAFT.title, next); setTitleState(next); };
  const setWhy = (next: string) => { keepDraft(NEW_DECISION_DRAFT.why, next); setWhyState(next); };
  const forget = () => {
    forgetDraft(NEW_DECISION_DRAFT.title);
    forgetDraft(NEW_DECISION_DRAFT.why);
    setTitleState("");
    setWhyState("");
  };
  const startNew = () => {
    if (composing) { back(); return; }
    void useDesk.getState().createPrimitive("decision", {});
  };
  const create = async () => {
    const name = title.trim();
    if (!name || creatingRef.current) return;
    const reason = why.trim();
    creatingRef.current = true;
    setCreating(true);
    try {
      await useDesk.getState().createPrimitive("decision", {
      title: name,
      ...(reason ? { why: reason } : {}),
      ...(about ? { project_id: about.id, project_name: about.name } : {}),
      });
      if (useDesk.getState().windowsById["surface-decisions"]?.scope?.startsWith("record:")) forget();
    } finally {
      creatingRef.current = false;
      setCreating(false);
    }
  };
  const cancel = () => { forget(); back(); };

  const byKey = new Map(rows.map((row) => [rowKey(row), row]));
  const pickedKey = onFace?.kind === "record" ? `record:${onFace.id}` : onFace?.kind === "meeting" ? rowKey(onFace.row) : null;
  const pickedRow = pickedKey ? byKey.get(pickedKey) ?? null : null;
  const proposed = rows.filter((row) => ["proposed", "disputed"].includes(standing(row)));
  const open = (item: ObjectListRow | null) => { const row = item ? byKey.get(item.id) : null; if (row) pickRow(row); };
  const write = async (item: ObjectListRow | null, action: "decide" | "commit" | "retire" | "resolve") => {
    const row = item ? byKey.get(item.id) : null;
    if (!row || writingRef.current) return;
    writingRef.current = true;
    setWriting(true);
    setWriteFailure("");
    try {
      if (action === "commit" && row.record_id) {
        const record = await hub.readRecord(row.record_id);
        await hub.commitDecision(row.record_id, record.owner);
      } else if (action === "resolve") {
        const answer = await hub.supersedeDecision(row.id);
        if (answer.decision?.id) openRef(`desk_decision:${answer.decision.id}`);
      } else await hub.writeDecisionStatus(row.id, action === "decide" ? "accepted" : "deprecated");
      setReadVersion((value) => value + 1);
      void app.reload();
      void useDesk.getState().refresh();
    } catch (cause) { setWriteFailure(`Could not ${action} it · ${plainReason(cause)}`); }
    finally { writingRef.current = false; setWriting(false); }
  };
  const can = (item: ObjectListRow | null, states: Standing[], desk = false) => {
    const row = item ? byKey.get(item.id) : null;
    return Boolean(!writing && row && (!desk || row.source === "desk") && states.includes(standing(row)));
  };
  const verbs: ListVerb[] = [
    { id: "new", variant: "primary", label: "New decision", key: "n", testId: "decisions-new", enabled: () => !creating, run: startNew },
    { id: "open", label: "Open", key: "Enter", enabled: (row) => Boolean(row), run: open },
    { id: "decide", label: "Decide", key: "d", enabled: (item) => can(item, ["proposed"], true), run: (item) => void write(item, "decide") },
    { id: "commit", label: "Commit", key: "k", enabled: (item) => can(item, ["decided"]) && Boolean(item && byKey.get(item.id)?.record_id), run: (item) => void write(item, "commit") },
    { id: "retire", label: "Retire", key: "r", enabled: (item) => can(item, ["decided", "committed"], true), run: (item) => void write(item, "retire") },
    { id: "resolve", label: "Resolve", key: "s", enabled: (item) => can(item, ["disputed"], true), run: (item) => void write(item, "resolve") },
    ...(rows.length > 0 && rows.length < total ? [{ id: "more", label: "Show more", key: "p", testId: "decisions-more", enabled: () => !more, run: () => void app.showMore() }] : []),
    ...(onlyRecords.length ? [{ enabled:()=>true, id: "all", label: "All decisions", key: "a", testId: "decisions-all", run: back }] : []),
  ];
  // Explicit object doors retain the reader and its actions. Selection in the
  // collection is a plain preview; only Open/Return/double-click enters here.
  if (onFace || pickError) return <div className="decisions-frame" data-testid="decisions-window" data-picked="">
    <div className="decisions-pane" data-testid="decisions-pane">
      {pickError ? <SurfaceState error={pickError} /> : onFace?.kind === "record"
        ? <RecordPane key={onFace.id} id={onFace.id} row={pickedRow} onBack={back} onOpenRecord={(id) => setPicked({ kind: "record", id })} />
        : onFace?.kind === "meeting" ? <MeetingDecisionPane row={onFace.row} onBack={back} /> : null}
    </div>
  </div>;

  return <ListApp app={app} label="Decisions" listShare={.6}
    ids={{ windowTestId: "decisions-window", listTestId: "decisions-rail", paneTestId: "decisions-preview", toolbarTestId: "decisions-toolbar", statusTestId: "decisions-status", loadingTestId: "decisions-loading" }}
    words={{ find: "Find a decision", empty: current ? "No current decisions" : "No decisions yet", noMatch: "No decisions match this search", select: "Select a decision." }}
    row={row => {
      const state = standing(row);
      return { id: rowKey(row), kind: "decision", name: row.text.trim() || "New decision", when: state === "proposed" ? "" : dayWords(row.decided_at),
        cells: { project: row.projectName }, state: { label: STANDING[state].word, tone: state === "decided" ? "ok" : STANDING[state].lamp } };
    }} list={{ columns: [
      { key: "name", word: "Decision", priority: 100, track: "minmax(0, 3fr)", minWidth: 200 },
      ...(app.visible.some(row => row.projectName) ? [{ key: "project", word: "Project", priority: 10, track: "minmax(0, 1fr)" }] : []),
      { key: "when", word: "Decided", priority: 20, track: "112px" },
      { key: "state", word: "State", priority: 30, track: "112px" },
    ], verbs, defaultVerb: "open", toolbar: { scopes: [{ id: "current", kind: "tick", label: "Current only", checked: current, onChange: setCurrent }] },
      rowProps: () => ({ "data-testid": "decisions-row", "data-kind": "decision" }) }}
    onSelect={() => { setComposing(false); if (onFace) back(); }}
    pane={selected => composing ? <DecisionComposer title={title} why={why} about={about} onTitle={setTitle} onWhy={setWhy}
      onCreate={() => void create()} onCancel={cancel} busy={creating} autoFocus />
      : selected ? <DecisionPreview key={`${rowKey(selected)}:${readVersion}`} row={selected} /> : null}
    status={[
      { key: "count", text: countWords(total, "decision") },
      { key: "open", lamp: "ask", text: proposed.length ? `${proposed.length} ${proposed.length === 1 ? "needs" : "need"} you` : null },
      { key: "failure", lamp: "fail", text: writeFailure || null },
    ]}>
    <ShowMe app="surface-decisions" />
  </ListApp>;
}

/** Read the selected record without opening its action surface. A late read
 * cannot replace the facts of the next selection. */
function DecisionPreview({ row }: { row: Row }) {
  const [record, setRecord] = useState<Rec | null>(null);
  const [failure, setFailure] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    if (!row.record_id) return;
    void hub.readRecord(row.record_id).then((answer) => { if (active) { setRecord(answer); setFailure(""); } })
      .catch((cause) => { if (active) setFailure(readableError(cause)); });
    return () => { active = false; };
  }, [row.record_id, row.lifecycle, row.status, row.committed_to, retry]);
  const projects = useDesk((state) => state.projects);
  const parts = rationaleParts(record?.rationale ?? row.rationale);
  const projectId = record?.project_id || record?.sources?.find((source) => source.source_type === "project")?.source_ref;
  const project = parts.about || projects.find((item) => item.id === projectId)?.name || "";
  const state = standing(row);
  const at = state === "proposed" ? record?.created_at ?? row.decided_at : row.decided_at;
  const facts = [
    ...(["proposed", "disputed", "superseded"].includes(state) ? [{ label: "State", value: STANDING[state].word }] : []),
    ...(record?.decision_text && record.decision_text !== row.text ? [{ label: "Words", value: record.decision_text }] : []),
    ...(project ? [{ label: "Project", value: project }] : []),
    ...(at ? [{ label: state === "proposed" ? "Created" : "Decided", value: dayWords(at) }] : []),
    ...(row.meeting_title ? [{ label: "Meeting", value: row.meeting_title }] : []),
    ...(parts.why ? [{ label: "Why", value: parts.why }] : []),
    ...(record?.dispute_reason ? [{ label: "Dispute", value: record.dispute_reason }] : []),
    ...(record?.owner ? [{ label: "Owner", value: record.owner }] : []),
    ...(record?.alternatives ? [{ label: "Choices", value: record.alternatives }] : []),
    ...(record?.review_date ? [{ label: "Review", value: dayWords(record.review_date) }] : []),
    ...(record?.committed_to || row.committed_to ? [{ label: "Committed to", value: record?.committed_to || row.committed_to }] : []),
  ];
  return <InspectorFacts name={row.text} rows={facts} testId="decision-summary" notice={failure ? <SurfaceState error={failure} onRetry={() => { setFailure(""); setRetry((value) => value + 1); }} /> : null} />;
}

/** A decision record: one declared action set and bounded reading views. */
function RecordPane({ id, row, onOpenRecord, onBack }: { id: string; row: Row | null; onOpenRecord(id: string): void; onBack(): void }) {
  useWindowInterior("list");
  const [record, setRecord] = useState<Rec | null>(null);
  const [failure, setFailure] = useState("");
  const [loading, setLoading] = useState(true);
  const reads = useRef(0);
  const load = (quiet = false) => {
    const mine = ++reads.current;
    if (!quiet) { setLoading(true); setFailure(""); }
    void hub.readRecord(id)
      .then((answer) => { if (mine === reads.current && answer?.id) setRecord(answer); })
      .catch((reason) => { if (mine === reads.current && !quiet) setFailure(readableError(reason)); })
      .finally(() => { if (mine === reads.current) setLoading(false); });
  };
  useEffect(() => { load(); return () => { reads.current += 1; }; }, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  useOnDeskChanged(() => load(true), ["decision", "decision_record"]);
  const deskId = record?.source_type === "desk" && record.source_id ? String(record.source_id) : "";
  const edit = useDeskDecisionEdit(deskId, () => load(true));
  // The window's Object menu is this decision's while the pane shows it.
  useEffect(() => { setDecisionReaderObject(deskId || null); return () => setDecisionReaderObject(null); }, [deskId]);
  const [sending, setSending] = useState(false);
  const [filing, setFiling] = useState(false);
  const [filed, setFiled] = useState("");
  const [writing, setWriting] = useState<"" | "accepted" | "deprecated" | "commit" | "resolve" | "delete">("");
  const [writeFailure, setWriteFailure] = useState("");

  const [committedHere, setCommittedHere] = useState<string | null>(null);
  const { copy, state: copyState } = useCopyReceipt();
  const copyReceipt = copyState === "copied" ? "Copied" : copyState === "failed" ? "Copy failed. Text kept. Try again." : "";

  const busy = Boolean(writing) || edit.saving;
  const writeStatus = async (next: "accepted" | "deprecated") => {
    if (!deskId || busy) return;
    setWriting(next);
    setWriteFailure("");

    try {
      await hub.writeDecisionStatus(deskId, next);

      void useDesk.getState().refresh();
      load(true);
      return true;
    } catch (cause) {
      setWriteFailure(`${next === "accepted" ? "Could not decide it" : "Could not retire it"} · ${plainReason(cause)}`);
    } finally {
      setWriting("");
    }
  };
  const commit = async () => {
    if (!record || busy) return;
    setWriting("commit");
    setWriteFailure("");
    try {
      const answer = await hub.commitDecision(record.id, record.owner);
      setCommittedHere(answer?.owner || record.owner || "");
      load(true);
    } catch (cause) {
      setWriteFailure(`Could not commit it · ${plainReason(cause)}`);
    } finally {
      setWriting("");
    }
  };
  // A dispute ends with a newer decision: Resolve makes the successor and opens it.
  const resolve = async () => {
    if (!deskId || busy) return;
    setWriting("resolve");
    setWriteFailure("");
    try {
      const answer = await hub.supersedeDecision(deskId);
      const next = answer?.decision?.id;
      if (next) openRef(`desk_decision:${next}`);
    } catch (cause) {
      setWriteFailure(`Could not resolve it · ${plainReason(cause)}`);
    } finally {
      setWriting("");
    }
  };
  const [tab, setTab] = useState("decision");
  const [sourceId, setSourceId] = useState<string | null>(null);
  const compact = useCompactViewport();
  const [question, setQuestion] = useState<"retire" | "delete" | null>(null);
  const [programBusy, setProgramBusy] = useState(false);
  useWindowTitle(record ? (record.title || record.decision_text) : null, [record?.title, record?.decision_text]);
  const deleteTarget = useRef("");
  deleteTarget.current = question === "delete" ? JSON.stringify(record) : "";
  useEffect(() => () => { deleteTarget.current = ""; }, []);
  const deleteDecision = async () => {
    if (!deskId || busy) return;
    const target = deleteTarget.current;
    setWriting("delete"); setWriteFailure("");
    const { verbById } = await import("../../desk/verbRegistry");
    if (!target || deleteTarget.current !== target) { setWriting(""); return; }
    const context = { selectedRef: "decision:" + deskId };
    const verb = verbById("object.delete");
    const refusal = verb?.ghost(context);
    setWriting("");
    if (!verb || refusal) { setWriteFailure(refusal || "Delete is not available."); return; }
    useDesk.getState().closeSurfaceWindow("open-decisions");
    verb.run(context);
  };

  if (loading || failure || !record) {
    return <PreferencePane label="Decision reader" testId="decision-reader">
      {loading ? <Loading /> : <SurfaceState error={failure || "Decision unavailable."} onRetry={() => load()} />}
    </PreferencePane>;
  }

  const name = (record.title || "").trim() || record.decision_text;
  const committedTo = record.committed_to || committedHere || row?.committed_to || null;
  const committed = Boolean(committedTo) || committedHere !== null || Boolean(row?.committed);
  const state = standing({ lifecycle: record.lifecycle, status: record.status, committed });
  const look = STANDING[state];
  const { about, why } = rationaleParts(record.rationale);
  const projectId = record.project_id ?? record.sources?.find((source) => source.source_type === "project")?.source_ref ?? "";
  const meetingSource = record.sources?.find((source) => source.meeting_id || source.source_type === "meeting");
  const from = row?.meeting_title || (meetingSource ? "a meeting" : record.source_type === "desk" ? "Desk" : "");
  const when = sinceWord(record.created_at);
  const sourceLabel = (source: hub.RecordSource): string | null => source.meeting_id || source.source_type === "meeting"
    ? "Open meeting" : source.source_type === "artifact" ? "Open artifact" : null;
  const openSource = (source: hub.RecordSource) => {
    const meetingId = source.meeting_id ?? (source.source_type === "meeting" ? source.source_ref : "");
    if (meetingId) openRef(`meeting:${meetingId.replace(/^meeting:/, "")}`);
    else if (source.source_type === "artifact") openRef(`artifact:${source.source_ref.replace(/^artifact:/, "")}`);
  };
  const evidence = record.sources?.filter((source) => !["predecessor", "successor", "desk", "project", "person"].includes(source.source_type)
    && (source.text || sourceLabel(source))) ?? [];
  const decided = state === "decided" || state === "committed";

  const stateWords = writing === "accepted" ? "Deciding" : writing === "deprecated" ? "Retiring" : writing === "commit" ? "Committing"
    : edit.saving ? "Saving" : ["proposed", "disputed"].includes(state) ? look.word : "";
  const words = [`# ${name}`, name !== record.decision_text.trim() ? record.decision_text : "", record.rationale || ""]
    .filter((part) => part.trim()).join("\n\n");
  const filingProps = {
    objectRef: qualifiedRef("decision", deskId), objectKind: "decision" as const, objectId: deskId, bare: true, onSummary: setFiled,
    projectRef: `decision_record:${record.id}`,
  };

  const ready = () => !busy && !programBusy && !question;
  const ask = (kind: "retire" | "delete") => { setSending(false); setFiling(false); setTab("decision"); setQuestion(kind); setWriteFailure(""); };
  const program = async () => {
    setProgramBusy(true); setWriteFailure("");
    try { await runAsProgram({ kind: "decision_record", id: record.id, title: name,
      goal: [record.decision_text, record.rationale].filter(Boolean).join("\n\n"), projectId: projectId || null }); }
    catch (cause) { setWriteFailure(runAsProgramRefusal(cause, "decision_record")); }
    finally { setProgramBusy(false); }
  };
  const verbs: ObjectVerb[] = edit.editing ? [] : [
    {id:"back",label:"All decisions",testId:compact ? undefined : "decision-reader-back",enabled:ready,run:onBack},
    ...(deskId ? [{ id: "edit", label: "Edit", testId: "decision-reader-edit", enabled: () => ready() && !edit.opening, run: () => void edit.start() }] : []),
    ...(state === "proposed" && deskId ? [{ id: "decide", label: "Decide", testId: "decision-reader-accept", enabled: ready, run: () => void writeStatus("accepted") }] : []),
    ...(state === "decided" ? [{ id: "commit", label: "Commit", testId: "decision-reader-commit", enabled: ready, run: () => void commit() }] : []),
    ...(state === "disputed" && deskId ? [{ id: "resolve", label: "Resolve", testId: "decision-reader-resolve", enabled: ready, run: () => void resolve() }] : []),
    ...(state !== "proposed" ? [
      { id: "send", label: "Send…", testId: "decision-reader-send", enabled: ready, run: () => setSending(!sending) },
      { id: "program", label: "Run as a program", menuOnly: true, testId: "decision-reader-program", enabled: ready, run: () => void program() },
    ] : []),
    { id: "copy", label: "Copy", testId: "decision-reader-copy", run: () => void copy(words) },
    ...(projectId ? [{id:"project",label:"Open project",menuOnly:true,testId:"decision-reader-about",run:() => openProjectRoom(projectId)}] : []),
    ...(deskId ? [
      { id: "file", label: "File", testId: "decision-reader-filed", enabled: ready, run: () => setFiling(!filing) },

      { id: "dictate", label: "Dictate about this", menuOnly:true, testId: "decision-reader-dictate", run: () => openSurfaceOr("dictate", "/dictation", qualifiedRef("decision", deskId)) },
      ...(decided ? [{ id: "retire", label: "Retire", testId: "decision-reader-retire", enabled: ready, run: () => ask("retire") }] : []),
      { id: "delete", label: "Delete", testId: "decision-reader-delete", enabled: ready, run: () => ask("delete") },
    ] : []),
    ...(record.predecessor_id ? [{ id: "previous", label: "Previous decision", menuOnly:true, run: () => onOpenRecord(record.predecessor_id!) }] : []),
    ...(record.successor_id ? [{ id: "next", label: "Open the new one", menuOnly:true, testId: "decision-reader-successor", run: () => onOpenRecord(record.successor_id!) }] : []),
  ];
  const sourceKey = (source: hub.RecordSource) => "source:" + source.source_type + ":" + source.source_ref + ":" + (source.meeting_id ?? "");
  const sourcesById = new Map(evidence.map(source => [sourceKey(source),source]));
  const sourceRows: ObjectListRow[] = [
    ...evidence.map(source => ({ id: sourceKey(source), kind: source.source_type, name: [source.speaker, source.text || sourceLabel(source)].filter(Boolean).join(": ") })),
    ...(record.work ?? []).map(work => ({ id: "work-" + work.id, kind: work.work_type, name: workName(work.work_type) + " · " + work.work_ref })),
  ];
  const openEvidence = (item: ObjectListRow | null) => {
    if (!item) return;
    const source = sourcesById.get(item.id);
    if (source) openSource(source);
    else { const work = record.work?.find(work => "work-" + work.id === item.id); if (work) useDesk.getState().openPullout(qualifiedRef(work.work_type, work.work_ref)); }
  };
  const tabs = [{ id: "decision", label: "Decision" }, { id: "facts", label: "Facts" },
    ...(sourceRows.length ? [{ id: "evidence", label: "Evidence" }] : []),
    ...(record.revisions?.length ? [{ id: "history", label: "History" }] : [])];
  const view = tabs.some(item => item.id === tab) ? tab : "decision";
  return <PreferencePane label="Decision reader" testId="decision-reader">
    {!edit.editing ? <ObjectActions label="Decision" verbs={verbs} testId="decision-reader-toolbar" /> : null}
    {edit.editing ? <DeskDecisionEditor edit={edit} />
      : sending ? <DecisionRecordSendSheet id={record.id} text={record.decision_text} onBack={() => setSending(false)} />
      : filing && deskId ? <section className="surface-pane-inspector" data-testid="decision-filing-well"><PreferenceWell><DeskFilingStrip {...filingProps} /></PreferenceWell></section>
      : <SegmentedTabs label="Decision views" tabs={tabs} value={view} onChange={next => {if(!question)setTab(next);}}>
        {view === "decision" ? <ObjectReader label="Decision" testId="decision-reading-well" facts={[{label:"State",value:look.word},{label:"From",value:from},{label:"Created",value:when},{label:"Owner",value:record.owner}]}><ReadingDocument data-testid="decision-words">{[record.decision_text, why ? "## Why\n\n" + why : ""].filter(Boolean).join("\n\n")}</ReadingDocument></ObjectReader> : null}
        {view === "facts" ? <InspectorFacts name="Facts" testId="decision-facts" rows={[
          {label:"State",value:look.word},{label:"From",value:from},{label:"Created",value:when},{label:"Owner",value:record.owner},
          {label:"About",value:about},{label:"Choices",value:record.alternatives},{label:"Review",value:dayWords(record.review_date)},
          {label:"Committed to",value:committedTo},{label:"Dispute",value:record.dispute_reason}, {label:"Filed in",value:filed},
        ]} /> : null}
        {view === "evidence" ? <ListPane label="Selected source" list={<ListView label="Evidence" rows={sourceRows} columns={[{key:"name",word:"Source"}]} ordered
          selectedId={sourceId} onSelect={setSourceId}
          verbs={[{id:"open",label:"Open source",key:"Enter",enabled:row => {const source = row ? sourcesById.get(row.id) : null;return Boolean(row && ((record.work ?? []).some(work => "work-" + work.id === row.id) || (source && sourceLabel(source))));},run:openEvidence}]} defaultVerb="open" />}>
          {sourceRows.find(source => source.id === sourceId) ? <section className="surface-pane-inspector"><PreferenceWell><ReadingDocument>{sourceRows.find(source => source.id === sourceId)!.name}</ReadingDocument></PreferenceWell></section> : "Select a source."}
        </ListPane> : null}
        {view === "history" ? <section className="surface-pane-inspector" data-testid="decision-history-well"><PreferenceWell><InspectorFacts name="History" testId="decision-history" rows={[...(record.revisions ?? [])].sort((a,b) => String(b.created_at).localeCompare(String(a.created_at))).map(revision => ({key:revision.id,label:dayWords(revision.created_at),value:revision.field_name.replace(/_/g," ") + ": " + (revision.old_value || "—") + " → " + (revision.new_value || "—")}))} /></PreferenceWell></section> : null}
      </SegmentedTabs>}
    {question ? <PaneActions><InspectorQuestion key={record.id + question} actionId={question} targetId={JSON.stringify(record)} question={(question === "retire" ? "Retire " : "Delete ") + name + "?"}
      keeps={question === "retire" ? ["The decision", "its history"] : undefined} cancel={() => setQuestion(null)}
      verb={{ label: question === "retire" ? "Retire" : "Delete", busy, run: () => { if (question === "retire") { void writeStatus("deprecated").then(saved => {if(saved)setQuestion(null);}); } else void deleteDecision(); } }}
      notice={writeFailure ? <SurfaceState error={writeFailure} /> : null} testId="decision-reader-question" /></PaneActions> : null}
    {deskId && !filing ? <span hidden aria-hidden="true"><DeskFilingStrip {...filingProps} /></span> : null}
    <StatusBar data-testid="decision-reader-status" parts={[
      {key:"state",lamp:busy ? "info" : look.lamp,testId:"decision-reader-state",text:stateWords},
      {key:"failure",lamp:"fail",text:writeFailure || edit.openFailure || null,testId:"decision-reader-failure"},
      {key:"receipt",lamp:copyState === "failed" ? "fail" : undefined,text:copyReceipt || (edit.editing ? "Draft kept" : edit.saved ? "Saved" : null),testId:"decision-reader-receipt"},
      {key:"changed",text:when,priority:1},
      {key:"sources",text:sourceRows.length ? countWords(sourceRows.length,"source") : null,priority:0},
    ]} />
    <ShowMe app="surface-decisions" />
  </PreferencePane>;
}

/** A meeting decision without a record uses the same bounded reading well. */
function MeetingDecisionPane({ row, onBack }: { row: Row; onBack():void }) {
  useWindowInterior("list");
  useWindowTitle(row.text, [row.text]);
  const compact = useCompactViewport();
  const meetingId = (row.meeting_id ?? "").trim();
  return <PreferencePane label="Decision reader" testId="decision-reader" data-from="meeting">
    {meetingId ? <ObjectActions label="Decision" verbs={[{id:"back",label:"All decisions",testId:compact ? undefined : "decision-reader-back",run:onBack},{id:"meeting",label:"Open meeting",testId:"decision-reader-meeting",run:() => openRef("meeting:" + meetingId)}]} /> : null}
    <section className="surface-pane-inspector"><PreferenceWell><ReadingDocument>{[row.text,row.rationale].filter(Boolean).join("\n\n")}</ReadingDocument></PreferenceWell></section>
    <StatusBar data-testid="decision-reader-status" parts={[{key:"changed",text:sinceWord(row.decided_at)},{key:"from",text:row.meeting_title}]} />
    <ShowMe app="surface-decisions" />
  </PreferencePane>;
}
