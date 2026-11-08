import { Button } from "../../../components/signal/Signal";
import { useEffect, useRef } from "react";
import { useDesk } from "../../store";
import { useSettleState } from "../../settleState";
import { verbById, verbLabel } from "../../verbRegistry";

/** Quiet-mode furniture stays in the existing Dock, beside the same RecordOrb. */
export function RoomActions() {
  const settled = useSettleState((s) => s.settled);
  const recording = useDesk((s) => s.recording);
  const external = useDesk((s) => s.recordingExternal);
  const back = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!settled) return;
    const active = document.activeElement;
    // Don't leave keyboard focus inside chrome that just became hidden.
    // Work already focused inside an editor keeps focus and its selection.
    if (
      active === document.body ||
      active?.closest(".desk-menubar, .desk-dock")
    ) {
      back.current?.focus({ preventScroll: true });
    }
  }, [settled]);
  const ctx = { selectedRef: null };
  const settle = verbById("desk.settle")!;
  const places = verbById("go.change-places")!;
  return (
    <span className="desk-room-actions">
      <Button
        type="button"
        ref={back}
        data-settle-toggle
        aria-pressed={settled}
        title={`${verbLabel(settle, ctx)} · ${settle.key}${settled ? " · Esc" : ""}`}
        onClick={() => settle.run(ctx)}
      >
        <span aria-hidden="true">{settled ? "↩" : settle.glyph}</span>
        {verbLabel(settle, ctx)}
      </Button>
      <Button
        type="button"
        title={`${places.label} · ${places.key}`}
        aria-label="Change places"
        onClick={() => places.run(ctx)}
      >
        <span aria-hidden="true">{places.glyph}</span>
        <span className="desk-room-place-label">Places</span>
      </Button>
      {settled && (
        <span className="desk-settle-capture" role="status">
          {recording === "recording"
            ? external
              ? "Recording elsewhere"
              : "Recording meeting"
            : recording === "busy"
              ? "Updating recording…"
              : "Meeting recorder idle"}
        </span>
      )}
    </span>
  );
}
