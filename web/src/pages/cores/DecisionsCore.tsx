/* Decisions, the native app (the language, 2026-11-08: Programs, the Room,
 * People). The rail of decisions at the left; the decision at the right as
 * one object: the mast (the decision sprite, its title, when · from where ·
 * who), its spine, the PLATE (the one thing that matters now, with its one
 * verb: Decide a proposal, Commit a decided record, Resolve a disputed one,
 * Open the new one of a superseded one) and the ledger (its words, the
 * choices, the evidence, the commitment, the history by time). New decision
 * is the composer as the plate, in this window. Every hub call goes through
 * `desk/decisions/api.ts`.
 *
 * Scopes: `record:<id>` opens a record; `decision:<id>` a meeting's
 * decision with no record yet; `records:<id>,<id>` only those records (WHY
 * with several); `current` the list with Current only on; `new` and
 * `new:project:<id>` the composer. */
import { useEffect, useRef, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
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
import { RunAsProgramVerb } from "../../desk/programs/RunAsProgram";
import { DeskDecisionEditor, useDeskDecisionEdit } from "../../desk/pullouts/views/DeskDecisionEdit";
import { Material, Mast, Spine, SurfaceLedger, SurfaceLedgerRow, SurfaceState, type SpineTone } from "../../desk/surface";
import { DotWord, Loading, StatusBar, ToolGlyph, ToolbarFold, countWords } from "../../desk/surface/kit";
import { wireDate } from "../../desk/surface/format";
import { plainReason } from "../../desk/surface/plainFailure";
import { useWindowInterior } from "../../desk/surface/interior";
import { useWindowBack } from "../../desk/surface/back";
import { useCompactViewport } from "../../desk/useCompactViewport";
import { spriteUrl } from "../../desk/sprites";
import { DecisionsRail, type RailDecision } from "../../desk/decisions/DecisionsRail";
import { DecisionComposer, type NewDecisionAbout } from "../../desk/decisions/Composer";
import * as hub from "../../desk/decisions/api";
import type { CoreProps } from "./core-types";
import "../../desk/decisions/decisions.css";

type Row = hub.LedgerRow;
type Rec = hub.DecisionRecord;
type Pick = { kind: "record"; id: string } | { kind: "meeting"; row: Row };

/** One page of the ledger. */
const PAGE = 100;
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const DECISION_SPRITE = `${import.meta.env.BASE_URL || "/_built/"}desk/sprites/decision.png`;

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
  useWindowInterior("list");
  const projects = useDesk((state) => state.projects);
  const recordScope = scope?.startsWith("record:") ? scope.slice("record:".length) : "";
  const decisionScope = scope?.startsWith("decision:") ? scope.slice("decision:".length) : "";
  const onlyRecords = scope?.startsWith("records:") ? scope.slice("records:".length).split(",").map((id) => id.trim()).filter(Boolean) : [];
  const composeScope = isNewDecisionScope(scope);
  const aboutId = composeScope && scope?.includes(":project:") ? scope.slice(scope.indexOf(":project:") + ":project:".length) : "";
  const about: NewDecisionAbout | null = aboutId
    ? { id: aboutId, name: scopeLabel || projects.find((item) => item.id === aboutId)?.name || "Project" }
    : null;

  const [query, setQuery] = useState("");
  const [current, setCurrent] = useState(scope === "current");
  const [rows, setRows] = useState<Row[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [more, setMore] = useState(false);
  const [error, setError] = useState("");
  const [picked, setPicked] = useState<Pick | null>(null);
  const [composing, setComposing] = useState(composeScope);
  const [pickError, setPickError] = useState("");

  // Reads can answer out of order: a read for an older search never lands,
  // and of two reads for the same search the later one wins.
  const reads = useRef({ query: 0, started: 0, landed: 0 });
  const beginRead = () => {
    const mine = { query: reads.current.query, order: ++reads.current.started };
    return () => {
      if (mine.query !== reads.current.query || mine.order < reads.current.landed) return false;
      reads.current.landed = mine.order;
      return true;
    };
  };
  const read = async (offset: number, limit = PAGE): Promise<{ rows: Row[]; total: number }> => {
    if (onlyRecords.length) {
      const found = await Promise.all(onlyRecords.map((id) => hub.readRecord(id).then((r) => (r?.id ? fromRecord(r) : null), () => null)));
      const kept = found.filter((row): row is Row => Boolean(row))
        .filter((row) => !current || ["decided", "committed", "proposed"].includes(standing(row)))
        .filter((row) => !query.trim() || row.text.toLowerCase().includes(query.trim().toLowerCase()));
      return { rows: offset ? [] : kept, total: kept.length };
    }
    const body = await hub.readLedger({ q: query, current, limit, offset });
    const page = Array.isArray(body?.decisions) ? body.decisions : [];
    return { rows: page, total: Number(body?.page?.total ?? page.length) };
  };
  const shown = useRef(0);
  shown.current = rows.length;
  useOnDeskChanged(() => {
    const lands = beginRead();
    void read(0, Math.min(500, Math.max(PAGE, shown.current)))
      .then((answer) => { if (lands()) { setRows(answer.rows); setTotal(answer.total); } })
      .catch(() => undefined);
  }, ["action", "action_item", "decision", "decision_record", "follow_through"]);
  useEffect(() => {
    let active = true;
    reads.current.query += 1;
    const timer = window.setTimeout(() => {
      setLoading(true);
      setError("");
      const lands = beginRead();
      void read(0)
        .then((answer) => { if (lands()) { setRows(answer.rows); setTotal(answer.total); } })
        .catch((reason) => { if (lands()) { setRows([]); setTotal(0); setError(readableError(reason)); } })
        .finally(() => { if (active) setLoading(false); });
    }, query.trim() ? 200 : 0);
    return () => { active = false; window.clearTimeout(timer); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, current, scope]);

  const showMore = () => {
    const lands = beginRead();
    setMore(true);
    void read(rows.length)
      .then((answer) => { if (lands()) { setRows((list) => [...list, ...answer.rows]); setTotal(answer.total); } })
      .catch((reason) => setError(readableError(reason)))
      .finally(() => setMore(false));
  };

  // The window's scope picks: a record, a meeting's decision (read by its id,
  // never found in the page), only some records (the first picked), the composer.
  const pickReads = useRef(0);
  useEffect(() => {
    setPickError("");
    setComposing(composeScope);
    if (composeScope) { setPicked(null); return; }
    if (recordScope) { setPicked({ kind: "record", id: recordScope }); return; }
    if (onlyRecords[0]) { setPicked({ kind: "record", id: onlyRecords[0] }); return; }
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
    if (row.record_id) setPicked({ kind: "record", id: row.record_id });
    else if (row.source === "desk") openRef(`desk_decision:${row.id}`);
    else setPicked({ kind: "meeting", row });
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
  // The first record is picked (Agents' way): the one that waits on him,
  // else the newest, so the mast, the spine and the ledger show at once. On
  // the phone the rail is the sheet until a pick.
  const pickable = (row: Row) => Boolean(row.record_id) || row.source === "meeting";
  const first = rows.find((row) => standing(row) === "proposed" && pickable(row)) ?? rows.find(pickable);
  const auto: Pick | null = !picked && !composing && !pickError && !loading && !compact && !decisionScope && first
    ? (first.record_id ? { kind: "record", id: first.record_id } : { kind: "meeting", row: first }) : null;
  const onFace = picked ?? auto;
  const away = Boolean(onFace || composing || pickError);
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
  const create = () => {
    const name = title.trim();
    if (!name) return;
    const reason = why.trim();
    forget();
    setComposing(false);
    void useDesk.getState().createPrimitive("decision", {
      title: name,
      ...(reason ? { why: reason } : {}),
      ...(about ? { project_id: about.id, project_name: about.name } : {}),
    });
  };
  const cancel = () => { forget(); back(); };

  const railRows: RailDecision[] = rows.map((row) => {
    const state = STANDING[standing(row)];
    return {
      key: rowKey(row), title: (row.text || "").trim() || "New decision", day: dayWords(row.decided_at),
      where: row.meeting_title || (row.source === "desk" ? "Desk" : row.meeting_id ? "Meeting" : ""),
      tone: state.tone, word: state.word,
    };
  });
  const byKey = new Map(rows.map((row) => [rowKey(row), row]));
  const pickedKey = onFace?.kind === "record" ? `record:${onFace.id}` : onFace?.kind === "meeting" ? rowKey(onFace.row) : null;
  const pickedRow = pickedKey ? byKey.get(pickedKey) ?? null : null;
  const proposed = rows.filter((row) => standing(row) === "proposed");
  const moreVerb = !loading && rows.length > 0 && rows.length < total ? (
    <Button variant="secondary" dense loading={more} onClick={showMore} className="decisions-rail-more" data-testid="decisions-more">
      {`Show more (${rows.length} of ${total})`}
    </Button>
  ) : null;

  let pane: ReactNode;
  if (composing) {
    pane = <div className="decisions-object"><DecisionComposer title={title} why={why} about={about} onTitle={setTitle} onWhy={setWhy} onCreate={create} onCancel={cancel} autoFocus /></div>;
  } else if (pickError) {
    pane = <SurfaceState error={pickError} />;
  } else if (onFace?.kind === "record") {
    pane = <RecordPane key={onFace.id} id={onFace.id} row={pickedRow} onOpenRecord={(id) => setPicked({ kind: "record", id })} />;
  } else if (onFace?.kind === "meeting") {
    pane = <MeetingDecisionPane row={onFace.row} />;
  } else if (loading) {
    pane = <Loading data-testid="decisions-loading" />;
  } else if (!rows.length && !error && !query.trim() && !current && !onlyRecords.length) {
    // No decisions at all: the plate is New decision itself.
    pane = <div className="decisions-object"><DecisionComposer title={title} why={why} onTitle={setTitle} onWhy={setWhy} onCreate={create} onCancel={forget} /></div>;
  } else {
    pane = <SurfaceState empty emptyLabel={query.trim() ? "No decisions match this search" : current ? "No current decisions" : countWords(total, "decision") ?? ""}
      emptyImage={DECISION_SPRITE} emptyKind="decision" />;
  }

  return (
    <div className="decisions-frame" data-testid="decisions-window" data-picked={away ? "" : undefined}>
      {error ? <SurfaceState error={error} /> : null}
      <div className="decisions-body">
        <DecisionsRail rows={railRows} picked={pickedKey} query={query} onQuery={setQuery} current={current} onCurrent={setCurrent}
          onPick={(key) => { const row = byKey.get(key); if (row) pickRow(row); }} onNew={startNew} composing={composing} more={moreVerb}
          head={onlyRecords.length ? <Button dense variant="secondary" onClick={back} data-testid="decisions-all">All decisions</Button> : null} />
        <div className="decisions-pane" data-testid="decisions-pane" aria-live="polite">
          {pane}
        </div>
      </div>
      {onFace ? null : <StatusBar
        data-testid="decisions-status"
        items={[
          { key: "count", text: countWords(total, "decision") },
          { key: "open", lamp: "ask" as const, text: countWords(proposed.length, "proposed", "proposed") },
        ]}
      />}
    </div>
  );
}

/** The plate (the language, 2026-11-08): the one raised thing of the face,
 *  the thing that matters now, with its verb. */
function Plate({ eyebrow, tone, title, facts, children, testId = "decisions-plate" }: {
  eyebrow: string; tone: SpineTone; title: ReactNode; facts?: ReactNode; children?: ReactNode; testId?: string;
}) {
  return <section className="decisions-plate" data-tone={tone} aria-label={eyebrow} data-testid={testId}>
    <span className="decisions-plate-eyebrow">{eyebrow}</span>
    <h3 className="decisions-plate-title">{title}</h3>
    {facts ? <p className="decisions-plate-facts">{facts}</p> : null}
    {children ? <div className="decisions-plate-verbs">{children}</div> : null}
  </section>;
}

/** One ledger section: a caption and its rows edge to edge. */
function Section({ caption, children, testId }: { caption: string; children: ReactNode; testId?: string }) {
  return <section className="decisions-section" aria-label={caption} data-testid={testId}>
    <h4 className="decisions-section-cap">{caption}</h4>
    {children}
  </section>;
}

/** A decision record as one object: mast, spine, plate, ledger; its verbs. */
function RecordPane({ id, row, onOpenRecord }: { id: string; row: Row | null; onOpenRecord(id: string): void }) {
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

  const deskId = record?.source_type === "desk" && record.source_id ? String(record.source_id) : "";
  const edit = useDeskDecisionEdit(deskId, () => load(true));
  // The window's Object menu is this decision's while the pane shows it.
  useEffect(() => { setDecisionReaderObject(deskId || null); return () => setDecisionReaderObject(null); }, [deskId]);
  const [sending, setSending] = useState(false);
  const [filing, setFiling] = useState(false);
  const [filed, setFiled] = useState("");
  const [writing, setWriting] = useState<"" | "accepted" | "deprecated" | "commit" | "resolve">("");
  const [writeFailure, setWriteFailure] = useState("");
  const [acceptedHere, setAcceptedHere] = useState(false);
  const [committedHere, setCommittedHere] = useState<string | null>(null);
  const { copy, receipt: copyReceipt } = useCopyReceipt();
  const items = useDesk((state) => state.items);

  const busy = Boolean(writing) || edit.saving;
  const writeStatus = async (next: "accepted" | "deprecated") => {
    if (!deskId || busy) return;
    setWriting(next);
    setWriteFailure("");
    setAcceptedHere(false);
    try {
      await hub.writeDecisionStatus(deskId, next);
      setAcceptedHere(next === "accepted");
      void useDesk.getState().refresh();
      load(true);
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
  const deleteDecision = () => {
    if (!deskId) return;
    const ctx = { selectedRef: `decision:${deskId}` };
    void import("../../desk/verbRegistry").then(({ verbById }) => {
      const verb = verbById("object.delete");
      if (!verb || verb.ghost(ctx)) return;
      useDesk.getState().closeSurfaceWindow("open-decisions");
      verb.run(ctx);
    });
  };

  if (loading || failure || !record) {
    return <div className="decisions-object" data-testid="decision-reader">
      {loading ? <Loading /> : <SurfaceState error={failure || "Decision unavailable."} onRetry={() => load()} />}
    </div>;
  }

  const name = (record.title || "").trim() || record.decision_text;
  const committedTo = record.committed_to || committedHere || row?.committed_to || null;
  const committed = Boolean(committedTo) || committedHere !== null || Boolean(row?.committed);
  const state = standing({ lifecycle: record.lifecycle, status: record.status, committed });
  const look = STANDING[state];
  const { about, why } = rationaleParts(record.rationale);
  const projectId = record.sources?.find((source) => source.source_type === "project")?.source_ref ?? "";
  const meetingSource = record.sources?.find((source) => source.meeting_id || source.source_type === "meeting");
  const from = row?.meeting_title || (meetingSource ? "a meeting" : record.source_type === "desk" ? "Desk" : "");
  const when = sinceWord(record.created_at);
  const facts = [when, from ? `from ${from}` : "", record.owner || ""].filter(Boolean);
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
  const leftOpen = (items.decision || []).filter((candidate) => candidate.id !== deskId && candidate.status === "proposed").length;
  const stateWords = writing === "accepted" ? "Deciding" : writing === "deprecated" ? "Retiring" : writing === "commit" ? "Committing"
    : edit.saving ? "Saving"
    : acceptedHere && decided ? `Decided · ${leftOpen > 0 ? `${leftOpen} proposed` : "all decided"}`
    : `${look.word}${decided && when ? ` ${when}` : ""}`;
  const words = [`# ${name}`, name !== record.decision_text.trim() ? record.decision_text : "", record.rationale || ""]
    .filter((part) => part.trim()).join("\n\n");
  const filingProps = {
    objectRef: qualifiedRef("decision", deskId), objectKind: "decision" as const, objectId: deskId, bare: true, onSummary: setFiled,
    projectRef: `decision_record:${record.id}`,
  };

  let plate: ReactNode = null;
  if (state === "proposed" && deskId) {
    plate = <Plate eyebrow="Waits on you" tone="brass" title="Proposed" facts={when}>
      <Button variant="primary" loading={writing === "accepted"} disabled={busy} onClick={() => void writeStatus("accepted")} data-testid="decision-reader-accept">
        <ToolGlyph kind="done" />Decide
      </Button>
    </Plate>;
  } else if (state === "decided") {
    plate = <Plate eyebrow="Decided" tone="steel" title={record.owner ? `Commit to ${record.owner}` : "Commit it"}>
      <Button variant="primary" loading={writing === "commit"} disabled={busy} onClick={() => void commit()} data-testid="decision-reader-commit">Commit</Button>
    </Plate>;
  } else if (state === "disputed") {
    plate = <Plate eyebrow="At risk" tone="coral" title="Disputed" facts={record.dispute_reason || undefined}>
      {deskId ? <Button variant="primary" loading={writing === "resolve"} disabled={busy} onClick={() => void resolve()} data-testid="decision-reader-resolve">Resolve</Button> : null}
    </Plate>;
  } else if (state === "superseded" && record.successor_id) {
    const next = record.successor_id;
    plate = <Plate eyebrow="Replaced" tone="graphite" title="Superseded">
      <Button variant="primary" onClick={() => onOpenRecord(next)} data-testid="decision-reader-successor">Open the new one</Button>
    </Plate>;
  }

  const verbs = edit.editing ? <>
    <Button dense variant="primary" disabled={busy} loading={edit.saving} onClick={() => void edit.commit()} data-testid="decision-reader-save">Save</Button>
    <Button dense variant="secondary" disabled={edit.saving} onClick={edit.cancel} data-testid="decision-reader-cancel">Cancel</Button>
  </> : <>
    {deskId ? <Button dense variant="secondary" loading={edit.opening} disabled={edit.opening} onClick={() => void edit.start()} data-testid="decision-reader-edit">
      <ToolGlyph kind="edit" />Edit
    </Button> : null}
    {state !== "proposed" ? <Button dense variant="secondary" aria-expanded={sending} onClick={() => setSending((open) => !open)} data-testid="decision-reader-send">
      <ToolGlyph kind="send" />Send…
    </Button> : null}
    {state !== "proposed" ? <RunAsProgramVerb variant="secondary" testId="decision-reader-program" title={name}
      origin={{ kind: "decision_record", id: record.id, title: name,
        goal: [record.decision_text, record.rationale].filter((part) => (part || "").trim()).join("\n\n"), projectId: projectId || null }} /> : null}
    <ToolbarFold foldAt="medium" data-testid="decision-reader-fold" verbs={[
      ...(decided && deskId ? [{ key: "retire", label: "Retire", testId: "decision-reader-retire", busy: writing === "deprecated", onSelect: () => void writeStatus("deprecated") }] : []),
      { key: "copy", label: "Copy", glyph: "copy" as const, testId: "decision-reader-copy", onSelect: () => void copy(words) },
      ...(deskId ? [{ key: "dictate", label: "Dictate about this", glyph: "record" as const, testId: "decision-reader-dictate",
        onSelect: () => openSurfaceOr("dictate", "/dictation", qualifiedRef("decision", deskId)) }] : []),
      ...(deskId ? [{ key: "delete", label: "Delete", testId: "decision-reader-delete", onSelect: deleteDecision }] : []),
    ]} />
  </>;

  const ledger = <>
    {name !== record.decision_text.trim() ? <Section caption="Decision"><Material className="decisions-words">{record.decision_text}</Material></Section> : null}
    {why ? <Section caption="Why"><Material className="decisions-words">{why}</Material></Section> : null}
    {about || record.alternatives || record.review_date ? <dl className="decisions-facts">
      {about ? <div><dt>About</dt><dd>{projectId ? (
        <Button dense variant="chrome" className="decisions-about" data-testid="decision-reader-about" onClick={() => openProjectRoom(projectId)}>
          <img src={spriteUrl("project", projectId, "rest", null, 20)} alt="" width={20} height={20} draggable={false} />{about}
        </Button>
      ) : <span className="decisions-about" data-testid="decision-reader-about">{about}</span>}</dd></div> : null}
      {record.alternatives ? <div><dt>Choices</dt><dd>{record.alternatives}</dd></div> : null}
      {record.review_date ? <div><dt>Review</dt><dd>{dayWords(record.review_date)}</dd></div> : null}
    </dl> : null}
    {evidence.length || record.work?.length ? <Section caption="Evidence" testId="decision-evidence">
      <SurfaceLedger>
        <ul className="surface-ledger-rows">
          {evidence.map((source, index) => <SurfaceLedgerRow key={`${source.source_type}-${source.source_ref}-${index}`} wrap expands={false}
            primary={<span className="decisions-quote">{source.speaker ? <b>{source.speaker}</b> : null}{source.text ? ` ${source.text}` : ""}</span>}
            trailing={sourceLabel(source) ? <Button dense variant="ghost" onClick={() => openSource(source)}>{sourceLabel(source)}</Button> : undefined} />)}
          {(record.work ?? []).map((work) => <SurfaceLedgerRow key={work.id} wrap expands={false}
            primary={`${workName(work.work_type)} · ${work.work_ref}`}
            trailing={<Button dense variant="ghost" aria-label={`Open ${workName(work.work_type)} · ${work.work_ref}`}
              onClick={() => useDesk.getState().openPullout(qualifiedRef(work.work_type, work.work_ref))}>{`Open ${workName(work.work_type)}`}</Button>} />)}
        </ul>
      </SurfaceLedger>
    </Section> : null}
    {committed ? <Section caption="Commitment" testId="decision-commitment">
      <SurfaceLedger><ul className="surface-ledger-rows">
        <SurfaceLedgerRow wrap expands={false} primary={committedTo || "Committed"} meta="Committed" metaTone="ok" />
      </ul></SurfaceLedger>
    </Section> : null}
    {record.predecessor_id || record.successor_id || record.revisions?.length ? <Section caption="History" testId="decision-history">
      <SurfaceLedger><ul className="surface-ledger-rows">
        {[...(record.revisions ?? [])].sort((a, b) => String(b.created_at).localeCompare(String(a.created_at))).map((revision) => (
          <SurfaceLedgerRow key={revision.id} wrap expands={false} time={dayWords(revision.created_at)}
            primary={`${revision.field_name.replace(/_/g, " ")}: ${revision.old_value || "—"} → ${revision.new_value || "—"}`} />
        ))}
      </ul></SurfaceLedger>
      <div className="decisions-lineage">
        {record.predecessor_id ? <Button dense variant="ghost" onClick={() => onOpenRecord(record.predecessor_id!)}>Previous decision</Button> : null}
        {record.successor_id ? <Button dense variant="ghost" onClick={() => onOpenRecord(record.successor_id!)}>Next decision</Button> : null}
      </div>
    </Section> : null}
    {filing && deskId ? <div className="decisions-filing" data-testid="decision-reader-filing"><DeskFilingStrip {...filingProps} /></div> : null}
  </>;

  return <div className="decisions-object" data-testid="decision-reader">
    <Mast kind="decision" id={record.id} title={<span data-testid="decision-reader-title">{name}</span>} data-testid="decision-mast"
      facts={<>
        <span>{facts.join(" · ")}</span>
        {committedTo ? <DotWord tone="ok" className="decisions-committed" data-testid="decision-reader-committed">{`Committed · ${committedTo}`}</DotWord> : null}
      </>}>
      {verbs}
    </Mast>
    <Spine className="decisions-spine" tone={look.tone} label={look.word} data-testid="decision-spine" />
    {edit.editing ? <DeskDecisionEditor edit={edit} />
      : sending ? <DecisionRecordSendSheet id={record.id} text={record.decision_text} onBack={() => setSending(false)} />
      : <>{plate}{ledger}</>}
    {deskId && !filing ? <span hidden aria-hidden="true"><DeskFilingStrip {...filingProps} /></span> : null}
    <StatusBar
      data-testid="decision-reader-status"
      items={[
        { key: "state", lamp: busy ? "info" : look.lamp, testId: "decision-reader-state", text: stateWords },
        writeFailure || edit.openFailure ? { key: "failure", lamp: "fail", text: writeFailure || edit.openFailure, testId: "decision-reader-failure" } : null,
        copyReceipt || edit.editing || edit.saved
          ? { key: "receipt", text: copyReceipt || (edit.editing ? "Draft kept" : "Saved"), testId: "decision-reader-receipt" } : null,
      ]}
      trailing={filed && deskId ? (
        <Button dense variant="ghost" aria-expanded={filing} onClick={() => setFiling((open) => !open)} data-testid="decision-reader-filed">
          {`Filed in: ${filed}`}
        </Button>
      ) : undefined}
    />
  </div>;
}

/** A meeting's decision with no record yet: its words, why, when and its meeting. */
function MeetingDecisionPane({ row }: { row: Row }) {
  const look = STANDING[standing(row)];
  const meetingId = (row.meeting_id ?? "").trim();
  const when = sinceWord(row.decided_at);
  return <div className="decisions-object" data-testid="decision-reader" data-from="meeting">
    <Mast kind="decision" id={row.id} title={<span data-testid="decision-reader-title">{row.text}</span>} data-testid="decision-mast"
      facts={[when, row.meeting_title ? `from ${row.meeting_title}` : "from a meeting"].filter(Boolean).join(" · ")}>
      {meetingId ? <Button dense variant="secondary" onClick={() => openRef(`meeting:${meetingId}`)} data-testid="decision-reader-meeting">
        <ToolGlyph kind="open" />Open meeting
      </Button> : null}
    </Mast>
    <Spine className="decisions-spine" tone={look.tone} label={look.word} />
    {row.rationale ? <Section caption="Why"><Material className="decisions-words">{row.rationale}</Material></Section> : null}
    <StatusBar data-testid="decision-reader-status" items={[
      { key: "state", lamp: look.lamp, text: look.word, testId: "decision-reader-state" },
      { key: "from", text: "From a meeting" },
    ]} />
  </div>;
}

