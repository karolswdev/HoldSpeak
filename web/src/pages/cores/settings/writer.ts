// The Settings writer (HS-130-07): the one full-document writer of
// `/api/settings`. It queues debounced edits, threads the freshest revision,
// repaints only the writes still pending, retries a refused write and flushes
// unsent edits when the page hides. Moved out of SettingsCore.tsx; the face
// calls `useSettingsWriter` once and hands its verbs to the sections.
import { useEffect, useMemo, useRef, useState } from "react";
import type { SettingsResponse } from "../core-types";
import { ApiError, apiFetch, readableError } from "../../../lib/api";
import { useFlushOnLeave } from "../../../lib/flushOnLeave";
import { announceTaskReturn } from "../../../desk/returnToTask";
import type { OwnerNameAdapter, OwnerSetting } from "../../../desk/firstrun/ownerName";

export type SettingsChanges = Array<[string[], unknown]>;

/** The answer of a leave send: accepted (with the hub's document) or refused. */
export type LeaveOutcome = { ok: true; settings?: SettingsResponse } | { ok: false; error: unknown };

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

/** Apply one settings transaction even when an older payload lacks a new section. */
export function mergeSettingsChanges(
  source: SettingsResponse,
  changes: Array<[string[], unknown]>,
): SettingsResponse {
  const draft = clone(source);
  for (const [path, next] of changes) {
    if (!path.length) continue;
    let cursor = draft as Record<string, unknown>;
    path.forEach((part, index) => {
      if (index === path.length - 1) {
        cursor[part] = next;
        return;
      }
      const child = cursor[part];
      if (!child || typeof child !== "object" || Array.isArray(child)) {
        cursor[part] = {};
      }
      cursor = cursor[part] as Record<string, unknown>;
    });
  }
  return draft;
}

/** Install the next full-document base before a queued write can overlap it. */
export function installSettingsChanges(
  source: SettingsResponse,
  changes: Array<[string[], unknown]>,
  install: (draft: SettingsResponse) => void,
): SettingsResponse {
  const draft = mergeSettingsChanges(source, changes);
  install(draft);
  return draft;
}

/** Repaint authoritative settings plus only the exact writes still pending. */
export function projectPendingSettingsChanges(
  base: SettingsResponse,
  groups: Array<Array<[string[], unknown]>>,
): SettingsResponse {
  return groups.reduce(
    (draft, changes) => mergeSettingsChanges(draft, changes),
    base,
  );
}

/** The writer's store: the settings resource it repaints. */
type SettingsStore = {
  data: SettingsResponse;
  setData: (next: SettingsResponse) => void;
};

/** `onSaved` runs after the hub accepted a queued write (the window's
 *  Saved stamp and the reads that follow a write). */
