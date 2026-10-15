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
  newCommandId,
  readAcquisition,
  readDetection,
  readRoster,
  writeChain,
  discoverLan,
  type AssignmentScope,
  type Detection,
  type Roster,
  type RosterEntry,
  type RunsOnEngine,
} from "./api";
import {
  DEFAULT_JOB,
  JOB_PROBE_CAPABILITIES,
  MEETINGS_JOB,
  SPEECH_JOB,
  accepts as acceptsRule,
  buildEngines,
  enginePlace,
  hostLabel,
  jobName,
  jobForScope,
  leadEngine,
  offMachine,
  ownEntries,
  rosterId,
  type BoardEngine,
} from "./model";

const POLL_MS = 1000;

export interface Egress {
  label: string;
  scope: "local" | "cloud";
}

export interface JobResult {
  /** idle: a press that checked nothing (NOT CHECKED). */
  tone: "ok" | "danger" | "busy" | "idle";
  /** Tokens, joined with ` · ` on the face. */
  tokens: string[];
  sampleInput?: string;
  sampleOutput?: string;
  egress?: Egress;
}

export interface Receipt {
  text: string;
  tone?: "danger";
}

/** One Undo: the chain before the patch, and the revision the patch itself
 *  produced. Undo is a CAS write against that revision (C1): if anyone moved
 *  the row since, Undo refuses instead of overwriting them. */
interface UndoStep {
  job: string;
  entries: Array<{ profile_id: string; profile_revision: number }>;
  produced: number;
  /** Meetings also wrote the exact summary row (C2). `own` says whether the
   *  row had its own head before the patch (else it was inherited, and Undo
   *  clears it back to inheritance). */
  summary?: {
    own: boolean;
    profileId: string | null;
    profileRevision: number | null;
    produced: number;
  };
}

/** The owner's row press is bound to the displayed job and destination (XI.4).
 *  The name is retained from the parked footer confirmation protocol. */
export interface PendingTry {
  job: string;
  engineKey: string;
  /** Where the engine reached when the press was shown (host + address). */
  engineHost: string;
  host: string;
  scope: "local" | "cloud";
  engineRevision?: number;
}

export type AddState = "IDLE" | "CHECKING" | "READY" | "UNREACHABLE" | "KEY_REQUIRED" | "KEY_INVALID" | "NOT_ADDED";
export type LanDiscoveryState = "IDLE" | "CHECKING";

function clock(): string {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
}

/** A.8: a latency the probe did not report (or reported as 0) is no token. */
export function msToken(ms: number | null | undefined): string[] {
  return typeof ms === "number" && ms > 0 ? [`${ms} MS`] : [];
}

const SUMMARY_CAPABILITY = "meeting.deferred_analysis";

/** The destination a consent names: the engine's host and its address. */
export function consentHost(engine: BoardEngine): string {
  return `${engine.host}|${engine.baseUrl ?? ""}`;
}

/** A consent holds only for the same job, engine id AND destination. */
export function consentHolds(consent: PendingTry, job: string, engine: BoardEngine): boolean {
  return consent.job === job && consent.engineKey === engine.key && consent.engineHost === consentHost(engine)
    && (consent.engineRevision === undefined || consent.engineRevision === engine.profileRevision);
}

