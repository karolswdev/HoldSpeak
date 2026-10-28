/** Decision pullout content (HS-117-15). */
import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { apiFetch, apiRequest } from "../../lib/api";
import { Button } from "../../components/signal/Signal";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { openIntelligence } from "../intelligenceNavigation";
import { qualifiedRef } from "../api";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { Material } from "../surface/Material";
import {
  SurfaceRow,
  SurfaceRows,
  SurfaceState,
} from "../surface/Surface";
import { humanTime } from "../surface/format";
import { FoldGadget, PadGadget } from "../surface/gadgets";
import { StatusBar, ToolGlyph, Toolbar, ToolbarFold } from "../surface/kit";
import { ActionNotice, StateChip } from "../surface";
import { currentWriteFailure, subscribeWriteFailure, writeFailureReason } from "../hooks/useWriteReceipt";
import type { PulloutContentProps } from "./types";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import { DeskDecisionSendSheet } from "../documentSendsLazy";
import { keptEditorPatch, keptField, updateKeptEditorFields } from "./editors/editorDraft";
import { DECISION_EDIT_EVENT as EDIT_EVENT, hasDecisionEditRequest, takeDecisionEditRequest as takeEditRequest } from "./decisionEdit";
import "./attention-records.css";
import "../../pages/cores/decisions.css";

/** The title createPrimitive("decision") gives (store/dataSlice.ts). */
export const DEFAULT_DECISION_TITLE = "New decision";

/** W1-TRUTH: one state word per decision, the same in the Decisions list
 *  (DecisionsView decisionState) and here. */
export const DECISION_STATES = [
  { value: "proposed", label: "Open" },
  { value: "accepted", label: "Accepted" },
  { value: "superseded", label: "Superseded" },
  { value: "deprecated", label: "Retired" },
  { value: "rejected", label: "Rejected" },
];
const DECISION_FIELDS = ["context_markdown", "decision_markdown", "consequences_markdown"] as const;
type DecisionField = typeof DECISION_FIELDS[number];

/** W6 (atlas pass 3, defect 11): the record's words in the reader's
 *  sections. The from-desk producer writes `About: …` into the background and
 *  `Why: …` into the consequences (decision_records.py create_from_desk);
 *  each goes under its own head, in the reader's order: About, Background,
 *  Why, Consequences. Any other words stay where they were written. */
export function decisionSections(context: string, consequences: string): {
  about: string; background: string; why: string; consequences: string;
} {
  const split = (text: string) => {
    let rest = String(text || "");
    let about = "";
    let why = "";
    rest = rest.replace(/(?:^|\n\n)\s*About:[ \t]*([^\n]*(?:\n(?!\s*Why:)(?!\n)[^\n]*)*)/i, (_, words: string) => {
      about = words.trim();
      return "";
    });
    rest = rest.replace(/(?:^|\n\n)\s*Why:\s*([\s\S]*)$/i, (_, words: string) => {
      why = words.trim();
      return "";
    });
    return { about, why, rest: rest.trim() };
  };
  const a = split(context);
  const b = split(consequences);
  return {
    about: a.about || b.about,
    background: a.rest,
    why: [a.why, b.why].filter(Boolean).join("\n\n"),
    consequences: b.rest,
  };
}

/** The decision's own words repeat its title (the from-desk producer writes
 *  the title as the decision text): the title bar says it once. */
