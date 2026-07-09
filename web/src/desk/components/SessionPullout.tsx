// The session pull-out (HS-87-01/02) — attach + arm, in the desk
// grammar. Watching is free; steering is armed: the ARM chip is a
// press-and-hold (the desk's consent gesture, the record-orb family),
// armed becomes the countdown, one tap disarms. Enforcement lives
// hub-side — this surface can only ask.
import { useEffect, useRef, useState } from "react";
import { motion } from "motion/react";
import { MicButton } from "./MicButton";
import { GroundingSection } from "./GroundingSection";
import { RailsPicker } from "./RailsPicker";
import { useDesk } from "../store";
import {
  buildGrounding,
  emptyGrounding,
  groundingIsEmpty,
  type GroundingSelection,
  type RailsPick,
} from "../grounding";
import { flipTargetForStory, useMissionControl } from "../missioncontrol";
import { mmss, useSteering } from "../steering";

// The steer's context budget mirrors the hub's 8 KB cap (≈2000 tokens
// at 4 chars/token); the gauge refuses past it before any send.
const STEER_LIMIT_TOKENS = 2000;

const PANE_STATE_LABEL: Record<string, string> = {
  pane_gone: "pane gone",
  tmux_absent: "tmux absent",
  no_pane: "no pane on this session",
  unknown_session: "gone from the registry",
  error: "peek failed",
  unreachable: "hub unreachable",
  idle: "…",
};

const HOLD_TO_ARM_MS = 600;

function ArmChip() {
  const armed = useSteering((s) => s.armed);
  const armedUntil = useSteering((s) => s.armedUntil);
  const armError = useSteering((s) => s.armError);
  const stale = useSteering((s) => Boolean(s.session?.stale));
  const [remaining, setRemaining] = useState(0);
  const [holding, setHolding] = useState(false);
  const holdTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!armed || armedUntil === null) return;
    const tick = () => setRemaining((armedUntil - Date.now()) / 1000);
    tick();
    const t = setInterval(tick, 500);
    return () => clearInterval(t);
  }, [armed, armedUntil]);

  const cancelHold = () => {
    setHolding(false);
    if (holdTimer.current !== null) {
      clearTimeout(holdTimer.current);
      holdTimer.current = null;
    }
  };

  if (armed) {
    return (
      <button
        type="button"
        className="desk-chip desk-arm-chip is-armed"
        title="armed — tap to disarm"
        onClick={() => void useSteering.getState().disarm()}
      >
        ⏻ {mmss(remaining)}
      </button>
    );
  }
  return (
    <span className="desk-arm-wrap">
      <button
        type="button"
        className={"desk-chip desk-arm-chip" + (holding ? " is-holding" : "")}
        title={stale ? "stale — arming will refuse" : "hold to arm steering"}
        onPointerDown={() => {
          setHolding(true);
          holdTimer.current = setTimeout(() => {
            cancelHold();
            void useSteering.getState().arm();
          }, HOLD_TO_ARM_MS);
        }}
        onPointerUp={cancelHold}
        onPointerLeave={cancelHold}
      >
        ARM
      </button>
      {armError && <span className="desk-arm-refusal">✕ {armError}</span>}
    </span>
  );
}

// The key palette (HS-90-02) — full key control on glass. Each button is
// ONE real key through `/keys`, shown only in the armed window. `^C` is the
// loud one (interrupt a runaway); the rest drive a TUI.
const KEY_BUTTONS: Array<{ label: string; key: string; title: string; loud?: boolean }> = [
  { label: "^C", key: "C-c", title: "interrupt — Ctrl-C", loud: true },
  { label: "Esc", key: "Escape", title: "Escape" },
  { label: "Tab", key: "Tab", title: "Tab" },
  { label: "⏎", key: "Enter", title: "Enter" },
  { label: "↑", key: "Up", title: "Up" },
  { label: "↓", key: "Down", title: "Down" },
  { label: "←", key: "Left", title: "Left" },
  { label: "→", key: "Right", title: "Right" },
];

