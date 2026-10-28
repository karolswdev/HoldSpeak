// HS-170-04 -- ChairHome: THE ARRIVAL.
// The Chair is the screen of objects (PHILO-14 A1) with two windows of its
// own: Needs you (NeedsDrawer) and Capture.
// Betterment daily D5: the Brief and The week windows retired into Today; their
// sections (and the dead Needs-you section) are parked in
// `_parked/ArrivalSections.tsx`.
import "./chair-work.css";
import { useCallback, useEffect, useRef, useState } from "react";
import { Chair } from "./Chair";
import { ChairDesk } from "./ChairDesk";
import { Screen } from "../screen";
import { FirstRun } from "../firstrun/FirstRun";
import { useDesk } from "../store";
import { openNewThought } from "../newThought";
import { Button } from "../../components/signal/Signal";
import { useTalk } from "../components/Talk";
import { PadGadget } from "../surface/gadgets";
import { ToolGlyph, Toolbar } from "../surface/kit";
import { useCompactViewport } from "../useCompactViewport";
import { workBand } from "../components/window/windowGeometry";
import type { PanelRect } from "../store/types";
import { onReturnToTask } from "../returnToTask";
import { refreshNeedsYou } from "../needsYou";
import { burstTimer } from "../burstTimer";
import { onlyWindowChanges } from "../components/window/dockState";
import { useRuntimeBus } from "../../runtime/RuntimeBus";
import { needYouWords } from "../surface";
import { useOnCoderFrame } from "../useDeskChangedRefresh";
import { useAgentFlightsLive } from "../agentFlights";
import { ComingUp } from "../../pages/cores/history/ComingUp";

/** Headline for the arrival: zero = "Nothing needs you" (UX-CANON A8).
 *  HS-200-07 (C4): the all-clear line is spoken ONLY over complete
 *  coverage; an empty PARTIAL result names the coverage instead.
 *  HS-200-15 (verdict): the display line is the TRUE total; the Project
 *  clause is withheld when there is exactly one Project (`3 need you`). */
export function headlineFor(
  count: number,
  projectCount: number,
  complete = true,
  pending = 0,
): string {
  // HS-201-01: `pending` is what needs the owner but is not an attention
  // row -- the meeting-path blocker and every FAILED meeting on the face.
  // The all-clear is never spoken over one (audits/face-walk-opus.md
  // defect 8: `Nothing needs you` above a FAILED meeting).
  // HS-201-11: the number the head speaks is ONE total -- the attention
  // list plus what asks beside it (the SETUP row, a FAILED meeting). The
  // rehearsal read `1 need you` while the attention list and the blocker
  // were counted separately (audits/rehearsal-07-opus.md, step 1). The
  // calendar row is an OFFER and is counted by neither (owner's ruling).
  const total = count + Math.max(0, pending);
  if (total <= 0) {
    return complete ? "Nothing needs you" : "Coverage incomplete";
  }
  const n = String(total);
  // The Project clause speaks only for the attention list, which is what
  // the Projects are counted over.
  if (count > 0 && projectCount > 1) {
    return needYouWords(n) + " across " + String(projectCount) + " projects";
  }
  // PHILO-15-09 (B11): `1 needs you`.
  return needYouWords(n);
}

// ── ChairHome ──────────────────────────────────────────────────────

export function ChairHome({ arrivalRequired = false }: { arrivalRequired?: boolean }) {
  if (arrivalRequired) {
    return (
      <main className="chair chair-first-value" data-testid="chair-first-value">
        {/* First run C1 "Heard first" (owner ratified 2026-10-05). */}
        <FirstRun />
      </main>
    );
  }

  return (
    <Chair>
      <Arrival />
    </Chair>
  );
}

// ── The Arrival face ───────────────────────────────────────────────

function Arrival() {
  // ONE Needs-you membership for the whole Desk (PHILO-13-03): the Chair
  // keeps it fresh. It re-reads when the owner comes back from a repair
  // (`holdspeak:settings-updated`), on the hub's `desk_changed` frame
  // (debounced) and when the window takes focus again.
  const readAssignments = useCallback(() => refreshNeedsYou(false), []);
  useEffect(() => onReturnToTask(() => { void readAssignments(); }), [readAssignments]);
  const { subscribe: subscribeFrames } = useRuntimeBus();
  useEffect(() => {
    // Never a forced rebuild: a hub write that changes the answer marks the
    // hub's cache dirty. A frame of window changes only reads nothing.
    const burst = burstTimer(() => { void refreshNeedsYou(false); }, 300);
    const unsubscribe = subscribeFrames("desk_changed", (frame) => {
      if (!onlyWindowChanges(frame.data)) burst.bump();
    });
    const onFocus = () => { void readAssignments(); };
    window.addEventListener("focus", onFocus);
    return () => {
      burst.cancel();
      unsubscribe();
      window.removeEventListener("focus", onFocus);
    };
  }, [subscribeFrames, readAssignments]);

  // Conductor F2 (K4c): the agents store stays live here (the screen and the
  // Conductor drawer read it). K3: an agent that begins or stops waiting
  // moves Needs you now (the `scope:"coder"` frame).
  useAgentFlightsLive();
  // The agent rows are read live on every needs-you read (not cached).
  const onCoderFrame = useCallback(() => {
    void refreshNeedsYou(false);
  }, []);
  useOnCoderFrame(onCoderFrame);

  return (
    <ChairDesk
      screen={<Screen />}
      needs={null}
      capture={
        <>
          {/* ── Capture Bar ── */}
          <div
            data-testid="arrival-aftercare-slot"
            data-aftercare-slot="before-capture"
          />
          <CaptureBar />
          {/* Capture C7: Schedule is replaced by the next two Coming-up rows
              (the same list as Meetings ▸ Record and Today). */}
          <ComingUp limit={2} data-testid="arrival-coming-up" emptyLine="Nothing is coming up" />
        </>
      }
    />
  );
}

