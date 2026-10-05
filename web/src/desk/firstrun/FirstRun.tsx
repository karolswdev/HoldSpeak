/* First run — "C1 · Heard first" (owner ratified 2026-10-05, canvas
 * FzBum28aTJQbsqwBvLuP16 v2). Three cards on one screen: Local AI · You ·
 * First words. One press downloads every local model; First words lights
 * when the speech model lands, so he can speak while the chat model still
 * downloads; his sentence comes back at the display step. */
import { useCallback, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import {
  ChoiceCardShell,
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
import { DICTATION_FAILURES, needsMicrophoneDoctor } from "../../lib/dictationRecovery";
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
import { useOwnerName } from "./ownerName";
import { useFirstTake } from "./useFirstTake";
import "../../features/concierge/concierge.css";
import "./firstrun.css";

function Card({
  title,
  state,
  lit,
  selected,
  disabled,
  className,
  testId,
  children,
}: {
  title: string;
  state?: ReactNode;
  lit?: boolean;
  selected?: boolean;
  disabled?: boolean;
  className?: string;
  testId: string;
  children: ReactNode;
}) {
  return (
    <ChoiceCardShell
      as="section"
      aria-label={title}
      className={`firstrun-card${className ? ` ${className}` : ""}`}
      data-lit={lit || undefined}
      data-testid={testId}
      selected={selected}
      disabled={disabled}
      label={
        <span className="firstrun-cardhead">
          <span className="firstrun-card-title">{title}</span>
          {state ? <span className="firstrun-cardstate">{state}</span> : null}
        </span>
      }
    >
      <div className="firstrun-card-body">{children}</div>
    </ChoiceCardShell>
  );
}

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

function LocalAiCard({ ai }: { ai: ReturnType<typeof useLocalAi> }) {
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
      ) : status ? (
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

function YouCard() {
  const owner = useOwnerName();
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
      state={
        ready ? (
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
          verbs={
            <>
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
          {contract ? (
            <div className="firstrun-fail" role="alert">
              <StateChip state="failure" label="NOT HEARD" />
              <span className="firstrun-reason">{contract.message}</span>
              {contract.setup ? (
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
          <Button
            variant="primary"
            className="firstrun-big"
            disabled={!take.supported || (contract ? !contract.retry : false)}
            onClick={() => void take.begin()}
          >
            {contract ? "Try again" : "◖ Dictate one sentence"}
          </Button>
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

export function FirstRun() {
  const ai = useLocalAi();
  // Speech on this device lights First words. A read that failed leaves it
  // open: the dictation path names its own failure (honest, never stuck).
  const speech = ai.read.kind === "unread" || (ai.read.kind === "ok" && speechReady(ai.read.status));
  const handoff = useCallback(async (disposition: "completed" | "dismissed") => {
    await apiFetch("/api/desk/seed", { method: "POST" });
    await apiFetch("/api/setup/onboarding", { method: "PUT", json: { disposition } });
    await useDesk.getState().refresh();
  }, []);
  const take = useFirstTake({ onHandoff: handoff });
  const heard = take.state === "heard";
  return (
    <section className="firstrun" data-heard={heard || undefined} aria-label="Get ready" data-testid="firstrun">
      {/* One display element per face: the heading until his words come
          back; then his words are the display fact. */}
      <h1 className={heard ? "firstrun-heading is-quiet" : "surface-display firstrun-heading"}>
        {heard ? "Heard" : "Get ready"}
      </h1>
      <div className="firstrun-cards">
        <LocalAiCard ai={ai} />
        <YouCard />
        <FirstWordsCard ready={speech} take={take} />
      </div>
      <div className="firstrun-foot">
        <Button variant="ghost" dense disabled={take.keeping} loading={take.keeping} onClick={() => void take.leave()}>
          {heard ? "Save draft & continue" : "Continue later"}
        </Button>
      </div>
    </section>
  );
}
