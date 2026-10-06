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
  /** The item the preview is for, and the profile asked for (Launch matches them). */
  kind?: string;
  id?: string;
  requested_profile?: string;
  /** The profile the launch would really run (a held launch keeps its own). */
  profile: string;
  /** A held launch of this item that Launch resumes (its brief, its agent). */
  resume?: { launch_id: string; profile: string; instruction_state: string | null } | null;
  refused: string[];
}

/** POST /api/agent/hand (202) and GET /api/agent/launches/{id}: the launch's delivery. */
export interface HandLaunch {
  launch_id?: string | null;
  status?: string;
  state?: string | null;
  instruction_state?: string | null;
  resumed?: boolean;
  profile?: string | null;
  failure?: { stage?: string; outcome?: string } | null;
}

export const HAND_LAUNCH_PATH = (id: string) => `/api/agent/launches/${encodeURIComponent(id)}`;
/** Deliver the held brief of the same launch again (no relaunch). */
export const HAND_DELIVER_PATH = (id: string) => `${HAND_LAUNCH_PATH(id)}/deliver`;
/** The delivery state is known once it leaves `pending` (first_message.py). */
const DELIVERY_POLL_MS = 2000;

const PROFILE_AGENT: Record<string, AgentId> = { "claude-default": "claude", "codex-default": "codex" };
export function agentOfProfile(profile: string | null | undefined, fallback: AgentId): AgentId {
  return PROFILE_AGENT[String(profile ?? "")] ?? fallback;
}

/** The launch's delivery as one token: the brief is pending, held, sent or refused. */
export function deliveryToken(launch: HandLaunch): { label: string; tone: "ok" | "warning" | "danger" | undefined; done: boolean } {
  const state = String(launch.instruction_state ?? "");
  if (state === "sent") return { label: "LAUNCHED · BRIEF SENT", tone: "ok", done: true };
  if (state === "pending" || state === "") return { label: "LAUNCHED · BRIEF PENDING", tone: undefined, done: false };
  if (state === "hooks_missing") return { label: "LAUNCHED · BRIEF HELD · NO HOOKS", tone: "warning", done: true };
  return { label: `LAUNCHED · BRIEF NOT SENT · ${codeWords(state)} · KEPT ON THE HUB · SEND AGAIN`, tone: "danger", done: true };
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
    case "launch_cap_reached":
      return "AGENT LIMIT REACHED";
    case "launch_profile_mismatch":
      // `agent` is the HELD launch's agent here (the sheet passes it).
      return `HELD FOR ${AGENT_NAME[agent].toUpperCase()}`;
    case "hub_unreachable":
      return "HUB UNREACHABLE";
    default:
      return codeWords(code);
  }
}

/** Home as `~` (the face never shows the owner's home path). */
function tilde(path: string): string {
  return path.replace(/^\/(?:Users|home)\/[^/]+/, "~");
}

/** The refusal's name: a named refusal ({code} / {error}), or a launch that
 * failed ({failure: {stage, outcome}}); HUB UNREACHABLE only when no answer came. */