/** How long the agent has waited: `JUST NOW`, `<n> MIN`, `<n> H`. */
export function coderAgeWord(item: { since?: string | null; waitStartedAt?: string | null; ageSeconds?: number | null }, now: Date): string {
  const stamp = Date.parse(String(item.waitStartedAt || item.since || ""));
  const seconds = Number.isFinite(stamp)
    ? Math.max(0, Math.floor((now.getTime() - stamp) / 1000))
    : Math.max(0, Number(item.ageSeconds ?? 0));
  if (seconds < 60) return "JUST NOW";
  if (seconds < 3600) return `${Math.floor(seconds / 60)} MIN`;
  return `${Math.floor(seconds / 3600)} H`;
}

// ── Capture Bar ────────────────────────────────────────────────────
// Betterment capture C8: three large verbs from the top — Talk, New note,
// Record. Talk keeps the one Talk rule (desk/components/Talk.tsx). New note
// unfolds an empty note under the verbs and makes the record on the first
// character, never on the press: a press with no typing leaves no record.

function CaptureBar() {
  const [dictating, setDictating] = useState(false);
  const [noting, setNoting] = useState(false);

  const handleMicText = useCallback((text: string) => {
    // Capture has no focused field. Give spoken words the same home as the
    // New note verb, creating the note only when words arrive.
    void openNewThought(text);
  }, []);

  const { talkKey, setupRow } = useTalk(
    { onText: handleMicText, label: "Talk", onState: (state) => setDictating(state === "listening") },
    { testId: "arrival-talk-setup" },
  );
  useCaptureRoom(Boolean(setupRow) || noting);

  return (
    <footer className="arrival-capture-bar" data-testid="arrival-capture-bar">
      {/* Window grammar (2026-10-25): the three verbs are the window's
          toolbar — Talk the one primary, New note and Record quiet. */}
      <Toolbar label="Capture" className="arrival-capture-toolbar">
        <span className="arrival-capture-talk arrival-capture-big">{talkKey}</span>
        <Button
          variant="secondary"
          className="arrival-capture-big"
          aria-expanded={noting}
          onClick={() => setNoting((open) => !open)}
          data-testid="arrival-develop-thought"
        >
          {/* Betterment Q8 (one note): one kind, one name. */}
          <ToolGlyph kind="note" />
          New note
        </Button>
        <Button
          variant="secondary"
          className="arrival-capture-big"
          onClick={() => void useDesk.getState().startRecording()}
          data-testid="arrival-record-meeting"
        >
          <ToolGlyph kind="record" />
          Record
        </Button>
      </Toolbar>
      {setupRow ? <div className="arrival-capture-place">{setupRow}</div> : null}
      {noting ? <FirstCharacterNote onDone={() => setNoting(false)} /> : null}
    </footer>
  );
}

/** An empty note under the verbs. Nothing is written until the first
 *  character: then the note is made (or the empty one is used again) and its
 *  window opens with these words in it (`openNewThought(firstWords)`). */
function FirstCharacterNote({ onDone }: { onDone: () => void }) {
  const [words, setWords] = useState("");
  return (
    <div
      className="arrival-capture-place arrival-capture-note"
      data-testid="arrival-new-note"
      onKeyDown={(event) => {
        if (event.key === "Escape") onDone();
      }}
    >
      <PadGadget
        label="New note"
        placeholder="New note"
        value={words}
        rows={3}
        autoFocus
        onChange={(next) => {
          setWords(next);
          if (!next) return;
          onDone();
          void openNewThought(next);
        }}
      />
    </div>
  );
}

/** While a Capture verb's place is open (the speech setup, the new note),
 *  Capture grows UP to hold it, its foot fixed, and its seat comes back when
 *  the place closes (the rule of the parked aftercare card,
 *  `_parked/aftercareCaptureEffects.ts`). A Capture he moved or sized keeps
 *  his geometry; at 393 Capture already takes the work area. The rect is
 *  this view's only (never saved). With no rect yet, chair.css grows the CSS
 *  seat the same way (`.arrival-capture-place`). */
const CAPTURE_ROOM_H = 212;

function useCaptureRoom(open: boolean): void {
  const compact = useCompactViewport();
  const rect = useDesk((s) => s.panelRects["chair:capture"]);
  const arranged = useDesk((s) => s.panelSaved.includes("chair:capture"));
  const seat = useRef<PanelRect | null>(null);
  useEffect(() => {
    if (compact || arranged) {
      seat.current = null;
      return;
    }
    const desk = useDesk.getState();
    if (open && rect && !seat.current) {
      const foot = rect.y + rect.h;
      const top = Math.max(workBand().top, foot - CAPTURE_ROOM_H);
      if (top >= rect.y) return;
      seat.current = rect;
      desk.setPanelRect("chair:capture", { ...rect, y: top, h: foot - top });
    } else if (!open && seat.current) {
      const back = seat.current;
      seat.current = null;
      if (rect) desk.setPanelRect("chair:capture", back);
    }
  }, [compact, arranged, open, rect]);
}
