/** Opaque producer preconditions. These identify a wait; they grant no authority. */
export interface WaitBinding {
  wait_id?: string | null;
  wait_revision?: string | null;
  wait_kind?: string | null;
  expected_pane_id?: string | null;
  expected_pane_fingerprint?: string | null;
}
export function waitBindingOf(row: Record<string, unknown> | undefined): WaitBinding | undefined {
  if (!row?.wait_revision) return undefined;
  const value = (key: string) => typeof row[key] === "string" ? row[key] as string : null;
  return {wait_id:value("wait_id"),wait_revision:value("wait_revision"),wait_kind:value("wait_kind"),
    expected_pane_id:value("expected_pane_id"),expected_pane_fingerprint:value("expected_pane_fingerprint")};
}
