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
  newCommandId,
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
  /** idle: a press that checked nothing (NOT CHECKED). */
  tone: "ok" | "danger" | "busy" | "idle";
  /** Tokens, joined with ` · ` on the face. */
  tokens: string[];
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

/** A pending off-machine Try (Article III): the consent is bound to the exact
 *  engine and host it was shown for (C3). */
export interface PendingTry {
  job: string;
  engineKey: string;
  host: string;
  scope: "local" | "cloud";
}

export type AddState = "IDLE" | "CHECKING" | "READY" | "UNREACHABLE" | "KEY_REQUIRED" | "KEY_INVALID" | "NOT_ADDED";

function clock(): string {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
}

/** A.8: a latency the probe did not report (or reported as 0) is no token. */
export function msToken(ms: number | null | undefined): string[] {
  return typeof ms === "number" && ms > 0 ? [`${ms} MS`] : [];
}

const SUMMARY_CAPABILITY = "meeting.deferred_analysis";

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
  const [pending, setPending] = useState<PendingTry | null>(null);
  const [downloads, setDownloads] = useState<Record<string, number>>({});
  /** A download that stopped: its reason token, kept until retried (V3). */
  const [failedDownloads, setFailedDownloads] = useState<Record<string, string>>({});
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
        const label = row.id === "global" ? "Default for AI work" : row.label;
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
    const label = rowOf(job)?.label ?? job;
    setReceipt({ text: `REFUSED · ${label.toUpperCase()} · ${reason}`, tone: "danger" });
  }, [rowOf]);

  const undo = useCallback(async () => {
    const step = undoStack[undoStack.length - 1];
    if (!step) return;
    const row = rowOf(step.job);
    const label = step.job === DEFAULT_JOB ? "Default for AI work" : (row?.label ?? step.job);
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
      // The step below now describes the row as it stands again.
      setUndoStack((stack) => {
        const next = [...stack];
        for (let i = next.length - 1; i >= 0; i -= 1) {
          if (next[i].job === step.job) {
            next[i] = { ...next[i], produced: restored };
            break;
          }
        }
        return next;
      });
      let text = `UNDONE ${clock()} · ${label}`;
      let tone: Receipt["tone"];
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
        }
      }
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

  /** Ask for the owner's press before bytes leave this machine. */
  const askConsent = useCallback((job: string, engine: BoardEngine, host?: string, scope?: Egress["scope"]) => {
    setPending({
      job,
      engineKey: engine.key,
      host: host ?? hostLabel(engine),
      scope: scope ?? (engine.emblem === "API" ? "cloud" : "local"),
    });
  }, []);

  const runTry = useCallback(
    async (job: string, consent: PendingTry | null) => {
      const engine = engineForJob(job);
      if (!engine) {
        setPending(null);
        return;
      }
      // C3: a consent authorizes exactly the engine and host it named. If the
      // job's engine changed since, the old press is void: ask again.
      if (consent && (consent.engineKey !== engine.key || consent.job !== job)) {
        if (offMachine(engine)) askConsent(job, engine);
        else setPending(null);
        return;
      }
      const confirmed = consent !== null;
      if (offMachine(engine) && !confirmed) {
        // Article III: the bytes leave only on the press that names the host.
        askConsent(job, engine);
        return;
      }
      setPending(null);
      setTrying({ job, engine: engine.key });
      setResults((prev) => ({ ...prev, [job]: { tone: "busy", tokens: ["TRYING"] } }));
      try {
        let tokens: string[];
        let tone: JobResult["tone"];
        let host = hostLabel(engine);
        if (job === THOUGHTS_JOB) {
          const answer = await conciergeTaskProbe(PROBE_CAPABILITY, confirmed || undefined);
          if (answer.state === "REFUSED") {
            // The route's boundary says a leg leaves this machine: name the
            // address the engine reaches, else say so plainly.
            askConsent(
              job,
              engine,
              engine.baseUrl ? endpointHostPort(engine.baseUrl).toUpperCase() : "OFF THIS MACHINE",
              answer.paid ? "cloud" : "local",
            );
            setResults((prev) => {
              const next = { ...prev };
              delete next[job];
              return next;
            });
            return;
          }
          if (answer.host) host = answer.host.toUpperCase();
          // A real request through the route: the only READY a Try may say.
          tone = answer.ok ? "ok" : "danger";
          tokens = answer.ok
            ? ["READY", answer.model || engine.name, ...msToken(answer.latencyMs)]
            : ["BROKEN", (answer.reasonCode || "NO ANSWER").replace(/_/g, " ").toUpperCase()];
        } else {
          if (!engine.detectId) throw new Error("not detected");
          const answer = await conciergeProbe(engine.detectId, engine.kind === "cloud");
          // A.10 / V2: this probe reads the engine's model list (or, for a
          // cloud engine with no probe to run, nothing at all). It says
          // REACHED or NOT CHECKED, never READY; ms only when measured.
          if (answer.state === "READY") {
            tone = "ok";
            tokens = ["REACHED", engine.name, ...msToken(answer.latencyMs)];
          } else if (answer.state === "NOT_SET") {
            tone = "idle";
            tokens = ["NOT CHECKED", engine.name];
          } else {
            tone = "danger";
            tokens = ["BROKEN", answer.state === "NOT_SUPPORTED" ? "NO ADAPTER" : "NO ANSWER"];
          }
        }
        if (tone === "ok") tokens.push(...limitTokens(job, engine));
        if (!mounted.current) return;
        setResults((prev) => ({ ...prev, [job]: { tone, tokens } }));
        setEgress({ label: host, scope: engine.emblem === "API" ? "cloud" : "local" });
      } catch {
        if (mounted.current) setResults((prev) => ({ ...prev, [job]: { tone: "danger", tokens: ["BROKEN", "NO ANSWER"] } }));
      } finally {
        if (mounted.current) setTrying(null);
      }
    },
    [askConsent, engineForJob],
  );

  // C3: when the job behind a pending press changes engine, the press goes
  // and a new one, naming the new host, takes its place.
  useEffect(() => {
    if (!pending) return;
    const engine = engineForJob(pending.job);
    if (engine && engine.key === pending.engineKey) return;
    if (engine && offMachine(engine)) askConsent(pending.job, engine);
    else setPending(null);
  }, [askConsent, engineForJob, pending]);

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
      else void runTry(job, null);
    },
    [runTry, trySpeech],
  );

  const confirmTry = useCallback(() => {
    if (pending) void runTry(pending.job, pending);
  }, [pending, runTry]);

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
    failedDownloads,
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
