import { windowName } from "../windowName";
import { SurfaceFooter } from "../surface/SurfaceFooter";
// The session pull-out (HS-87-01/02) — attach + arm, in the desk
// grammar. Watching is free. Secure/Normal use an exact pane grant; a Hub
// policy decision can make a registered pane directly steerable in YOLO.
//
// HS-111-04 — the channel strip (audit §3.4): the consent mechanics are
// byte-for-byte unchanged (every arm/disarm/steer/sendKeys/killOpen call,
// the typed-refusal rendering, the grant re-sync); only the RENDER moved
// to the gadget grammar — transport keys, lamps, LedMeters, facts tokens.
import "./session-pullout.css";
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { MicButton } from "./MicButton";
import { GroundingSection } from "./GroundingSection";
import { ReceiptLine } from "./ReceiptLine";
import { RailsPicker } from "./RailsPicker";
import { useDesk } from "../store";
import {
  buildGrounding,
  emptyGrounding,
  groundingIsEmpty,
  groundingTokens,
  railsTokens,
  type GroundingSelection,
  type RailsPick,
} from "../grounding";
import { flipTargetForStory, useMissionControl } from "../missioncontrol";
import { mmss, useSteering } from "../steering";
import { useDurableDraft } from "../../lib/durableDraft";
import { controlModeLabel, humanizeWireValue } from "../../lib/productLanguage";
import { PaneWell, SurfaceFacts, SurfaceSection, SurfaceWell } from "../surface/Surface";
import { AskWell, FoldGadget } from "../surface";
import { AppHead, StatusStrip } from "../surface/kit";
import { wireClock } from "../surface/format";
import { useAgentFlights } from "../agentFlights";
import { agentName } from "../lane/laneWire";
import {
  CycleGadget,
  LampGadget,
  LedMeter,
  PadGadget,
  StringGadget,
  TransportKey,
  TransportRow,
} from "../surface/gadgets";
import {
  DeskWindowFrame,
  announceLauncher,
  retractLauncher,
} from "./DeskWindow";
import { spriteUrl } from "../sprites";
import { AgentWords } from "./AgentWords";
import { useLaneOwnsSteering } from "../lane/laneStore";
import { useOnCoderFrame } from "../useDeskChangedRefresh";

// The steer's context budget mirrors the hub's 8 KB cap (≈2000 tokens
// at 4 chars/token); the gauge refuses past it before any send.
const STEER_LIMIT_TOKENS = 2000;

// Glyph constants — avoid raw dingbat codepoints in JSX source lines.
const GLYPH_EDIT = String.fromCodePoint(0x270E);
const GLYPH_CLOSE = String.fromCodePoint(0x2715);
const GLYPH_CHECK = String.fromCodePoint(0x2713);

export const PANE_STATE_LABEL: Record<string, string> = {
  pane_gone: "pane gone",
  tmux_absent: "tmux absent",
  no_pane: "no pane on this session",
  unknown_session: "gone from the registry",
  error: "peek failed",
  unreachable: "hub unreachable",
  idle: "…",
};

/** The arming strip (HS-87-02 mechanics, HS-111-04 render): ARM is one
 * transport key — armed is INVERTED VIDEO, never a glow ring — and the
 * grant's remainder drains a `GRANT` LedMeter beside the mono clock. */
