/** Remote factory + discovery on the Desk (HS-94-08 / §9, §10).
 *
 * Panes and sessions surface as node-issued TARGETS (each with an immutable
 * target_id + target_generation), never a client-known `pane:%N`. Agent launch
 * is a typed operation: the client picks a node-configured profile and a Story;
 * it can never supply an executable, argv, or shell fragment (the hub refuses
 * each by name). A launch binds a Work attempt and issues the pane's target on
 * the same spine, so a launched agent is reachable — or honestly
 * `failed_to_register` — without any client write.
 */

import { create } from "zustand";
import { apiRequest } from "../lib/api";
import type { OpenTarget } from "./deliveryTerminal";

export interface DiscoveredTarget {
  nodeId: string;
  session: string;
  paneId: string;
  targetId: string;
  targetGeneration: string;
  sourceId: string | null;
  worktreeId: string | null;
  profileId: string | null;
  launchId: string | null;
  storyRef: { project: string; storyId: string } | null;
  attemptId: string | null;
  attemptState: string | null;
  sessionBound: boolean;
}

export interface AgentProfile {
  profileId: string;
  label: string;
  executable: string;
}

const fromWireTarget = (t: any): DiscoveredTarget => {
  const ref = t?.story_ref;
  return {
    nodeId: String(t?.node_id || "local"),
    session: String(t?.session || ""),
    paneId: String(t?.pane_id || ""),
    targetId: String(t?.target_id || ""),
    targetGeneration: String(t?.target_generation || ""),
    sourceId: t?.source_id ? String(t.source_id) : null,
    worktreeId: t?.worktree_id ? String(t.worktree_id) : null,
    profileId: t?.profile_id ? String(t.profile_id) : null,
    launchId: t?.launch_id ? String(t.launch_id) : null,
    storyRef: ref
      ? { project: String(ref.project || ""), storyId: String(ref.story_id || "") }
      : null,
    attemptId: t?.attempt_id ? String(t.attempt_id) : null,
    attemptState: t?.attempt_state ? String(t.attempt_state) : null,
    sessionBound: Boolean(t?.session_bound),
  };
};

/** A discovered target → the immutable handle the terminal window opens. The
 *  label names the Story it is bound to when known, else the session/pane. */
export function targetHandle(t: DiscoveredTarget): OpenTarget {
  const label = t.storyRef
    ? `${t.storyRef.storyId}`
    : t.session
      ? `${t.session} · ${t.paneId}`
      : t.paneId;
  return {
    targetId: t.targetId,
    targetGeneration: t.targetGeneration,
    nodeId: t.nodeId,
    label,
    sessionLabel: t.session,
    worktreeId: t.worktreeId,
    agent: t.profileId || "session",
  };
}

interface FactoryState {
  targets: DiscoveredTarget[];
  status: "idle" | "loading" | "ok" | "tmux_absent" | "error";
  detail: string;
  profiles: AgentProfile[];
  launchState: "idle" | "working" | "done" | "failed";
  launchDetail: string;
  discover(): Promise<void>;
  loadProfiles(): Promise<void>;
  launch(args: {
    profileId: string;
    sourceId: string;
    worktreeId: string;
    project: string;
    storyId: string;
    sessionLabel: string;
  }): Promise<boolean>;
}

export const useDeliveryFactory = create<FactoryState>((set, get) => ({
  targets: [],
  status: "idle",
  detail: "",
  profiles: [],
  launchState: "idle",
  launchDetail: "",

  async discover() {
    set({ status: "loading" });
    try {
      const res = await apiRequest("/api/delivery/factory/discover");
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        set({ status: "error", detail: String(body.error || res.status), targets: [] });
        return;
      }
      const status = String(body.status || "ok");
      set({
        targets: (body.targets || []).map(fromWireTarget),
        status: status === "ok" ? "ok" : (status as FactoryState["status"]),
        detail: String(body.detail || ""),
      });
    } catch {
      set({ status: "error", detail: "hub unreachable", targets: [] });
    }
  },

  async loadProfiles() {
    try {
      const res = await apiRequest("/api/delivery/factory/profiles");
      if (!res.ok) return;
      const body = await res.json().catch(() => ({}));
      set({
        profiles: (body.profiles || []).map((p: any): AgentProfile => ({
          profileId: String(p.profile_id || ""),
          label: String(p.label || p.profile_id || ""),
          executable: String(p.executable || ""),
        })),
      });
    } catch {
      /* no profiles reachable — the launcher stays honest-empty */
    }
  },

  async launch(args) {
    set({ launchState: "working", launchDetail: "" });
    try {
      const res = await apiRequest("/api/delivery/factory/launch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          verb: "agent.launch",
          agent_profile_id: args.profileId,
          source_id: args.sourceId,
          worktree: { mode: "existing", worktree_id: args.worktreeId },
          story_ref: { project: args.project, story_id: args.storyId },
          session_label: args.sessionLabel,
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (res.ok && body.ok !== false) {
        set({ launchState: "done", launchDetail: String(body.attempt_id || "") });
        await get().discover();
        return true;
      }
      set({
        launchState: "failed",
        launchDetail: String(body.detail || body.error || `HTTP ${res.status}`),
      });
      return false;
    } catch {
      set({ launchState: "failed", launchDetail: "hub unreachable" });
      return false;
    }
  },
}));
