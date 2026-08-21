import { useCallback, useEffect, useRef, useState } from "react";
import { readableError } from "../../lib/api";
import { thoughtWorkbench, type Thought, type ThoughtWorkspaceProjection } from "../thoughts";

function isNewer(next: ThoughtWorkspaceProjection, current: ThoughtWorkspaceProjection | null): boolean {
  if (!current) return true;
  if (next.workspace_cursor.thought_id !== current.workspace_cursor.thought_id) return false;
  if (next.workspace_cursor.hub_id !== current.workspace_cursor.hub_id) return false;
  if (next.workspace_cursor.aggregate_revision !== current.workspace_cursor.aggregate_revision) {
    return next.workspace_cursor.aggregate_revision > current.workspace_cursor.aggregate_revision;
  }
  return next.workspace_cursor.continuity_revision >= current.workspace_cursor.continuity_revision;
}

export function useThoughtWorkspaceController(initialThought: Thought) {
  const [projection, setProjection] = useState<ThoughtWorkspaceProjection | null>(null);
  const [opening, setOpening] = useState(true);
  const [error, setError] = useState("");
  const [restartDetected, setRestartDetected] = useState(false);
  const epoch = useRef(0);
  const current = useRef<ThoughtWorkspaceProjection | null>(null);

  const install = useCallback((next: ThoughtWorkspaceProjection) => {
    if (next.schema_version !== 1 || next.thought.id !== initialThought.id) return false;
    if (current.current && next.workspace_cursor.hub_id !== current.current.workspace_cursor.hub_id) {
      setRestartDetected(true);
      return false;
    }
    if (!isNewer(next, current.current)) return false;
    current.current = next;
    setProjection(next);
    setOpening(false);
    setError("");
    setRestartDetected(false);
    return true;
  }, [initialThought.id]);

  const reload = useCallback(async (adoptRestartedHub = false) => {
    const requestEpoch = ++epoch.current;
    setError("");
    try {
      const next = await thoughtWorkbench(initialThought.id);
      if (requestEpoch === epoch.current) {
        const hubChanged = current.current && next.workspace_cursor.hub_id !== current.current.workspace_cursor.hub_id;
        if (hubChanged && !adoptRestartedHub) {
          setRestartDetected(true);
          return next;
        }
        if (hubChanged && adoptRestartedHub) {
          current.current = null;
          setProjection(null);
          setRestartDetected(false);
        }
        install(next);
      }
      return next;
    } catch (cause) {
      if (requestEpoch === epoch.current) {
        setOpening(false);
        setError(readableError(cause));
      }
      throw cause;
    }
  }, [initialThought.id, install]);

  useEffect(() => {
    const requestEpoch = ++epoch.current;
    const abort = new AbortController();
    setProjection(null);
    current.current = null;
    setOpening(true);
    setError("");
    setRestartDetected(false);
    void thoughtWorkbench(initialThought.id, abort.signal).then((next) => {
      if (requestEpoch === epoch.current) install(next);
    }).catch((cause) => {
      if (abort.signal.aborted || requestEpoch !== epoch.current) return;
      setOpening(false);
      setError(readableError(cause));
    });
    return () => {
      abort.abort();
      epoch.current += 1;
    };
  }, [initialThought.id, install]);

  return { projection, opening, error, restartDetected, install, reload };
}