function KeyPalette() {
  const keyState = useSteering((s) => s.keyState);
  const keyDetail = useSteering((s) => s.keyDetail);
  const lastKey = useSteering((s) => s.lastKey);
  return (
    <div className="desk-keypad">
      <span className="desk-keypad-label">Keys</span>
      <div className="desk-keypad-row">
        {KEY_BUTTONS.map((k) => (
          <button
            key={k.key}
            type="button"
            className={"desk-key" + (k.loud ? " is-interrupt" : "")}
            title={k.title}
            onClick={() => void useSteering.getState().sendKeys([k.key], k.label)}
          >
            {k.label}
          </button>
        ))}
        {keyState === "sent" && (
          <span className="desk-key-fate desk-steer-sent">✓ {lastKey}</span>
        )}
        {keyState === "refused" && (
          <span className="desk-key-fate desk-arm-refusal">✕ {keyDetail}</span>
        )}
      </div>
    </div>
  );
}

// The node chip (HS-90-02) — which machine the steering targets. Tap to
// cycle this Mac → each configured node; a node routes arm/steer/keys
// through the relay. Absent config reads the honest "this Mac".
function NodeChip() {
  const nodes = useSteering((s) => s.nodes);
  const targetNode = useSteering((s) => s.targetNode);
  useEffect(() => {
    void useSteering.getState().listNodes();
  }, []);
  if (nodes.length === 0) {
    return (
      <span className="desk-chip quiet desk-node-chip" title="steering targets this Mac">
        ⧉ this Mac
      </span>
    );
  }
  const options: (string | null)[] = [null, ...nodes];
  const next = options[(options.indexOf(targetNode) + 1) % options.length];
  return (
    <button
      type="button"
      className={"desk-chip desk-node-chip" + (targetNode ? " is-remote" : "")}
      title="tap to change the target machine"
      onClick={() => useSteering.getState().setTargetNode(next)}
    >
      ⧉ {targetNode || "this Mac"}
    </button>
  );
}

/** The pane picker (HS-90-02) — attach to ANY tmux pane on the machine,
 * not only a tracked session. Watching is free; arm to steer. A launcher
 * mounted on the desk beside the session surface. */
