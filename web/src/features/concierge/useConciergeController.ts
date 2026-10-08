// HS-170-03 — the Concierge controller.
// One screen: detect engines, propose a set, pick per group, apply.

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, readableError } from "../../lib/api";
import { announceTaskReturn } from "../../desk/returnToTask";
import {
  conciergeDetect,
  conciergePropose,
  conciergeProbe,
  conciergeApply,
  conciergeDownload,
  conciergeTaskProbe,
  conciergeSummarySelection,
  checkEndpoint,
  defineEndpoint,
  type Engine,
  type EngineState,
  type ProposalRow,
  type DetectResponse,
  type ProposeResponse,
  type Repair,
  type SummaryAssignment,
  type TaskProbeResponse,
  type ApplyResponse,
  type GroupFit,
} from "./api";
import { endpointDraft, endpointHostPort, endpointProfileId } from "./endpointDraft";

/* ── Group glyphs — the seven user-visible groups ── */

export const GROUP_GLYPHS: Record<string, string> = {
  thoughts_notes: "•",     // bullet
  chat_practice: "■",      // black square
  writing_dictation: "–",  // en-dash (pen nib)
  speech_recognition: "∕", // division slash (tuning fork)
  meetings: "■",           // black square
  agents_tools: "◦",       // white bullet
  background: "○",         // white circle
};

/* ── Kind emblems ── */

export function kindEmblem(kind: string): string {
  switch (kind) {
    case "lan": return "LAN";
    case "local": return "MAC";
    case "cloud": return "API";
    case "preset": return "MAC";
    default: return "—";
  }
}

/* ── Human-readable size ── */

/* PHILO-15 10 (B18): ONE size rule for every face. The catalogue states
   download sizes in decimal units (2 740 937 888 bytes = 2.7 GB); first run
   said 2.7 GB and this face said 2.6 GB for the same file. First run's
   `formatBytes` is this function. */
