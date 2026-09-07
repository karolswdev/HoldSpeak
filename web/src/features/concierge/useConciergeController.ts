// HS-170-03 — the Concierge controller.
// One screen: detect engines, propose a set, pick per group, apply.

import { useCallback, useEffect, useRef, useState } from "react";
import { readableError } from "../../lib/api";
import {
  conciergeDetect,
  conciergePropose,
  conciergeProbe,
  conciergeApply,
  conciergeDownload,
  conciergeTaskProbe,
  type Engine,
  type EngineState,
  type ProposalRow,
  type DetectResponse,
  type ProposeResponse,
  type Repair,
  type TaskProbeResponse,
} from "./api";

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
}

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
  setAddEngineUrl: (v: string) => void;
  checkNewEngine: () => void;
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
          return {
            group: r.group,
            label: r.label,
            engineId: r.engineId,
            host: r.host,
            state: r.state as EngineState,
            pickerOpen: false,
            alternatives: alts,
          };
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

  // Can apply: every group must be READY or explicitly OFF.
  // A group is OFF when the user picked OFF (engineId === "OFF", state === "READY").
  // A group with null engineId and WAITING state is NOT off -- it's unset.
  const canApply =
    setRows.length > 0 &&
    setRows.every(
      (r) => r.state === "READY" || r.engineId === "OFF",
    );

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
    setApplying(true);
    setError("");
    setApplyFailures([]);
    try {
      const rows = setRows.map((r) => ({
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
          // The one existing readiness signal (SettingsCore dispatches the same
          // event after a save). Faces holding an unfinished task recheck on it
          // instead of reloading and losing their draft.
          try {
            window.dispatchEvent(new Event("holdspeak:settings-updated"));
          } catch {
            // A page without a window still applied the set.
          }
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

  const addEngine = useCallback(() => {
    setAddEngineOpen(true);
  }, []);

  const checkNewEngine = useCallback(async () => {
    const url = addEngineUrl.trim();
    if (!url) return;
    setAddEngineChecking(true);
    try {
      const { apiFetch } = await import("../../lib/api");
      await apiFetch("/api/inference/model-library/define-endpoint", {
        method: "POST",
        json: {
          draft: {
            request_id: `concierge-${Date.now()}`,
            label: url,
            endpoint: url,
            model: "",
            requires_key: false,
          },
          secret: null,
        },
      });
      safe(() => {
        setAddEngineChecking(false);
        setAddEngineOpen(false);
        setAddEngineUrl("");
        void load(); // Re-detect
      });
    } catch (err) {
      safe(() => {
        setAddEngineChecking(false);
        setError(readableError(err));
      });
    }
  }, [addEngineUrl]); // eslint-disable-line react-hooks/exhaustive-deps

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
          setAddEngineUrl(repair.baseUrl);
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
    [downloadPreset, openPicker],
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
    setAddEngineUrl,
    checkNewEngine,
  };
}
