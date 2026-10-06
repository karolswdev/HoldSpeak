/* First run — "C1 · Heard first" (owner ratified 2026-10-05, canvas
 * FzBum28aTJQbsqwBvLuP16 v2). Three cards on one screen: Local AI · You ·
 * First words. One press downloads every local model; First words lights
 * when the speech model lands, so he can speak while the chat model still
 * downloads; his sentence comes back at the display step.
 *
 * Option A "One screen" (owner ratified 2026-10-05, canvas
 * YDTpkaJqFs3hyrZ4g581Mx §1): Calendar and Connections are two more cards
 * on the same screen. One card at a time is lit (the next press). When
 * every step is done, Ready goes to the top: "Ready, <his name>", the
 * success chips, and three verbs; every card stays, selected.
 *
 * Skip (owner ruling 2026-10-06): Calendar and Connections each have one
 * Skip. A skipped step counts as done for Ready; Settings sets it up later. */
import { useCallback, useState } from "react";
import { Button } from "../../components/signal/Signal";
import {
  EgressChip,
  HeardQuote,
  LampGadget,
  LedMeter,
  ProgressPlan,
  Receipt,
  StateChip,
  StringGadget,
  countToken,
  SurfaceLedgerRow,
} from "../surface";
import { apiFetch } from "../../lib/api";
import { DICTATION_FAILURES, needsMicrophoneDoctor, type DictationFailure } from "../../lib/dictationRecovery";
import { openSurfaceOr } from "../shell";
import { useDesk } from "../store";
import {
  formatBytes,
  groupsOf,
  missingBytes,
  planSteps,
  sourceHost,
  speechReady,
  useLocalAi,
  type LocalAiGroup,
} from "./localAi";
import { Found, useProposals } from "./Found";
import { useOwnerName } from "./ownerName";
import { useFirstTake } from "./useFirstTake";
import { Card } from "./Card";
import { CalendarCard } from "./CalendarCard";
import { ConnectionsCard } from "./ConnectionsCard";
import { useCalendarStep } from "./calendarStep";
import { useConnectionsStep } from "./connectionsStep";
import { useSkips, type SkippableStep, type Skips } from "./skips";
import type { SkipProps } from "./Card";
import { Ready } from "./Ready";
import "../../features/concierge/concierge.css";
import "./firstrun.css";

/** A failed take, as two tokens: what happened, and the plain reason. */
const FAILURE_TOKENS: Record<DictationFailure, { chip: string; reason: string }> = {
  permission_denied: { chip: "MIC BLOCKED", reason: "ALLOW IN BROWSER" },
  no_microphone: { chip: "NO MIC", reason: "NO DEVICE FOUND" },
  microphone_unavailable: { chip: "MIC BUSY", reason: "IN USE ELSEWHERE" },
  missing_model: { chip: "NO SPEECH MODEL", reason: "SET UP LOCAL AI" },
  rejected_token: { chip: "NOT HEARD", reason: "TOKEN REFUSED" },
  unreachable_hub: { chip: "NOT HEARD", reason: "HUB OFFLINE" },
  delivery_conflict: { chip: "NOT HEARD", reason: "TAKE CONFLICT" },
  transcription_failed: { chip: "NOT HEARD", reason: "SPEECH FAILED" },
  timeout: { chip: "NOT HEARD", reason: "TIMED OUT" },
  no_speech: { chip: "NOT HEARD", reason: "NO WORDS" },
  mic_interval_closed: { chip: "MIC CLOSED", reason: "TAKE ENDED" },
  provider_failure: { chip: "NOT HEARD", reason: "SPEECH FAILED" },
  audio_floor_held: { chip: "MIC BUSY", reason: "ANOTHER CAPTURE" },
  unknown: { chip: "NOT HEARD", reason: "NO REASON GIVEN" },
};

function ModelRows({ groups, ready }: { groups: LocalAiGroup[]; ready: boolean }) {
  return (
    <ul className="concierge-found-list firstrun-ledger" aria-label="Local models">
      {groups.map((group) => (
        <SurfaceLedgerRow
          key={group.key}
          lead={<span className="concierge-group-glyph">{group.glyph}</span>}
          primary={<span className="concierge-group-name">{group.name}</span>}
          cells={
            <span className="concierge-found-cells">
              <span className="concierge-token">{group.model}</span>
              <span className="concierge-token">{formatBytes(group.bytes)}</span>
              <span className="concierge-found-state">
                {ready || group.onDevice ? <LampGadget label="ON DEVICE" on /> : null}
              </span>
            </span>
          }
          expands={false}
          wrap
        />
      ))}
    </ul>
  );
}