export function humanSize(bytes: number | null | undefined): string | null {
  if (bytes == null || bytes <= 0) return null;
  if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(1)} GB`;
  if (bytes >= 1e6) return `${Math.round(bytes / 1e6)} MB`;
  if (bytes >= 1e3) return `${Math.round(bytes / 1e3)} KB`;
  return `${bytes} B`;
}

/* ── Hardware token string ── */

export function hardwareToken(hw: DetectResponse["hardware"]): string {
  const cap = hw?.capability;
  if (!cap) return "THIS MAC";
  const parts: string[] = ["THIS MAC"];
  if (cap.apple_silicon) parts.push("M‑SERIES");
  if (cap.ram_gb) parts.push(`${cap.ram_gb} GB`);
  return parts.join(" · ");
}

/* ── Latency token ── */

export function latencyToken(ms: number | null | undefined): string | null {
  if (ms == null) return null;
  return `${ms} MS`;
}

/* ── Engine host label for egress chips ── */

export function engineHostLabel(engine: Engine): string {
  if (engine.kind === "cloud") {
    return engine.host.toUpperCase();
  }
  if (engine.kind === "lan") {
    const suffix = engine.host.match(/^(\d+\.\d+\.\d+\.\d+)/) ? " · LAN" : "";
    return `${engine.host}${suffix}`.toUpperCase();
  }
  return "THIS DEVICE";
}

/* ── Engine host scope for egress chip color ── */

export function engineHostScope(engine: Engine): "local" | "cloud" {
  return engine.kind === "cloud" ? "cloud" : "local";
}

/* ── Concierge row types ── */

export interface FoundRow {
  engine: Engine;
  downloading: boolean;
  progress: { received: number; total: number } | null;
}

export interface SetRow {
  group: string;
  label: string;
  engineId: string | null;
  host: string;
  state: EngineState;
  pickerOpen: boolean;
  alternatives: Engine[];
  /** HS-201-09: this row is the APPLIED truth, not a proposal. */
  applied?: boolean;
  /** The applied engine's own label when detection no longer lists it. */
  appliedLabel?: string;
  /** PHILO-15 10 (B05): the work this engine cannot do in this group. */
  blocked?: string[];
  plainReason?: string;
  /** The authority's answer for every engine the picker offers. */
  fits?: Record<string, GroupFit>;
  /** A failed group's reason token from the last press (kept on reload). */
  failToken?: string;
}

/** PHILO-15 10 (B10): what the last press did, said on this face. */
export interface ApplyReceipt {
  /** `set` = Use these; `summaries` = Use this for summaries. */
  kind: "set" | "summaries";
  engine: string;
  host: string;
  ready: number;
  limited: number;
  failed: number;
  off: number;
  defaultSet: boolean;
  /** Every failed group, each with its reason token (Astra r1, finding 3). */
  failures: Array<{ group: string; label: string; token: string }>;
}

/** The receipt line: `USING · Qwen3.8 27B · 6 GROUPS · 4 LIMITED`. */
export function receiptLine(receipt: ApplyReceipt): string {
  const parts: string[] = [];
  if (receipt.engine) parts.push(`USING · ${receipt.engine.toUpperCase()}`);
  if (receipt.kind === "summaries") {
    parts.push("SUMMARIES");
  } else {
    const set = receipt.ready + receipt.limited;
    if (set > 0) parts.push(`${set} ${set === 1 ? "GROUP" : "GROUPS"}`);
    if (receipt.limited > 0) parts.push(`${receipt.limited} LIMITED`);
    if (receipt.off > 0) parts.push(`${receipt.off} OFF`);
  }
  if (receipt.defaultSet) parts.push("DEFAULT SET");
  // Astra r2 (finding 4): each cause ONCE. One group names itself; several
  // with one cause read `5 GROUPS · NO MODEL RECORD`. Each row keeps its own.
  const byToken = new Map<string, string[]>();
  for (const failure of receipt.failures) {
    byToken.set(failure.token, [...(byToken.get(failure.token) ?? []), failure.label]);
  }
  for (const [token, labels] of byToken) {
    parts.push(labels.length === 1 ? `${labels[0].toUpperCase()} · ${token}` : `${labels.length} GROUPS · ${token}`);
  }
  return parts.join(" · ");
}

/** The group's short name in a refusal: `WAITS · SPEECH DOWNLOAD`. */
export function waitsToken(group: string, label: string): string {
  const short = group === "speech_recognition" ? "SPEECH" : label.toUpperCase();
  return `WAITS · ${short} DOWNLOAD`;
}

/** The one group whose row IS the exact `meeting.deferred_analysis` choice. */
export const SUMMARY_GROUP = "meetings";

/** HS-201-09 — the rows one `Use these` may write: READY, or explicitly OFF.
 *  A WAITING group is left alone; it never blocks the groups beside it.
 *  PHILO-15 10: a LIMITED group is written (most of its work runs, and the
 *  receipt says what does not); UNKNOWN is written so the owner can try it;
 *  INCOMPATIBLE is never written. */
export function applicableSetRows<
  T extends { state: string; engineId: string | null },
>(rows: readonly T[]): T[] {
  return rows.filter(
    (r) =>
      r.state === "READY" ||
      r.state === "LIMITED" ||
      r.state === "UNKNOWN" ||
      r.engineId === "OFF",
  );
}

/* HS-201-09 (rehearsal defect 4) — the Meetings row reads the APPLIED
   assignment, never the proposal.  Reopening Models after the owner chose
   showed him a fresh proposal again, so the face forgot his choice and OFF
   came back as an engine. `summaryAssignment` is the same projection the
   deferred queue resolves; it is the only truth this row may draw. */
export function summaryRowFromAssignment(
  row: SetRow,
  assignment: SummaryAssignment | null,
  engines: Engine[],
): SetRow {
  if (!assignment) return row;
  if (assignment.status === "off") {
    return {
      ...row,
      engineId: "OFF",
      state: "READY" as EngineState,
      host: "",
      applied: true,
      appliedLabel: undefined,
    };
  }
  if (assignment.status !== "assigned" && assignment.status !== "attention") {
    return row;
  }
  // PHILO-15 10 (B05): the applied engine still serves only part of the
  // group; the proposal's LIMITED stands over the applied truth.
  // PHILO-15 10 (Astra r1, finding 1): the applied engine's state is the
  // authority's answer for it (`fits`); with no answer it is UNKNOWN.
  const engine = engines.find((e) => e.profileId === assignment.profileId);
  const fit = engine ? row.fits?.[engine.id] : undefined;
  const state: EngineState =
    assignment.status === "attention" ? "NOT_SET" : fit?.state ?? "UNKNOWN";
  if (engine) {
    return {
      ...row,
      engineId: engine.id,
      state,
      blocked: fit?.blocked,
      host: engineHostLabel(engine),
      applied: true,
      appliedLabel: undefined,
    };
  }
  return {
    ...row,
    engineId: assignment.profileId,
    state,
    host: (assignment.boundary ?? "").toUpperCase(),
    applied: true,
    appliedLabel: assignment.label ?? undefined,
  };
}

/** HS-201-09 — the Add-an-engine well's own state machine. */
export type AddEngineState =
  | "IDLE"
  | "CHECKING"
  | "READY"
  | "UNREACHABLE"
  /** PHILO-15 02: the server answered 401/403. */
  | "KEY_REQUIRED"
  /** PHILO-15 02: the typed key cannot ride in a header. */
  | "KEY_INVALID";

export interface AdjustRow {
  capabilityId: string;
  group: string;
  engineId: string | null;
  engineName: string;
  host: string;
}

/* ── Controller interface ── */

export interface ConciergeController {
  loading: boolean;
  error: string;
  // Detection
  engines: Engine[];
  foundCount: number;
  hardware: DetectResponse["hardware"];
  checkedAt: string;
  foundRows: FoundRow[];
  // Proposal
  setRows: SetRow[];
  receipt: ProposeResponse["receipt"];
  // Adjust
  adjustOpen: boolean;
  adjustRows: AdjustRow[];
  // HS-200-04 — the named repair states and the task probe
  repairs: Repair[];
  runRepair: (repair: Repair) => void;
  probeResult: TaskProbeResponse | null;
  probing: boolean;
  runTaskProbe: (confirmOffMachine?: boolean) => void;
  // State
  applying: boolean;
  applied: boolean;
  /** PHILO-15 10 (B10): the receipt of the last press, on this face. */
  applyReceipt: ApplyReceipt | null;
  canApply: boolean;
  applyFailures: Array<{ group: string; plainReason: string }>;
  // Add engine inline
  addEngineOpen: boolean;
  addEngineUrl: string;
  addEngineChecking: boolean;
  /** HS-201-09: the check's own answer, shown beside its verb. */
  addEngineState: AddEngineState;
  addEngineReason: string;
  addEngineModel: string;
  /** PHILO-15 10: the server's answer to "do you take tool calls?". */
  addEngineTools: "yes" | "no" | "unknown" | null;
  /** Astra r1: MY SERVER, the owner's word that the address is his own. */
  addEngineMyServer: boolean;
  setAddEngineMyServer: (v: boolean) => void;
  setAddEngineUrl: (v: string) => void;
  /** PHILO-15 02: the optional key for the endpoint (never stored here). */
  addEngineKey: string;
  setAddEngineKey: (v: string) => void;
  checkNewEngine: () => void;
  useNewEngineForSummaries: () => void;
  // Actions
  openPicker: (group: string) => void;
  closePicker: (group: string) => void;
  pickEngine: (group: string, engineId: string | null) => void;
  toggleAdjust: () => void;
  downloadPreset: (presetId: string) => void;
  checkCloud: (engineId: string) => void;
  apply: () => void;
  cancel: () => void;
  addEngine: () => void;
}

/* ── Controller hook ── */

export function useConciergeController(): ConciergeController {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [detection, setDetection] = useState<DetectResponse | null>(null);
  const [proposal, setProposal] = useState<ProposeResponse | null>(null);
  const [setRows, setSetRows] = useState<SetRow[]>([]);
  const [adjustOpen, setAdjustOpen] = useState(false);
  const [applying, setApplying] = useState(false);
  const [applied, setApplied] = useState(false);
  const [applyReceipt, setApplyReceipt] = useState<ApplyReceipt | null>(null);
  const [applyFailures, setApplyFailures] = useState<
    Array<{ group: string; plainReason: string }>
  >([]);
  const [downloadingEngines, setDownloadingEngines] = useState<
    Record<string, { received: number; total: number }>
  >({});
  const [repairs, setRepairs] = useState<Repair[]>([]);
  const [probeResult, setProbeResult] = useState<TaskProbeResponse | null>(null);
  const [probing, setProbing] = useState(false);
  const mountedRef = useRef(true);
  // Astra r1 (finding 3): the groups the last press failed, with their
  // tokens; a re-read of the proposal keeps them FAILED until the next press.
  const failedRef = useRef<Record<string, string>>({});

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const safe = useCallback(
    <T,>(fn: () => T): T | undefined => {
      if (mountedRef.current) return fn();
      return undefined;
    },
    [],
  );

  /* ── Load detection + proposal ── */

  const load = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    setError("");
    try {
      const det = await conciergeDetect();
      const prop = await conciergePropose();
      safe(() => {
        setDetection(det);
        setProposal(prop);
        setRepairs(det.repairs);
        // Astra r2 (finding 3): the failed groups are the HUB's record of
        // the last press (its receipt), so a reload or a reopen shows them.
        const lastFailures = det.lastApply?.failures ?? [];
        failedRef.current = Object.fromEntries(lastFailures.map((f) => [f.group, f.token]));
        if (lastFailures.length) {
          const labelOf = (group: string) =>
            prop.rows.find((r) => r.group === group)?.label ?? group;
          setApplyReceipt((current) =>
            current ?? {
              kind: "set",
              engine: "",
              host: "",
              ready: 0,
              limited: 0,
              failed: lastFailures.length,
              off: 0,
              defaultSet: false,
              failures: lastFailures.map((f) => ({ ...f, label: labelOf(f.group) })),
            },
          );
        }
        // Build set rows from proposal
        const rows: SetRow[] = prop.rows.map((r) => {
          // Build alternatives: all engines compatible with this group
          const alts = buildAlternatives(r.group, det.engines);
          const row: SetRow = {
            group: r.group,
            label: r.label,
            engineId: r.engineId,
            host: r.host,
            state: r.state as EngineState,
            pickerOpen: false,
            alternatives: alts,
            blocked: r.blocked,
            plainReason: r.plainReason,
            fits: r.fits,
          };
          const shown = r.group === SUMMARY_GROUP
            ? summaryRowFromAssignment(row, det.summaryAssignment, det.engines)
            : row;
          const failed = failedRef.current[r.group];
          return failed
            ? { ...shown, state: "UNREACHABLE" as EngineState, failToken: failed }
            : shown;
        });
        setSetRows(rows);
        setLoading(false);
      });
    } catch (err) {
      safe(() => {
        setError(readableError(err));
        setLoading(false);
      });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    void load();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /* ── Build alternatives for a group ── */

  function buildAlternatives(group: string, engines: Engine[]): Engine[] {
    if (group === "speech_recognition") {
      // Local whisper only
      return engines.filter(
        (e) =>
          e.kind === "local" &&
          e.name.toLowerCase().includes("whisper"),
      );
    }
    // All engines: ready engines first, then presets, then cloud
    // PHILO-15 10: the device's Whisper is a speech engine only.
    const ready = engines.filter(
      (e) =>
        e.state === "READY" &&
        e.kind !== "preset" &&
        !(e.kind === "local" && e.name.toLowerCase().includes("whisper")),
    );
    const presets = engines.filter((e) => e.kind === "preset");
    const cloud = engines.filter(
      (e) => e.kind === "cloud" && e.state === "READY",
    );
    // Deduplicate
    const seen = new Set<string>();
    const result: Engine[] = [];
    for (const e of [...ready, ...presets, ...cloud]) {
      if (!seen.has(e.id)) {
        seen.add(e.id);
        result.push(e);
      }
    }
    return result;
  }

  /* ── Derived values ── */

  const engines = detection?.engines ?? [];
  const foundCount = engines.filter(
    (e) => e.kind !== "preset" || e.state === "READY",
  ).length;
  const hardware = detection?.hardware ?? {};
  const checkedAt = detection?.checkedAt ?? "";

  const foundRows: FoundRow[] = engines.map((e) => ({
    engine: e,
    downloading: e.id in downloadingEngines,
    progress: downloadingEngines[e.id] ?? null,
  }));

  const receipt = proposal?.receipt ?? { groups: 0, engines: 0, waiting: 0 };

  // HS-201-09 (rehearsal defect 5) — Use these applies PER GROUP.
  //
  // It used to require EVERY row to be READY or explicitly OFF, so one
  // unrelated WAITING group (Speech recognition, waiting on a download)
  // disabled the whole apply: to get a summary engine the stranger first
  // had to switch OFF the thing that transcribes his meeting.  A group
  // that is READY or OFF is applicable on its own; a WAITING group is
  // simply not sent, and the service's own refusal for a WAITING row
  // (concierge_service.apply) stays exactly where it is.
  const applicableRows = applicableSetRows(setRows);
  const canApply = applicableRows.length > 0;

  // Build adjust rows from current set
  const adjustRows: AdjustRow[] = setRows.map((r) => {
    const engine = engines.find((e) => e.id === r.engineId);
    return {
      capabilityId: r.group,
      group: r.label,
      engineId: r.engineId,
      engineName: engine?.name ?? (r.engineId === "OFF" ? "OFF" : "—"),
      host: engine ? engineHostLabel(engine) : r.host.toUpperCase() || "—",
    };
  });

  /* ── Picker ── */

  const openPicker = useCallback(
    (group: string) => {
      setSetRows((prev) =>
        prev.map((r) =>
          r.group === group
            ? { ...r, pickerOpen: true }
            : { ...r, pickerOpen: false },
        ),
      );
    },
    [],
  );

  const closePicker = useCallback(
    (group: string) => {
      setSetRows((prev) =>
        prev.map((r) => (r.group === group ? { ...r, pickerOpen: false } : r)),
      );
    },
    [],
  );

  const pickEngine = useCallback(
    (group: string, engineId: string | null) => {
      setSetRows((prev) =>
        prev.map((r) => {
          if (r.group !== group) return r;
          if (engineId === null || engineId === "OFF") {
            return {
              ...r,
              engineId: "OFF",
              state: "READY" as EngineState,
              host: "",
              pickerOpen: false,
            };
          }
          const engine = engines.find((e) => e.id === engineId);
          // PHILO-15 10 (Astra r1, finding 1): the state of a pick is the
          // authority's answer for THIS engine in THIS group (`fits`), never
          // the engine's reachability. No answer -> UNKNOWN, never READY.
          const fit = r.fits?.[engineId];
          const newState: EngineState =
            engine?.kind === "preset"
              ? "WAITING"
              : fit?.state ?? "UNKNOWN";
          return {
            ...r,
            engineId,
            state: newState,
            blocked: fit?.blocked,
            plainReason: undefined,
            host: engine ? engineHostLabel(engine) : r.host,
            pickerOpen: false,
          };
        }),
      );

      // Probe the engine for latency
      if (engineId && engineId !== "OFF") {
        const engine = engines.find((e) => e.id === engineId);
        if (engine && engine.kind !== "preset") {
          // The probe can only say the engine is NOT there; it never makes
          // a group READY (Astra r1, finding 1).
          void conciergeProbe(engineId).then((result) => {
            if (result.state === "READY") return;
            safe(() => {
              setSetRows((prev) =>
                prev.map((r) =>
                  r.group === group && r.engineId === engineId
                    ? { ...r, state: "UNREACHABLE" as EngineState }
                    : r,
                ),
              );
            });
          });
        }
      }
    },
    [engines], // eslint-disable-line react-hooks/exhaustive-deps
  );

  /* ── Adjust ── */

  const toggleAdjust = useCallback(() => {
    setAdjustOpen((prev) => !prev);
  }, []);

  /* ── Download ── */

  const downloadPreset = useCallback(
    async (presetId: string) => {
      try {
        const engine = engines.find(
          (e) => e.kind === "preset" && e.presetId === presetId,
        );
        if (!engine) return;
        setDownloadingEngines((prev) => ({
          ...prev,
          [engine.id]: { received: 0, total: engine.sizeBytes ?? 0 },
        }));
        await conciergeDownload(presetId);
        // Download started -- in a real implementation we would poll
        // For now, we just mark it
      } catch (err) {
        safe(() => setError(readableError(err)));
      }
    },
    [engines], // eslint-disable-line react-hooks/exhaustive-deps
  );

  /* ── Cloud check ── */

  const checkCloud = useCallback(
    async (engineId: string) => {
      try {
        const result = await conciergeProbe(engineId, true);
        safe(() => {
          // Update the engine in detection
          setDetection((prev) => {
            if (!prev) return prev;
            return {
              ...prev,
              engines: prev.engines.map((e) =>
                e.id === engineId
                  ? { ...e, state: result.state, latencyMs: result.latencyMs }
                  : e,
              ),
            };
          });
        });
      } catch (err) {
        safe(() => setError(readableError(err)));
      }
    },
    [], // eslint-disable-line react-hooks/exhaustive-deps
  );

  /* ── Apply ── */

  const apply = useCallback(async () => {
    if (!canApply) return;
    // HS-200-41 (return-to-task, focus half): the control the owner pressed
    // to finish setup, captured HERE — synchronously, before the await.
    // After the round trip `document.activeElement` can no longer tell his
    // hand from the DOM's, and that is exactly the difference the
    // do-not-steal rule turns on (`desk/returnToTask.ts`).
    const from =
      typeof document !== "undefined"
        ? (document.activeElement as HTMLElement | null)
        : null;
    setApplying(true);
    setError("");
    setApplyFailures([]);
    try {
      const rows = applicableRows.map((r) => ({
        group: r.group,
        engineId: r.engineId,
        state: r.state,
      }));
      const resp = await conciergeApply(rows);
      safe(() => {
        setApplying(false);
        // Read per-group results. Every failed group is kept, with its
        // reason token (Astra r1, finding 3), and survives the re-read.
        const labelOf = (group: string) =>
          setRows.find((r) => r.group === group)?.label ?? group;
        const results = resp.results ?? [];
        const failures = results
          .filter((result) => result.state === "FAILED" || result.state === "SKIPPED")
          .map((result) => ({
            group: result.group,
            label: labelOf(result.group),
            token: result.token || "FAILED",
          }));
        failedRef.current = Object.fromEntries(failures.map((f) => [f.group, f.token]));
        if (results.length) {
          setSetRows((prev) =>
            prev.map((r) => {
              const result = results.find((res) => res.group === r.group);
              if (!result) return r;
              if (result.state === "FAILED" || result.state === "SKIPPED") {
                return { ...r, state: "UNREACHABLE" as EngineState, failToken: result.token || "FAILED" };
              }
              if (
                result.state === "READY" ||
                result.state === "LIMITED" ||
                result.state === "INCOMPATIBLE" ||
                result.state === "UNKNOWN"
              ) {
                return {
                  ...r,
                  state: result.state as EngineState,
                  blocked: result.blocked,
                  failToken: undefined,
                };
              }
              return r;
            }),
          );
        }
        setApplyFailures(failures.map((f) => ({ group: f.group, plainReason: f.token })));
        setApplied(failures.length === 0);
        // PHILO-15 10 (B10): the window STAYS and says what happened —
        // the engine, the groups, what is limited, what failed. It used to
        // close itself with no receipt.
        const summary = resp.summary ?? ({} as ApplyResponse["summary"]);
        setApplyReceipt({
          kind: "set",
          engine: summary.engine ?? "",
          host: summary.host ?? "",
          ready: summary.ready ?? 0,
          limited: summary.limited ?? 0,
          failed: failures.length,
          off: summary.off ?? 0,
          defaultSet: Boolean(summary.default),
          failures,
        });
        if (failures.length === 0) {
          // The one existing readiness signal (SettingsCore dispatches the
          // same event after a save). Faces holding an unfinished task
          // recheck on it instead of reloading and losing their draft.
          announceTaskReturn(from);
        }
        // The repairs and the set, read again without a LOADING flash.
        void load(true);
      });
    } catch (err) {
      safe(() => {
        setApplying(false);
        // Astra r1, finding 3: the server's refusal of a waiting group is a
        // token in the receipt, not its sentence in an alert.
        const payload =
          err instanceof ApiError && err.payload && typeof err.payload === "object"
            ? (err.payload as Record<string, unknown>)
            : null;
        if (payload?.code === "concierge_waiting_group") {
          const group = String(payload.group ?? "");
          const label = setRows.find((r) => r.group === group)?.label ?? group;
          setApplyReceipt({
            kind: "set",
            engine: "",
            host: "",
            ready: 0,
            limited: 0,
            failed: 1,
            off: 0,
            defaultSet: false,
            failures: [{ group, label, token: waitsToken(group, label) }],
          });
          return;
        }
        setError(readableError(err));
      });
    }
  }, [canApply, setRows, load]); // eslint-disable-line react-hooks/exhaustive-deps

  /* ── Cancel ── */

  const cancel = useCallback(() => {
    import("../../desk/store").then(({ useDesk }) => {
      useDesk.getState().closeSurfaceWindow("surface-concierge");
    });
  }, []);

  /* ── Add engine (unfolds the inline StringGadget row) ── */

  const [addEngineOpen, setAddEngineOpen] = useState(false);
  const [addEngineUrl, setAddEngineUrl] = useState("");
  const [addEngineChecking, setAddEngineChecking] = useState(false);
  const [addEngineState, setAddEngineState] =
    useState<AddEngineState>("IDLE");
  const [addEngineReason, setAddEngineReason] = useState("");
  const [addEngineModel, setAddEngineModel] = useState("");
  const [addEngineTools, setAddEngineTools] = useState<"yes" | "no" | "unknown" | null>(null);
  // Astra r1 (finding 4): the owner says this address is his own server.
  // Only then may the Check send its 1-token request to a keyed or named
  // address.
  const [addEngineMyServer, setAddEngineMyServer] = useState(false);
  const [addEngineKey, setAddEngineKeyState] = useState("");
  const addEngineKeyRef = useRef("");
  // HS-201-09 (counsel finding 3): the address a check ANSWERED for. A
  // check is a statement about one address; the moment the owner edits the
  // field that statement is no longer about what he is looking at, so
  // READY and the model it named are dropped and a late answer for the
  // old address is discarded instead of being shown as the new one's.
  const addEngineUrlRef = useRef("");

  const editAddEngineUrl = useCallback((value: string) => {
    addEngineUrlRef.current = value;
    setAddEngineUrl((previous) => {
      if (previous.trim() !== value.trim()) {
        setAddEngineState("IDLE");
        setAddEngineModel("");
        setAddEngineReason("");
      }
      return value;
    });
  }, []);

  // PHILO-15 02: a check is a statement about one address AND one key; a
  // changed key drops the old answer the same way a changed address does.
  const editAddEngineKey = useCallback((value: string) => {
    addEngineKeyRef.current = value;
    setAddEngineKeyState((previous) => {
      if (previous.trim() !== value.trim()) {
        setAddEngineState("IDLE");
        setAddEngineModel("");
        setAddEngineReason("");
      }
      return value;
    });
  }, []);

  const addEngine = useCallback(() => {
    setAddEngineOpen(true);
    setAddEngineKeyState("");
    addEngineKeyRef.current = "";
    setAddEngineState("IDLE");
    setAddEngineReason("");
    setAddEngineModel("");
    addEngineUrlRef.current = "";
  }, []);

  /* HS-201-09 — Check: the HUB reads the endpoint's /models and names the
     model it serves.  The browser never leaves this machine; the reason for
     a refusal is the server's own plain words, shown beside the verb. */
  const checkNewEngine = useCallback(async () => {
    const url = addEngineUrl.trim();
    if (!url) return;
    const key = addEngineKey.trim();
    setAddEngineChecking(true);
    setAddEngineState("CHECKING");
    setAddEngineReason("");
    setAddEngineModel("");
    setAddEngineTools(null);
    try {
      const result = await checkEndpoint(url, key, addEngineMyServer);
      // The field moved on while this was in flight: the answer is about
      // an address the owner is no longer looking at. Drop the ANSWER —
      // but end the flight, or `Check` stays disabled for ever and the
      // corrected address can never be checked at all (round 2 residual).
      if (addEngineUrlRef.current.trim() !== url || addEngineKeyRef.current.trim() !== key) {
        safe(() => setAddEngineChecking(false));
        return;
      }
      safe(() => {
        setAddEngineChecking(false);
        if (result.ok && result.models.length > 0) {
          setAddEngineState("READY");
          setAddEngineModel(result.models[0]);
          setAddEngineTools(result.tools ?? "unknown");
          setAddEngineReason("");
          return;
        }
        if (result.reason === "key_required") {
          setAddEngineState("KEY_REQUIRED");
          setAddEngineReason("");
          return;
        }
        if (result.reason === "key_invalid") {
          setAddEngineState("KEY_INVALID");
          setAddEngineReason(result.detail);
          return;
        }
        setAddEngineState("UNREACHABLE");
        setAddEngineReason(result.detail);
      });
    } catch (err) {
      if (addEngineUrlRef.current.trim() !== url || addEngineKeyRef.current.trim() !== key) {
        safe(() => setAddEngineChecking(false));
        return;
      }
      safe(() => {
        setAddEngineChecking(false);
        setAddEngineState("UNREACHABLE");
        setAddEngineReason(readableError(err));
      });
    }
  }, [addEngineUrl, addEngineKey, addEngineMyServer]); // eslint-disable-line react-hooks/exhaustive-deps

  /* HS-201-09 — the one gesture that finishes setup from the face:
     define the endpoint through the Model Library command (which never
     touches assignments), then make ONE explicit summary selection with
     the immutable profile revision that command just minted. */
  const useNewEngineForSummaries = useCallback(async () => {
    const url = addEngineUrl.trim();
    if (!url || !addEngineModel) return;
    const key = addEngineKey.trim();
    // HS-201-09 (counsel finding 1): this IS the setup gesture, so it ends
    // the way ordinary Apply ends (the block at `apply` above) — the
    // window closes, the one readiness signal fires so the arrival drops
    // its SETUP row without another gesture, and focus goes back to the
    // verb the owner left. Captured synchronously, before the await.
    const from =
      typeof document !== "undefined"
        ? (document.activeElement as HTMLElement | null)
        : null;
    setAddEngineChecking(true);
    setAddEngineReason("");
    try {
      const defined = await defineEndpoint(
        endpointDraft({
          url,
          model: addEngineModel,
          requestId: `concierge-${Date.now()}`,
          requiresKey: Boolean(key),
          // An engine already saved for this address re-saves at its own
          // revision (a changed record mints the next one).
          expectedProfileRevision:
            engines.find((e) => e.profileId === endpointProfileId(url))?.profileRevision ?? 0,
        }),
        key,
      );
      if (!defined.profileId || defined.profileRevision < 1) {
        throw new Error("The engine was saved without a model record.");
      }
      const selection = await conciergeSummarySelection({
        commandId: `concierge-summary-${Date.now()}`,
        expectedAssignmentRevision:
          detection?.summaryAssignment?.assignmentRevision ?? 0,
        profileId: defined.profileId,
        profileRevision: defined.profileRevision,
        // Astra r1 (finding 2): the engine he chose also answers the rest
        // of his AI work, once, when no default ever existed.
        setDefault: true,
      });
      // HTTP 200 is not the answer; the result's own state is.
      if (selection.state !== "READY") {
        safe(() => {
          setAddEngineChecking(false);
          setAddEngineState("UNREACHABLE");
          setAddEngineReason(
            selection.plainReason || "The summary engine could not be selected.",
          );
        });
        return;
      }
      safe(() => {
        setAddEngineChecking(false);
        setAddEngineOpen(false);
        setAddEngineUrl("");
        addEngineUrlRef.current = "";
        setAddEngineKeyState("");
        addEngineKeyRef.current = "";
        setAddEngineState("IDLE");
        setAddEngineModel("");
        setAddEngineTools(null);
        setAddEngineReason("");
        setApplied(true);
        // PHILO-15 10 (B10): the window stays and says what was set.
        setApplyReceipt({
          kind: "summaries",
          engine: addEngineModel || selection.summaryAssignment?.label || "",
          host: endpointHostPort(url),
          ready: 1,
          limited: 0,
          failed: 0,
          off: 0,
          defaultSet: Boolean(selection.defaultSet),
          failures: [],
        });
        void load(true); // The set now proposes this engine.
        announceTaskReturn(from);
      });
    } catch (err) {
      safe(() => {
        setAddEngineChecking(false);
        setAddEngineState("UNREACHABLE");
        setAddEngineReason(readableError(err));
      });
    }
  }, [addEngineUrl, addEngineModel, addEngineKey, detection, engines]); // eslint-disable-line react-hooks/exhaustive-deps

  /* ── HS-200-04: one verb per repair state, each opening an existing control ── */

  const runRepair = useCallback(
    (repair: Repair) => {
      switch (repair.control) {
        case "model_library":
          if (repair.presetId) {
            void downloadPreset(repair.presetId);
            return;
          }
          if (repair.groups[0]) openPicker(repair.groups[0]);
          return;
        case "endpoint_editor":
          setAddEngineOpen(true);
          // Through the invalidating setter, so the ref that guards a
          // late check answer knows which address the field now holds.
          editAddEngineUrl(repair.baseUrl);
          return;
        case "engine_picker":
          if (repair.groups[0]) openPicker(repair.groups[0]);
          return;
        case "connections":
          void import("../../desk/shell").then(({ openSurfaceOr }) =>
            openSurfaceOr("configure-integrations", "/settings"),
          );
          return;
        default:
          return;
      }
    },
    [downloadPreset, openPicker, editAddEngineUrl],
  );

  const runTaskProbe = useCallback(
    async (confirmOffMachine?: boolean) => {
      setProbing(true);
      setError("");
      try {
        const result = await conciergeTaskProbe(undefined, confirmOffMachine);
        safe(() => {
          setProbing(false);
          setProbeResult(result);
        });
      } catch (err) {
        safe(() => {
          setProbing(false);
          setError(readableError(err));
        });
      }
    },
    [], // eslint-disable-line react-hooks/exhaustive-deps
  );

  return {
    loading,
    error,
    engines,
    foundCount,
    hardware,
    checkedAt,
    foundRows,
    setRows,
    receipt,
    adjustOpen,
    adjustRows,
    repairs,
    runRepair,
    probeResult,
    probing,
    runTaskProbe,
    applying,
    applied,
    applyReceipt,
    canApply,
    openPicker,
    closePicker,
    pickEngine,
    toggleAdjust,
    downloadPreset,
    checkCloud,
    apply,
    cancel,
    addEngine,
    applyFailures,
    addEngineOpen,
    addEngineUrl,
    addEngineChecking,
    addEngineState,
    addEngineReason,
    addEngineModel,
    addEngineTools,
    addEngineMyServer,
    setAddEngineMyServer,
    setAddEngineUrl: editAddEngineUrl,
    addEngineKey,
    setAddEngineKey: editAddEngineKey,
    checkNewEngine,
    useNewEngineForSummaries,
  };
}