export function useSettingsWriter(resource: SettingsStore, onSaved: (changes: SettingsChanges) => void) {
  const [saving, setSaving] = useState(false);
  const [refusal, setRefusal] = useState("");
  /* HS-101 round 3 — the configuring archetype saves ON CHANGE
     (Article VII: no ceremony): every edit lands debounced. HS-111-01:
     the receipt is the footer status bar (USING · WRITTEN hh:mm:ss);
     a refusal replaces it in the danger tone until the next edit. */
  const saveTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  useEffect(() => () => clearTimeout(saveTimer.current), []);
  // HS-130-07: Settings is the canonical full-document writer. It threads the
  // FRESHEST `_revision` (via a ref, not the possibly-stale debounced draft)
  // so its own back-to-back saves never self-conflict, while a genuinely
  // concurrent write from another surface is still rejected + reconciled.
  type SettingsWriteJob = {
    id: number;
    changes: Array<[string[], unknown]>;
  };
  const authoritativeBaseRef = useRef<SettingsResponse>(resource.data);
  const revisionRef = useRef<string | undefined>(resource.data._revision);
  const saveQueue = useRef<Promise<void>>(Promise.resolve());
  const pendingJobsRef = useRef<SettingsWriteJob[]>([]);
  const debouncedChangesRef = useRef<Array<[string[], unknown]>>([]);
  const nextJobIdRef = useRef(0);
  const writerFencedRef = useRef(false);
  const failedChangesRef = useRef<Array<[string[], unknown]>>([]);
  const lastFailureRef = useRef("");
  type LeaveWrite = {
    jobIds: number[];
    changes: Array<[string[], unknown]>;
    newerChanges: Array<[string[], unknown]>;
    status: "pending" | "succeeded" | "failed";
  };
  // A leave patch can supersede only the jobs it actually covered, and only
  // after that patch is accepted.  This replaces the old lifetime boolean:
  // a later job must keep its own conflict/refusal path.
  const leaveWritesRef = useRef<LeaveWrite[]>([]);
  const pruneLeaveWrites = () => {
    const liveJobIds = new Set(pendingJobsRef.current.map((job) => job.id));
    leaveWritesRef.current = leaveWritesRef.current.filter(
      (leave) => leave.status === "pending" || leave.jobIds.some((id) => liveJobIds.has(id)),
    );
  };
  const repaintPending = () => {
    const visible = projectPendingSettingsChanges(
      authoritativeBaseRef.current,
      [
        failedChangesRef.current,
        ...pendingJobsRef.current.map((pending) => pending.changes),
        debouncedChangesRef.current,
      ],
    );
    resource.setData(visible);
  };
  useEffect(() => {
    if (pendingJobsRef.current.length || debouncedChangesRef.current.length || failedChangesRef.current.length)
      return;
    authoritativeBaseRef.current = resource.data;
    revisionRef.current = resource.data._revision;
  }, [resource.data]);
  const readAuthoritativeBase = async () => {
    const authoritative = await apiFetch<SettingsResponse>("/api/settings");
    authoritativeBaseRef.current = authoritative;
    revisionRef.current = authoritative._revision;
    writerFencedRef.current = false;
    return authoritative;
  };
  const removePendingJob = (id: number) => {
    pendingJobsRef.current = pendingJobsRef.current.filter(
      (pending) => pending.id !== id,
    );
    pruneLeaveWrites();
  };
  const sameSettingValue = (left: unknown, right: unknown) => {
    if (Object.is(left, right)) return true;
    try {
      return JSON.stringify(left) === JSON.stringify(right);
    } catch {
      return false;
    }
  };
  const clearFailedChangesCoveredByLeave = (changes: Array<[string[], unknown]>) => {
    const finalValues = new Map<string, unknown>();
    for (const [path, next] of changes) finalValues.set(path.join("."), next);
    failedChangesRef.current = failedChangesRef.current.filter(([path, next]) => {
      const key = path.join(".");
      return !finalValues.has(key) || !sameSettingValue(next, finalValues.get(key));
    });
    setRefusal(failedChangesRef.current.length ? lastFailureRef.current : "");
  };
  const leaveCoveredJobIds = () => {
    const covered = new Set<number>();
    for (const leave of leaveWritesRef.current) {
      // A terminal failed attempt still owns these job identities for this
      // leave cycle, so a repeated hide does not duplicate its request.  The
      // status is checked separately before any 409 can be superseded.
      for (const id of leave.jobIds) covered.add(id);
    }
    return covered;
  };
  const newerChangesForLeave = (leave: LeaveWrite) => [
    ...leave.newerChanges,
    ...pendingJobsRef.current
      .filter((job) => !leave.jobIds.includes(job.id))
      .flatMap((job) => job.changes),
    ...debouncedChangesRef.current,
  ];
  const latestValues = (changes: Array<[string[], unknown]>) => {
    const values = new Map<string, unknown>();
    for (const [path, next] of changes) values.set(path.join("."), next);
    return values;
  };
  const performSave = async (job: SettingsWriteJob) => {
    // HS-200-41 (return-to-task, focus half): the control the owner was on
    // when this write began, captured BEFORE the await — see the
    // do-not-steal rule in `desk/returnToTask.ts`.
    const from =
      typeof document !== "undefined"
        ? (document.activeElement as HTMLElement | null)
        : null;
    setSaving(true);
    setRefusal("");
    try {
      if (writerFencedRef.current) await readAuthoritativeBase();
      const payload = mergeSettingsChanges(
        {} as SettingsResponse,
        job.changes,
      );
      const result = await apiFetch<{ settings?: Record<string, unknown> }>(
        "/api/settings",
        {
          method: "PUT",
          json: revisionRef.current
            ? { ...payload, _revision: revisionRef.current }
            : payload,
        },
      );
      const authoritative = result.settings ?? mergeSettingsChanges(authoritativeBaseRef.current, job.changes);
      authoritativeBaseRef.current = authoritative as SettingsResponse;
      revisionRef.current = authoritative._revision as string | undefined;
      failedChangesRef.current = failedChangesRef.current.filter(([path]) => !job.changes.some(([saved]) => saved.join(".") === path.join(".")));
      setRefusal(failedChangesRef.current.length ? lastFailureRef.current : "");
      removePendingJob(job.id);
      repaintPending();
      // The readiness signal AND the focus return, in one call: a face
      // holding an unfinished task re-reads without a reload, and the verb
      // the owner left gets focus back (design D2(a) "Focus return").
      announceTaskReturn(from);
      onSaved(job.changes);
      return true;
    } catch (error) {
      // A revisionless leave patch can supersede this save only when this
      // exact job was in that patch and the keepalive was accepted.  A
      // pending or failed leave does not make a conflict disappear.
      const supersededByLeave =
        error instanceof ApiError &&
        error.status === 409 &&
        leaveWritesRef.current.some(
          (leave) => leave.status === "succeeded" && leave.jobIds.includes(job.id),
        );
      if (!supersededByLeave) {
        failedChangesRef.current.push(...job.changes);
        lastFailureRef.current = readableError(error);
        setRefusal(lastFailureRef.current);
      }
      writerFencedRef.current = true;
      removePendingJob(job.id);
      if (!supersededByLeave) {
        try {
          await readAuthoritativeBase();
        } catch {
          // A later queued job must reconcile before it can write.
        }
      }
      repaintPending();
      return false;
    } finally {
      setSaving(false);
    }
  };
  const save = (changes: Array<[string[], unknown]>): Promise<boolean> => {
    for (const leave of leaveWritesRef.current) {
      if (leave.status === "pending") leave.newerChanges.push(...changes);
    }
    const job = { id: ++nextJobIdRef.current, changes };
    pendingJobsRef.current.push(job);
    const next = saveQueue.current.then(
      () => performSave(job),
      () => performSave(job),
    );
    saveQueue.current = next.then(
      () => undefined,
      () => undefined,
    );
    return next;
  };
  const updateMany = (changes: Array<[string[], unknown]>) => {
    installSettingsChanges(resource.data, changes, resource.setData);
    debouncedChangesRef.current.push(...changes);
    clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      const pending = debouncedChangesRef.current;
      debouncedChangesRef.current = [];
      if (pending.length) void save(pending);
    }, 700);
  };
  const update = (path: string[], next: unknown) => updateMany([[path, next]]);
  // PHILO-17 words: a reload inside the 700 ms delay lost the edit. When the
  // page hides, the unsent edits (and any queued behind a save in flight) go
  // out NOW as one keepalive PUT of only the changed paths, never chained
  // behind the queue (Astra r2 on #1090). It carries no revision, so it
  // applies; an older full-document save still in flight carries the old
  // revision, and the hub refuses it if it lands later.
  // `extra` is a change the caller adds to this leave patch (the You fields
  // send their newest value here when the page hides or the editor closes).
  // The answer settles after the writer's own bookkeeping and never rejects.
  const flushLeave = (extra: SettingsChanges = []): Promise<LeaveOutcome> | null => {
    clearTimeout(saveTimer.current);
    const unsent = [...debouncedChangesRef.current, ...extra];
    const coveredJobIds = leaveCoveredJobIds();
    const queuedJobs = pendingJobsRef.current.filter((job) => !coveredJobIds.has(job.id));
    if (!unsent.length && !queuedJobs.length) return null;
    debouncedChangesRef.current = [];
    const changes = [...queuedJobs.flatMap((job) => job.changes), ...unsent];
    const patch = mergeSettingsChanges({} as SettingsResponse, changes);
    const leave: LeaveWrite = {
      jobIds: queuedJobs.map((job) => job.id),
      changes,
      newerChanges: [],
      status: "pending",
    };
    leaveWritesRef.current.push(leave);
    writerFencedRef.current = true;
    return apiFetch<{ settings?: SettingsResponse }>("/api/settings", {
      method: "PUT",
      json: patch,
      keepalive: true,
    }).then((result): LeaveOutcome => {
      leave.status = "succeeded";
      // Keep later local jobs ahead of this older leave patch.  A keepalive
      // response can arrive after a new ordinary job has already completed;
      // adopting its whole document would repaint that newer value away.
      const newerPaths = new Set(
        newerChangesForLeave(leave).map(([path]) => path.join(".")),
      );
      const acceptedLeaveChanges = changes.filter(([path]) => !newerPaths.has(path.join(".")));
      const rebased = mergeSettingsChanges(
        authoritativeBaseRef.current,
        acceptedLeaveChanges,
      );
      if (result?.settings?._revision && !newerPaths.size) {
        rebased._revision = result.settings._revision;
        revisionRef.current = result.settings._revision;
      }
      authoritativeBaseRef.current = rebased;
      // A newer local write can share the same value/path as this leave
      // patch.  Its own 409 refusal remains authoritative until Retry; only
      // the paths this response actually accepted may clear failed drafts.
      clearFailedChangesCoveredByLeave(acceptedLeaveChanges);
      repaintPending();
      pruneLeaveWrites();
      return { ok: true, settings: result?.settings };
    }).catch((error): LeaveOutcome => {
      leave.status = "failed";
      // The queued jobs retain their own save/error lifecycle.  Only edits
      // which existed solely in this keepalive need to enter Retry now.
      const newerValues = latestValues(newerChangesForLeave(leave));
      const failedUnsent = unsent.filter(([path]) => {
        const key = path.join(".");
        return !newerValues.has(key);
      });
      if (failedUnsent.length) {
        failedChangesRef.current.push(...failedUnsent);
        lastFailureRef.current = readableError(error);
        setRefusal(lastFailureRef.current);
        repaintPending();
      }
      pruneLeaveWrites();
      return { ok: false, error };
    });
  };
  useFlushOnLeave(() => void flushLeave());
  const commitMany = async (changes: Array<[string[], unknown]>) => {
    installSettingsChanges(resource.data, changes, resource.setData);
    setRefusal("");
    clearTimeout(saveTimer.current);
    const pending = [...debouncedChangesRef.current, ...changes];
    debouncedChangesRef.current = [];
    return save(pending);
  };
  const retryFailedChanges = () => {
    const newer = [...pendingJobsRef.current.flatMap((job) => job.changes), ...debouncedChangesRef.current];
    const retry = failedChangesRef.current.filter(([path]) => !newer.some(([pending]) => pending.join(".") === path.join(".")));
    return commitMany(retry);
  };
  const reconcileSettings = async () => {
    const reconcile = async () => {
      try {
        await readAuthoritativeBase();
        repaintPending();
        setRefusal(failedChangesRef.current.length ? lastFailureRef.current : "");
        return true;
      } catch (error) {
        setRefusal(readableError(error));
        writerFencedRef.current = true;
        return false;
      }
    };
    const next = saveQueue.current.then(reconcile, reconcile);
    saveQueue.current = next.then(
      () => undefined,
      () => undefined,
    );
    return next;
  };
  const beforeCalendarChange = async () => {
    if (debouncedChangesRef.current.length) {
      const accepted = await commitMany([]);
      return accepted && failedChangesRef.current.length === 0;
    }
    await saveQueue.current;
    return failedChangesRef.current.length === 0;
  };
  /** The refusal the failed writes still carry, or none. */
  const restoreRefusal = () => setRefusal(failedChangesRef.current.length ? lastFailureRef.current : "");
  /** True while a write that matches is debounced, queued or refused. */
  const hasPendingWrite = (matches: (change: [string[], unknown]) => boolean) =>
    debouncedChangesRef.current.some(matches) ||
    failedChangesRef.current.some(matches) ||
    pendingJobsRef.current.some((job) => job.changes.some(matches));
  return {
    saving,
    refusal,
    setRefusal,
    restoreRefusal,
    update,
    updateMany,
    commitMany,
    retryFailedChanges,
    reconcileSettings,
    beforeCalendarChange,
    hasPendingWrite,
    flushLeave,
    failedChangesRef,
    lastFailureRef,
    authoritativeBaseRef,
  };
}

