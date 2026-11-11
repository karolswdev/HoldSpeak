// Parked: the older Needs row Look also uses the one Send face.
export function SendNeedWell({ face, onDone }: { face: NeedFace; onDone(): void }) {
  const v = face.verbs;
  if (v.kind !== "send") return null;
  const s = v.send as unknown as ChannelSend;
  const channel = String(s.channel || "file") as Channel;
  const account = (s.account || {}) as Record<string, string | boolean>;
  const target = (s.target || {}) as Record<string, string | number>;
  const frozen = previewOf(channel, target, account, s.preview, s.file_path);
  return (
    <li className="needs-drawer-well" role="region" aria-label={`Preview: ${face.name}`} data-testid="needs-send-preview">
      <PreviewWell preview={frozen} testid="needs-send-preview-well" verbs={
        <Button dense variant="ghost" aria-label="Close preview" onClick={onDone}>Close</Button>
      } />
    </li>
  );
}
