import type { ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { StringGadget, DotWord } from "../../desk/surface";
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
      return { state: { tone: "fail", word: "Not allowed", title: "macOS does not let HoldSpeak use the microphone." }, level: null, verb: "allow" };
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


export function LiveReady({ settings, speech, name, onName, mic = null, checkingMic = false, onCheckMic, start }: {
  settings: Record<string, unknown>; hub: Record<string, unknown>; speech: SpeechSetupState;
  name: string; onName(next: string): void; mic?: MicCheck | null; checkingMic?: boolean;
  onCheckMic?(): void; start?: ReactNode;
}) {
  const face = micRow(mic);
  const device = settings.meeting as Record<string, unknown> | undefined;
  return <div className="live-ready" data-testid="live-ready">
    <StringGadget label="Meeting name" placeholder="Name this meeting" value={name} onChange={onName} />
    <section className="live-ready-plate" aria-label="Microphone" data-testid="live-ready-mic">
      <div className="live-ready-head"><strong>Microphone</strong>
        {face.state ? <DotWord tone={face.state.tone} data-testid="live-ready-mic-state">{face.state.word}</DotWord> : null}
        {face.level !== null ? <LevelBars level={face.level} label="Microphone level" /> : null}
      </div>
      <span className="live-ready-fact">{String(device?.mic_device || "System default")}</span>
      <div className="live-ready-actions">
        {face.verb === "allow" && mic?.settings_url ? <Button dense variant="secondary" data-testid="live-mic-allow"
          title="Open Microphone in System Settings" onClick={() => window.open(String(mic.settings_url), "_self", "noopener")}>Allow…</Button>
          : face.verb === "check" ? <Button dense variant="secondary" data-testid="live-mic-check" loading={checkingMic} onClick={onCheckMic}>Retry</Button>
          : start}
      </div>
    </section>
    {speech.notSetUp ? <div data-testid="live-ready-transcript"><SpeechSetup setup={speech} primary={false} toolbar testId="live-speech-setup" /></div> : null}
  </div>;
}