/** Refusals name the server's rule; a success reason is never an error label. */
export function probeReason(code: string | undefined): string {
  if (code === "route_probe_assignment_changed") return "Route changed";
  if (code === "route_probe_off_machine_not_confirmed") return "Destination not confirmed";
  if (!code || code === "inference_succeeded") return "No usable result";
  const words = code.replace(/^(route_probe_|inference_)/, "").replace(/_/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

/** A stopped download's reason as a token (`model_download_network` →
 *  `NETWORK`); a cancel is CANCELLED; no code is NO ANSWER. */
export function downloadReason(state: string, code: string | null): string {
  if (state === "cancelled") return "CANCELLED";
  if (!code) return "NO ANSWER";
  return code.replace(/^(model_download_|model_|inference_)/, "").replace(/_/g, " ").toUpperCase();
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

function endpointKey(url: string | undefined): string {
  return String(url ?? "").trim().replace(/\/+$/, "").toLowerCase();
}

function modelKey(value: unknown): string {
  return String(value || "").trim().toLowerCase().replace(/[^a-z0-9]+/g, "");
}

function modelKeys(engine: RunsOnEngine): Set<string> {
  return new Set(
    [engine.legacyLabel, engine.name]
      .map(modelKey)
      .filter(Boolean),
  );
}

function sameLanEndpointModel(left: RunsOnEngine, right: RunsOnEngine): boolean {
  const leftModels = modelKeys(left);
  return (
    Boolean(left.baseUrl) &&
    endpointKey(left.baseUrl) === endpointKey(right.baseUrl) &&
    [...modelKeys(right)].some((model) => leftModels.has(model))
  );
}

function mergeLanFound(base: RunsOnEngine[], transient: RunsOnEngine[]): RunsOnEngine[] {
  const rows = [...base];
  for (const candidate of transient) {
    if (rows.some((existing) => existing.profileId && sameLanEndpointModel(existing, candidate))) continue;
    if (!rows.some((existing) => existing.id === candidate.id)) rows.push(candidate);
  }
  return rows;
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
  const [detectionFailed, setDetectionFailed] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [egress, setEgress] = useState<Egress | null>(null);
  const [results, setResults] = useState<Record<string, JobResult>>({});
  const [trying, setTrying] = useState<{ job: string; engine: string } | null>(null);
  const [listening, setListening] = useState(false);
  const [downloads, setDownloads] = useState<Record<string, number>>({});
  /** A download that stopped: its reason token, kept until retried (V3). */
  const [failedDownloads, setFailedDownloads] = useState<Record<string, string>>({});
  const [undoStack, setUndoStack] = useState<UndoStep[]>([]);
  const [busy, setBusy] = useState(false);
  const [lanDiscovery, setLanDiscovery] = useState<LanDiscoveryState>("IDLE");
  const [lanFound, setLanFound] = useState<RunsOnEngine[]>([]);
  const mounted = useRef(true);
  const detectionRef = useRef<Promise<Detection | null> | null>(null);
  const timers = useRef(new Map<string, ReturnType<typeof setInterval>>());
  const scopeApplied = useRef(false);
  const activeTry = useRef<string | null>(null);

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
    if (mounted.current) setDetectionFailed(false);
    const promise = readDetection()
      .then((next) => {
        if (mounted.current) setDetection(next);
        return next;
      })
      .catch(() => {
        // Astra r2 (M1): a failed read is said, never guessed around.
        if (mounted.current) setDetectionFailed(true);
        return null;
      });
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

  const displayedDetection = useMemo(
    () => (detection ? { ...detection, engines: mergeLanFound(detection.engines, lanFound) } : detection),
    [detection, lanFound],
  );
  const engines = useMemo(() => buildEngines(roster, displayedDetection), [roster, displayedDetection]);
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

  /** Write the exact `meeting.deferred_analysis` row through the Concierge's
   *  summary selection (the service-principal rule): `target` sets it,
   *  null clears it back to inheritance. CAS on `expected`. Returns the
   *  revision it produced, or a refusal token. */
  const writeSummary = useCallback(
    async (
      target: { profileId: string; profileRevision: number } | null,
      expected: number,
    ): Promise<{ produced: number } | { refused: string }> => {
      try {
        if (target) {
          const answer = await conciergeSummarySelection({
            commandId: newCommandId("runson-summary"),
            expectedAssignmentRevision: expected,
            profileId: target.profileId,
            profileRevision: target.profileRevision,
          });
          if (answer.summaryAssignment && mounted.current) {
            setDetection((prev) => (prev ? { ...prev, summaryAssignment: answer.summaryAssignment } : prev));
          }
          if (answer.state === "READY") return { produced: answer.summaryAssignment?.assignmentRevision ?? 0 };
          return { refused: answer.state === "CONFLICT" ? "CHANGED ELSEWHERE" : "NOT SAVED" };
        }
        if (expected < 1) return { produced: 0 };
        const cleared = await clearChain({
          scope: { kind: "capability", capability_id: SUMMARY_CAPABILITY },
          capabilityId: SUMMARY_CAPABILITY,
          expectedRevision: expected,
        });
        void loadDetection();
        return { produced: Number(cleared.revision ?? 0) };
      } catch (err) {
        return { refused: isConflict(err) ? "CHANGED ELSEWHERE" : "NOT SAVED" };
      }
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
      // Whether the summary row had its own head BEFORE this patch (the
      // roster says; the detection's projection cannot tell an inherited
      // `assigned` from an own one).
      const summaryOwn = Boolean(roster?.tasks.find((t) => t.id === SUMMARY_CAPABILITY)?.has_override);
      try {
        const written = await writeChain({ scope: scopeFor(job), expectedRevision: row.expected_revision, entries });
        if (!mounted.current) return;
        const step: UndoStep = {
          job,
          entries: own.map((e) => ({ profile_id: e.profile_id, profile_revision: e.profile_revision })),
          produced: Number(written.revision ?? 0),
        };
        const label = jobName(job, row);
        let text = `PATCHED ${clock()} · ${label} → ${engine.name}${asFallback ? " · FALLBACK" : ""}`;
        if (job === MEETINGS_JOB) {
          const before = det?.summaryAssignment ?? null;
          const first = entries[0];
          const answer = await writeSummary(
            first ? { profileId: first.profile_id, profileRevision: first.profile_revision } : null,
            before?.assignmentRevision ?? 0,
          );
          if ("refused" in answer) text += ` · SUMMARIES ${answer.refused}`;
          else
            step.summary = {
              own: summaryOwn,
              profileId: summaryOwn ? (before?.profileId ?? null) : null,
              profileRevision: summaryOwn ? (before?.profileRevision ?? null) : null,
              produced: answer.produced,
            };
        }
        setUndoStack((stack) => [...stack, step]);
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
    [detection, engineByKey, loadRoster, roster, rowOf, writeSummary],
  );

  const refuse = useCallback((job: string, _key: string, reason: string) => {
    const label = jobName(job, rowOf(job));
    setReceipt({ text: `REFUSED · ${label.toUpperCase()} · ${reason}`, tone: "danger" });
  }, [rowOf]);

  const undo = useCallback(async () => {
    const step = undoStack[undoStack.length - 1];
    if (!step) return;
    const row = rowOf(step.job);
    const label = jobName(step.job, row);
    setBusy(true);
    // The step leaves the stack whatever happens: a refused Undo is not
    // retried against a row someone else now owns.
    setUndoStack((stack) => stack.slice(0, -1));
    try {
      // CAS against the revision THIS patch produced (C1).
      let restored: number;
      if (step.entries.length) {
        const written = await writeChain({ scope: scopeFor(step.job), expectedRevision: step.produced, entries: step.entries });
        restored = Number(written.revision ?? 0);
      } else {
        const capability = row?.editor_capability_id;
        if (!capability) throw new Error("no capability");
        const cleared = await clearChain({ scope: scopeFor(step.job), capabilityId: capability, expectedRevision: step.produced });
        restored = Number(cleared.revision ?? 0);
      }
      let text = `UNDONE ${clock()} · ${label}`;
      let tone: Receipt["tone"];
      let summaryRestored: number | null = null;
      if (step.summary) {
        // C2: an inherited summary row goes back to inheritance (cleared);
        // an own one gets its own engine back. Both CAS on our own write.
        const answer = await writeSummary(
          step.summary.own && step.summary.profileId && step.summary.profileRevision
            ? { profileId: step.summary.profileId, profileRevision: step.summary.profileRevision }
            : null,
          step.summary.produced,
        );
        if ("refused" in answer) {
          text += ` · SUMMARIES ${answer.refused}`;
          tone = "danger";
        } else {
          summaryRestored = answer.produced;
        }
      }
      // The entry below now describes the rows as they stand again: our own
      // Undo moved the group (and the summary row), so the next Undo CASes on
      // these revisions; anyone else's change still refuses it (M3, r2).
      setUndoStack((stack) => {
        const next = [...stack];
        for (let i = next.length - 1; i >= 0; i -= 1) {
          if (next[i].job === step.job) {
            const below = next[i];
            next[i] = {
              ...below,
              produced: restored,
              summary:
                below.summary && summaryRestored !== null
                  ? { ...below.summary, produced: summaryRestored }
                  : below.summary,
            };
            break;
          }
        }
        return next;
      });
      if (mounted.current) setReceipt({ text, tone });
    } catch (err) {
      if (mounted.current) {
        if (isConflict(err)) setReceipt({ text: `CHANGED ELSEWHERE · ${label}`, tone: "danger" });
        else setReceipt({ text: `REFUSED · ${codeToken(err)}`, tone: "danger" });
      }
    } finally {
      if (mounted.current) setBusy(false);
      await loadRoster();
    }
  }, [loadRoster, rowOf, undoStack, writeSummary]);

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

  /** Only destinations the row can show are authorized by its press. Summary
   *  capability overrides may differ from the Meetings group's chain. */
  const trialTargetsForJob = useCallback((job: string): BoardEngine[] => {
    if (job === DEFAULT_JOB) return [];
    const group = engineForJob(job);
    const lead = leadEngine(job, group, detection, engines, detectionFailed);
    if (!lead || typeof lead !== "object" || !lead.profileId) return [];
    const entries = rowOf(job)?.assignment?.entries ?? [];
    const targets = entries[0]?.profile_id === lead.profileId
      ? entries.map((entry) => engineByKey(entry.profile_id))
      : [lead];
    if (targets.some((target) => !target || (offMachine(target) && hostLabel(target) === "NOT SET"))) return [];
    return targets as BoardEngine[];
  }, [detection, detectionFailed, engineByKey, engineForJob, engines, rowOf]);
  const currentTrialTargets = useRef(trialTargetsForJob);
  currentTrialTargets.current = trialTargetsForJob;

  const trialBindingsForJob = useCallback((job: string): PendingTry[] => trialTargetsForJob(job).map((engine) => ({
    job,
    engineKey: engine.key,
    engineHost: consentHost(engine),
    engineRevision: engine.profileRevision,
    host: hostLabel(engine),
    scope: enginePlace(engine).place === "cloud" ? "cloud" : "local",
  })), [trialTargetsForJob]);

  const runTry = useCallback(
    async (job: string, shown: PendingTry[]) => {
      if (activeTry.current) return;
      const capability = JOB_PROBE_CAPABILITIES[job];
      if (!capability) return;
      const targets = currentTrialTargets.current(job);
      const engine = targets[0];
      if (!engine || !shown.length || targets.length !== shown.length || targets.some((target, index) => !consentHolds(shown[index], job, target))) {
        setResults((prev) => ({ ...prev, [job]: { tone: "danger", tokens: ["Not tried", "Route changed"] } }));
        return;
      }
      activeTry.current = job;
      setTrying({ job, engine: engine.key });
      setResults((prev) => ({ ...prev, [job]: { tone: "busy", tokens: ["Trying"] } }));
      try {
        const answer = await conciergeTaskProbe(capability, targets.some(offMachine) || undefined, targets.map((target) => target.profileId!));
        if (!mounted.current) return;
        const completed = answer.state === "READY" && answer.ok;
        const empty = completed && answer.emptyOutput;
        const tokens = completed
          ? ["Completed", ...(answer.testedTask ? [answer.testedTask] : []), answer.model || engine.name, ...msToken(answer.latencyMs), ...(empty ? ["No text returned"] : [])]
          : [answer.state === "REFUSED" ? "Not tried" : "Not completed", probeReason(answer.reasonCode)];
        const place = answer.host ? { ...engine, host: answer.host, baseUrl: undefined, emblem: answer.boundary === "local" ? "MAC" as const : answer.boundary === "cloud" ? "API" as const : "LAN" as const } : engine;
        setResults((prev) => ({ ...prev, [job]: {
          tone: completed ? (empty ? "idle" : "ok") : "danger",
          tokens,
          sampleInput: answer.sampleInput,
          sampleOutput: completed ? answer.sampleOutput : undefined,
          egress: offMachine(place) ? { label: hostLabel(place), scope: enginePlace(place).place === "cloud" ? "cloud" : "local" } : undefined,
        } }));
      } catch {
        if (mounted.current) setResults((prev) => ({ ...prev, [job]: { tone: "danger", tokens: ["Not completed", "No answer"] } }));
      } finally {
        activeTry.current = null;
        if (mounted.current) setTrying(null);
      }
    },
    [],
  );

  /** Speech: you speak, it shows what it heard (the speak-to-fill route,
   *  `/api/dictation/transcribe`: on this device, nothing egresses). */
  const trySpeech = useCallback(async () => {
    if (!listening) {
      if (activeTry.current) return;
      activeTry.current = SPEECH_JOB;
      setTrying({ job: SPEECH_JOB, engine: engineForJob(SPEECH_JOB)?.key ?? "" });
      setResults((prev) => ({ ...prev, [SPEECH_JOB]: { tone: "busy", tokens: ["Starting"] } }));
      try {
        await startCapture();
        if (!mounted.current) return;
        setListening(true);
        setResults((prev) => ({ ...prev, [SPEECH_JOB]: { tone: "busy", tokens: ["LISTENING"] } }));
      } catch {
        activeTry.current = null;
        setTrying(null);
        setResults((prev) => ({ ...prev, [SPEECH_JOB]: { tone: "danger", tokens: ["BROKEN", "NO MICROPHONE"] } }));
      }
      return;
    }
    setListening(false);
    setResults((prev) => ({ ...prev, [SPEECH_JOB]: { tone: "busy", tokens: ["Transcribing"] } }));
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
    } catch {
      await cancelCapture();
      if (mounted.current) setResults((prev) => ({ ...prev, [SPEECH_JOB]: { tone: "danger", tokens: ["BROKEN", "NOT HEARD"] } }));
    } finally {
      activeTry.current = null;
      if (mounted.current) setTrying(null);
    }
  }, [engineForJob, listening]);

  const tryJob = useCallback(
    (job: string, shown: PendingTry[]) => {
      setSelected(job);
      if (job === SPEECH_JOB) void trySpeech();
      else void runTry(job, shown);
    },
    [runTry, trySpeech],
  );

  /* ── Download: the bar fills on the engine itself ── */

  const download = useCallback(
    async (key: string) => {
      const engine = engineByKey(key);
      if (!engine?.presetId || timers.current.has(key)) return;
      // A retry clears the last failure's reason.
      setFailedDownloads((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
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
              if (acquisition.state === "ready") {
                setReceipt({ text: `DOWNLOADED ${clock()} · ${engine.name}` });
              } else {
                // V3: the failure and its reason stay on the plate.
                const reason = downloadReason(acquisition.state, acquisition.error);
                setFailedDownloads((prev) => ({ ...prev, [key]: reason }));
                setReceipt({ text: `DOWNLOAD STOPPED · ${engine.name} · ${reason}`, tone: "danger" });
              }
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
        const reason = codeToken(err);
        setFailedDownloads((prev) => ({ ...prev, [key]: reason }));
        setReceipt({ text: `DOWNLOAD STOPPED · ${engine.name} · ${reason}`, tone: "danger" });
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

  /* ── Find on LAN (one owner press, transient rows only) ── */

  const findOnLan = useCallback(async () => {
    if (lanDiscovery === "CHECKING") return;
    setLanDiscovery("CHECKING");
    setReceipt({ text: "SEARCHING LAN…" });
    try {
      const answer = await discoverLan();
      if (!mounted.current) return;
      setLanFound(answer.engines);
      const suffix = answer.partial ? " · PARTIAL" : "";
      if (answer.unavailable) {
        setReceipt({ text: "LAN DISCOVERY UNAVAILABLE", tone: "danger" });
      } else if (answer.engines.length) {
        setReceipt({ text: `FOUND ON LAN${suffix}` });
      } else {
        setReceipt({ text: `NO ENGINE FOUND ON LAN${suffix}` });
      }
    } catch (_error) {
      if (mounted.current) setReceipt({ text: "LAN DISCOVERY FAILED", tone: "danger" });
    } finally {
      if (mounted.current) setLanDiscovery("IDLE");
    }
  }, [lanDiscovery]);

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
      setAddState("NOT_ADDED");
      setAddReason(codeToken(err));
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
    detectionFailed,
    readAgain: () => void loadDetection(),
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
    tryJob,
    trialBindingsForJob,
    engineForJob,
    downloads,
    failedDownloads,
    download,
    useFound,
    findOnLan,
    lanDiscovery,
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
