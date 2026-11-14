import type { ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { StringGadget, DotWord, InspectorForm, PreferenceWell, PaneActions, PaneNotice, ActionNotice } from "../../desk/surface";
import { SpeechSetup, type SpeechSetupState } from "../../desk/firstrun/SpeechSetup";
import { LevelBars, type MicCheck } from "./LiveLevel";
type Tone = "ok" | "warn" | "fail" | "info" | "idle";
/** The hub's mic-check answer → the Microphone row's word, its dot, the
 *  level (only when it listened), and the one verb. */
function micRow(mic: MicCheck | null): {
  state: { tone: Tone; word: string; title?: string } | null;
  level: number | null;
  verb: "check" | "allow" | null;
} {
  if (!mic) return { state: null, level: null, verb: null };
  const level = typeof mic.level === "number" ? mic.level : null;
  switch (mic.state) {
    case "hearing":
      return { state: { tone: "ok", word: "Hearing" }, level, verb: null };
    case "quiet":
      return { state: { tone: "idle", word: "Quiet", title: "The microphone sends no sound. Speak, then check again." }, level, verb: "check" };
    case "not_allowed":
      return { state: { tone: "fail", word: "Microphone not allowed", title: "macOS does not let HoldSpeak use the microphone." }, level: null, verb: "allow" };
    case "not_asked":
      return { state: { tone: "info", word: "Asks at start", title: "macOS asks for the microphone when the meeting starts." }, level: null, verb: null };
    case "in_use":
      return { state: { tone: "info", word: "In use" }, level: null, verb: null };
    case "failed":
      return { state: { tone: "fail", word: "No answer", title: mic.error || undefined }, level: null, verb: "check" };
    default:
      // `off` (a rig hub) and `unknown` (a grant that could not be read):
      // nothing was heard, so nothing is claimed.
      return { state: { tone: "idle", word: "Not checked" }, level: null, verb: null };
  }
}

export function LiveReady({
  speech,
  microphone,
  name,
  onName,
  mic = null,
  checkingMic = false,
  onCheckMic,
}: {
  microphone?: ReactNode;
  settings: Record<string, unknown>;
  hub: Record<string, unknown>;
  speech: SpeechSetupState;
  name: string;
  onName(next: string): void;
  mic?: MicCheck | null;
  checkingMic?: boolean;
  onCheckMic?(): void;
  start?: ReactNode;
}) {
  const face = micRow(mic);
  return (
    <PreferenceWell><PaneNotice>
      <InspectorForm
        fit="rows"
        testId="live-ready"
        rows={[
          {
            label: "Meeting name",
            control: (
              <StringGadget label="Meeting name" placeholder="Name this meeting" value={name} onChange={onName} />
            ),
          },
          {
            label: "Microphone",
            control: (
              mic?.state === "not_allowed" && !checkingMic ? (
                <div data-testid="live-ready-mic">
                  {microphone}
                  <ActionNotice tone="danger" action={mic.settings_url ? {
                    label: "Allow Microphone…",
                    onClick: () => window.open(String(mic.settings_url), "_self", "noopener"),
                  } : undefined}>
                    <span data-testid="live-ready-mic-state" data-tone="fail">Microphone not allowed</span>
                  </ActionNotice>
                </div>
              ) : <PaneActions data-testid="live-ready-mic" aria-busy={checkingMic}>
                {microphone}
                {checkingMic ? (
                  <DotWord tone="info">Checking</DotWord>
                ) : face.state ? (
                  <DotWord tone={face.state.tone} data-testid="live-ready-mic-state">
                    {face.state.word}
                  </DotWord>
                ) : null}
                {face.level !== null ? <LevelBars level={face.level} label="Microphone level" /> : null}
                {face.verb === "check" ? (
                  <Button
                    dense
                    variant="secondary"
                    data-testid="live-mic-check"
                    loading={checkingMic}
                    onClick={onCheckMic}
                  >
                    Retry
                  </Button>
                ) : null}
              </PaneActions>
            ),
          },
          {
            label: "Speech",
            control: (
              <span data-testid="live-ready-transcript" aria-busy={speech.ai.read.kind === "loading" || undefined}>
                {speech.ai.read.kind === "loading" ? (
                  <DotWord tone="info">Reading speech…</DotWord>
                ) : speech.notSetUp ? (
                  <SpeechSetup setup={speech} primary={false} toolbar testId="live-speech-setup" />
                ) : speech.ready ? (
                  <DotWord tone="info">Speech ready</DotWord>
                ) : (
                  <DotWord tone="warn">Speech not read</DotWord>
                )}
              </span>
            ),
          },
        ]}
      />
    </PaneNotice></PreferenceWell>
  );
}
