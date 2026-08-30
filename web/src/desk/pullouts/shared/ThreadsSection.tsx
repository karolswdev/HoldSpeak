/** HS-151-07 — shared Threads row for pullouts.
 * Lists threads whose thread_refs name a given object (by ref_id).
 * Shows titles only — People content never leaves the encrypted store. */
import { useEffect, useState } from "react";
import { useDesk } from "../../store";
import { listThreadsByRef, type ThreadWire } from "../../threads";
import {
  SurfaceRows,
  SurfaceRow,
} from "../../surface/Surface";

export function ThreadsSection({ refId }: { refId: string }) {
  const [threads, setThreads] = useState<ThreadWire[]>([]);
  const { openPullout } = useDesk.getState();

  useEffect(() => {
    if (!refId) return;
    listThreadsByRef(refId)
      .then(setThreads)
      .catch(() => setThreads([]));
  }, [refId]);

  if (threads.length === 0) return null;

  return (
    <section>
      <h3>Threads</h3>
      <SurfaceRows>
        {threads.map((t) => (
          <SurfaceRow
            key={t.id}
            title={t.title || "Untitled thread"}
            detail={
              t.last_turn_at
                ? new Date(t.last_turn_at).toLocaleDateString()
                : ""
            }
            onOpen={() => openPullout(`thread:${t.id}`)}
          />
        ))}
      </SurfaceRows>
    </section>
  );
}
