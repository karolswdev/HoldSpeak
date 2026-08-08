import { SurfaceFooter } from "../surface/SurfaceFooter";
// The immutable-target terminal window (HS-94-08) — the Phase-93 session
// pull-out, migrated onto the node-issued target. It subscribes by the
// server's {target_id, target_generation}; selecting a different node or
// worktree is opening a DIFFERENT target, never reinterpreting this one.
// Watching is free; a command names the open target and carries no
// client authority. Voice fills the steer text; the exact destination and
// consequence show at the send boundary.
//
// HS-111-06 (audit §3.4): the pane mounts through the shared PaneWell
// seam (HS-111-11 swaps its interior for xterm once, both terminals
// inherit); the keypad is the TransportKey species (the dead desk-key
// class died in the tree, not just in the CSS); the send preview is
// axis-named tokens. The consent spine — deliveryTerminal.ts send/keys
// wires — is byte-untouched.
import { useEffect, useState } from "react";
import { MicButton } from "./MicButton";
import { useDurableDraft } from "../../lib/durableDraft";
import { useDeliveryTerminal, type TerminalStatus } from "../deliveryTerminal";
import { PaneWell } from "../surface/Surface";
import { TransportKey, TransportRow } from "../surface/gadgets";
import { DeskWindowFrame } from "./DeskWindow";

const ABSENCE_LABEL: Record<string, string> = {
  stream_unavailable: "stream unavailable",
  target_gone: "target gone",
  generation_mismatch: "pane recycled · target changed",
  unauthorized: "not authorized",
  unreachable: "hub unreachable",
  resyncing: "resyncing",
};

// The key palette — full key control on the open target. Same species
// as the session pullout (HS-111-04): glyph over mono word, ^C loud.
const KEY_BUTTONS: Array<{
  word: string;
  glyph: string;
  key: string;
  title: string;
  loud?: boolean;
}> = [
  { word: "INT", glyph: "^C", key: "C-c", title: "interrupt: Ctrl-C", loud: true },
  { word: "ESC", glyph: "⎋", key: "Escape", title: "Escape" },
  { word: "TAB", glyph: "⇥", key: "Tab", title: "Tab" },
  { word: "ENTER", glyph: "⏎", key: "Enter", title: "Enter" },
  { word: "UP", glyph: "↑", key: "Up", title: "Up" },
  { word: "DOWN", glyph: "↓", key: "Down", title: "Down" },
];

function KeyPalette() {
  const sendState = useDeliveryTerminal((s) => s.sendState);
  const sendDetail = useDeliveryTerminal((s) => s.sendDetail);
  return (
    <div className="desk-keypad">
      <span className="desk-keypad-label">Keys</span>
      <TransportRow>
        {KEY_BUTTONS.map((k) => (
          <TransportKey
            key={k.key}
            label={k.word}
            glyph={k.glyph}
            tone={k.loud ? "danger" : undefined}
            title={k.title}
            onClick={() =>
              void useDeliveryTerminal.getState().sendKeys([k.key], k.word)
            }
          />
        ))}
      </TransportRow>
      {sendState === "sent" && (
        <span className="desk-key-fate desk-steer-sent">✓ {sendDetail}</span>
      )}
      {sendState === "refused" && (
        <span className="desk-key-fate desk-arm-refusal">✕ {sendDetail}</span>
      )}
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

  const send = async () => {
    const ok = await useDeliveryTerminal.getState().sendText(text, submitOn);
    if (ok) setText(""); // a refused send keeps its composition
  };

  return (
    <div className="desk-steer">
      <div className="desk-steer-row">
        <MicButton
          label="Speak"
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
        <TransportKey
          compact
          label="ENTER"
          glyph="⏎"
          active={submitOn}
          title={submitOn ? "Enter after send" : "no Enter: text only"}
          onClick={() => setSubmitOn((v) => !v)}
        />
        <TransportKey
          compact
          label="SEND"
          glyph="▸"
          disabled={sendState === "sending" || !text.trim()}
          onClick={() => void send()}
        />
      </div>
      {target ? (
        <div className="desk-dlv-consequence" role="status">
          <span className="surface-token">TARGET · {target.label}</span>
          <span className="surface-token">NODE · {target.nodeId}</span>
          <span className="surface-token">
            {submitOn ? "SEND · TEXT+ENTER" : "SEND · TEXT ONLY"}
          </span>
          <span className="surface-token">RECEIPT · PER SEND</span>
        </div>
      ) : null}
      {recovered ? (
        <span className="quiet">Recovered local steer draft.</span>
      ) : null}
      {sendState === "refused" && (
        <span className="desk-arm-refusal">✕ {sendDetail}</span>
      )}
      {sendState === "refused" && text.trim() ? (
        <TransportKey
          compact
          label="RETRY"
          glyph="↻"
          title="Retry this message"
          onClick={() => void send()}
        />
      ) : null}
      {sendState === "sent" && (
        <span className="desk-steer-sent">✓ {sendDetail}</span>
      )}
    </div>
  );
}

export function DeliveryTerminalWindow() {
  const target = useDeliveryTerminal((s) => s.openTarget);
  const status = useDeliveryTerminal((s) => s.status);
  const detail = useDeliveryTerminal((s) => s.detail);
  const lines = useDeliveryTerminal((s) => s.lines);
  const raw = useDeliveryTerminal((s) => s.raw);
  const changedAt = useDeliveryTerminal((s) => s.changedAt);
  const { close } = useDeliveryTerminal.getState();

  useEffect(() => {
    if (!target) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [target]);

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
    <DeskWindowFrame
      id="delivery-terminal"
      glyph="▮"
      minW={460}
      label={`Terminal ${target.label}`}
      className="desk-pullout is-session desk-dlv-terminal"
      icon={<span className="desk-session-glyph">▮</span>}
      title={target.label}
      actions={
        <>
          <span className="desk-chip quiet desk-dlv-node" title="Node">
            ⧉ {target.nodeId}
          </span>
          {live && (
            <span className="desk-session-live" title="watching">
              ●
            </span>
          )}
        </>
      }
      open={Boolean(target)}
      onClose={close}
    >

      <div className="desk-pullout-body">
        <p className="desk-dlv-target-line">
          <span className="surface-token">{target.targetId.slice(0, 12)}</span>
        </p>
        <PaneWell
          live={live || status === "resyncing"}
          lines={lines}
          raw={raw}
          changedAt={changedAt}
          absence={
            <>
              ✕ {ABSENCE_LABEL[status] || status}
              {detail ? ` · ${detail}` : ""}
            </>
          }
        />
      </div>

      {!absent ? (
        <SurfaceFooter verbs={<><KeyPalette /><SteerComposer /></>} />
      ) : null}
    </DeskWindowFrame>
  );
}
