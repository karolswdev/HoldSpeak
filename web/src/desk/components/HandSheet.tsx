/* The launch sheet (the Conductor canvas K3a/K3b, ratified 2026-10-06):
 * Hand to agent opens this docked desk window in the Ask AI posture (the
 * desk stays alive behind it; never a modal). It shows what the hand-off
 * will do BEFORE the press: the agent (Claude Code by the owner's ruling,
 * or Codex), the brief (its sources, bytes, the People cut, the acceptance
 * checks, the text), WHERE (the repository, a new worktree, the branch),
 * the Control mode, and the host the brief goes to on the Launch footer.
 * A refusal is a named token in the sheet, never prose. */
import { useCallback, useEffect, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { ApiError, apiFetch, readableError } from "../../lib/api";
import {
  ChoiceCard,
  ChoiceCardGroup,
  Disclosure,
  EgressChip,
  StateChip,
  SurfaceFooter,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
} from "../surface";
import { countToken } from "../surface/count";
import { useDesk } from "../store";
import { DeskWindowFrame } from "./DeskWindow";
import {
  AGENT_PROFILE,
  DEFAULT_AGENT,
  HAND_PATH,
  HAND_PREVIEW_PATH,
  HAND_WINDOW_ID,
  useAgentHand,
  type HandOrigin,
} from "../agentHand";
import { AGENTS_PATH, AGENT_HOST, AGENT_NAME, type AgentId, type AgentsDetect } from "../firstrun/agentsStep";
import { codeWords } from "../firstrun/AgentsCard";
import "./hand-sheet.css";

export interface HandPreview {
  text: string;
  refs: string[];
  bytes: number;
  people_cut: number;
  sources: { kind: string; ref: string; title: string; lines: number | null }[];
  acceptance: string[];
  repo: string | null;
  /** The repository as the face shows it (the hub's home is `~`). */
  repo_label?: string | null;
  branch: string;
  worktree: string;
  project_id: string | null;
  control_mode: string;
  profile: string;
  refused: string[];
}

const AGENTS: AgentId[] = ["claude", "codex"];

/** The Control mode as the owner names it (Settings: Secure, Normal, YOLO). */
export function modeWord(mode: string | null | undefined): string {
  const m = String(mode ?? "").toLowerCase();
  return m === "safe" ? "SECURE" : m === "neutral" ? "NORMAL" : m === "yolo" ? "YOLO" : m.toUpperCase();
}

/** The brief's size, as the canvas reads it (4.2 KB). */
export function kb(bytes: number): string {
  return `${(Math.max(0, bytes) / 1024).toFixed(1)} KB`;
}

const LEAD: Record<string, string> = {
  action: "ACT",
  meeting: "MTG",
  decision: "DEC",
  decision_record: "DEC",
  desk_decision: "DEC",
  note: "NOTE",
  artifact: "ART",
  project_item: "ITEM",
  project_decisions: "RM",
  project_commitments: "RM",
  memory: "MEM",
  hs_context: ".HS",
};
const KIND_WORD: Record<string, string> = {
  action: "ACTION ITEM",
  meeting: "MEETING",
  decision: "DECISION",
  decision_record: "DECISION",
  desk_decision: "DECISION",
  note: "NOTE",
  artifact: "ARTIFACT",
  project_item: "PROJECT ITEM",
};
const LINE_UNIT: Record<string, [string, string]> = {
  project_decisions: ["DECISION", "DECISIONS"],
  project_commitments: ["OPEN", "OPEN"],
  memory: ["LINE", "LINES"],
  hs_context: ["LINE", "LINES"],
};

/** One source's fact token: the item's kind, or the count a composed part holds. */
export function sourceFact(source: HandPreview["sources"][number]): string | null {
  const unit = LINE_UNIT[source.kind];
  if (unit) return countToken(source.lines ?? 0, unit[0], unit[1]);
  return KIND_WORD[source.kind] ?? codeWords(source.kind);
}

/** A refusal code as its token (the agent named where the code names it). */
export function refusalToken(code: string, agent: AgentId): string {
  switch (code) {
    case "no_repository":
      return "NO REPOSITORY";
    case "item_unknown":
      return "ITEM NOT FOUND";
    case "executable_absent":
      return `${AGENT_NAME[agent].toUpperCase()} NOT INSTALLED`;
    case "tmux_absent":
      return "TMUX NOT INSTALLED";
    case "worktree_duplicate":
      return "WORKTREE EXISTS";
    case "brief_over_cap":
      return "BRIEF OVER 32 KB";
    case "item_kind_unsupported":
      return "KIND NOT SUPPORTED";
    case "owner_required":
      return "OWNER ONLY";
    default:
      return codeWords(code);
  }
}

/** Home as `~` (the face never shows the owner's home path). */
function tilde(path: string): string {
  return path.replace(/^\/(?:Users|home)\/[^/]+/, "~");
}

function codeOf(error: unknown): string {
  if (error instanceof ApiError) {
    const payload = error.payload as Record<string, unknown> | null;
    const code = payload?.code ?? payload?.error;
    if (typeof code === "string" && code) return code;
  }
  return "hub_unreachable";
}

function useDetect() {
  const [detect, setDetect] = useState<AgentsDetect | null>(null);
  useEffect(() => {
    let live = true;
    apiFetch<AgentsDetect>(AGENTS_PATH).then((d) => live && setDetect(d)).catch(() => {});
    return () => { live = false; };
  }, []);
  return detect;
}

function AgentSummary({ agent, detect }: { agent: AgentId; detect: AgentsDetect | null }) {
  const row = detect?.agents.find((a) => a.id === agent);
  if (!row) return null;
  const words = !row.installed
    ? "NOT INSTALLED"
    : [row.hooks === "installed" ? "HOOKS IN" : "NO HOOKS", row.version].filter(Boolean).join(" · ");
  return <span className="surface-token" data-chip>{words}</span>;
}

function Sheet({ origin }: { origin: HandOrigin }) {
  const close = useAgentHand((s) => s.close);
  const detect = useDetect();
  const [agent, setAgent] = useState<AgentId>(DEFAULT_AGENT);
  const [preview, setPreview] = useState<HandPreview | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [briefOpen, setBriefOpen] = useState(false);
  const [launching, setLaunching] = useState(false);
  const [launchError, setLaunchError] = useState<string | null>(null);

  useEffect(() => {
    useDesk.getState().focusPanel(HAND_WINDOW_ID);
  }, [origin.kind, origin.id]);

  useEffect(() => {
    let live = true;
    setPreviewError(null);
    setLaunchError(null);
    apiFetch<HandPreview>(HAND_PREVIEW_PATH, {
      method: "POST",
      json: { kind: origin.kind, id: origin.id, profile: AGENT_PROFILE[agent], project_id: origin.projectId || null },
    })
      .then((p) => { if (live) setPreview(p); })
      .catch((error) => {
        if (!live) return;
        setPreview(null);
        setPreviewError(codeOf(error));
      });
    return () => { live = false; };
  }, [origin.kind, origin.id, origin.projectId, agent]);

  const launch = useCallback(async () => {
    if (launching) return;
    setLaunching(true);
    setLaunchError(null);
    try {
      await apiFetch(HAND_PATH, {
        method: "POST",
        json: { kind: origin.kind, id: origin.id, profile: AGENT_PROFILE[agent], project_id: origin.projectId || null },
      });
      close();
    } catch (error) {
      setLaunchError(codeOf(error));
      if (!(error instanceof ApiError)) console.warn("hand to agent:", readableError(error));
    } finally {
      setLaunching(false);
    }
  }, [agent, close, launching, origin.id, origin.kind, origin.projectId]);

  const blocked = preview?.refused ?? [];
  const sources = preview?.sources ?? [];
  const mode = modeWord(preview?.control_mode);
  const canLaunch = preview !== null && blocked.length === 0 && !launching;
  const pick = (value: string) => setAgent(value as AgentId);
  return (
    <DeskWindowFrame
      id={HAND_WINDOW_ID}
      glyph="⇥"
      label="Hand to agent"
      kindWord="Agent launch"
      className="desk-pullout desk-hand"
      defaultW={560}
      defaultH={660}
      icon={<span className="desk-ask-glyph" aria-hidden="true">⇥</span>}
      title={origin.title}
      open
      onClose={close}
    >
      <div className="desk-pullout-body desk-hand-body" data-testid="hand-sheet">
        <SurfaceSection label="AGENT">
          <ChoiceCardGroup name="hand-agent" value={agent} layout="row" ariaLabel="Agent" onChange={pick}>
            {AGENTS.map((a) => (
              <ChoiceCard
                key={a}
                name="hand-agent"
                selectedValue={agent}
                onChange={pick}
                value={a}
                label={AGENT_NAME[a]}
                summary={<AgentSummary agent={a} detect={detect} />}
              />
            ))}
          </ChoiceCardGroup>
        </SurfaceSection>
        {previewError ? (
          <div className="desk-hand-refused" role="alert" data-testid="hand-preview-refused">
            <StateChip state="failure" label="NO BRIEF" />
            <span className="surface-token" data-tone="danger">{refusalToken(previewError, agent)}</span>
          </div>
        ) : null}
        {preview ? (
          <>
            <SurfaceSection
              label={["BRIEF", countToken(sources.length, "SOURCE"), kb(preview.bytes)].filter(Boolean).join(" · ")}
            >
              <SurfaceLedger count={null} cols="room">
                {sources.map((s) => {
                  const fact = sourceFact(s);
                  return (
                    <SurfaceLedgerRow
                      key={`${s.kind}:${s.ref}`}
                      lead={<span className="desk-hand-lead">{LEAD[s.kind] ?? "SRC"}</span>}
                      primary={s.title}
                      cells={fact ? <span className="surface-token" data-chip>{fact}</span> : undefined}
                      expands={false}
                      wrap
                    />
                  );
                })}
              </SurfaceLedger>
              <span className="desk-hand-tokens" data-testid="hand-brief-tokens">
                {preview.people_cut > 0 ? (
                  <span className="surface-token" data-chip>PEOPLE CUT · {countToken(preview.people_cut, "PART")}</span>
                ) : null}
                {preview.acceptance.length ? (
                  <span className="surface-token" data-chip>ACCEPTANCE · {countToken(preview.acceptance.length, "CHECK")}</span>
                ) : null}
              </span>
              <Disclosure label="BRIEF TEXT" open={briefOpen} onOpenChange={setBriefOpen}>
                <pre className="desk-pullout-md desk-hand-text">{preview.text}</pre>
              </Disclosure>
            </SurfaceSection>
            <SurfaceSection label="WHERE">
              <span className="desk-hand-tokens" data-testid="hand-where">
                {preview.repo ? (
                  <>
                    <span className="surface-token" data-chip>{preview.repo_label || tilde(preview.repo)}</span>
                    <span className="surface-token" data-chip>NEW WORKTREE</span>
                    <span className="surface-token" data-chip>{preview.branch}</span>
                  </>
                ) : null}
                <span className="surface-token" data-chip data-testid="hand-control">CONTROL · {mode}</span>
              </span>
              {blocked.length ? (
                <span className="desk-hand-refused" role="alert" data-testid="hand-refused">
                  {blocked.map((code) => (
                    <span key={code} className="surface-token" data-tone="danger">{refusalToken(code, agent)}</span>
                  ))}
                </span>
              ) : null}
            </SurfaceSection>
          </>
        ) : null}
      </div>
      <SurfaceFooter
        className="desk-hand-footer"
        egress={<EgressChip label={AGENT_HOST[agent]} scope="cloud" />}
        receipt={
          launchError ? (
            <span className="surface-footer-receipt-line" data-tone="danger" role="alert" data-testid="hand-launch-refused">
              NOT LAUNCHED · {refusalToken(launchError, agent)}
            </span>
          ) : (
            <span className="surface-footer-receipt-line">
              {AGENT_NAME[agent].toUpperCase()}{preview ? ` · ${mode}` : ""}
            </span>
          )
        }
        verbs={
          <>
            <Button dense variant="ghost" onClick={close}>Cancel</Button>
            <Button
              dense
              variant="primary"
              loading={launching}
              disabled={!canLaunch}
              onClick={() => void launch()}
              data-testid="hand-launch"
            >
              Launch
            </Button>
          </>
        }
      />
    </DeskWindowFrame>
  );
}

/** The launch sheet, mounted once on the desk; it shows while an item is handed. */
export function HandSheet() {
  const origin = useAgentHand((s) => s.origin);
  if (!origin) return null;
  return <Sheet key={`${origin.kind}:${origin.id}`} origin={origin} />;
}
