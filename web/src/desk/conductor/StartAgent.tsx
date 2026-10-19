/** Betterment AG8: Start an agent, in place in Agents (agents/DESIGN.md §4,
 *  "The Agents window"). He says what it should do, picks the project and
 *  the agent, and presses Start: the hub files a note with his words in the
 *  project (`POST /api/notes`, `PUT /api/projects/{id}/resources/note:{id}`)
 *  and hands that note (`POST /api/agent/hand`), so the brief is grounded the
 *  same way as a hand from the work. At the limit the hand waits for a free
 *  agent (`queue: true`). Three presses: Start an agent, the words (or the
 *  mic), Start. */
import { useEffect, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { ApiError, apiFetch } from "../../lib/api";
import { ActionNotice } from "../surface";
import { CycleGadget, GadgetRow, StringGadget } from "../surface/gadgets";
import { AGENT_PROFILE, rememberAgent, rememberedAgent } from "../agentHand";
import { AGENT_NAME, type AgentId } from "../firstrun/agentsStep";
import { codeOf, refusalToken } from "../components/HandSheet";

interface ProjectRow {
  id: string;
  name: string;
}

const AGENTS: readonly AgentId[] = ["claude", "codex", "pi"];
const PROJECT_KEY = "hs.agents.start.project";

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

export function StartAgent({ onStarted, onCancel }: {
  /** The new agent's row (`launch:<id>` or `queue:<id>`), or null. */
  onStarted(row: string | null): void;
  onCancel(): void;
}) {
  const [words, setWords] = useState("");
  const [projects, setProjects] = useState<ProjectRow[] | null>(null);
  const [projectId, setProjectId] = useState("");
  const [agent, setAgent] = useState<AgentId>("claude");
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    apiFetch<{ projects?: Array<Record<string, unknown>> }>("/api/projects")
      .then((answer) => {
        if (!live) return;
        const rows = (answer?.projects ?? [])
          .filter((p) => p && p.id && !p.archived)
          .map((p) => ({ id: String(p.id), name: String(p.name ?? p.id) }));
        setProjects(rows);
        const remembered = rememberedProject();
        const pick = rows.find((p) => p.id === remembered)?.id ?? rows[0]?.id ?? "";
        setProjectId(pick);
        setAgent(rememberedAgent(pick) ?? "claude");
      })
      .catch(() => {
        if (live) setProjects([]);
      });
    return () => {
      live = false;
    };
  }, []);

  const start = async () => {
    const text = words.trim();
    if (!text || !projectId || busy) return;
    setBusy(true);
    setFailure(null);
    let step: "note" | "file" | "hand" = "note";
    try {
      const made = await apiFetch<{ note?: { note_id?: string; id?: string } }>("/api/notes", {
        method: "POST",
        json: { title: noteTitle(text), body_markdown: text, tags: ["agent"] },
      });
      const noteId = String(made?.note?.note_id ?? made?.note?.id ?? "");
      step = "file";
      await apiFetch(`/api/projects/${encodeURIComponent(projectId)}/resources/${encodeURIComponent(`note:${noteId}`)}`, {
        method: "PUT",
        json: {},
      });
      step = "hand";
      const answer = await apiFetch<{ launch_id?: string; queue_id?: string }>("/api/agent/hand", {
        method: "POST",
        json: { kind: "note", id: noteId, profile: AGENT_PROFILE[agent], project_id: projectId, queue: true },
      });
      try {
        localStorage.setItem(PROJECT_KEY, projectId);
      } catch {
        /* a per-viewer convenience */
      }
      rememberAgent(projectId, agent);
      onStarted(answer?.launch_id ? `launch:${answer.launch_id}` : answer?.queue_id ? `queue:${answer.queue_id}` : null);
    } catch (error) {
      setFailure(failureWords(step, error, agent));
    } finally {
      setBusy(false);
    }
  };

  const noProject = projects !== null && projects.length === 0;
  return (
    <section className="cw-section cw-start" data-testid="conductor-start-form" aria-label="Start an agent">
      <GadgetRow label="What should it do?" wide>
        <StringGadget
          label="What should it do?"
          value={words}
          onChange={setWords}
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
      <GadgetRow label="Project">
        {noProject ? (
          <span className="cw-start-none">No project yet</span>
        ) : (
          <CycleGadget
            label="Project"
            value={projectId}
            options={(projects ?? []).map((p) => ({ value: p.id, label: p.name }))}
            onChange={(next) => {
              setProjectId(next);
              setAgent(rememberedAgent(next) ?? agent);
            }}
            disabled={busy || projects === null}
          />
        )}
      </GadgetRow>
      <GadgetRow label="Agent">
        <CycleGadget
          label="Agent"
          value={agent}
          options={AGENTS.map((id) => ({ value: id, label: AGENT_NAME[id] }))}
          onChange={(next) => setAgent(next as AgentId)}
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
          disabled={!words.trim() || !projectId}
          onClick={() => void start()}
          data-testid="conductor-start-go"
        >
          Start
        </Button>
      </div>
    </section>
  );
}
