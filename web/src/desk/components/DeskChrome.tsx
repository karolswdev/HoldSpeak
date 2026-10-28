// The Desk's floating system chrome. The room menu stays compact; the opposite
// cluster exposes the three daily starts, one searchable tool shelf, layout,
// and refresh. A fresh Desk renders the same starts centrally instead.
// HS-111-07 — the mark menu DERIVES from the one verb registry (its
// hardcoded verb list was parallel list #2) and rides the WorkMenu
// portal, so it draws over windows like every chrome transient.
import { needYouWords } from "../surface/count";
import "./chrome-menus.css";
import { useEffect, useState, useRef } from "react";
import { useTrustWindow } from "./TrustWindow";
import { useDesk } from "../store";
import { useSettleState } from "../settleState";
import { WorkMenu, type WorkMenuEntry } from "./DeskMenu";
import { verbById, verbLabel, type VerbContext } from "../verbRegistry";
import { useKeymap } from "../keymap";
import { egressBadge, inboundBadge, type EgressBadge } from "../setup";
import { LampGadget } from "../surface/gadgets";
import { ScreenRecordLamp } from "../recordings/ScreenRecord";
import { subscribeMicPhase, type MicPhase } from "../../lib/micSession";
import { callLoopState, stopCallLoop } from "../../lib/callLoop";
import { TALK_STOP_EVENT } from "./MicButton";
import { DeskToolShelf } from "./DeskToolShelf";
import { DeskMenuBar } from "./DeskMenuBar";
import { useFrontWindowId, useAllOpenWindows } from "./window/windowRegistry";
import { useNeedsYou } from "../needsYou";
import { openNeedsYouDrawer } from "../screen/open";
import { useAftercare } from "../intelligenceAttention";
import { openSourceRef } from "../surface/citations";
import { useRuntimeBus } from "../../runtime/RuntimeBus";
import { useDeskWriteReceipt } from "../hooks/useWriteReceipt";
import { useCompactViewport } from "../useCompactViewport";
import { phoneRing, usePhoneSwipe } from "./window/phoneRing";
import { ScreenSwitcher } from "./window/ScreenSwitcher";
import { SYSTEM } from "../systemSprites";
import { MARK_APPLICATION_COMMANDS } from "../applications";
import { Button } from "../../components/signal/Signal";

/** The mark menu holds setup only. Builder actions, including Refresh from
 * hub, live under Go ▸ Builder; keyboard help is the final setup row. */
const MARK_VERBS: string[] = [];

/** HS-100-11 — the attention bell. PHILO-17 (needsyou, walker TAXES): the
 * bell carries the ONE needs-you number and opens Needs you, the list that
 * number counts (not the system shade). */
function AttentionBell() {
  const { count } = useNeedsYou();
  const aftercare = useAftercare();
  const [readyVisible, setReadyVisible] = useState(Boolean(aftercare));
  useEffect(() => {
    if (!aftercare) {
      setReadyVisible(false);
      return;
    }
    setReadyVisible(true);
    const timer = window.setTimeout(() => setReadyVisible(false), 6000);
    return () => window.clearTimeout(timer);
  }, [aftercare?.meetingId, aftercare?.title]);
  const badge = count > 0 ? count : 0;
  const ready = readyVisible && aftercare;
  return (
    <Button
      variant="chrome"
      className="desk-bell"
      aria-label={ready ? `Meeting ready: ${ready.title}` : badge ? `Needs you: ${needYouWords(badge)}` : "Needs you"}
      title={ready ? "Meeting ready" : "Needs you"}
      data-testid="desk-bell"
      onClick={() => ready ? openSourceRef(`meeting:${ready.meetingId}?view=review`) : openNeedsYouDrawer()}
    >
      {/* HS-111-09 — 16px source renders at 16 CSS px (integer-true). */}
      <img src={SYSTEM.menuBell} alt="" width={16} height={16} className="desk-chrome-sprite" draggable={false} />
      {ready ? <span className="desk-bell-ready" role="status">READY</span> : null}
      {badge ? <strong>{badge}</strong> : null}
    </Button>
  );
}

/* HS-112-06 — the mic lamp: while the Desk holds a microphone grant the
   chrome says so, from every room. It is absent only when the device is
   released (tracks stopped) — so its presence, not a colour, is the honest
   signal that audio is live.
   Betterment C8: while it listens the lamp says `Listening` and carries the
   verb that ends it, `Stop` (TALK_STOP_EVENT reaches the Talk that listens;
   an open mic is dropped). `MIC HELD` is gone from the face. */
