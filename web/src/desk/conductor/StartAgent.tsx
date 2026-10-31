/** Betterment AG8: Start an agent, in place in Agents (agents/DESIGN.md §4,
 *  "The Agents window"). He says what it should do, picks the project and
 *  the agent, and presses Start: the hub files a note with his words in the
 *  project (`POST /api/notes`, `PUT /api/projects/{id}/resources/note:{id}`)
 *  and hands that note (`POST /api/agent/hand`), so the brief is grounded the
 *  same way as a hand from the work. At the limit the hand waits for a free
 *  agent (`queue: true`). Three presses: Start an agent, the words (or the
 *  mic), Start. */
import { useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { ApiError, apiFetch } from "../../lib/api";
import { ActionNotice, Disclosure, SurfaceWell } from "../surface";
import { CycleGadget, GadgetRow, StringGadget } from "../surface/gadgets";
import { AGENT_PROFILE, rememberAgent, rememberedAgent } from "../agentHand";
import { AGENT_NAME, type AgentId } from "../firstrun/agentsStep";
import { codeOf, refusalToken } from "../components/HandSheet";
import { useDesk } from "../store";
import {
  captureWorkspaceHandoff,
  readWorkspaceHandoffDraft,
  workspaceHandoffScope,
  workspaceHandoffSourceWords,
  workspaceHandoffWords,
  writeWorkspaceHandoffDraft,
  type WorkspaceHandoffPreparation,
} from "../terminals/workspaceHandoff";

interface ProjectRow {
  id: string;
  name: string;
}

const AGENTS: readonly AgentId[] = ["claude", "codex", "pi"];
const REVIEW_BY = [
  { value: "none", label: "None" },
  { value: "codex", label: "Codex" },
  { value: "claude", label: "Claude Code" },
  { value: "pi", label: "pi" },
] as const;
const PROJECT_KEY = "hs.agents.start.project";

interface StartIntent {
  words: string;
  preparedWords: string;
  projectId: string;
  scope: string;
  noteId: string;
  filed: boolean;
}

function rememberedProject(): string {
  try {
    return localStorage.getItem(PROJECT_KEY) ?? "";
  } catch {
    return "";
  }
}

/** The note's title: his first line, cut at a word under 80 characters. */
export function noteTitle(words: string): string {
  const line = words.trim().split(/\n/)[0].trim();
  if (line.length <= 80) return line;
  const cut = line.slice(0, 80);
  return `${cut.slice(0, Math.max(cut.lastIndexOf(" "), 40)).trim()}…`;
}

/** The refusal in his words: the hand's own token, else the step that failed. */
function failureWords(step: "note" | "file" | "hand", error: unknown, agent: AgentId): string {
  const code = codeOf(error);
  if (step === "hand") return `Not started · ${refusalToken(code, agent)}`;
  const status = error instanceof ApiError ? ` · ${error.status}` : "";
  return step === "note" ? `The note was not made${status}` : `The note was not filed in the project${status}`;
}

export interface StartAgentProps {
  /** The new agent's row (`launch:<id>` or `queue:<id>`), or null. */
  onStarted(row: string | null, context?: { projectId: string; noteId: string; agent: AgentId; reviewBy: string; requestEpoch?: number }): void;
  onStarting?(): number | void;
  onCancel(): void;
  initialProjectId?: string | null;
  /**
   * Optional workspace preparation. Canonical Desk objects use the existing
   * Hand sheet; this additive path is for a file read in the workspace.
   */
  preparation?: WorkspaceHandoffPreparation | null;
}

export function StartAgent({ onStarted, onStarting, onCancel, initialProjectId, preparation = null }: StartAgentProps) {
  const preparationContext = preparation?.context ?? null;
  const projectLocked = Boolean(preparation && (preparationContext?.project?.id || initialProjectId));
  const suppliedProjectId = preparationContext?.project?.id ?? initialProjectId ?? null;
  const [projects, setProjects] = useState<ProjectRow[] | null>(null);
  const [projectsError, setProjectsError] = useState<string | null>(null);
  const [projectReadNonce, setProjectReadNonce] = useState(0);
  const [projectId, setProjectId] = useState(() => preparationContext?.project?.id ?? initialProjectId ?? "");
  const draftProjectId = (preparationContext?.project?.id ?? projectId) || initialProjectId;
  const draftKey = workspaceHandoffScope(preparationContext, draftProjectId);
  const retainedDraft = useDesk((state) => state.drafts[draftKey] ?? "");
  const retainedRecord = readWorkspaceHandoffDraft(retainedDraft);
  const setDeskDraft = useDesk((state) => state.setDraft);
  const [words, setWords] = useState(() => retainedRecord ? retainedRecord.words : (preparation?.words ?? ""));
  const [agent, setAgent] = useState<AgentId>("claude");
  const [reviewBy, setReviewBy] = useState("none");
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);
  const projectTouched = useRef(false);
  const agentTouched = useRef(false);
  const draftScope = useRef(draftKey);
  const wordsValue = useRef(words);
  const wordsTouched = useRef(Boolean(retainedRecord));
  const intent = useRef<StartIntent | null>(retainedRecord?.noteId && retainedRecord.scope && retainedRecord.projectId
    ? {
      words: retainedRecord.words.trim(),
      preparedWords: retainedRecord.preparedWords ?? workspaceHandoffWords(retainedRecord.words, preparationContext),
      projectId: retainedRecord.projectId,
      scope: retainedRecord.scope,
      noteId: retainedRecord.noteId,
      filed: retainedRecord.filed === true,
    }
    : null);

  // A wing change selects a new scope. Restore that scope's existing Desk
  // draft, but never let the late project read overwrite owner typing.
  useEffect(() => {
    if (draftScope.current === draftKey) return;
    const lateProjectRead = !projectTouched.current && !preparationContext?.project?.id;
    const typedBeforeRead = lateProjectRead && wordsTouched.current;
    const previousDraftKey = draftScope.current;
    draftScope.current = draftKey;
    if (typedBeforeRead && !retainedRecord) {
      // The project list answered after the owner typed. Keep those words and
      // move the same draft into the now-known Project scope; never lose them
      // to a late default read.
      const previousDraft = readWorkspaceHandoffDraft(useDesk.getState().drafts[previousDraftKey]);
      if (previousDraft?.words === wordsValue.current) setDeskDraft(previousDraftKey, null);
      setDeskDraft(draftKey, writeWorkspaceHandoffDraft({ words: wordsValue.current }));
    } else {
      wordsTouched.current = Boolean(retainedRecord);
      wordsValue.current = retainedRecord ? retainedRecord.words : (preparation?.words ?? "");
      setWords(wordsValue.current);
    }
    setFailure(null);
  }, [draftKey, preparation?.words, preparationContext?.project?.id, retainedRecord?.words, setDeskDraft]);

  useEffect(() => {
    if (draftScope.current === draftKey && retainedRecord && !wordsTouched.current) {
      wordsValue.current = retainedRecord.words;
      setWords(retainedRecord.words);
    }
  }, [draftKey, retainedRecord?.words]);

  useEffect(() => {
    let live = true;
    setProjects(null);
    setProjectsError(null);
    apiFetch<{ projects?: Array<Record<string, unknown>> }>("/api/projects")
      .then((answer) => {
        if (!live) return;
        const rows = (answer?.projects ?? [])
          .filter((p) => p && p.id && !p.archived)
          .map((p) => ({ id: String(p.id), name: String(p.name ?? p.id) }));
        setProjects(rows);
        const remembered = rememberedProject();
        const pick = projectLocked
          ? rows.find((p) => p.id === suppliedProjectId)?.id ?? ""
          : rows.find((p) => p.id === suppliedProjectId)?.id
            ?? rows.find((p) => p.id === remembered)?.id
            ?? rows[0]?.id
            ?? "";
        if (!projectTouched.current) setProjectId(pick);
        if (!agentTouched.current && !projectTouched.current) setAgent(rememberedAgent(pick) ?? "claude");
      })
      .catch(() => {
        if (live) {
          setProjects([]);
          setProjectsError("Project list not available");
        }
      });
    return () => {
      live = false;
    };
  }, [initialProjectId, preparation?.context.project?.id, projectLocked, suppliedProjectId, projectReadNonce]);

  const start = async () => {
    const capturedDraft = words;
    const text = capturedDraft.trim();
    const projectReady = projects !== null
      && projects.some((project) => project.id === projectId)
      && (!projectLocked || projectId === suppliedProjectId);
    if (!text || !projectReady || busy) return;
    const requestEpoch = onStarting?.();
    // Capture every mutable input before the first await. A selection or
    // project read that changes while the hub works must not retarget this
    // hand, and a retry must compare the same captured scope.
    const capturedContext = captureWorkspaceHandoff(preparationContext);
    const preparedWords = workspaceHandoffWords(text, capturedContext);
    const capturedProjectId = projectId;
    const capturedScope = workspaceHandoffScope(capturedContext, capturedProjectId);
    const mayWriteCapturedDraft = () => {
      const current = readWorkspaceHandoffDraft(useDesk.getState().drafts[draftKey]);
      return !current || (current.words === capturedDraft && (!current.scope || current.scope === capturedScope));
    };
    setBusy(true);
    setFailure(null);
    let step: "note" | "file" | "hand" = "note";
    try {
      const previous = intent.current;
      const reusable = previous
        && previous.words === text
        && previous.preparedWords === preparedWords
        && previous.projectId === capturedProjectId
        && previous.scope === capturedScope
        ? previous
        : null;
      let noteId = reusable?.noteId ?? "";
      let filed = reusable?.filed ?? false;
      if (!noteId) {
        const made = await apiFetch<{ note?: { note_id?: string; id?: string } }>("/api/notes", {
          method: "POST",
          json: { title: noteTitle(text), body_markdown: preparedWords, tags: ["agent"] },
        });
        noteId = String(made?.note?.note_id ?? made?.note?.id ?? "");
        if (!noteId) throw new Error("The hub did not return a note");
        intent.current = { words: text, preparedWords, projectId: capturedProjectId, scope: capturedScope, noteId, filed: false };
        if (mayWriteCapturedDraft()) setDeskDraft(draftKey, writeWorkspaceHandoffDraft({
          words: capturedDraft, preparedWords, projectId: capturedProjectId, scope: capturedScope, noteId,
        }));
      }
      if (!filed) {
        step = "file";
        await apiFetch(`/api/projects/${encodeURIComponent(capturedProjectId)}/resources/${encodeURIComponent(`note:${noteId}`)}`, {
          method: "PUT",
          json: {},
        });
        filed = true;
        intent.current = { words: text, preparedWords, projectId: capturedProjectId, scope: capturedScope, noteId, filed: true };
        if (mayWriteCapturedDraft()) setDeskDraft(draftKey, writeWorkspaceHandoffDraft({
          words: capturedDraft, preparedWords, projectId: capturedProjectId, scope: capturedScope, noteId, filed: true,
        }));
      }
      step = "hand";
      const answer = await apiFetch<{ launch_id?: string; queue_id?: string }>("/api/agent/hand", {
        method: "POST",
        json: { kind: "note", id: noteId, profile: AGENT_PROFILE[agent], project_id: capturedProjectId, queue: true, review_by: reviewBy },
      });
      intent.current = null;
      const acknowledgedDraft = readWorkspaceHandoffDraft(useDesk.getState().drafts[draftKey]);
      if (acknowledgedDraft?.words === capturedDraft
        && (!acknowledgedDraft.scope || acknowledgedDraft.scope === capturedScope)
        && (!acknowledgedDraft.noteId || acknowledgedDraft.noteId === noteId))
        setDeskDraft(draftKey, null);
      try {
        localStorage.setItem(PROJECT_KEY, capturedProjectId);
      } catch {
        /* a per-viewer convenience */
      }
      rememberAgent(capturedProjectId, agent);
      onStarted(
        answer?.launch_id ? `launch:${answer.launch_id}` : answer?.queue_id ? `queue:${answer.queue_id}` : null,
        { projectId: capturedProjectId, noteId, agent, reviewBy, ...(typeof requestEpoch === "number" ? { requestEpoch } : {}) },
      );
    } catch (error) {
      setFailure(failureWords(step, error, agent));
    } finally {
      setBusy(false);
    }
  };

  const noProject = projects !== null && projects.length === 0 && !projectsError;
  const projectUnavailable = projectLocked && projects !== null && Boolean(suppliedProjectId) && !projects.some((project) => project.id === suppliedProjectId);
  const projectSelectionValid = projects !== null
    && projects.some((project) => project.id === projectId)
    && (!projectLocked || projectId === suppliedProjectId);
  return (
    <section className="cw-section cw-start" data-testid="conductor-start-form" aria-label="Start an agent">
      <GadgetRow label="What should it do?" wide>
        <StringGadget
          label="What should it do?"
          value={words}
          onChange={(next) => {
            wordsTouched.current = true;
            wordsValue.current = next;
            setWords(next);
            intent.current = null;
            setDeskDraft(draftKey, writeWorkspaceHandoffDraft({ words: next }));
          }}
          placeholder="Say or type the work"
          micLabel="Speak the work"
          autoFocus
          disabled={busy}
          inputProps={{ "data-testid": "conductor-start-words" } as Record<string, string>}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.nativeEvent.isComposing) {
              event.preventDefault();
              void start();
            }
          }}
        />
      </GadgetRow>
      {preparationContext?.source ? (
        <SurfaceWell head={<span>Reference file</span>}>
          <div className="cw-start-context" data-testid="conductor-start-context">
            <span className="cw-start-context-summary" data-testid="conductor-start-source">{workspaceHandoffSourceWords(preparationContext)}</span>
            <span className="cw-start-context-meta">
              {preparationContext.worktree ? `Captured ${preparationContext.worktree.branch || preparationContext.worktree.id}` : null}
              {preparationContext.file?.content != null ? " · Read copy" : null}
            </span>
            <Disclosure label="Source context" variant="dense" ariaLabel="Source context">
              <pre className="cw-start-context-preview" data-testid="conductor-start-context-preview">{workspaceHandoffWords(words, preparationContext)}</pre>
            </Disclosure>
          </div>
        </SurfaceWell>
      ) : null}
      <GadgetRow label="Project">
        {projectsError ? (
          <span className="cw-start-none" role="alert" data-testid="conductor-start-project-read-error">
            {projectsError}. <Button dense variant="ghost" onClick={() => setProjectReadNonce((value) => value + 1)}>Retry</Button>
          </span>
        ) : noProject ? (
          <span className="cw-start-none">No project yet</span>
        ) : projectUnavailable ? (
          <span className="cw-start-none" role="alert" data-testid="conductor-start-project-unavailable">Project unavailable · Task kept · Cancel, choose a Project</span>
        ) : (
          <CycleGadget
            label="Project"
            value={projectId}
            options={(projects ?? []).map((p) => ({ value: p.id, label: p.name }))}
            onChange={(next) => {
              projectTouched.current = true;
              setProjectId(next);
              agentTouched.current = true;
              setAgent(rememberedAgent(next) ?? agent);
            }}
            disabled={busy || projects === null || projectLocked}
          />
        )}
      </GadgetRow>
      <GadgetRow label="Agent">
        <CycleGadget
          label="Agent"
          value={agent}
          options={AGENTS.map((id) => ({ value: id, label: AGENT_NAME[id] }))}
          onChange={(next) => {
            agentTouched.current = true;
            setAgent(next as AgentId);
          }}
          disabled={busy}
        />
      </GadgetRow>
      <GadgetRow label="Review by">
        <CycleGadget
          label="Review by"
          value={reviewBy}
          options={REVIEW_BY.map((choice) => ({ value: choice.value, label: choice.label }))}
          onChange={setReviewBy}
          disabled={busy}
        />
      </GadgetRow>
      {failure ? (
        <ActionNotice tone="danger" role="alert">
          {failure}
        </ActionNotice>
      ) : null}
      <div className="cw-start-verbs">
        <Button dense variant="ghost" disabled={busy} onClick={onCancel}>
          Cancel
        </Button>
        <Button
          dense
          variant="primary"
          loading={busy}
          disabled={!words.trim() || !projectSelectionValid || projectUnavailable}
          onClick={() => void start()}
          data-testid="conductor-start-go"
        >
          Start
        </Button>
      </div>
    </section>
  );
}
