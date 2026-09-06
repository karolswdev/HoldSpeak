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
import { useEffect, useRef, useState } from "react";
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
import { PaneWell, SurfaceFacts } from "../surface/Surface";
import {
  CycleGadget,
  LampGadget,
  LedMeter,
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

// The steer's context budget mirrors the hub's 8 KB cap (≈2000 tokens
// at 4 chars/token); the gauge refuses past it before any send.
const STEER_LIMIT_TOKENS = 2000;

// Glyph constants — avoid raw dingbat codepoints in JSX source lines.
const GLYPH_EDIT = String.fromCodePoint(0x270E);
const GLYPH_CLOSE = String.fromCodePoint(0x2715);
const GLYPH_CHECK = String.fromCodePoint(0x2713);

const PANE_STATE_LABEL: Record<string, string> = {
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
function ArmStrip() {
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

function KeyPalette() {
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
      label: "Panes",
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
            <button
              key={p.paneId}
              type="button"
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
            </button>
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

/** The voice-first composer (HS-87-03), available under resolved authority. */
function SteerComposer() {
  const steerState = useSteering((s) => s.steerState);
  const steerDetail = useSteering((s) => s.steerDetail);
  const openKey = useSteering((s) => s.openKey);
  const meetings = useDesk((s) => s.items.meeting);
  const {
    value: text,
    setDraft: setText,
    recovered: textRecovered,
  } = useDurableDraft(`steer:${openKey || "unattached"}`);
  const [submitOn, setSubmitOn] = useState(true);
  const [grounding, setGrounding] =
    useState<GroundingSelection>(emptyGrounding());
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

  const budgetTokens = groundingTokens(grounding) + railsTokens(rails);

  return (
    <div className="desk-steer">
      <div className="desk-steer-row">
        <MicButton
          label="Speak"
          draftScope={`steer:${openKey || "unattached"}`}
          onText={(t) => setText((prev) => (prev ? `${prev} ${t}` : t))}
        />
        {/* UX-CANON: needs redesign (HS-170-04) — raw textarea; no multiline gadget species */}
        <textarea
          className="desk-steer-input"
          value={text}
          rows={2}
          placeholder="Steer"
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(event) => {
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
          onClick={() => setSubmitOn((v) => !v)}
        />
        <TransportKey
          compact
          label="SEND"
          glyph="▸"
          disabled={steerState === "sending" || !text.trim()}
          onClick={() => void send()}
        />
      </div>
      {textRecovered ? (
        <span className="quiet">Recovered local steer draft.</span>
      ) : null}
      <GroundingSection
        meetings={(meetings || []).map((m) => ({
          id: m.id,
          title: String(m.title || "Untitled meeting"),
          startedAt: m.startedAt,
        }))}
        selection={grounding}
        onChange={setGrounding}
        limitTokens={STEER_LIMIT_TOKENS}
        meter={false}
      />
      <RailsPicker
        picks={rails}
        onChange={setRails}
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
      {steerState === "refused" && (
        <span className="desk-arm-refusal"><span aria-hidden="true">{GLYPH_CLOSE}</span> {steerDetail}</span>
      )}
      {steerState === "sent" && (
        <span className="desk-steer-sent"><span aria-hidden="true">{GLYPH_CHECK}</span> {steerDetail || "sent"}</span>
      )}
    </div>
  );
}

/** The policy line as axis-named tokens (HS-111-04): PANE · AUTHORITY
 * · RECEIPT — never a sentence. */
function SteeringPolicyFacts() {
  const operation = useSteering((s) => s.operation);
  const policy = useSteering((s) => s.policy);
  if (!operation || !policy) return null;
  const authority =
    policy.authority_basis === "control_posture"
      ? `${controlModeLabel(policy.mode || "yolo")} posture`
      : "armed pane grant";
  return (
    <SurfaceFacts
      value={{
        pane: operation.destination || "unresolved",
        authority,
        receipt: "after every attempt",
      }}
    />
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
            ? "KEPT"
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
                .proposeFlip(
                  flipTarget.repo,
                  flipTarget.project,
                  flipTarget.story,
                  "done",
                )
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
            PINNED {pinned}
          </button>
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
  const paneRaw = useSteering((s) => s.paneRaw);
  const paneGeom = useSteering((s) => s.paneGeom);
  const paneChangedAt = useSteering((s) => s.paneChangedAt);
  const armed = useSteering((s) => s.armed);
  const postureAuthorized = useSteering((s) => s.postureAuthorized);
  const paneId = useSteering((s) => s.paneId);
  const targetNode = useSteering((s) => s.targetNode);
  const { closeSession } = useSteering.getState();

  useEffect(() => {
    if (!openKey) return;
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
  }, [openKey]);

  if (!openKey) return null;

  const sessionId = openKey.split(":", 2)[1] || openKey;
  const live = paneStatus === "live";

  return (
    <DeskWindowFrame
      id="session"
      glyph="▮"
      minW={420}
      label={`${session?.agent || openKey.split(":", 2)[0]} · ${sessionId.slice(0, 8)}`}
      className="desk-pullout is-session"
      icon={
        <img
          src={spriteUrl("agent", sessionId)}
          alt=""
          width={16}
          height={16}
          className="desk-session-glyph desk-chrome-sprite"
          draggable={false}
        />
      }
      title={
        <>
          {session?.agent || openKey.split(":", 2)[0]} · {sessionId.slice(0, 8)}
        </>
      }
      actions={
        <>
          {live && <LampGadget label="LIVE" on tone="ok" />}
          <NodeCycle />
        </>
      }
      open={Boolean(openKey)}
      onClose={closeSession}
    >

      <div className="desk-pullout-body">
        <SurfaceFacts
          value={{
            pane: paneId || "",
            node: targetNode || "this Mac",
            state: session?.stale ? "stale" : "",
          }}
        />
        {session?.awaitingResponse && session.question ? (
          <pre className="desk-pullout-md desk-session-question">
            {session.question}
          </pre>
        ) : null}
        {/* HS-111-06/11 — the shared PaneWell seam: the raw stream
            renders through xterm; a stripped-only hub falls back to
            the pre face, named honestly. Read-only either way. */}
        <PaneWell
          live={live}
          lines={paneLines}
          raw={paneRaw}
          pane={paneGeom}
          changedAt={paneChangedAt}
          absence={
            <>
              <span aria-hidden="true">{GLYPH_CLOSE}</span> {PANE_STATE_LABEL[paneStatus] || humanizeWireValue(paneStatus)}
            </>
          }
        />
      </div>

      <SurfaceFooter
        receipt={<ReceiptLine sessionKey={openKey} />}
        verbs={<>
          <ArmStrip />
          {(armed || postureAuthorized) && (
            <>
              <SteeringPolicyFacts />
              <KeyPalette />
              <SteerComposer />
              {armed ? (
                <FactoryControls />
              ) : (
                <button
                  type="button"
                  className="desk-chip quiet"
                  onClick={() => void useSteering.getState().arm()}
                >
                  Arm pane {paneId || "unresolved"} for rename and kill
                </button>
              )}
            </>
          )}
          <ClassifySection sessionKey={openKey} />
        </>}
      />
    </DeskWindowFrame>
  );
}
