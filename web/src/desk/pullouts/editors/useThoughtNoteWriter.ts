import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { ApiError } from "../../../lib/api";
import {
  saveThoughtWorkingInWorkspace,
  saveThoughtWorking,
  type Thought,
  type ThoughtWorkspaceProjection,
  type ThoughtWorkspaceCursor,
} from "../../thoughts";

export type ThoughtDraft = { title: string; body: string; tags: string };

/* PHILO-3-04 — the foot states the fault; the writer names its cause.
   `no_answer`: the request got no response (fetch threw).
   `not_accepted`: the hub answered with an error status (ApiError). */
export type ThoughtSaveFailure = "no_answer" | "not_accepted";

/** The writer's own refusal, so a face can leave it to the foot. */
export class ThoughtSaveFault extends Error {
  constructor(message: "thought save failed" | "thought save conflict") {
    super(message);
    this.name = "ThoughtSaveFault";
  }
}

const toDraft = (thought: Thought): ThoughtDraft => ({
  title: thought.working_note.title,
  body: thought.working_note.body_markdown,
  tags: thought.working_note.tags.join(", "),
});

/**
 * The sole serialized writer for a Thought's working Note. Presentation is a
 * consumer: the compact legacy editor and the Workbench document plane share
 * this exact authority/failure algorithm.
 */
