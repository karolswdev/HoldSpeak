/* W2-LIVE-2 (2026-10-27; canvas betterment/canvases/live-direction-2026-10-27.html,
 * direction A, "Before"): the ready sheet. Before a meeting the Live window
 * says what will hear him and what will write the result, each as an object
 * row (glyph · name · the quiet fact · a dot and a word · the one verb that
 * fixes it). The meeting's name is a quiet editable line; Start meeting (the
 * toolbar) is the one primary.
 *
 * Facts, all read from the hub: the devices from GET /api/settings
 * (`meeting.mic_device`, `meeting.system_audio_device`; empty = the system
 * default / Auto), the speech model from the speech setup read
 * (`/api/setup/local-ai` `speech`), and the summary engine from
 * /api/settings/hub (`meetings.engine`, `engineSet`, `summariesOff`). The hub
 * sends no microphone level before a meeting, so the microphone row says
 * Ready (the canvas: "draw Ready until it does"). */
import type { ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { openSurfaceOr } from "../../desk/shell";
import { DotWord, ToolGlyph } from "../../desk/surface/kit";
import { StringGadget } from "../../desk/surface/gadgets";
import { presentValue } from "../../desk/surface/format";
import { SpeechSetup, type SpeechSetupState } from "../../desk/firstrun/SpeechSetup";

type Tone = "ok" | "warn" | "fail" | "info" | "idle";

function Glyph({ kind }: { kind: "mic" | "speaker" | "transcript" | "summary" }) {
  const pen = { stroke: "currentColor", strokeWidth: 1.5, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, fill: "none" };
  return (
    <svg className="live-ready-glyph" width={18} height={18} viewBox="0 0 16 16" aria-hidden="true">
      {kind === "mic" ? (
        <>
          <rect x="5.75" y="1.75" width="4.5" height="8" rx="2.25" {...pen} />
          <path d="M3.5 7.5a4.5 4.5 0 0 0 9 0M8 12v2.25" {...pen} />
        </>
      ) : kind === "speaker" ? (
        <>
          <path d="M2.5 6h2.25L8 3.25v9.5L4.75 10H2.5z" {...pen} />
          <path d="M10.5 5.75a3 3 0 0 1 0 4.5M12.25 4a5.5 5.5 0 0 1 0 8" {...pen} />
        </>
      ) : (
        <>
          <path d="M4 1.75h5.5L12.5 4.75v9.5H4z" {...pen} />
          <path d={kind === "transcript" ? "M6 7.5h4.5M6 10h4.5M6 12.5h3" : "M6 7.5h4.5M6 10h2.5"} {...pen} />
        </>
      )}
    </svg>
  );
}

function ReadyRow({ glyph, name, fact, state, verb, testId }: {
  glyph: "mic" | "speaker" | "transcript" | "summary";
  name: string;
  fact?: string;
  state?: { tone: Tone; word: string } | null;
  verb?: ReactNode;
  testId: string;
}) {
  return (
    <li className="live-ready-row" data-testid={testId}>
      <Glyph kind={glyph} />
      <span className="live-ready-name">{name}</span>
      <span className="live-ready-fact">{fact}</span>
      <span className="live-ready-state">
        {state ? <DotWord tone={state.tone} data-testid={`${testId}-state`}>{state.word}</DotWord> : null}
      </span>
      <span className="live-ready-verb">{verb}</span>
    </li>
  );
}

export function LiveReady({ settings, hub, speech, name, onName }: {
  /** GET /api/settings */
  settings: Record<string, unknown>;
  /** GET /api/settings/hub */
  hub: Record<string, unknown>;
  speech: SpeechSetupState;
  name: string;
  onName(next: string): void;
}) {
  const meeting = (settings.meeting ?? null) as Record<string, unknown> | null;
  const read = meeting !== null;
  const mic = presentValue(meeting?.mic_device) || "System default";
  const system = presentValue(meeting?.system_audio_device) || "Auto";

  const model = presentValue(speech.status?.speech?.model);
  const transcriptFact = model ? `Whisper ${model}, on this Mac` : "On this Mac";
  const transcriptState = speech.ready
    ? { tone: "ok" as const, word: "Ready" }
    : speech.notSetUp
      ? { tone: "warn" as const, word: "Not set up" }
      : null;

  const meetings = (hub.meetings ?? null) as Record<string, unknown> | null;
  const engine = presentValue(meetings?.engine);
  const summaryOff = meetings?.summariesOff === true;
  const summaryMissing = !summaryOff && meetings?.engineSet === false;
  const summaryFact = summaryOff ? "Off" : engine ? `${engine}, after the meeting` : undefined;
  const summaryState = summaryOff
    ? { tone: "idle" as const, word: "Off" }
    : summaryMissing
      ? { tone: "warn" as const, word: "No engine" }
      : engine
        ? { tone: "ok" as const, word: "Ready" }
        : null;

  return (
    <div className="live-ready" data-testid="live-ready">
      <div className="live-ready-name-line">
        <StringGadget label="Meeting name" placeholder="Name this meeting" value={name} onChange={onName} />
      </div>
      <h3 className="live-ready-cap">It will hear</h3>
      <ul className="live-ready-rows" aria-label="It will hear">
        <ReadyRow glyph="mic" name="Microphone" fact={read ? mic : undefined}
          state={read ? { tone: "ok", word: "Ready" } : null} testId="live-ready-mic" />
        <ReadyRow glyph="speaker" name="System audio" fact={read ? system : undefined}
          state={read ? { tone: "ok", word: "Ready" } : null} testId="live-ready-system" />
      </ul>
      <h3 className="live-ready-cap">It will write</h3>
      <ul className="live-ready-rows" aria-label="It will write">
        <ReadyRow glyph="transcript" name="Transcript" fact={transcriptFact} state={transcriptState}
          verb={<SpeechSetup setup={speech} primary={false} toolbar testId="live-speech-setup" />}
          testId="live-ready-transcript" />
        <ReadyRow glyph="summary" name="Summary" fact={summaryFact} state={summaryState}
          verb={summaryMissing ? (
            <Button dense variant="secondary" data-testid="live-choose-engine"
              onClick={() => openSurfaceOr("open-concierge", "/models", "meetings")}>
              <ToolGlyph kind="engine" />
              Choose engine
            </Button>
          ) : null}
          testId="live-ready-summary" />
      </ul>
    </div>
  );
}
