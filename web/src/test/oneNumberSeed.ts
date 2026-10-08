/** PHILO-15-09 (B11, Astra r2): ONE seed for the one-number fences. An item,
 *  an agent's question the hub folded into it, a source that could not be
 *  read and a recording that arms. The hub counts 3 rows (the item, the
 *  source, the recording); the Needs drawer draws 3 rows and the Dock badge
 *  says 3 (NeedsDrawer.test.tsx, Dock.test.tsx). */
export const ONE_NUMBER_ROWS = 3;

export const ONE_NUMBER_SEED = {
  count: ONE_NUMBER_ROWS,
  items: [
    {
      id: "door:ai-runbook", ref: "ai-runbook", kind: "action_item", source: "action_item",
      title: "Write the rollback runbook", why: "DUE TODAY", severity: "warning",
      projectId: "", projectName: "", owner: null, _isDoor: true,
      _doorCard: { id: "ai-runbook", target_ref: "action_item:ai-runbook" },
    },
    {
      id: "coder:claude:s1", ref: "coder:claude:s1", kind: "coder", source: "coder",
      title: "Jordan or Avery?", question: "Jordan or Avery?", why: "TO ANSWER",
      severity: "warning", sessionKey: "claude:s1", agent: "claude", waitKind: "answer",
      projectId: "", projectName: "", foldedInto: "ai-runbook",
    },
  ],
  blockers: [],
  failedMeetings: [],
  coverage: [
    { source_id: "gh:ledger", kind: "project", state: "failed", observed_at: null,
      label: "CI red on main", project_id: "p1", reason: "gh not signed in" },
    { source_id: "jira:ops", kind: "project", state: "available", observed_at: null, label: "Ops", project_id: "p2" },
  ],
  arming: [{ scheduleId: "sch-seed", title: "Standup" }],
  complete: false,
};
