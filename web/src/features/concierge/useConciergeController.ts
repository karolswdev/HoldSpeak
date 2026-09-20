// HS-170-03 — the Concierge controller.
// One screen: detect engines, propose a set, pick per group, apply.

import { useCallback, useEffect, useRef, useState } from "react";
import { readableError } from "../../lib/api";
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
} from "./api";
import { endpointDraft } from "./endpointDraft";

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

export function humanSize(bytes: number | null | undefined): string | null {
  if (bytes == null || bytes <= 0) return null;
  if (bytes >= 1_073_741_824) return `${(bytes / 1_073_741_824).toFixed(1)} GB`;
  if (bytes >= 1_048_576) return `${Math.round(bytes / 1_048_576)} MB`;
  if (bytes >= 1024) return `${Math.round(bytes / 1024)} KB`;
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
}

/** The one group whose row IS the exact `meeting.deferred_analysis` choice. */
export const SUMMARY_GROUP = "meetings";

/** HS-201-09 — the rows one `Use these` may write: READY, or explicitly OFF.
 *  A WAITING group is left alone; it never blocks the groups beside it. */
export function applicableSetRows<
  T extends { state: string; engineId: string | null },
>(rows: readonly T[]): T[] {
  return rows.filter((r) => r.state === "READY" || r.engineId === "OFF");
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
  const state: EngineState =
    assignment.status === "attention" ? "NOT_SET" : "READY";
  const engine = engines.find((e) => e.profileId === assignment.profileId);
  if (engine) {
    return {
      ...row,
      engineId: engine.id,
      state,
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
export type AddEngineState = "IDLE" | "CHECKING" | "READY" | "UNREACHABLE";

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
  receipt: { groups: number; engines: number; waiting: number };
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
  setAddEngineUrl: (v: string) => void;
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

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const det = await conciergeDetect();
      const prop = await conciergePropose();
      safe(() => {
        setDetection(det);
        setProposal(prop);
        setRepairs(det.repairs);
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
          };
          return r.group === SUMMARY_GROUP
            ? summaryRowFromAssignment(row, det.summaryAssignment, det.engines)
            : row;
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
    const ready = engines.filter(
      (e) => e.state === "READY" && e.kind !== "preset",
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
          const newState: EngineState =
            engine?.state === "READY"
              ? "READY"
              : engine?.kind === "preset"
                ? "WAITING"
                : "CHECKING";
          return {
            ...r,
            engineId,
            state: newState,
            host: engine ? engineHostLabel(engine) : r.host,
            pickerOpen: false,
          };
        }),
      );

      // Probe the engine for latency
      if (engineId && engineId !== "OFF") {
        const engine = engines.find((e) => e.id === engineId);
        if (engine && engine.kind !== "preset") {
          void conciergeProbe(engineId).then((result) => {
            safe(() => {
              setSetRows((prev) =>
                prev.map((r) =>
                  r.group === group
                    ? { ...r, state: result.state as EngineState }
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
        // Read per-group results: update row states and collect failures
        const failures: Array<{ group: string; plainReason: string }> = [];
        if (resp.results) {
          setSetRows((prev) =>
            prev.map((r) => {
              const result = resp.results.find((res) => res.group === r.group);
              if (!result) return r;
              if (result.state === "FAILED") {
                failures.push({
                  group: r.group,
                  plainReason: result.plainReason ?? "Apply failed",
                });
                return { ...r, state: "UNREACHABLE" as EngineState };
              }
              if (result.state === "READY") {
                return { ...r, state: "READY" as EngineState };
              }
              return r;
            }),
          );
        }
        setApplyFailures(failures);
        setApplied(failures.length === 0);
        if (failures.length === 0) {
          // The one existing readiness signal (SettingsCore dispatches the
          // same event after a save). Faces holding an unfinished task
          // recheck on it instead of reloading and losing their draft —
          // and now focus goes back to the verb the owner left, which is
          // the second half of the ratified behaviour (design D2(a)).
          //
          // The window closes first, because D2(a) says it does: leaving
          // the Concierge open over the Room while focus jumps behind it
          // is the bug, not the fix.
          void import("../../desk/store").then(({ useDesk }) => {
            useDesk.getState().closeSurfaceWindow("surface-concierge");
          }).catch(() => {
            // A page without the desk store still applied the set.
          });
          announceTaskReturn(from);
        }
      });
    } catch (err) {
      safe(() => {
        setApplying(false);
        setError(readableError(err));
      });
    }
  }, [canApply, setRows]); // eslint-disable-line react-hooks/exhaustive-deps

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

  const addEngine = useCallback(() => {
    setAddEngineOpen(true);
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
    setAddEngineChecking(true);
    setAddEngineState("CHECKING");
    setAddEngineReason("");
    setAddEngineModel("");
    try {
      const result = await checkEndpoint(url);
      // The field moved on while this was in flight: the answer is about
      // an address the owner is no longer looking at.
      if (addEngineUrlRef.current.trim() !== url) return;
      safe(() => {
        setAddEngineChecking(false);
        if (result.ok && result.models.length > 0) {
          setAddEngineState("READY");
          setAddEngineModel(result.models[0]);
          setAddEngineReason("");
          return;
        }
        setAddEngineState("UNREACHABLE");
        setAddEngineReason(result.detail);
      });
    } catch (err) {
      if (addEngineUrlRef.current.trim() !== url) return;
      safe(() => {
        setAddEngineChecking(false);
        setAddEngineState("UNREACHABLE");
        setAddEngineReason(readableError(err));
      });
    }
  }, [addEngineUrl]); // eslint-disable-line react-hooks/exhaustive-deps

  /* HS-201-09 — the one gesture that finishes setup from the face:
     define the endpoint through the Model Library command (which never
     touches assignments), then make ONE explicit summary selection with
     the immutable profile revision that command just minted. */
  const useNewEngineForSummaries = useCallback(async () => {
    const url = addEngineUrl.trim();
    if (!url || !addEngineModel) return;
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
        }),
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
        setAddEngineState("IDLE");
        setAddEngineModel("");
        setAddEngineReason("");
        setApplied(true);
        void load(); // Re-detect, for the moment before the window goes.
        void import("../../desk/store")
          .then(({ useDesk }) => {
            useDesk.getState().closeSurfaceWindow("surface-concierge");
          })
          .catch(() => {
            // A page without the desk store still assigned the engine.
          });
        announceTaskReturn(from);
      });
    } catch (err) {
      safe(() => {
        setAddEngineChecking(false);
        setAddEngineState("UNREACHABLE");
        setAddEngineReason(readableError(err));
      });
    }
  }, [addEngineUrl, addEngineModel, detection]); // eslint-disable-line react-hooks/exhaustive-deps

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
    setAddEngineUrl: editAddEngineUrl,
    checkNewEngine,
    useNewEngineForSummaries,
  };
}
