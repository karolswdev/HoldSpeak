import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useOnDeskChanged } from "../useDeskChangedRefresh";

export type EngineState = "set" | "none" | "unread" | "failed";

export type EngineFact = {
  state: EngineState;
  model: string;
  place: string;
};

type SummaryStore = {
  body: any | null;
  state: "unread" | "ready" | "failed";
  listeners: Set<() => void>;
  pending: Promise<void> | null;
};

// The roster is one desk fact. Keep one request and one subscription fan-out
// for every capability surface mounted on that desk.
const summary: SummaryStore = {
  body: null,
  state: "unread",
  listeners: new Set(),
  pending: null,
};

function placeFor(boundary: unknown): string {
  const value = String(boundary || "").toLowerCase();
  if (value === "same_device" || value === "local") return "This Mac";
  if (value === "private_network" || value === "lan") return "LAN";
  if (value === "private_mesh" || value === "mesh" || value === "paired") return "MESH";
  if (value === "external_service" || value === "cloud") return "CLOUD";
  return "";
}

function factFromSummary(capabilityId: string): EngineFact {
  if (summary.state === "unread") return { state: "unread", model: "", place: "" };
  if (summary.state === "failed") return { state: "failed", model: "", place: "" };
  const row = (summary.body?.task_overrides || []).find(
    (candidate: any) => String(candidate?.id || "") === capabilityId,
  );
  const effective = row?.effective;
  const status = String(effective?.status || "no_assignment");
  if (status === "no_assignment" || !effective?.assignment) {
    return { state: "none", model: "", place: "" };
  }
  const entry = effective.assignment.entries?.[0] || {};
  return {
    // P0: an assignment with no compatible engine cannot answer: not "set".
    state: status === "assigned" ? "set" : "none",
    // A profile id is an implementation key and is not useful on the Desk.
    model: String(entry.label || "Selected engine"),
    place: placeFor(entry.boundary),
  };
}

function notify(): void {
  summary.listeners.forEach((listener) => listener());
}

/** Read the shared roster. A normal read is cached; explicit retries refresh. */
export async function refreshEngine(
  _capabilityId: string,
  force = true,
): Promise<void> {
  if (summary.pending) return summary.pending;
  if (!force && summary.state === "ready") return;
  summary.pending = apiFetch<any>("/api/inference/assignments")
    .then((body) => {
      summary.body = body;
      summary.state = "ready";
    })
    .catch(() => {
      summary.state = "failed";
    })
    .finally(() => {
      summary.pending = null;
      notify();
    });
  return summary.pending;
}

export function useEngine(capabilityId: string): EngineFact {
  const [, redraw] = useState(0);
  const reread = useCallback(() => {
    void refreshEngine(capabilityId);
  }, [capabilityId]);
  useEffect(() => {
    const listener = () => redraw((value) => value + 1);
    summary.listeners.add(listener);
    void refreshEngine(capabilityId, false);
    return () => {
      summary.listeners.delete(listener);
    };
  }, [capabilityId]);
  useOnDeskChanged(reread);
  return factFromSummary(capabilityId);
}

/** Forget the read while preserving mounted readers and their subscriptions. */
export function clearEngineCache(): void {
  summary.body = null;
  summary.state = "unread";
  notify();
}