export function MicLamp() {
  const [phase, setPhase] = useState<MicPhase>("closed");
  useEffect(() => subscribeMicPhase(setPhase), []);
  if (phase === "closed") return null;
  const listening = phase !== "suspended";
  return (
    <span className="desk-mic-lamp" role="status" data-testid="desk-mic-lamp">
      <LampGadget label={listening ? "Listening" : "Mic idle"} on={listening} tone={listening ? "ok" : "warn"} />
      {listening ? (
        <Button
          dense
          variant="ghost"
          data-testid="desk-mic-lamp-stop"
          onClick={() => {
            // The Talk that listens (a held capture) and Speak's open mic
            // stop themselves on the event; a hands-free call loop stops here.
            window.dispatchEvent(new Event(TALK_STOP_EVENT));
            if (phase !== "held" && callLoopState() !== "idle") stopCallLoop();
          }}
        >
          Stop
        </Button>
      ) : null}
    </span>
  );
}

/** PHILO-13-11 (C1) — the screen title bar names the front window. It reads
 * the SAME front window as the blue frame (useFrontWindowId), so the bar
 * never disagrees with the glass. With no window open it names the screen:
 * the Chair (PHILO-17: the one desk). */
function ScreenTitle() {
  const front = useFrontWindowId();
  const open = useAllOpenWindows();
  const name = (front ? open.find((w) => w.id === front)?.label : null) ?? "Desk";
  // W2-BUILDER (atlas 2026-10-27, phone-three-393): at 393 only the front
  // sheet shows. With more than one window open the title is the switcher
  // again (PHILO-13-17 Q2, ratified 2026-10-03): `<window> ▾` lists every
  // open window, so the ones behind are two taps away.
  const compact = useCompactViewport();
  if (compact && open.length > 1 && phoneRing().length > 1) return <ScreenSwitcher name={name} />;
  return (
    <span className="desk-screen-title" data-testid="desk-screen-title">
      <span className="desk-screen-name" title={name}>{name}</span>
    </span>
  );
}