export type SettingsWriter = ReturnType<typeof useSettingsWriter>;

const isOwnerChange = ([path]: [string[], unknown]) => path[0] === "owner";

/** The You fields of the Settings window write through the window's one
 *  writer: one revision, one queue, one 409 path. The You face keeps its own
 *  field words and its own Retry, so a refused owner change leaves the
 *  writer's Retry list and its refusal goes back to the You fields. A 409
 *  says the hub's word ("Settings changed in another surface…"). */
export function settingsOwnerAdapter(writer: () => SettingsWriter): OwnerNameAdapter {
  const ownerOf = (settings: SettingsResponse | undefined, sent: OwnerSetting): OwnerSetting => {
    const owner = (settings as { owner?: Partial<OwnerSetting> } | undefined)?.owner;
    return owner && typeof owner === "object"
      ? { name: String(owner.name ?? ""), aliases: Array.isArray(owner.aliases) ? owner.aliases.map(String) : [] }
      : sent;
  };
  const refused = (current: SettingsWriter): Error | null => {
    if (!current.failedChangesRef.current.some(isOwnerChange)) return null;
    const message = current.lastFailureRef.current || "Not saved";
    current.failedChangesRef.current = current.failedChangesRef.current.filter((change) => !isOwnerChange(change));
    current.restoreRefusal();
    return new Error(message);
  };
  return {
    read: () => apiFetch<{ owner?: Partial<OwnerSetting>; _revision?: string }>("/api/settings"),
    async write(owner, _revision, options) {
      const current = writer();
      const change: SettingsChanges = [[["owner"], owner]];
      if (options?.keepalive) {
        const outcome = await current.flushLeave(change);
        if (outcome && !outcome.ok) {
          throw refused(current) ?? (outcome.error instanceof Error ? outcome.error : new Error(readableError(outcome.error)));
        }
        return { settings: { owner: ownerOf(outcome?.ok ? outcome.settings : undefined, owner) } };
      }
      // A false answer with no refused owner change: a leave send carried
      // this change and the hub accepted it.
      await current.commitMany(change);
      const failure = refused(current);
      if (failure) throw failure;
      const base = current.authoritativeBaseRef.current;
      return { settings: { owner: ownerOf(base, owner), _revision: base._revision } };
    },
  };
}

/** A window with no Settings document of its own (the first-run You card,
 *  the People window) gets its own one writer for the You fields: the store
 *  is the document the owner read fills, so the writer threads that read's
 *  revision. A 409 says the hub's word, as in Settings. */
export function useOwnerWriter(): OwnerNameAdapter {
  const [data, setData] = useState<SettingsResponse>({} as SettingsResponse);
  const writer = useSettingsWriter({ data, setData }, () => {});
  const writerRef = useRef(writer);
  writerRef.current = writer;
  return useMemo(() => {
    const adapter = settingsOwnerAdapter(() => writerRef.current);
    return {
      ...adapter,
      async read() {
        const settings = await adapter.read();
        setData(settings as SettingsResponse);
        return settings;
      },
    };
  }, []);
}
