// PHILO-16 (C) — the Runs on controller.
//
// Reads the roster first (the jobs paint at once) and the detection beside
// it (engines fill in). Every drop writes the job's whole chain at once
// (`/api/inference/assignments/set`, CAS on the row's own revision); a 409
// re-reads and redraws. Undo writes the previous chain back (a stack).
// Meetings also writes the exact `meeting.deferred_analysis` row through the
// Concierge's summary selection, because the meeting queue reads only that
// row's sources (HS-201-05, §12). Try it, Download and Use it run the real
// routes; an off-machine Try waits for the owner's press (Article III).

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ApiError } from "../../lib/api";
import { announceTaskReturn } from "../../desk/returnToTask";
import {
  checkEndpoint,
  conciergeDownload,
  conciergeProbe,
  conciergeSummarySelection,
  conciergeTaskProbe,
  defineEndpoint,
  type SummaryAssignment,
} from "../concierge/api";
import { endpointDraft, endpointHostPort, endpointProfileId } from "../concierge/endpointDraft";
import { startCapture, stopAndTranscribe, cancelCapture } from "../../lib/speakToFill";
import { patchChain } from "../../desk/surface/switchboardGeometry";
import {
  clearChain,
  readAcquisition,
  readDetection,
  readRoster,
  writeChain,
  type AssignmentScope,
  type Detection,
  type Roster,
  type RosterEntry,
} from "./api";
import {
  DEFAULT_JOB,
  MEETINGS_JOB,
  SPEECH_JOB,
  THOUGHTS_JOB,
  accepts as acceptsRule,
  buildEngines,
  hostLabel,
  jobForScope,
  limitTokens,
  offMachine,
  ownEntries,
  rosterId,
  type BoardEngine,
} from "./model";

/** The probeable capability (route_probe.py PROBE_CAPABILITIES): Ask, in
 *  Thoughts & notes. Every other job's Try it asks its first engine. */
export const PROBE_CAPABILITY = "ask.answer";
const POLL_MS = 1000;

export interface Egress {
  label: string;
  scope: "local" | "cloud";
}

export interface JobResult {
  tone: "ok" | "danger" | "busy";
  /** Tokens, joined with ` · ` on the face. */
  tokens: string[];
}

export interface Receipt {
  text: string;
  tone?: "danger";
}

interface UndoStep {
  job: string;
  entries: Array<{ profile_id: string; profile_revision: number }>;
  summary?: SummaryAssignment | null;
}

export type AddState = "IDLE" | "CHECKING" | "READY" | "UNREACHABLE" | "KEY_REQUIRED" | "KEY_INVALID";

function clock(): string {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
}

/** A.8: a latency the probe did not report (or reported as 0) is no token. */
export function msToken(ms: number | null | undefined): string[] {
  return typeof ms === "number" && ms > 0 ? [`${ms} MS`] : [];
}

function scopeFor(job: string): AssignmentScope {
  return job === DEFAULT_JOB ? { kind: "global" } : { kind: "group", group_id: job };
}

function codeToken(err: unknown): string {
  if (err instanceof ApiError && err.payload && typeof err.payload === "object") {
    const code = String((err.payload as Record<string, unknown>).code ?? "");
    if (code === "inference_assignment_incompatible") return "INCOMPATIBLE";
    if (code === "inference_assignment_binding_missing") return "NO BINDING";
    if (code === "inference_assignment_profile_missing") return "NO MODEL RECORD";
    if (code) return code.replace(/^inference_assignment_/, "").replace(/_/g, " ").toUpperCase();
  }
  return "NOT SAVED";
}

function isConflict(err: unknown): boolean {
  return (
    err instanceof ApiError &&
    err.status === 409 &&
    String((err.payload as Record<string, unknown> | null)?.code ?? "") ===
      "inference_assignment_revision_conflict"
  );
}

