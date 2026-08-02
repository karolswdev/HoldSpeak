// HS-112-06 — the browser's seat at the one audio floor.
//
// The host has always arbitrated capture through a single owner model
// (`VoiceTypingSession`: hotkey, devices, meeting recorder, wake). An
// ambient open mic in this tab is capture too, so it takes a seat at the
// SAME table instead of listening behind the arbiter's back: claim before
// the first frame, renew on a heartbeat, release when the mic is dropped.
//
// The claim is LEASED. A tab that dies stops renewing and the floor frees
// itself, so a closed browser can never wedge the owner's hotkey.

import { ApiError, apiFetch } from "./api";

/** Seconds the server holds the claim without a heartbeat. */
export const FLOOR_LEASE_SECONDS = 20;
/** Heartbeat interval — half the lease, so one lost beat is survivable. */
export const FLOOR_RENEW_MS = (FLOOR_LEASE_SECONDS / 2) * 1000;

/** The floor is held by someone else, and we can say who. */
export class FloorHeldError extends Error {
  constructor(public owner: string) {
    super(`Audio floor held by ${owner}`);
    this.name = "FloorHeldError";
  }
  /** The room's refusal code — rendered as WHAT ("FLOOR HELD MEETING"). */
  get refusal(): string {
    return `floor_held_${this.owner || "unknown"}`;
  }
}

function ownerOf(error: unknown): string | null {
  if (!(error instanceof ApiError) || error.status !== 409) return null;
  const payload =
    error.payload && typeof error.payload === "object"
      ? (error.payload as Record<string, unknown>)
      : {};
  const owner = payload.owner;
  return typeof owner === "string" && owner ? owner : "unknown";
}

/** Claim the floor for this tab's open mic. Throws when someone holds it. */
export async function claimAudioFloor(): Promise<void> {
  try {
    await apiFetch("/api/dictation/floor/claim", {
      method: "POST",
      json: { lease_seconds: FLOOR_LEASE_SECONDS },
    });
  } catch (error) {
    const owner = ownerOf(error);
    if (owner) throw new FloorHeldError(owner);
    throw error;
  }
}

/** Heartbeat. False means the floor was lost — stop capturing. */
export async function renewAudioFloor(): Promise<boolean> {
  try {
    await apiFetch("/api/dictation/floor/claim", {
      method: "POST",
      json: { lease_seconds: FLOOR_LEASE_SECONDS },
    });
    return true;
  } catch {
    return false;
  }
}

export async function releaseAudioFloor(): Promise<void> {
  try {
    await apiFetch("/api/dictation/floor/release", { method: "POST" });
  } catch {
    /* the lease expires on its own — a failed release is never fatal */
  }
}