export function useThoughtNoteWriter({
  thought,
  onThought,
  onProjection,
  onCursorConflict,
  locked = false,
  workspaceCursor,
}: {
  thought: Thought;
  onThought: (thought: Thought) => void;
  onProjection?: (projection: ThoughtWorkspaceProjection) => boolean | void;
  onCursorConflict?: () => void | ThoughtWorkspaceProjection | Promise<void | ThoughtWorkspaceProjection>;
  locked?: boolean;
  workspaceCursor?: ThoughtWorkspaceCursor;
}) {
  const [draftState, setDraftState] = useState<ThoughtDraft>(() => toDraft(thought));
  const [saving, setSaving] = useState(false);
  /* PHILO-3-04 — the foot's four states are React state, never a ref read
     at render: an edit, a failure and a conflict each re-render the foot. */
  const [pending, setPending] = useState(false);
  const [failure, setFailure] = useState<ThoughtSaveFailure | null>(null);
  const [conflicted, setConflicted] = useState(false);
  const [keptAt, setKeptAt] = useState<string | null>(() => thought.working_note.last_modified ?? null);
  const timer = useRef<number | null>(null);
  const inFlight = useRef(false);
  const dirty = useRef(false);
  const saveFailed = useRef(false);
  const conflictFenced = useRef(false);
  const commandFence = useRef(locked);
  const cursorRetryUsed = useRef(false);
  const authorityEpoch = useRef(0);
  const mounted = useRef(true);
  const draft = useRef<ThoughtDraft>(toDraft(thought));
  const current = useRef(thought);
  const cursor = useRef(workspaceCursor);
  const waiters = useRef<Array<() => void>>([]);

  const fence = (value: boolean) => {
    conflictFenced.current = value;
    if (mounted.current) setConflicted(value);
  };
  const fail = (value: ThoughtSaveFailure | null) => {
    saveFailed.current = value !== null;
    if (mounted.current) setFailure(value);
  };
  const settle = () => { if (mounted.current) setPending(false); };

  const wake = () => {
    const pending = waiters.current.splice(0);
    pending.forEach((resolve) => resolve());
  };
  const wait = () => new Promise<void>((resolve) => waiters.current.push(resolve));
  const clearTimer = () => {
    if (timer.current !== null) {
      window.clearTimeout(timer.current);
      timer.current = null;
    }
  };

  const installAuthoritative = useCallback((authoritative: Thought, options: { fence: boolean; notify: boolean }) => {
    authorityEpoch.current += 1;
    clearTimer();
    dirty.current = false;
    fail(null);
    fence(options.fence);
    current.current = authoritative;
    const next = toDraft(authoritative);
    draft.current = next;
    if (mounted.current) {
      setDraftState(next);
      setSaving(false);
      setPending(false);
      setKeptAt(authoritative.working_note.last_modified ?? null);
    }
    if (options.notify) onThought(authoritative);
    wake();
  }, [onThought]);

  const retainDraftAgainst = useCallback((authoritative: Thought) => {
    authorityEpoch.current += 1;
    clearTimer();
    current.current = authoritative;
    dirty.current = true;
    fail(null);
    fence(true);
    if (mounted.current) {
      setSaving(false);
      setPending(false);
      onThought(authoritative);
    }
    wake();
  }, [onThought]);

  const drainRef = useRef<(force?: boolean) => Promise<void>>(async () => undefined);
  const drain = useCallback(async (force = false): Promise<void> => {
    timer.current = null;
    if ((!force && commandFence.current) || inFlight.current || !dirty.current || conflictFenced.current) return;
    inFlight.current = true;
    dirty.current = false;
    fail(null);
    if (mounted.current) setSaving(true);
    const requestEpoch = authorityEpoch.current;
    const sent = { ...draft.current };
    try {
      const patch = {
        title: sent.title,
        body_markdown: sent.body,
        tags: sent.tags.split(",").map((tag) => tag.trim()).filter(Boolean),
      };
      const result = cursor.current
        ? await saveThoughtWorkingInWorkspace(current.current, patch, cursor.current)
        : { thought: await saveThoughtWorking(current.current, patch) };
      inFlight.current = false;
      if (requestEpoch !== authorityEpoch.current) {
        wake();
        return;
      }
      if (result.workbench && onProjection?.(result.workbench) === false) {
        dirty.current = true;
        fence(true);
        settle();
        if (mounted.current) setSaving(false);
        wake();
        return;
      }
      current.current = result.thought;
      cursorRetryUsed.current = false;
      if (result.workbench) cursor.current = result.workbench.workspace_cursor;
      if (mounted.current) {
        onThought(result.thought);
        setSaving(false);
        /* The receipt's time is the hub's stamp on THIS write
           (refinement_thought_service.py:1158), never the client clock. */
        setKeptAt(result.thought.working_note.last_modified ?? null);
      }
      if (dirty.current && !conflictFenced.current) {
        schedule(0);
      } else {
        settle();
      }
      wake();
    } catch (cause) {
      inFlight.current = false;
      if (mounted.current) setSaving(false);
      const payload = cause instanceof ApiError && cause.payload && typeof cause.payload === "object"
        ? cause.payload as { error?: string; code?: string; workbench?: unknown; current?: unknown; context?: { current?: unknown } }
        : null;
      const conflictCurrent = payload?.workbench ?? payload?.context?.current ?? payload?.current;
      const projection = conflictCurrent && typeof conflictCurrent === "object" && "workspace_cursor" in conflictCurrent && "thought" in conflictCurrent
        ? conflictCurrent as ThoughtWorkspaceProjection
        : null;
      const cursorConflict = cause instanceof ApiError && cause.status === 409
        && (payload?.code === "workspace_cursor_conflict" || payload?.error === "workspace_cursor_conflict");
      if (cursorConflict) {
        const refreshed = projection ?? await onCursorConflict?.() ?? null;
        if (!cursorRetryUsed.current && refreshed && refreshed.thought.id === current.current.id
            && (!cursor.current || refreshed.workspace_cursor.hub_id === cursor.current.hub_id)) {
          const sameAuthority = refreshed.thought.aggregate_revision === current.current.aggregate_revision
            && refreshed.thought.working_revision === current.current.working_revision
            && refreshed.thought.attachment_revision === current.current.attachment_revision;
          if (sameAuthority && (!projection || onProjection?.(projection) !== false)) {
            cursorRetryUsed.current = true;
            current.current = refreshed.thought;
            cursor.current = refreshed.workspace_cursor;
            dirty.current = true;
            fail(null);
            fence(false);
            if (mounted.current) setSaving(false);
            schedule(0);
            wake();
            return;
          }
        }
        dirty.current = true;
        fence(true);
        settle();
        wake();
        return;
      }
      if (projection) {
        if (onProjection?.(projection) === false) {
          dirty.current = true;
          fence(true);
          settle();
          wake();
          return;
        }
        cursor.current = projection.workspace_cursor;
      }
      const authoritative = (projection?.thought ?? conflictCurrent) as Thought | undefined;
      const sameThought = authoritative?.id === current.current.id;
      const superseded = requestEpoch !== authorityEpoch.current;
      if (authoritative?.working_note && typeof authoritative.aggregate_revision === "number" && sameThought
          && (!superseded || authoritative.aggregate_revision > current.current.aggregate_revision)) {
        retainDraftAgainst(authoritative);
      } else if (!superseded) {
        dirty.current = true;
        fail(cause instanceof ApiError ? "not_accepted" : "no_answer");
        settle();
      }
      wake();
    }
  }, [installAuthoritative, onCursorConflict, onProjection, onThought, retainDraftAgainst]);
  drainRef.current = drain;

  const schedule = (delay = 450) => {
    if (conflictFenced.current || inFlight.current || commandFence.current) return;
    clearTimer();
    timer.current = window.setTimeout(() => void drainRef.current(), delay);
  };

  const edit = (next: Partial<ThoughtDraft>) => {
    if (commandFence.current) return;
    const value = { ...draft.current, ...next };
    draft.current = value;
    setDraftState(value);
    dirty.current = true;
    fail(null);
    cursorRetryUsed.current = false;
    fence(false);
    setPending(true);
    schedule();
  };

  const flush = async ({ fence = false }: { fence?: boolean } = {}): Promise<Thought> => {
    if (fence) commandFence.current = true;
    clearTimer();
    if (saveFailed.current) throw new ThoughtSaveFault("thought save failed");
    while (inFlight.current || dirty.current) {
      if (!inFlight.current && dirty.current) await drainRef.current(true);
      else await wait();
      if (conflictFenced.current) throw new ThoughtSaveFault("thought save conflict");
      if (saveFailed.current) throw new ThoughtSaveFault("thought save failed");
    }
    if (conflictFenced.current) throw new ThoughtSaveFault("thought save conflict");
    return current.current;
  };

  const retry = () => {
    if (inFlight.current || conflictFenced.current || commandFence.current) return;
    dirty.current = true;
    fail(null);
    setPending(true);
    schedule(0);
  };

  const pause = async (): Promise<{ thought: Thought; workspaceCursor?: ThoughtWorkspaceCursor }> => {
    commandFence.current = true;
    clearTimer();
    while (inFlight.current) await wait();
    return { thought: current.current, workspaceCursor: cursor.current };
  };

  const resume = () => {
    commandFence.current = locked;
    if (!locked && dirty.current && !inFlight.current && !saveFailed.current && !conflictFenced.current) schedule(0);
  };

  const release = () => { commandFence.current = locked; };

  useLayoutEffect(() => { commandFence.current = locked; }, [locked]);
  useLayoutEffect(() => { cursor.current = workspaceCursor; }, [workspaceCursor]);
  useEffect(() => {
    if (thought.id !== current.current.id || thought.aggregate_revision > current.current.aggregate_revision) {
      if (dirty.current || inFlight.current) retainDraftAgainst(thought);
      else installAuthoritative(thought, { fence: false, notify: false });
    }
  }, [installAuthoritative, retainDraftAgainst, thought]);
  useEffect(() => () => {
    mounted.current = false;
    clearTimer();
    wake();
  }, []);

  return {
    draft: draftState,
    edit,
    flush,
    release,
    retry,
    pause,
    resume,
    saving,
    /* true from an edit (inside the 450 ms wait) until the write lands or
       fails; `saving` alone is only the request in flight. */
    pending,
    dirty: dirty.current,
    conflicted,
    failed: failure !== null,
    failure,
    /** The hub's `last_modified` for the last kept write (ISO, UTC). */
    keptAt,
  };
}