export function ArmStrip() {
  const armed = useSteering((s) => s.armed);
  const armedUntil = useSteering((s) => s.armedUntil);
  const armError = useSteering((s) => s.armError);
  const armCommitment = useSteering((s) => s.armCommitment);
  const stale = useSteering((s) => Boolean(s.session?.stale));
  const postureAuthorized = useSteering((s) => s.postureAuthorized);
  const policy = useSteering((s) => s.policy);
  const paneId = useSteering((s) => s.paneId);
  const [remaining, setRemaining] = useState(0);
  // The grant's full span, observed client-side: the largest remainder
  // seen while armed anchors the draining meter.
  const totalRef = useRef(0);

  useEffect(() => {
    if (!armed || armedUntil === null) {
      totalRef.current = 0;
      return;
    }
    const tick = () => setRemaining((armedUntil - Date.now()) / 1000);
    tick();
    const t = setInterval(tick, 500);
    return () => clearInterval(t);
  }, [armed, armedUntil]);
  if (armed && remaining > totalRef.current) totalRef.current = remaining;

  const grantMeter = armed ? (
    <>
      <LedMeter
        label="GRANT"
        value={totalRef.current > 0 ? remaining / totalRef.current : 0}
      />
      <span className="surface-token">{mmss(remaining)}</span>
    </>
  ) : null;

  if (postureAuthorized) {
    return (
      <TransportRow>
        <TransportKey
          compact
          active
          label={`${controlModeLabel(policy?.mode || "yolo")} · DIRECT`}
          glyph="⏻"
          title={`Registered ${paneId || "pane"}; steering runs directly and leaves a Receipt`}
        />
        {armed ? (
          <TransportKey
            compact
            active
            label="CTRL"
            glyph="⌸"
            title="Disarm the separate session-control grant"
            onClick={() => void useSteering.getState().disarm()}
          />
        ) : null}
        {grantMeter}
      </TransportRow>
    );
  }

  return (
    <TransportRow>
      <TransportKey
        label="ARM"
        glyph="⏻"
        active={armed}
        title={
          armed
            ? "Armed: press to disarm"
            : stale
              ? "Stale session; arming will refuse"
              : armCommitment
        }
        onClick={() =>
          void (armed
            ? useSteering.getState().disarm()
            : useSteering.getState().arm())
        }
      />
      {grantMeter}
      {armError && <span className="desk-arm-refusal"><span aria-hidden="true">{GLYPH_CLOSE}</span> {armError}</span>}
    </TransportRow>
  );
}

// The key palette (HS-90-02) — full key control on glass. Each key is
// ONE real key through `/keys`, shown under resolved grant/posture
// authority. `^C` is the loud one (interrupt a runaway); the rest drive
// a TUI. HS-111-04: rendered as transport keys (glyph over mono word).
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
  { word: "LEFT", glyph: "←", key: "Left", title: "Left" },
  { word: "RIGHT", glyph: "→", key: "Right", title: "Right" },
];

export function KeyPalette() {
  const keyState = useSteering((s) => s.keyState);
  const keyDetail = useSteering((s) => s.keyDetail);
  const lastKey = useSteering((s) => s.lastKey);
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
              void useSteering.getState().sendKeys([k.key], k.word)
            }
          />
        ))}
      </TransportRow>
      {keyState === "sent" && (
        <span className="desk-key-fate desk-steer-sent">
          <span aria-hidden="true">{GLYPH_CHECK}</span> {keyDetail || lastKey}
        </span>
      )}
      {keyState === "refused" && (
        <span className="desk-key-fate desk-arm-refusal"><span aria-hidden="true">{GLYPH_CLOSE}</span> {keyDetail}</span>
      )}
    </div>
  );
}

// The node gadget (HS-90-02) — which machine the steering targets; a
// cycling pick IS the CycleGadget species. Absent config reads the
// honest "this Mac".
function NodeCycle() {
  const nodes = useSteering((s) => s.nodes);
  const targetNode = useSteering((s) => s.targetNode);
  useEffect(() => {
    void useSteering.getState().listNodes();
  }, []);
  return (
    <CycleGadget
      label="Node"
      value={targetNode || ""}
      disabled={nodes.length === 0}
      options={[
        { value: "", label: "NODE: this Mac" },
        ...nodes.map((n) => ({ value: n, label: `NODE: ${n}` })),
      ]}
      onChange={(v) => useSteering.getState().setTargetNode(v || null)}
    />
  );
}

