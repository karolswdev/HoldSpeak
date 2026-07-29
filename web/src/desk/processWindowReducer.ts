/** HS-109-06 — the process window's pure journal fold.
 *
 * Journal lifecycle records and the kernel's `view=process` projections go in;
 * the five fixed surface sections come out. The reducer does not use wall-clock
 * age to classify work and never promotes an operation to a state the kernel
 * did not report.
 */

export const RECENTLY_ENDED_LIMIT = 20;
export const PROCESS_HEAD_LIMIT = 120;

export interface KernelProcessEvent {
  cursor: number;
  operation_id: string;
  correlation_id?: string;
  causation_id?: string;
  event_type: string;
  refs?: unknown[];
  privacy_class?: string;
  head?: string;
  timestamp?: string | number;
  /** Checkpoint-only field retained while events are compacted per operation. */
  first_timestamp?: string | number;
}

export interface KernelProcessObject {
  ref?: string;
  operation?: Record<string, unknown>;
  process?: Record<string, unknown>;
}

export type ProcessSectionId =
  | "needs-you"
  | "running"
  | "waiting"
  | "unknown"
  | "recently-ended";

export interface ProcessRow {
  operationId: string;
  parentOperationId: string;
  correlationId: string;
  principal: string;
  kind: string;
  target: string;
  placement: string;
  state: string;
  domainState: string;
  timestamp: string | number | "";
  refs: string[];
  head: string;
  privacyClass: string;
  latestEventType: string;
  children: ProcessRow[];
}

export interface ProcessSection {
  id: ProcessSectionId;
  label: "Needs you" | "Running" | "Waiting" | "Unknown" | "Recently ended";
  rows: ProcessRow[];
}

const SECTION_ROWS: Array<{ id: ProcessSectionId; label: ProcessSection["label"] }> = [
  { id: "needs-you", label: "Needs you" },
  { id: "running", label: "Running" },
  { id: "waiting", label: "Waiting" },
  { id: "unknown", label: "Unknown" },
  { id: "recently-ended", label: "Recently ended" },
];

const TERMINAL_EVENTS = new Set(["operation.receipt", "operation.refused"]);
const TERMINAL_STATES = new Set([
  "ended",
  "failed",
  "succeeded",
  "refused",
  "indeterminate",
  "complete",
  "completed",
  "rejected",
]);
const RUNNING_STATES = new Set(["running", "starting", "claimed"]);
const WAITING_STATES = new Set([
  "waiting",
  "admitting",
  "approved",
  "awaiting_execution",
  "pending",
]);

function text(value: unknown): string {
  return typeof value === "string" || typeof value === "number"
    ? String(value)
    : "";
}

function operationIdFromRef(ref: unknown): string {
  return text(ref).replace(/^operation:/, "");
}

function eventTime(event: KernelProcessEvent): number {
  const value = event.timestamp;
  if (typeof value === "number") return value < 1e12 ? value * 1000 : value;
  const parsed = Date.parse(String(value ?? ""));
  return Number.isNaN(parsed) ? 0 : parsed;
}

function rowTime(row: ProcessRow): number {
  const value = row.timestamp;
  if (typeof value === "number") return value < 1e12 ? value * 1000 : value;
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? 0 : parsed;
}

