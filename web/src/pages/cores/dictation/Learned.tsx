/** HS-176-05 — the `Learned` wing: what the desk knows (settled design D2(c),
 *  boards `Learned` / `LearnedQuiet` / `LearnedPhone`).
 *
 *  What changed from HS-111-02's door table:
 *   1. It is a WING, not a gear panel. "The only path to what the pipeline
 *      learned is the gear" was the defect; the corrections table moves out
 *      of `Memory.tsx` and the Configure door keeps only the digest.
 *   2. The row is a `SurfaceLedgerRow`, not a `GadgetTable`: the 52px lead
 *      slot carries the kind emblem (`TEXT` / `INTENT` / `TARGET`), the
 *      primary carries the key (the heard span, or the routing gist), then
 *      `-> <value>` — and the value is the LABEL, never a raw id (canon E.4,
 *      ruling R12): a block's description for `intent`, the target profile's
 *      label for `target`, the said phrase verbatim for `text`.
 *   3. `N APPLIED` is a REAL firing count from the wire (`applied`, ruling
 *      R3) — the retained journal rows whose `corrections_applied` names the
 *      rule. Absent at zero (UX-CANON A.8). It counts the RETAINED journal,
 *      so it can go DOWN as rows age out (C3 note).
 *   4. No caption count (ruling N5b): the tab is the name, the rows are the
 *      count, and the footer's `N TODAY` is the one count per face (A.7).
 *      `LEARNED` therefore appears exactly once on this face — the wing tab.
 *   5. `Forget` is the library `ConfirmVerb` (a Button), never the `x` glyph,
 *      with the one-step in-world confirm (no modals, ledger not gate).
 *   6. Empty state: ONE token, `NOTHING LEARNED` — no sentence, no zero.
 */
import "./learned.css";
import { useCallback, useEffect, useMemo, useState } from "react";
import { apiFetch, readableError } from "../../../lib/api";
import { asRows, rowId, useResource } from "../../pageSupport";
import { useRuntimeBus } from "../../../runtime/RuntimeBus";
import type { DictationCorrectionsResponse } from "../core-types";
import { deSnake, presentValue } from "../../../desk/surface/format";
import {
  ConfirmVerb,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  SurfaceState,
} from "../../../desk/surface/Surface";

type Row = Record<string, unknown>;

/** The three kinds the store holds (`plugins/dictation/corrections.py`), as
 *  the lead-slot emblem. A kind the store grows later still reads as words,
 *  never as a raw snake_case wire value (canon E.4). */
const KIND_EMBLEMS: Record<string, string> = {
  text: "TEXT",
  intent: "INTENT",
  target: "TARGET",
};

export function kindEmblem(value: unknown): string {
  const raw = String(value ?? "").trim();
  if (!raw) return "";
  return KIND_EMBLEMS[raw] ?? deSnake(raw).toUpperCase();
}

/** The value column: the LABEL the owner reads, never the id on the wire
 *  (ruling R12). `text` values are his own words and pass through verbatim;
 *  `intent` resolves through the loaded blocks' descriptions; `target`
 *  through readiness's `target.overrides` label map. An id neither map
 *  carries still reads as words. */
export function valueLabel(
  row: Row,
  blocks: Record<string, string>,
  targets: Record<string, string>,
): string {
  const raw = presentValue(row.value ?? row.replacement);
  if (!raw) return "";
  const kind = String(row.kind ?? "");
  if (kind === "text") return raw;
  if (kind === "intent") return blocks[raw] ?? deSnake(raw);
  if (kind === "target") return targets[raw] ?? deSnake(raw);
  return raw;
}

/** `N APPLIED`, absent at zero (UX-CANON A.8 — no counters of zero). */
export function appliedToken(row: Row): string {
  const count = Number(row.applied ?? 0);
  return Number.isFinite(count) && count > 0 ? `${count} APPLIED` : "";
}

/** readiness → `{id: label}` for the target profiles (ruling R12). A failed
 *  read costs nothing: the id still renders as words. */
