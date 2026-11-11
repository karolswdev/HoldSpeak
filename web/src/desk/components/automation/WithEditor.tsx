/** Betterment A4 — the With editor (DESIGN §4, RECIPE A4).
 *
 * The minimal engine picker until Engines E5 lands: his engines, then what
 * this Mac (and, on a press, the network) has that the library does not
 * (Found), each with one verb. Use writes this automation's engine (the
 * subject assignment `subject:workbench:<id>:capability:workbench.item`; the
 * hub re-freezes a live schedule). Add puts a found engine in the library
 * (the Engines app's own paths: `connect_cli_engine` for an agent CLI,
 * define-endpoint for a server) and uses it, in one press. Every row says
 * where its prompt goes. Under the engine in use: the optional Spend limit
 * per run for this automation, when that engine can stop at a limit. */
import { apiFetch } from "../../../lib/api";
import { defineEndpoint } from "../../../features/concierge/api";
import { endpointDraft, endpointProfileId } from "../../../features/concierge/endpointDraft";
import { connectCliEngine } from "../../../features/runson/api";
import { enginePlace, hostLabel, type BoardEngine } from "../../../features/runson/model";

export interface NativeAgentOption {
  profileId: string;
  agentId: string;
  label: string;
  executable: string;
  installed: boolean;
  ready: boolean;
}

interface NativeProfilesWire {
  profiles?: Array<{ profile_id?: string; label?: string; executable?: string }>;
}

interface NativeAgentsWire {
  agents?: Array<{ id?: string; label?: string; installed?: boolean; ready?: boolean }>;
  tmux?: { installed?: boolean };
}

/** The existing native profile and onboarding producers, joined by executable. */
export async function readNativeAgentOptions(): Promise<NativeAgentOption[]> {
  const [profileWire, agentWire] = await Promise.all([
    apiFetch<NativeProfilesWire>("/api/delivery/factory/profiles"),
    apiFetch<NativeAgentsWire>("/api/onboarding/agents"),
  ]);
  const agents = Array.isArray(agentWire.agents) ? agentWire.agents : [];
  const tmuxReady = agentWire.tmux?.installed === true;
  return (Array.isArray(profileWire.profiles) ? profileWire.profiles : [])
    .map((profile) => {
      const executable = String(profile.executable ?? "");
      const found = agents.find((agent) => String(agent.id ?? "") === executable);
      if (!found || found.installed !== true) return null;
      return {
        profileId: String(profile.profile_id ?? ""),
        agentId: executable,
        label: String(profile.label ?? found.label ?? executable),
        executable,
        installed: true,
        ready: found.ready === true && tmuxReady,
      };
    })
    .filter((option): option is NativeAgentOption => Boolean(option?.profileId));
}

/** Where an engine's prompt goes, for its chip. */
export function placeOf(engine: BoardEngine): { label: string; scope: "local" | "cloud" } {
  if (engine.vendor) return { label: engine.vendor, scope: "cloud" };
  const place = enginePlace(engine);
  return { label: hostLabel(engine), scope: place.place === "mac" || place.place === "lan" ? "local" : "cloud" };
}

/** The profile id a found engine gets when it is added (the Engines paths). */
function addedId(engine: BoardEngine): string {
  if (engine.agentPreset) return `agent-${engine.agentPreset}`;
  return endpointProfileId(engine.baseUrl ?? "", engine.model || engine.name);
}

/** Shared by the object editor and the list inspector; Add follows the engine library's path. */
export async function automationEngineProfile(engine: BoardEngine): Promise<string> {
  let profileId = assignedId(engine);
  if (engine.found) {
    profileId = addedId(engine);
    if (engine.agentPreset) await connectCliEngine({ preset: engine.agentPreset, profileId, expectedProfileRevision: 0 });
    else await defineEndpoint(endpointDraft({ url: engine.baseUrl ?? "", model: engine.model || engine.name,
      requestId: `automation-add-${Date.now()}`, expectedProfileRevision: 0 }));
  }
  return profileId;
}

/** The id an assignment names for a library engine. A v1 endpoint has no
 *  profile revision: the assignment calls it `legacy-<id>`. */
export function assignedId(engine: BoardEngine): string {
  const id = engine.profileId ?? "";
  if (!id || engine.profileRevision || id.startsWith("legacy-")) return id;
  return `legacy-${id}`;
}

export function usable(engine: BoardEngine): boolean {
  if (engine.kind === "preset") return false; // a download is the Engines app's job
  if (engine.found) return Boolean(engine.agentPreset || engine.baseUrl);
  return Boolean(engine.profileId);
}
