// The Desk's floating system chrome. The room menu stays compact; the opposite
// cluster exposes the three daily starts, one searchable tool shelf, layout,
// and refresh. A fresh Desk renders the same starts centrally instead.
// HS-111-07 — the mark menu DERIVES from the one verb registry (its
// hardcoded verb list was parallel list #2) and rides the WorkMenu
// portal, so it draws over windows like every chrome transient.
import { useEffect, useState, useRef } from "react";
import { useTrustWindow } from "./TrustWindow";
import { useDesk } from "../store";
import { WorkMenu, type WorkMenuEntry } from "./DeskMenu";
import { verbById, verbLabel, type VerbContext } from "../verbRegistry";
import { useKeymap } from "../keymap";
import { egressBadge } from "../setup";
import { EgressChip, LampGadget } from "../surface/gadgets";
import { subscribeMicPhase, type MicPhase } from "../../lib/micSession";
import { DeskToolShelf } from "./DeskToolShelf";
import { DeskMenuBar } from "./DeskMenuBar";
import { useLaunchers } from "./DeskWindow";
import { SYSTEM } from "../systemSprites";

/** The mark menu's registry rows: the floor verbs, then the four
 * applications (the same go.* truth the Go menu and the dock speak). */
const MARK_VERBS = ["desk.toggle-view", "desk.arrange", "desk.refresh"];
const MARK_APPS = [
  "go.dictate",
  "go.review-meetings",
  "go.inspect-personas-and-coders",
  "go.configure-settings",
];

/** HS-100-11 — the attention bell: the approve-queue's badge lives in
 * the system bar, not the dock (the dock carries the applications). */
function AttentionBell() {
  const launchers = useLaunchers();
  const attention = launchers.find((l) => l.id === "attention");
  if (!attention) return null;
  return (
    <button
      type="button"
      className={`desk-bell${attention.open ? " is-open" : ""}`}
      aria-label={
        attention.badge
          ? `Desk memory: ${attention.badge} need attention`
          : "Desk memory"
      }
      title="Desk memory"
      onClick={() => attention.activate()}
    >
      {/* HS-111-09 — 16px source renders at 16 CSS px (integer-true). */}
      <img src={SYSTEM.menuBell} alt="" width={16} height={16} className="desk-chrome-sprite" draggable={false} />
      {attention.badge ? <strong>{attention.badge}</strong> : null}
    </button>
  );
}

/* HS-112-06 — the mic lamp: while the Desk holds a microphone grant the
   chrome says so, in the session's own words, from every room. It is
   absent only when the device is released (tracks stopped) — so its
   presence, not a colour, is the honest signal that audio is live. */
const MIC_LAMP_FACT: Record<Exclude<MicPhase, "closed">, string> = {
  suspended: "Mic idle",
  open: "Mic open",
  segmenting: "Mic speech",
  held: "Mic held",
};

function MicLamp() {
  const [phase, setPhase] = useState<MicPhase>("closed");
  useEffect(() => subscribeMicPhase(setPhase), []);
  if (phase === "closed") return null;
  return (
    <span className="desk-mic-lamp" role="status">
      <LampGadget
        label={MIC_LAMP_FACT[phase]}
        on={phase !== "suspended"}
        tone={phase === "suspended" ? "warn" : "ok"}
      />
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
  // Subscribed so the mark menu's derived labels/ghosts re-render live.
  useDesk((s) => s.positions);
  useDesk((s) => s.viewMode);
  const [menuOpen, setMenuOpen] = useState(false);
  const [menuAt, setMenuAt] = useState<{ x: number; y: number }>({
    x: 0,
    y: 0,
  });
  const markRef = useRef<HTMLButtonElement | null>(null);

  const anyLive = Object.values(status).some((v) => v === "live");
  const hubState = error ? "degraded" : anyLive ? "live" : "connecting";
  const hubTitle =
    hubState === "live"
      ? "Hub connected"
      : hubState === "degraded"
        ? error
        : "Connecting";
  const badge = egressBadge(setup);

  return (
    <div className="desk-menubar">
      <div className="desk-chrome desk-chrome-tl">
        <div className="desk-menu-wrap">
          <button
            type="button"
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
          </button>
          {menuOpen &&
            (() => {
              const ctx: VerbContext = { selectedRef: null };
              const row = (id: string): WorkMenuEntry | null => {
                const v = verbById(id);
                return v
                  ? {
                      type: "item",
                      id: v.id,
                      label: verbLabel(v, ctx),
                      keycap: v.key,
                      ghost: v.ghost(ctx),
                      onSelect: () => v.run(ctx),
                    }
                  : null;
              };
              const entries: WorkMenuEntry[] = [
                ...MARK_VERBS.map(row),
                { type: "sep" as const, id: "mark-sep" },
                ...MARK_APPS.map(row),
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
                />
              );
            })()}
        </div>
        <DeskMenuBar />
        <span
          className={`desk-hub-dot is-${hubState}`}
          title={hubTitle}
          aria-label={hubTitle}
        />
        {/* HS-111-07 — ONE badge species: the chrome badge is the same
            EgressChip the gadget rows wear, with the trust click-through
            (egressBadge() stays the data source). */}
        <EgressChip
          label={badge.text}
          title={badge.title}
          scope={badge.scope}
          className={`egress-badge is-${badge.scope} egress-badge-button`}
          ariaLabel={`Privacy and trust: ${badge.text}`}
          onClick={() => useTrustWindow.getState().setOpen(true)}
        />
      </div>

      <div className="desk-chrome desk-chrome-tr">
        <MicLamp />
        <AttentionBell />
        <DeskToolShelf />
        <DeskClock />
      </div>
    </div>
  );
}