function targetLabels(data: Record<string, unknown> | undefined): Record<string, string> {
  const target = data?.target;
  const overrides =
    target && typeof target === "object"
      ? (target as Record<string, unknown>).overrides
      : null;
  const map: Record<string, string> = {};
  if (Array.isArray(overrides)) {
    for (const option of overrides) {
      if (!option || typeof option !== "object") continue;
      const entry = option as Record<string, unknown>;
      const id = String(entry.id ?? "");
      const label = String(entry.label ?? "");
      if (id && label) map[id] = label;
    }
  }
  return map;
}

/** the blocks document → `{block id: description}` (ruling R12; the route is
 *  the one `Blocks.tsx` already reads). */
function blockLabels(data: Record<string, unknown> | undefined): Record<string, string> {
  const document = data?.document;
  const blocks =
    document && typeof document === "object"
      ? (document as Record<string, unknown>).blocks
      : null;
  const map: Record<string, string> = {};
  if (Array.isArray(blocks)) {
    for (const block of blocks) {
      if (!block || typeof block !== "object") continue;
      const entry = block as Record<string, unknown>;
      const id = String(entry.id ?? "");
      const description = String(entry.description ?? "");
      if (id && description) map[id] = description;
    }
  }
  return map;
}

export function Learned() {
  const { subscribe } = useRuntimeBus();
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const readiness = useResource<Record<string, unknown>>(
    "/api/dictation/readiness",
    {},
  );
  const blocks = useResource<Record<string, unknown>>(
    "/api/dictation/blocks?scope=global",
    {},
  );
  const targets = useMemo(() => targetLabels(readiness.data), [readiness.data]);
  const blockMap = useMemo(() => blockLabels(blocks.data), [blocks.data]);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiFetch<DictationCorrectionsResponse>(
        "/api/dictation/corrections",
      );
      setRows(asRows(payload, ["items", "corrections"]));
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  /* A teach anywhere on the desk emits `learning_event` on the ONE runtime
     bus (`web/routes/dictation/pipeline.py`), so the wing re-reads rather
     than going stale behind the owner's back. Watching is free (Article
     V.1) — this is a read, and the read is the whole refresh. */
  useEffect(
    () => subscribe("learning_event", () => void load()),
    [subscribe, load],
  );

  const forget = async (row: Row) => {
    await apiFetch(
      `/api/dictation/corrections/${encodeURIComponent(String(row.id))}`,
      { method: "DELETE" },
    );
    await load();
  };

  return (
    <SurfaceSection className="speak-learned">
      <SurfaceLedger count={null}>
        <SurfaceState
          loading={loading}
          error={error}
          empty={!rows.length}
          emptyLabel="NOTHING LEARNED"
          emptyGlyph="▤"
          onRetry={() => void load()}
        >
          {rows.map((row, index) => {
            const applied = appliedToken(row);
            return (
              <SurfaceLedgerRow
                key={rowId(row, index)}
                expands={false}
                lead={
                  <span className="surface-ledger-cell learned-kind">
                    {kindEmblem(row.kind)}
                  </span>
                }
                primary={String(row.key ?? "")}
                cells={
                  <span className="learned-cells">
                    <span className="learned-arrow" aria-hidden="true">
                      →
                    </span>
                    <span className="learned-value">
                      {valueLabel(row, blockMap, targets)}
                    </span>
                  </span>
                }
                trailing={
                  <>
                    {/* The count slot holds its width whether or not the row
                        carries one, so a rule that has never fired never
                        moves its neighbours (canon D). */}
                    <span className="surface-ledger-cell learned-applied">
                      {applied}
                    </span>
                    <span className="learned-forget">
                      <ConfirmVerb
                        label="Forget"
                        confirmLabel="Forget?"
                        onConfirm={() => void forget(row)}
                      />
                    </span>
                  </>
                }
              />
            );
          })}
        </SurfaceState>
      </SurfaceLedger>
    </SurfaceSection>
  );
}
