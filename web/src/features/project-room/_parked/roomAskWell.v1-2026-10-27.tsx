// PARKED (Window Program W2-ASKWELLS, 2026-10-27): the Room's own Ask well —
// its StringGadget well, the Result choice, the engine chip ("No engine for
// answers" + Choose) and the hidden Submit. The Room now composes the Ask
// window's composer row (web/src/desk/components/askFace.tsx AskComposer),
// scoped to the project. Code as it stood in ProjectRoomCore.tsx; nothing
// imports it.
/* eslint-disable */
// @ts-nocheck
/** The Room's ask (Phase 16: the kit's AskWell: the sunken paper well with
 *  the mic on its right edge, the model's egress chip beside it). The
 *  Room window on the desk (the Project's drawer) draws the same well. */
export function RoomAskWell({
  ask,
  projectId,
  onOpenRef,
  onPrepare,
}: {
  ask: RoomAsk;
  projectId: string;
  onOpenRef: (ref: string) => void;
  /** HS-200-11: `Result → Preparation brief` hands the words to the Prepare
   *  posture; nothing here requires a calendar (AC1). */
  onPrepare?: (purpose: string) => void;
}) {
  const { prompt, setPrompt, inputRef } = ask;
  const modelLabel = useModelLabel(projectId);

  return (
    <div className="room-ask-section" data-testid="room-ask-well">
      <div className="room-ask-well" data-testid="room-ask-input-well">
        {/* Phase 16 (the interior kit, §11 "AskWell"): the library string
            well (sunken paper, the mic on its right edge) replaces the raw
            input HS-170-04 left for a redesign. */}
        <StringGadget
          label="Ask this project"
          value={prompt}
          onChange={setPrompt}
          placeholder="Ask this project…"
          micLabel="Speak to ask this project"
          micDraftScope={`project-ask-${projectId}`}
          inputRef={inputRef}
          inputProps={{ className: "room-ask-input" }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void ask.ask();
            }
          }}
        />
        {onPrepare ? (
          <span className="room-ask-result" data-testid="room-ask-result">
            <CycleGadget
              label="Result"
              value="answer"
              options={RESULT_OPTIONS}
              onChange={(next) => { if (next === "brief") onPrepare(prompt); }}
            />
          </span>
        ) : null}
        {/* NOT SET = the plain fact and Choose; assigned = the engine's name. */}
        {modelLabel.host === "NOT SET" ? (
          <span className="room-ask-model-chip">
            {/* PHILO-17 U31: the plain fact, not MODEL · NOT SET. */}
            <DotWord tone="warn" data-testid="room-ask-no-engine">No engine for answers</DotWord>
            <Button
              dense
              variant="ghost"
              onClick={() => {
                // The verb he leaves is `Choose`, but `Choose` is GONE once a
                // model is set — so the place to come back to is the well he
                // was typing in, with his words still in it (design D2(a)).
                rememberTaskFocus(inputRef.current);
                openSurfaceOr("configure-runs-on", "/settings", "models");
              }}
            >
              Choose
            </Button>
          </span>
        ) : (
          <span className="room-ask-model-chip room-ask-engine" data-testid="room-ask-engine">{modelLabel.host}</span>
        )}
        {/* Condition 1: no raw <button>; visually-hidden submit for a11y */}
        <Button dense variant="ghost" className="room-ask-submit-hidden" aria-label="Submit" onClick={() => void ask.ask()} tabIndex={-1}>
          Submit
        </Button>
      </div>
    </div>
  );
}
