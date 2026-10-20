import { SurfaceFooter } from "../surface/SurfaceFooter";
/** Decision pullout content (HS-117-15). */
import { useEffect, useId, useRef, useState, useSyncExternalStore } from "react";
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
import { CycleGadget, FoldGadget, PadGadget } from "../surface/gadgets";
import { ActionNotice, StateChip } from "../surface";
import { currentWriteFailure, subscribeWriteFailure, writeFailureReason } from "../hooks/useWriteReceipt";
import type { PulloutContentProps } from "./types";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import { DeskDecisionSendWells } from "../documentSendsLazy";
import { keptEditorPatch, keptField, updateKeptEditorFields } from "./editors/editorDraft";
import "./attention-records.css";

/** The title createPrimitive("decision") gives (store/dataSlice.ts). */
export const DEFAULT_DECISION_TITLE = "New decision";

const DECISION_STATES = [
  { value: "proposed", label: "Proposed" },
  { value: "accepted", label: "Accepted" },
  { value: "superseded", label: "Replaced" },
  { value: "deprecated", label: "Retired" },
];
const DECISION_FIELDS = ["context_markdown", "decision_markdown", "consequences_markdown"] as const;
type DecisionField = typeof DECISION_FIELDS[number];

export function DecisionPullout({ object: o }: PulloutContentProps) {
  const items = useDesk((s) => s.items);
  const decisionHeading = useId();
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
    useDesk.getState().newIds.includes(o.id) || DECISION_FIELDS.some((field) => field in keptEditorPatch("decision", o.id)),
  );
  const [decisionDraft, setDecisionDraft] = useState(draftFromMemory);
  const [savedDecision, setSavedDecision] = useState(false);
  const [savingDecision, setSavingDecision] = useState(false);
  const decisionWrite = useRef({ pending: false, generation: 0 });
  const draftVersion = useRef(0);
  const writeFailure = useSyncExternalStore(subscribeWriteFailure, currentWriteFailure, currentWriteFailure);
  const [savedStatus, setSavedStatus] = useState<string | null>(null);
  const [savingStatus, setSavingStatus] = useState(false);
  const [statusFailure, setStatusFailure] = useState("");
  const [retryStatus, setRetryStatus] = useState<string | null>(null);
  const statusWrite = useRef({ pending: false, generation: 0 });
  useEffect(() => {
    setSavedStatus(null);
  }, [o.id, ir.status]);
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
    try {
      const response = await apiRequest(`/api/decisions/${encodeURIComponent(o.id)}/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: next }),
      });
      if (!response.ok) throw response;
      const body = await response.json();
      if (generation !== statusWrite.current.generation) return;
      setSavedStatus(String(body?.decision?.status ?? next));
      setRetryStatus(null);
      void useDesk.getState().refresh();
    } catch (cause) {
      if (generation !== statusWrite.current.generation) return;
      setStatusFailure(`STATUS FAILED · ${writeFailureReason(cause)}`);
      setRetryStatus(next);
    } finally {
      statusWrite.current.pending = false;
      if (generation === statusWrite.current.generation) setSavingStatus(false);
    }
  };

  return (
    <>
      <div className="desk-pullout-body desk-surface-body">
        <section className="desk-decision-card attention-decision">
          <div className="attention-decision-strip">
            <CycleGadget label="Decision status" value={status} options={DECISION_STATES}
              disabled={savingStatus || savingDecision} onChange={(next) => void writeStatus(next)} />
            {Array.isArray(ir.deciders) && ir.deciders.length ? <span className="attention-decision-fact">{ir.deciders.join(" · ")}</span> : null}
            {ir.decidedAt ? <span className="attention-decision-fact">{humanTime(String(ir.decidedAt))}</span> : null}
            {editingDecision ? <Button variant="ghost" dense disabled={savingDecision || savingStatus} onClick={cancelDecisionEdit}>Cancel</Button> : null}
          </div>
          {savingStatus ? <StateChip state="working" label="Saving status" /> : null}
          {statusFailure ? <div className="attention-record-feedback">
            <SurfaceState error={statusFailure} />
            <Button dense variant="ghost" disabled={savingStatus || savingDecision} onClick={() => retryStatus && void writeStatus(retryStatus)}>Retry</Button>
          </div> : null}
          {editingDecision && savingDecision ? <StateChip state="working" label="Saving decision" /> : null}
          {editingDecision && writeFailure?.subject === resourceRef && writeFailure.verb === "SAVE" ? (
            <ActionNotice tone="danger" role="alert"><StateChip state="failure" label="Save failed" /><span>{o.title}</span></ActionNotice>
          ) : null}
          {editingDecision || [ir.decisionMarkdown, ir.contextMarkdown, ir.consequencesMarkdown].some((value) => String(value || "").trim()) ? (
            <div className={`attention-decision-paper${editingDecision ? " desk-decision-editor" : ""}`}>
              {editingDecision || String(ir.decisionMarkdown || "").trim() ? (
                <section className="attention-decision-main" aria-labelledby={decisionHeading}>
                  <h2 id={decisionHeading}>Decision</h2>
                  {editingDecision ? (
                    <PadGadget label="Decision" value={decisionDraft.decision_markdown} rows={6} autoGrow autoFocus
                      onChange={(value) => changeDecisionField("decision_markdown", value)} />
                  ) : <Material>{String(ir.decisionMarkdown)}</Material>}
                </section>
              ) : null}
              {([
                ["context_markdown", "contextMarkdown", "Background"],
                ["consequences_markdown", "consequencesMarkdown", "Consequences"],
              ] as const).map(([field, recordField, label]) => (
                editingDecision || String(ir[recordField] || "").trim() ? (
                  <FoldGadget key={field} title={label} open={editingDecision ? Boolean(decisionDraft[field].trim()) : true} className="attention-decision-support">
                    {editingDecision ? (
                      <PadGadget label={label} value={decisionDraft[field]} rows={3} autoGrow
                        onChange={(value) => changeDecisionField(field, value)} />
                    ) : <Material>{String(ir[recordField])}</Material>}
                  </FoldGadget>
                ) : null
              ))}
            </div>
          ) : null}
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
          {canonicalId ? (
            <Button variant="ghost" dense onClick={() => openIntelligence({ view: "receipts", receiptId: canonicalId })}>
              Open canonical record
            </Button>
          ) : null}
          {editingDecision ? <FoldGadget title="More" className="attention-decision-support">
            <div className="attention-record-verbs">
              <Button variant="ghost" dense onClick={() => void copy(decisionContent)}>Copy</Button>
              <Button variant="ghost" dense onClick={() => openSurfaceOr("dictate", "/dictation", resourceRef)}>Dictate about this</Button>
            </div>
          </FoldGadget> : null}
          {!editingDecision ? <DeskDecisionSendWells id={o.id} title={o.title} version={documentVersion} /> : null}
        </section>
        <DeskFilingStrip
          objectRef={resourceRef}
          objectKind={o.kind}
          objectId={o.id}
        />
      </div>
      <SurfaceFooter receipt={copyReceipt || (editingDecision ? "Draft kept" : savedDecision ? "Saved" : DECISION_STATES.find((entry) => entry.value === status)?.label)} verbs={<>
        {!editingDecision ? <>
        <Button
          variant="ghost"
          dense
          onClick={() => void copy(decisionContent)}
        >
          Copy
        </Button>
        <Button
          variant="ghost"
          dense
          onClick={() =>
            openSurfaceOr("dictate", "/dictation", resourceRef)
          }
        >
          Dictate about this
        </Button>
        </> : null}
        {editingDecision ? (
          <>
            <Button variant="primary" dense disabled={savingDecision || savingStatus} onClick={() => void commitDecisionEdit()}>Save</Button>
          </>
        ) : (
          <Button variant="primary" dense onClick={startDecisionEdit}>Edit</Button>
        )} </>} />
    </>
  );
}
