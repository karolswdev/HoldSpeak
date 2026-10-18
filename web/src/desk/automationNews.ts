/** Betterment A6 — the automations that hold a NEW result.
 *
 * One read (`GET /api/automations/new`), shared by every face that shows it:
 * Today ("<name> has a new result") and the Automations dock tile (the NEW
 * count, absent at zero). Each face re-reads it after a desk change (opening a
 * result is a write, so NEW goes everywhere at once) and after a run ends. */
import { useCallback, useEffect, useState } from "react";
import { fetchAutomationNews, type AutomationNews } from "./api";
import { useBusSubscribe, useOnDeskChanged } from "./useDeskChangedRefresh";

export type { AutomationNews };

/** `Friday team update has a new result` (two: `has 2 new results`). */
export function newsWords(row: Pick<AutomationNews, "name" | "new_count">): string {
  const count = Math.max(1, row.new_count);
  return `${row.name} has ${count === 1 ? "a new result" : `${count} new results`}`;
}

/** The rows and their NEW total. `null` until the first read answers; a read
 *  that fails keeps the last rows (a face never invents an all-clear). */
export function useAutomationNews(): { rows: AutomationNews[] | null; count: number } {
  const [rows, setRows] = useState<AutomationNews[] | null>(null);
  const reload = useCallback(() => {
    void fetchAutomationNews().then(setRows).catch(() => undefined);
  }, []);
  useEffect(() => { reload(); }, [reload]);
  useOnDeskChanged(reload);
  const subscribe = useBusSubscribe();
  useEffect(() => {
    if (!subscribe) return undefined;
    const off = subscribe("workbench.run_complete", () => reload());
    return () => { if (typeof off === "function") off(); };
  }, [subscribe, reload]);
  const count = (rows ?? []).reduce((total, row) => total + Math.max(0, row.new_count), 0);
  return { rows, count };
}
