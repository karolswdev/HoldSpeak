// HS-117-07 — shared hooks extracted from the 16 core page components.
// useAction: the busy/message/try-catch-finally wrapper (was copy-pasted
// across 8+ cores). useCoreWings: the WINGS + useState + useWindowWings
// triple (was copy-pasted across 9 cores).

import { useState, type ReactNode } from "react";
import { readableError } from "../../lib/api";
import { SurfaceWings, useWindowWings } from "../../desk/surface/wings";
import type { WingSpec } from "../../desk/surface/wings";

/* ── useAction ─────────────────────────────────────────────── */

/** Replaces the hand-rolled busy/message/try-catch-finally pattern.
 *  `run(fn)` guards the async work; the catch branch stores the
 *  readable error; the caller can also `setMessage` directly. */
export function useAction() {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function run(fn: () => Promise<void>) {
    setBusy(true);
    setMessage("");
    try {
      await fn();
    } catch (e) {
      setMessage(readableError(e));
    } finally {
      setBusy(false);
    }
  }

  return { busy, message, run, setMessage } as const;
}

/* ── useCoreWings ──────────────────────────────────────────── */

/** Encapsulates the WINGS constant + view state + useWindowWings call
 *  that 9 cores repeat. When `door` is provided the gear toggle and
 *  auto-close-on-wing-change are wired automatically. */
export function useCoreWings(
  wings: WingSpec[],
  initial: string,
  door?: string,
) {
  const [view, setView] = useState(initial);
  const [doorOpen, setDoorOpen] = useState(false);

  const wingNode: ReactNode = door ? (
    <SurfaceWings
      wings={wings}
      active={doorOpen ? "" : view}
      onChange={(id: string) => {
        setDoorOpen(false);
        setView(id);
      }}
      door={door}
      doorOpen={doorOpen}
      onDoor={() => setDoorOpen((v) => !v)}
    />
  ) : (
    <SurfaceWings wings={wings} active={view} onChange={setView} />
  );

  useWindowWings(wingNode, door ? [view, doorOpen] : [view]);

  return { view, setView, doorOpen, setDoorOpen };
}
