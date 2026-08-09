import type { InferenceTarget } from "./api";

export type EgressLamp = {
  label: "LOCAL" | "LAN" | "PAIRED" | "MESH" | "CLOUD" | "NO MODEL";
  tone: "ok" | "warn" | "fail";
};

/** The compact instrument readout for an inference destination boundary. */
export function boundaryEgressLamp(
  boundary: string | null | undefined,
): EgressLamp {
  switch (boundary) {
    case "same_device":
      return { label: "LOCAL", tone: "ok" };
    case "private_network":
      return { label: "LAN", tone: "warn" };
    case "paired_device":
      return { label: "PAIRED", tone: "warn" };
    case "private_mesh":
      return { label: "MESH", tone: "warn" };
    case "external_service":
      return { label: "CLOUD", tone: "fail" };
    default:
      return { label: "NO MODEL", tone: "fail" };
  }
}

export function inferenceEgressLamp(
  target: Pick<InferenceTarget, "boundary"> | null | undefined,
): EgressLamp {
  return boundaryEgressLamp(target?.boundary);
}

/** Receipts without an actual-placement boundary retain the hub's scope. */
export function egressScopeLamp(scope: string | null | undefined): EgressLamp {
  switch (scope) {
    case "local":
      return { label: "LOCAL", tone: "ok" };
    // HS-130-04: the run-egress badge now speaks the four-value vocabulary. A
    // LAN endpoint is private_network (LAN), never a flat cloud lie.
    case "private_network":
      return { label: "LAN", tone: "warn" };
    case "mesh":
      return { label: "PAIRED", tone: "warn" };
    case "cloud":
      return { label: "CLOUD", tone: "fail" };
    default:
      return { label: "NO MODEL", tone: "fail" };
  }
}
