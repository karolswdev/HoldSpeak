// The immutable-target terminal window (HS-94-08) — the Phase-93 session
// pull-out, migrated onto the node-issued target. It subscribes by the
// server's {target_id, target_generation}; selecting a different node or
// worktree is opening a DIFFERENT target, never reinterpreting this one.
// Watching is free; a command names the open target and carries no
// client authority. Voice fills the steer text; the exact destination and
// consequence show at the send boundary.
import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { MicButton } from "./MicButton";
import { useDurableDraft } from "../../lib/durableDraft";
import {
  sendPreview,
  useDeliveryTerminal,
  type TerminalStatus,
} from "../deliveryTerminal";
import { useDeskWindow } from "./DeskWindow";

const ABSENCE_LABEL: Record<string, string> = {
  stream_unavailable: "stream unavailable",
  target_gone: "target gone",
  generation_mismatch: "pane recycled · target changed",
  unauthorized: "not authorized",
  unreachable: "hub unreachable",
  resyncing: "resyncing",
};

const KEY_BUTTONS: Array<{ label: string; key: string; loud?: boolean }> = [
  { label: "^C", key: "C-c", loud: true },
  { label: "Esc", key: "Escape" },
  { label: "Tab", key: "Tab" },
  { label: "Enter", key: "Enter" },
  { label: "Up", key: "Up" },
  { label: "Down", key: "Down" },
];

function KeyPalette() {
  const sendState = useDeliveryTerminal((s) => s.sendState);
  const sendDetail = useDeliveryTerminal((s) => s.sendDetail);
  return (
    <div className="desk-keypad">
      <span className="desk-keypad-label">Keys</span>
      <div className="desk-keypad-row">
        {KEY_BUTTONS.map((k) => (
          <button
            key={k.key}
            type="button"
            className={"desk-key" + (k.loud ? " is-interrupt" : "")}
            title={`send ${k.label} to the pane`}
            onClick={() =>
              void useDeliveryTerminal.getState().sendKeys([k.key], k.label)
            }
          >
            {k.label}
          </button>
        ))}
        {sendState === "sent" && (
          <span className="desk-key-fate desk-steer-sent">✓ {sendDetail}</span>
        )}
        {sendState === "refused" && (
          <span className="desk-key-fate desk-arm-refusal">✕ {sendDetail}</span>
        )}
      </div>
    </div>
  );
}

function SteerComposer() {
  const target = useDeliveryTerminal((s) => s.openTarget);
  const sendState = useDeliveryTerminal((s) => s.sendState);
  const sendDetail = useDeliveryTerminal((s) => s.sendDetail);
  const scope = `dlv-steer:${target ? target.targetId : "none"}`;
  const {
    value: text,
    setDraft: setText,
    recovered,
  } = useDurableDraft(scope);
  const [submitOn, setSubmitOn] = useState(true);

  const preview = sendPreview(target, "terminal.text", submitOn);

  const send = async () => {
    const ok = await useDeliveryTerminal.getState().sendText(text, submitOn);
    if (ok) setText(""); // a refused send keeps its composition
  };

  return (
    <div className="desk-steer">
      <div className="desk-steer-row">
        <MicButton
          label="Hold to speak"
          draftScope={scope}
          onText={(t) => setText((prev) => (prev ? `${prev} ${t}` : t))}
        />
        <textarea
          className="desk-steer-input"
          value={text}
          rows={2}
          placeholder="Steer"
          onChange={(e) => setText(e.target.value)}
        />
        <button
          type="button"
          className={"desk-chip desk-steer-enter" + (submitOn ? " is-on" : "")}
          title={submitOn ? "Enter after send" : "no Enter · text only"}
          onClick={() => setSubmitOn((v) => !v)}
        >
          ⏎
        </button>
        <button
          type="button"
          className="desk-chip"
          disabled={sendState === "sending" || !text.trim()}
          onClick={() => void send()}
        >
          {sendState === "sending" ? "…" : "Send text"}
        </button>
      </div>
      {preview ? (
        <p className="quiet desk-dlv-consequence">
          → {preview.destination} · {preview.consequence} · Receipt after every
          send
        </p>
      ) : null}
      {recovered ? (
        <span className="quiet">Recovered local steer draft.</span>
      ) : null}
      {sendState === "refused" && (
        <span className="desk-arm-refusal">✕ {sendDetail}</span>
      )}
      {sendState === "sent" && (
        <span className="desk-steer-sent">✓ {sendDetail}</span>
      )}
    </div>
  );
}

export function DeliveryTerminalWindow() {
  const reducedMotion = useReducedMotion();
  const target = useDeliveryTerminal((s) => s.openTarget);
  const status = useDeliveryTerminal((s) => s.status);
  const detail = useDeliveryTerminal((s) => s.detail);
  const lines = useDeliveryTerminal((s) => s.lines);
  const { close } = useDeliveryTerminal.getState();
  const preRef = useRef<HTMLPreElement | null>(null);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const win = useDeskWindow("delivery-terminal", {
    minW: 460,
    open: Boolean(target),
  });

  useEffect(() => {
    if (!target) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [target]);

  useEffect(() => {
    const pre = preRef.current;
    if (pre) pre.scrollTop = pre.scrollHeight;
  }, [lines]);

  if (!target) return null;
  const live = status === "live";
  const absent = (
    [
      "stream_unavailable",
      "target_gone",
      "generation_mismatch",
      "unauthorized",
      "unreachable",
    ] as TerminalStatus[]
  ).includes(status);

  return (
    <motion.div
      ref={(el: HTMLDivElement | null) => {
        rootRef.current = el;
        win.setEl(el);
      }}
      className={
        "desk-pullout is-session desk-window desk-dlv-terminal" +
        (win.floating ? " is-floating" : "")
      }
      style={win.style}
      role="region"
      aria-label={`Terminal ${target.label}`}
      initial={reducedMotion ? false : { x: 60, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 320, damping: 30 }}
      onPointerDown={(e) => {
        win.focus();
        e.stopPropagation();
      }}
    >
      <header
        className="desk-pullout-head desk-window-handle"
        {...win.handleProps}
      >
        <span className="desk-session-glyph">▮</span>
        <span className="desk-pullout-title">{target.label}</span>
        <span className="desk-chip quiet desk-dlv-node" title="Node">
          ⧉ {target.nodeId}
        </span>
        {live && (
          <span className="desk-session-live" title="watching">
            ●
          </span>
        )}
        <button
          type="button"
          className="desk-pullout-close"
          onClick={close}
          aria-label="Close"
        >
          ✕
        </button>
      </header>

      <div className="desk-pullout-body">
        <p className="quiet desk-dlv-target-line">
          Target {target.targetId.slice(0, 12)} · gen{" "}
          {target.targetGeneration.slice(0, 8)}
          {target.worktreeId ? ` · worktree ${target.worktreeId.slice(0, 8)}` : ""}
        </p>
        {live || status === "resyncing" ? (
          <pre ref={preRef} className="desk-session-pane">
            {lines.join("\n")}
          </pre>
        ) : (
          <p className="desk-session-state">
            ✕ {ABSENCE_LABEL[status] || status}
            {detail ? ` · ${detail}` : ""}
          </p>
        )}
      </div>

      {!absent ? (
        <footer className="desk-pullout-foot">
          <KeyPalette />
          <SteerComposer />
        </footer>
      ) : null}
      {win.grip}
    </motion.div>
  );
}
