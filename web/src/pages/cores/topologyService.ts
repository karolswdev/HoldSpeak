/** Topology data service — aggregates existing API facts into the map model.
 *  No new authority: reads setup, assignments, and model-library projections. */

import { apiFetch } from "../../lib/api";
import { getAssignmentSummary, type AssignmentSummary } from "./assignmentExperience";
import { getModelLibrary, type ModelLibraryProjection } from "./modelLibrary";

// ── Wire types (from GET /api/front-door/topology) ─────────────────

export type TopologyNodeWire = {
  id: string;
  label: string;
  kind: "this_machine" | "private_endpoint" | "external_service" | "paired_device" | "mesh_node";
  home: boolean;
  state: "ready" | "unreachable" | "unavailable" | "stale_manifest" | "offline" | "idle";
  runtimes?: Array<{ id: string; state: string }>;
  models?: string[];
  base_url?: string;
};

export type TopologyWire = {
  nodes: TopologyNodeWire[];
  flows: Array<{
    group_id: string;
    group_label: string;
    target_node_id: string;
  }>;
};

// ── Fetchers ────────────────────────────────────────────────────────

export async function getTopology(signal?: AbortSignal): Promise<TopologyWire> {
  return apiFetch<TopologyWire>("/api/front-door/topology", { signal });
}

export async function getTopologyFull(signal?: AbortSignal): Promise<{
  topology: TopologyWire;
  assignments: AssignmentSummary;
  library: ModelLibraryProjection;
}> {
  const [topology, assignments, library] = await Promise.all([
    getTopology(signal),
    getAssignmentSummary(signal),
    getModelLibrary(signal),
  ]);
  return { topology, assignments, library };
}

// ── Helpers ─────────────────────────────────────────────────────────

/** Map a node wire state to a ChipState for the surface library. */
export function nodeChipState(
  state: TopologyNodeWire["state"],
): "success" | "unreachable" | "warning" | "idle" | "working" {
  switch (state) {
    case "ready":
      return "success";
    case "unreachable":
    case "unavailable":
    case "offline":
      return "unreachable";
    case "stale_manifest":
      return "warning";
    default:
      return "idle";
  }
}

/** Human-readable state label for a topology node. */
export function nodeStateLabel(state: TopologyNodeWire["state"]): string {
  switch (state) {
    case "ready":
      return "Ready";
    case "unreachable":
      return "Unreachable";
    case "unavailable":
      return "Unavailable";
    case "stale_manifest":
      return "Stale";
    case "offline":
      return "Offline";
    default:
      return "Idle";
  }
}

/** Human-readable kind label. */
export function nodeKindLabel(kind: TopologyNodeWire["kind"]): string {
  switch (kind) {
    case "this_machine":
      return "This Mac";
    case "private_endpoint":
      return "LAN server";
    case "external_service":
      return "Cloud";
    case "paired_device":
      return "Paired device";
    case "mesh_node":
      return "Mesh node";
    default:
      return kind;
  }
}