export function codeOf(error: unknown): string {
  if (error instanceof ApiError) {
    const payload = (error.payload ?? {}) as Record<string, unknown>;
    const failure = (payload.failure ?? null) as { stage?: unknown; outcome?: unknown } | null;
    for (const code of [payload.code, payload.error, failure?.outcome, failure?.stage]) {
      if (typeof code === "string" && code) return code;
    }
    return `http_${error.status}`;
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
  const [launched, setLaunched] = useState<HandLaunch | null>(null);

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

  // The delivery is known once it leaves `pending`: read the launch until then.
  useEffect(() => {
    if (!launched?.launch_id || deliveryToken(launched).done) return;
    let live = true;
    const timer = window.setTimeout(() => {
      apiFetch<HandLaunch>(HAND_LAUNCH_PATH(String(launched.launch_id)))
        .then((next) => { if (live) setLaunched({ ...launched, ...next }); })
        .catch(() => { if (live) setLaunched({ ...launched }); });
    }, DELIVERY_POLL_MS);
    return () => { live = false; window.clearTimeout(timer); };
  }, [launched]);

  const sendAgain = useCallback(async () => {
    if (!launched?.launch_id || launching) return;
    setLaunching(true);
    try {
      const next = await apiFetch<HandLaunch>(HAND_DELIVER_PATH(String(launched.launch_id)), { method: "POST" });
      setLaunched({ ...launched, ...next });
    } catch (error) {
      setLaunched({ ...launched, instruction_state: codeOf(error) });
    } finally {
      setLaunching(false);
    }
  }, [launched, launching]);

  const launch = useCallback(async () => {
    if (launching) return;
    setLaunching(true);
    setLaunchError(null);
    try {
      const answer = await apiFetch<HandLaunch>(HAND_PATH, {
        method: "POST",
        json: { kind: origin.kind, id: origin.id, profile: AGENT_PROFILE[agent], project_id: origin.projectId || null },
      });
      setLaunched(answer ?? {});
    } catch (error) {
      setLaunchError(codeOf(error));
      if (!(error instanceof ApiError)) console.warn("hand to agent:", readableError(error));
    } finally {
      setLaunching(false);
    }
  }, [agent, launching, origin.id, origin.kind, origin.projectId]);

  // The preview on screen is the one for THIS item and THIS pick; a late answer
  // for another pick never arms Launch.
  const current = preview !== null
    && (preview.requested_profile ?? preview.profile) === AGENT_PROFILE[agent]
    && (preview.kind ?? origin.kind) === origin.kind
    && (preview.id ?? origin.id) === origin.id;
  const blocked = preview?.refused ?? [];
  const sources = preview?.sources ?? [];
  const mode = modeWord(preview?.control_mode);
  // The agent the launch really runs: a held launch keeps its own.
  const actual = current ? agentOfProfile(preview?.profile, agent) : agent;
  const canLaunch = current && blocked.length === 0 && !launching && launched === null;
  const delivery = launched ? deliveryToken(launched) : null;
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
                    {preview.resume ? (
                      <span className="surface-token" data-chip data-testid="hand-resume">
                        RESUMES · BRIEF {codeWords(preview.resume.instruction_state || "pending")}
                      </span>
                    ) : (
                      <span className="surface-token" data-chip>NEW WORKTREE</span>
                    )}
                    <span className="surface-token" data-chip>{preview.branch}</span>
                  </>
                ) : null}
                <span className="surface-token" data-chip data-testid="hand-control">CONTROL · {mode}</span>
              </span>
              {blocked.length ? (
                <span className="desk-hand-refused" role="alert" data-testid="hand-refused">
                  {blocked.map((code) => (
                    <span key={code} className="surface-token" data-tone="danger">
                      {refusalToken(code, code === "launch_profile_mismatch" ? actual : agent)}
                    </span>
                  ))}
                </span>
              ) : null}
            </SurfaceSection>
          </>
        ) : null}
      </div>
      <SurfaceFooter
        className="desk-hand-footer"
        egress={<EgressChip label={AGENT_HOST[actual]} scope="cloud" />}
        receipt={
          delivery ? (
            <span className="surface-footer-receipt-line" data-tone={delivery.tone} role="status" data-testid="hand-launch-receipt">
              {delivery.label}
            </span>
          ) : launchError ? (
            <span className="surface-footer-receipt-line" data-tone="danger" role="alert" data-testid="hand-launch-refused">
              NOT LAUNCHED · {refusalToken(launchError, agent)}
            </span>
          ) : (
            <span className="surface-footer-receipt-line">
              {AGENT_NAME[actual].toUpperCase()}{preview ? ` · ${mode}` : ""}
            </span>
          )
        }
        verbs={
          launched ? (
            <>
              <Button dense variant="ghost" onClick={close}>Close</Button>
              {delivery?.tone === "danger" ? (
                <Button dense variant="primary" loading={launching} disabled={launching}
                  onClick={() => void sendAgain()} data-testid="hand-send-again">
                  Send again
                </Button>
              ) : null}
            </>
          ) : (
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
          )
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