/** Keep one bounded, privacy-preserving lifecycle summary per operation. */
export function mergeProcessEvents(
  standing: KernelProcessEvent[],
  incoming: KernelProcessEvent[],
): KernelProcessEvent[] {
  const byOperation = new Map<string, KernelProcessEvent>();
  for (const event of [...standing, ...incoming]) {
    const operationId = text(event.operation_id);
    if (!operationId) continue;
    const previous = byOperation.get(operationId);
    const firstTimestamp =
      previous?.first_timestamp || previous?.timestamp || event.first_timestamp || event.timestamp;
    if (previous && Number(previous.cursor || 0) > Number(event.cursor || 0)) continue;
    const refs = Array.isArray(event.refs)
      ? event.refs.map(text).filter(Boolean).slice(0, 8)
      : previous?.refs ?? [];
    const incomingHead = text(event.head);
    const previousHead = text(previous?.head);
    const genericReceipt =
      event.event_type === "operation.receipt" &&
      ["succeeded", "failed", "refused", "indeterminate"].includes(incomingHead);
    // A terminal receipt follows operation.refused. Keep the named refusal
    // reason rather than replacing it with the generic receipt outcome.
    const nextHead = genericReceipt && previousHead ? previousHead : incomingHead || previousHead;
    byOperation.set(operationId, {
      cursor: Number(event.cursor || 0),
      operation_id: operationId,
      correlation_id: text(event.correlation_id) || text(previous?.correlation_id),
      causation_id: text(event.causation_id) || text(previous?.causation_id),
      event_type: text(event.event_type),
      refs,
      privacy_class: text(event.privacy_class) || text(previous?.privacy_class),
      head: nextHead.slice(0, PROCESS_HEAD_LIMIT),
      timestamp: event.timestamp ?? previous?.timestamp,
      first_timestamp: firstTimestamp,
    });
  }
  return [...byOperation.values()].sort(
    (a, b) => Number(a.cursor || 0) - Number(b.cursor || 0),
  );
}

function projectedState(
  operation: Record<string, unknown>,
  process: Record<string, unknown>,
): string {
  return text(process.generic_state) || text(operation.state) || "unknown";
}

function ownSection(row: ProcessRow, operationState: string): ProcessSectionId {
  if (
    operationState === "awaiting_decision" ||
    row.latestEventType === "operation.awaiting_decision"
  )
    return "needs-you";
  const state = row.state.toLowerCase();
  if (TERMINAL_STATES.has(state)) return "recently-ended";
  if (TERMINAL_EVENTS.has(row.latestEventType)) return "recently-ended";
  if (RUNNING_STATES.has(state)) return "running";
  if (WAITING_STATES.has(state)) return "waiting";
  return "unknown";
}

const SECTION_PRIORITY: Record<ProcessSectionId, number> = {
  "needs-you": 0,
  running: 1,
  waiting: 2,
  unknown: 3,
  "recently-ended": 4,
};

function groupSection(
  row: ProcessRow,
  own: Map<string, ProcessSectionId>,
): ProcessSectionId {
  let section = own.get(row.operationId) ?? "unknown";
  for (const child of row.children) {
    const childSection = groupSection(child, own);
    if (SECTION_PRIORITY[childSection] < SECTION_PRIORITY[section]) section = childSection;
  }
  return section;
}

function sortRows(rows: ProcessRow[]): ProcessRow[] {
  return rows
    .map((row) => ({ ...row, children: sortRows(row.children) }))
    .sort((a, b) => rowTime(b) - rowTime(a) || a.operationId.localeCompare(b.operationId));
}

/**
 * Fold journal summaries into the process window's five sections.
 *
 * Explicit parent operation IDs win. Correlation is only a fallback: peers
 * attach to the correlation root (the operation whose ID is the correlation
 * ID), or to the oldest operation in that correlation when no root is present.
 */