export function PanePicker() {
  const panes = useSteering((s) => s.panes);
  const panesState = useSteering((s) => s.panesState);
  const [open, setOpen] = useState(false);
  const toggle = () => {
    const next = !open;
    setOpen(next);
    if (next) void useSteering.getState().listPanes();
  };
  return (
    <div className={"desk-panepicker" + (open ? " is-open" : "")}>
      <button
        type="button"
        className="desk-chip desk-panepicker-launch"
        onClick={toggle}
        title="attach to any tmux pane"
      >
        ⧉ Panes
      </button>
      {open && (
        <div className="desk-panepicker-list">
          {panesState === "loading" && <span className="desk-panepicker-empty">…</span>}
          {panesState === "error" && (
            <span className="desk-panepicker-empty">tmux unreachable</span>
          )}
          {panesState === "loaded" && panes.length === 0 && (
            <span className="desk-panepicker-empty">no tmux panes</span>
          )}
          {panes.map((p) => (
            <button
              key={p.paneId}
              type="button"
              className={"desk-panepicker-item" + (p.active ? " is-active" : "")}
              onClick={() => {
                useSteering.getState().openSession(`pane:${p.paneId}`);
                setOpen(false);
              }}
            >
              <span className="desk-panepicker-id">{p.paneId}</span>
              <span className="desk-panepicker-meta">
                {p.session}
                {p.command ? ` · ${p.command}` : ""}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/** The voice-first composer (HS-87-03) — spoken first, typed if you
 * like, Enter its own deliberate chip. Rendered only while armed: the
 * ARM chip in the header IS the unarmed affordance. */
function SteerComposer() {
  const steerState = useSteering((s) => s.steerState);
  const steerDetail = useSteering((s) => s.steerDetail);
  const meetings = useDesk((s) => s.items.meeting);
  const [text, setText] = useState("");
  const [submitOn, setSubmitOn] = useState(true);
  const [grounding, setGrounding] = useState<GroundingSelection>(emptyGrounding());
  const [rails, setRails] = useState<RailsPick[]>([]);

  const send = async () => {
    const delivered = await useSteering
      .getState()
      .steer(text, submitOn, buildGrounding(grounding, rails));
    if (delivered) {
      setText(""); // a refused steer keeps its composition
      setGrounding(emptyGrounding());
      setRails([]);
    }
  };

  return (
    <div className="desk-steer">
      <div className="desk-steer-row">
        <MicButton
          label="Hold to speak"
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
          title={submitOn ? "Enter after send" : "no Enter — text only"}
          onClick={() => setSubmitOn((v) => !v)}
        >
          ⏎
        </button>
        <button
          type="button"
          className="desk-chip"
          disabled={steerState === "sending" || !text.trim()}
          onClick={() => void send()}
        >
          {steerState === "sending" ? "…" : "Send"}
        </button>
      </div>
      <GroundingSection
        meetings={(meetings || []).map((m) => ({
          id: m.id,
          title: String((m as any).title || "Untitled meeting"),
          startedAt: (m as any).startedAt,
        }))}
        selection={grounding}
        onChange={setGrounding}
        limitTokens={STEER_LIMIT_TOKENS}
      />
      <RailsPicker picks={rails} onChange={setRails} limitTokens={STEER_LIMIT_TOKENS} />
      {(!groundingIsEmpty(grounding) || rails.length > 0) && (
        <span className="desk-steer-grounded">
          objects ride in with a provenance header, capped at 8 KB
        </span>
      )}
      {steerState === "refused" && (
        <span className="desk-arm-refusal">✕ {steerDetail}</span>
      )}
      {steerState === "sent" && <span className="desk-steer-sent">✓ sent</span>}
    </div>
  );
}

/** Classify (HS-87-05): triage the session onto the desk and the rails —
 * keep the ask as a note, pin to a story, or flip a correlated story
 * through the Phase-82 proposal leg (the ProposalCard renders in the
 * conveyor). All through existing write paths. */
function ClassifySection({ sessionKey }: { sessionKey: string }) {
  const classifyState = useSteering((s) => s.classifyState);
  const manualPins = useSteering((s) => s.manualPins);
  const repos = useMissionControl((s) => s.repos);
  const mcSessions = useMissionControl((s) => s.sessions);
  const [pinInput, setPinInput] = useState("");

  const mc = mcSessions.find((s) => s.key === sessionKey);
  const correlated = mc?.storyRefs[0] || null;
  const flipTarget = correlated
    ? flipTargetForStory(repos, correlated.storyId, correlated.project)
    : null;
  const pinned = manualPins[sessionKey];

  return (
    <div className="desk-classify">
      <span className="desk-classify-label">Classify</span>
      <div className="desk-classify-row">
        <button
          type="button"
          className="desk-chip"
          onClick={() => void useSteering.getState().keepAsNote()}
        >
          {classifyState === "kept"
            ? "✓ kept as note"
            : classifyState === "failed"
              ? "retry keep"
              : "Keep as note"}
        </button>
        {flipTarget && (
          <button
            type="button"
            className="desk-chip"
            title={`propose a status flip for ${flipTarget.story}`}
            onClick={() =>
              useMissionControl
                .getState()
                .proposeFlip(flipTarget.repo, flipTarget.project, flipTarget.story, "done")
            }
          >
            Flip {flipTarget.story} →
          </button>
        )}
      </div>
      <div className="desk-classify-row">
        {pinned ? (
          <button
            type="button"
            className="desk-chip quiet"
            title="clear the manual pin"
            onClick={() => useSteering.getState().clearPin(sessionKey)}
          >
            pinned → {pinned} ✕
          </button>
        ) : (
          <>
            <MicButton label="Pin to story" onText={(t) => setPinInput(t.trim())} />
            <input
              className="desk-classify-input"
              value={pinInput}
              placeholder="story id (e.g. HS-87-05)"
              onChange={(e) => setPinInput(e.target.value)}
            />
            <button
              type="button"
              className="desk-chip quiet"
              disabled={!pinInput.trim()}
              onClick={() => {
                useSteering.getState().pinToStory(sessionKey, pinInput.trim());
                setPinInput("");
              }}
            >
              Pin
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export function SessionPullout() {
  const openKey = useSteering((s) => s.openKey);
  const session = useSteering((s) => s.session);
  const paneStatus = useSteering((s) => s.paneStatus);
  const paneDetail = useSteering((s) => s.paneDetail);
  const paneLines = useSteering((s) => s.paneLines);
  const armed = useSteering((s) => s.armed);
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
        <NodeChip />
        <ArmChip />
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

      {armed && (
        <footer className="desk-pullout-foot">
          <KeyPalette />
          <SteerComposer />
        </footer>
      )}
      <footer className="desk-pullout-foot">
        <ClassifySection sessionKey={openKey} />
      </footer>
    </motion.div>
  );
}
