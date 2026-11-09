/* PARKED 20261108 (queue view park): web callers only the queue view imported.
 *
 * The old queue view (WorkbenchWindow, behind RAW) is parked beside this file:
 * every automation run is a Program (#2032/#2033). These stood in
 * src/desk/api.ts; nothing live imports them.
 *
 * Their routes are parked (holdspeak/web/routes/_parked/
 * workbench_queue_view_routes_20261108.py): fetchSkills, parkWorkbenchItems,
 * restoreWorkbenchItems, clearWorkbenchMemory, promoteMemoryToSkill, retryMint,
 * resolveVoiceReferences, fetchResourcefulHistory.
 *
 * Their routes stay (other callers, or a later cut): fetchParkedWorkbenchItems
 * (GET /api/workbenches/{id}?parked=true), fetchWorkbenchRuns, the event-start
 * calls fetchWorkbenchAutomations, createWorkbenchAutomation,
 * testWorkbenchAutomation, fetchWorkbenchAutomationHistory, and
 * fetchResourcefulPolicy, updateResourcefulPolicy.
 *
 * Not imported (tsconfig and vitest exclude _parked). Restore with git revert
 * of the parking commit.
 */
export {};

/*
export async function fetchSkills(): Promise<Skill[]> {
  const data = await apiFetch<Record<string, unknown>>("/api/skills");
  return (wireArray(data, "skills") as Skill[]) || [];
}

export async function parkWorkbenchItems(
  workbenchId: string,
  itemIds: string[],
): Promise<string[]> {
  const data = await apiFetch<Record<string, unknown>>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/items/park`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item_ids: itemIds }),
    },
  );
  return wireArray(data, "parked").filter((id): id is string => typeof id === "string");
}

export async function restoreWorkbenchItems(
  workbenchId: string,
  itemIds: string[],
): Promise<string[]> {
  const data = await apiFetch<Record<string, unknown>>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/items/restore`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item_ids: itemIds }),
    },
  );
  return wireArray(data, "restored").filter((id): id is string => typeof id === "string");
}

export async function clearWorkbenchMemory(workbenchId: string): Promise<void> {
  await apiFetch<Record<string, unknown>>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/memory`,
    { method: "DELETE" },
  );
}

export async function promoteMemoryToSkill(
  workbenchId: string,
  index: number,
): Promise<void> {
  await apiFetch<Record<string, unknown>>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/memory/${index}/promote`,
    { method: "POST" },
  );
}

export async function retryMint(
  workbenchId: string,
  itemId: string,
): Promise<string | null> {
  const data = await apiFetch<Record<string, unknown>>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/items/${encodeURIComponent(itemId)}/retry-mint`,
    { method: "POST" },
  );
  return data?.artifact_id ? String(data.artifact_id) : null;
}

/** HS-118-05: resolve voice references via the workbench's resolver profile. *\/
export async function resolveVoiceReferences(
  workbenchId: string,
  transcript: string,
  requestId: string,
): Promise<{
  refs: Array<{ name: string; id: string; ref: string; kind: string }>;
  egress: { boundary: string; model: string };
  request_id: string;
  error?: string;
  attempts?: number;
}> {
  return apiFetch(`/api/workbenches/${encodeURIComponent(workbenchId)}/voice/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ transcript, request_id: requestId }),
  });
}

export async function fetchResourcefulHistory(
  workbenchId: string,
): Promise<ResourcefulDispatch[]> {
  const data = await apiFetch<{ history?: ResourcefulDispatch[] }>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/resourceful/history`,
  );
  return Array.isArray(data.history) ? data.history : [];
}

export async function fetchParkedWorkbenchItems(
  workbenchId: string,
): Promise<WorkbenchItem[]> {
  const data = await apiFetch<Record<string, unknown>>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}?parked=true`,
  );
  const workbench = wireRaw(data, "workbench");
  return wireArray(workbench, "items") as WorkbenchItem[];
}

export async function fetchWorkbenchAutomations(
  workbenchId: string,
): Promise<WorkbenchAutomation[]> {
  const data = await apiFetch<{ automations?: Record<string, unknown>[] }>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/automations`,
  );
  return Array.isArray(data.automations) ? data.automations.map(automationFromWire) : [];
}

export async function createWorkbenchAutomation(
  workbenchId: string,
  presetId: "github-review-requested" | "jira-assigned-to-me",
  repository: string,
): Promise<WorkbenchAutomation> {
  const data = await apiFetch<{ automation: Record<string, unknown> }>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/automations`,
    { method: "POST", json: { preset_id: presetId, repository } },
  );
  return automationFromWire(data.automation);
}

/** A test exercises matching without adding an item or advancing the baseline. *\/
export async function testWorkbenchAutomation(
  workbenchId: string,
  automationId: string,
): Promise<AutomationTestResult> {
  const data = await apiFetch<Record<string, unknown>>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/automations/${encodeURIComponent(automationId)}/test`,
    { method: "POST" },
  );
  const changes = Array.isArray(data.changes) ? data.changes.length : Number(data.changes || 0);
  return {
    entity_count: Number(data.entity_count || 0),
    changes,
    would_add: Number(data.would_project || data.would_add || 0),
  };
}

export async function fetchWorkbenchAutomationHistory(
  workbenchId: string,
  automationId: string,
): Promise<AutomationHistoryEntry[]> {
  const data = await apiFetch<{ history?: Record<string, unknown>[] }>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/automations/${encodeURIComponent(automationId)}/history`,
  );
  return Array.isArray(data.history) ? data.history.map((entry) => ({
    id: String(entry.id || entry.event_id || ""),
    occurred_at: String(entry.occurred_at || entry.projected_at || entry.event_created_at || ""),
    outcome: entry.item_id ? "added" : "skipped",
    event_kind: String(entry.event_kind || entry.event_type || "event"),
    subject: String(entry.subject || entry.subject_ref || ""),
    receipt_id: entry.receipt_id ? String(entry.receipt_id) : null,
    detail: entry.detail ? String(entry.detail) : null,
  })) : [];
}

export async function fetchResourcefulPolicy(
  workbenchId: string,
): Promise<ResourcefulPolicy> {
  const data = await apiFetch<{ policy: ResourcefulPolicy }>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/resourceful`,
  );
  return data.policy;
}

export async function updateResourcefulPolicy(
  workbenchId: string,
  policy: Pick<ResourcefulPolicy,
    "enabled" | "idle_after_minutes" | "cooldown_hours" | "nightly_target" |
    "night_only" | "night_start_hour" | "night_end_hour" | "routines"
  >,
): Promise<ResourcefulPolicy> {
  const data = await apiFetch<{ policy: ResourcefulPolicy }>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/resourceful`,
    { method: "PUT", json: policy },
  );
  return data.policy;
}

export async function fetchWorkbenchRuns(id: string): Promise<WorkbenchRun[]> {
  const data = await apiFetch<Record<string, unknown>>(`/api/workbenches/${encodeURIComponent(id)}/runs`);
  return (wireArray(data, "runs") as WorkbenchRun[]) || [];
}

*/