export function repeatsTitle(body: string, title: string): boolean {
  const plain = (text: string) => String(text || "").replace(/^#+\s*/, "").trim().replace(/[.!]+$/, "").toLowerCase();
  return Boolean(plain(title)) && plain(body) === plain(title);
}

export function DecisionPullout({ object: o }: PulloutContentProps) {
  const items = useDesk((s) => s.items);
  const { openPullout } = useDesk.getState();
  if (o.ref.kind !== "decision") return null;
  const ir = o.ref;
  const [canonicalId, setCanonicalId] = useState<string | null>(null);
  useEffect(() => {
    let live = true;
    void apiFetch<Array<{ id?: string }>>(
      `/api/decision-records/source/desk/${encodeURIComponent(o.id)}`,
    ).then((records) => {
      const record = Array.isArray(records) ? records[0] : null;
      if (live && record?.id) setCanonicalId(String(record.id));
    }).catch(() => undefined);
    return () => { live = false; };
  }, [o.id]);
  const resourceRef = qualifiedRef(o.kind, o.id);
  const { copy, receipt: copyReceipt } = useCopyReceipt();
  const decisionContent = [
    `# Background\n\n${String(ir.contextMarkdown || "")}`,
    `# Decision\n\n${String(ir.decisionMarkdown || "")}`,
    `# Consequences\n\n${String(ir.consequencesMarkdown || "")}`,
  ].join("\n\n");

  // PHILO-3-01 — every draft starts from the current record, so an Edit
  // that opens by itself (a decision just created) never writes blanks
  // over saved text.
  const draftFromRecord = () => ({
    context_markdown: String(ir.contextMarkdown || ""),
    decision_markdown: String(ir.decisionMarkdown || ""),
    consequences_markdown: String(ir.consequencesMarkdown || ""),
  });
  const draftFromMemory = () => {
    const kept = keptEditorPatch("decision", o.id);
    const record = draftFromRecord();
    return {
      context_markdown: keptField(kept, "context_markdown", record.context_markdown),
      decision_markdown: keptField(kept, "decision_markdown", record.decision_markdown),
      consequences_markdown: keptField(kept, "consequences_markdown", record.consequences_markdown),
    };
  };
  // Reopening restores unsaved words without submitting them to the hub.
  const [editingDecision, setEditingDecision] = useState(() =>
    hasDecisionEditRequest(o.id) || useDesk.getState().newIds.includes(o.id) || DECISION_FIELDS.some((field) => field in keptEditorPatch("decision", o.id)),
  );
  const [decisionDraft, setDecisionDraft] = useState(draftFromMemory);
  const [savedDecision, setSavedDecision] = useState(false);
  const [savingDecision, setSavingDecision] = useState(false);
  const decisionWrite = useRef({ pending: false, generation: 0 });
  const draftVersion = useRef(0);
  const [sending, setSending] = useState(false);
  const [filing, setFiling] = useState(false);
  const [filed, setFiled] = useState("");
  const writeFailure = useSyncExternalStore(subscribeWriteFailure, currentWriteFailure, currentWriteFailure);
  const [savedStatus, setSavedStatus] = useState<string | null>(null);
  const [savingStatus, setSavingStatus] = useState(false);
  const [statusFailure, setStatusFailure] = useState("");
  const [retryStatus, setRetryStatus] = useState<string | null>(null);
  const statusWrite = useRef({ pending: false, generation: 0 });
  // DELIGHT 2 (small joys): an Accept pressed in this window makes the status
  // bar count what is left ("Accepted · 3 open"), from the desk's decisions.
  const [acceptedHere, setAcceptedHere] = useState(false);
  useEffect(() => {
    setSavedStatus(null);
  }, [o.id, ir.status]);
  useEffect(() => { setAcceptedHere(false); }, [o.id]);
  useEffect(() => () => { statusWrite.current.generation += 1; }, [o.id]);
  useEffect(() => () => { decisionWrite.current.generation += 1; }, [o.id]);
  useEffect(() => {
    if (editingDecision && !DECISION_FIELDS.some((field) => field in keptEditorPatch("decision", o.id))) {
      updateKeptEditorFields("decision", o.id, decisionDraft);
    }
  }, [o.id, editingDecision]);
  const status = savedStatus ?? String(ir.status || "proposed");
  const documentVersion = JSON.stringify([
    o.title, status, ir.deciders, ir.contextMarkdown, ir.decisionMarkdown,
    ir.consequencesMarkdown, ir.alternatives,
  ]);

  const startDecisionEdit = () => {
    draftVersion.current += 1;
    const draft = draftFromMemory();
    setDecisionDraft(draft);
    updateKeptEditorFields("decision", o.id, draft);
    setSavedDecision(false);
    setEditingDecision(true);
  };
  const startEditRef = useRef(startDecisionEdit);
  startEditRef.current = startDecisionEdit;
  useEffect(() => {
    // The request this window opened with is spent.
    takeEditRequest(o.id);
    const heard = (event: Event) => {
      if ((event as CustomEvent<string>).detail !== o.id || !takeEditRequest(o.id)) return;
      startEditRef.current();
    };
    window.addEventListener(EDIT_EVENT, heard);
    return () => window.removeEventListener(EDIT_EVENT, heard);
  }, [o.id]);
  const changeDecisionField = (field: DecisionField, value: string) => {
    draftVersion.current += 1;
    setDecisionDraft((current) => ({ ...current, [field]: value }));
    updateKeptEditorFields("decision", o.id, { [field]: value });
  };
  const cancelDecisionEdit = () => {
    updateKeptEditorFields("decision", o.id, {}, [...DECISION_FIELDS]);
    setEditingDecision(false);
  };
  const commitDecisionEdit = async () => {
    if (decisionWrite.current.pending || statusWrite.current.pending) return;
    decisionWrite.current.pending = true;
    const generation = decisionWrite.current.generation;
    const submittedVersion = draftVersion.current;
    setSavingDecision(true);
    // PHILO-3-01 — the default title yields to the first line of the
    // decision text, so the brief says "Review decision: <that line>".
    const firstLine = decisionDraft.decision_markdown
      .split("\n")
      .map((line) => line.replace(/^#+\s*/, "").trim())
      .find(Boolean);
    const title = String(o.title || "");
    const patch =
      firstLine && (!title || title === DEFAULT_DECISION_TITLE)
        ? { ...decisionDraft, title: firstLine.slice(0, 120) }
        : decisionDraft;
    try {
      const accepted = await useDesk.getState().updatePrimitive("decision", o.id, patch);
      // An acknowledgement can outlive this window. Only retire values this
      // exact request saved; a reopened editor may already have newer words.
      if (accepted) {
        const kept = keptEditorPatch("decision", o.id);
        updateKeptEditorFields("decision", o.id, {}, DECISION_FIELDS.filter((field) => kept[field] === patch[field]));
      }
      if (generation !== decisionWrite.current.generation) return;
      if (accepted && submittedVersion === draftVersion.current && !DECISION_FIELDS.some((field) => field in keptEditorPatch("decision", o.id))) {
        setEditingDecision(false);
        setSavedDecision(true);
      }
    } finally {
      decisionWrite.current.pending = false;
      if (generation === decisionWrite.current.generation) setSavingDecision(false);
    }
  };
  const writeStatus = async (next: string) => {
    if (statusWrite.current.pending || decisionWrite.current.pending || next === status) return;
    statusWrite.current.pending = true;
    const generation = statusWrite.current.generation;
    setSavingStatus(true);
    setStatusFailure("");
    setAcceptedHere(false);
    try {
      const response = await apiRequest(`/api/decisions/${encodeURIComponent(o.id)}/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: next }),
      });
      if (!response.ok) throw response;
      const body = await response.json();
      if (generation !== statusWrite.current.generation) return;
      const saved = String(body?.decision?.status ?? next);
      setSavedStatus(saved);
      setAcceptedHere(saved === "accepted");
      setRetryStatus(null);
      void useDesk.getState().refresh();
    } catch (cause) {
      if (generation !== statusWrite.current.generation) return;
      setStatusFailure(writeFailureReason(cause));
      setRetryStatus(next);
    } finally {
      statusWrite.current.pending = false;
      if (generation === statusWrite.current.generation) setSavingStatus(false);
    }
  };

  // W1-TRUTH (atlas 2026-10-27): the record on the reader grammar. Toolbar
  // (every verb), the decision as the reader's words (no box, no state cycle
  // at the top), the folds, and a status bar: the state as a dot and a word,
  // and where it is filed (a press opens the drawers and Projects).
  const stateWord = DECISION_STATES.find((entry) => entry.value === status)?.label ?? "Open";
  const stateTone = status === "accepted" ? "ok" : status === "proposed" ? "ask" : "info";
  // The receipt counts what is left: the other open decisions on the desk.
  // No counter of zero: the last one reads "all decided".
  const leftOpen = (items.decision || []).filter((candidate) => candidate.id !== o.id && candidate.status === "proposed").length;
  const acceptedWords = acceptedHere && status === "accepted"
    ? `Accepted · ${leftOpen > 0 ? `${leftOpen} open` : "all decided"}` : "";
  const receiptWords = copyReceipt || (editingDecision ? "Draft kept" : savedDecision ? "Saved" : "");
  const facts = [
    Array.isArray(ir.deciders) && ir.deciders.length ? ir.deciders.join(" · ") : "",
    ir.decidedAt ? humanTime(String(ir.decidedAt)) : "",
  ].filter(Boolean).join(" · ");
  return (
    <>
      <div className="desk-pullout-body desk-surface-body decision-reader-window" data-interior="editor" data-testid="desk-decision-reader">
        <Toolbar label="Decision" className="desk-decision-reader-toolbar" data-testid="desk-decision-toolbar">
          {editingDecision ? (
            <>
              <Button variant="primary" dense disabled={savingDecision || savingStatus} onClick={() => void commitDecisionEdit()}>Save</Button>
              <Button variant="secondary" dense disabled={savingDecision || savingStatus} onClick={cancelDecisionEdit}>Cancel</Button>
            </>
          ) : (
            <>
              <Button variant="primary" dense onClick={startDecisionEdit}><ToolGlyph kind="edit" />Edit</Button>
              {/* The state changes by a verb, never a cycle at the top: an
                  open decision is accepted; an accepted one can retire. */}
              {status === "proposed" ? (
                <Button variant="secondary" dense disabled={savingStatus || savingDecision} loading={savingStatus}
                  onClick={() => void writeStatus("accepted")} data-testid="desk-decision-accept">
                  <ToolGlyph kind="done" />Accept
                </Button>
              ) : status === "accepted" ? (
                <Button variant="ghost" dense disabled={savingStatus || savingDecision}
                  onClick={() => void writeStatus("deprecated")} data-testid="desk-decision-retire">
                  Retire
                </Button>
              ) : null}
              {/* W6 (atlas pass 3): every verb says its word. Send stays on
                  the band; on a narrow window Copy, Dictate and Open record
                  fold into More ▾ (the kit's ToolbarFold), never bare icons. */}
              <Button variant="secondary" dense aria-expanded={sending} onClick={() => setSending((open) => !open)} data-testid="desk-decision-send">
                <ToolGlyph kind="send" />Send…
              </Button>
              <ToolbarFold
                foldAt="medium"
                data-testid="desk-decision-fold"
                verbs={[
                  { key: "copy", label: "Copy", glyph: "copy", onSelect: () => void copy(decisionContent) },
                  { key: "dictate", label: "Dictate about this", glyph: "record", onSelect: () => openSurfaceOr("dictate", "/dictation", resourceRef) },
                  ...(canonicalId ? [{
                    key: "record", label: "Open record", glyph: "open" as const, testId: "desk-decision-open-record",
                    onSelect: () => openIntelligence({ view: "receipts", receiptId: canonicalId }),
                  }] : []),
                ]}
              />
            </>
          )}
        </Toolbar>
        <article className="decision-reader desk-decision-reader desk-decision-card" aria-label={String(o.title || "Decision")}>
          {sending && !editingDecision ? (
            <DeskDecisionSendSheet id={o.id} title={o.title} version={documentVersion} onBack={() => setSending(false)} />
          ) : (
            <>
              {statusFailure ? <div className="attention-record-feedback" title={statusFailure}>
                <SurfaceState error="Could not change the status. The decision is unchanged; choose a status again." />
                <Button dense variant="ghost" disabled={savingStatus || savingDecision} onClick={() => retryStatus && void writeStatus(retryStatus)}>Try again</Button>
              </div> : null}
              {editingDecision && writeFailure?.subject === resourceRef && writeFailure.verb === "SAVE" ? (
                <ActionNotice tone="danger" role="alert"><StateChip state="failure" label="Save failed" /><span>{o.title}</span></ActionNotice>
              ) : null}
              {editingDecision || (String(ir.decisionMarkdown || "").trim() && !repeatsTitle(String(ir.decisionMarkdown), String(o.title || ""))) ? (
                <section className={`desk-decision-main${editingDecision ? " desk-decision-editor" : ""}`} aria-label="Decision">
                  {editingDecision ? (
                    <PadGadget label="Decision" value={decisionDraft.decision_markdown} rows={6} autoGrow autoFocus
                      onChange={(value) => changeDecisionField("decision_markdown", value)} />
                  ) : <Material className="decision-reader-why">{String(ir.decisionMarkdown)}</Material>}
                </section>
              ) : null}
              {editingDecision ? ([
                ["context_markdown", "Background"],
                ["consequences_markdown", "Consequences"],
              ] as const).map(([field, label]) => (
                <FoldGadget key={field} title={label} open={Boolean(decisionDraft[field].trim())} className="attention-decision-support">
                  <PadGadget label={label} value={decisionDraft[field]} rows={3} autoGrow
                    onChange={(value) => changeDecisionField(field, value)} />
                </FoldGadget>
              )) : (() => {
                const parts = decisionSections(String(ir.contextMarkdown || ""), String(ir.consequencesMarkdown || ""));
                return ([
                  ["about", "About", parts.about],
                  ["background", "Background", parts.background],
                  ["why", "Why", parts.why],
                  ["consequences", "Consequences", parts.consequences],
                ] as const).map(([key, label, words]) => words ? (
                  <FoldGadget key={key} title={label} open className="attention-decision-support">
                    <Material>{words}</Material>
                  </FoldGadget>
                ) : null);
              })()}
              {Array.isArray(ir.alternatives) && ir.alternatives.length ? (
                <FoldGadget title="Alternatives considered">
                  <SurfaceRows>{ir.alternatives.map((alternative: any, index: number) => (
                    <SurfaceRow key={`${alternative.name}-${index}`} title={String(alternative.name || "Alternative")} detail={String(alternative.reason || "")} />
                  ))}</SurfaceRows>
                </FoldGadget>
              ) : null}
              {(items.decision || []).filter((candidate) => candidate.supersededBy === o.id).map((candidate) => (
                <Button key={candidate.id} variant="ghost" dense onClick={() => openPullout(String(candidate.id))}>
                  Previous decision · {String(candidate.title || "Decision")}
                </Button>
              ))}
              {ir.supersededBy ? (
                <Button variant="ghost" dense onClick={() => openPullout(String(ir.supersededBy))}>
                  Next decision{items.decision.find((candidate) => candidate.id === ir.supersededBy)?.title
                    ? ` · ${items.decision.find((candidate) => candidate.id === ir.supersededBy)!.title}` : ""}
                </Button>
              ) : null}
              {filing ? (
                <div className="desk-decision-filing" data-testid="desk-decision-filing">
                  <DeskFilingStrip objectRef={resourceRef} objectKind={o.kind} objectId={o.id} bare onSummary={setFiled} />
                </div>
              ) : null}
            </>
          )}
        </article>
        {filing ? null : (
          <span hidden aria-hidden="true">
            <DeskFilingStrip objectRef={resourceRef} objectKind={o.kind} objectId={o.id} bare onSummary={setFiled} />
          </span>
        )}
      </div>
      <StatusBar
        data-testid="desk-decision-status"
        items={[
          { key: "state", lamp: savingStatus || (editingDecision && savingDecision) ? "info" : stateTone, testId: "desk-decision-state",
            text: savingStatus ? "Saving" : editingDecision && savingDecision ? "Saving" : acceptedWords ? acceptedWords : facts ? `${stateWord} · ${facts}` : stateWord },
          receiptWords ? { key: "receipt", text: receiptWords } : null,
        ]}
        trailing={filed ? (
          <Button dense variant="ghost" aria-expanded={filing} onClick={() => setFiling((open) => !open)} data-testid="desk-decision-filed">
            {`Filed in: ${filed}`}
          </Button>
        ) : undefined}
      />
    </>
  );
}
