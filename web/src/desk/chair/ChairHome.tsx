// HS-170-04 -- ChairHome: THE ARRIVAL.
// The Chair is the screen of objects (PHILO-14 A1) with two windows of its
// own: Needs you (NeedsDrawer) and Capture.
// Betterment daily D5: the Brief and The week windows retired into Today; their
// sections (and the dead Needs-you section) are parked in
// `_parked/ArrivalSections.tsx`.
import "./chair-work.css";
import { useCallback, useEffect, useState } from "react";
import { Chair } from "./Chair";
import { ChairDesk } from "./ChairDesk";
import { Screen } from "../screen";
import { FirstRun } from "../firstrun/FirstRun";
import { useDesk } from "../store";
import { openNewThought } from "../newThought";
import { Button } from "../../components/signal/Signal";
import { MicButton } from "../components/MicButton";
import { onReturnToTask } from "../returnToTask";
import { refreshNeedsYou } from "../needsYou";
import { burstTimer } from "../burstTimer";
import { useRuntimeBus } from "../../runtime/RuntimeBus";
import { needYouWords } from "../surface";
import { useOnCoderFrame } from "../useDeskChangedRefresh";
import { useAgentFlightsLive } from "../agentFlights";

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
    const burst = burstTimer(() => { void refreshNeedsYou(true); }, 300);
    const unsubscribe = subscribeFrames("desk_changed", burst.bump);
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
  const onCoderFrame = useCallback(() => {
    void refreshNeedsYou(true);
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

function CaptureBar() {
  const [dictating, setDictating] = useState(false);

  const handleMicText = useCallback((text: string) => {
    // Voice commands handled by the MicButton pipeline.
  }, []);

  return (
    <footer className="arrival-capture-bar" data-testid="arrival-capture-bar">
      <span className="arrival-capture-talk">
        <MicButton
          onText={handleMicText}
          label="Talk"
          variant="transport"
          onState={(state) => setDictating(state === "listening")}
        />
      </span>
      {/* HS-202-02 job 3 — this verb opened the Speak dictation router.
          It opens a new note in the Thought window now (HS-201-12's
          face), which is what its name says (04-sober-eye.md rank 3). */}
      <Button
        variant="ghost"
        onClick={() => void openNewThought()}
        data-testid="arrival-develop-thought"
      >
        Write a thought
      </Button>
      <Button
        variant="ghost"
        onClick={() => void useDesk.getState().startRecording()}
        data-testid="arrival-record-meeting"
      >
        Record meeting
      </Button>
      <Button
        variant="ghost"
        onClick={() => useDesk.getState().openScheduleCreate()}
        data-testid="arrival-schedule"
      >
        Schedule
      </Button>
    </footer>
  );
}