/** The pane picker (HS-90-02) — attach to ANY tmux pane on the machine,
 * not only a tracked session. Watching is free; policy resolves steering
 * authority. A launcher mounted on the desk beside the session surface.
 * HS-111-04: the transient is mini-ledger rows; active = the ledger's
 * open well fill, never a smuggled left accent rail. */
export function PanePicker() {
  const panes = useSteering((s) => s.panes);
  const panesState = useSteering((s) => s.panesState);
  const factoryState = useSteering((s) => s.factoryState);
  const factoryDetail = useSteering((s) => s.factoryDetail);
  const [open, setOpen] = useState(false);
  const [spawnName, setSpawnName] = useState("");
  const doSpawn = async () => {
    const name = spawnName.trim();
    if (!name) return;
    const ok = await useSteering.getState().spawnSession(name);
    if (ok) {
      setSpawnName("");
      setOpen(false); // the new session's pull-out is now open
    }
  };
  // HS-97-07 — one shelf: the floating pill is gone; the dock carries
  // the Panes launcher (toggle: the list is a transient, not a window).
  useEffect(() => {
    announceLauncher({
      id: "panes",
      label: "Terminals",
      glyph: "⧉",
      open,
      activate: () => {
        const next = !open;
        setOpen(next);
        if (next) void useSteering.getState().listPanes();
      },
    });
    return () => retractLauncher("panes");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  return (
    <div className={"desk-panepicker" + (open ? " is-open" : "")}>
      {open && (
        <div className="desk-panepicker-list">
          {/* HS-90-03: spawn a new session from the desk */}
          <div className="desk-panepicker-spawn">
            <StringGadget
              label="New session name"
              value={spawnName}
              onChange={setSpawnName}
              onKeyDown={(e) => {
                if (e.key === "Enter") void doSpawn();
              }}
            />
            <TransportKey
              compact
              label="SPAWN"
              glyph="＋"
              disabled={!spawnName.trim() || factoryState === "working"}
              onClick={() => void doSpawn()}
            />
          </div>
          {factoryState === "failed" && (
            <span className="desk-panepicker-empty desk-arm-refusal">
              <span aria-hidden="true">{GLYPH_CLOSE}</span> {factoryDetail}
            </span>
          )}
          <div className="desk-panepicker-divider" />
          {panesState === "loading" && (
            <span className="desk-panepicker-empty">…</span>
          )}
          {panesState === "error" && (
            <span className="desk-panepicker-empty">tmux unreachable</span>
          )}
          {panesState === "loaded" && panes.length === 0 && (
            <span className="desk-panepicker-empty">no tmux panes</span>
          )}
          {panes.map((p) => (
            <Button
              key={p.paneId}
              variant="chrome"
              className={
                "desk-panepicker-item" + (p.active ? " is-active" : "")
              }
              onClick={() => {
                useSteering.setState({ attachedSession: p.session });
                useSteering.getState().openSession(`pane:${p.paneId}`);
                setOpen(false);
              }}
            >
              <span className="desk-panepicker-id">{p.paneId}</span>
              <span className="desk-panepicker-meta">
                {p.session}
                {p.command ? ` · ${p.command}` : ""}
              </span>
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}

// The factory controls (HS-90-03) — rename + kill the open session, on glass.
// Rendered only with the separate session-control grant: factory authority is
// deliberately not inherited from direct YOLO steering. Kill is two-step; the
// confirm state is inverted danger video (HS-111-04).
function FactoryControls() {
  const attachedSession = useSteering((s) => s.attachedSession);
  const factoryState = useSteering((s) => s.factoryState);
  const [renaming, setRenaming] = useState(false);
  const [newName, setNewName] = useState("");
  const [confirmKill, setConfirmKill] = useState(false);

  return (
    <div className="desk-factory">
      <span className="desk-factory-label">Session</span>
      <div className="desk-factory-row">
        {renaming ? (
          <>
            <StringGadget
              label="New session name"
              value={newName}
              placeholder={attachedSession || undefined}
              autoFocus
              onChange={setNewName}
              onKeyDown={(event) => {
                if (event.key !== "Escape") return;
                event.preventDefault();
                event.stopPropagation();
                setNewName("");
                setRenaming(false);
              }}
            />
            <TransportKey
              compact
              label="RENAME"
              glyph={GLYPH_EDIT}
              disabled={!newName.trim() || factoryState === "working"}
              onClick={async () => {
                const ok = await useSteering
                  .getState()
                  .renameOpen(newName.trim());
                if (ok) {
                  setRenaming(false);
                  setNewName("");
                }
              }}
            />
            <TransportKey
              compact
              label="BACK"
              glyph={GLYPH_CLOSE}
              onClick={() => setRenaming(false)}
            />
          </>
        ) : (
          <TransportKey
            compact
            label="RENAME"
            glyph={GLYPH_EDIT}
            disabled={!attachedSession}
            title={
              attachedSession
                ? `rename ${attachedSession}`
                : "no session to rename"
            }
            onClick={() => setRenaming(true)}
          />
        )}
        {confirmKill ? (
          <>
            <TransportKey
              compact
              active
              tone="danger"
              label="KILL · SURE?"
              glyph="⌫"
              onClick={() => void useSteering.getState().killOpen("session")}
            />
            <TransportKey
              compact
              label="BACK"
              glyph={GLYPH_CLOSE}
              onClick={() => setConfirmKill(false)}
            />
          </>
        ) : (
          <TransportKey
            compact
            tone="danger"
            label="KILL"
            glyph="⌫"
            title="end this session (armed + confirm)"
            onClick={() => setConfirmKill(true)}
          />
        )}
      </div>
    </div>
  );
}

interface SteerOptions {
  submitOn: boolean;
  grounding: GroundingSelection;
  rails: RailsPick[];
}
const emptySteerOptions = (): SteerOptions => ({ submitOn: true, grounding: emptyGrounding(), rails: [] });

/** The voice-first composer (HS-87-03), available under resolved authority. */
function SteerComposer({ listenSignal = 0, available = true, options, onOptionsChange }: {
  listenSignal?: number;
  available?: boolean;
  options: SteerOptions;
  onOptionsChange: (options: SteerOptions) => void;
}) {
  const steerState = useSteering((s) => s.steerState);
  const openKey = useSteering((s) => s.openKey);
  const meetings = useDesk((s) => s.items.meeting);
  const {
    value: text,
    setDraft: setText,
    recovered: textRecovered,
  } = useDurableDraft(`steer:${openKey || "unattached"}`);
  const { submitOn, grounding, rails } = options;

  const send = async () => {
    if (!available) return;
    const delivered = await useSteering
      .getState()
      .steer(text, submitOn, buildGrounding(grounding, rails));
    if (delivered && useSteering.getState().openKey === openKey) {
      setText(""); // a refused steer keeps its composition
      onOptionsChange({ ...options, grounding: emptyGrounding(), rails: [] });
    }
  };

  const budgetTokens = groundingTokens(grounding) + railsTokens(rails);

  return (
    <div className="desk-steer">
      <div className="desk-steer-row">
        <PadGadget
          label="Direct"
          micLabel="Speak"
          micStartSignal={listenSignal}
          micDraftScope={`steer:${openKey || "unattached"}`}
          value={text}
          rows={2}
          placeholder="Direct the agent"
          onChange={setText}
          onKeyDown={(event) => {
            // Conductor F2 (K5c): Enter sends; Shift+Enter is a new line.
            if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
              event.preventDefault();
              if (text.trim() && steerState !== "sending") void send();
              return;
            }
            if (event.key !== "Escape") return;
            event.preventDefault();
            event.stopPropagation();
            setText("");
          }}
        />
        <TransportKey
          compact
          label="ENTER"
          glyph="⏎"
          active={submitOn}
          title={submitOn ? "Enter after send" : "no Enter: text only"}
          onClick={() => onOptionsChange({ ...options, submitOn: !submitOn })}
        />
        <TransportKey
          compact
          label="SEND"
          glyph="▸"
          disabled={!available || steerState === "sending" || !text.trim()}
          onClick={() => void send()}
        />
      </div>
      {textRecovered ? (
        <span className="quiet">Recovered local steer draft.</span>
      ) : null}
      <FoldGadget title="Steering sources">
      <GroundingSection
        meetings={(meetings || []).map((m) => ({
          id: m.id,
          title: String(m.title || "Meeting with no title"),
          startedAt: m.startedAt,
        }))}
        selection={grounding}
        onChange={(grounding) => onOptionsChange({ ...options, grounding })}
        limitTokens={STEER_LIMIT_TOKENS}
        meter={false}
      />
      <RailsPicker
        picks={rails}
        onChange={(rails) => onOptionsChange({ ...options, rails })}
        limitTokens={STEER_LIMIT_TOKENS}
        meter={false}
      />
      {(!groundingIsEmpty(grounding) || rails.length > 0) && (
        <span className="desk-steer-grounded">
          <LedMeter
            label="CTX"
            value={budgetTokens / STEER_LIMIT_TOKENS}
          />
          <span className="surface-token">CAP 8 KB</span>
        </span>
      )}
      </FoldGadget>
    </div>
  );
}

/** The policy line as axis-named tokens (HS-111-04): AUTHORITY ·
 * RECEIPT — never a sentence. Conductor F2: compact tokens on the footer
 * row (a facts list there squeezed to one letter per line), and the pane
 * is said once, in the body's facts. */
export function SteeringPolicyFacts() {
  const operation = useSteering((s) => s.operation);
  const policy = useSteering((s) => s.policy);
  if (!operation || !policy) return null;
  const authority =
    policy.authority_basis === "control_posture"
      ? `${controlModeLabel(policy.mode || "yolo")} POSTURE`
      : "ARMED PANE GRANT";
  return (
    <span className="desk-session-policy" data-testid="session-policy">
      <span className="surface-token" data-chip>{`AUTHORITY · ${authority.toUpperCase()}`}</span>
      <span className="surface-token" data-chip>RECEIPT · EVERY ATTEMPT</span>
    </span>
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
        <Button
          dense
          variant="ghost"
          className="desk-chip"
          onClick={() => void useSteering.getState().keepAsNote()}
        >
          {classifyState === "kept"
            ? "KEPT"
            : classifyState === "failed"
              ? "Retry keep"
              : "Keep as note"}
        </Button>
        {flipTarget && (
          <Button
            dense
            variant="ghost"
            className="desk-chip"
            title={`propose a status flip for ${flipTarget.story}`}
            onClick={() =>
              useMissionControl
                .getState()
                .proposeFlip(
                  flipTarget.repo,
                  flipTarget.project,
                  flipTarget.story,
                  "done",
                )
            }
          >
            Flip {flipTarget.story} →
          </Button>
        )}
      </div>
      <div className="desk-classify-row">
        {pinned ? (
          <Button
            dense
            variant="ghost"
            className="desk-chip quiet"
            title="clear the manual pin"
            onClick={() => useSteering.getState().clearPin(sessionKey)}
          >
            PINNED {pinned}
          </Button>
        ) : (
          <>
            <MicButton
              label="Pin to story"
              draftScope={`story-pin:${sessionKey}`}
              onText={(t) => setPinInput(t.trim())}
            />
            <StringGadget
              label="Story id"
              value={pinInput}
              placeholder="e.g. HS-87-05"
              onChange={setPinInput}
            />
            <Button
              dense
              variant="ghost"
              className="desk-chip quiet"
              disabled={!pinInput.trim()}
              onClick={() => {
                useSteering.getState().pinToStory(sessionKey, pinInput.trim());
                setPinInput("");
              }}
            >
              Pin
            </Button>
          </>
        )}
      </div>
    </div>
  );
}

/** The same ask well as a launched lane, through the existing steering route. */
function SessionAnswerWell({ question, agent, available, listenSignal }: { question: string; agent: string; available: boolean; listenSignal: number }) {
  const openKey = useSteering((s) => s.openKey);
  const sending = useSteering((s) => s.steerState === "sending");
  const armed = useSteering((s) => s.armed);
  const direct = useSteering((s) => s.postureAuthorized);
  const { value, setDraft } = useDurableDraft(`steer:${openKey || "unattached"}`);
  const answer = async (text: string) => {
    if (await useSteering.getState().steer(text, true, null)) setDraft("");
  };
  return <div className="desk-session-answer" data-testid="session-answer-well">
    <AskWell
      agent={agent}
      question={question}
      value={value}
      onChange={setDraft}
      onAnswer={(text) => void answer(text)}
      draftScope={`steer:${openKey || "unattached"}`}
      listenSignal={listenSignal}
      busy={sending}
      disabled={!available}
      arm={available ? armed || direct ? <SteeringPolicyFacts /> : <ArmStrip /> : <span className="desk-session-terminal-fact">Terminal unavailable</span>}
    />
  </div>;
}

export function SessionPullout() {
  const openKey = useSteering((s) => s.openKey);
  const session = useSteering((s) => s.session);
  const paneStatus = useSteering((s) => s.paneStatus);
  const paneDetail = useSteering((s) => s.paneDetail);
  const paneLines = useSteering((s) => s.paneLines);
  const paneRaw = useSteering((s) => s.paneRaw);
  const paneGeom = useSteering((s) => s.paneGeom);
  const paneChangedAt = useSteering((s) => s.paneChangedAt);
  const armed = useSteering((s) => s.armed);
  const postureAuthorized = useSteering((s) => s.postureAuthorized);
  const answerOpen = useSteering((s) => s.answerOpen);
  const answerSeq = useSteering((s) => s.answerSeq);
  const paneId = useSteering((s) => s.paneId);
  const targetNode = useSteering((s) => s.targetNode);
  const steerState = useSteering((s) => s.steerState);
  const steerDetail = useSteering((s) => s.steerDetail);
  const row = useAgentFlights((s) => s.sessions.find((r) => r.key === openKey));
  const [terminal, setTerminal] = useState(false);
  const [directing, setDirecting] = useState(false);
  const [steerOptions, setSteerOptions] = useState(emptySteerOptions);
  const terminalAnswerSeq = useRef(0);
  const { closeSession } = useSteering.getState();
  // PHILO-14 C2: a session that belongs to a launch has the agent's lane
  // window as its face (lane/LaneWindow.tsx); this window is for a plain one
  // (a pane opened from Panes keeps it while a lane is open).
  const laneLaunchId = useLaneOwnsSteering();
  const refresh = useCallback(() => {
    if (openKey) void useAgentFlights.getState().load();
  }, [openKey]);
  useOnCoderFrame(refresh);

  useEffect(() => {
    setTerminal(Boolean(openKey?.startsWith("pane:")));
    setDirecting(false);
    setSteerOptions(emptySteerOptions());
    terminalAnswerSeq.current = 0;
    if (openKey && !useAgentFlights.getState().loaded) void useAgentFlights.getState().load();
  }, [openKey]);

  useEffect(() => {
    if (answerOpen && answerSeq && answerSeq !== terminalAnswerSeq.current) setTerminal(false);
  }, [answerOpen, answerSeq]);

  useEffect(() => {
    if (!openKey || laneLaunchId) return;
    // A desk window closes deliberately (✕ or Escape) — never from a stray
    // click elsewhere on the desk; a live peek must survive arranging.
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape" || e.defaultPrevented) return;
      // Inline rename/compose owns Escape first; their handlers cancel and
      // stop propagation rather than letting the window consume the key.
      if (
        e.target instanceof Element &&
        e.target.matches(".desk-steer-input, .gadget-string input")
      )
        return;
      closeSession();
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
    };
  }, [openKey, laneLaunchId]);

  if (!openKey || laneLaunchId) return null;

  const sessionId = openKey.slice(openKey.indexOf(":") + 1);
  const live = paneStatus === "live";
  const available = live && Boolean(paneId);
  const raw = (row?.raw?.session ?? row?.raw ?? {}) as Record<string, unknown>;
  const agentId = row?.agent || session?.agent || openKey.split(":", 1)[0];
  const agent = agentName(agentId);
  const question = (session?.blocked || session?.awaitingResponse || row?.blocked) ? session?.question || row?.question || "" : "";
  const report = String(raw.last_assistant_text ?? "").trim();
  const screenReport = String(row?.screen?.said ?? "").trim();
  const latestReport = report || screenReport;
  // A Back press restores the composer without replaying the Speak request
  // whose mic was unmounted on entry to the terminal. A later request is new.
  const listenSignal = answerOpen && answerSeq !== terminalAnswerSeq.current ? answerSeq : 0;
  const tool = String(raw.last_tool_name ?? "").trim();
  const screenCommand = String(row?.screen?.command ?? "").trim();
  const updated = String(raw.last_assistant_text_at || raw.updated_at || session?.updatedAt || "");
  const state = session?.stale ? "Stale session" : question ? row?.idle ? "Idle" : "Needs your answer" : humanizeWireValue(row?.state || "working");
  // The all-session projection retains working sessions that the awaiting
  // desk bucket deliberately omits. Compound identity keeps agents separate.
  const sessionName = windowName({
    kind: "session",
    project: row?.flight?.title || row?.flight?.projectName || row?.name,
    agent,
  }, sessionId);

  return (
    <DeskWindowFrame
      id="session"
      glyph="▮"
      minW={360}
      defaultW={760}
      fitContent
      label={sessionName}
      kindWord="Agent session"
      className="desk-pullout is-session"
      icon={
        <img
          src={spriteUrl("agent", openKey, "rest", row?.agent || session?.agent || openKey.split(":", 1)[0])}
          alt=""
          width={16}
          height={16}
          className="desk-session-glyph desk-chrome-sprite"
          draggable={false}
        />
      }
      title={sessionName}
      actions={
        <>
          {live && <LampGadget label="LIVE" on tone="ok" />}
        </>
      }
      open={Boolean(openKey)}
      onClose={closeSession}
    >

      <div className="desk-pullout-body desk-session-body">
        {terminal ? <div className="desk-session-terminal" data-testid="session-terminal">
          <PaneWell
            live={live}
            lines={paneLines}
            raw={paneRaw}
            pane={paneGeom}
            changedAt={paneChangedAt}
            absence={
              <>
                <span>Terminal unavailable · {PANE_STATE_LABEL[paneStatus] || humanizeWireValue(paneStatus)}</span>
                {paneDetail ? <span className="desk-session-pane-detail">{paneDetail}</span> : null}
              </>
            }
          />
          {!live ? <div className="desk-session-terminal-verbs">
            <Button dense variant="ghost" onClick={() => void useSteering.getState().poll()}>Retry</Button>
            <Button dense variant="ghost" onClick={() => setTerminal(false)}>Back to session</Button>
          </div> : null}
        </div> : <>
        <div className="desk-session-identity" data-testid="session-agent-identity">
          <img
            src={spriteUrl("agent", openKey, "rest", agentId)}
            alt=""
            width={64}
            height={64}
            className="desk-session-agent-portrait desk-chrome-sprite"
            data-testid="session-agent-portrait"
            draggable={false}
          />
          <AppHead fact={state} data-testid="session-head">
            <StatusStrip items={[{ text: agent }, updated ? { text: wireClock(updated) } : null, raw.model ? { text: String(raw.model) } : null]} />
          </AppHead>
        </div>
        {question ? <SessionAnswerWell key={openKey} question={question} agent={agent} available={available} listenSignal={listenSignal} /> : null}
        {latestReport && latestReport !== question ? (
          <SurfaceSection label="Latest report" className="desk-session-report" data-testid="session-report">
            <SurfaceWell><AgentWords text={latestReport} /></SurfaceWell>
          </SurfaceSection>
        ) : null}
        {tool || screenCommand ? (
          <div className="desk-session-activity" data-testid="session-activity">
            <span className="desk-session-activity-lamp" aria-hidden="true" />
            <span className="desk-session-activity-label">Latest activity</span>
            {tool ? <span className="desk-session-activity-value">{tool}</span> : null}
            {screenCommand ? <><span className="desk-session-activity-label">Command</span><span className="desk-session-activity-value">{screenCommand}</span></> : null}
          </div>
        ) : !latestReport && !question ? <p className="desk-session-state">No report yet</p> : null}
        {!question && (answerOpen || directing) ? (
          <div className="desk-session-answer" data-testid="session-answer-well">
            {available ? armed || postureAuthorized ? <SteeringPolicyFacts /> : <ArmStrip /> : <span className="desk-session-terminal-fact">Terminal unavailable</span>}
            <SteerComposer key={openKey} listenSignal={listenSignal} available={available} options={steerOptions} onOptionsChange={setSteerOptions} />
          </div>
        ) : null}
        <FoldGadget title="Details" className="desk-session-details">
          <SurfaceFacts value={{ session: sessionId, project: row?.name || "", node: targetNode || "this Mac", pane: paneId || "", folder: String(raw.cwd || "") }} />
          <NodeCycle />
          <div className="desk-session-controls" data-testid="session-controls">
            {available ? <>
              {!question && !answerOpen && !directing ? <ArmStrip /> : null}
              {(armed || postureAuthorized) ? <>
                <KeyPalette />
                {armed ? <FactoryControls /> : <span className="desk-session-arm" data-testid="session-arm-control">
                  <span className="surface-token" data-testid="session-arm-pane">{`PANE · ${paneId}`}</span>
                  <Button dense variant="ghost" className="desk-chip quiet" aria-label={`Arm rename/kill: pane ${paneId}`} data-testid="session-arm-verb" onClick={() => void useSteering.getState().arm()}>Arm rename/kill</Button>
                </span>}
              </> : null}
            </> : null}
            <ClassifySection sessionKey={openKey} />
          </div>
        </FoldGadget>
        </>}
      </div>

      <SurfaceFooter
        className="desk-session-footer"
        receipt={steerState === "sent" || steerState === "refused" ? <span className={steerState === "refused" ? "desk-arm-refusal" : "desk-steer-sent"}>{steerState === "sent" ? "sent" : "Not sent"}{steerDetail ? ` · ${steerDetail}` : ""}</span> : <ReceiptLine sessionKey={openKey} />}
        verbs={<>
          <Button dense variant="ghost" data-testid="session-open-terminal" aria-pressed={terminal} onClick={() => {
            if (!terminal) terminalAnswerSeq.current = answerSeq;
            setTerminal(!terminal);
          }}>{terminal ? "Back to session" : "Open terminal"}</Button>
          {!question && available ? <Button dense variant="secondary" aria-pressed={directing} onClick={() => { setDirecting(terminal || !directing); setTerminal(false); }}>Direct</Button> : null}
          <Button dense variant="ghost" data-testid="session-refresh" onClick={() => { void refresh(); void useSteering.getState().poll(); }}>Refresh</Button>
        </>}
      />
    </DeskWindowFrame>
  );
}
