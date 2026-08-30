/** HS-150-07 — one-time import of localStorage chat threads.
 *
 * On first Desk load, if `localStorage['hs.desk.chats']` exists, call
 * `POST /api/threads/import` with its payload, then remove the key.
 * Failures leave the key in place and surface a named receipt line via
 * useWriteReceipt. Never a modal. */
import { type ReactElement, useEffect, useRef } from "react";
import { importThreads } from "../threads";
import { useWriteReceipt } from "./useWriteReceipt";

const CHATS_KEY = "hs.desk.chats";

export function useChatImport(): { receipt: ReactElement | null } {
  const ran = useRef(false);
  const { attempt, receipt } = useWriteReceipt();

  useEffect(() => {
    if (ran.current) return;
    ran.current = true;

    let raw: string | null = null;
    try {
      raw = localStorage.getItem(CHATS_KEY);
    } catch {
      // Storage unavailable — nothing to import.
      return;
    }
    if (!raw) return;

    let payload: Record<string, unknown>;
    try {
      payload = JSON.parse(raw);
    } catch {
      // Corrupt data — leave the key for manual inspection.
      return;
    }
    if (!payload || typeof payload !== "object") return;

    // Build the import payload: convert the per-persona chat map into the
    // threads import format the server expects.
    const threads: Array<Record<string, unknown>> = [];
    for (const [personaId, turns] of Object.entries(payload)) {
      if (!Array.isArray(turns) || turns.length === 0) continue;
      threads.push({ recipe_id: personaId, turns });
    }
    if (threads.length === 0) {
      // Empty map — clean up and done.
      try { localStorage.removeItem(CHATS_KEY); } catch { /* ok */ }
      return;
    }

    void attempt("import chats", async () => {
      await importThreads({ threads });
      try { localStorage.removeItem(CHATS_KEY); } catch { /* ok */ }
    });
  }, [attempt]);

  return { receipt };
}
