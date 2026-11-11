/** The one decision face (2026-11-08): a Desk decision is edited in its
 *  record's reader in the Decisions window. This is the editor the Decision
 *  pullout had (parked: pullouts/_parked/DecisionPullout.tsx), moved: the draft
 *  is kept per decision until the hub accepts the save, one write runs at a
 *  time, and the default title yields to the first line of the decision. */
import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { apiFetch } from "../../../lib/api";
import { useDesk } from "../../store";
import { qualifiedRef } from "../../api";
import { ActionNotice, PaneInspector, InspectorForm, PadGadget, StateChip } from "../../surface";
import { plainReason } from "../../surface/plainFailure";
import { currentWriteFailure, subscribeWriteFailure } from "../../hooks/useWriteReceipt";
import { keptEditorPatch, keptField, updateKeptEditorFields } from "../editors/editorDraft";

/** The title createPrimitive("decision") gives (store/dataSlice.ts). */
export const DEFAULT_DECISION_TITLE = "New decision";

const FIELDS = ["context_markdown", "decision_markdown", "consequences_markdown"] as const;
type Field = typeof FIELDS[number];
type Draft = Record<Field, string>;
type DeskRow = {
  title?: string | null;
  context_markdown?: string | null;
  decision_markdown?: string | null;
  consequences_markdown?: string | null;
};

const EMPTY: Draft = { context_markdown: "", decision_markdown: "", consequences_markdown: "" };

/** The Desk decision's saved words: the desk's own item when it holds one,
 *  else the hub's read of that decision. */
async function readDeskDecision(id: string): Promise<{ title: string; draft: Draft }> {
  const item = (useDesk.getState().items.decision || []).find((candidate) => candidate.id === id);
  const row: DeskRow = item
    ? {
      title: item.title,
      context_markdown: item.contextMarkdown,
      decision_markdown: item.decisionMarkdown,
      consequences_markdown: item.consequencesMarkdown,
    }
    : (await apiFetch<{ decision?: DeskRow }>(`/api/decisions/${encodeURIComponent(id)}`))?.decision ?? {};
  return {
    title: String(row.title || ""),
    draft: {
      context_markdown: String(row.context_markdown || ""),
      decision_markdown: String(row.decision_markdown || ""),
      consequences_markdown: String(row.consequences_markdown || ""),
    },
  };
}

export type DeskDecisionEdit = ReturnType<typeof useDeskDecisionEdit>;

/** The editor's state for one Desk decision. `onSaved` runs after the hub
 *  accepts a save (the reader reads its record again). */
