// Parked: preview verbs moved to the single completion row.
export function PreviewWell({
  preview,
  testid,
  verbs,
  onEdit,
  editBusy,
}: {
  preview: Preview;
  testid: string;
  verbs?: ReactNode;
  onEdit?: () => void;
  editBusy?: boolean;
}) {
  const safe = safeSendPreview(preview);
  return (
    <div data-send="preview" data-testid={testid} data-feedback-redact="true">
      <InspectorForm
        rows={safe.fields.map((f) => ({
          label: f.label,
          control: <span data-testid="send-preview-field">{f.value}</span>,
        }))}
      />
      <SurfaceWell>
        <div className="send-preview-body" data-testid="send-preview-body">
          {safe.body_kind === "markdown" ? <Material>{safe.body}</Material> : safe.body}
        </div>
      </SurfaceWell>
      {onEdit || verbs ? (
        <PaneActions>
          {onEdit ? (
            <Button dense variant="ghost" data-testid="send-edit" loading={editBusy} disabled={editBusy} onClick={onEdit}>
              Edit
            </Button>
          ) : null}
          {verbs}
        </PaneActions>
      ) : null}
    </div>
  );
}
