/* PARKED 20261108 (workbench fold): two web callers no live face imports.
 *
 * - deleteWorkbenchItem: a wrapper of parkWorkbenchItem; no importer.
 * - updateSkill: PUT /api/skills/{id}; its only importer was a parked test
 *   (src/_parked/desk/components/__tests__/workbenchSkillsGuard.test.ts). The
 *   route and WorkbenchService.update_skill are parked beside it
 *   (holdspeak/web/routes/_parked/workbench_skills_cancel_20261108.py).
 *
 * They stood in src/desk/api.ts. Not imported (tsconfig and vitest exclude
 * _parked). Restore with git revert of the parking commit.
 */
export {};

/*
export async function deleteWorkbenchItem(
  workbenchId: string,
  itemId: string,
): Promise<void> {
  await parkWorkbenchItem(workbenchId, itemId);
}

export async function updateSkill(
  skillId: string,
  fields: Record<string, unknown>,
): Promise<void> {
  await apiFetch<Record<string, unknown>>(`/api/skills/${encodeURIComponent(skillId)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(fields),
  });
}

*/