export function foldProcessWindow(
  events: KernelProcessEvent[],
  objects: KernelProcessObject[],
  endedLimit = RECENTLY_ENDED_LIMIT,
): ProcessSection[] {
  const latest = mergeProcessEvents([], events);
  const objectByOperation = new Map<string, KernelProcessObject>();
  for (const object of objects) {
    const operation = object.operation ?? {};
    const operationId =
      text(operation.operation_id) || operationIdFromRef(object.ref);
    if (operationId) objectByOperation.set(operationId, object);
  }

  const rows = new Map<string, ProcessRow>();
  const own = new Map<string, ProcessSectionId>();
  for (const event of latest) {
    const operationId = text(event.operation_id);
    const object = objectByOperation.get(operationId) ?? {};
    const operation = object.operation ?? {};
    const process = object.process ?? {};
    const operationState = text(operation.state).toLowerCase();
    const state = projectedState(operation, process).toLowerCase();
    const row: ProcessRow = {
      operationId,
      parentOperationId:
        text(operation.parent_operation_id) ||
        (text(event.causation_id).startsWith("op_") ? text(event.causation_id) : ""),
      correlationId: text(operation.correlation_id) || text(event.correlation_id),
      principal: text(process.principal) || text(operation.principal_identity),
      kind: text(process.kind) || text(operation.name),
      target: text(process.target_ref) || text(operation.target_ref),
      placement: text(operation.placement),
      state,
      domainState: text(process.domain_state),
      timestamp:
        event.first_timestamp || text(operation.created_at) || event.timestamp || "",
      refs: (Array.isArray(event.refs) ? event.refs : [])
        .map(text)
        .filter(Boolean)
        .slice(0, 8),
      head: text(event.head).slice(0, PROCESS_HEAD_LIMIT),
      privacyClass: text(event.privacy_class),
      latestEventType: text(event.event_type),
      children: [],
    };
    rows.set(operationId, row);
    own.set(operationId, ownSection(row, operationState));
  }

  // Older checkpoints may have hydrated objects before their event summary was
  // retained. Include them without inventing lifecycle details.
  for (const [operationId, object] of objectByOperation) {
    if (rows.has(operationId)) continue;
    const operation = object.operation ?? {};
    const process = object.process ?? {};
    const operationState = text(operation.state).toLowerCase();
    const row: ProcessRow = {
      operationId,
      parentOperationId: text(operation.parent_operation_id),
      correlationId: text(operation.correlation_id),
      principal: text(process.principal) || text(operation.principal_identity),
      kind: text(process.kind) || text(operation.name),
      target: text(process.target_ref) || text(operation.target_ref),
      placement: text(operation.placement),
      state: projectedState(operation, process).toLowerCase(),
      domainState: text(process.domain_state),
      timestamp: text(operation.created_at),
      refs: [],
      head: "",
      privacyClass: "",
      latestEventType: "",
      children: [],
    };
    rows.set(operationId, row);
    own.set(operationId, ownSection(row, operationState));
  }

  const correlationGroups = new Map<string, ProcessRow[]>();
  for (const row of rows.values()) {
    if (!row.correlationId) continue;
    const group = correlationGroups.get(row.correlationId) ?? [];
    group.push(row);
    correlationGroups.set(row.correlationId, group);
  }
  const correlationRoot = new Map<string, string>();
  for (const [correlationId, group] of correlationGroups) {
    const named = rows.get(correlationId);
    const root =
      named ??
      [...group].sort(
        (a, b) => rowTime(a) - rowTime(b) || a.operationId.localeCompare(b.operationId),
      )[0];
    if (root) correlationRoot.set(correlationId, root.operationId);
  }

  const roots: ProcessRow[] = [];
  for (const row of rows.values()) {
    let parentId = row.parentOperationId;
    if (!parentId && row.correlationId) {
      const candidate = correlationRoot.get(row.correlationId) ?? "";
      if (candidate !== row.operationId) parentId = candidate;
    }
    const parent = rows.get(parentId);
    if (parent && parent !== row) parent.children.push(row);
    else roots.push(row);
  }

  const grouped = new Map<ProcessSectionId, ProcessRow[]>(
    SECTION_ROWS.map(({ id }) => [id, []]),
  );
  for (const root of roots) grouped.get(groupSection(root, own))?.push(root);

  return SECTION_ROWS.map(({ id, label }) => ({
    id,
    label,
    rows: sortRows(grouped.get(id) ?? []).slice(
      0,
      id === "recently-ended" ? Math.max(0, endedLimit) : undefined,
    ),
  }));
}

export function operationIdsInSections(sections: ProcessSection[]): Set<string> {
  const ids = new Set<string>();
  const visit = (row: ProcessRow) => {
    ids.add(row.operationId);
    row.children.forEach(visit);
  };
  sections.forEach((section) => section.rows.forEach(visit));
  return ids;
}