function LocalAiCard({ ai, folded }: { ai: ReturnType<typeof useLocalAi>; folded: boolean }) {
  const status = ai.read.kind === "ok" ? ai.read.status : null;
  const groups = groupsOf(status);
  const state = status?.state;
  const ready = state === "ready";
  const running = state === "downloading";
  const stopped = state === "failed" || state === "needs_runtime" || state === "incomplete";
  const host = ai.host || sourceHost(status);
  const total = groups.reduce((sum, group) => sum + group.bytes, 0);
  const missing = missingBytes(status);
  return (
    <Card
      title="Local AI"
      testId="firstrun-local-ai"
      selected={ready}
      state={ready ? <LampGadget label="ON DEVICE" on /> : null}
    >
      {ai.read.kind === "unread" ? (
        <div className="firstrun-fail" role="alert">
          <StateChip state="unreachable" label="CAN'T CHECK" />
          <span className="firstrun-reason">{ai.read.reason}</span>
          <Button dense variant="secondary" onClick={() => void ai.refresh()}>
            Try again
          </Button>
        </div>
      ) : null}
      {status && (running || state === "failed") ? (
        <ProgressPlan compact steps={planSteps(status, ai.rate)} ariaLabel="Local AI download" />
      ) : status && !(folded && ready) ? (
        <ModelRows groups={groups} ready={ready} />
      ) : null}
      {status && stopped ? (
        <div className="firstrun-fail" role="alert">
          <StateChip
            state="failure"
            label={state === "failed" ? "CAN'T DOWNLOAD" : state === "incomplete" ? "NO SPEECH MODEL" : "NO RUNTIME"}
          />
          {status.error ? <span className="firstrun-reason">{status.error}</span> : null}
          {/* `incomplete`: setup cannot get the selected Whisper model, so a
              second press would do nothing (UX-CANON A11). */}
          {state !== "incomplete" ? (
            <Button dense variant="primary" loading={ai.busy} disabled={ai.busy} onClick={() => void ai.start()}>
              Try again
            </Button>
          ) : null}
        </div>
      ) : null}
      {status ? (
        <div className="firstrun-card-foot">
          {ready ? (
            <Receipt
              status="ok"
              label={[countToken(groups.length, "MODEL"), formatBytes(total), host ? `FROM ${host}` : null]
                .filter(Boolean)
                .join(" · ")}
              timestamp={ai.finishedAt ?? undefined}
            />
          ) : host && (missing > 0 || running) ? (
            <EgressChip label={host} scope="cloud" />
          ) : null}
          {state === "not_started" ? (
            <Button variant="primary" loading={ai.busy} disabled={ai.busy} onClick={() => void ai.start()}>
              {missing > 0 ? `Set up local AI · ${formatBytes(missing)}` : "Set up local AI"}
            </Button>
          ) : null}
          {running ? (
            <Button dense variant="ghost" disabled={ai.busy} onClick={() => void ai.cancel()}>
              Stop
            </Button>
          ) : null}
        </div>
      ) : null}
    </Card>
  );
}

function YouCard({ owner, folded }: { owner: ReturnType<typeof useOwnerName>; folded: boolean }) {
  const [alias, setAlias] = useState("");
  const commit = () => {
    if (!alias.trim()) return;
    owner.addAliases(alias);
    setAlias("");
  };
  return (
    <Card
      title="You"
      testId="firstrun-you"
      selected={owner.isSet}
      state={owner.isSet ? <StateChip state="success" label="SET" icon="●" /> : null}
    >
      {folded ? (
        <>
          <span className="firstrun-owner">{owner.name}</span>
          {owner.aliases.length ? (
            <span className="firstrun-alias-row">
              {owner.aliases.map((name) => (
                <span key={name} className="surface-token" data-chip>
                  {name}
                </span>
              ))}
            </span>
          ) : null}
        </>
      ) : (
      <div className="firstrun-name">
        <label className="firstrun-field">
          <span className="firstrun-caption">YOUR NAME</span>
          <StringGadget
            label="Your name"
            value={owner.name}
            onChange={owner.setName}
            placeholder="Name"
            inputProps={{ onBlur: () => void owner.flush() }}
          />
        </label>
        <label className="firstrun-field">
          <span className="firstrun-caption">ALSO CALLED</span>
          <span className="firstrun-alias-row">
            {owner.aliases.map((name) => (
              <span key={name} className="surface-token" data-chip>
                {name}
              </span>
            ))}
            <StringGadget
              label="Also called"
              value={alias}
              onChange={(next) => {
                // A spoken or pasted list arrives whole: commas split it.
                if (next.includes(",")) {
                  owner.addAliases(next);
                  setAlias("");
                } else setAlias(next);
              }}
              placeholder="Add"
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  commit();
                } else if (event.key === "Backspace" && !alias) owner.removeLastAlias();
              }}
              inputProps={{ onBlur: commit }}
            />
          </span>
        </label>
      </div>
      )}
      {owner.error ? (
        <div className="firstrun-fail" role="alert">
          <StateChip state="failure" label="NOT SAVED" />
          <span className="firstrun-reason">{owner.error}</span>
        </div>
      ) : null}
    </Card>
  );
}

