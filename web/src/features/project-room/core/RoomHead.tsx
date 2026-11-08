// The Room's head (R1 "the brief", owner 2026-11-08): the window toolbar
// (Write update, History, the Ask field with its mic), the status line (the
// state as a dot and a word, the last update, what needs him) and the
// draft's run. A failed health read is named.
import type { ReactNode } from "react";
import { DotWord, RunLine, StateChip, SurfaceSection, Toolbar } from "../../../desk/surface";
import { StringGadget } from "../../../desk/surface/gadgets";
import { refOpener } from "../../../desk/openObject";
import { openSurfaceOr } from "../../../desk/shell";
import { useEngine } from "../../../desk/hooks/useEngine";
import { Button } from "../../../components/signal/Signal";
import type { RoomNowData, RoomSnapshot } from "../model";
import { dayWords, isMine, stateLine, type StateLine } from "../now/model";
import type { useUpdateController } from "../update/useUpdateController";
import type { RoomAsk } from "./Ask";
import { sourcesWord } from "./format";
import "./now-face.css";

/** What needs him on this Project: his own Needs you rows, or the claims
 *  that wait on his review when he has no row. Never a zero (the caller
 *  omits the part). */
export function needCount(room: RoomSnapshot, pendingCount: number): number {
  const mine = room.needsYou.state === "ok" ? room.needsYou.items.filter(isMine).length : 0;
  return mine || pendingCount;
}

/** The state as a lamp and a word ("At risk: tokenization waits on the HSM
 *  ceremony"): the state word leads in its colour with its lamp (the Room's
 *  own .room-state-word), the reason follows in ink; its source opens from it. */
function RoomHeadline({ line }: { line: StateLine }) {
  const open = line.ref ? refOpener(line.ref) : null;
  const split = line.text.indexOf(": ");
  const words = split > 0
    ? <><span className="room-state-word">{line.text.slice(0, split + 1)}</span>{" "}<span className="room-state-reason">{line.text.slice(split + 2)}</span></>
    : <span className="room-state-word">{line.text}</span>;
  return (
    <span className="room-headline" data-testid="room-headline" data-tone={line.tone}>
      {open ? (
        <Button variant="chrome" className="room-headline-open room-link" data-testid="room-headline-open"
          aria-label={`${line.text}. Open the source`} onClick={open}>
          {words}
        </Button>
      ) : words}
    </span>
  );
}

