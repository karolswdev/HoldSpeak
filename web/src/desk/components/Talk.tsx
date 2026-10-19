/* Betterment capture C8 — ONE Talk rule.
 *
 * Every Talk (the floor, Capture, Speak) works when speech is set up. When it
 * is not, the press opens `Set up speech · <size>` in place, once, and when
 * the model is on the device it listens. No Talk is dimmed in one place and
 * live in another (docs/internal/betterment/capture/DESIGN.md §4 Speak).
 *
 * The speech truth is the one `useSpeechSetup` read (GET /api/setup/local-ai).
 * While that read is out, or when it cannot be read, Talk is the plain
 * MicButton, as before: nothing is claimed that was not read. */
import { useEffect, useRef, useState, type ComponentProps, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { SYSTEM } from "../systemSprites";
import { MicButton } from "./MicButton";
import { SpeechSetup, useSpeechSetup, type SpeechSetupState } from "../firstrun/SpeechSetup";
import "./talk.css";

type MicProps = ComponentProps<typeof MicButton>;

/** The Talk key while speech is not set up: live, the same plate as Talk. */
function TalkKey({ open, onPress, testId }: { open: boolean; onPress: () => void; testId: string }) {
  return (
    <Button
      variant="chrome"
      className="desk-mic gadget-transport-key is-idle"
      aria-label="Talk"
      aria-expanded={open}
      data-testid={`${testId}-key`}
      onClick={(event) => {
        event.preventDefault();
        event.stopPropagation();
        onPress();
      }}
    >
      <span className="gadget-transport-glyph" aria-hidden="true">
        <img src={SYSTEM.micGlyph} alt="" width={16} height={16} className="desk-chrome-sprite" draggable={false} />
      </span>
      <span className="gadget-transport-word">Talk</span>
    </Button>
  );
}

/** The rule as two parts, so a face can seat the setup row where it fits
 *  (Speak puts it under its transport row). `speech` lets a face that
 *  already reads speech share its read. */
export function useTalk(
  mic: MicProps,
  {
    speech: shared,
    testId = "talk-speech-setup",
    primary = false,
    onReady,
  }: { speech?: SpeechSetupState; testId?: string; primary?: boolean; onReady?: () => void } = {},
): { talkKey: ReactNode; setupRow: ReactNode } {
  const own = useSpeechSetup();
  const speech = shared ?? own;
  const [asked, setAsked] = useState(false);
  const [start, setStart] = useState(0);
  const wasMissing = useRef(false);
  const readyRef = useRef(onReady);
  readyRef.current = onReady;
  useEffect(() => {
    if (speech.notSetUp) wasMissing.current = true;
    else if (speech.ready && wasMissing.current) {
      // The model is here now: the host reads its own readiness again.
      wasMissing.current = false;
      readyRef.current?.();
    }
  }, [speech.notSetUp, speech.ready]);
  // The model landed after the press: listen now (the press asked to talk).
  useEffect(() => {
    if (asked && speech.ready) {
      setAsked(false);
      setStart((n) => n + 1);
    }
  }, [asked, speech.ready]);

  // While the speech read is out the face is still reading: it says so
  // (aria-busy), so nothing reads it as settled before the answer lands and
  // moves what is under it (the desk sweep's still fence; SpeechSetup's rule).
  const reading =
    speech.ai.read.kind === "loading" ? <span hidden aria-busy="true" data-testid={`${testId}-reading`} /> : null;
  if (speech.notSetUp) {
    return {
      talkKey: <TalkKey open={asked} onPress={() => setAsked((v) => !v)} testId={testId} />,
      setupRow: asked ? (
        <span className="talk-setup" data-testid={`${testId}-place`}>
          <SpeechSetup setup={speech} bare primary={primary} testId={testId} />
        </span>
      ) : null,
    };
  }
  return {
    talkKey: (
      <>
        <MicButton {...mic} variant="transport" label={mic.label ?? "Talk"} startSignal={start || mic.startSignal} />
        {reading}
      </>
    ),
    setupRow: null,
  };
}

/** Talk with the rule: the key, then (after a press while speech is not set
 *  up) the setup row beside it. */
export function Talk(props: MicProps & { setupTestId?: string }) {
  const { setupTestId, ...mic } = props;
  const { talkKey, setupRow } = useTalk(mic, { testId: setupTestId });
  return (
    <>
      {talkKey}
      {setupRow}
    </>
  );
}