export function useDeskDecisionEdit(deskId: string, onSaved: () => void) {
  const [editing, setEditing] = useState(false);
  const [opening, setOpening] = useState(false);
  const [openFailure, setOpenFailure] = useState("");
  const [draft, setDraft] = useState<Draft>(EMPTY);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const title = useRef("");
  const write = useRef({ pending: false, generation: 0 });
  const opens = useRef(0);
  const draftVersion = useRef(0);
  const savedRef = useRef(onSaved);
  savedRef.current = onSaved;
  const resourceRef = deskId ? qualifiedRef("decision", deskId) : "";

  // Every draft starts from the saved decision; words kept from an earlier
  // edit (a closed window, a reload) come back over it, never sent by
  // themselves.
  const start = async () => {
    if (!deskId) return;
    const mine = ++opens.current;
    setOpening(true);
    setOpenFailure("");
    try {
      const saved = await readDeskDecision(deskId);
      if (mine !== opens.current) return;
      const kept = keptEditorPatch("decision", deskId);
      const next: Draft = {
        context_markdown: keptField(kept, "context_markdown", saved.draft.context_markdown),
        decision_markdown: keptField(kept, "decision_markdown", saved.draft.decision_markdown),
        consequences_markdown: keptField(kept, "consequences_markdown", saved.draft.consequences_markdown),
      };
      title.current = saved.title;
      draftVersion.current += 1;
      setDraft(next);
      updateKeptEditorFields("decision", deskId, next);
      setSaved(false);
      setEditing(true);
    } catch (cause) {
      if (mine === opens.current) setOpenFailure(`Could not open the editor · ${plainReason(cause)}`);
    } finally {
      if (mine === opens.current) setOpening(false);
    }
  };
  const startRef = useRef(start);
  startRef.current = start;

  useEffect(() => {
    setEditing(false);
    setSaved(false);
    setSaving(false);
    setOpenFailure("");
    // Reopening restores unsaved words without submitting them to the hub.
    if (deskId && FIELDS.some((field) => field in keptEditorPatch("decision", deskId))) void startRef.current();
    return () => {
      opens.current += 1;
      write.current.generation += 1;
    };
  }, [deskId]);

  const change = (field: Field, value: string) => {
    draftVersion.current += 1;
    setDraft((current) => ({ ...current, [field]: value }));
    updateKeptEditorFields("decision", deskId, { [field]: value });
  };
  const cancel = () => {
    opens.current += 1;
    updateKeptEditorFields("decision", deskId, {}, [...FIELDS]);
    setEditing(false);
    setOpening(false);
  };
  const commit = async () => {
    if (write.current.pending || !deskId) return;
    write.current.pending = true;
    const generation = write.current.generation;
    const submittedVersion = draftVersion.current;
    setSaving(true);
    // PHILO-3-01: the default title yields to the first line of the
    // decision text, so the brief says "Review decision: <that line>".
    const firstLine = draft.decision_markdown
      .split("\n")
      .map((line) => line.replace(/^#+\s*/, "").trim())
      .find(Boolean);
    const named = title.current;
    const patch: Record<string, string> = firstLine && (!named || named === DEFAULT_DECISION_TITLE)
      ? { ...draft, title: firstLine.slice(0, 120) }
      : { ...draft };
    try {
      const accepted = await useDesk.getState().updatePrimitive("decision", deskId, patch);
      // An acknowledgement can outlive this reader. Only retire values this
      // exact request saved; a reopened editor may already have newer words.
      if (accepted) {
        const kept = keptEditorPatch("decision", deskId);
        updateKeptEditorFields("decision", deskId, {}, FIELDS.filter((field) => kept[field] === patch[field]));
        if (patch.title) title.current = patch.title;
      }
      if (generation !== write.current.generation) return;
      if (accepted && submittedVersion === draftVersion.current
        && !FIELDS.some((field) => field in keptEditorPatch("decision", deskId))) {
        setEditing(false);
        setSaved(true);
        savedRef.current();
      }
    } finally {
      write.current.pending = false;
      if (generation === write.current.generation) setSaving(false);
    }
  };

  return { deskId, resourceRef, editing, opening, openFailure, draft, saving, saved, start, change, cancel, commit };
}

/** The editor body: the decision first, Background and Consequences as
 *  folds (open when they hold words). */
export function DeskDecisionEditor({ edit }: { edit: DeskDecisionEdit }) {
  const writeFailure = useSyncExternalStore(subscribeWriteFailure, currentWriteFailure, currentWriteFailure);
  return <PaneInspector label="Edit decision"><InspectorForm testId="decision-reader-editor"
    rows={[
      {label:"Decision",control:<PadGadget label="Decision" value={edit.draft.decision_markdown} rows={6} autoFocus onChange={value => edit.change("decision_markdown",value)} />},
      {label:"Background",control:<PadGadget label="Background" value={edit.draft.context_markdown} rows={3} onChange={value => edit.change("context_markdown",value)} />},
      {label:"Consequences",control:<PadGadget label="Consequences" value={edit.draft.consequences_markdown} rows={3} onChange={value => edit.change("consequences_markdown",value)} />},
    ]}
    notice={writeFailure?.subject === edit.resourceRef && writeFailure.verb === "SAVE" ? <ActionNotice tone="danger" role="alert"><StateChip state="failure" label="Save failed" /></ActionNotice> : null}
    completion={{cancel:edit.cancel,cancelDisabled:edit.saving,cancelTestId:"decision-reader-cancel",primary:{label:"Save",run:() => void edit.commit(),busy:edit.saving,testId:"decision-reader-save"}}}
  /></PaneInspector>;
}
