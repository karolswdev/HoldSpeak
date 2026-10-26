// Parked 2026-10-25 (owner ruling, UX-CANON A.9 amended): the lane draws no
// draft host chip, so this hook had no caller. Lifted whole from LaneWindow.tsx;
// imports are not repaired (the folder is not compiled or collected).
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiFetch } from "../../../lib/api";
import { useDesk } from "../../store";
import { egressFor } from "../../surface/egress";
import { useOnDeskChanged } from "../../useDeskChangedRefresh";

const DRAFT_CAPABILITY = "background.cadence_draft";

/* ── the drafting model's host ────────────────────────────────────── */

type AssignmentEntry = { profile_id?: string; label?: string; boundary?: string };
type AssignmentRoster = { task_overrides?: Array<{ id?: string; effective?: { assignment?: { entries?: AssignmentEntry[] } | null } }> };

/** The drafting model's entry, read now. `effective` is the whole chain
 * (exact, group, global): with only the Default for AI work, drafts inherit
 * it (PHILO-15 05). No cache: a changed default shows at once (Astra r1). */
function readDraftEntry(capability: string): Promise<AssignmentEntry | null> {
  return apiFetch<AssignmentRoster>("/api/inference/assignments").then((body) => {
    const row = (body?.task_overrides ?? []).find((r) => r?.id === capability);
    return row?.effective?.assignment?.entries?.[0] ?? null;
  });
}

/** Owner ruling 2026-10-25: the lane draws no draft host chip; this hook
 * stays for its tests and a later caller that names the engine by name.
 * The label of the model that drafts answers: its endpoint's host
 * (`API.ANTHROPIC.COM`, `192.168.1.43 · LAN`, `THIS DEVICE`), else the
 * model's name; `NOT SET` when no model is assigned to drafts and no Default
 * for AI work exists (drafts inherit the default, PHILO-15 05). Read on every
 * open and again after any desk write (`desk_changed`: the Settings and the
 * Concierge assign through mutating `/api` requests, which announce it). */
export function useDraftEgress(
  enabled: boolean,
  /** PHILO-15 B53: the Room's Draft update names its own model's host. */
  capability: string = DRAFT_CAPABILITY,
): {
  label: string;
  scope?: "local" | "mixed" | "cloud" | "remote";
  /** PHILO-17 U31: true an engine is set, false none is, undefined not read yet. */
  assigned?: boolean;
  /** The first read failed: nothing is known (Try again with `retry`). */
  failed?: boolean;
  retry?: () => void;
} {
  const targets = useDesk((s) => s.inferenceTargets);
  const [entry, setEntry] = useState<AssignmentEntry | null | undefined>(undefined);
  const [readFailed, setReadFailed] = useState(false);
  const seq = useRef(0);
  const read = useCallback(() => {
    const mine = ++seq.current;
    setReadFailed(false);
    void readDraftEntry(capability)
      .then((e) => {
        if (seq.current === mine) setEntry(e);
      })
      .catch(() => {
        // The last read stays on the glass when a re-read fails; with no
        // read yet, the failure is said (never taken as "no engine").
        if (seq.current === mine) setReadFailed(true);
      });
  }, [capability]);
  useEffect(() => {
    if (!enabled) return;
    read();
    return () => {
      seq.current += 1; // an answer after close is dropped
    };
  }, [enabled, read]);
  useOnDeskChanged(() => {
    if (enabled) read();
  });
  return useMemo(() => {
    // PHILO-17 U31: `assigned` says if an engine is set (undefined: not read yet).
    if (entry === undefined) return { label: "NOT SET", assigned: undefined, failed: readFailed, retry: read };
    if (!entry) return { label: "NOT SET", assigned: false, retry: read };
    const target = targets.find((t) => t.profile_id === entry.profile_id || t.id === entry.profile_id);
    let host = "";
    if (target?.endpoint) {
      try {
        host = new URL(target.endpoint).hostname;
      } catch {
        host = "";
      }
    }
    // The assignment projection names a this-device entry `local`; the
    // deployment revision names it `same_device` (PHILO-15 05: a local
    // default read its model label as a cloud host).
    if (!host && [entry.boundary, target?.boundary].some((b) => b === "same_device" || b === "local")) host = "same_device";
    const egress = egressFor(host || entry.label || "");
    // No host to read: the chip names the model (its label), and its scope is
    // the entry's own boundary, so a LAN default never reads as cloud.
    const lan = !host && ["private_network", "mesh"].includes(String(entry.boundary ?? target?.boundary ?? ""));
    return { label: (egress.label || "NOT SET").toUpperCase(), scope: lan ? "local" : egress.scope, assigned: true, retry: read };
  }, [entry, targets, readFailed, read]);
}

/** Test seam (the chip keeps no cache since PHILO-15 05 r1). */
export function __resetDraftEgress(): void {}
