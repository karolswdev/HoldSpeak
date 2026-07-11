// The guiding empty state (HS-73-02): a fresh desk answers "what is this"
// in the world's own voice — the wordmark, the canonical short form (the
// POSITIONING one-liner's tagline tier; the egress badge carries the trust
// answer, so no privacy sentence here), and the next actions glowing.
export function EmptyDesk() {
  return (
    <div className="desk-empty">
      <div className="desk-empty-mark" aria-hidden="true">
        ◍
      </div>
      <h1 className="desk-empty-word">HoldSpeak</h1>
      <p className="desk-empty-line">
        Hold a key, speak, it types. Record a meeting, it closes the loop.
      </p>
      <p className="desk-empty-next">
        <a className="desk-chip" href="/dictation">
          Set up dictation
        </a>
        <a className="desk-chip" href="/history">
          Record a meeting
        </a>
      </p>
    </div>
  );
}