/** The OS clock — every desktop has one. */
function DeskClock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 30_000);
    return () => clearInterval(t);
  }, []);
  const time = now.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });
  const day = now.toLocaleDateString(undefined, {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
  return (
    <span className="desk-clock" aria-label={`${day} ${time}`}>
      <span>{day}</span>
      <strong>{time}</strong>
    </span>
  );
}

/** The HoldSpeak menu's first line: where the desk's data goes, in words. */
export function trustLine(badge: EgressBadge): string {
  if (badge.scope === "local") return "Stays on this Mac";
  const name = badge.text.replace(/^[^\p{L}\p{N}]+/u, "").trim();
  if (badge.scope === "cloud") return name.startsWith("Leaves device · ") ? `Can send to ${name.slice(16)}` : "Can send to an endpoint";
  return /^your network$/i.test(name) ? "Sends to your network" : `Sends to ${name}`;
}

export function DeskChrome({
  showDailyStarts = true,
}: {
  showDailyStarts?: boolean;
}) {
  // HS-111-07 — the ONE key binder rides the chrome (registry-driven).
  useKeymap();
  // HS-100-11 — the daily starts live on the arrival and the dock; the
  // bar keeps system truth only.
  void showDailyStarts;
  const status = useDesk((s) => s.status);
  const error = useDesk((s) => s.error);
  const setup = useDesk((s) => s.setup);
  const loading = useDesk((s) => s.loading);
  const { state: runtimeState } = useRuntimeBus();
  // Subscribed so the mark menu's derived labels/ghosts re-render live.
  useDesk((s) => s.positions);
  useDesk((s) => s.viewMode);
  const [menuOpen, setMenuOpen] = useState(false);
  const settled = useSettleState((s) => s.settled);
  useEffect(() => {
    if (settled) setMenuOpen(false);
  }, [settled]);
  const [menuAt, setMenuAt] = useState<{ x: number; y: number }>({
    x: 0,
    y: 0,
  });
  const markRef = useRef<HTMLButtonElement | null>(null);
  // HS-132-06 — the desk's backstop receipt line. A refused floor write
  // (Create, Seed) names itself in the system bar beside the hub state it
  // belongs with, and yields to any nearer receipt line on screen.
  const { receipt: writeReceipt } = useDeskWriteReceipt({ fallback: true });
  // PHILO-3-01 (the owner's ruling 2026-09-23): at phone width the receipt
  // is its own full-width row in the desk flow (DeskReceiptRow), not a seat
  // in the bar.
  const compact = useCompactViewport();
  usePhoneSwipe(compact);
  const frontWindow = useFrontWindowId();

  const anyLive = Object.values(status).some((v) => v === "live");
  const hubState = error ? "degraded" : anyLive ? "live" : "connecting";
  const hubTitle =
    hubState === "live"
      ? "Hub connected"
      : hubState === "degraded"
        ? error
        : "Connecting";
  const badge = egressBadge(setup);
  // HS-201-01 (counsel fix round, Astra finding 4): who may REACH this hub
  // is its own token beside the egress chip -- never folded into it, and
  // never decided by the destination count.
  const inbound = inboundBadge(setup);

  return (
    <div className="desk-menubar">
      <div className="desk-chrome desk-chrome-tl">
        <div className="desk-menu-wrap">
          <Button
            variant="chrome"
            ref={markRef}
            className="desk-mark"
            aria-expanded={menuOpen}
            aria-haspopup="menu"
            onPointerDown={(e) => {
              if (e.button !== 0) return;
              if (menuOpen) setMenuOpen(false);
              else {
                const r = e.currentTarget.getBoundingClientRect();
                setMenuAt({ x: r.left, y: r.bottom });
                setMenuOpen(true);
              }
            }}
            onClick={(e) => {
              if (e.detail === 0 && !menuOpen) {
                const r = e.currentTarget.getBoundingClientRect();
                setMenuAt({ x: r.left, y: r.bottom });
                setMenuOpen(true);
              }
            }}
            title="HoldSpeak"
          >
            <img src={SYSTEM.menuMark} alt="" width={16} height={16} className="desk-mark-glyph desk-chrome-sprite" draggable={false} />
            HoldSpeak
          </Button>
          {!settled && menuOpen &&
            (() => {
              const ctx: VerbContext = { selectedRef: null };
              const row = (id: string): WorkMenuEntry | null => {
                const v = verbById(id);
                return v
                  ? {
                      type: "item",
                      id: v.id,
                      label: verbLabel(v, ctx),
                      glyph: v.glyph,
                      keycap: v.key,
                      ghost: v.ghost(ctx),
                      onSelect: () => v.run(ctx),
                    }
                  : null;
              };
              const entries: WorkMenuEntry[] = [
                // Window Program W4 (UX-CANON A.9 as amended 2026-10-25): the
                // device and trust word is the HoldSpeak menu's first line,
                // never a chip in the bar; it opens Privacy and trust.
                {
                  type: "item" as const,
                  id: "mark.trust",
                  label: trustLine(badge),
                  onSelect: () => useTrustWindow.getState().setOpen(true),
                },
                { type: "sep" as const, id: "mark-trust-sep" },
                ...MARK_VERBS.map(row),
                ...MARK_APPLICATION_COMMANDS.map(row),
                { type: "sep" as const, id: "mark-sep" },
                row("system.sheet"),
              ].filter((e): e is WorkMenuEntry => e !== null);
              return (
                <WorkMenu
                  className="desk-menu"
                  label="HoldSpeak"
                  anchor="below"
                  x={menuAt.x}
                  y={menuAt.y}
                  entries={entries}
                  onClose={() => setMenuOpen(false)}
                  returnFocus={() => markRef.current?.focus()}
                  menuContext="launcher"
                />
              );
            })()}
        </div>
        <DeskMenuBar />
        <ScreenTitle />
        <span
          className={`desk-hub-dot is-${hubState}`}
          data-scope={badge.scope}
          title={`${hubTitle} · ${badge.title}`}
          aria-label={hubTitle}
          data-testid="chrome-hub-dot"
        />
        {runtimeState === "reconnecting" ? (
          <LampGadget label="RECONNECTING" on tone="warn" />
        ) : runtimeState === "offline" ? (
          <LampGadget label="OFFLINE" on tone="fail" />
        ) : null}
        {/* Window Program W4 (A.9 as amended 2026-10-25): no scope chip at
            rest. The bar keeps the hub's lamp; the device and trust word is
            the HoldSpeak menu's first line (egressBadge() stays its data). */}
        {inbound ? (
          // HS-201-01 (counsel round 2, condition 2): at phone width the
          // words collapse to the lamp itself; the fact stays in the
          // title and the accessible name, exactly as the egress badge
          // keeps its own (chrome-menus.css, the 720px rule).
          <span
            data-testid="chrome-inbound"
            className="desk-chrome-inbound"
            role="img"
            aria-label={inbound.text}
            title={inbound.title}
          >
            <LampGadget label={inbound.text} on tone="warn" />
          </span>
        ) : null}
      </div>

      {writeReceipt && !compact ? (
        <div className="desk-chrome desk-chrome-receipt">{writeReceipt}</div>
      ) : null}

      <div className="desk-chrome desk-chrome-tr">
        <ScreenRecordLamp />
        <MicLamp />
        <AttentionBell />
        <DeskToolShelf />
        {/* Muad'Dib's ruling 2026-10-04: at 393 the clock leaves the bar
            while a window is in front, and the window's name takes its
            width (the bar has no free width: 393 px of parts). */}
        {compact && frontWindow ? null : <DeskClock />}
      </div>
    </div>
  );
}