function FirstWordsCard({
  ready,
  take,
}: {
  ready: boolean;
  take: ReturnType<typeof useFirstTake>;
}) {
  const heard = take.state === "heard" && take.take;
  const contract = take.failure ? DICTATION_FAILURES[take.failure] : null;
  return (
    <Card
      title="First words"
      testId="firstrun-first-words"
      className="firstrun-words"
      disabled={!ready}
      lit={ready && !heard}
      selected={take.kept}
      state={
        take.kept ? (
          <StateChip state="success" label="HEARD" icon="●" />
        ) : ready ? (
          <StateChip state="success" label="SPEECH READY" icon="●" />
        ) : (
          <StateChip state="idle" label="WAITS FOR SPEECH" />
        )
      }
    >
      {!ready ? (
        <Button variant="secondary" disabled>
          Dictate one sentence
        </Button>
      ) : heard && take.take ? (
        <HeardQuote
          text={take.take.text}
          seconds={take.take.seconds}
          at={take.take.at}
          local
          size={take.kept ? "primary" : "display"}
          verbs={
            take.kept ? undefined : <>
              {take.canPlay ? (
                <Button dense variant="secondary" aria-pressed={take.playing} onClick={take.play}>
                  {"▶ Play"}
                </Button>
              ) : null}
              <Button dense variant="ghost" disabled={take.keeping} onClick={take.again}>
                Again
              </Button>
              <Button
                dense
                variant="primary"
                loading={take.keeping}
                disabled={take.keeping}
                onClick={() => void take.keep()}
              >
                Keep as note
              </Button>
            </>
          }
        />
      ) : take.state === "listening" ? (
        <div className="firstrun-listen">
          <StateChip state="active" label="LISTENING" icon="●" />
          <LedMeter label="MIC" value={take.level} segments={16} />
          <Button dense variant="secondary" aria-label="Stop listening" onClick={() => void take.stop()}>
            Stop
          </Button>
        </div>
      ) : take.state === "writing" ? (
        <div className="firstrun-listen">
          <StateChip state="working" label="WRITING" icon="↻" />
          <LedMeter label="SPEECH" value={0} segments={16} scanning />
        </div>
      ) : (
        <>
          {take.failure ? (
            /* Astra #859 P2: tokens, not the shared recovery paragraph (this
               card has no draft editor; UX-CANON A3). The verbs are the ones
               that work: Again, the setup door when there is one, and
               Continue later at the foot of the face. */
            <div className="firstrun-fail" role="alert" data-testid="firstrun-take-failure">
              <StateChip state="failure" label={FAILURE_TOKENS[take.failure].chip} />
              <span className="surface-token" data-tone="danger">{FAILURE_TOKENS[take.failure].reason}</span>
              {contract?.setup ? (
                <Button
                  dense
                  variant="secondary"
                  onClick={() =>
                    needsMicrophoneDoctor(take.failure)
                      ? openSurfaceOr("configure-setup", "/")
                      : openSurfaceOr("project-setup", "/")
                  }
                >
                  {needsMicrophoneDoctor(take.failure) ? "Check the microphone" : "Setup"}
                </Button>
              ) : null}
            </div>
          ) : null}
          {contract && !contract.retry ? null : (
            <Button
              variant="primary"
              className="firstrun-big"
              disabled={!take.supported}
              onClick={() => void take.begin()}
            >
              {contract ? "Again" : "◖ Dictate one sentence"}
            </Button>
          )}
        </>
      )}
      {take.message ? (
        <div className="firstrun-fail" role="alert">
          <StateChip state="failure" label="NOT KEPT" />
          <span className="firstrun-reason">{take.message}</span>
        </div>
      ) : null}
    </Card>
  );
}

