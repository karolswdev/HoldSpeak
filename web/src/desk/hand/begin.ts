/** PHILO-14 C3 — what a drop (or the drawer's Hand to agent verb) does.
 *
 *  Muad'Dib's Phase 14 ruling on the Conductor's K5 modes: in YOLO the
 *  launch is one confirm line with the brief one press away; in Secure and
 *  Normal the launch sheet opens, on the agent the drop named. The mode is
 *  the hub's (`GET /api/authority/policy`, a local read). When the mode
 *  cannot be read, the sheet opens: it shows everything before the press. */
import { apiFetch } from "../../lib/api";
import { DEFAULT_AGENT, handRefOf, openHand, pickDefaultAgent, type HandOrigin } from "../agentHand";
import { AGENTS_PATH, type AgentId, type AgentsDetect } from "../firstrun/agentsStep";
import { useDropHand, type HandEnd } from "./store";

export const POLICY_PATH = "/api/authority/policy";

/** The hub's Control mode (`safe` | `neutral` | `yolo`), or null when unread. */
export async function readControlMode(): Promise<string | null> {
  try {
    const policy = await apiFetch<{ control_mode?: string } | null>(POLICY_PATH);
    const mode = String(policy?.control_mode ?? "").trim().toLowerCase();
    return mode || null;
  } catch {
    return null;
  }
}

/** PHILO-15 B36: the default agent from the agents read (a local file read);
 *  an unread answer keeps Claude Code. */
export async function readDefaultAgent(): Promise<{ agent: AgentId; skipped: AgentId | null }> {
  try {
    return pickDefaultAgent(await apiFetch<AgentsDetect>(AGENTS_PATH));
  } catch {
    return { agent: DEFAULT_AGENT, skipped: null };
  }
}

/** `where.agent`: the agent the owner named (a drop on that agent's icon);
 *  absent, the default agent (the first with a KNOWN sign-in). */
export async function beginHand(
  origin: HandOrigin,
  where: { agent?: AgentId; host: string; source: HandEnd },
): Promise<void> {
  const [mode, pick] = await Promise.all([
    readControlMode(),
    where.agent ? Promise.resolve({ agent: where.agent, skipped: null }) : readDefaultAgent(),
  ]);
  if (mode === "yolo") {
    useDropHand.getState().confirm({
      origin, agent: pick.agent, host: where.host, source: where.source, skipped: pick.skipped,
    });
    return;
  }
  openHand({ ...origin, agent: pick.agent });
}

/** The item an object ref hands, or null (it is not a work item `agent.hand`
 *  takes: holdspeak/services/agent_brief.py BRIEF_KINDS). A Room issue is
 *  `issue:<watch_id>.<entity_id>` (Conductor R4). */
export function handOriginOfRef(
  ref: string,
  title: string,
  projectId?: string | null,
): HandOrigin | null {
  const clean = String(ref ?? "").trim();
  const name = title || "Untitled";
  if (clean.startsWith("issue:") && clean.length > "issue:".length) {
    return { kind: "issue", id: clean.slice("issue:".length), title: name, projectId: projectId ?? null };
  }
  const hand = handRefOf(clean);
  return hand ? { ...hand, title: name, projectId: projectId ?? null } : null;
}

const AGENTS: ReadonlySet<string> = new Set(["claude", "codex"]);

/** The agent a drop target stands for: the Conductor drawer is the default
 *  agent (Claude Code, the owner's ruling); an agent icon (`coder:<agent>:<session>`)
 *  is that agent's kind. Null: not a drop target. */
export function agentOfTarget(key: string): AgentId | null {
  if (key === "drawer:conductor") return DEFAULT_AGENT;
  if (!key.startsWith("coder:")) return null;
  const agent = key.split(":")[1] ?? "";
  return AGENTS.has(agent) ? (agent as AgentId) : null;
}
