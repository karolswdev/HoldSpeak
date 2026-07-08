// The session pull-out (HS-87-01) — attach: a real view into a real
// agent session, in the desk grammar. Read-only in this story: watching
// is free, and this surface issues no grants and sends no keystrokes;
// the arming chip and the composer land with HS-87-02/03.
import { useEffect, useRef } from "react";
import { motion } from "motion/react";
import { useSteering } from "../steering";

const PANE_STATE_LABEL: Record<string, string> = {
  pane_gone: "pane gone",
  tmux_absent: "tmux absent",
  no_pane: "no pane on this session",
  unknown_session: "gone from the registry",
  error: "peek failed",
  unreachable: "hub unreachable",
  idle: "…",
};

export function SessionPullout() {
  const openKey = useSteering((s) => s.openKey);
  const session = useSteering((s) => s.session);
  const paneStatus = useSteering((s) => s.paneStatus);
  const paneDetail = useSteering((s) => s.paneDetail);
  const paneLines = useSteering((s) => s.paneLines);
  const { closeSession } = useSteering.getState();
  const ref = useRef<HTMLDivElement | null>(null);
  const preRef = useRef<HTMLPreElement | null>(null);

  useEffect(() => {
    if (!openKey) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeSession();
    };
    const onDown = (e: PointerEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) closeSession();
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onDown);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onDown);
    };
  }, [openKey]);

  // The newest output is the point of a peek: follow the tail.
  useEffect(() => {
    const pre = preRef.current;
    if (pre) pre.scrollTop = pre.scrollHeight;
  }, [paneLines]);

  if (!openKey) return null;

  const sessionId = openKey.split(":", 2)[1] || openKey;
  const live = paneStatus === "live";

  return (
    <motion.div
      ref={ref}
      className="desk-pullout is-session"
      initial={{ x: 60, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 320, damping: 30 }}
      onPointerDown={(e) => e.stopPropagation()}
    >
      <header className="desk-pullout-head">
        <span className="desk-session-glyph">
          {session?.awaitingResponse ? "🙋" : "🤖"}
        </span>
        <span className="desk-pullout-title">
          {session?.agent || openKey.split(":", 2)[0]} · {sessionId.slice(0, 8)}
        </span>
        {session?.stale && <span className="desk-chip quiet is-stale">stale</span>}
        {live && <span className="desk-session-live" title="watching">●</span>}
        <button
          type="button"
          className="desk-pullout-close"
          onClick={closeSession}
          aria-label="Close"
        >
          ✕
        </button>
      </header>

      <div className="desk-pullout-body">
        {session?.awaitingResponse && session.question ? (
          <pre className="desk-pullout-md desk-session-question">{session.question}</pre>
        ) : null}
        {live ? (
          <pre ref={preRef} className="desk-session-pane">
            {paneLines.join("\n")}
          </pre>
        ) : (
          <p className="desk-session-state">
            ✕ {PANE_STATE_LABEL[paneStatus] || paneStatus}
            {paneDetail ? ` — ${paneDetail}` : ""}
          </p>
        )}
      </div>
    </motion.div>
  );
}
