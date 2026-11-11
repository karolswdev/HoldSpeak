// Parked: prepared Needs you sends use the shared Send face. The operation callbacks stay in ItemReader.
function PreparedNeed({need, answer, busy}: {need: SelectedNeed; answer: AnswerNeed; busy: boolean}) {
  const v = need.face.verbs;
  if (v.kind !== "send") return null;
  const s = v.send as unknown as Send, channel = String(s.channel || "file") as Channel;
  const eg = egressOf({channel, account: s.account, target: s.target, synced: false});
  const preview = previewOf(channel, s.target, s.account, s.preview, s.file_path);
  const url = farSide(channel, s.target, s.account);
  return <><PreferenceWell><InspectorFacts name={needName(need)} rows={[{label: "From", value: need.from}]} />
    <PreviewWell preview={preview} testid="needs-send-preview" /></PreferenceWell>
    <PaneActions>{v.state === "unknown" ? <Button dense variant="secondary" disabled={busy} onClick={() => answer(need, {id: "check", label: "Checked destination", keeps: true, run: async () => {
      if (url) window.open(url, "_blank", "noopener");
      await wire.sends(v.documentRef);
    }})}>Check</Button> : null}
      {v.state !== "unknown" || s.retry_command ? <Button dense variant="primary" disabled={busy} title={eg.title || eg.label} data-testid="needs-send"
        onClick={() => answer(need, {id: "send", label: v.state === "prepared" ? "Sent" : "Sent again", run: () => sendNeed(v)})}>{v.state === "prepared" ? "Send" : "Try again"}</Button> : null}
    </PaneActions></>;
}
