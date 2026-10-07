/* Hand to agent (docs/internal/CONDUCTOR.md step 2; the Conductor canvas
 * K2/K3, ratified 2026-10-06): one item to a coding agent.
 *
 * Every entry (the Object menu, the object context menu, ⌘K, a Door row, a
 * Room row) opens the SAME launch sheet: a docked desk window in the Ask AI
 * posture (never a modal). The owner ruled that the sheet shows on every
 * hand-off, in every Control mode; the default agent is Claude Code.
 *
 *   POST /api/agent/hand/preview   the brief, repository and branch; no side effect
 *   POST /api/agent/hand           the launch (the `agent.hand` operation)
 */
import { create } from "zustand";
import type { PrimitiveKind } from "../lib/primitives";
import type { AgentId } from "./firstrun/agentsStep";
import { issueOriginId } from "./agentFlights";

export const HAND_PATH = "/api/agent/hand";
export const HAND_PREVIEW_PATH = "/api/agent/hand/preview";
export const HAND_WINDOW_ID = "agent-hand";

/** The item kinds `agent.hand` takes (holdspeak/services/agent_brief.py BRIEF_KINDS). */
export type HandKind = "action" | "decision" | "decision_record" | "project_item" | "note" | "meeting" | "artifact" | "issue";

export interface HandOrigin {
  kind: HandKind;
  id: string;
  title: string;
  projectId?: string | null;
}

/** The launch profile of each agent (factory_launch `_DEFAULT_PROFILES`). */
export const AGENT_PROFILE: Record<AgentId, string> = { claude: "claude-default", codex: "codex-default" };
/** The owner's ruling (2026-10-06): the sheet opens on Claude Code. */
export const DEFAULT_AGENT: AgentId = "claude";

/** The Desk object kinds a brief can carry: the same id on both sides. */
const DESK_HAND_KINDS: Partial<Record<PrimitiveKind, HandKind>> = {
  meeting: "meeting",
  artifact: "artifact",
  note: "note",
  decision: "decision",
};

export function handKindOf(kind: PrimitiveKind): HandKind | null {
  return DESK_HAND_KINDS[kind] ?? null;
}

/** A Desk route token (`decision:<id>`, `action_item:<id>`) as a hand origin. */
export function handRefOf(ref: string | null | undefined): { kind: HandKind; id: string } | null {
  const [kind, ...rest] = String(ref ?? "").split(":");
  const id = rest.join(":");
  if (!id) return null;
  if (kind === "action_item" || kind === "action") return { kind: "action", id };
  if (kind === "decision" || kind === "meeting" || kind === "note" || kind === "artifact") return { kind, id };
  return null;
}

interface HandState {
  origin: HandOrigin | null;
  open: (origin: HandOrigin) => void;
  close: () => void;
}

export const useAgentHand = create<HandState>((set) => ({
  origin: null,
  open: (origin) => set({ origin }),
  close: () => set({ origin: null }),
}));

/** Open the launch sheet for one item (and bring its window to the front). */
export function openHand(origin: HandOrigin): void {
  useAgentHand.getState().open(origin);
}

/** The fields a Door or Room row carries that name its item. */
export interface HandRowItem {
  title?: string | null;
  source?: string | null;
  actionItemId?: string | null;
  openRef?: string | null;
  projectId?: string | null;
  /** A Room issue row (Conductor R4): `kind: "issue"`, its Watch and its entity. */
  kind?: string | null;
  watchId?: string | null;
  entityId?: string | null;
  _doorCard?: { lawful_verbs?: Array<{ name: string; arguments: Record<string, unknown> }> } | null;
}

/** The item a row hands to an agent, or null (the verb is withheld: A.11).
 * In order: the Door card's declared `agent.hand` verb; a commitment's
 * action item; a decision's Desk route token; a Room issue row (its Watch
 * and entity: `issue:<watch_id>.<entity_id>`, Conductor R4). */
export function handOriginOfRow(item: HandRowItem): HandOrigin | null {
  const title = String(item.title ?? "") || "Untitled";
  const projectId = item.projectId ? String(item.projectId) : null;
  for (const verb of item._doorCard?.lawful_verbs ?? []) {
    if (verb.name !== "agent.hand") continue;
    const ref = handRefOf(`${String(verb.arguments.kind ?? "")}:${String(verb.arguments.id ?? "")}`);
    if (ref) return { ...ref, title, projectId };
  }
  if (item.actionItemId) return { kind: "action", id: String(item.actionItemId), title, projectId };
  const issue = issueOriginId(item);
  if (issue) return { kind: "issue", id: issue, title, projectId };
  if (item.source === "decision") {
    const ref = handRefOf(item.openRef);
    if (ref?.kind === "decision") return { ...ref, title, projectId };
  }
  return null;
}