export function useRunsOn(scope?: string) {
  const [roster, setRoster] = useState<Roster | null>(null);
  const [detection, setDetection] = useState<Detection | null>(null);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [egress, setEgress] = useState<Egress | null>(null);
  const [results, setResults] = useState<Record<string, JobResult>>({});
  const [trying, setTrying] = useState<{ job: string; engine: string } | null>(null);
  const [listening, setListening] = useState(false);
  const [pending, setPending] = useState<{ job: string; host: string; scope: Egress["scope"] } | null>(null);
  const [downloads, setDownloads] = useState<Record<string, number>>({});
  const [undoStack, setUndoStack] = useState<UndoStep[]>([]);
  const [busy, setBusy] = useState(false);
  const mounted = useRef(true);
  const detectionRef = useRef<Promise<Detection | null> | null>(null);
  const timers = useRef(new Map<string, ReturnType<typeof setInterval>>());
  const scopeApplied = useRef(false);

  useEffect(() => {
    mounted.current = true;
    const live = timers.current;
    return () => {
      mounted.current = false;
      for (const timer of live.values()) clearInterval(timer);
      live.clear();
    };
  }, []);

  const loadRoster = useCallback(async () => {
    try {
      const next = await readRoster();
      if (mounted.current) setRoster(next);
      return next;
    } catch (err) {
      if (mounted.current) setError(err instanceof Error ? err.message : "Could not read Runs on.");
      return null;
    }
  }, []);

  const loadDetection = useCallback(() => {
    const promise = readDetection()
      .then((next) => {
        if (mounted.current) setDetection(next);
        return next;
      })
      .catch(() => null);
    detectionRef.current = promise;
    return promise;
  }, []);

  useEffect(() => {
    // The roster paints the jobs first; the detection's LAN probes may take
    // seconds and never hold the first paint.
    void loadRoster();
    void loadDetection();
  }, [loadRoster, loadDetection]);

  // A caller that named a job (`open-concierge` with a scope) opens on it.
  useEffect(() => {
    if (scopeApplied.current || !roster) return;
    scopeApplied.current = true;
    const job = jobForScope(scope, roster);
    if (job) setSelected(job);
  }, [roster, scope]);

  const engines = useMemo(() => buildEngines(roster, detection), [roster, detection]);
  const engineByKey = useCallback((key: string) => engines.find((e) => e.key === key), [engines]);
  const rowOf = useCallback(
    (job: string) => roster?.rows.find((row) => row.id === rosterId(job)),
    [roster],
  );

  const accepts = useCallback(
    (job: string, key: string) => acceptsRule(job, engineByKey(key)),
    [engineByKey],
  );

  /* ── the summary row (Meetings) ── */

  const writeSummary = useCallback(
    async (target: { profileId: string; profileRevision: number } | null, current: SummaryAssignment | null) => {
      if (target) {
        const answer = await conciergeSummarySelection({
          commandId: `runson-summary-${Date.now()}`,
          expectedAssignmentRevision: current?.assignmentRevision ?? 0,
          profileId: target.profileId,
          profileRevision: target.profileRevision,
        });
        if (answer.summaryAssignment && mounted.current) {
          setDetection((prev) => (prev ? { ...prev, summaryAssignment: answer.summaryAssignment } : prev));
        }
        return answer.state === "READY" ? null : answer.state === "CONFLICT" ? "CHANGED ELSEWHERE" : "NOT SAVED";
      }
      if (current && current.status === "assigned" && current.assignmentRevision > 0) {
        await clearChain({
          scope: { kind: "capability", capability_id: "meeting.deferred_analysis" },
          capabilityId: "meeting.deferred_analysis",
          expectedRevision: current.assignmentRevision,
        });
        void loadDetection();
      }
      return null;
    },
    [loadDetection],
  );

  /* ── a drop ── */

  const patch = useCallback(
    async (job: string, key: string, asFallback: boolean) => {
      const engine = engineByKey(key);
      const row = rowOf(job);
      if (!engine?.profileId || !row) return;
      const verdict = acceptsRule(job, engine);
      if (!verdict.ok) {
        setReceipt({ text: `REFUSED · ${verdict.reason}`, tone: "danger" });
        return;
      }
      const own = ownEntries(row);
      const revisions = new Map(own.map((e) => [e.profile_id, e.profile_revision]));
      const nextKeys = patchChain(
        own.map((e) => e.profile_id),
        engine.profileId,
        asFallback,
      );
      const entries = nextKeys.map((id) => ({
        profile_id: id,
        profile_revision: revisions.get(id) ?? engineByKey(id)?.profileRevision ?? 0,
      }));
      setBusy(true);
      // Meetings writes the summary row too: it needs the detection's
      // summary revision, so it waits for the detection once.
      const det = job === MEETINGS_JOB ? (detection ?? (await detectionRef.current)) : detection;
      try {
        await writeChain({ scope: scopeFor(job), expectedRevision: row.expected_revision, entries });
        if (!mounted.current) return;
        const step: UndoStep = {
          job,
          entries: own.map((e) => ({ profile_id: e.profile_id, profile_revision: e.profile_revision })),
          summary: job === MEETINGS_JOB ? (det?.summaryAssignment ?? null) : undefined,
        };
        setUndoStack((stack) => [...stack, step]);
        const label = row.id === "global" ? "Default for AI work" : row.label;
        let text = `PATCHED ${clock()} · ${label} → ${engine.name}${asFallback ? " · FALLBACK" : ""}`;
        if (job === MEETINGS_JOB) {
          const first = entries[0];
          const refused = await writeSummary(
            first ? { profileId: first.profile_id, profileRevision: first.profile_revision } : null,
            det?.summaryAssignment ?? null,
          );
          if (refused) text += ` · SUMMARIES ${refused}`;
        }
        setReceipt({ text });
        setEgress({ label: hostLabel(engine), scope: engine.emblem === "API" ? "cloud" : "local" });
        setSelected(job);
        announceTaskReturn(null);
      } catch (err) {
        if (isConflict(err)) setReceipt({ text: "CHANGED ELSEWHERE", tone: "danger" });
        else setReceipt({ text: `REFUSED · ${codeToken(err)}`, tone: "danger" });
      } finally {
        if (mounted.current) setBusy(false);
        await loadRoster();
      }
    },
    [detection, engineByKey, loadRoster, rowOf, writeSummary],
  );

  const refuse = useCallback((job: string, _key: string, reason: string) => {
    const label = rowOf(job)?.label ?? job;
    setReceipt({ text: `REFUSED · ${label.toUpperCase()} · ${reason}`, tone: "danger" });
  }, [rowOf]);

  const undo = useCallback(async () => {
    const step = undoStack[undoStack.length - 1];
    if (!step) return;
    setBusy(true);
    try {
      const fresh = await readRoster();
      if (mounted.current) setRoster(fresh);
      const row = fresh.rows.find((r) => r.id === rosterId(step.job));
      if (!row) return;
      if (step.entries.length) {
        await writeChain({ scope: scopeFor(step.job), expectedRevision: row.expected_revision, entries: step.entries });
      } else if (row.expected_revision > 0 && row.editor_capability_id) {
        await clearChain({
          scope: scopeFor(step.job),
          capabilityId: row.editor_capability_id,
          expectedRevision: row.expected_revision,
        });
      }
      if (step.job === MEETINGS_JOB && step.summary !== undefined) {
        const det = await loadDetection();
        const prev = step.summary;
        await writeSummary(
          prev && prev.status === "assigned" && prev.profileId && prev.profileRevision
            ? { profileId: prev.profileId, profileRevision: prev.profileRevision }
            : null,
          det?.summaryAssignment ?? null,
        );
      }
      if (!mounted.current) return;
      setUndoStack((stack) => stack.slice(0, -1));
      setReceipt({ text: `UNDONE ${clock()} · ${row.id === "global" ? "Default for AI work" : row.label}` });
    } catch (err) {
      if (isConflict(err)) setReceipt({ text: "CHANGED ELSEWHERE", tone: "danger" });
      else setReceipt({ text: `REFUSED · ${codeToken(err)}`, tone: "danger" });
    } finally {
      if (mounted.current) setBusy(false);
      await loadRoster();
    }
  }, [loadDetection, loadRoster, undoStack, writeSummary]);

  /* ── Try it ── */

  /** The engine a job runs on now: its own first wire, else the default's. */
  const engineForJob = useCallback(
    (job: string): BoardEngine | undefined => {
      const row = rowOf(job);
      const first = row?.assignment?.entries[0];
      return first ? engineByKey(first.profile_id) : undefined;
    },
    [engineByKey, rowOf],
  );

  const runTry = useCallback(
    async (job: string, confirmed: boolean) => {
      const engine = engineForJob(job);
      if (!engine) return;
      if (offMachine(engine) && !confirmed) {
        // Article III: the bytes leave only on the press that names the host.
        setPending({ job, host: hostLabel(engine), scope: engine.emblem === "API" ? "cloud" : "local" });
        return;
      }
      setPending(null);
      setTrying({ job, engine: engine.key });
      setResults((prev) => ({ ...prev, [job]: { tone: "busy", tokens: ["TRYING"] } }));
      try {
        let tokens: string[];
        let ok: boolean;
        let host = hostLabel(engine);
        if (job === THOUGHTS_JOB) {
          const answer = await conciergeTaskProbe(PROBE_CAPABILITY, confirmed || undefined);
          if (answer.state === "REFUSED") {
            // A fallback leg leaves the machine: the press first.
            // The route's boundary says a leg leaves this machine: name the
            // address the engine reaches, else say so plainly.
            setPending({
              job,
              host: engine.baseUrl ? endpointHostPort(engine.baseUrl).toUpperCase() : "OFF THIS MACHINE",
              scope: answer.paid ? "cloud" : "local",
            });
            setResults((prev) => {
              const next = { ...prev };
              delete next[job];
              return next;
            });
            return;
          }
          ok = answer.ok;
          if (answer.host) host = answer.host.toUpperCase();
          tokens = ok
            ? ["READY", answer.model || engine.name, ...msToken(answer.latencyMs)]
            : ["BROKEN", (answer.reasonCode || "NO ANSWER").replace(/_/g, " ").toUpperCase()];
        } else {
          if (!engine.detectId) throw new Error("not detected");
          const answer = await conciergeProbe(engine.detectId, engine.kind === "cloud");
          ok = answer.state === "READY";
          // A.10: this probe reads the engine's model list, not a request
          // through the route, so it says REACHED, never READY.
          tokens = ok
            ? ["REACHED", engine.name, ...msToken(answer.latencyMs)]
            : ["BROKEN", answer.state === "NOT_SUPPORTED" ? "NO ADAPTER" : "NO ANSWER"];
        }
        if (ok) tokens.push(...limitTokens(job, engine));
        if (!mounted.current) return;
        setResults((prev) => ({ ...prev, [job]: { tone: ok ? "ok" : "danger", tokens } }));
        setEgress({ label: host, scope: engine.emblem === "API" ? "cloud" : "local" });
      } catch {
        if (mounted.current) setResults((prev) => ({ ...prev, [job]: { tone: "danger", tokens: ["BROKEN", "NO ANSWER"] } }));
      } finally {
        if (mounted.current) setTrying(null);
      }
    },
    [engineForJob],
  );

  /** Speech: you speak, it shows what it heard (the speak-to-fill route,
   *  `/api/dictation/transcribe`: on this device, nothing egresses). */
  const trySpeech = useCallback(async () => {
    if (!listening) {
      try {
        await startCapture();
        setListening(true);
        setTrying({ job: SPEECH_JOB, engine: engineForJob(SPEECH_JOB)?.key ?? "" });
        setResults((prev) => ({ ...prev, [SPEECH_JOB]: { tone: "busy", tokens: ["LISTENING"] } }));
      } catch {
        setResults((prev) => ({ ...prev, [SPEECH_JOB]: { tone: "danger", tokens: ["BROKEN", "NO MICROPHONE"] } }));
      }
      return;
    }
    setListening(false);
    const started = performance.now();
    try {
      const text = await stopAndTranscribe();
      const ms = Math.round(performance.now() - started);
      if (!mounted.current) return;
      setResults((prev) => ({
        ...prev,
        [SPEECH_JOB]: text.trim()
          ? { tone: "ok", tokens: [`HEARD: "${text.trim()}"`, ...msToken(ms)] }
          : { tone: "danger", tokens: ["HEARD NOTHING"] },
      }));
      setEgress({ label: "THIS DEVICE", scope: "local" });
    } catch {
      await cancelCapture();
      if (mounted.current) setResults((prev) => ({ ...prev, [SPEECH_JOB]: { tone: "danger", tokens: ["BROKEN", "NOT HEARD"] } }));
    } finally {
      if (mounted.current) setTrying(null);
    }
  }, [engineForJob, listening]);

  const tryJob = useCallback(
    (job: string) => {
      setSelected(job);
      if (job === SPEECH_JOB) void trySpeech();
      else void runTry(job, false);
    },
    [runTry, trySpeech],
  );

  const confirmTry = useCallback(() => {
    if (pending) void runTry(pending.job, true);
  }, [pending, runTry]);

  /* ── Download: the bar fills on the engine itself ── */

  const download = useCallback(
    async (key: string) => {
      const engine = engineByKey(key);
      if (!engine?.presetId || timers.current.has(key)) return;
      setDownloads((prev) => ({ ...prev, [key]: 0 }));
      setEgress({ label: (engine.downloadHost ?? "huggingface.co").toUpperCase(), scope: "cloud" });
      try {
        const started = await conciergeDownload(engine.presetId);
        if (!started.jobId) throw new Error("no job");
        const timer = setInterval(async () => {
          try {
            const acquisition = await readAcquisition(started.jobId);
            if (!mounted.current) return;
            setDownloads((prev) => ({ ...prev, [key]: acquisition.percent }));
            if (["ready", "failed", "cancelled", "indeterminate"].includes(acquisition.state)) {
              clearInterval(timer);
              timers.current.delete(key);
              setDownloads((prev) => {
                const next = { ...prev };
                delete next[key];
                return next;
              });
              setReceipt(
                acquisition.state === "ready"
                  ? { text: `DOWNLOADED ${clock()} · ${engine.name}` }
                  : { text: `DOWNLOAD STOPPED · ${engine.name}`, tone: "danger" },
              );
              // The repairs say which wire it mends; read both again.
              void loadDetection();
              void loadRoster();
            }
          } catch {
            /* the next tick asks again */
          }
        }, POLL_MS);
        timers.current.set(key, timer);
      } catch (err) {
        setDownloads((prev) => {
          const next = { ...prev };
          delete next[key];
          return next;
        });
        setReceipt({ text: `DOWNLOAD STOPPED · ${codeToken(err)}`, tone: "danger" });
      }
    },
    [engineByKey, loadDetection, loadRoster],
  );

  /* ── Use it (a found engine joins the column, with no wire) ── */

  const useFound = useCallback(
    async (key: string) => {
      const engine = engineByKey(key);
      if (!engine?.baseUrl) return;
      setBusy(true);
      try {
        await defineEndpoint(
          endpointDraft({
            url: engine.baseUrl,
            model: engine.model || engine.name,
            requestId: `runson-use-${Date.now()}`,
            expectedProfileRevision:
              engines.find((e) => e.profileId === endpointProfileId(engine.baseUrl ?? ""))?.profileRevision ?? 0,
          }),
        );
        if (!mounted.current) return;
        setReceipt({ text: `ADDED ${clock()} · ${engine.name}` });
        await Promise.all([loadDetection(), loadRoster()]);
      } catch (err) {
        setReceipt({ text: `NOT ADDED · ${codeToken(err)}`, tone: "danger" });
      } finally {
        if (mounted.current) setBusy(false);
      }
    },
    [engineByKey, engines, loadDetection, loadRoster],
  );

  /* ── Add an engine (address + key + Check, inline) ── */

  const [addOpen, setAddOpen] = useState(false);
  const [addUrl, setAddUrlState] = useState("");
  const [addKey, setAddKeyState] = useState("");
  const [addMine, setAddMine] = useState(false);
  const [addState, setAddState] = useState<AddState>("IDLE");
  const [addModel, setAddModel] = useState("");
  const [addTools, setAddTools] = useState<"yes" | "no" | "unknown" | null>(null);
  const [addReason, setAddReason] = useState("");
  const addAsked = useRef({ url: "", key: "" });

  const resetAnswer = () => {
    setAddState("IDLE");
    setAddModel("");
    setAddReason("");
    setAddTools(null);
  };
  const setAddUrl = useCallback((value: string) => {
    addAsked.current.url = value;
    setAddUrlState(value);
    resetAnswer();
  }, []);
  const setAddKey = useCallback((value: string) => {
    addAsked.current.key = value;
    setAddKeyState(value);
    resetAnswer();
  }, []);

  const checkAdd = useCallback(async () => {
    const url = addUrl.trim();
    const key = addKey.trim();
    if (!url) return;
    setAddState("CHECKING");
    const answer = await checkEndpoint(url, key, addMine);
    // The field moved on: the answer is about another address.
    if (addAsked.current.url.trim() !== url || addAsked.current.key.trim() !== key) return;
    if (!mounted.current) return;
    if (answer.ok && answer.models.length) {
      setAddState("READY");
      setAddModel(answer.models[0]);
      setAddTools(answer.tools ?? "unknown");
    } else if (answer.reason === "key_required") setAddState("KEY_REQUIRED");
    else if (answer.reason === "key_invalid") setAddState("KEY_INVALID");
    else {
      setAddState("UNREACHABLE");
      setAddReason(answer.detail);
    }
  }, [addKey, addMine, addUrl]);

  const submitAdd = useCallback(async () => {
    const url = addUrl.trim();
    if (!url || !addModel) return;
    setBusy(true);
    try {
      await defineEndpoint(
        endpointDraft({
          url,
          model: addModel,
          requestId: `runson-add-${Date.now()}`,
          requiresKey: Boolean(addKey.trim()),
          expectedProfileRevision:
            engines.find((e) => e.profileId === endpointProfileId(url))?.profileRevision ?? 0,
        }),
        addKey,
      );
      if (!mounted.current) return;
      setReceipt({ text: `ADDED ${clock()} · ${addModel} · ${endpointHostPort(url).toUpperCase()}` });
      setAddOpen(false);
      setAddUrlState("");
      setAddKeyState("");
      addAsked.current = { url: "", key: "" };
      resetAnswer();
      await Promise.all([loadDetection(), loadRoster()]);
    } catch (err) {
      setAddState("UNREACHABLE");
      setAddReason(err instanceof Error ? err.message : "Not added.");
    } finally {
      if (mounted.current) setBusy(false);
    }
  }, [addKey, addModel, addUrl, engines, loadDetection, loadRoster]);

  const openAdd = useCallback((url = "") => {
    setAddOpen(true);
    addAsked.current = { url, key: "" };
    setAddUrlState(url);
    setAddKeyState("");
    resetAnswer();
  }, []);

  return {
    roster,
    detection,
    error,
    engines,
    selected,
    select: setSelected,
    accepts,
    patch,
    refuse,
    undo,
    canUndo: undoStack.length > 0,
    receipt,
    egress,
    results,
    trying,
    listening,
    pending,
    tryJob,
    confirmTry,
    cancelTry: () => setPending(null),
    engineForJob,
    downloads,
    download,
    useFound,
    busy,
    add: {
      open: addOpen,
      openRow: openAdd,
      url: addUrl,
      setUrl: setAddUrl,
      key: addKey,
      setKey: setAddKey,
      mine: addMine,
      setMine: setAddMine,
      state: addState,
      model: addModel,
      tools: addTools,
      reason: addReason,
      check: checkAdd,
      submit: submitAdd,
    },
  };
}

export type RunsOnController = ReturnType<typeof useRunsOn>;
export type { RosterEntry };