function skipProps(skips: Skips, step: SkippableStep): SkipProps {
  return {
    skipped: skips[step],
    busy: skips.busy === step,
    error: skips.error?.step === step ? skips.error.reason : "",
    onSkip: () => void skips.skip(step),
  };
}

export function FirstRun() {
  const ai = useLocalAi();
  const owner = useOwnerName();
  // Speech on this device lights First words. A read that failed leaves it
  // open: the dictation path names its own failure (honest, never stuck).
  const speech = ai.read.kind === "unread" || (ai.read.kind === "ok" && speechReady(ai.read.status));
  const aiReady = ai.read.kind === "ok" && ai.read.status.state === "ready";
  const handoff = useCallback(async (disposition: "completed" | "dismissed") => {
    await apiFetch("/api/desk/seed", { method: "POST" });
    await apiFetch("/api/setup/onboarding", { method: "PUT", json: { disposition } });
    await useDesk.getState().refresh();
  }, []);
  const take = useFirstTake({ onHandoff: handoff });
  const proposals = useProposals();
  const calendar = useCalendarStep();
  const connections = useConnectionsStep();
  const skips = useSkips();
  // Each optional step is done when it is in use, or when he skipped it.
  const calendarSkipped = skips.calendar && !calendar.inUse;
  const calendarDone = calendar.inUse || calendarSkipped;
  const connectionsDone = connections.done || skips.connections;
  // The C1 part is done: models here, his name, his words kept. Its three
  // cards fold to their receipts (canvas A: "the three C1 cards, finished").
  const c1Done = aiReady && owner.isSet && take.kept;
  // While the ingest still reads a source just added, the Door's next
  // meeting may change: Ready waits for the read (calendarStep `follow`).
  const ready = c1Done && skips.loaded && calendarDone && !calendar.following && connectionsDone;
  // His words are back and not kept yet: they are the face's display fact.
  const heard = take.state === "heard" && !take.kept;
  // One lit card: the next press. First words lights itself while it waits
  // for his sentence; then the Calendar; then the Connections.
  const wordsPending = speech && !take.kept;
  const calendarLit = !ready && !wordsPending && skips.loaded && calendar.loaded && !calendarDone;
  const connectionsLit = !ready && !wordsPending && skips.loaded && calendarDone && connections.loaded && !connectionsDone;
  return (
    <section
      className="firstrun"
      data-heard={heard || undefined}
      data-ready={ready || undefined}
      aria-label="Get ready"
      data-testid="firstrun"
    >
      {/* One display element per face: the heading until his words come
          back; then his words are the display fact; when every step is
          done, "Ready, <his name>". */}
      {ready ? (
        <Ready
          name={owner.name}
          heardText={take.take?.text ?? ""}
          calendar={calendar}
          calendarSkipped={calendarSkipped}
          connections={connections}
          finish={take.finish}
          busy={take.keeping}
        />
      ) : (
        <h1 className={heard ? "firstrun-heading is-quiet" : "surface-display firstrun-heading"}>
          {heard ? "Heard" : "Get ready"}
        </h1>
      )}
      <div className="firstrun-cards">
        <LocalAiCard ai={ai} folded={c1Done} />
        <YouCard owner={owner} folded={c1Done} />
        <FirstWordsCard ready={speech} take={take} />
      </div>
      <div className="firstrun-cards firstrun-cards-two">
        <CalendarCard step={calendar} lit={calendarLit} skip={skipProps(skips, "calendar")} />
        <ConnectionsCard step={connections} lit={connectionsLit} skip={skipProps(skips, "connections")} />
      </div>
      <Found proposals={proposals} />
      {take.message && ready ? (
        <div className="firstrun-fail" role="alert">
          <StateChip state="failure" label="NOT KEPT" />
          <span className="firstrun-reason">{take.message}</span>
        </div>
      ) : null}
      {ready ? null : (
        <div className="firstrun-foot">
          <Button variant="ghost" dense disabled={take.keeping} loading={take.keeping} onClick={() => void take.leave()}>
            {heard ? "Save draft & continue" : "Continue later"}
          </Button>
        </div>
      )}
    </section>
  );
}