export function RoomHead({
  room,
  updateCtrl,
  ask,
  pendingCount,
  needsOpen,
  onNeeds,
  onHistory,
  quiet = false,
}: {
  room: RoomSnapshot;
  updateCtrl: ReturnType<typeof useUpdateController>;
  ask: RoomAsk;
  pendingCount: number;
  /** The Needs you rows are open under the status line. */
  needsOpen: boolean;
  onNeeds: () => void;
  onHistory: () => void;
  /** PHILO-17: another well holds the face's one primary (Add source's Add). */
  quiet?: boolean;
}) {
  const updateEngine = useEngine("project.update_draft");
  const sources = room.sources.state === "ok" ? room.sources.items : [];
  const sourceWord = sourcesWord(sources, room.sources.state === "ok" ? room.sources.quietUntil : null);
  const now = room.now?.state === "ok" ? (room.now as RoomNowData & { state: "ok" }) : null;
  const lastUpdate = now?.lastUpdateAt ? dayWords(now.lastUpdateAt) : "";
  // PHILO-15 B69/B60: a STALE source, or quiet hours holding the sweep, is
  // said on the line (a plain Checked time is not: the window reads itself).
  const sourceFact = sourceWord && !/^Checked /.test(sourceWord.word) ? sourceWord : null;
  const need = needCount(room, pendingCount);
  const draftRun = updateCtrl.draftRun;
  const parts: ReactNode[] = [];
  if (lastUpdate) parts.push(<span key="last" data-testid="room-status-last-update">{`last update ${lastUpdate}`}</span>);
  if (need > 0) {
    parts.push(
      <Button key="need" variant="chrome" className="room-link" aria-expanded={needsOpen}
        onClick={onNeeds} data-testid="room-status-need">
        {`${need} need you`}
      </Button>,
    );
  }
  if (sourceFact) {
    parts.push(<DotWord key="src" tone={sourceFact.stale ? "warn" : "idle"} data-testid="room-sources-word">{sourceFact.word}</DotWord>);
  }

  return (
    <div className="room-head" data-testid="room-head">
      {/* The Project's name, unseen: the title bar says it; the desk rigs
          read which Project this Room holds here. */}
      <span className="room-head-name-measure" aria-hidden="true">{room.project.name}</span>
      {/* R1: one primary, History, and the Ask as a plain field with its mic. */}
      <Toolbar label="Project actions" className="room-toolbar" trailing={(
        <span className="room-ask-field" data-testid="room-ask-well">
          <StringGadget
            label="Ask this project"
            value={ask.prompt}
            onChange={ask.setPrompt}
            placeholder="Ask this project"
            inputRef={ask.inputRef}
            micDraftScope={`project-ask-${room.project.id}`}
            inputProps={{ className: "room-ask-input" }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                e.preventDefault();
                ask.ask();
              }
            }}
          />
        </span>
      )}>
        <Button
          dense
          variant={quiet ? "secondary" : "primary"}
          loading={updateCtrl.loading || updateCtrl.draftBusy}
          disabled={updateEngine.state === "unread"}
          // Betterment P1: the records draft at once; the engine's after.
          onClick={() => void updateCtrl.write(updateEngine.state === "set")}
          data-testid="updates-verb"
        >
          Write update
        </Button>
        <Button dense variant="secondary" onClick={onHistory} data-testid="room-head-history">History</Button>
      </Toolbar>
      <p className="room-status-line" data-testid="room-status-line">
        <RoomHeadline line={stateLine(room, Boolean(sourceWord?.stale))} />
        {room.project.isArchived ? (
          <span className="kit-pill" data-tone="danger" data-dot="">Archived</span>
        ) : null}
        {parts.map((part, index) => (
          <span key={index} className="room-status-part">
            <span className="room-status-sep" aria-hidden="true">·</span>
            {part}
          </span>
        ))}
      </p>
      {/* P0 (betterment/projects): the draft's run where he pressed it.
          The Update posture draws its own line once it is open. */}
      {updateCtrl.posture === "off" && (draftRun.phase === "running" || draftRun.phase === "failure") ? (
        <div className="room-head-run" data-testid="room-head-draft-run">
          <RunLine
            phase={draftRun.phase}
            verb="Working"
            pastVerb="Drafted"
            model={draftRun.generator === "model" ? updateEngine.model : ""}
            startedAt={draftRun.startedAt}
            elapsedSeconds={draftRun.elapsedSeconds}
            reason={draftRun.reason}
            detail={draftRun.detail}
            onRetry={draftRun.generator ? () => void updateCtrl.draft(draftRun.generator!) : undefined}
            onAction={draftRun.reason === "no_engine"
              ? () => openSurfaceOr("configure-runs-on", "/settings", "models") : undefined}
          />
          {draftRun.phase === "failure" && draftRun.generator === "model" ? (
            <Button dense variant="ghost" onClick={() => void updateCtrl.draft("deterministic")}
              data-testid="room-head-draft-records">
              Use a draft from your records
            </Button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

/* A failed health read is named, with Retry (the head then says "Not all
 * read"; it never claims a state it could not read). Betterment P3 keeps
 * this from the parked SIGNALS plate. */
export function HealthNotRead({ onRetry }: { onRetry: () => void }) {
  return (
    <SurfaceSection
      label="Health"
      actions={<Button dense variant="ghost" onClick={onRetry} data-testid="health-retry">Retry</Button>}
    >
      <span data-testid="health-not-read">
        <StateChip state="unreachable" label="HEALTH NOT READ" />
      </span>
    </SurfaceSection>
  );
}
